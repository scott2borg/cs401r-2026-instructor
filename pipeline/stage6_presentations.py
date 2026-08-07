"""
Stage 6 — Lecture Presentations → Canvas

Uploads the .pptx decks to Canvas Files → 'Presentations' and links each into
its week's module.

Uploads only; it never regenerates. generate_presentations.py builds the decks
and they are the source of truth -- re-running it would rewrite slides Scott has
edited by hand.
"""

import os

from .canvas_api import CanvasAPI

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PPTX = ("application/vnd.openxmlformats-officedocument."
         "presentationml.presentation")


def run(cfg: dict, api: CanvasAPI, module_ids: dict | None = None):
    print("\n[Stage 6] Lecture Presentations → Canvas")

    decks = cfg.get("presentations", [])
    if not decks:
        print("  No presentations configured — nothing to do")
        return

    if module_ids is None:
        print("  Fetching Canvas module IDs...")
        module_ids = api.get_modules()

    folder_id = api.get_or_create_folder("Presentations")
    if not folder_id:
        print("  ✗ Cannot create Presentations folder — aborting Stage 6")
        return
    print(f"  ✓ folder_id={folder_id}")

    uploaded = linked = skipped = 0
    for i, d in enumerate(decks, 1):
        path = os.path.join(_BASE, d["file"])
        name = os.path.basename(path)
        if not os.path.exists(path):
            print(f"  [{i:02d}/{len(decks)}] ✗ missing: {d['file']}")
            skipped += 1
            continue

        size_mb = os.path.getsize(path) / 1024 / 1024
        print(f"  [{i:02d}/{len(decks)}] {d['title']}  ({size_mb:.1f} MB)")

        fid = api.upload_file(path, name, folder_id, _PPTX)
        if not fid:
            print(f"            ✗ upload failed")
            skipped += 1
            continue
        uploaded += 1

        mid = module_ids.get(d["module"])
        if not mid:
            print(f"            ! module not found: {d['module']}")
            continue
        # add_module_item is idempotent -- matches on (type, content_id) -- so
        # re-running does not append a second copy of the same deck.
        api.add_module_item(mid, "File", fid, d["title"])
        linked += 1

    print(f"\n  ✓ Stage 6 complete — {uploaded} uploaded, {linked} linked, "
          f"{skipped} skipped")
