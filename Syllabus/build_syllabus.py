"""
build_syllabus.py
Generate a PDF and/or DOCX of the CS 401R-4 Syllabus styled to match
the EAIE book manuscript.

Usage:
    python3 build_syllabus.py           # PDF only
    python3 build_syllabus.py --docx    # PDF + DOCX
    python3 build_syllabus.py --open    # build + open in Preview/Word

Output:
    CS_401R_Syllabus_<YYYY-MM-DD>.pdf
    CS_401R_Syllabus_<YYYY-MM-DD>.docx  (with --docx)

Requires: pandoc 3+, xelatex (TeX Live), Avenir Next font (macOS system font)
"""

import re
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime

# ─── Paths ───────────────────────────────────────────────────────────────────
SCRIPT_DIR  = Path(__file__).resolve().parent
SYLLABUS_MD = SCRIPT_DIR / "CS 401R-4 Syllabus.md"
DATE_STAMP  = datetime.now().strftime('%Y-%m-%d')
OUTPUT_PDF  = SCRIPT_DIR / f"CS_401R_Syllabus_{DATE_STAMP}.pdf"
OUTPUT_DOCX = SCRIPT_DIR / f"CS_401R_Syllabus_{DATE_STAMP}.docx"

# Reference .docx from the EAIE build for Word styling baseline
REFERENCE_DOCX = (
    SCRIPT_DIR.parent / "EAIE" / "Build" / "pandoc.docx"
)

# ─── Markdown cleaning ────────────────────────────────────────────────────────

def clean_markdown(text: str) -> str:
    """Strip Obsidian-specific syntax and fix layout issues for Pandoc."""

    # 1. Strip YAML frontmatter
    text = re.sub(r'^---.*?---\s*', '', text, flags=re.S)

    # 2. Resolve Obsidian wikilinks [[Note|alias]] → alias or Note
    def resolve_wikilink(m):
        inner = m.group(1)
        parts = inner.split('|', 1)
        return parts[1].strip() if len(parts) == 2 else parts[0].strip()

    text = re.sub(r'(?<!!)\[\[(.*?)\]\]', resolve_wikilink, text)

    # 3. Strip Obsidian image embeds ![[...]]
    text = re.sub(r'!\[\[.*?\]\]', '', text)

    # 4. Normalize horizontal rules (avoid YAML-block misparse by Pandoc)
    text = re.sub(r'^---\s*$', '* * *', text, flags=re.M)

    # 5. Ensure blank lines before lists for correct Pandoc rendering
    text = re.sub(r'([^\n])\n([ \t]*[*+-] )',    r'\1\n\n\2', text)
    text = re.sub(r'([^\n])\n([ \t]*[0-9]+\. )', r'\1\n\n\2', text)

    # 6. Replace emoji with LaTeX/DOCX-safe equivalents
    #    ⚠️ becomes a bold dagger-style marker Pandoc renders cleanly in both formats
    text = text.replace('⚠️', r'\textbf{(!)}')

    # 7. Hard line breaks for consecutive **Label:** value lines.
    #    Pandoc collapses such lines into a single paragraph unless we add
    #    a Pandoc hard-break marker (\  at end of line).  This preserves the
    #    instructor info block layout without changing the source note.
    lines = text.split('\n')
    result = []
    LABEL_RE = re.compile(r'^\*\*[^*]+:\*\*')
    for i, line in enumerate(lines):
        stripped = line.strip()
        next_stripped = lines[i + 1].strip() if i + 1 < len(lines) else ''
        if LABEL_RE.match(stripped) and LABEL_RE.match(next_stripped):
            result.append(line.rstrip() + '\\')   # Pandoc hard line break
        else:
            result.append(line)
    text = '\n'.join(result)

    # 8. Unicode normalization (matches EAIE build_book.py)
    replacements = {
        '“': '"',   # left double quotation mark
        '”': '"',   # right double quotation mark
        '‘': "'",   # left single quotation mark
        '’': "'",   # right single quotation mark / apostrophe
        '—': '---', # em dash
        '…': '...', # horizontal ellipsis
        ' ': ' ',   # non-breaking space
    }
    for char, rep in replacements.items():
        text = text.replace(char, rep)

    return text.strip()


# ─── Pandoc YAML headers ──────────────────────────────────────────────────────

def build_pdf_header(now: datetime) -> str:
    """Pandoc YAML metadata block for PDF/XeLaTeX output."""
    return f"""\
---
documentclass: article
geometry: "margin=1in"
mainfont: "Avenir Next"
fontsize: 11pt
header-includes: |
  \\usepackage{{fancyhdr}}
  \\usepackage{{booktabs}}
  \\usepackage{{longtable}}
  \\usepackage{{array}}
  \\usepackage{{xcolor}}
  \\usepackage{{caption}}
  \\usepackage{{hyperref}}
  \\definecolor{{syllabusblue}}{{HTML}}{{1A3A5C}}
  \\captionsetup{{font=it}}
  \\pagestyle{{fancy}}
  \\fancyhf{{}}
  \\fancyhead[L]{{\\small\\color{{syllabusblue}}\\textbf{{CS 401R: Engineering Production AI Systems}}}}
  \\fancyhead[R]{{\\small\\color{{syllabusblue}}Fall 2026 --- BYU}}
  \\fancyfoot[L]{{\\scriptsize Scott Toborg --- scott@toborg.com}}
  \\fancyfoot[C]{{\\thepage}}
  \\fancyfoot[R]{{\\scriptsize Generated {now.strftime('%Y-%m-%d')}}}
  \\renewcommand{{\\headrulewidth}}{{0.4pt}}
  \\renewcommand{{\\footrulewidth}}{{0.4pt}}
  \\setlength{{\\headheight}}{{14pt}}
  \\hypersetup{{
    colorlinks=true,
    linkcolor=syllabusblue,
    urlcolor=syllabusblue
  }}
suppress-bibliography: true
---
"""


def build_docx_header(now: datetime) -> str:
    """Pandoc YAML metadata block for DOCX output (no LaTeX-specific directives)."""
    return f"""\
---
title: "CS 401R: Engineering Production AI Systems"
subtitle: "Brigham Young University --- Fall 2026"
author: "Scott Toborg"
date: "{now.strftime('%B %d, %Y')}"
suppress-bibliography: true
---
"""


# ─── Build functions ──────────────────────────────────────────────────────────

def _run_pandoc(src_md: Path, output: Path, extra_args: list[str]) -> bool:
    """Run Pandoc and return True on success."""
    cmd = ["pandoc", str(src_md), "-o", str(output)] + extra_args
    print(f"Running Pandoc → {output.name} ...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"\n[ERROR] Pandoc failed building {output.name}. Stderr:\n")
        print(result.stderr)
        return False
    print(f"[OK] {output}")
    return True


def run_build(build_docx: bool = False, open_after: bool = False) -> bool:
    now = datetime.now()

    if not SYLLABUS_MD.exists():
        raise FileNotFoundError(f"Syllabus not found: {SYLLABUS_MD}")

    raw_text   = SYLLABUS_MD.read_text(encoding='utf-8')
    clean_text = clean_markdown(raw_text)

    all_ok = True

    # ── PDF ──────────────────────────────────────────────────────────────────
    pdf_manuscript = build_pdf_header(now) + "\n" + clean_text
    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.md', encoding='utf-8', delete=False
    ) as tmp:
        tmp.write(pdf_manuscript)
        tmp_pdf_path = Path(tmp.name)

    ok = _run_pandoc(tmp_pdf_path, OUTPUT_PDF, [
        "--pdf-engine=xelatex",
        "--number-sections=false",
        "--syntax-highlighting=tango",
    ])
    tmp_pdf_path.unlink(missing_ok=True)
    all_ok = all_ok and ok

    if ok and open_after:
        subprocess.run(["open", str(OUTPUT_PDF)])

    # ── DOCX ─────────────────────────────────────────────────────────────────
    if build_docx:
        # DOCX version: strip the \textbf{(!)} we injected for LaTeX and use
        # plain text instead, since raw LaTeX commands don't render in Word.
        docx_text = clean_text.replace(r'\textbf{(!)}', '(!)')
        docx_manuscript = build_docx_header(now) + "\n" + docx_text

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.md', encoding='utf-8', delete=False
        ) as tmp:
            tmp.write(docx_manuscript)
            tmp_docx_path = Path(tmp.name)

        docx_args = ["--number-sections=false"]
        if REFERENCE_DOCX.exists():
            docx_args += [f"--reference-doc={REFERENCE_DOCX}"]
            print(f"Using reference doc: {REFERENCE_DOCX.name}")

        ok = _run_pandoc(tmp_docx_path, OUTPUT_DOCX, docx_args)
        tmp_docx_path.unlink(missing_ok=True)
        all_ok = all_ok and ok

        if ok and open_after:
            subprocess.run(["open", str(OUTPUT_DOCX)])

    return all_ok


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Build CS 401R Syllabus PDF (and optionally DOCX)")
    parser.add_argument("--docx",  action="store_true", help="Also generate a .docx version")
    parser.add_argument("--open",  action="store_true", help="Open output(s) after building")
    args = parser.parse_args()

    success = run_build(build_docx=args.docx, open_after=args.open)
    raise SystemExit(0 if success else 1)
