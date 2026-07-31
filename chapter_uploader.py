#!/usr/bin/env python3
"""
CS 401R — Chapter PDF Builder & Canvas Uploader
================================================
Converts each Part 3 & 4 chapter markdown file to a formatted PDF,
then uploads it to the correct Canvas module as a reading.

    pip install requests
    export CANVAS_API_TOKEN="your_token"
    export CANVAS_COURSE_ID="34609"
    python chapter_uploader.py

Requirements:
    - pandoc (brew install pandoc)
    - xelatex (from MacTeX or TeX Live)
    - ghostscript for compression (brew install ghostscript)
    - requests
"""

import os
import sys
import json
import shutil
import subprocess
import tempfile
import requests

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

EAIE_DIR  = "/Users/scott1/Documents/Vault/Efforts/Projects/Active/EAIE"
BIB_FILE  = os.path.join(EAIE_DIR, "Build/references.bib")
OUT_DIR   = os.path.join(EAIE_DIR, "Build/canvas_chapters")   # where PDFs are saved

BASE_URL  = "https://byu.instructure.com"
COURSE_ID = os.environ.get("CANVAS_COURSE_ID", "34609").strip()
API_TOKEN = os.environ.get("CANVAS_API_TOKEN", "").strip()

if not API_TOKEN:
    sys.exit("ERROR: Set CANVAS_API_TOKEN environment variable.")

ROOT    = f"{BASE_URL}/api/v1/courses/{COURSE_ID}"
HEADERS = {"Authorization": f"Bearer {API_TOKEN}"}   # no Content-Type — varies by call

GS = shutil.which("gs")   # Ghostscript for compression (optional)


# ─────────────────────────────────────────────────────────────────────────────
# Chapter → Module Mapping
# (chapter source file, short PDF name, list of module names to link into)
# ─────────────────────────────────────────────────────────────────────────────

CHAPTERS = [
    # ── Part 3: Build ────────────────────────────────────────────────────────
    (
        "Part 3. Build/AI Systems Development Lifecycle--The Framework for Building Production Systems.md",
        "Ch01-AI-Systems-Development-Lifecycle.pdf",
        ["Week 02 — AISDLC + Platform I (Sep 8–10)"],
    ),
    (
        "Part 3. Build/AI Platform & Cloud Architecture--Building the Foundation for Scalable Systems.md",
        "Ch02-AI-Platform-Cloud-Architecture.pdf",
        [
            "Week 02 — AISDLC + Platform I (Sep 8–10)",
            "Week 03 — Platform II + Data Engineering I (Sep 15–17)",
        ],
    ),
    (
        "Part 3. Build/Data & Feature Engineering--Turning Raw Data into AI Fuel.md",
        "Ch03-Data-Feature-Engineering.pdf",
        [
            "Week 03 — Platform II + Data Engineering I (Sep 15–17)",
            "Week 04 — Data Engineering II + Model Dev I (Sep 22–24)",
        ],
    ),
    (
        "Part 3. Build/Model Development--Training, Fine-Tuning, RAG, and Orchestrating Intelligence.md",
        "Ch04-Model-Development.pdf",
        [
            "Week 04 — Data Engineering II + Model Dev I (Sep 22–24)",
            "Week 05 — Model Dev II & III: RAG + Agents (Sep 29–Oct 1)",
        ],
    ),
    (
        "Part 3. Build/The XOps Stack—Applying DevOps Discipline to Data, Models, LLMs, and Agents.md",
        "Ch05-XOps-Stack.pdf",
        ["Week 06 — XOps I & II (Oct 6–8)"],
    ),
    (
        "Part 3. Build/Testing and Evaluation--Verifying That AI Does What It Claims.md",
        "Ch06-Testing-Evaluation.pdf",
        ["Week 07 — Testing & Evaluation (Oct 13–15)"],
    ),
    (
        "Part 3. Build/Continuous Delivery—Automating the Pipeline From Commit to Production.md",
        "Ch07-Continuous-Delivery.pdf",
        ["Week 08 — Continuous Delivery (Oct 20–22)"],
    ),
    (
        "Part 3. Build/Deployment and Scaling--Getting AI Into the World and Growing It With Confidence.md",
        "Ch08-Deployment-Scaling.pdf",
        ["Week 09 — Deployment & Scaling (Oct 27–29)"],
    ),
    (
        "Part 3. Build/Security, Privacy & Compliance--Building Systems That Are Secure, Private, and Compliant by Design.md",
        "Ch09-Security-Privacy-Compliance.pdf",
        ["Week 10 — Security, Privacy & Compliance (Nov 3–5)"],
    ),
    # ── Part 4: Operate ───────────────────────────────────────────────────────
    (
        "Part 4. Operate/Metrics, Benchmarks, and Guardrails—Defining What Success Looks Like.md",
        "Ch10-Metrics-Benchmarks-Guardrails.pdf",
        ["Week 11 — Metrics + Monitoring (Nov 10–12)"],
    ),
    (
        "Part 4. Operate/Monitoring, Observability & Model Lifecycle Management.md",
        "Ch11-Monitoring-Observability.pdf",
        ["Week 11 — Metrics + Monitoring (Nov 10–12)"],
    ),
    (
        "Part 4. Operate/Reliability Engineering—Building AI Systems That Hold Under Pressure and Recover Fast.md",
        "Ch12-Reliability-Engineering.pdf",
        ["Week 12 — Reliability + Economics (Nov 17–19)"],
    ),
    (
        "Part 4. Operate/AI Economics—Managing Costs and Measuring Returns.md",
        "Ch13-AI-Economics.pdf",
        ["Week 12 — Reliability + Economics (Nov 17–19)"],
    ),
    (
        "Part 4. Operate/Measuring Business Value—Closing the Gap Between What AI Does and What the Business Needs.md",
        "Ch14-Measuring-Business-Value.pdf",
        ["Week 13 — Business Value + Project Launch (Nov 24)"],
    ),
    (
        "Part 4. Operate/AI Governance—Establishing Accountability, Policies, and Oversight.md",
        "Ch15-AI-Governance.pdf",
        ["Week 14 — Team Project Workshop I (Dec 1–3)"],
    ),
    (
        "Part 4. Operate/Closing the Loop—Feeding Operational Intelligence Back Into Strategy, Design, and Development.md",
        "Ch16-Closing-the-Loop.pdf",
        ["Week 15 — Team Project Workshop II + Final Thoughts (Dec 8–10)"],
    ),
]

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


# ─────────────────────────────────────────────────────────────────────────────
# PDF Generation
# ─────────────────────────────────────────────────────────────────────────────

def build_pdf(src_rel, pdf_filename, out_dir):
    """Convert a chapter .md file to PDF using pandoc + xelatex."""
    src = os.path.join(EAIE_DIR, src_rel)
    out = os.path.join(out_dir, pdf_filename)

    if not os.path.exists(src):
        print(f"  ✗ Source not found: {src_rel}")
        return None

    cmd = [
        "pandoc", src,
        "-o", out,
        "--pdf-engine=xelatex",
        f"--resource-path={EAIE_DIR}:{os.path.join(EAIE_DIR, 'Attachments')}",
        f"--bibliography={BIB_FILE}",
        "--citeproc",
        "-V", "geometry:margin=1in",
        "-V", "fontsize=11pt",
        "-V", "mainfont=Palatino",
        "-V", "monofont=Menlo",
        "-V", f"header-includes={UNICODE_HEADER}",
        "--from", "markdown+smart",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=EAIE_DIR)

    if not os.path.exists(out):
        print(f"  ✗ pandoc failed for {pdf_filename}")
        print(result.stderr[-500:] if result.stderr else "(no stderr)")
        return None

    # Compress with Ghostscript if available
    if GS:
        compressed = out.replace(".pdf", "_c.pdf")
        gs_cmd = [
            GS, "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.4",
            "-dPDFSETTINGS=/ebook", "-dNOPAUSE", "-dQUIET", "-dBATCH",
            f"-sOutputFile={compressed}", out
        ]
        gs_result = subprocess.run(gs_cmd, capture_output=True)
        if os.path.exists(compressed):
            original_size = os.path.getsize(out)
            compressed_size = os.path.getsize(compressed)
            if compressed_size < original_size:
                os.replace(compressed, out)
                reduction = (1 - compressed_size / original_size) * 100
                size_mb = compressed_size / 1024 / 1024
                print(f"  ✓ {pdf_filename} — {size_mb:.1f} MB (compressed {reduction:.0f}%)")
                return out

    size_mb = os.path.getsize(out) / 1024 / 1024
    print(f"  ✓ {pdf_filename} — {size_mb:.1f} MB")
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Canvas File Upload
# ─────────────────────────────────────────────────────────────────────────────

def get_or_create_readings_folder():
    """Return the Canvas folder ID for 'Readings', creating it if needed."""
    r = requests.get(f"{ROOT}/folders/by_path/Readings", headers=HEADERS)
    if r.ok:
        return r.json()["id"]
    # Create it
    r = requests.post(f"{ROOT}/folders", headers={**HEADERS, "Content-Type": "application/json"},
                      json={"name": "Readings", "parent_folder_path": "/"})
    if r.ok:
        return r.json()["id"]
    print(f"  ✗ Could not create Readings folder: {r.text[:200]}")
    return None


def upload_file_to_canvas(local_path, canvas_name, folder_id):
    """
    Upload a local file to Canvas using the 3-step pre-signed upload flow.
    Returns the Canvas file ID, or None on failure.
    """
    file_size = os.path.getsize(local_path)

    # Step 1 — Request upload slot
    r = requests.post(
        f"{BASE_URL}/api/v1/courses/{COURSE_ID}/files",
        headers={**HEADERS, "Content-Type": "application/json"},
        json={
            "name":         canvas_name,
            "size":         file_size,
            "content_type": "application/pdf",
            "folder_id":    folder_id,
            "on_duplicate": "overwrite",
        }
    )
    if not r.ok:
        print(f"  ✗ Upload slot request failed: {r.text[:200]}")
        return None

    info        = r.json()
    upload_url  = info["upload_url"]
    upload_params = info["upload_params"]

    # Step 2 — POST file to pre-signed URL
    with open(local_path, "rb") as f:
        files = [("file", (canvas_name, f, "application/pdf"))]
        r = requests.post(upload_url, data=upload_params, files=files,
                          allow_redirects=False)

    # Step 3 — Follow redirect to confirm
    if r.status_code in (301, 302, 303):
        confirm_url = r.headers["Location"]
        r = requests.get(confirm_url, headers=HEADERS)

    if not r.ok:
        print(f"  ✗ Upload confirmation failed ({r.status_code}): {r.text[:200]}")
        return None

    file_obj = r.json()
    return file_obj.get("id")


# ─────────────────────────────────────────────────────────────────────────────
# Canvas Module Linking
# ─────────────────────────────────────────────────────────────────────────────

def get_module_ids():
    """Return {module_name: module_id} for all course modules."""
    modules = {}
    url = f"{ROOT}/modules?per_page=50"
    while url:
        r = requests.get(url, headers=HEADERS)
        r.raise_for_status()
        for m in r.json():
            modules[m["name"]] = m["id"]
        url = r.links.get("next", {}).get("url")
    return modules


def add_file_to_module(module_id, file_id, title):
    r = requests.post(
        f"{ROOT}/modules/{module_id}/items",
        headers={**HEADERS, "Content-Type": "application/json"},
        json={"module_item": {"title": title, "type": "File", "content_id": file_id}}
    )
    if not r.ok:
        print(f"    ✗ Module item failed: {r.text[:150]}")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("CS 401R — Chapter PDF Builder & Canvas Uploader")
    print(f"EAIE source: {EAIE_DIR}")
    print(f"Canvas course: {BASE_URL}/courses/{COURSE_ID}\n")

    # Setup output folder
    os.makedirs(OUT_DIR, exist_ok=True)

    # Pre-fetch module IDs
    print("Fetching Canvas module IDs...")
    module_ids = get_module_ids()
    print(f"  Found {len(module_ids)} modules\n")

    # Get/create Readings folder on Canvas
    print("Setting up Canvas Readings folder...")
    folder_id = get_or_create_readings_folder()
    if not folder_id:
        sys.exit("Cannot proceed without a Readings folder.")
    print(f"  Readings folder id={folder_id}\n")

    # Process each chapter
    results = []
    for i, (src_rel, pdf_name, target_modules) in enumerate(CHAPTERS, 1):
        print(f"[{i:02d}/{len(CHAPTERS)}] {pdf_name}")

        # 1. Build PDF
        pdf_path = build_pdf(src_rel, pdf_name, OUT_DIR)
        if not pdf_path:
            results.append((pdf_name, "BUILD FAILED", []))
            continue

        # 2. Upload to Canvas
        file_id = upload_file_to_canvas(pdf_path, pdf_name, folder_id)
        if not file_id:
            results.append((pdf_name, "UPLOAD FAILED", []))
            continue
        print(f"  ✓ Uploaded (file_id={file_id})")

        # 3. Link into each target module
        linked = []
        for mod_name in target_modules:
            mid = module_ids.get(mod_name)
            if not mid:
                print(f"    ✗ Module not found: {mod_name}")
                continue
            # Use short chapter name for the module item title
            short_title = pdf_name.replace("-", " ").replace(".pdf", "")
            add_file_to_module(mid, file_id, short_title)
            print(f"    → Added to: {mod_name}")
            linked.append(mod_name)

        results.append((pdf_name, "OK", linked))
        print()

    # Summary
    print("═" * 60)
    print("SUMMARY")
    print("═" * 60)
    for name, status, modules in results:
        icon = "✓" if status == "OK" else "✗"
        print(f"  {icon} {name}: {status}")
        for m in modules:
            print(f"      → {m}")

    total_ok = sum(1 for _, s, _ in results if s == "OK")
    print(f"\n{total_ok}/{len(CHAPTERS)} chapters built and uploaded.")
    print(f"PDFs saved to: {OUT_DIR}")
    print(f"Canvas Readings: {BASE_URL}/courses/{COURSE_ID}/files")


if __name__ == "__main__":
    main()
