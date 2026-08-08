"""Resolve and validate the Canvas API token.

WHY THIS EXISTS
---------------
Two failures cost real time on 2026-08-07.

1. A rejected token produced `✗ 401` on every write while build_course.py
   exited 0. Nothing reached Canvas, and it looked like a verify-only problem
   because verify_course.py was the only script that failed loudly. Writes go
   through CanvasAPI._post/_put, which print and return None rather than raise
   -- deliberately, so one bad item does not abandon a run. The cost is that a
   bad *token* looks identical to 900 bad items. preflight() closes that: one
   authenticated call before any stage runs.

2. The token itself. `read -rs` is correct but fragile: paste the surrounding
   command block and `read` eats the next line; use the bash idiom `read -rsp`
   and zsh silently sets it empty. Both produce "Invalid access token" with no
   hint. resolve() removes the paste from the common path entirely by keeping
   the token in the macOS Keychain.

RESOLUTION ORDER
----------------
    1. $CANVAS_API_TOKEN      -- CI, or a deliberate one-off override
    2. macOS Keychain         -- the normal path, survives new shells
    3. interactive prompt     -- getpass; offers to save to the Keychain

A stale exported token beats the Keychain, which is the one sharp edge. It is
deliberate -- an explicit env var should win -- and resolve() says out loud
where the token came from so a stale export is visible rather than mysterious.

SECURITY
--------
Writes go through `security -i`, which reads the command from stdin, so the
token never appears in this process's argv and cannot be read out of `ps`.
Passing it as `security add-generic-password -w <token>` would expose it.
Reads use `find-generic-password -w`, which returns the secret on stdout only.
"""

from __future__ import annotations

import getpass
import os
import subprocess
import sys

import requests

SERVICE = "cs401r-canvas"
ACCOUNT = "canvas-api-token"
ENV_VAR = "CANVAS_API_TOKEN"


# ── Keychain (macOS) ──────────────────────────────────────────────────────────

def _keychain_available() -> bool:
    return sys.platform == "darwin"


def keychain_get() -> str | None:
    if not _keychain_available():
        return None
    r = subprocess.run(
        ["security", "find-generic-password", "-s", SERVICE, "-a", ACCOUNT, "-w"],
        capture_output=True, text=True,
    )
    return r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else None


def keychain_set(token: str) -> bool:
    """Store the token. Secret goes over stdin, never argv."""
    if not _keychain_available():
        return False
    cmd = f"add-generic-password -s {SERVICE} -a {ACCOUNT} -w {token} -U\n"
    r = subprocess.run(["security", "-i"], input=cmd,
                       capture_output=True, text=True)
    return r.returncode == 0


def keychain_delete() -> bool:
    if not _keychain_available():
        return False
    r = subprocess.run(
        ["security", "delete-generic-password", "-s", SERVICE, "-a", ACCOUNT],
        capture_output=True, text=True,
    )
    return r.returncode == 0


# ── Resolution ────────────────────────────────────────────────────────────────

def _clean(raw: str) -> str:
    """Undo the damage a paste does. Mirrors check_token.py."""
    t = raw.strip().strip('"').strip("'")
    t = t.replace("\x1b[200~", "").replace("\x1b[201~", "")
    return t.split()[0] if t.split() else ""


def resolve(allow_prompt: bool = True) -> tuple[str, str]:
    """Return (token, source). Exits with a diagnosis if nothing is available."""
    raw = os.environ.get(ENV_VAR, "")
    if raw.strip():
        return _clean(raw), f"${ENV_VAR}"

    tok = keychain_get()
    if tok:
        return _clean(tok), "macOS Keychain"

    if not allow_prompt or not sys.stdin.isatty():
        sys.exit(
            f"ERROR: no Canvas token.\n"
            f"  Not in ${ENV_VAR}, and nothing stored in the Keychain.\n"
            f"  Store one once:  python canvas_login.py\n"
            f"  Or for this shell only:\n"
            f"    printf 'Canvas token: '; read -rs {ENV_VAR}; echo; export {ENV_VAR}"
        )

    print("No stored Canvas token found.")
    print("  Canvas -> avatar -> Account -> Settings -> Approved Integrations")
    tok = _clean(getpass.getpass("Canvas token (input hidden): "))
    if not tok:
        sys.exit("ERROR: nothing entered.")
    return tok, "prompt"


# ── Validation ────────────────────────────────────────────────────────────────

def preflight(base_url: str, token: str, source: str = "", course_id=None) -> str:
    """One authenticated call before any write. Returns the Canvas user name.

    Exits with a diagnosis rather than letting a bad token turn into a wall of
    `✗ 401` from individual writes.
    """
    base_url = base_url.rstrip("/")
    headers = {"Authorization": f"Bearer {token}"}

    try:
        r = requests.get(f"{base_url}/api/v1/users/self", headers=headers, timeout=30)
    except requests.RequestException as e:
        sys.exit(f"ERROR: cannot reach {base_url}: {e}")

    if r.status_code == 401:
        where = f" (from {source})" if source else ""
        hint = ""
        if source == f"${ENV_VAR}":
            hint = (f"\n       ${ENV_VAR} is set in this shell and is what was used.\n"
                    "       If you recently generated a NEW token, this shell still\n"
                    "       holds the OLD one -- and generating a replacement often\n"
                    "       revokes it. Run:  unset " + ENV_VAR + "\n"
                    "       then re-run; the Keychain copy will be used instead.")
        elif source == "macOS Keychain":
            hint = ("\n       The stored token was rejected. Replace it with:\n"
                    "         python canvas_login.py --replace")
        sys.exit(
            f"ERROR: Canvas rejected the token ({len(token)} chars){where}.\n"
            f"       Diagnose without revealing it:  python check_token.py"
            f"{hint}"
        )

    if r.status_code == 403:
        sys.exit("ERROR: token authenticated but is forbidden (403). It may be "
                 "scoped, or the account lacks permission on this Canvas.")
    r.raise_for_status()

    name = r.json().get("name", "?")

    if course_id is not None:
        c = requests.get(f"{base_url}/api/v1/courses/{course_id}",
                         headers=headers, timeout=30)
        if c.status_code in (401, 403, 404):
            sys.exit(f"ERROR: authenticated as {name}, but course {course_id} is "
                     f"not visible to this token ({c.status_code}).\n"
                     f"       Wrong Canvas account, or wrong course_id in "
                     f"course_config.yaml.")
        c.raise_for_status()
        return f"{name} | course: {c.json().get('name','?')}"

    return name
