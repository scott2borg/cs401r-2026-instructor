#!/usr/bin/env python3
"""Consolidate the duplicate "Assignments" groups created by the nested-payload bug.

Seven groups, all named "Assignments", all weight 0.0, all created by
ensure_assignment_group sending {"assignment_group": {...}} to an endpoint that
wants flat params. Canvas took no name and no weight and used its defaults.

This creates the four intended groups correctly, moves every assignment into
the right one, then deletes the empty duplicates -- passing move_assignments_to
so nothing can be destroyed even if something is still filed there.

    python fix_assignment_groups.py            # show the plan, change nothing
    python fix_assignment_groups.py --apply    # do it
"""
import os, sys, yaml
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pipeline.canvas_api import CanvasAPI

APPLY = "--apply" in sys.argv
cfg = yaml.safe_load(open("course_config.yaml"))
tok = os.environ.get("CANVAS_API_TOKEN", "").strip()
if not tok:
    sys.exit("Set CANVAS_API_TOKEN first.")
api = CanvasAPI(cfg["canvas"]["base_url"], cfg["canvas"]["course_id"], tok)


def target_group(name: str) -> str:
    if name.startswith(("Lab ", "Pre-Lab ")):             return "Labs"
    if name.startswith("Quiz "):                          return "Reading Quizzes"
    if "Final Project" in name or "Team Sign-Up" in name: return "Final Project"
    if "AWS Academy" in name:                             return "AWS Academy Courses"
    return "Labs"


groups   = api._get_all("/assignment_groups")
assigns  = api._get_all("/assignments")
wanted   = {g["name"]: g["weight"] for g in cfg["grading"]["groups"]}
by_name  = {}
for g in groups:
    by_name.setdefault(g["name"], []).append(g)

print(f"── Current state ──\n  {len(groups)} group(s), {len(assigns)} assignment(s)")
for n, gs in by_name.items():
    print(f"    {n!r} x{len(gs)}  ids={[g['id'] for g in gs]}")

print("\n── Plan ──")
for n, w in wanted.items():
    have = [g for g in by_name.get(n, []) if g.get("group_weight")]
    print(f"  {'keep  ' if have else 'create'}  {n} (weight {w})")
moves = {}
for a in assigns:
    moves.setdefault(target_group(a["name"]), []).append(a["name"])
for g, names in moves.items():
    print(f"  move    {len(names):>2} assignment(s) -> {g}")
stale = [g for g in groups if g["name"] not in wanted]
print(f"  delete  {len(stale)} stale group(s) named {sorted({g['name'] for g in stale})}"
      f" (assignments moved, never destroyed)")

empty = [n for n in wanted if not moves.get(n)]
if empty:
    print("\n  ⚠ WEIGHTED GROUPS WITH NO ASSIGNMENTS: " + ", ".join(empty))
    print("    Canvas EXCLUDES an empty group from weighting and scales the rest up.")
    remaining = sum(w for n, w in wanted.items() if n not in empty)
    for n, w in wanted.items():
        if n not in empty:
            print(f"      {n}: {w}% would effectively become {w / remaining * 100:.1f}%")
    print("    Add at least one assignment to each empty group, or its weight vanishes.")

if not APPLY:
    print("\nDry run. Re-run with --apply to execute.")
    sys.exit(0)

print("\n── Applying ──")
gid = {}
for i, (n, w) in enumerate(wanted.items(), 1):
    existing = [g for g in by_name.get(n, []) if g.get("group_weight")]
    if existing:
        g = existing[0]; gid[n] = g["id"]
        if float(g.get("group_weight") or 0) != float(w):
            api._put(f"/assignment_groups/{g['id']}", {"group_weight": w})
            print(f"  reweighted {n} ({g['id']}) {g.get('group_weight')} -> {w}")
        else:
            print(f"  kept   {n} ({gid[n]}) weight={g.get('group_weight')}")
    else:
        new = api._post("/assignment_groups",
                        {"name": n, "group_weight": w, "position": i})
        if new and new.get("name") == n:
            gid[n] = new["id"]; print(f"  created {n} ({new['id']}) weight={new.get('group_weight')}")
        else:
            sys.exit(f"  FAILED to create {n}: {new}")

for a in assigns:
    want = gid.get(target_group(a["name"]))
    if want and a.get("assignment_group_id") != want:
        api._put(f"/assignments/{a['id']}", {"assignment": {"assignment_group_id": want}})
        print(f"  moved  {a['name'][:52]} -> {target_group(a['name'])}")

for g in stale:
    api.delete_assignment_group(g["id"], move_to=gid["Labs"])
    print(f"  deleted stale group {g['id']}")

api.set_weighted_grading(cfg["grading"]["weighted"])
print("\nDone. Re-run: python survey_course.py")
