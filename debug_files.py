#!/usr/bin/env python3
"""Show exactly what the Files API returns. Read-only."""
import os, sys, yaml, requests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pipeline.canvas_api import CanvasAPI
cfg = yaml.safe_load(open("course_config.yaml"))
tok = os.environ.get("CANVAS_API_TOKEN", "").strip()
if not tok: sys.exit("Set CANVAS_API_TOKEN first.")
api = CanvasAPI(cfg["canvas"]["base_url"], cfg["canvas"]["course_id"], tok)

for path in ("/files", "/files?per_page=100", "/folders", "/folders?per_page=100"):
    r = requests.get(f"{api.root}{path}", headers=api.headers)
    n = len(r.json()) if r.ok else -1
    nxt = "yes" if r.links.get("next") else "no"
    print(f"  {path:<24} status={r.status_code}  first page={n:>4}  next-link={nxt}")

print("\n  via _get_all (follows next links):")
print(f"    /files                 -> {len(api._get_all('/files'))}")
print(f"    /files?per_page=100    -> {len(api._get_all('/files?per_page=100'))}")
print(f"    /folders?per_page=100  -> {len(api._get_all('/folders?per_page=100'))}")

print("\n  folders present:")
for f in sorted(api._get_all("/folders?per_page=100"), key=lambda x: x["full_name"]):
    print(f"    {f['files_count']:>4} file(s)  {f['full_name']}")
