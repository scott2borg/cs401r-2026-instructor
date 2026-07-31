#!/usr/bin/env python3
"""
Upload Lab 1-4 starter kit zips to Canvas and link into the correct modules.
    export CANVAS_API_TOKEN="your_token"
    python upload_starter_kits.py
"""

import os, sys, requests

BASE_URL  = "https://byu.instructure.com"
COURSE_ID = "34609"
API_TOKEN = os.environ.get("CANVAS_API_TOKEN", "").strip()
if not API_TOKEN:
    sys.exit("Set CANVAS_API_TOKEN")

ROOT    = f"{BASE_URL}/api/v1/courses/{COURSE_ID}"
HEADERS = {"Authorization": f"Bearer {API_TOKEN}"}

KITS = [
    ("/tmp/canvas_starter_kits/Lab1-Starter-Kit.zip", "Lab1-Starter-Kit.zip",
     "Week 01 — Introduction (Sep 3)"),
    ("/tmp/canvas_starter_kits/Lab2-Starter-Kit.zip", "Lab2-Starter-Kit.zip",
     "Week 03 — Platform II + Data Engineering I (Sep 15–17)"),
    ("/tmp/canvas_starter_kits/Lab3-Starter-Kit.zip", "Lab3-Starter-Kit.zip",
     "Week 05 — Model Dev II & III: RAG + Agents (Sep 29–Oct 1)"),
    ("/tmp/canvas_starter_kits/Lab4-Starter-Kit.zip", "Lab4-Starter-Kit.zip",
     "Week 07 — Testing & Evaluation (Oct 13–15)"),
]

def get_or_create_folder(name):
    r = requests.get(f"{ROOT}/folders/by_path/{name}", headers=HEADERS)
    if r.ok:
        return r.json()["id"]
    r = requests.post(f"{ROOT}/folders",
        headers={**HEADERS, "Content-Type": "application/json"},
        json={"name": name, "parent_folder_path": "/"})
    return r.json()["id"] if r.ok else None

def get_modules():
    modules, url = {}, f"{ROOT}/modules?per_page=50"
    while url:
        r = requests.get(url, headers=HEADERS)
        r.raise_for_status()
        for m in r.json():
            modules[m["name"]] = m["id"]
        url = r.links.get("next", {}).get("url")
    return modules

def upload_file(local_path, canvas_name, folder_id):
    size = os.path.getsize(local_path)
    r = requests.post(f"{BASE_URL}/api/v1/courses/{COURSE_ID}/files",
        headers={**HEADERS, "Content-Type": "application/json"},
        json={"name": canvas_name, "size": size,
              "content_type": "application/zip",
              "folder_id": folder_id, "on_duplicate": "overwrite"})
    if not r.ok:
        print(f"  ✗ Slot request failed: {r.text[:150]}"); return None
    info = r.json()
    with open(local_path, "rb") as f:
        r2 = requests.post(info["upload_url"], data=info["upload_params"],
                           files=[("file", (canvas_name, f, "application/zip"))],
                           allow_redirects=False)
    if r2.status_code in (301, 302, 303):
        r2 = requests.get(r2.headers["Location"], headers=HEADERS)
    return r2.json().get("id") if r2.ok else None

def add_to_module(module_id, file_id, title):
    requests.post(f"{ROOT}/modules/{module_id}/items",
        headers={**HEADERS, "Content-Type": "application/json"},
        json={"module_item": {"title": title, "type": "File", "content_id": file_id}})

def main():
    print("Uploading Lab Starter Kits to Canvas\n")
    folder_id = get_or_create_folder("Lab Starter Kits")
    print(f"Folder: Lab Starter Kits (id={folder_id})\n")
    module_ids = get_modules()

    for local, name, module_name in KITS:
        label = name.replace("-", " ").replace(".zip", "")
        print(f"  Uploading {name}...")
        file_id = upload_file(local, name, folder_id)
        if not file_id:
            print(f"  ✗ Upload failed"); continue
        print(f"  ✓ Uploaded (file_id={file_id})")
        mid = module_ids.get(module_name)
        if mid:
            add_to_module(mid, file_id, label)
            print(f"  → Linked to: {module_name}")
        print()

    print("Done. View at:")
    print(f"  {BASE_URL}/courses/{COURSE_ID}/files")

if __name__ == "__main__":
    main()
