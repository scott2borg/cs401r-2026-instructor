#!/usr/bin/env python3
"""Diagnose CANVAS_API_TOKEN without revealing it.

Reports the shape of whatever is in the variable -- length, prefix, and any
stray characters -- then tries a single authenticated call. Prints enough to
identify the problem and never enough to leak the credential.

    python check_token.py
"""

import os
import re
import sys

import requests

BASE = "https://byu.instructure.com"

raw = os.environ.get("CANVAS_API_TOKEN")

print("── CANVAS_API_TOKEN shape ──")
if raw is None:
    sys.exit("  NOT SET in this shell at all.")
if raw == "":
    sys.exit("  SET BUT EMPTY. `read` captured nothing — most often because the\n"
             "  whole command block was pasted at once and `read` consumed a\n"
             "  blank line instead of waiting for you.")

print(f"  raw length        : {len(raw)}")
print(f"  starts with       : {raw[:5]!r}")
print(f"  ends with         : {raw[-4:]!r}")

# Canvas tokens are <digits>~<alphanumerics>, typically ~70 chars total.
looks_right = bool(re.fullmatch(r"\d+~[A-Za-z0-9]+", raw.strip()))
print(f"  matches <id>~<alnum>: {looks_right}")

problems = []
if "\n" in raw or "\r" in raw:
    problems.append(f"contains newline(s) — {raw.count(chr(10))} LF, {raw.count(chr(13))} CR")
if raw != raw.strip():
    problems.append("has leading/trailing whitespace")
if " " in raw.strip():
    problems.append("contains an internal space — more than one token/word was captured")
if "\x1b" in raw:
    problems.append("contains ESC characters — bracketed-paste escape codes were captured")
if raw.strip().startswith(("'", '"')) or raw.strip().endswith(("'", '"')):
    problems.append("wrapped in quotes — the quotes are part of the value")
if len(raw) > 120:
    problems.append(f"far too long ({len(raw)}); a Canvas token is ~70 characters")
if "python" in raw or "export" in raw or "printf" in raw:
    problems.append("contains shell command text — a pasted command line was captured, not a token")

if problems:
    print("\n  PROBLEMS FOUND:")
    for p in problems:
        print("   -", p)
else:
    print("\n  shape looks correct")

# What a cleaned-up version would be
cleaned = raw.strip().strip('"').strip("'").split()[0] if raw.strip() else ""
cleaned = cleaned.replace("\x1b[200~", "").replace("\x1b[201~", "")
if cleaned != raw:
    print(f"\n  after cleaning    : {len(cleaned)} chars, starts {cleaned[:5]!r}")

print("\n── live auth test ──")
for label, tok in (("as-is", raw), ("cleaned", cleaned)):
    if label == "cleaned" and cleaned == raw:
        continue
    r = requests.get(f"{BASE}/api/v1/users/self",
                     headers={"Authorization": f"Bearer {tok}"})
    if r.ok:
        print(f"  {label:8s} -> OK, authenticated as {r.json().get('name','?')}")
        if label == "cleaned":
            print("\n  FIX: the token is fine; the variable is dirty. Re-set it with:")
            print("    printf 'Canvas token: '; read -rs CANVAS_API_TOKEN; echo; export CANVAS_API_TOKEN")
            print("  and paste ONLY the token — do not paste the surrounding commands.")
    else:
        print(f"  {label:8s} -> {r.status_code} {r.text[:80]}")
