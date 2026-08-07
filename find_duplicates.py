#!/usr/bin/env python3
"""Find every duplicate in the Canvas course, of every kind. Read-only.

Written because duplicates kept being reported after targeted fixes, and each
fix addressed one mechanism inferred from partial evidence. This looks at all
of them at once so the next fix is aimed at what is actually there.

Canvas quirk worth knowing: a Quiz also appears in /assignments as a shadow
assignment with the same title. That is normal and is NOT a duplicate; this
script accounts for it rather than reporting it.

    python find_duplicates.py
"""

import os
import sys
from collections import defaultdict

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pipeline.canvas_api import CanvasAPI  # noqa: E402

cfg = yaml.safe_load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                       "course_config.yaml")))
tok = os.environ.get("CANVAS_API_TOKEN", "").strip().strip('"').strip("'")
if not tok:
    sys.exit("Set CANVAS_API_TOKEN first.")
api = CanvasAPI(cfg["canvas"]["base_url"],
                os.environ.get("CANVAS_COURSE_ID") or cfg["canvas"]["course_id"], tok)

found = 0


def report(kind, groups, fmt):
    """groups: {identity: [objects]}"""
    global found
    dupes = {k: v for k, v in groups.items() if len(v) > 1}
    if not dupes:
        print(f"  OK    {kind}: no duplicates ({len(groups)} unique)")
        return
    print(f"  DUPES {kind}: {len(dupes)} identity/identities duplicated")
    for k, v in sorted(dupes.items(), key=lambda x: -len(x[1])):
        found += len(v) - 1
        print(f"          {len(v)}x  {fmt(v[0])}")
        print(f"                ids: {[o.get('id') for o in v]}")


print(f"Scanning {cfg['canvas']['base_url']}/courses/{api.course_id}\n")

# ── Assignment groups ───────────────────────────────────────────────────────
groups = api._get_all("/assignment_groups")
g = defaultdict(list)
for x in groups:
    g[x["name"]].append(x)
report("assignment groups", g, lambda o: f"{o['name']} (weight {o.get('group_weight')})")

# ── Quizzes ─────────────────────────────────────────────────────────────────
quizzes = api._get_all("/quizzes")
q = defaultdict(list)
for x in quizzes:
    q[x["title"]].append(x)
report("quizzes", q, lambda o: o["title"])
quiz_titles = {x["title"] for x in quizzes}

# ── Assignments (excluding quiz shadows) ────────────────────────────────────
assigns = api._get_all("/assignments")
a = defaultdict(list)
shadow = 0
for x in assigns:
    if x["name"] in quiz_titles and x.get("quiz_id"):
        shadow += 1
        continue
    a[x["name"]].append(x)
report("assignments", a, lambda o: f"{o['name']} ({o.get('points_possible')} pts)")
print(f"        ({shadow} quiz shadow assignment(s) excluded — normal)")

# ── Modules ─────────────────────────────────────────────────────────────────
mods = api._get_all("/modules")
m = defaultdict(list)
for x in mods:
    m[x["name"]].append(x)
report("modules", m, lambda o: o["name"])

# ── Module items, per module ────────────────────────────────────────────────
print()
item_dupes = 0
for mod in mods:
    items = api._get_all(f"/modules/{mod['id']}/items?per_page=100")
    per = defaultdict(list)
    for it in items:
        ident = ("Page", it.get("page_url")) if it.get("type") == "Page" \
                else (it.get("type"), it.get("content_id"))
        per[ident].append(it)
    d = {k: v for k, v in per.items() if len(v) > 1}
    if d:
        print(f"  DUPES module items in '{mod['name']}': {len(items)} item(s), "
              f"{sum(len(v) - 1 for v in d.values())} redundant")
        for k, v in d.items():
            item_dupes += len(v) - 1
            print(f"          {len(v)}x  {v[0].get('title','?')[:52]}")
if not item_dupes:
    print(f"  OK    module items: no duplicates across {len(mods)} module(s)")
found += item_dupes

# ── Pages ───────────────────────────────────────────────────────────────────
pages = api._get_all("/pages")
p = defaultdict(list)
for x in pages:
    p[x["title"]].append(x)
report("pages", p, lambda o: o["title"])

# ── Files, by name within folder ────────────────────────────────────────────
folders = {f["id"]: f["full_name"] for f in api._get_all("/folders")}
files = api._get_all("/files")
f_ = defaultdict(list)
for x in files:
    f_[(folders.get(x["folder_id"], "?"), x["display_name"])].append(x)
report("files", f_, lambda o: f"{folders.get(o['folder_id'],'?')}/{o['display_name']}")

print(f"\n{'=' * 60}")
print(f"TOTAL redundant objects: {found}")
if found:
    print("\nNext: python dedupe_course.py            (module items)")
    print("      python fix_assignment_groups.py    (groups)")
    print("      python fix_stray_guides.py         (misplaced guide files)")
    print("\nAnything not covered by those, paste this output and I will handle it.")
