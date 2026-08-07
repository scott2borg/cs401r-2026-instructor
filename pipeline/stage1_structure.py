"""
Stage 1 — Canvas Course Structure
Creates/updates: assignment groups, modules, lab assignments,
final project, quizzes, and content pages.
All operations are idempotent.
"""

import os
import pathlib
from datetime import datetime, timedelta, timezone
from .canvas_api import CanvasAPI
from . import lab_content

MDT = timezone(timedelta(hours=-6))

def to_utc(date_str: str, hour: int = 23, minute: int = 59) -> str:
    local = datetime.strptime(date_str, "%Y-%m-%d").replace(
        hour=hour, minute=minute, second=0, tzinfo=MDT)
    return local.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def due(d):       return to_utc(d, 23, 59)
def open_at(d):   return to_utc(d,  8,  0)
def unlock(d):    return to_utc(d,  9,  0)


# ── Page content ─────────────────────────────────────────────────────────────

def grading_table(cfg: dict) -> str:
    """Grading table, GENERATED from cfg["grading"]["groups"].

    This was hardcoded HTML listing Labs 60 / Project 25 / Quizzes 10 /
    Participation 5. Change the weights in the config and the syllabus kept
    showing the old ones -- the same drift that put a retired gate in front of
    students. There is now one source.
    """
    rows = "\n".join(
        f'  <tr><td>{g["name"]}</td><td>{g["weight"]}%</td>'
        f'<td>{g.get("notes","")}</td></tr>'
        for g in cfg["grading"]["groups"])
    total = sum(g["weight"] for g in cfg["grading"]["groups"])
    if total != 100:
        raise SystemExit(
            f"\nREFUSING TO BUILD: grading weights total {total}%, not 100%.\n"
            f"  Fix `grading.groups` in course_config.yaml.")
    return ('<table border="1" cellpadding="6" cellspacing="0" '
            'style="border-collapse:collapse;width:100%">\n'
            '  <tr><th>Component</th><th>Weight</th><th>Notes</th></tr>\n'
            + rows + '\n</table>')


def syllabus_html(cfg: dict) -> str:
    c = cfg["course"]
    return f"""
<h1>{c['title']}</h1>
<h2>Brigham Young University — {c['semester']}</h2>
<p><strong>Instructor:</strong> {c['instructor']} &nbsp;|&nbsp;
   <strong>Email:</strong> {c['email']}<br>
<strong>Dates:</strong> {c['start_date']} – {c['end_date']} &nbsp;|&nbsp;
<strong>Credits:</strong> {c['credits']} &nbsp;|&nbsp;
<strong>Format:</strong> {c['format']}</p>

<h2>Grading</h2>
{grading_table(cfg)}
<p><strong>Late Policy:</strong> Labs lose 10% per calendar day late. Contact instructor before the deadline.</p>
<p><strong>AI Tools:</strong> Coding assistants permitted. You must explain everything you submit.</p>
<p><strong>Academic Honesty:</strong> BYU Honor Code applies. Sharing lab solutions before the due date is dishonesty.</p>
"""


def northstar_html() -> str:
    return """
<h1>NorthStar Retail — Case Overview</h1>
<p><strong>NorthStar Retail</strong> is a fictional specialty retailer: 400 stores across North America,
growing e-commerce presence, ~$3.2B annual revenue.</p>
<h2>AI Systems</h2>
<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;width:100%">
  <tr><th>System</th><th>Type</th><th>Business Goal</th></tr>
  <tr><td>Churn Prediction</td><td>Batch ML (XGBoost)</td><td>Identify at-risk customers 90 days before churn</td></tr>
  <tr><td>Offer Generation</td><td>LLM / RAG</td><td>Personalize retention offers</td></tr>
  <tr><td>Customer Service Agent</td><td>Agentic AI</td><td>Handle inquiries and escalations autonomously</td></tr>
</table>
<h2>Repository Structure</h2>
<pre style="background:#f4f4f4;padding:12px;border-radius:4px">
northstar-ai-platform/
├── infrastructure/    ← Lab 1: Terraform IaC
├── data/              ← Lab 2: Pipelines and features
├── models/            ← Lab 3: Model development
├── pipeline/          ← Lab 4: CI/CD
├── deployment/        ← Lab 5: Deployment
├── monitoring/        ← Lab 6: Observability
└── docs/              ← Written reports
</pre>
"""


def aws_setup_html() -> str:
    return """
<h1>AWS Educate Setup Guide</h1>
<p>Complete before Lab 1.</p>
<h2>Step 1 — Activate AWS Educate</h2>
<p>Accept the invitation at your BYU email. Do not enter a personal credit card.</p>
<h2>Step 2 — Set a Budget Alert</h2>
<p>Billing → Budgets → Create Budget. Set alert at 80% of your credit limit.</p>
<h2>Step 3 — Install Terraform</h2>
<pre>brew install terraform   # macOS
terraform version        # verify 1.5+</pre>
<h2>Step 4 — Configure AWS CLI</h2>
<pre>pip install awscli
aws configure   # use credentials from AWS Educate portal; region: us-east-1</pre>
<h2>Cost Guardrails</h2>
<ul>
  <li>Stop Studio instances when not in use — they bill hourly</li>
  <li>Use ml.t3.medium for development; ml.m5.xlarge for training only</li>
  <li>Delete SageMaker endpoints after each lab submission</li>
</ul>
"""


# ── Lab HTML description builder ─────────────────────────────────────────────


BASE = pathlib.Path(__file__).resolve().parent.parent


def office_hours_html() -> str:
    return """
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


def prelab_html(pl: dict) -> str:
    """Assignment body for a pre-lab: a short summary plus a link to the guide."""
    link = PRELAB_GUIDE_LINKS.get(pl["number"], "")
    gates = pl.get("gates", "")
    return f"""
<p><strong>Assigned:</strong> {pl['assigned']} &nbsp;|&nbsp; <strong>Due:</strong> {pl['due']}<br>
<strong>Gates:</strong> {gates}</p>

<p style="border-left:4px solid #c8102e;padding:.5rem .9rem;background:#fafafa">
This is an out-of-band prerequisite. It is worth <strong>0 points on its own</strong> and is
graded inside the lab it gates &mdash; but the lab cannot be completed until the AWS approval
it asks for has landed, and that approval time is not yours to control.
<strong>Do it in September, not the week the lab is due.</strong></p>

<p><strong>Full instructions:</strong> {link or '<em>see the course repository</em>'}</p>
"""


def upload_guides(cfg: dict, api: CanvasAPI):
    """Render the lab and pre-lab markdown to HTML and upload to Canvas Files."""
    import tempfile
    print("\n  Guides -> Canvas Files")

    lab_folder = api.get_or_create_folder("Lab Guides")
    if lab_folder:
        for n in sorted(lab_content.LAB_FILES):
            parsed = lab_content.parse_lab(n)
            html = lab_content.md_to_html_full(parsed)
            with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False,
                                             encoding="utf-8") as t:
                t.write(html); tmp = t.name
            fid = api.upload_file(tmp, f"{parsed['path'].stem}.html",
                                  lab_folder, "text/html")
            os.unlink(tmp)
            if fid:
                LAB_GUIDE_LINKS[n] = _file_link(api, fid, "Open the full lab guide")
                print(f"    ok  Lab {n} guide")

    pre_folder = api.get_or_create_folder("Pre-Lab Guides")
    if pre_folder:
        for pl in cfg.get("prelabs", []):
            src = BASE / pl["guide"]
            if not src.exists():
                print(f"    !!  missing guide: {src}")
                continue
            parsed = {"body": src.read_text(), "title": pl["title"], "path": src}
            html = lab_content.md_to_html_full(parsed)
            with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False,
                                             encoding="utf-8") as t:
                t.write(html); tmp = t.name
            fid = api.upload_file(tmp, f"{src.stem}.html", pre_folder, "text/html")
            os.unlink(tmp)
            if fid:
                PRELAB_GUIDE_LINKS[pl["number"]] = _file_link(
                    api, fid, f"Pre-Lab {pl['number']} — full guide")
                print(f"    ok  Pre-Lab {pl['number']} guide")


def _file_link(api: CanvasAPI, fid: int, label: str) -> str:
    return (f'<a class="instructure_file_link inline_disabled" '
            f'href="/courses/{api.course_id}/files/{fid}?wrap=1" '
            f'target="_blank" rel="noopener">{label}</a>')


def academy_html(a: dict) -> str:
    """Assignment body for an AWS Academy prerequisite course."""
    return f"""
<p><strong>Opens:</strong> {a['assigned']} (first day of class) &nbsp;|&nbsp;
<strong>Due:</strong> {a['due']}, 11:59 PM MDT</p>

<h2>What to do</h2>
<p>Complete <strong>{a['course']}</strong> in AWS Academy, then submit a
screenshot or PDF of your course-completion page showing your name and the
completion date.</p>

<p style="border-left:4px solid #c8102e;padding:.5rem .9rem;background:#fafafa">
This overlaps Lab 1 on purpose. Lab 1 is deliberately light, and this is
self-paced coursework you can do in evenings &mdash; but it is <strong>not
something to leave until the due date</strong>, because the modules take longer
than they look and the completion page is the only accepted proof.</p>

<h2>Which AWS account</h2>
<p>These courses run in the <strong>AWS Academy Learner Lab</strong>, which is
separate from the personal AWS account you use for the labs. The Learner Lab is
used for these prerequisite courses <em>only</em> &mdash; every lab in this
course runs on your own account. See the AWS Educate Setup Guide.</p>

<h2>Submission</h2>
<p>Upload the completion snapshot. A screenshot that does not show your name and
the completion date will be returned.</p>
"""


def lab_html(lab: dict) -> str:
    """Assignment description, GENERATED from the authoritative lab markdown.

    This used to be a ten-line stub that printed the due date and told the
    student to go find a "Lab Guide page". Everything substantive -- objective,
    starter kit, task breakdown, point split -- either lived nowhere or lived
    in a second hand-maintained copy that drifted. On 2026-08-04 a hand-written
    copy shipped a promotion gate to students that had been retired two days
    earlier ("AUC-ROC >= 0.72").

    lab_content.py parses Lab_N--*.md for the meta block, prerequisite banners,
    Objective, Starter Kit inventory and the `### Task N — ... (X points)`
    headings. Edit the markdown; Canvas follows. Do not edit a lab description
    in the Canvas editor -- the next run overwrites it.
    """
    n = lab["number"]
    parsed = lab_content.parse_lab(n)
    body = lab_content.lab_summary_html(parsed, LAB_GUIDE_LINKS.get(n, ""))
    body = resolve_prelab_links(body)
    return body + f"""
<h2>Submission</h2>
<p>Submit a GitHub repository link before the deadline.
A repo that does not clone cleanly loses 20 points automatically.
Never commit AWS credentials — committed secrets = automatic 0.</p>
<p><strong>Late policy:</strong> 10% per calendar day. Contact instructor before the deadline, not after.</p>
"""


# Populated by stage 1 before assignments are written, so the generated
# descriptions can link to the uploaded guides instead of falling back to
# "see the course repository".
LAB_GUIDE_LINKS = {}
PRELAB_GUIDE_LINKS = {}


def resolve_prelab_links(html: str) -> str:
    """Swap {{PRELAB_N_LINK}} tokens for real Canvas file links."""
    for n, link in PRELAB_GUIDE_LINKS.items():
        html = html.replace("{{PRELAB_%d_LINK}}" % n, link)
    # Anything still unresolved degrades to readable text rather than a
    # literal {{...}} in front of a student.
    import re as _re
    return _re.sub(r"\{\{PRELAB_(\d)_LINK\}\}",
                   lambda m: "<em>Pre-Lab %s guide (see the course repository)</em>" % m.group(1),
                   html)


# ── Main stage function ───────────────────────────────────────────────────────

def run(cfg: dict, api: CanvasAPI):
    print("\n[Stage 1] Canvas Course Structure")

    # Course dates
    print("\n  Course dates")
    # Check the result. This used to print a check mark unconditionally, so a
    # 401 produced "x 401 PUT ..." immediately followed by "OK Start/end dates
    # set" -- the run reported success on the same line it reported failure.
    # A stage that cannot tell whether its write landed is not a stage.
    r = api.set_course_dates(
        to_utc(cfg["course"]["start_date"], 0, 0),
        to_utc(cfg["course"]["end_date"], 23, 59),
    )
    if r is None or (hasattr(r, "ok") and not r.ok):
        print("    ✗ Start/end dates NOT set — aborting stage 1")
        raise SystemExit(
            "\nStage 1 could not authenticate to Canvas. Nothing was written.\n"
            "Diagnose the token without revealing it:  python check_token.py"
        )
    print("    ✓ Start/end dates set")

    # Assignment groups
    print("\n  Assignment groups")
    existing_groups = api.get_assignment_groups()
    # Remove default "Assignments" group if present
    # Deferred: the default group can only be removed once the Labs group
    # exists to receive anything filed in it. Deleting first destroys those
    # assignments, which is what happened on 2026-08-05.
    _default_group = existing_groups.get("Assignments")

    group_ids = {}
    for i, grp in enumerate(cfg["grading"]["groups"], 1):
        gid = api.ensure_assignment_group(
            grp["name"], grp["weight"], i, existing_groups)
        if gid:
            group_ids[grp["name"]] = gid
    api.set_weighted_grading(cfg["grading"]["weighted"])

    # Now that Labs exists, the default group can go -- with its assignments
    # moved rather than deleted.
    if _default_group and group_ids.get("Labs"):
        api.delete_assignment_group(_default_group, move_to=group_ids["Labs"])
        print("    ✓ Removed default Assignments group (assignments moved to Labs)")

    # Modules
    print("\n  Modules")
    existing_modules = api.get_modules()
    module_ids = {}
    for i, name in enumerate(cfg["modules"], 1):
        mid = api.ensure_module(name, i, existing_modules)
        if mid:
            module_ids[name] = mid
        elif name in existing_modules:
            module_ids[name] = existing_modules[name]

    # Content pages
    print("\n  Pages")
    existing_pages = api.get_pages()
    syl_url = api.ensure_page("Course Syllabus",
                              syllabus_html(cfg), existing_pages, published=True)
    api.ensure_page("NorthStar Retail — Case Overview",
                    northstar_html(), existing_pages)
    api.ensure_page("AWS Educate Setup Guide",
                    aws_setup_html(), existing_pages)
    if syl_url:
        api.set_front_page(syl_url)
    api.set_syllabus(syllabus_html(cfg))
    # Add pages to Start Here module
    start_here_id = module_ids.get("Start Here")
    if start_here_id:
        existing_pages_now = api.get_pages()
        for page_title in ["Course Syllabus",
                           "NorthStar Retail — Case Overview",
                           "AWS Educate Setup Guide"]:
            if page_title in existing_pages_now:
                api.add_module_page(start_here_id,
                                    existing_pages_now[page_title], page_title)

    # Office hours page
    api.ensure_page("Office Hours", office_hours_html(), api.get_pages())
    if start_here_id:
        _pages = api.get_pages()
        if "Office Hours" in _pages:
            api.add_module_page(start_here_id, _pages["Office Hours"], "Office Hours")

    # Guides -> Canvas Files. Must happen BEFORE the assignments below, because
    # the generated descriptions link to these files; upload after, and every
    # link silently degrades to "see the course repository".
    upload_guides(cfg, api)

    # Lab assignments
    print("\n  Lab assignments")
    existing_assignments = api.get_assignments()
    labs_gid = group_ids.get("Labs")
    for lab in cfg["labs"]:
        name = f"Lab {lab['number']} — {lab['title']}"
        payload = {
            "assignment": {
                "name":                name,
                "description":         lab_html(lab),
                "due_at":              due(lab["due"]),
                "unlock_at":           unlock(lab["assigned"]),
                "points_possible":     lab["points"],
                "assignment_group_id": labs_gid,
                "submission_types":    ["online_url"],
                "allowed_attempts":    -1,
                "published":           False,
            }
        }
        aid = api.ensure_assignment(payload, existing_assignments)
        if aid:
            mid = module_ids.get(lab["module"])
            if mid:
                api.add_module_item(mid, "Assignment", aid, name)

    # Pre-lab assignments
    print("\n  Pre-lab exercises")
    for pl in cfg.get("prelabs", []):
        payload = {
            "assignment": {
                "name":                pl["title"],
                "description":         resolve_prelab_links(prelab_html(pl)),
                "due_at":              due(pl["due"]),
                "unlock_at":           unlock(pl["assigned"]),
                "points_possible":     pl.get("points", 0),
                "assignment_group_id": labs_gid,
                "submission_types":    ["online_text_entry", "online_upload"],
                "allowed_attempts":    -1,
                "published":           False,
            }
        }
        aid = api.ensure_assignment(payload, existing_assignments)
        if aid:
            mid = module_ids.get(pl["module"])
            if mid:
                api.add_module_item(mid, "Assignment", aid, pl["title"])

    # Final project
    print("\n  Final project")
    fp_gid = group_ids.get("Final Project")
    fp = cfg["final_project"]
    for item in [
        {
            "name": "Team Sign-Up (due Nov 25)",
            "desc": "<p>Submit team roster (names + NetIDs) before the deadline. 2–3 students per team.</p>",
            "due":  fp["teams_due"],
            "pts":  0,
            "types": ["online_text_entry"],
            "module": fp["team_module"],
        },
        {
            "name": "Final Project — NorthStar AI Platform Design",
            "desc": "<p>Technical design document covering all course layers. See Final Project instructions page for full rubric.</p>",
            "due":  fp["submission_due"],
            "pts":  fp["points"],
            "types": ["online_upload", "online_url"],
            "module": fp["submit_module"],
        },
    ]:
        payload = {
            "assignment": {
                "name":                item["name"],
                "description":         item["desc"],
                "due_at":              due(item["due"]),
                "unlock_at":           unlock(cfg["course"]["start_date"]),
                "points_possible":     item["pts"],
                "assignment_group_id": fp_gid,
                "submission_types":    item["types"],
                "published":           False,
            }
        }
        aid = api.ensure_assignment(payload, existing_assignments)
        if aid:
            mid = module_ids.get(item["module"])
            if mid:
                api.add_module_item(mid, "Assignment", aid, item["name"])

    # AWS Academy prerequisite courses
    print("\n  AWS Academy courses")
    academy_gid = group_ids.get("AWS Academy Courses")
    if not academy_gid:
        print("    ! 'AWS Academy Courses' group missing — assignments would land "
              "in the default group and the 11% weight would not apply")
    for a in cfg.get("academy", []):
        payload = {
            "assignment": {
                "name":                a["title"],
                "description":         academy_html(a),
                "due_at":              due(a["due"]),
                "unlock_at":           unlock(a["assigned"]),
                "points_possible":     a["points"],
                "assignment_group_id": academy_gid,
                "submission_types":    ["online_upload", "online_text_entry"],
                "allowed_attempts":    -1,
                "published":           False,
            }
        }
        aid = api.ensure_assignment(payload, existing_assignments)
        if aid:
            mid = module_ids.get(a["module"])
            if mid:
                api.add_module_item(mid, "Assignment", aid, a["title"])

    # Participation was removed from the grading scheme on 2026-08-05.
    # Its 5% went to Labs/Final Project/AWS Academy Courses. The block that
    # created a "Participation — Full Semester" assignment is gone with it.

    # Reading quizzes
    print("\n  Reading quizzes")
    existing_quizzes = api.get_quizzes()
    quiz_gid = group_ids.get("Reading Quizzes")
    for q in cfg["quizzes"]:
        payload = {
            "quiz": {
                "title":                q["title"],
                "quiz_type":            "assignment",
                "points_possible":      q["points"],
                "assignment_group_id":  quiz_gid,
                "unlock_at":            open_at(q["open_date"]),
                "due_at":               due(q["due_date"]),
                "lock_at":              due(q["due_date"]),
                "time_limit":           15,
                "allowed_attempts":     1,
                "show_correct_answers": True,
                "published":            False,
                "description":          "<p>Covers assigned readings for this week. Opens Saturday 8 AM. 15 minutes, 1 attempt. Due Monday night.</p>",
            }
        }
        qid = api.ensure_quiz(payload, existing_quizzes)
        if qid:
            mid = module_ids.get(q["module"])
            if mid:
                api.add_module_item(mid, "Quiz", qid, q["title"])

    print("\n  ✓ Stage 1 complete")
    return module_ids
