#!/usr/bin/env python3
"""Store the Canvas API token in the macOS Keychain, once.

    python canvas_login.py              # store (refuses to clobber silently)
    python canvas_login.py --replace    # overwrite an existing entry
    python canvas_login.py --status     # is one stored? is it still valid?
    python canvas_login.py --forget     # remove it

After this, build_course.py and verify_course.py find the token by themselves.
No `export`, no `read -rs`, no paste into a shell that might mangle it, and
nothing that stops working when you open a new terminal tab.

The token is validated against Canvas BEFORE it is stored, so a truncated
paste fails here rather than halfway through a course build.

It never appears in argv (written via `security -i`, secret on stdin) and never
in shell history (read via getpass).
"""

import getpass
import os
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pipeline import canvas_token as ct  # noqa: E402

CONFIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "course_config.yaml")


def main() -> int:
    if sys.platform != "darwin":
        sys.exit("This helper uses the macOS Keychain. On another OS, export "
                 f"${ct.ENV_VAR} instead.")

    cfg = yaml.safe_load(open(CONFIG))
    base_url = cfg["canvas"]["base_url"]
    course_id = cfg["canvas"]["course_id"]

    if "--forget" in sys.argv:
        print("removed from Keychain" if ct.keychain_delete() else "nothing stored")
        return 0

    if "--status" in sys.argv:
        tok = ct.keychain_get()
        if not tok:
            print("No token stored. Run: python canvas_login.py")
            return 1
        print(f"Stored: {len(tok)} chars, starts {tok[:5]!r}")
        who = ct.preflight(base_url, tok, "macOS Keychain", course_id)
        print(f"Valid. Authenticated as {who}")
        return 0

    if ct.keychain_get() and "--replace" not in sys.argv:
        print("A token is already stored. Use --replace to overwrite, "
              "--status to test it, or --forget to remove it.")
        return 1

    print(f"Canvas: {base_url}  (course {course_id})")
    print("  Get a token: avatar -> Account -> Settings -> Approved Integrations")
    print("  -> New Access Token. Canvas shows it once; use the copy button.")
    token = ct._clean(getpass.getpass("Paste token (input hidden): "))
    if not token:
        sys.exit("Nothing entered.")

    # Validate BEFORE storing. Storing a bad token just moves the failure.
    who = ct.preflight(base_url, token, "prompt", course_id)
    print(f"Valid. Authenticated as {who}")

    if not ct.keychain_set(token):
        sys.exit("ERROR: could not write to the Keychain.")
    print("Stored in the macOS Keychain.")

    if os.environ.get(ct.ENV_VAR, "").strip():
        print(f"\nNOTE: ${ct.ENV_VAR} is ALSO set in this shell and takes "
              f"precedence.\n      If it holds an older token, run: unset {ct.ENV_VAR}")

    print("\nbuild_course.py and verify_course.py will now find it automatically.")
    print("When the course is finished, revoke the token in Canvas and run:")
    print("  python canvas_login.py --forget")
    return 0


if __name__ == "__main__":
    sys.exit(main())
