#!/usr/bin/env python3
"""Remove duplicate module items from the Canvas course.

add_module_item() and add_module_page() were bare POSTs with no existence
check, so every build_course.py run appended another copy of every link. Four
runs meant four identical entries per assignment in each module.

Keeps the LOWEST id of each duplicate group -- the original, whose position in
the module is the one you arranged -- and deletes the rest. Assignments, pages,
files and quizzes themselves are untouched; only the module *links* are removed.

    python dedupe_course.py            # show what would go
    python dedupe_course.py --apply
"""
import os, sys, yaml, requests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pipeline.canvas_api import CanvasAPI

APPLY = "--apply" in sys.argv
cfg = yaml.safe_load(open("course_config.yaml"))
tok = os.environ.get("CANVAS_API_TOKEN", "").strip()
if not tok:
    sys.exit("Set CANVAS_API_TOKEN first.")
api = CanvasAPI(cfg["canvas"]["base_url"], cfg["canvas"]["course_id"], tok)


def key(it):
    """Identity of a module item: what it points at, not what it is called."""
    if it.get("type") == "Page":
        return ("Page", it.get("page_url"))
    return (it.get("type"), it.get("content_id"))


modules = api.get_modules()
total_dupes = 0
plan = []

for name, mid in modules.items():
    items = api.get_module_items(mid)
    groups = {}
    for it in items:
        groups.setdefault(key(it), []).append(it)
    dupes = {k: v for k, v in groups.items() if len(v) > 1}
    if not dupes:
        continue
    print(f"\n── {name}")
    for k, v in dupes.items():
        v.sort(key=lambda x: x["id"])
        keep, drop = v[0], v[1:]
        total_dupes += len(drop)
        title = keep.get("title", "?")
        print(f"  {len(v)}x  {title[:56]}")
        print(f"        keep id={keep['id']}, delete {[d['id'] for d in drop]}")
        plan.extend((mid, d["id"], title) for d in drop)

print(f"\n── Summary ──")
print(f"  {len(modules)} module(s) scanned")
print(f"  {total_dupes} duplicate module item(s) to remove")

if not total_dupes:
    print("  Nothing to do.")
    sys.exit(0)

if not APPLY:
    print("\nDry run. Re-run with --apply to delete.")
    sys.exit(0)

print("\n── Applying ──")
ok = fail = 0
for mid, item_id, title in plan:
    r = requests.delete(f"{api.root}/modules/{mid}/items/{item_id}",
                        headers=api.headers)
    if r.ok:
        ok += 1
    else:
        fail += 1
        print(f"  FAILED {title[:44]} ({item_id}): {r.status_code}")
print(f"  deleted {ok}, failed {fail}")
print("\nDone. Re-run: python verify_course.py")
