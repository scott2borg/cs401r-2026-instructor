"""
Stage 2 — Chapter PDFs
Converts each chapter Markdown file to PDF, compresses with Ghostscript,
uploads to the Canvas 'Readings' folder, and links into the correct modules.
All operations are idempotent (Canvas uses on_duplicate: overwrite).
"""

import os
import shutil
import subprocess

from .canvas_api import CanvasAPI

# Unicode characters that require explicit LaTeX mapping (xelatex + Palatino)
UNICODE_HEADER = (
    r"\usepackage{newunicodechar}"
    r"\newunicodechar{→}{$\rightarrow$}"
    r"\newunicodechar{←}{$\leftarrow$}"
    r"\newunicodechar{↔}{$\leftrightarrow$}"
    r"\newunicodechar{⇒}{$\Rightarrow$}"
    r"\newunicodechar{≥}{$\geq$}"
    r"\newunicodechar{≤}{$\leq$}"
    r"\newunicodechar{≠}{$\neq$}"
    r"\newunicodechar{×}{$\times$}"
    r"\newunicodechar{÷}{$\div$}"
    r"\newunicodechar{…}{\ldots}"
    r"\newunicodechar{•}{$\bullet$}"
    r"\newunicodechar{✓}{$\checkmark$}"
    r"\newunicodechar{✗}{$\times$}"
    r"\newunicodechar{™}{\texttrademark}"
    r"\newunicodechar{®}{\textregistered}"
    r"\newunicodechar{©}{\textcopyright}"
    r"\newunicodechar{—}{---}"
    r"\newunicodechar{–}{--}"
    r"\newunicodechar{∞}{$\infty$}"
    r"\newunicodechar{∑}{$\sum$}"
    r"\newunicodechar{α}{$\alpha$}"
    r"\newunicodechar{β}{$\beta$}"
    r"\newunicodechar{γ}{$\gamma$}"
    r"\newunicodechar{δ}{$\delta$}"
    r"\newunicodechar{σ}{$\sigma$}"
    r"\newunicodechar{μ}{$\mu$}"
)


def _build_pdf(src_path: str, out_path: str, eaie_dir: str, bib_file: str) -> bool:
    """Run pandoc + xelatex to build a single chapter PDF. Returns True on success."""
    cmd = [
        "pandoc", src_path,
        "-o", out_path,
        "--pdf-engine=xelatex",
        f"--resource-path={eaie_dir}:{os.path.join(eaie_dir, 'Attachments')}",
        f"--bibliography={bib_file}",
        "--citeproc",
        "-V", "geometry:margin=1in",
        "-V", "fontsize=11pt",
        "-V", "mainfont=Palatino",
        "-V", "monofont=Menlo",
        "-V", f"header-includes={UNICODE_HEADER}",
        "--from", "markdown+smart",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=eaie_dir)
    if not os.path.exists(out_path):
        print(f"    ✗ pandoc failed")
        if result.stderr:
            print(result.stderr[-600:])
        return False
    return True


def _compress_pdf(pdf_path: str, setting: str | None = "/ebook") -> None:
    """Ghostscript compression in-place. No-op if gs missing or setting is None.

    /ebook is aggressive: measured on Ch01 it took an 18.5 MB chapter to 1.1 MB
    but downsampled the worst figure to 12% of its pixels. These chapters are
    full of architecture diagrams with small text labels, which is exactly what
    that ruins. /printer keeps roughly 3x the detail at ~18% of original size.

    Set `source.compress_pdfs` in course_config.yaml:
        null / false  -> no compression (full resolution; ~143 MB for 16)
        "/printer"    -> balanced
        "/ebook"      -> smallest, softest figures
    """
    if not setting:
        return
    gs = shutil.which("gs")
    if not gs:
        return
    tmp = pdf_path.replace(".pdf", "_c.pdf")
    subprocess.run([
        gs, "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.4",
        f"-dPDFSETTINGS={setting}", "-dNOPAUSE", "-dQUIET", "-dBATCH",
        f"-sOutputFile={tmp}", pdf_path,
    ], capture_output=True)
    if os.path.exists(tmp):
        orig = os.path.getsize(pdf_path)
        comp = os.path.getsize(tmp)
        if comp < orig:
            os.replace(tmp, pdf_path)
            pct = (1 - comp / orig) * 100
            print(f"    → Compressed {pct:.0f}%  ({comp/1024/1024:.1f} MB)")
        else:
            os.remove(tmp)


def run(cfg: dict, api: CanvasAPI, module_ids: dict = None, rebuild: bool = False):
    """
    Convert chapters to PDF, upload to Canvas, link to modules.

    Args:
        cfg:        Full course config dict.
        api:        Authenticated CanvasAPI instance.
        module_ids: {module_name: canvas_module_id}. Fetched if not provided.
        rebuild:    Force re-build of PDFs even if they already exist.
    """
    print("\n[Stage 2] Chapter PDFs → Canvas Readings")

    src = cfg["source"]
    eaie_dir  = src["directory"]
    bib_file  = os.path.join(eaie_dir, src["bibliography"])
    out_dir   = os.path.join(eaie_dir, src["output_dir"])
    chapters  = cfg["chapters"]

    os.makedirs(out_dir, exist_ok=True)

    # Fetch module IDs if not passed in from Stage 1
    if module_ids is None:
        print("  Fetching Canvas module IDs...")
        module_ids = api.get_modules()

    # Ensure Readings folder exists on Canvas
    print("  Setting up Canvas Readings folder...")
    folder_id = api.get_or_create_folder("Readings")
    if not folder_id:
        print("  ✗ Cannot create Readings folder — aborting Stage 2")
        return
    print(f"    ✓ folder_id={folder_id}")

    results = []
    total = len(chapters)

    for i, ch in enumerate(chapters, 1):
        src_rel    = ch["file"]
        pdf_name   = ch["pdf"]
        modules    = ch["modules"]
        src_path   = os.path.join(eaie_dir, src_rel)
        out_path   = os.path.join(out_dir, pdf_name)

        print(f"\n  [{i:02d}/{total}] {pdf_name}")

        if not os.path.exists(src_path):
            print(f"    ✗ Source missing: {src_rel}")
            results.append((pdf_name, "MISSING", []))
            continue

        # Build PDF (skip if already exists and rebuild not requested)
        if os.path.exists(out_path) and not rebuild:
            size_mb = os.path.getsize(out_path) / 1024 / 1024
            print(f"    ↩ PDF exists ({size_mb:.1f} MB) — skipping build")
        else:
            print(f"    Building PDF...")
            ok = _build_pdf(src_path, out_path, eaie_dir, bib_file)
            if not ok:
                results.append((pdf_name, "BUILD FAILED", []))
                continue
            _compress_pdf(out_path, cfg["source"].get("compress_pdfs"))
            size_mb = os.path.getsize(out_path) / 1024 / 1024
            print(f"    ✓ Built — {size_mb:.1f} MB")

        # Upload to Canvas (overwrite if present)
        print(f"    Uploading to Canvas...")
        file_id = api.upload_file(out_path, pdf_name, folder_id, "application/pdf")
        if not file_id:
            results.append((pdf_name, "UPLOAD FAILED", []))
            continue
        print(f"    ✓ Uploaded (file_id={file_id})")

        # Link into each target module
        linked = []
        short_title = pdf_name.replace("-", " ").replace(".pdf", "")
        for mod_name in modules:
            mid = module_ids.get(mod_name)
            if not mid:
                print(f"    ✗ Module not found: {mod_name}")
                continue
            api.add_module_item(mid, "File", file_id, short_title)
            print(f"    → {mod_name}")
            linked.append(mod_name)

        results.append((pdf_name, "OK", linked))

    # Summary
    print("\n  " + "─" * 56)
    ok_count = sum(1 for _, s, _ in results if s == "OK")
    for name, status, mods in results:
        icon = "✓" if status == "OK" else "✗"
        print(f"  {icon} {name}: {status}")
    print(f"\n  {ok_count}/{total} chapters uploaded.")
    print(f"  PDFs at: {out_dir}")
    print("\n  ✓ Stage 2 complete")
