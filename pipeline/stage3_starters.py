"""
Stage 3 — Lab Starter Kits
Zips each lab's starter kit directory, uploads to Canvas
'Lab Starter Kits' folder, and links into the correct module.
Idempotent: uses on_duplicate=overwrite.
"""

import os
import shutil
import subprocess
import tempfile

from .canvas_api import CanvasAPI

# Script-level base — CS_401R_2026 folder
_SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _zip_starter_kit(source_dir: str, zip_name: str, tmp_dir: str) -> str | None:
    """Create a zip of source_dir. Returns the zip path, or None on failure."""
    if not os.path.isdir(source_dir):
        print(f"    ✗ Starter kit directory not found: {source_dir}")
        return None
    zip_path = os.path.join(tmp_dir, zip_name)
    # zip -r preserves directory structure
    result = subprocess.run(
        ["zip", "-r", zip_path, "."],
        capture_output=True, cwd=source_dir
    )
    if not os.path.exists(zip_path):
        print(f"    ✗ zip failed: {result.stderr.decode()[:200]}")
        return None
    size_kb = os.path.getsize(zip_path) // 1024
    print(f"    ✓ Zipped — {size_kb} KB")
    return zip_path


def run(cfg: dict, api: CanvasAPI, module_ids: dict = None):
    """
    Zip and upload all lab starter kits that have a starter_kit path defined.

    Args:
        cfg:        Full course config dict.
        api:        Authenticated CanvasAPI instance.
        module_ids: {module_name: canvas_module_id}. Fetched if not provided.
    """
    print("\n[Stage 3] Lab Starter Kits → Canvas")

    if module_ids is None:
        print("  Fetching Canvas module IDs...")
        module_ids = api.get_modules()

    # Ensure destination folder
    folder_id = api.get_or_create_folder("Lab Starter Kits")
    if not folder_id:
        print("  ✗ Cannot create Lab Starter Kits folder — aborting Stage 3")
        return
    print(f"  ✓ folder_id={folder_id}")

    labs_with_kits = [lab for lab in cfg["labs"] if lab.get("starter_kit")]
    if not labs_with_kits:
        print("  No labs have starter_kit entries — nothing to upload")
        return

    tmp_dir = tempfile.mkdtemp(prefix="canvas_starter_kits_")
    try:
        for lab in labs_with_kits:
            n          = lab["number"]
            title      = lab["title"]
            kit_rel    = lab["starter_kit"]   # e.g. "Starter Kits/Lab 1"
            mod_name   = lab["module"]
            zip_name   = f"Lab{n}-Starter-Kit.zip"
            source_dir = os.path.join(_SCRIPT_DIR, kit_rel)

            print(f"\n  Lab {n} — {title}")
            print(f"    Source: {source_dir}")

            zip_path = _zip_starter_kit(source_dir, zip_name, tmp_dir)
            if not zip_path:
                continue

            # Upload
            file_id = api.upload_file(zip_path, zip_name, folder_id,
                                      "application/zip")
            if not file_id:
                print(f"    ✗ Upload failed for {zip_name}")
                continue
            print(f"    ✓ Uploaded (file_id={file_id})")

            # Link into module
            mid = module_ids.get(mod_name)
            if mid:
                label = zip_name.replace("-", " ").replace(".zip", "")
                api.add_module_item(mid, "File", file_id, label)
                print(f"    → Linked: {mod_name}")
            else:
                print(f"    ✗ Module not found: {mod_name}")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    print("\n  ✓ Stage 3 complete")
