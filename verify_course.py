#!/usr/bin/env python3
"""Verify what build_course.py actually did, against the live Canvas API.

Why this exists
---------------
The pipeline prints a check mark for every write it attempts, and cannot see
the failures that have actually bitten this course:

  * A **duplicate** assignment. `ensure_*` matches on NAME, so an item created
    earlier under a slightly different name is not updated -- it is joined by a
    second copy, silently.
  * A **retired gate** surviving in a description. On 2026-08-04 a live push
    shipped "AUC-ROC >= 0.72" to students, retired two days earlier. Every
    targeted check passed, because none of them was looking for it.
  * A guide link that **fell back to plain text** because the upload had not
    happened when the description was generated. Reads fine, goes nowhere.
  * An assignment created but placed in **no module**, because module lookup is
    by exact name and a mismatch fails silently by design of the Canvas API.

Run it with the same environment as the build:

    export CANVAS_API_TOKEN="1234~..."
    python verify_course.py

Exits non-zero if anything FAILs.
"""

import os
import pathlib
import re
import sys

import requests
import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pipeline.canvas_api import CanvasAPI  # noqa: E402

CONFIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "course_config.yaml")

PASS, FAIL, WARN = [], [], []


def ok(m, d=""):   PASS.append(m); print(f"  PASS  {m}" + (f"  [{d}]" if d else ""))
def bad(m, d=""):  FAIL.append(m); print(f"  FAIL  {m}" + (f"  [{d}]" if d else ""))
def warn(m, d=""): WARN.append(m); print(f"  WARN  {m}" + (f"  [{d}]" if d else ""))


# Content that must no longer appear anywhere a student can read it. Each of
# these was live at some point; the sweep is deliberately broader than the
# targeted checks, because the targeted checks are what missed the 0.72 gate.
RETIRED = [
    (r"AUC[- ]?ROC\s*(&ge;|>=|≥)\s*0\.72", "retired absolute AUC 0.72 gate"),
    (r"(&ge;|>=|≥)\s*0\.03\s*(lift|AUC)",   "retired fixed 0.03 lift gate"),
    (r"[Tt]rain freely",                    "'train freely' — training quota is 0 by default"),
    (r"5 stages",                           "superseded '5 stages' wording"),
    (r"0\.7696|0\.7233|0\.6833|0\.3106",    "hardcoded reference metric (XGBoost-version dependent)"),
    (r"1,200[- ]customer",                  "retired 1,200-customer dataset"),
    (r"242 \+ 188|430 DPU",                 "DPU-s as a point value (measured range is 380-502)"),
]

FALLBACK = "see the course repository"


def preflight(api, cfg):
    """Fail with a diagnosis, not a traceback."""
    r = requests.get(f"{api.base_url}/api/v1/users/self", headers=api.headers)
    if r.status_code == 401:
        sys.exit(
            f"ERROR: Canvas rejected the token ({len(api.headers.get('Authorization','')) - 7} chars).\n"
            "       Most often it is simply not exported in THIS shell.\n"
            "       Otherwise it has expired, or was truncated on paste.\n"
            "       New token: avatar -> Account -> Settings -> Approved Integrations."
        )
    r.raise_for_status()
    print(f"Authenticated as {r.json().get('name','?')}")
    c = requests.get(api.root, headers=api.headers)
    if c.status_code == 404:
        sys.exit(f"ERROR: course {cfg['canvas']['course_id']} not found, or the token cannot see it.")
    c.raise_for_status()
    print(f"Course: {c.json().get('name','?')}\n")


def main():
    cfg = yaml.safe_load(open(CONFIG))
    token = os.environ.get("CANVAS_API_TOKEN", "").strip().strip('"').strip("'")
    if not token:
        sys.exit('ERROR: CANVAS_API_TOKEN is empty or unset in this shell.\n'
                 '       That is what produces Canvas\'s "Invalid access token."')
    course_id = os.environ.get("CANVAS_COURSE_ID", "").strip() or cfg["canvas"]["course_id"]
    api = CanvasAPI(cfg["canvas"]["base_url"], course_id, token)

    print(f"Verifying {cfg['canvas']['base_url']}/courses/{course_id}\n")
    preflight(api, cfg)

    assigns = api._get_all("/assignments")
    by_name = {}
    for a in assigns:
        by_name.setdefault(a["name"], []).append(a)

    lab_names     = [f"Lab {l['number']} — {l['title']}" for l in cfg["labs"]]
    prelab_names  = [p["title"] for p in cfg.get("prelabs", [])]
    academy_names = [a["title"] for a in cfg.get("academy", [])]

    # ── 1. Duplicates — the migration's biggest risk ────────────────────────
    print("── Duplicates ──")
    dupes = {n: v for n, v in by_name.items() if len(v) > 1}
    if dupes:
        for n, v in dupes.items():
            bad(f"DUPLICATED x{len(v)}: {n}", ",".join(str(x['id']) for x in v))
    else:
        ok(f"no duplicate assignment names ({len(assigns)} total)")

    # ── 2. Expected items exist ─────────────────────────────────────────────
    print("\n── Expected assignments ──")
    for n in lab_names + prelab_names + academy_names:
        hits = by_name.get(n, [])
        if not hits:
            bad(f"missing: {n}")
        elif len(hits) == 1:
            ok(f"exactly one: {n}", f"id={hits[0]['id']}")

    # ── 3. Lab descriptions are generated and linked ────────────────────────
    print("\n── Lab descriptions ──")
    for l in cfg["labs"]:
        n = f"Lab {l['number']} — {l['title']}"
        for a in by_name.get(n, []):
            d = a.get("description") or ""
            if "Point Breakdown" not in d:
                bad(f"Lab {l['number']} has no generated points table")
            if a.get("points_possible") != l["points"]:
                bad(f"Lab {l['number']} points_possible={a.get('points_possible')}",
                    f"expected {l['points']}")
            if FALLBACK in d:
                bad(f"Lab {l['number']} guide link fell back to plain text",
                    "guides were not uploaded before the description was generated")
            elif re.search(r"/courses/\d+/files/\d+", d):
                ok(f"Lab {l['number']} links to an uploaded guide")
            else:
                warn(f"Lab {l['number']} has no guide link")
            if "{{" in d:
                bad(f"Lab {l['number']} contains an UNRESOLVED template token")

    # ── 4. Pre-labs ─────────────────────────────────────────────────────────
    print("\n── Pre-labs ──")
    for p in cfg.get("prelabs", []):
        for a in by_name.get(p["title"], []):
            if a.get("points_possible") not in (0, 0.0):
                warn(f"Pre-Lab {p['number']} points={a.get('points_possible')}", "expected 0")
            else:
                ok(f"Pre-Lab {p['number']} is 0 points")
            if (a.get("due_at") or "").startswith(("2026-09-30", "2026-10-01")):
                ok(f"Pre-Lab {p['number']} due date set", a["due_at"])
            else:
                warn(f"Pre-Lab {p['number']} unexpected due date", str(a.get("due_at")))
            d = a.get("description") or ""
            if FALLBACK in d or not re.search(r"/courses/\d+/files/\d+", d):
                bad(f"Pre-Lab {p['number']} does not link to its uploaded guide")
            else:
                ok(f"Pre-Lab {p['number']} links to its guide")

    # ── 5. Retired content, across everything ───────────────────────────────
    print("\n── Retired content sweep ──")
    found = False
    for a in assigns:
        d = a.get("description") or ""
        for pat, label in RETIRED:
            if re.search(pat, d):
                bad(f"{a['name']}: {label}"); found = True
    # Page bodies too. The syllabus is generated from config and is the one
    # place a stale figure could hide outside an assignment.
    for title in (api.get_pages() or {}):
        r = api._get(f"/pages/{requests.utils.quote(title, safe='')}")
        body = (r.json().get("body") or "") if r.ok else ""
        for pat, label in RETIRED:
            if re.search(pat, body):
                bad(f"page '{title}': {label}"); found = True
    if not found:
        ok("no retired gates or stale figures in any assignment or page")

    # ── 6. Module placement AND duplicate module items ──────────────────────
    #
    # Duplicates here are invisible in the build output: add_module_item was a
    # bare POST, so every run appended another copy of every link. Checking
    # only "is it in a module" would pass while a student saw it four times.
    print("\n── Module placement ──")
    placed = {}
    dupe_items = 0
    for name, mid in (api.get_modules() or {}).items():
        items = api._get_all(f"/modules/{mid}/items")
        seen = {}
        for it in items:
            ident = ("Page", it.get("page_url")) if it.get("type") == "Page" \
                    else (it.get("type"), it.get("content_id"))
            seen.setdefault(ident, []).append(it)
            if it.get("type") == "Assignment":
                placed.setdefault(it.get("title"), []).append(name)
        for ident, group in seen.items():
            if len(group) > 1:
                dupe_items += len(group) - 1
                bad(f"module '{name}': {len(group)}x {group[0].get('title','?')[:44]}",
                    "duplicate module items — run dedupe_course.py")
    if not dupe_items:
        ok("no duplicate module items in any module")
    for n in lab_names + prelab_names + academy_names:
        where = sorted(set(placed.get(n, [])))
        if where:
            ok(f"in module: {n}", "; ".join(where))
        else:
            bad(f"{n} is in NO module", "created but orphaned — module name lookup missed")

    # ── 7. Files ────────────────────────────────────────────────────────────
    print("\n── Course files ──")
    files = api._get_all("/files?per_page=100")
    folders = {f["id"]: f["full_name"] for f in api._get_all("/folders?per_page=100")}
    # Match the folder EXACTLY, not as a substring. "Lab Guides" is a
    # substring of "Pre-Lab Guides", so `key in folder` put every pre-lab
    # guide into the Lab Guides bucket as well. That reported
    #   FAIL  Lab Guides: 9 file(s), expected 7
    # against a course where both folders were correct -- 7 lab guides plus
    # the 2 pre-lab guides double-counted. clean_lab_guides.py got this right
    # with endswith() and reported 0 strays, which is how the contradiction
    # surfaced. A verifier that cries wolf is worse than no verifier: the next
    # person reaches for a delete script against a clean course.
    # These must be the folder names the pipeline ACTUALLY creates -- see
    # get_or_create_folder() in stage1_structure.py and stage3_starters.py.
    # The starter-kit folder is "Lab Starter Kits", not "Starter Kits"; the
    # old substring match happened to catch it, an exact match on the wrong
    # name would silently report "stage 3 may not have run" on a good course.
    def in_folder(f, key):
        return folders.get(f["folder_id"], "").endswith(f"/{key}")

    counts = {}
    for f in files:
        for key in ("Lab Guides", "Pre-Lab Guides", "Lab Starter Kits"):
            if in_folder(f, key):
                counts[key] = counts.get(key, 0) + 1
    # Check MEMBERSHIP, not count. A count tells you something is wrong; the
    # expected filenames tell you which file and in which direction.
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from pipeline import lab_content

    expected_files = {
        "Lab Guides": {f"{lab_content.parse_lab(n)['path'].stem}.html"
                       for n in lab_content.LAB_FILES},
        "Pre-Lab Guides": {f"{pathlib.Path(pl['guide']).stem}.html"
                           for pl in cfg.get("prelabs", [])},
    }
    for key, want in expected_files.items():
        have = {f["display_name"] for f in files if in_folder(f, key)}
        missing, extra = want - have, have - want
        if not missing and not extra:
            ok(f"{key}: exactly the {len(want)} expected file(s)")
            continue
        bad(f"{key}: {len(have)} file(s), expected {len(want)}")
        for n in sorted(missing):
            print(f"          MISSING  {n}")
        for n in sorted(extra):
            print(f"          STRAY    {n}")
    if counts.get("Lab Starter Kits", 0) > 0:
        ok(f"Lab Starter Kits: {counts['Lab Starter Kits']} file(s)")
    else:
        warn("Lab Starter Kits: no files found", "stage 3 may not have run")

    # ── 7b. Chapter readings and starter kits ───────────────────────────────
    #
    # These were not checked at all until 2026-08-05, which is why "everything
    # uploaded?" could not be answered: stages 2 and 3 could fail silently and
    # nothing in the report would say so.
    print("\n── Chapter readings (stage 2) ──")
    want_pdfs = {ch["pdf"] for ch in cfg.get("chapters", [])}
    have_pdfs = {f["display_name"] for f in files
                 if in_folder(f, "Readings")}
    if not have_pdfs:
        bad(f"no Readings folder or no files in it",
            f"expected {len(want_pdfs)} chapter PDF(s) — stage 2 did not complete")
    else:
        missing, extra = want_pdfs - have_pdfs, have_pdfs - want_pdfs
        if not missing and not extra:
            ok(f"all {len(want_pdfs)} chapter PDFs present")
        else:
            bad(f"Readings: {len(have_pdfs)} file(s), expected {len(want_pdfs)}")
            for n in sorted(missing):
                print(f"          MISSING  {n}")
            for n in sorted(extra):
                print(f"          STRAY    {n}")

    print("\n── Presentations (stage 6) ──")
    want_p = {pathlib.Path(d["file"]).name for d in cfg.get("presentations", [])}
    have_p = {f["display_name"] for f in files
              if in_folder(f, "Presentations")}
    if not want_p:
        warn("no presentations configured")
    else:
        miss_p, extra_p = want_p - have_p, have_p - want_p
        if not miss_p and not extra_p:
            ok(f"all {len(want_p)} lecture deck(s) present")
        else:
            bad(f"Presentations: {len(have_p)} file(s), expected {len(want_p)}")
            for n in sorted(miss_p):
                print(f"          MISSING  {n}")
            for n in sorted(extra_p):
                print(f"          STRAY    {n}")

    print("\n── Starter kits (stage 3) ──")
    # `or ""` not a default: labs 5-7 have starter_kit set to null, and
    # dict.get(k, "") returns None for an explicit null, which then blows up
    # path joining.
    kit_labs = [l["number"] for l in cfg["labs"]
                if (l.get("starter_kit") or "")
                and (pathlib.Path(__file__).parent / l["starter_kit"]).is_dir()]
    want_kits = {f"Lab{n}-Starter-Kit.zip" for n in kit_labs}
    have_kits = {f["display_name"] for f in files
                 if in_folder(f, "Lab Starter Kits")}
    missing_k, extra_k = want_kits - have_kits, have_kits - want_kits
    if want_kits and not missing_k and not extra_k:
        ok(f"all {len(want_kits)} starter kit zip(s) present")
    else:
        bad(f"Starter Kits: {len(have_kits)} file(s), expected {len(want_kits)}")
        for n in sorted(missing_k):
            print(f"          MISSING  {n}")
        for n in sorted(extra_k):
            print(f"          STRAY    {n}")

    # ── 8. Quizzes and their questions ──────────────────────────────────────
    print("\n── Quizzes ──")
    quizzes = api.get_quizzes() or {}
    expected_q = len(cfg.get("quizzes", []))
    (ok if len(quizzes) == expected_q else bad)(
        f"{len(quizzes)} quiz shell(s)", f"expected {expected_q}")
    empty = [t for t, qid in quizzes.items() if not api.get_quiz_questions(qid)]
    if empty:
        bad(f"{len(empty)} quiz(zes) have NO questions", "run: python build_course.py --stage 4")
        for t in empty[:4]:
            print(f"          - {t}")
    elif quizzes:
        ok("every quiz has questions")

    # ── 8b. Empty weighted groups ───────────────────────────────────────────
    # Canvas EXCLUDES a weighted group with no assignments and scales the rest
    # up, so an empty group silently redistributes its weight.
    print("\n── Grading weights ──")
    groups = api._get_all("/assignment_groups")
    gid_name = {g["id"]: g["name"] for g in groups}
    populated = set()
    for a in assigns:
        populated.add(gid_name.get(a.get("assignment_group_id")))
    for g in cfg["grading"]["groups"]:
        live = [x for x in groups if x["name"] == g["name"]]
        if not live:
            bad(f"group missing: {g['name']}")
            continue
        if live[0].get("group_weight") != g["weight"]:
            bad(f"{g['name']} weight is {live[0].get('group_weight')}",
                f"expected {g['weight']}")
        elif g["name"] not in populated:
            bad(f"{g['name']} has weight {g['weight']}% but NO assignments",
                "Canvas will drop this weight and scale the others up")
        else:
            ok(f"{g['name']}: {g['weight']}%, populated")
    total = sum(g["weight"] for g in cfg["grading"]["groups"])
    (ok if total == 100 else bad)(f"weights total {total}%", "expected 100")

    # ── 9. Pages ────────────────────────────────────────────────────────────
    print("\n── Pages ──")
    pages = api.get_pages() or {}
    for t in ("Course Syllabus", "NorthStar Retail — Case Overview",
              "AWS Educate Setup Guide", "Office Hours"):
        (ok if t in pages else bad)(f"page present: {t}")

    print("\n" + "=" * 60)
    print(f"PASS {len(PASS)}   WARN {len(WARN)}   FAIL {len(FAIL)}")
    if FAIL:
        print("\nFAILURES:")
        for f in FAIL:
            print("  -", f)
        sys.exit(1)
    print("\nAll checks passed." if not WARN else "\nNo failures; review warnings above.")


if __name__ == "__main__":
    main()
