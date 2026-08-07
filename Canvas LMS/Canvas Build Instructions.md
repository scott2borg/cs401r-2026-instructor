---
superseded: 2026-08-05
---

# Moved

The Canvas runbook now lives at the project root, next to the scripts it
describes:

**[[Canvas Update Process]]** — `CS_401R_2026/Canvas Update Process.md`

It moved because keeping it here caused the exact mistake it was meant to
prevent: the scripts are at `CS_401R_2026/`, this folder holds only retired
code, and running `python build_course.py` from here fails with
`can't open file`.

`_superseded/` holds the retired `canvas_builder.py` and its verifier. Do not
run them.
