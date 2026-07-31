"""
Stage 1 — Canvas Course Structure
Creates/updates: assignment groups, modules, lab assignments,
final project, quizzes, participation, and content pages.
All operations are idempotent.
"""

from datetime import datetime, timedelta, timezone
from .canvas_api import CanvasAPI

MDT = timezone(timedelta(hours=-6))

def to_utc(date_str: str, hour: int = 23, minute: int = 59) -> str:
    local = datetime.strptime(date_str, "%Y-%m-%d").replace(
        hour=hour, minute=minute, second=0, tzinfo=MDT)
    return local.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def due(d):       return to_utc(d, 23, 59)
def open_at(d):   return to_utc(d,  8,  0)
def unlock(d):    return to_utc(d,  9,  0)


# ── Page content ─────────────────────────────────────────────────────────────

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
<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;width:100%">
  <tr><th>Component</th><th>Weight</th><th>Notes</th></tr>
  <tr><td>Labs (7 total)</td><td>60%</td><td>~8.57% each, equally weighted</td></tr>
  <tr><td>Final Project</td><td>25%</td><td>Team-based; full system design + presentation</td></tr>
  <tr><td>Reading Quizzes</td><td>10%</td><td>Weekly — opens Saturday, due Monday night</td></tr>
  <tr><td>Participation</td><td>5%</td><td>In-class contribution quality, not attendance</td></tr>
</table>
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
  <tr><td>Churn Prediction</td><td>Batch ML (XGBoost)</td><td>Identify at-risk customers 30 days before churn</td></tr>
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

def lab_html(lab: dict) -> str:
    n   = lab["number"]
    due = lab["due"]
    return f"""
<p><strong>Due:</strong> {due}, 11:59 PM MDT</p>
<p>See the <strong>Lab Guide</strong> page in this module for full task specifications and rubrics.</p>
<h2>Submission</h2>
<p>Submit a GitHub repository link before the deadline.
A repo that does not clone cleanly loses 20 points automatically.
Never commit AWS credentials — committed secrets = automatic 0.</p>
<p><strong>Late policy:</strong> 10% per calendar day. Contact instructor before the deadline, not after.</p>
"""


# ── Main stage function ───────────────────────────────────────────────────────

def run(cfg: dict, api: CanvasAPI):
    print("\n[Stage 1] Canvas Course Structure")

    # Course dates
    print("\n  Course dates")
    api.set_course_dates(
        to_utc(cfg["course"]["start_date"], 0, 0),
        to_utc(cfg["course"]["end_date"], 23, 59),
    )
    print("    ✓ Start/end dates set")

    # Assignment groups
    print("\n  Assignment groups")
    existing_groups = api.get_assignment_groups()
    # Remove default "Assignments" group if present
    if "Assignments" in existing_groups:
        api.delete_assignment_group(existing_groups["Assignments"])
        print("    ✓ Removed default Assignments group")

    group_ids = {}
    for i, grp in enumerate(cfg["grading"]["groups"], 1):
        gid = api.ensure_assignment_group(
            grp["name"], grp["weight"], i, existing_groups)
        if gid:
            group_ids[grp["name"]] = gid
    api.set_weighted_grading(cfg["grading"]["weighted"])

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

    # Participation
    print("\n  Participation")
    part_gid = group_ids.get("Participation")
    payload = {
        "assignment": {
            "name":                "Participation — Full Semester",
            "description":         "<p>In-class contribution quality, assigned by instructor at end of term.</p>",
            "points_possible":     100,
            "assignment_group_id": part_gid,
            "submission_types":    ["none"],
            "published":           False,
        }
    }
    api.ensure_assignment(payload, existing_assignments)

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
