#!/usr/bin/env python3
"""Read-only survey of the live Canvas course. Writes nothing.

Written on 2026-08-05 after stage 1 deleted the default "Assignments" group.
Canvas destroys the assignments inside a deleted group unless the request says
where to move them, and it did not. This reports what is actually there now.
"""
import os, sys, yaml, requests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pipeline.canvas_api import CanvasAPI

cfg = yaml.safe_load(open("course_config.yaml"))
tok = os.environ.get("CANVAS_API_TOKEN", "").strip()
if not tok:
    sys.exit("Set CANVAS_API_TOKEN first.")
api = CanvasAPI(cfg["canvas"]["base_url"], cfg["canvas"]["course_id"], tok)

print("── Assignment groups ──")
groups = api._get_all("/assignment_groups")
gid_name = {g["id"]: g["name"] for g in groups}
for g in groups:
    print(f"  {g['id']:>8}  {g['name']:<22} weight={g.get('group_weight')}")

print("\n── Assignments (what survived) ──")
assigns = api._get_all("/assignments")
print(f"  {len(assigns)} total\n")
for a in sorted(assigns, key=lambda x: x["name"]):
    grp = gid_name.get(a.get("assignment_group_id"), "?")
    print(f"  {a['points_possible']!s:>5} pts  [{grp:<16}]  {a['name']}")

expected = [f"Lab {l['number']} — {l['title']}" for l in cfg["labs"]] + \
           [p["title"] for p in cfg.get("prelabs", [])]
have = {a["name"] for a in assigns}
missing = [e for e in expected if e not in have]
print("\n── Expected but MISSING ──")
print("  none" if not missing else "")
for m in missing:
    print("  !!", m)

print("\n── Quizzes ──")
qz = api.get_quizzes() or {}
print(f"  {len(qz)} quiz shell(s)")

print("\n── Files ──")
folders = {f["id"]: f["full_name"] for f in api._get_all("/folders")}
files = api._get_all("/files")
counts = {}
for f in files:
    counts[folders.get(f["folder_id"], "?")] = counts.get(folders.get(f["folder_id"], "?"), 0) + 1
for k, v in sorted(counts.items()):
    print(f"  {v:>4}  {k}")
if not files:
    print("  (none)")
