#!/usr/bin/env python3
"""Move files out of 'unfiled' into the folders they were meant to go to.

Every upload landed in 'unfiled' because canvas_api.upload_file sent
`folder_id` instead of `parent_folder_id`. Canvas ignored the unknown parameter
and used the default folder, returning a valid file id each time so nothing
reported a failure.

Moving is a PUT on each file -- far cheaper than re-uploading 216 MB.

    python fix_unfiled.py            # show the plan
    python fix_unfiled.py --apply
"""
import os, re, sys, yaml, requests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pipeline.canvas_api import CanvasAPI

APPLY = "--apply" in sys.argv
cfg = yaml.safe_load(open("course_config.yaml"))
tok = os.environ.get("CANVAS_API_TOKEN", "").strip()
if not tok:
    sys.exit("Set CANVAS_API_TOKEN first.")
api = CanvasAPI(cfg["canvas"]["base_url"], cfg["canvas"]["course_id"], tok)


def destination(name: str) -> str | None:
    """Which folder a file belongs in, from its name."""
    if re.match(r"CS-401R-4-F26-L\d{2}\.pptx$", name):        return "Presentations"
    if re.match(r"Ch\d{2}-.*\.pdf$", name):                   return "Readings"
    if re.match(r"Lab\d-Starter-Kit\.zip$", name):            return "Lab Starter Kits"
    if name.startswith("Pre-Lab ") and name.endswith(".html"):return "Pre-Lab Guides"
    if name.startswith("Lab_") and name.endswith(".html"):    return "Lab Guides"
    return None


folders = {f["full_name"]: f["id"] for f in api._get_all("/folders")}
files = api._get_all("/files")
unfiled = [f for f in files
           if "unfiled" in next((k for k, v in folders.items()
                                 if v == f["folder_id"]), "")]

print(f"── {len(unfiled)} file(s) in unfiled ──")
plan, unknown = [], []
for f in unfiled:
    dest = destination(f["display_name"])
    if not dest:
        unknown.append(f)
        continue
    fid = folders.get(f"course files/{dest}")
    if not fid:
        print(f"  ! destination folder missing: {dest}")
        continue
    plan.append((f, dest, fid))

by_dest = {}
for f, dest, _ in plan:
    by_dest.setdefault(dest, []).append(f["display_name"])
for dest, names in sorted(by_dest.items()):
    print(f"  {len(names):>3} -> {dest}")
if unknown:
    print(f"\n  {len(unknown)} file(s) with no destination rule (left alone):")
    for f in unknown[:12]:
        print(f"        {f['display_name']}")

if not APPLY:
    print("\nDry run. Re-run with --apply to move them.")
    sys.exit(0)

print("\n── Moving ──")
ok = fail = 0
for f, dest, fid in plan:
    r = requests.put(f"{api.base_url}/api/v1/files/{f['id']}",
                     headers=api.headers, json={"parent_folder_id": fid})
    if r.ok:
        ok += 1
    elif r.status_code == 409:
        # The real copy is already in the destination; this unfiled one is
        # redundant rather than un-movable. fix_leftovers.py removes it.
        fail += 1
        print(f"  SKIP   {f['display_name'][:44]} — already in {dest}, "
              f"unfiled copy is redundant")
    else:
        fail += 1
        print(f"  FAILED {f['display_name'][:44]}: {r.status_code} {r.text[:80]}")
print(f"  moved {ok}, failed {fail}")
print("\nDone. Re-run: python verify_course.py")
