#!/usr/bin/env python3
"""Verify what `canvas_builder.py --sync` actually did, against the live API.

Written because the sync output prints a check mark for every step it attempts
and cannot see three things that matter:

  * whether the uploaded files are really in the Pre-Lab Guides folder
  * whether the assignment descriptions contain REAL file links, or silently
    fell back to the "see the course repository" plain-text placeholder
  * whether the pre-lab assignments landed in a module at all -- module lookup
    is by exact name, and a mismatch fails silently by design of the Canvas API

Run with the same env vars as the builder:
    export CANVAS_API_TOKEN="..."
    export CANVAS_COURSE_ID="34609"
    python verify_canvas_sync.py
"""

import os
import re
import sys

import requests

BASE_URL  = "https://byu.instructure.com"
COURSE_ID = os.environ.get("CANVAS_COURSE_ID", "").strip()
API_TOKEN = os.environ.get("CANVAS_API_TOKEN", "").strip()

# Strip stray quotes: `export CANVAS_API_TOKEN="'abc'"` and copy-paste from a
# doc both leave them attached, and Canvas reports the result as an invalid
# token rather than a malformed header.
API_TOKEN = API_TOKEN.strip().strip('"').strip("'")
COURSE_ID = COURSE_ID.strip().strip('"').strip("'")

if not API_TOKEN:
    sys.exit(
        "ERROR: CANVAS_API_TOKEN is empty or unset in THIS shell.\n"
        "       An empty bearer token is what produces Canvas's\n"
        '       {"errors":[{"message":"Invalid access token."}]}\n'
        "       Re-export it in this terminal:\n"
        '         export CANVAS_API_TOKEN="1234~..."\n'
        '         export CANVAS_COURSE_ID="34609"'
    )
if not COURSE_ID:
    sys.exit("ERROR: CANVAS_COURSE_ID is empty or unset in this shell.")

ROOT    = f"{BASE_URL}/api/v1/courses/{COURSE_ID}"
HEADERS = {"Authorization": f"Bearer {API_TOKEN}"}


def preflight():
    """Fail with a diagnosis, not a traceback."""
    r = requests.get(f"{BASE_URL}/api/v1/users/self", headers=HEADERS)
    if r.status_code == 401:
        sys.exit(
            f"ERROR: Canvas rejected the token ({len(API_TOKEN)} chars).\n"
            "       Causes, in order of likelihood:\n"
            "         1. Not exported in this shell (most common)\n"
            "         2. Expired - Canvas tokens can carry a 30-day expiry\n"
            "         3. Truncated on paste, or wrapping quotes included\n"
            "       Mint a new one: avatar -> Account -> Settings ->\n"
            "       Approved Integrations -> New Access Token."
        )
    r.raise_for_status()
    me = r.json()
    print(f"Authenticated as {me.get('name','?')} (user {me.get('id','?')})")

    c = requests.get(ROOT, headers=HEADERS)
    if c.status_code == 404:
        sys.exit(f"ERROR: course {COURSE_ID} not found, or this token cannot see it.")
    c.raise_for_status()
    print(f"Course: {c.json().get('name','?')}\n")

PASS, FAIL, WARN = [], [], []


def ok(msg, detail=""):   PASS.append(msg); print(f"  PASS  {msg}" + (f"  [{detail}]" if detail else ""))
def bad(msg, detail=""):  FAIL.append(msg); print(f"  FAIL  {msg}" + (f"  [{detail}]" if detail else ""))
def warn(msg, detail=""): WARN.append(msg); print(f"  WARN  {msg}" + (f"  [{detail}]" if detail else ""))


def get_all(path):
    out, url = [], f"{ROOT}{path}"
    params = {"per_page": 100}
    while url:
        r = requests.get(url, headers=HEADERS, params=params)
        if not r.ok:
            sys.exit(f'ERROR: GET {url} -> {r.status_code} {r.text[:200]}')
        out.extend(r.json())
        url = None
        for part in r.headers.get("Link", "").split(","):
            if 'rel="next"' in part:
                url = part.split(";")[0].strip().strip("<>")
                params = {}
        # noqa
    return out


PRELAB_NAMES = [
    "Pre-Lab 3 — Bedrock Model Access Setup",
    "Pre-Lab 4 — SageMaker Training Quota Setup",
]
LAB_NAMES = [
    "Lab 3 — Model Development",
    "Lab 4 — XOps, Testing & CI/CD Pipeline",
]

print(f"Verifying {BASE_URL}/courses/{COURSE_ID}\n")
preflight()

# ── 1. Files ────────────────────────────────────────────────────────────────
print("── Files ──")
files   = get_all("/files")
folders = {f["id"]: f["full_name"] for f in get_all("/folders")}
guide_files = {}
for f in files:
    if f["display_name"].startswith("Pre-Lab"):
        guide_files[f["display_name"]] = f
        folder = folders.get(f["folder_id"], "?")
        detail = f"id={f['id']} {f['size']:,}B in {folder}"
        if "Pre-Lab Guides" in folder:
            ok(f"{f['display_name']} in correct folder", detail)
        else:
            warn(f"{f['display_name']} in unexpected folder", detail)
        if f["content-type"] != "text/html":
            warn(f"{f['display_name']} content-type is {f['content-type']}",
                 "Canvas may download rather than preview it")
        if f.get("hidden") or f.get("locked"):
            warn(f"{f['display_name']} is hidden/locked", "students will not see it")

if len(guide_files) == 0:
    bad("no Pre-Lab guide files found in course Files")
elif len(guide_files) > 2:
    bad(f"{len(guide_files)} guide files found — duplicates?",
        ", ".join(guide_files))
else:
    ok(f"{len(guide_files)} guide file(s) present")

# ── 2. Assignments: existence, duplicates, settings ─────────────────────────
print("\n── Assignments ──")
assigns = get_all("/assignments")
by_name = {}
for a in assigns:
    by_name.setdefault(a["name"], []).append(a)

for n in PRELAB_NAMES + LAB_NAMES:
    hits = by_name.get(n, [])
    if not hits:
        bad(f"missing: {n}")
    elif len(hits) > 1:
        bad(f"DUPLICATED x{len(hits)}: {n}", ",".join(str(h['id']) for h in hits))
    else:
        ok(f"exactly one: {n}", f"id={hits[0]['id']}")

for n in PRELAB_NAMES:
    for a in by_name.get(n, []):
        if a["points_possible"] not in (0, 0.0):
            warn(f"{n} points_possible={a['points_possible']}", "expected 0")
        else:
            ok(f"{n} is 0 points")
        if a.get("due_at", "").startswith("2026-09-30") or a.get("due_at", "").startswith("2026-10-01"):
            ok(f"{n} due date set", a["due_at"])
        else:
            warn(f"{n} unexpected due date", str(a.get("due_at")))
        if a.get("published"):
            warn(f"{n} is PUBLISHED", "expected draft")

# ── 3. The important one: do descriptions carry REAL file links? ────────────
print("\n── Link resolution (the silent-failure check) ──")
FALLBACK = "see the course repository"
for n in PRELAB_NAMES + LAB_NAMES:
    for a in by_name.get(n, []):
        desc = a.get("description") or ""
        links = re.findall(r'/courses/\d+/files/(\d+)', desc)
        if FALLBACK in desc:
            bad(f"{n} used the FALLBACK text — upload id was missing at build time")
        elif links:
            good = [l for l in links if any(str(g["id"]) == l for g in guide_files.values())]
            if good:
                ok(f"{n} links to real uploaded file(s)", "file ids " + ",".join(sorted(set(good))))
            else:
                bad(f"{n} links to file ids not in this course", ",".join(links))
        else:
            if n in PRELAB_NAMES:
                bad(f"{n} has no file link at all")
            else:
                warn(f"{n} has no file link", "expected a prerequisite banner")
        if "{{PRELAB" in desc:
            bad(f"{n} contains an UNRESOLVED placeholder")

# ── 4. Module placement (fails silently in the builder) ─────────────────────
print("\n── Module placement ──")
modules = get_all("/modules")
placed = {}
for m in modules:
    for it in get_all(f"/modules/{m['id']}/items"):
        if it.get("type") == "Assignment":
            placed.setdefault(it.get("title"), []).append(m["name"])

for n in PRELAB_NAMES:
    where = placed.get(n, [])
    if not where:
        bad(f"{n} is in NO module", "created but orphaned — module name lookup missed")
    else:
        ok(f"{n} in module", "; ".join(where))

# ── 5. Content corrections landed ─────────────────────────────────────────
#
# The "5 phases" check that used to live here was a stale positive: it looked
# for a literal string that only ever existed in the hand-written HTML. Lab
# descriptions are generated from the markdown now, so the useful checks are
# structural. "5 stages" must not appear -- that is covered by the sweep below.
print("\n── Generated-content structure ──")

for lab_name in LAB_NAMES + PRELAB_NAMES:
    for a in by_name.get(lab_name, []):
        d = a.get("description") or ""
        if "Tasks &amp; Point Breakdown" in d or "Tasks & Point Breakdown" in d:
            ok(f"{lab_name} has a generated points table")
        elif lab_name in LAB_NAMES:
            bad(f"{lab_name} has NO points table", "generation may have failed")

lab3 = (by_name.get("Lab 3 — Model Development") or [{}])[0]
d3 = lab3.get("description") or ""
if "training quota is" in d3 or "on-demand training quota" in d3:
    ok("Lab 3 surfaces the training-quota constraint")
else:
    bad("Lab 3 does not mention the training quota",
        "it is in the markdown body but not the meta block, so it never reaches Canvas")

lab4 = (by_name.get("Lab 4 — XOps, Testing & CI/CD Pipeline") or [{}])[0]
d4 = lab4.get("description") or ""
if "no local fallback" in d4:
    ok("Lab 4 states there is no local fallback for the quota")
else:
    warn("Lab 4 does not state the no-local-fallback constraint")

# ── 6. Retired-gate / stale-figure sweep across ALL assignments ─────────────
#
# Added after a live push shipped "AUC-ROC >= 0.72" to students -- a gate
# retired 2026-08-02 because it failed on 58% of splits. The targeted checks
# above only look at things we deliberately changed, so they missed it. This
# sweep looks for things that must no longer appear ANYWHERE.
print("\n── Retired content sweep (all assignments) ──")
RETIRED = [
    (r"AUC[- ]?ROC\s*(&ge;|>=|≥)\s*0\.72", "retired absolute AUC 0.72 gate"),
    (r"(&ge;|>=|≥)\s*0\.03\s*(lift|AUC)", "retired fixed 0.03 lift gate"),
    (r"[Tt]rain freely",                      "'train freely' - training quota is 0 by default"),
    (r"5 stages",                             "superseded '5 stages' wording (now 5 phases)"),
    (r"0\.7696|0\.7233|0\.6833|0\.3106",     "hardcoded reference metric (XGBoost-version dependent)"),
    (r"1,200[- ]customer",                    "retired 1,200-customer dataset"),
    (r"242 \+ 188|430 DPU",                   "DPU-s as a point value (measured range is 380-502)"),
]
found_any = False
for a in assigns:
    desc = a.get("description") or ""
    for pat, label in RETIRED:
        if re.search(pat, desc):
            bad(f"{a['name']}: {label}")
            found_any = True
if not found_any:
    ok("no retired gates or stale figures in any assignment description")

# ── Summary ─────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print(f"PASS {len(PASS)}   WARN {len(WARN)}   FAIL {len(FAIL)}")
if FAIL:
    print("\nFAILURES:")
    for f in FAIL:
        print("  -", f)
    sys.exit(1)
print("\nAll checks passed." if not WARN else "\nNo failures; review warnings above.")
