#!/usr/bin/env python3
"""
CS 401R — Canvas Course Builder
=================================
Populates the CS 401R "Engineering Production AI Systems" Canvas course shell
via the Canvas REST API. Run ONCE on a clean shell.

    pip install requests
    export CANVAS_API_TOKEN="your_token"
    export CANVAS_COURSE_ID="123456"
    python canvas_builder.py

NOT idempotent. To start over: Course Settings → Reset Course Content, then re-run.
"""

import os
import pathlib
import sys
from datetime import datetime, timedelta, timezone
import requests

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

BASE_URL  = "https://byu.instructure.com"
COURSE_ID = os.environ.get("CANVAS_COURSE_ID", "").strip()
API_TOKEN = os.environ.get("CANVAS_API_TOKEN", "").strip()

if not COURSE_ID:
    sys.exit("ERROR: Set CANVAS_COURSE_ID to your course ID (the number in the course URL).")
if not API_TOKEN:
    sys.exit("ERROR: Set CANVAS_API_TOKEN to your Canvas API token.")

ROOT    = f"{BASE_URL}/api/v1/courses/{COURSE_ID}"
HEADERS = {"Authorization": f"Bearer {API_TOKEN}", "Content-Type": "application/json"}


# ─────────────────────────────────────────────────────────────────────────────
# API Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _req(method, path, data=None, label=""):
    url = f"{ROOT}{path}"
    r = getattr(requests, method)(url, headers=HEADERS, json=data)
    if not r.ok:
        print(f"  ✗ {r.status_code} {method.upper()} {path}: {r.text[:250]}")
        return None
    obj = r.json()
    if label:
        oid = obj.get("id", "?") if isinstance(obj, dict) else "?"
        print(f"  ✓ {label} (id={oid})")
    return obj

def post(path, data, label=""):  return _req("post", path, data, label)
def put(path, data, label=""):   return _req("put",  path, data, label)
def delete(path):
    r = requests.delete(f"{ROOT}{path}", headers=HEADERS)
    return r.ok

def get_all(path):
    """Fetch all pages of a paginated Canvas endpoint."""
    results, url = [], f"{ROOT}{path}"
    while url:
        r = requests.get(url, headers=HEADERS)
        r.raise_for_status()
        results.extend(r.json())
        url = r.links.get("next", {}).get("url")
    return results


# ─────────────────────────────────────────────────────────────────────────────
# Date Helpers  (fall semester = Mountain Daylight Time, UTC-6)
# ─────────────────────────────────────────────────────────────────────────────

MDT = timezone(timedelta(hours=-6))

def mdt(date_str: str, hour: int = 23, minute: int = 59) -> str:
    local = datetime.strptime(date_str, "%Y-%m-%d").replace(
        hour=hour, minute=minute, second=0, tzinfo=MDT)
    return local.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def due(d):        return mdt(d, 23, 59)
def quiz_open(d):  return mdt(d,  8,  0)


# ─────────────────────────────────────────────────────────────────────────────
# Module Names
# ─────────────────────────────────────────────────────────────────────────────

MODULE_NAMES = [
    "Start Here",
    "Week 01 — Introduction (Sep 3)",
    "Week 02 — AISDLC + Platform I (Sep 8–10)",
    "Week 03 — Platform II + Data Engineering I (Sep 15–17)",
    "Week 04 — Data Engineering II + Model Dev I (Sep 22–24)",
    "Week 05 — Model Dev II & III: RAG + Agents (Sep 29–Oct 1)",
    "Week 06 — XOps I & II (Oct 6–8)",
    "Week 07 — Testing & Evaluation (Oct 13–15)",
    "Week 08 — Continuous Delivery (Oct 20–22)",
    "Week 09 — Deployment & Scaling (Oct 27–29)",
    "Week 10 — Security, Privacy & Compliance (Nov 3–5)",
    "Week 11 — Metrics + Monitoring (Nov 10–12)",
    "Week 12 — Reliability + Economics (Nov 17–19)",
    "Week 13 — Business Value + Project Launch (Nov 24)",
    "Week 14 — Team Project Workshop I (Dec 1–3)",
    "Week 15 — Team Project Workshop II + Final Thoughts (Dec 8–10)",
]


# ─────────────────────────────────────────────────────────────────────────────
# Assignment Groups
# ─────────────────────────────────────────────────────────────────────────────

ASSIGNMENT_GROUPS = [
    {"name": "Labs",            "group_weight": 60, "position": 1},
    {"name": "Final Project",   "group_weight": 25, "position": 2},
    {"name": "Reading Quizzes", "group_weight": 10, "position": 3},
    {"name": "Participation",   "group_weight": 5,  "position": 4},
]


# ─────────────────────────────────────────────────────────────────────────────
# Canvas Files upload
#
# Canvas uploads are a three-step handshake, not a single POST:
#   1. POST /files announcing name/size/type  -> returns a one-time upload_url
#      and a dict of upload_params that must be sent EXACTLY as given
#   2. POST the file to that upload_url as multipart. This request must NOT
#      carry the Authorization header -- the pre-signed URL already authorises
#      it, and sending the bearer token makes S3 reject the request
#   3. The response redirects to a confirmation URL returning the file JSON
# ─────────────────────────────────────────────────────────────────────────────

def upload_course_file(local_path, folder_path, display_name=None, content_type="text/html"):
    """Upload one file into a Canvas course Files folder. Returns the file id."""
    local_path = pathlib.Path(local_path)
    if not local_path.exists():
        print(f"  ✗ missing: {local_path}")
        return None
    name = display_name or local_path.name
    size = local_path.stat().st_size

    step1 = post("/files", {
        "name":               name,
        "size":               size,
        "content_type":       content_type,
        "parent_folder_path": folder_path,
        # Re-running the builder should replace the guide, not accumulate
        # "guide-1.html", "guide-2.html" beside it.
        "on_duplicate":       "overwrite",
    }, f"announce {name}")
    if not step1 or "upload_url" not in step1:
        print(f"  ✗ no upload_url returned for {name}")
        return None

    with open(local_path, "rb") as fh:
        r2 = requests.post(step1["upload_url"],
                           data=step1.get("upload_params", {}),
                           files={"file": (name, fh, content_type)})
    if not r2.ok:
        print(f"  ✗ upload failed for {name}: {r2.status_code} {r2.text[:200]}")
        return None

    try:
        info = r2.json()
    except ValueError:
        print(f"  ✗ non-JSON confirm response for {name}")
        return None

    fid = info.get("id")
    print(f"  ✓ uploaded {name} (file id {fid})")
    return fid


def md_to_html(md_path):
    """Render a guide to standalone HTML so Canvas previews it in-browser.

    A raw .md in Canvas Files downloads as plain text rather than rendering,
    which is a poor way to deliver a 260-line guide a student needs to follow
    step by step.
    """
    try:
        import markdown
    except ImportError:
        sys.exit("ERROR: pip install markdown  (needed to render the pre-lab guides)")
    body = markdown.markdown(
        pathlib.Path(md_path).read_text(),
        extensions=["tables", "fenced_code", "toc", "sane_lists"],
    )
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>{pathlib.Path(md_path).stem}</title>
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


VAULT_LABS = pathlib.Path(__file__).resolve().parent.parent / "CS_401R_Labs"

PRELAB_GUIDES = {
    3: VAULT_LABS / "Pre-Lab 3 — Bedrock Access Setup.md",
    4: VAULT_LABS / "Pre-Lab 4 — SageMaker Training Quota Setup.md",
}

# Filled in by build_prelab_files(); consumed by the {{PRELAB_N_LINK}}
# placeholders in the lab and pre-lab HTML.
PRELAB_FILE_IDS = {}


def build_prelab_files():
    """Render both pre-lab guides to HTML and upload them to Canvas Files."""
    print("\n── Pre-Lab Guides → Canvas Files ──")
    import tempfile
    for n, md in PRELAB_GUIDES.items():
        if not md.exists():
            print(f"  ✗ guide not found: {md}")
            continue
        html = md_to_html(md)
        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as tmp:
            tmp.write(html)
            tmp_path = tmp.name
        fid = upload_course_file(tmp_path, "course files/Pre-Lab Guides",
                                 display_name=f"{md.stem}.html")
        os.unlink(tmp_path)
        if fid:
            PRELAB_FILE_IDS[n] = fid


def prelab_link(n, text=None):
    """An <a> to the uploaded guide, or honest fallback text if absent."""
    fid = PRELAB_FILE_IDS.get(n)
    label = text or f"Pre-Lab {n} — full guide"
    if not fid:
        return f"<em>{label} (see the course repository)</em>"
    return (f'<a class="instructure_file_link inline_disabled" '
            f'href="/courses/{COURSE_ID}/files/{fid}?wrap=1" '
            f'target="_blank" rel="noopener">{label}</a>')


def resolve_links(html):
    """Swap {{PRELAB_N_LINK}} placeholders for real Canvas file links."""
    for n in (3, 4):
        html = html.replace(f"{{{{PRELAB_{n}_LINK}}}}", prelab_link(n))
    return html


# ─────────────────────────────────────────────────────────────────────────────
# Lab Assignment HTML Descriptions
# ─────────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
# Lab assignment HTML is GENERATED, not stored.
#
# This file used to carry LAB_HTML[1..7] as hand-written HTML summaries of each
# lab, maintained separately from the authoritative Lab_N--*.md markdown. They
# drifted, and on 2026-08-04 a sync pushed a promotion gate to students that had
# been retired two days earlier ("AUC-ROC >= 0.72"). Nothing caught it because
# nothing connected the two artifacts.
#
# lab_content.py now derives the description from the markdown: meta block,
# prerequisite banners, Objective, Starter Kit inventory, and the Tasks & Points
# table parsed from the `### Task N — ... (X points)` headings. Edit the
# markdown; Canvas follows. The previous hand-written blocks are preserved in
# canvas_builder.py.pre-generator.bak.
# ─────────────────────────────────────────────────────────────────────────────

import lab_content


def build_lab_files():
    """Render each full lab to HTML and upload it to Canvas Files."""
    print("\n── Lab Guides → Canvas Files ──")
    import tempfile
    for n in sorted(lab_content.LAB_FILES):
        parsed = lab_content.parse_lab(n)
        html = lab_content.md_to_html_full(parsed)
        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as t:
            t.write(html); tmp = t.name
        fid = upload_course_file(tmp, "course files/Lab Guides",
                                 display_name=f"{parsed['path'].stem}.html")
        os.unlink(tmp)
        if fid:
            LAB_FILE_IDS[n] = fid


LAB_FILE_IDS = {}
KIT_FILE_IDS = {}

_CONTENT_TYPES = {
    ".py": "text/plain", ".sh": "text/plain", ".yml": "text/plain",
    ".yaml": "text/plain", ".tf": "text/plain", ".md": "text/plain",
    ".txt": "text/plain", ".json": "application/json", ".csv": "text/csv",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".example": "text/plain", ".hcl": "text/plain",
}


def build_starter_kits():
    """Upload each lab's starter kit to Canvas Files, preserving structure.

    Every lab header reads "Starter Kit (Canvas: Lab N)", so this is a promise
    the course makes. Until 2026-08-04 nothing uploaded them and the promise
    was unmet -- a student could not begin Lab 1.

    Directory shape is preserved, so terraform-module-template/modules/vpc/
    main.tf lands under Starter Kits/Lab 1/terraform-module-template/modules/vpc/.
    """
    print("")
    print("-- Starter Kits -> Canvas Files --")
    for n in sorted(lab_content.LAB_FILES):
        kit = lab_content.STARTER_KITS / ("Lab %d" % n)
        if not kit.is_dir():
            continue
        files = sorted(f for f in kit.rglob("*")
                       if f.is_file() and not f.name.startswith(("~$", ".")))
        if not files:
            continue
        print("  Lab %d: %d file(s)" % (n, len(files)))
        for f in files:
            rel = f.relative_to(kit).parent
            folder = "course files/Starter Kits/Lab %d" % n
            if str(rel) != ".":
                folder = folder + "/" + str(rel)
            fid = upload_course_file(
                f, folder, display_name=f.name,
                content_type=_CONTENT_TYPES.get(f.suffix.lower(),
                                                "application/octet-stream"))
            if fid:
                KIT_FILE_IDS.setdefault(n, []).append(fid)




def lab_guide_link(n):
    fid = LAB_FILE_IDS.get(n)
    if not fid:
        return "<em>full lab guide (see the course repository)</em>"
    return (f'<a class="instructure_file_link inline_disabled" '
            f'href="/courses/{COURSE_ID}/files/{fid}?wrap=1" '
            f'target="_blank" rel="noopener">Open the full lab guide</a>')


def lab_html(n):
    """The generated assignment description for lab n."""
    return lab_content.lab_summary_html(lab_content.parse_lab(n), lab_guide_link(n))


def validate_all_labs():
    """Refuse to push if any lab fails structural validation."""
    problems = []
    for n in sorted(lab_content.LAB_FILES):
        problems += lab_content.validate(lab_content.parse_lab(n))
    # Retired gates and stale figures must never reach a student. The
    # post-push verifier catches these too, but by then they are live -- which
    # is exactly what happened on 2026-08-04 with "AUC-ROC >= 0.72".
    import re as _re
    RETIRED = [
        (r"AUC[- ]?ROC\s*(&ge;|>=|≥)\s*0\.72", "retired absolute AUC 0.72 gate"),
        (r"(&ge;|>=|≥)\s*0\.03\s*(lift|AUC)",   "retired fixed 0.03 lift gate"),
        (r"[Tt]rain freely",                      "'train freely' — training quota is 0 by default"),
        (r"5 stages",                             "superseded '5 stages' wording"),
        (r"1,200[- ]customer",                    "retired 1,200-customer dataset"),
    ]
    for n in sorted(lab_content.LAB_FILES):
        html = lab_content.lab_summary_html(lab_content.parse_lab(n))
        for pat, label in RETIRED:
            if _re.search(pat, html):
                problems.append(f"Lab {n}: generated description contains {label}")

    # A lab that promises a file it does not ship is a broken promise the
    # student discovers, not us. Lab 1 shipped exactly that: it advertised
    # `northstar-overview.md` (the file is northstar-scenario-overview.md) and
    # a `terraform-module-template/` that had never been written.
    for _n in sorted(lab_content.LAB_FILES):
        _parsed = lab_content.parse_lab(_n)
        _, _missing = lab_content.check_starter_kit(_parsed)
        for _miss in _missing:
            problems.append(
                "Lab %d: starter kit promises '%s' but it is not in "
                "Starter Kits/Lab %d/" % (_n, _miss, _n))

    if problems:
        print("\nREFUSING TO PUSH — lab content failed validation:")
        for pr in problems:
            print("  !!", pr)
        sys.exit(1)
    print(f"✓ All {len(lab_content.LAB_FILES)} labs validated "
          f"(points sum to 100, no retired gates)")


LABS = [
    {
        "name":      "Lab 1 — Platform Foundation",
        "due_at":    due("2026-09-19"),
        "unlock_at": mdt("2026-09-03", 9, 0),
        "n":         1,
        "module":    "Week 01 — Introduction (Sep 3)",
    },
    {
        "name":      "Lab 2 — Data & Feature Engineering",
        "due_at":    due("2026-10-03"),
        "unlock_at": mdt("2026-09-17", 9, 0),
        "n":         2,
        "module":    "Week 03 — Platform II + Data Engineering I (Sep 15–17)",
    },
    {
        "name":      "Lab 3 — Model Development",
        "due_at":    due("2026-10-17"),
        "unlock_at": mdt("2026-10-01", 9, 0),
        "n":         3,
        "module":    "Week 05 — Model Dev II & III: RAG + Agents (Sep 29–Oct 1)",
    },
    {
        "name":      "Lab 4 — XOps, Testing & CI/CD Pipeline",
        "due_at":    due("2026-10-31"),
        "unlock_at": mdt("2026-10-15", 9, 0),
        "n":         4,
        "module":    "Week 07 — Testing & Evaluation (Oct 13–15)",
    },
    {
        "name":      "Lab 5 — Deployment & Scaling",
        "due_at":    due("2026-11-14"),
        "unlock_at": mdt("2026-10-29", 9, 0),
        "n":         5,
        "module":    "Week 09 — Deployment & Scaling (Oct 27–29)",
    },
    {
        "name":      "Lab 6 — Monitoring & Reliability",
        "due_at":    due("2026-11-28"),
        "unlock_at": mdt("2026-11-12", 9, 0),
        "n":         6,
        "module":    "Week 11 — Metrics + Monitoring (Nov 10–12)",
    },
    {
        "name":      "Lab 7 — Metrics, Economics & Business Value",
        "due_at":    due("2026-12-01"),
        "unlock_at": mdt("2026-11-19", 9, 0),
        "n":         7,
        "module":    "Week 12 — Reliability + Economics (Nov 17–19)",
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# Final Project
# ─────────────────────────────────────────────────────────────────────────────

FINAL_PROJECT_HTML = """
<p><strong>Teams:</strong> 2–3 students &nbsp;|&nbsp; <strong>Teams finalized:</strong> Tue Nov 25<br>
<strong>Submission due:</strong> Thu Dec 17, 11:59 PM MDT (last day of finals)<br>
<strong>Presentations:</strong> Finals week — schedule posted by Dec 1 (15 min + 5 min Q&amp;A)</p>

<h2>Prompt</h2>
<p>Design a production AI system for a company and use case of your choosing. Your deliverable is
a technical design document covering all course layers:</p>
<ul>
  <li>Platform architecture</li>
  <li>Data and feature pipeline</li>
  <li>Model development approach</li>
  <li>XOps plan</li>
  <li>Deployment strategy</li>
  <li>Operating model (monitoring + reliability)</li>
  <li>Economic justification</li>
  <li>Governance framework</li>
</ul>
<p>Use the NorthStar platform from your labs as your architecture reference.</p>

<h2>Grading Rubric</h2>
<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;width:100%">
  <tr><th>Dimension</th><th style="text-align:center">Weight</th></tr>
  <tr><td>Technical depth and correctness</td><td style="text-align:center">40%</td></tr>
  <tr><td>Integration and coherence across all layers</td><td style="text-align:center">30%</td></tr>
  <tr><td>Business/executive communication quality</td><td style="text-align:center">20%</td></tr>
  <tr><td>Presentation</td><td style="text-align:center">10%</td></tr>
</table>
"""

TEAM_SIGNUP_HTML = """
<p><strong>Due:</strong> Tue Nov 25, 11:59 PM MDT</p>
<p>Form a team of 2–3 students. Submit your team roster here before the deadline.
Teams cannot change after Nov 25 without instructor approval.</p>
<p><strong>Submit:</strong> List each team member's full name and NetID, one per line.</p>
"""

# ─────────────────────────────────────────────────────────────────────────────
# Pre-Lab Exercises
#
# These existed as markdown in the vault and were assigned in the lab headers,
# but were never created in Canvas by this builder -- so students could not see
# them. Both gate later labs and both depend on AWS approval times that are not
# ours to control, which is the entire reason they are assigned in September.
#
# 0 points on purpose: each is graded inside the lab it gates (Pre-Lab 3 within
# Lab 3 Task 4, Pre-Lab 4 within Lab 4 Task 2). The due date is what matters --
# it puts them on the student calendar and to-do list.
# ─────────────────────────────────────────────────────────────────────────────

PRELAB_HTML = {}

PRELAB_HTML[3] = """
<p><strong>Assigned:</strong> Thu Sep 17 (with Lab 2) &nbsp;|&nbsp; <strong>Due:</strong> Wed Sep 30<br>
<strong>Effort:</strong> ~30 minutes of your time, then waiting on AWS<br>
<strong>Counts toward:</strong> Lab 3 Task 4. <strong>Lab 3 Track B and C cannot start without it.</strong></p>

<p>Lab 3 Tracks B and C require Amazon Bedrock. Access is <strong>opt-in and not instant</strong> &mdash; a one-time
Anthropic use-case form, per-model enablement, and possibly quota increases that AWS reviews on its own
schedule. Until you enable a model, every Bedrock inference quota on your account reads <strong>zero</strong>,
regardless of how old the account is.</p>

<p><strong>Do this while you are working on Lab 2.</strong> Do not wait until Lab 3 is assigned.</p>

<p>Watch for two misleading errors: <code>ResourceNotFoundException: Model use case details have not been
submitted</code> means the form is outstanding; <code>ThrottlingException: Too many tokens per day</code> does
<em>not</em> mean you used your allowance &mdash; it means your allowance is zero.</p>

<p><strong>Deliverable:</strong> <code>docs/bedrock-access-verification.txt</code> with your verification output,
your quota values, and one paragraph justifying the capacity you requested. That last part is the real
assignment.</p>

<p><strong>Full instructions:</strong> {{PRELAB_3_LINK}}</p>
"""

PRELAB_HTML[4] = """
<p><strong>Assigned:</strong> Thu Sep 17 (with Lab 2) &nbsp;|&nbsp; <strong>Due:</strong> Wed Sep 30<br>
<strong>Effort:</strong> ~20 minutes of your time, then waiting on AWS<br>
<strong>Counts toward:</strong> Lab 4 Task 2. <strong>Lab 4 cannot be completed without it &mdash; there is no local fallback.</strong></p>

<p>Lab 4&#39;s pipeline runs a <strong>SageMaker Training Job</strong>. On a new AWS account the on-demand training
quota for every instance family is <strong>zero</strong>, so that job fails with <code>ResourceLimitExceeded</code>
before it starts. This is not a billing limit you can spend past &mdash; no capacity is allocated to your
account until you ask for some.</p>

<p>Lab 4 is not assigned until <strong>Oct 15</strong>, and that is the point: you are filing six weeks early
because the approval time is not yours to control. Same lesson as Pre-Lab 3.</p>

<p><strong>The trap:</strong> <code>get-service-quota</code> tells you what <em>your</em> account has;
<code>get-aws-default-service-quota</code> tells you what a <em>new</em> account starts with. Accounts that have
been used a while accrue elevated quotas quietly. Check both &mdash; the smaller one is the truth for you.</p>

<pre><code>aws service-quotas get-aws-default-service-quota \
  --service-code sagemaker --quota-code L-611FA074

aws service-quotas request-service-quota-increase \
  --service-code sagemaker --quota-code L-611FA074 --desired-value 2</code></pre>

<p>Ask for <strong>2, not 20</strong>, and be ready to defend the number. If approval is slow, spot training has a
non-zero default (4 for <code>ml.m5.large</code>) &mdash; see Step 3 of the full guide.</p>

<p><strong>Deliverable:</strong> <code>docs/training-quota-verification.txt</code> showing the AWS default beside
your applied value, your request status, and one paragraph on what you requested, why that number, and your
fallback.</p>

<p><strong>Full instructions:</strong> {{PRELAB_4_LINK}}</p>
"""

PRELABS = [
    {
        "name":      "Pre-Lab 3 — Bedrock Model Access Setup",
        "due_at":    due("2026-09-30"),
        "unlock_at": mdt("2026-09-17", 9, 0),
        "html":      PRELAB_HTML[3],
        "module":    "Week 03 — Platform II + Data Engineering I (Sep 15–17)",
    },
    {
        "name":      "Pre-Lab 4 — SageMaker Training Quota Setup",
        "due_at":    due("2026-09-30"),
        "unlock_at": mdt("2026-09-17", 9, 0),
        "html":      PRELAB_HTML[4],
        "module":    "Week 03 — Platform II + Data Engineering I (Sep 15–17)",
    },
]


FINAL_ASSIGNMENTS = [
    {
        "name":      "Team Sign-Up (due Nov 25)",
        "due_at":    due("2026-11-25"),
        "unlock_at": mdt("2026-11-24", 9, 0),
        "points":    0,
        "html":      TEAM_SIGNUP_HTML,
        "types":     ["online_text_entry"],
        "module":    "Week 13 — Business Value + Project Launch (Nov 24)",
    },
    {
        "name":      "Final Project — NorthStar AI Platform Design",
        "due_at":    due("2026-12-17"),
        "unlock_at": mdt("2026-11-24", 9, 0),
        "points":    100,
        "html":      FINAL_PROJECT_HTML,
        "types":     ["online_upload", "online_url"],
        "module":    "Week 14 — Team Project Workshop I (Dec 1–3)",
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# Reading Quizzes
# One per week, weeks 2–13. Opens Saturday 8 AM, due Monday 11:59 PM MDT.
# (name, open_saturday, due_monday, module_name)
# ─────────────────────────────────────────────────────────────────────────────

QUIZZES = [
    ("Quiz — Week 02: AISDLC + AI Platform",
        "2026-09-05", "2026-09-07", "Week 02 — AISDLC + Platform I (Sep 8–10)"),
    ("Quiz — Week 03: AI Platform II + Data Engineering",
        "2026-09-12", "2026-09-14", "Week 03 — Platform II + Data Engineering I (Sep 15–17)"),
    ("Quiz — Week 04: Data Engineering II + Model Development",
        "2026-09-19", "2026-09-21", "Week 04 — Data Engineering II + Model Dev I (Sep 22–24)"),
    ("Quiz — Week 05: RAG + Agent Development",
        "2026-09-26", "2026-09-28", "Week 05 — Model Dev II & III: RAG + Agents (Sep 29–Oct 1)"),
    ("Quiz — Week 06: XOps Stack",
        "2026-10-03", "2026-10-05", "Week 06 — XOps I & II (Oct 6–8)"),
    ("Quiz — Week 07: Testing & Evaluation",
        "2026-10-10", "2026-10-12", "Week 07 — Testing & Evaluation (Oct 13–15)"),
    ("Quiz — Week 08: Continuous Delivery",
        "2026-10-17", "2026-10-19", "Week 08 — Continuous Delivery (Oct 20–22)"),
    ("Quiz — Week 09: Deployment & Scaling",
        "2026-10-24", "2026-10-26", "Week 09 — Deployment & Scaling (Oct 27–29)"),
    ("Quiz — Week 10: Security, Privacy & Compliance",
        "2026-10-31", "2026-11-02", "Week 10 — Security, Privacy & Compliance (Nov 3–5)"),
    ("Quiz — Week 11: Metrics + Monitoring",
        "2026-11-07", "2026-11-09", "Week 11 — Metrics + Monitoring (Nov 10–12)"),
    ("Quiz — Week 12: Reliability Engineering + AI Economics",
        "2026-11-14", "2026-11-16", "Week 12 — Reliability + Economics (Nov 17–19)"),
    ("Quiz — Week 13: Measuring Business Value",
        "2026-11-21", "2026-11-23", "Week 13 — Business Value + Project Launch (Nov 24)"),
]


# ─────────────────────────────────────────────────────────────────────────────
# Pages
# ─────────────────────────────────────────────────────────────────────────────

SYLLABUS_HTML = """
<h1>CS 401R: Engineering Production AI Systems</h1>
<h2>Brigham Young University — Fall 2026</h2>

<p><strong>Instructor:</strong> Scott Toborg &nbsp;|&nbsp; <strong>Email:</strong> scott@toborg.com<br>
<strong>Meeting Times:</strong> Tuesday &amp; Thursday, 75 minutes<br>
<strong>Dates:</strong> Sep 3 – Dec 10, 2026 &nbsp;|&nbsp;
<strong>Credits:</strong> 3 &nbsp;|&nbsp; <strong>Format:</strong> In-person + AWS lab</p>

<h2>Course Description</h2>
<p>This course teaches engineers how to build, ship, and operate AI systems at production scale
inside real enterprises. We move from theory to working systems: you will design platform architectures,
build data and model pipelines, rigorously evaluate AI outputs, deploy with confidence, and operate
those systems with the economic, governance, and reliability discipline that enterprise stakeholders demand.</p>
<p>The course is organized around a single running case study — <strong>NorthStar Retail</strong> —
a fictional but architecturally realistic enterprise AI deployment. Every lab builds one layer of that system.
By the end, you will have designed and prototyped a complete, end-to-end enterprise AI platform on AWS.</p>
<p><strong>Primary text:</strong> <em>Engineering the AI Enterprise: Orchestrating Strategy, Product, and Execution</em>
(Toborg, 2026) — Parts 3 and 4. Draft chapters distributed as PDFs on Canvas. Do not share outside the course.</p>

<h2>Prerequisites</h2>
<ul>
  <li>CS 240 or equivalent (Advanced Software Construction)</li>
  <li>CS 270 or equivalent (Introduction to Machine Learning)</li>
  <li>Recommended: CS 301R, CS 329, CS 452, CS 574</li>
  <li>Strong Python; working SQL; cloud computing familiarity</li>
</ul>

<h2>Learning Objectives</h2>
<p>By the end of this course, you will be able to:</p>
<ol>
  <li>Design a production-grade AI platform architecture on AWS with IaC, feature stores, and model registries</li>
  <li>Build end-to-end data and feature engineering pipelines that handle real-world distribution shift</li>
  <li>Train, fine-tune, and deploy models across the full development spectrum — prompt engineering to RAG to agents</li>
  <li>Apply XOps discipline (DataOps, MLOps, LLMOps, AgentOps) to automate the model lifecycle</li>
  <li>Implement CI/CD pipelines for AI with canary, blue/green, and shadow deployment strategies</li>
  <li>Evaluate AI quality rigorously across predictive, generative, and agentic systems</li>
  <li>Operate AI systems: monitoring, drift detection, reliability engineering, and incident response</li>
  <li>Measure and communicate AI business value to engineering and executive audiences</li>
  <li>Manage AI costs using FinOps discipline</li>
  <li>Design governance frameworks that scale to agentic AI systems</li>
</ol>

<h2>Grading</h2>
<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;width:100%">
  <tr><th>Component</th><th style="text-align:center">Weight</th><th>Notes</th></tr>
  <tr><td>Labs (7 total)</td><td style="text-align:center">60%</td><td>~8.57% each, equally weighted</td></tr>
  <tr><td>Final Project</td><td style="text-align:center">25%</td><td>Team-based; full NorthStar system design + presentation</td></tr>
  <tr><td>Reading Quizzes</td><td style="text-align:center">10%</td><td>Weekly — opens Saturday, due Monday night before class</td></tr>
  <tr><td>Participation</td><td style="text-align:center">5%</td><td>In-class contribution quality, not attendance</td></tr>
</table>

<p><strong>Late Policy:</strong> Labs lose 10% per calendar day late. Contact me <em>before</em> the deadline
if you have a documented emergency — not after.</p>
<p><strong>Grade Scale:</strong> A 93+, A- 90–92, B+ 87–89, B 83–86, B- 80–82, C+ 77–79, C 73–76, below 73 see instructor.</p>

<h2>Course Policies</h2>
<p><strong>Attendance:</strong> Not graded. This course moves fast. Missing a lecture is your problem to solve.</p>
<p><strong>AI Tools:</strong> You may use AI coding assistants (GitHub Copilot, Claude, etc.) for lab work.
You must understand and be able to explain everything you submit. Cannot explain it in office hours = no credit.</p>
<p><strong>Academic Honesty:</strong> BYU Honor Code applies. Sharing lab solutions before the Saturday due date
is academic dishonesty.</p>
<p><strong>Office Hours:</strong> Posted on Canvas. Email for appointments outside posted hours.</p>
"""

NORTHSTAR_HTML = """
<h1>NorthStar Retail — Case Overview</h1>
<p>Every lab in CS 401R builds a layer of the same system. This page is your reference for the company,
the AI initiative, and the data you'll work with all semester.</p>

<h2>The Company</h2>
<p><strong>NorthStar Retail</strong> is a fictional specialty retailer: 400 stores across North America,
growing e-commerce presence, ~$3.2B annual revenue. The architecture and operational challenges are
modeled on real enterprise retailers at this scale.</p>

<h2>The AI Initiative</h2>
<p>NorthStar's Chief Data Officer has commissioned three AI systems to drive customer retention and lifetime value:</p>
<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;width:100%">
  <tr><th>System</th><th>Type</th><th>Business Goal</th></tr>
  <tr><td><strong>Churn Prediction</strong></td><td>Batch ML (XGBoost)</td>
      <td>Identify at-risk customers 90 days before churn; trigger retention offers</td></tr>
  <tr><td><strong>Offer Generation</strong></td><td>LLM / RAG</td>
      <td>Personalize retention offers using customer history and product catalog</td></tr>
  <tr><td><strong>Customer Service Agent</strong></td><td>Agentic AI</td>
      <td>Handle order inquiries, returns, and escalations autonomously</td></tr>
</table>
<p>All three systems share a single AWS platform. You build that platform across the seven labs.</p>

<h2>Data Sources (All Synthetic — No Real PII)</h2>
<ul>
  <li><code>customers.csv</code> — 250,000 customer records: demographics, tenure, loyalty tier</li>
  <li><code>transactions.parquet</code> — 18 months of purchase history (~4.2M rows)</li>
  <li><code>clickstream.parquet</code> — web/app behavior events, last 90 days (~8.1M rows)</li>
  <li><code>store_events.csv</code> — 400 stores, 18 months of promotions and inventory events</li>
  <li><code>product_catalog.json</code> — 12,000 SKUs: descriptions, categories, pricing</li>
  <li><code>policy_docs/</code> — return policy, loyalty program terms, FAQs (for RAG in Lab 3)</li>
</ul>

<h2>Repository Structure</h2>
<p>You maintain <strong>one GitHub repository</strong> for the entire semester. Each lab adds a folder.</p>
<pre style="background:#f4f4f4;padding:12px;border-radius:4px">
northstar-ai-platform/
├── README.md                  ← Platform overview, updated each lab
├── infrastructure/            ← Lab 1: Terraform IaC
├── data/                      ← Lab 2: Pipelines and features
├── models/                    ← Lab 3: Model development
├── pipeline/                  ← Lab 4: CI/CD automation
├── deployment/                ← Lab 5: Deployment and security
├── monitoring/                ← Lab 6: Observability and reliability
└── docs/                      ← Written reports, one per lab
</pre>

<h2>Starter Kit Progression</h2>
<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;width:100%">
  <tr><th>Lab</th><th>Data</th><th>Infrastructure Templates</th><th>Code Scaffolding</th></tr>
  <tr><td>1</td><td>Schema + sample</td><td>Terraform module structure</td><td>None</td></tr>
  <tr><td>2</td><td>Full synthetic dataset</td><td>Glue job skeleton</td><td>None</td></tr>
  <tr><td>3</td><td>Evaluation harness</td><td>None</td><td>Training script skeleton</td></tr>
  <tr><td>4</td><td>None</td><td>CodePipeline YAML starter</td><td>Test template</td></tr>
  <tr><td>5–7</td><td>None</td><td>None</td><td>None</td></tr>
</table>
"""

AWS_SETUP_HTML = """
<h1>AWS Educate Setup Guide</h1>
<p>All lab work runs on AWS SageMaker. Complete these steps <strong>before Lab 1</strong>.</p>

<h2>Step 1 — Activate AWS Educate</h2>
<ol>
  <li>You will receive an AWS Educate invitation at your BYU email. Accept it.</li>
  <li>AWS Educate provides credits for this course. Do <strong>not</strong> enter a personal credit card.</li>
  <li>Access the AWS Console through the Educate portal — not directly at aws.amazon.com.</li>
</ol>

<h2>Step 2 — Set a Budget Alert (Do This First)</h2>
<ol>
  <li>AWS Console → Billing → Budgets → Create Budget</li>
  <li>Set a monthly budget equal to your total credit amount</li>
  <li>Alert at 80% threshold → your BYU email</li>
</ol>
<p>If you exhaust your credits, contact the instructor immediately. Do not enter personal payment info.</p>

<h2>Step 3 — Install Terraform</h2>
<ul>
  <li>macOS: <code>brew install terraform</code></li>
  <li>Windows: download from terraform.io → add to PATH</li>
  <li>Linux: use tfenv or download binary</li>
</ul>
<p>Verify: <code>terraform version</code> should return 1.5+</p>

<h2>Step 4 — Configure AWS CLI</h2>
<pre style="background:#f4f4f4;padding:12px;border-radius:4px">pip install awscli
aws configure
# Access Key ID: [from AWS Educate portal]
# Secret Access Key: [from AWS Educate portal]
# Default region: us-east-1
# Output format: json</pre>

<h2>Step 5 — Verify SageMaker Access</h2>
<p>Navigate to Amazon SageMaker in the AWS Console. Confirm you can open the Studio dashboard.
Permission errors → email the instructor before Lab 1 class.</p>

<h2>Cost Guardrails</h2>
<ul>
  <li>Stop SageMaker Studio instances when not in use — they bill by the hour</li>
  <li>Use <code>ml.t3.medium</code> for development; reserve <code>ml.m5.xlarge</code> for training jobs only</li>
  <li>Terminate training jobs running longer than 30 minutes — something is wrong</li>
  <li>Delete SageMaker endpoints after submitting each lab — endpoints bill 24/7</li>
</ul>
"""


# ─────────────────────────────────────────────────────────────────────────────
# Builder Functions
# ─────────────────────────────────────────────────────────────────────────────

def build_assignment_groups():
    print("\n── Assignment Groups ──")
    # Remove the default "Assignments" group (fresh shell only has one)
    existing = get_all("/assignment_groups")
    new_group_names = {g["name"] for g in ASSIGNMENT_GROUPS}
    for g in existing:
        if g["name"] not in new_group_names:
            if delete(f"/assignment_groups/{g['id']}"):
                print(f"  ✓ Removed default group: {g['name']}")

    group_ids = {}
    for grp in ASSIGNMENT_GROUPS:
        r = post("/assignment_groups", {"assignment_group": grp}, grp["name"])
        if r:
            group_ids[grp["name"]] = r["id"]

    # Enable weighted grading on the course
    put("", {"course": {"apply_assignment_group_weights": True}}, "Weighted grading enabled")
    return group_ids


def build_modules():
    print("\n── Modules ──")
    module_ids = {}
    for i, name in enumerate(MODULE_NAMES, 1):
        r = post("/modules", {"module": {"name": name, "position": i}}, name)
        if r:
            module_ids[name] = r["id"]
    return module_ids


def add_to_module(module_ids, module_name, item_type, content_id, title):
    mid = module_ids.get(module_name)
    if not mid:
        print(f"  ✗ Module not found: {module_name}")
        return
    post(f"/modules/{mid}/items", {
        "module_item": {
            "title": title,
            "type": item_type,
            "content_id": content_id,
        }
    })


def build_labs(module_ids, group_ids):
    print("\n── Lab Assignments ──")
    lab_gid = group_ids.get("Labs")
    for lab in LABS:
        r = post("/assignments", {
            "assignment": {
                "name":                 lab["name"],
                "description":          resolve_links(lab_html(lab["n"])),
                "due_at":               lab["due_at"],
                "unlock_at":            lab["unlock_at"],
                "points_possible":      100,
                "assignment_group_id":  lab_gid,
                "submission_types":     ["online_url"],
                "allowed_attempts":     -1,
                "published":            False,
            }
        }, lab["name"])
        if r:
            add_to_module(module_ids, lab["module"], "Assignment", r["id"], lab["name"])


def build_prelabs(module_ids, group_ids):
    """Create the two pre-lab exercises as 0-point, due-dated assignments.

    0 points is deliberate: each is graded inside the lab it gates. The due
    date is the payload -- it is what puts these on the calendar early enough
    for the AWS approval time to elapse.
    """
    print("\n── Pre-Lab Exercises ──")
    lab_gid = group_ids.get("Labs")
    for pl in PRELABS:
        r = post("/assignments", {
            "assignment": {
                "name":                 pl["name"],
                "description":          resolve_links(pl["html"]),
                "due_at":               pl["due_at"],
                "unlock_at":            pl["unlock_at"],
                "points_possible":      0,
                "assignment_group_id":  lab_gid,
                "submission_types":     ["online_text_entry", "online_upload"],
                "allowed_attempts":     -1,
                "published":            False,
            }
        }, pl["name"])
        if r:
            add_to_module(module_ids, pl["module"], "Assignment", r["id"], pl["name"])


def build_final_project(module_ids, group_ids):
    print("\n── Final Project ──")
    fp_gid = group_ids.get("Final Project")
    for fa in FINAL_ASSIGNMENTS:
        r = post("/assignments", {
            "assignment": {
                "name":                 fa["name"],
                "description":          fa["html"],
                "due_at":               fa["due_at"],
                "unlock_at":            fa["unlock_at"],
                "points_possible":      fa["points"],
                "assignment_group_id":  fp_gid,
                "submission_types":     fa["types"],
                "published":            False,
            }
        }, fa["name"])
        if r:
            add_to_module(module_ids, fa["module"], "Assignment", r["id"], fa["name"])


def build_participation(module_ids, group_ids):
    print("\n── Participation ──")
    r = post("/assignments", {
        "assignment": {
            "name":                 "Participation — Full Semester",
            "description":          "<p>In-class contribution quality across the full semester, assessed by the instructor at end of term. This is not an attendance grade.</p>",
            "points_possible":      100,
            "assignment_group_id":  group_ids.get("Participation"),
            "submission_types":     ["none"],
            "published":            False,
        }
    }, "Participation")
    if r:
        add_to_module(module_ids, "Start Here", "Assignment", r["id"], "Participation — Full Semester")


def build_quizzes(module_ids, group_ids):
    print("\n── Reading Quizzes ──")
    quiz_gid = group_ids.get("Reading Quizzes")
    for name, open_sat, due_mon, module_name in QUIZZES:
        r = post("/quizzes", {
            "quiz": {
                "title":                name,
                "quiz_type":            "assignment",
                "points_possible":      10,
                "assignment_group_id":  quiz_gid,
                "unlock_at":            quiz_open(open_sat),
                "due_at":               due(due_mon),
                "lock_at":              due(due_mon),
                "time_limit":           15,
                "allowed_attempts":     1,
                "show_correct_answers": True,
                "published":            False,
                "description":          (
                    "<p>Covers assigned readings for both class sessions this week. "
                    "Opens Saturday at 8 AM. You have 15 minutes and one attempt. "
                    "Due by Monday night before class.</p>"
                ),
            }
        }, name)
        if r:
            add_to_module(module_ids, module_name, "Quiz", r["id"], name)


OFFICE_HOURS_HTML = """
<h2>Office Hours</h2>

<p><strong>Tuesdays and Thursdays, immediately after class</strong> &mdash; or by appointment.</p>

<p>No appointment is needed for the after-class slot; just stay. For anything that needs
more time, or a different day, email me and we will find one.</p>

<h3>What office hours are good for</h3>
<ul>
  <li><strong>AWS problems you cannot reproduce.</strong> Bring the exact error text and the
      command that produced it &mdash; not a screenshot of the console.</li>
  <li><strong>Design decisions before you build.</strong> Cheaper here than in a rubric.</li>
  <li><strong>Anything blocked on an external approval</strong> &mdash; Bedrock access, a
      SageMaker quota increase. Come early; those have lead times neither of us controls.</li>
</ul>

<p>If you are stuck on something with a deadline, come before the deadline, not after.</p>
"""


def build_pages(module_ids):
    print("\n── Pages ──")
    pages = [
        {
            "title":      "Course Syllabus",
            "body":       SYLLABUS_HTML,
            "module":     "Start Here",
            "front_page": True,
        },
        {
            "title":  "NorthStar Retail — Case Overview",
            "body":   NORTHSTAR_HTML,
            "module": "Start Here",
        },
        {
            "title":  "AWS Educate Setup Guide",
            "body":   AWS_SETUP_HTML,
            "module": "Start Here",
        },
        {
            "title":  "Office Hours",
            "body":   OFFICE_HOURS_HTML,
            "module": "Start Here",
        },
    ]
    for page in pages:
        r = post("/pages", {
            "wiki_page": {
                "title":      page["title"],
                "body":       page["body"],
                "published":  False,
            }
        }, page["title"])
        if r:
            page_url = r.get("url", "")
            mid = module_ids.get(page["module"])
            if mid and page_url:
                post(f"/modules/{mid}/items", {
                    "module_item": {
                        "title":    page["title"],
                        "type":     "Page",
                        "page_url": page_url,
                    }
                })
            if page.get("front_page") and page_url:
                put(f"/pages/{page_url}", {"wiki_page": {"front_page": True}}, "Front page set")


def update_canvas_syllabus_tab():
    """Populate the Canvas Syllabus tab (the dedicated course syllabus view)."""
    print("\n── Canvas Syllabus Tab ──")
    put("", {"course": {"syllabus_body": SYLLABUS_HTML}}, "Syllabus tab updated")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def sync_prelabs_and_labs():
    """Additive, re-runnable update for a course that already exists.

    main() is NOT idempotent -- running it twice duplicates every assignment,
    and the documented remedy is Reset Course Content, which wipes the course.
    That is far too blunt for adding two pre-labs and correcting a rubric line.

    This mode instead:
      * uploads the pre-lab guides (overwrite-on-duplicate, so safe to repeat)
      * UPDATES Lab 3 and Lab 4 descriptions in place, matched by name
      * creates the two pre-lab assignments, or updates them if already present
    It never creates a second copy of anything.
    """
    print("CS 401R Canvas — additive sync (no duplicates, no reset)")
    print(f"Target: {BASE_URL}/courses/{COURSE_ID}\n")

    validate_all_labs()
    build_prelab_files()
    build_lab_files()
    build_starter_kits()

    existing = {a["name"]: a["id"] for a in get_all("/assignments")}
    print(f"\n── Found {len(existing)} existing assignments ──")

    # Lab bodies that gained prerequisite banners
    print("\n── Updating lab descriptions ──")
    for lab in LABS:
        aid = existing.get(lab["name"])
        if not aid:
            print(f"  ✗ not found in course: {lab['name']} (skipped)")
            continue
        put(f"/assignments/{aid}",
            {"assignment": {"description": resolve_links(lab_html(lab["n"]))}},
            f"updated {lab['name']}")

    # Pre-labs: create or update
    print("\n── Pre-lab assignments ──")
    group_ids = {g["name"]: g["id"] for g in get_all("/assignment_groups")}
    module_ids = {m["name"]: m["id"] for m in get_all("/modules")}
    lab_gid = group_ids.get("Labs")

    for pl in PRELABS:
        payload = {
            "name":                pl["name"],
            "description":         resolve_links(pl["html"]),
            "due_at":              pl["due_at"],
            "unlock_at":           pl["unlock_at"],
            "points_possible":     0,
            "assignment_group_id": lab_gid,
            "submission_types":    ["online_text_entry", "online_upload"],
            "allowed_attempts":    -1,
            "published":           False,
        }
        aid = existing.get(pl["name"])
        if aid:
            put(f"/assignments/{aid}", {"assignment": payload}, f"updated {pl['name']}")
        else:
            r = post("/assignments", {"assignment": payload}, f"created {pl['name']}")
            if r:
                mid = module_ids.get(pl["module"])
                if mid:
                    post(f"/modules/{mid}/items", {"module_item": {
                        "title": pl["name"], "type": "Assignment", "content_id": r["id"]}})

    print("\n✓ Sync complete. Nothing was duplicated; new items are DRAFTS.")
    print(f"  Review: {BASE_URL}/courses/{COURSE_ID}/assignments")


def main():
    print(f"CS 401R Canvas Builder")
    print(f"Target: {BASE_URL}/courses/{COURSE_ID}\n")

    group_ids  = build_assignment_groups()
    module_ids = build_modules()

    validate_all_labs()
    build_prelab_files()
    build_lab_files()
    build_starter_kits()
    build_labs(module_ids, group_ids)
    build_prelabs(module_ids, group_ids)
    build_final_project(module_ids, group_ids)
    build_participation(module_ids, group_ids)
    build_quizzes(module_ids, group_ids)
    build_pages(module_ids)
    update_canvas_syllabus_tab()

    print(f"\n✓ Done. All items created as DRAFTS.")
    print(f"  Review and publish: {BASE_URL}/courses/{COURSE_ID}/modules")
    print(f"\nNext steps:")
    print(f"  1. Add quiz questions (12 quizzes are shells — no questions yet)")
    print(f"  2. Upload starter kit files to the Files section")
    print(f"  3. Upload chapter PDFs to the Readings folder")
    print(f"  4. Publish modules when ready")


if __name__ == "__main__":
    # `--sync` updates an existing course in place. Bare invocation builds the
    # whole course from scratch and WILL duplicate if the course is not empty.
    if "--sync" in sys.argv:
        sync_prelabs_and_labs()
        sys.exit(0)
    main()
