#!/usr/bin/env python3
"""Remove non-lab-guide files from the Lab Guides folder.

Single purpose, verbose about what it sees, so if it does nothing you can tell
why. Deletes a file only when an identical name exists in Pre-Lab Guides.

    python clean_lab_guides.py            # show
    python clean_lab_guides.py --apply
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

folders = {f["id"]: f["full_name"] for f in api._get_all("/folders")}
files = api._get_all("/files")

expected = {f"{lab_content.parse_lab(n)['path'].stem}.html"
            for n in lab_content.LAB_FILES}

in_lab, in_prelab = [], set()
for f in files:
    full = folders.get(f["folder_id"], "")
    if full.endswith("/Lab Guides"):
        in_lab.append(f)
    elif full.endswith("/Pre-Lab Guides"):
        in_prelab.add(f["display_name"])

print(f"── Lab Guides contains {len(in_lab)} file(s) ──")
for f in sorted(in_lab, key=lambda x: x["display_name"]):
    n = f["display_name"]
    tag = "expected" if n in expected else "NOT a lab guide"
    print(f"  id={f['id']:<10} {tag:<16} {n}")

print(f"\n── Pre-Lab Guides contains {len(in_prelab)} file(s) ──")
for n in sorted(in_prelab):
    print(f"  {n}")

strays = [f for f in in_lab if f["display_name"] not in expected]
print(f"\n── {len(strays)} stray(s) in Lab Guides ──")
if not strays:
    print("  none — folder is clean")
    sys.exit(0)

deletable = []
for f in strays:
    n = f["display_name"]
    safe = n in in_prelab
    print(f"  {n}")
    print(f"      copy in Pre-Lab Guides: {safe}  -> {'delete' if safe else 'WITHHOLD'}")
    if safe:
        deletable.append(f)

if not deletable:
    print("\n  Nothing safely deletable.")
    sys.exit(0)
if not APPLY:
    print(f"\nDry run. Re-run with --apply to delete {len(deletable)} file(s).")
    sys.exit(0)

print("\n── Deleting ──")
for f in deletable:
    r = requests.delete(f"{api.base_url}/api/v1/files/{f['id']}", headers=api.headers)
    print(f"  {'deleted' if r.ok else 'FAILED ' + str(r.status_code)}  {f['display_name']}")
print("\nDone. Re-run: python verify_course.py")
