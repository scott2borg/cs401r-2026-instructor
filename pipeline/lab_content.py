#!/usr/bin/env python3
"""Generate Canvas lab HTML from the authoritative lab markdown.

Why this exists
---------------
`canvas_builder.py` used to carry `LAB_HTML[1..7]` as hand-written HTML: a
~30-line summary of each 264-700 line markdown lab, maintained separately and
by hand. It drifted, silently, and on 2026-08-04 a sync pushed
"AUC-ROC >= 0.72" to students -- a promotion gate retired two days earlier
because it failed on 58% of splits. Nothing flagged it, because nothing
connected the two artifacts.

The standalone `Lab_N--*.md` files are authoritative (see the project CLAUDE.md).
This module makes Canvas a derived artifact of them, so the drift class cannot
recur: the task/point table in particular is now parsed out of the markdown
headings rather than retyped.

What is generated vs. kept
--------------------------
Generated from markdown: the meta block, any prerequisite banners, Objective,
Starter Kit, and the Tasks & Points table (names, points and a one-line summary
taken from the first sentence under each task heading).

NOT generated: the Submission paragraph. No lab has a `## Submission` heading,
so that text lives here as a per-lab template.

The full lab is not inlined -- it is rendered separately and uploaded to Canvas
Files, then linked. A 700-line assignment body is not a readable assignment.
"""

import html as _html
import pathlib
import re
import sys

try:
    import markdown as _markdown
except ImportError:  # pragma: no cover
    sys.exit("ERROR: pip install markdown")

VAULT_LABS = pathlib.Path(__file__).resolve().parent.parent / "CS_401R_Labs"

LAB_FILES = {
    1: "Lab_1--Platform Foundation.md",
    2: "Lab_2--Data & Feature Engineering.md",
    3: "Lab_3--Model Development.md",
    4: "Lab_4--XOps & CICD.md",
    5: "Lab_5--Deployment & Security.md",
    6: "Lab_6--Monitoring & Reliability.md",
    7: "Lab_7--Metrics & Business Value.md",
}

# No lab has a "## Submission" heading, so this stays hand-maintained. Keep it
# short: anything with figures or gates in it belongs in the markdown instead.
SUBMISSION = {
    1: "Submit your GitHub repository link. The TA will clone it and run "
       "<code>terraform apply</code> and <code>terraform destroy</code> against a clean account.",
    2: "Submit your GitHub repository link. The TA will verify your Glue jobs ran and that "
       "the Feature Store offline store is populated.",
    3: "Submit your GitHub repository link, including <code>docs/lab3-model-design.md</code> "
       "and your evaluation metrics.",
    4: "Submit your GitHub repository link. The TA will introduce a deliberate test failure and "
       "verify the run halts in the phase that owns tests, reaches no registration, and fires "
       "the build-failure alarm.",
    5: "Submit your GitHub repository link, including your deployment and rollback evidence.",
    6: "Submit your GitHub repository link, including <code>docs/lab6-runbook.md</code>.",
    7: "Submit your GitHub repository link, including your cost model and business case.",
}

# Lab 1 is the one structural outlier. It nests `### Task A1 — ... (10 points)`
# under `## Lab 1a: Manual Provisioning (35 points)`, so counting every
# points-bearing heading double-counts and sums to 200. Count the GROUP level
# only. The two-level structure is deliberate pedagogy, so the generator bends,
# not the lab.
GROUPED_LABS = {1}


# ── markdown → inline HTML ──────────────────────────────────────────────────

def _inline(md_text: str) -> str:
    """Render a short span of markdown, without the wrapping <p>."""
    out = _markdown.markdown(md_text.strip(), extensions=["sane_lists"])
    out = re.sub(r"^<p>(.*)</p>$", r"\1", out.strip(), flags=re.S)
    return out.strip()


def _block(md_text: str) -> str:
    """Render a multi-paragraph / list block of markdown."""
    return _markdown.markdown(md_text.strip(),
                              extensions=["tables", "fenced_code", "sane_lists"]).strip()


def _first_sentence(text: str) -> str:
    """First sentence of a bullet, keeping trailing markdown intact."""
    parts = re.split(r"(?<=[.!?])\s+", text.strip(), maxsplit=1)
    return parts[0].strip()


def starter_kit_inventory(md_text: str) -> str:
    """Reduce a Starter Kit section to a plain inventory of what you receive.

    Lab 2's section is 2.4 KB even after trimming bullet prose: it carries the
    full 10-row CSV schema table, indented continuation paragraphs, and a
    blockquote explaining a retired data generator. All of that is real content
    and all of it belongs in the lab guide, not in the assignment summary whose
    only job is "what files do I get".

    Keeps: top-level bullets, one sentence each; and prose sections with no
    bullets at all, because Labs 5-7 say "**None.** ..." in a paragraph.
    Drops: indented continuations, tables, blockquotes.
    """
    lines = md_text.split("\n")
    bullets = [l for l in lines if l.startswith(("- ", "* "))]
    if not bullets:
        # No list: prose section (Labs 5-7). Keep the first paragraph only.
        para = []
        for l in lines:
            if not l.strip():
                if para:
                    break
                continue
            if l.strip().startswith((">", "|", "#")):
                continue
            para.append(l.strip())
        return " ".join(para)
    return "\n".join(l[:2] + _first_sentence(l[2:]) for l in bullets)


# ── parsing ─────────────────────────────────────────────────────────────────

def _section(body: str, heading: str) -> str:
    """Text under `## <heading>` up to the next `##`."""
    m = re.search(rf"^##\s+{re.escape(heading)}[^\n]*\n(.*?)(?=^##\s|\Z)",
                  body, re.M | re.S)
    return m.group(1).strip() if m else ""


def parse_lab(n: int) -> dict:
    path = VAULT_LABS / LAB_FILES[n]
    body = path.read_text()

    title_m = re.search(r"^#\s+(.*)$", body, re.M)
    title = title_m.group(1).strip() if title_m else f"Lab {n}"

    # Consecutive **Key:** value lines directly under the H1.
    meta = []
    after_title = body[title_m.end():] if title_m else body
    for line in after_title.split("\n"):
        s = line.strip()
        if not s:
            if meta:
                break
            continue
        if s.startswith("**") and ":**" in s:
            meta.append(s)
        elif meta:
            break

    if n in GROUPED_LABS:
        pat = re.compile(r"^##\s+(.*?)\s*\((\d+)\s*points?\)", re.M)
    else:
        pat = re.compile(r"^###\s+(Task\s+[A-Z]?\d+)\s*[—–-]\s*(.*?)\s*\((\d+)\s*points?\)", re.M)

    lines = body.split("\n")
    tasks = []
    for m in pat.finditer(body):
        if n in GROUPED_LABS:
            name, pts = m.group(1), int(m.group(2))
            tid = ""
        else:
            tid, name, pts = m.group(1), m.group(2), int(m.group(3))

        # One-line summary: first non-empty, non-heading line beneath.
        start_line = body[:m.start()].count("\n")
        summary = ""
        # Skip anything that is not a prose sentence. A naive "first non-empty
        # line" picked up a rubric TABLE HEADER for Lab 2 Task 5
        # ("| Item | Points | Pass Criteria |") and a colon lead-in for Task 4.
        for j in range(start_line + 1, min(start_line + 12, len(lines))):
            s = lines[j].strip()
            if not s or s.startswith(("#", ">", "|", "-", "*", "`", "!")):
                continue
            # A trailing colon is fine if there is a complete sentence before
            # it -- Lab 6 Task 5 reads "Write complete runbooks for two failure
            # scenarios in docs/lab6-runbook.md. Choose from:" and the first
            # sentence is exactly the summary we want. Reject only when the
            # line is a bare lead-in with no sentence in it.
            first = re.split(r"(?<=[.!?])\s", s)[0].strip()
            if not first or first.endswith(":"):
                continue
            summary = s
            break
        # Trim to the first sentence so the table stays a table.
        summary = re.split(r"(?<=[.!?])\s", summary)[0] if summary else ""

        tasks.append({
            "id": tid,
            "name": name.strip(),
            "points": pts,
            "summary": summary.strip(),
        })

    return {
        "n": n,
        "path": path,
        "title": title,
        "meta": meta,
        "objective": _section(body, "Objective"),
        "starter_kit": _section(body, "Starter Kit"),
        "tasks": tasks,
        "total": sum(t["points"] for t in tasks),
        "body": body,
    }


# ── starter kits ────────────────────────────────────────────────────────────

STARTER_KITS = pathlib.Path(__file__).resolve().parent.parent / "CS_401R_Labs" / "Starter Kits"


def promised_kit_files(parsed: dict) -> list:
    """Filenames each lab tells students they will receive.

    Only the FIRST backticked token of each bullet counts. Later backticks in a
    bullet are prose -- Lab 1 once described its template as containing
    `modules/{vpc,storage,iam,sagemaker}/`, which is documentation, not a file
    to look for. Reading every backtick produced false 'missing file' reports.
    """
    out = []
    for line in parsed["starter_kit"].split("\n"):
        st = line.strip()
        if not st.startswith(("- ", "* ")):
            continue
        m = re.match(r"[-*]\s+`([^`]+)`", st)
        if m:
            out.append(m.group(1))
    return out


def check_starter_kit(parsed: dict) -> tuple:
    """(present, missing) for one lab's promised starter-kit files.

    Labs 5-7 have no kit; their section is prose and yields no bullets, which
    correctly produces two empty lists rather than a failure.
    """
    kit = STARTER_KITS / f"Lab {parsed['n']}"
    present, missing = [], []
    for ref in promised_kit_files(parsed):
        path = kit / ref.rstrip("/")
        if path.exists():
            present.append(ref)
        else:
            # tolerate a bullet naming a file nested one level down
            hits = list(kit.rglob(pathlib.Path(ref.rstrip("/")).name)) if kit.exists() else []
            (present if hits else missing).append(ref)
    return present, missing


# ── validation ──────────────────────────────────────────────────────────────

def validate(parsed: dict) -> list:
    """Return a list of problems. A non-empty list must block the push."""
    problems = []
    n = parsed["n"]
    if parsed["total"] != 100:
        problems.append(f"Lab {n}: task points sum to {parsed['total']}, expected 100")
    if not parsed["tasks"]:
        problems.append(f"Lab {n}: no task headings parsed")
    if not parsed["objective"]:
        problems.append(f"Lab {n}: '## Objective' section is empty or missing")
    if not parsed["starter_kit"]:
        problems.append(f"Lab {n}: '## Starter Kit' section is empty or missing")
    if not parsed["meta"]:
        problems.append(f"Lab {n}: no '**Assigned:** ...' meta block found under the title")
    return problems


def notes(parsed: dict) -> list:
    """Non-blocking observations. A task with no prose summary is legitimate --
    'Repository Quality' in Labs 2 and 3 goes straight into a rubric table --
    so the row simply renders with the task name and no descriptor."""
    return [f"Lab {parsed['n']}: task '{t['name']}' has no prose summary (row shows name only)"
            for t in parsed["tasks"] if not t["summary"]]


# ── HTML generation ─────────────────────────────────────────────────────────

BANNER = ('<p style="border-left:4px solid #c8102e;padding:.5rem .9rem;'
          'background:#fafafa">{}</p>')


def lab_summary_html(parsed: dict, guide_link: str = "") -> str:
    n = parsed["n"]
    out = []

    # Meta block. "**Prerequisite:**" lines are pulled out into a banner so
    # they read as a gate rather than as another bullet of front matter.
    plain = [m for m in parsed["meta"] if not m.startswith("**Prerequisite")]
    prereq = [m for m in parsed["meta"] if m.startswith("**Prerequisite")]

    if plain:
        out.append("<p>" + "<br>\n".join(_inline(m) for m in plain) + "</p>")
    for p in prereq:
        # Turn the italicised pre-lab title into the {{PRELAB_N_LINK}} token
        # that canvas_builder.resolve_links() swaps for the uploaded Canvas
        # file link. Without this the banner still reads correctly but is dead
        # text, and the student has no way to reach the guide it names.
        p = re.sub(r"\*(Pre-Lab\s*(\d)[^*]*)\*",
                   lambda m: "{{PRELAB_%s_LINK}}" % m.group(2), p)
        out.append(BANNER.format(_inline(p)))

    out.append("<h2>Objective</h2>")
    out.append(_block(parsed["objective"]))

    out.append("<h2>Starter Kit</h2>")
    out.append(_block(starter_kit_inventory(parsed["starter_kit"])))

    out.append("<h2>Tasks &amp; Point Breakdown</h2>")
    rows = ['<table border="1" cellpadding="6" cellspacing="0" '
            'style="border-collapse:collapse;width:100%">',
            '  <tr><th>Task</th><th style="text-align:center">Points</th></tr>']
    for t in parsed["tasks"]:
        label = f"{t['id']} — {t['name']}" if t["id"] else t["name"]
        cell = _inline(label)
        if t["summary"]:
            cell += f"<br><span style=\"color:#555;font-size:.93em\">{_inline(t['summary'])}</span>"
        rows.append(f'  <tr><td>{cell}</td>'
                    f'<td style="text-align:center">{t["points"]}</td></tr>')
    rows.append(f'  <tr><td><strong>Total</strong></td>'
                f'<td style="text-align:center"><strong>{parsed["total"]}</strong></td></tr>')
    rows.append("</table>")
    out.append("\n".join(rows))

    if guide_link:
        out.append(f"<p><strong>Full lab guide, rubrics and worked detail:</strong> {guide_link}</p>")

    out.append("<h2>Submission</h2>")
    out.append(f"<p>{SUBMISSION.get(n, 'Submit your GitHub repository link.')}</p>")

    return "\n\n".join(x for x in out if x)


def md_to_html_full(parsed: dict) -> str:
    """The complete lab rendered standalone, for Canvas Files.

    Self-contained rather than importing canvas_builder's renderer, so this
    module stays importable without Canvas credentials in the environment.
    """
    body = _markdown.markdown(parsed["body"],
                              extensions=["tables", "fenced_code", "toc", "sane_lists"])
    # Obsidian wikilinks have no meaning in Canvas. There is one target today
    # ([[Pre-Lab 4 ...]]); render as bold text rather than leaving [[...]] on
    # screen, and warn so a new one cannot slip through silently.
    for wl in re.findall(r"\[\[([^\]]+)\]\]", body):
        print(f"    note: wikilink '{wl}' rendered as plain text in {parsed['path'].name}")
        body = body.replace(f"[[{wl}]]", f"<strong>{_html.escape(wl)}</strong>")
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>{_html.escape(parsed['title'])}</title>
<style>
 body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
      line-height:1.55;max-width:52rem;margin:2rem auto;padding:0 1.25rem;color:#1a1a1a}}
 code{{background:#f4f4f4;padding:.12em .35em;border-radius:3px;font-size:.92em}}
 pre{{background:#f4f4f4;padding:1rem;border-radius:5px;overflow-x:auto}}
 pre code{{background:none;padding:0}}
 table{{border-collapse:collapse;width:100%;margin:1rem 0}}
 th,td{{border:1px solid #ccc;padding:.5rem .6rem;text-align:left;vertical-align:top}}
 th{{background:#f0f0f0}}
 blockquote{{border-left:4px solid #c8102e;margin:1rem 0;padding:.4rem 1rem;background:#fafafa}}
 h1,h2,h3{{line-height:1.25}} hr{{border:none;border-top:1px solid #ddd;margin:2rem 0}}
</style></head><body>
{body}
</body></html>"""


# ── CLI: inspect without touching Canvas ────────────────────────────────────

if __name__ == "__main__":
    fail = 0
    for n in sorted(LAB_FILES):
        p = parse_lab(n)
        probs = validate(p)
        status = "OK  " if not probs else "FAIL"
        print(f"{status} Lab {n}: {len(p['tasks'])} tasks, {p['total']} pts — {p['title'][:48]}")
        for t in p["tasks"]:
            lbl = f"{t['id']} — {t['name']}" if t["id"] else t["name"]
            print(f"       {t['points']:>3}  {lbl[:60]}")
        for pr in probs:
            print(f"       !! {pr}")
            fail += 1
        for nt in notes(p):
            print(f"       -- {nt}")
    print(f"\n{'ALL LABS VALID' if not fail else f'{fail} PROBLEM(S)'}")
    sys.exit(1 if fail else 0)
