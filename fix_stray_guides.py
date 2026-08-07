#!/usr/bin/env python3
"""Remove files from the guide folders that do not belong there.

The two pre-lab guides ended up in BOTH "Lab Guides" and "Pre-Lab Guides"
during the 2026-08-05 migration -- correct copies in the right folder, stray
duplicates in the wrong one. Current code cannot produce this (labs and
pre-labs are uploaded to separate folder ids), so these are historical.

Deletes ONLY files whose names are not in the expected set for their folder,
and only after confirming the same name exists in its correct folder.

    python fix_stray_guides.py            # show what would go
    python fix_stray_guides.py --apply
"""
import os, pathlib, sys, yaml, requests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pipeline.canvas_api import CanvasAPI
from pipeline import lab_content

APPLY = "--apply" in sys.argv
cfg = yaml.safe_load(open("course_config.yaml"))
tok = os.environ.get("CANVAS_API_TOKEN", "").strip()
if not tok:
    sys.exit("Set CANVAS_API_TOKEN first.")
api = CanvasAPI(cfg["canvas"]["base_url"], cfg["canvas"]["course_id"], tok)

expected = {
    "Lab Guides": {f"{lab_content.parse_lab(n)['path'].stem}.html"
                   for n in lab_content.LAB_FILES},
    "Pre-Lab Guides": {f"{pathlib.Path(pl['guide']).stem}.html"
                       for pl in cfg.get("prelabs", [])},
}

folders = {f["id"]: f["full_name"] for f in api._get_all("/folders")}
files = api._get_all("/files")

# name -> folders it correctly lives in
correct_home = {}
for folder, names in expected.items():
    for n in names:
        correct_home[n] = folder

strays = []
for f in files:
    folder = folders.get(f["folder_id"], "")
    key = next((k for k in expected if k in folder), None)
    if not key:
        continue
    if f["display_name"] in expected[key]:
        continue
    home = correct_home.get(f["display_name"])
    safe = any(g["display_name"] == f["display_name"]
               and home and home in folders.get(g["folder_id"], "")
               for g in files)
    strays.append((f, key, home, safe))

print("── Strays ──")
if not strays:
    print("  none — guide folders are clean")
    sys.exit(0)
for f, key, home, safe in strays:
    print(f"  {f['display_name']}")
    print(f"     sitting in : {key}")
    print(f"     belongs in : {home or 'UNKNOWN — not an expected guide at all'}")
    print(f"     safe copy exists in correct folder: {safe}")

deletable = [s for s in strays if s[3]]
risky = [s for s in strays if not s[3]]
print(f"\n  {len(deletable)} safe to delete, {len(risky)} withheld")
for f, key, home, _ in risky:
    print(f"    WITHHELD {f['display_name']} — no confirmed copy elsewhere; "
          f"move it manually rather than lose it")

if not APPLY:
    print("\nDry run. Re-run with --apply to delete the safe ones.")
    sys.exit(0)

for f, key, home, _ in deletable:
    r = requests.delete(f"{api.base_url}/api/v1/files/{f['id']}", headers=api.headers)
    print(f"  {'deleted' if r.ok else 'FAILED'} {f['display_name']} from {key}")
print("\nDone. Re-run: python verify_course.py")
