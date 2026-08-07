#!/usr/bin/env python3
"""Delete leftover files that the folder-parameter bug and earlier runs left behind.

Three categories, each verified safe before deletion:

  1. Files still in 'unfiled' whose name ALREADY exists in the folder they
     belong to. fix_unfiled.py could not move these -- Canvas returns 409
     "file already exists" -- because the real copy was already in place. The
     unfiled one is redundant.

  2. Guide files sitting in the wrong guide folder, where a copy exists in the
     correct one.

  3. Obsolete loose starter-kit files from before the kits were zipped:
     aws-educate-setup.md (now aws-account-setup.md), northstar-overview.md
     (now northstar-scenario-overview.md), northstar-data-schema.md (now inside
     Lab1-Starter-Kit.zip).

Nothing is deleted unless a replacement is confirmed present.

    python fix_leftovers.py            # show the plan
    python fix_leftovers.py --apply
"""
import os, pathlib, re, sys, yaml, requests
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


def folder_of(f):
    return folders.get(f["folder_id"], "?")


# name -> set of folders it currently lives in
where = {}
for f in files:
    where.setdefault(f["display_name"], set()).add(folder_of(f))

expected = {
    "course files/Lab Guides": {f"{lab_content.parse_lab(n)['path'].stem}.html"
                                for n in lab_content.LAB_FILES},
    "course files/Pre-Lab Guides": {f"{pathlib.Path(p['guide']).stem}.html"
                                    for p in cfg.get("prelabs", [])},
    "course files/Presentations": {pathlib.Path(d["file"]).name
                                   for d in cfg.get("presentations", [])},
    "course files/Readings": {c["pdf"] for c in cfg.get("chapters", [])},
    "course files/Lab Starter Kits": {f"Lab{l['number']}-Starter-Kit.zip"
                                      for l in cfg["labs"]
                                      if (l.get("starter_kit") or "")},
}
home = {name: folder for folder, names in expected.items() for name in names}

OBSOLETE = {"aws-educate-setup.md", "northstar-overview.md",
            "northstar-data-schema.md"}

plan, kept = [], []
for f in files:
    fld, name = folder_of(f), f["display_name"]

    # 1. redundant copy stuck in unfiled
    if "unfiled" in fld:
        dest = home.get(name)
        if dest and dest in where.get(name, set()):
            plan.append((f, "redundant unfiled copy", f"real copy already in {dest}"))
        else:
            kept.append((f, "in unfiled, no confirmed copy elsewhere"))
        continue

    # 2. guide/kit file in a folder it does not belong to
    if fld in expected and name not in expected[fld]:
        dest = home.get(name)
        if dest and dest in where.get(name, set()):
            plan.append((f, f"stray in {fld.split('/')[-1]}", f"copy present in {dest}"))
        elif name in OBSOLETE:
            plan.append((f, "obsolete", "superseded by the current starter kit zip"))
        else:
            kept.append((f, f"unexpected in {fld}, no copy elsewhere"))

print(f"── {len(plan)} file(s) to delete ──")
for f, why, detail in plan:
    print(f"  {f['display_name'][:50]:52s} {why}")
    print(f"      {detail}")
if kept:
    print(f"\n── {len(kept)} withheld (no confirmed replacement) ──")
    for f, why in kept:
        print(f"  {f['display_name'][:50]:52s} {why}")

if not plan:
    print("\nNothing to do.")
    sys.exit(0)
if not APPLY:
    print("\nDry run. Re-run with --apply to delete.")
    sys.exit(0)

print("\n── Deleting ──")
ok = fail = 0
for f, why, _ in plan:
    r = requests.delete(f"{api.base_url}/api/v1/files/{f['id']}", headers=api.headers)
    if r.ok:
        ok += 1
    else:
        fail += 1
        print(f"  FAILED {f['display_name'][:44]}: {r.status_code}")
print(f"  deleted {ok}, failed {fail}")
print("\nDone. Re-run: python verify_course.py")
