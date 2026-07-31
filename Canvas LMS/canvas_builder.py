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
# Lab Assignment HTML Descriptions
# ─────────────────────────────────────────────────────────────────────────────

LAB_HTML = {}

LAB_HTML[1] = """
<p><strong>Assigned:</strong> Thu Sep 3 &nbsp;|&nbsp; <strong>Due:</strong> Sat Sep 19, 11:59 PM MDT<br>
<strong>Chapter:</strong> <em>AI Platform &amp; Cloud Architecture</em></p>

<h2>Objective</h2>
<p>Stand up the NorthStar Retail AI platform skeleton on AWS using Infrastructure as Code.
Every AWS resource you create here will be used by all subsequent labs.
Deliverable: a reproducible environment a teammate could recreate from scratch with a single
<code>terraform apply</code>.</p>

<h2>Starter Kit</h2>
<ul>
  <li><code>northstar-overview.md</code> — NorthStar Retail case description</li>
  <li><code>terraform-module-template/</code> — empty Terraform module directory structure</li>
  <li><code>aws-educate-setup.md</code> — AWS Educate account setup and budget guardrails</li>
  <li><code>northstar-data-schema.md</code> — data source schemas</li>
</ul>

<h2>Tasks &amp; Point Breakdown</h2>
<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;width:100%">
  <tr><th>Task</th><th style="text-align:center">Points</th></tr>
  <tr><td>Task 1 — AWS Environment Setup (SageMaker Domain, S3, IAM roles, VPC)</td><td style="text-align:center">20</td></tr>
  <tr><td>Task 2 — Terraform Module Structure (remote state, parameterized, clean apply)</td><td style="text-align:center">30</td></tr>
  <tr><td>Task 3 — Architecture Decision Record (600–900 words)</td><td style="text-align:center">25</td></tr>
  <tr><td>Task 4 — Monthly Cost Estimate (4 components, assumptions, 1 optimization)</td><td style="text-align:center">15</td></tr>
  <tr><td>Task 5 — Repository Quality (README, .gitignore, structure)</td><td style="text-align:center">10</td></tr>
  <tr><td><strong>Total</strong></td><td style="text-align:center"><strong>100</strong></td></tr>
</table>
<p>Full rubrics are in the Lab Guide page in this module.</p>

<h2>Submission</h2>
<p>Submit a link to your GitHub repository. TA will clone and run <code>terraform apply</code>.
A repo that does not clone cleanly loses 20 points automatically.
<strong>Never commit AWS credentials — committed secrets = automatic 0.</strong></p>
"""

LAB_HTML[2] = """
<p><strong>Assigned:</strong> Thu Sep 17 &nbsp;|&nbsp; <strong>Due:</strong> Sat Oct 3, 11:59 PM MDT<br>
<strong>Chapter:</strong> <em>Data &amp; Feature Engineering</em><br>
<strong>Builds on:</strong> Lab 1 — uses your S3 structure, IAM roles, and VPC</p>

<h2>Objective</h2>
<p>Build NorthStar's data ingestion and feature engineering pipeline. Raw customer and transaction
data flows in, gets cleaned and transformed, and lands in a SageMaker Feature Store that Lab 3
will read from. A broken feature pipeline is the most common reason AI projects fail in production.</p>

<h2>Starter Kit</h2>
<ul>
  <li><code>northstar-data/</code> — full synthetic dataset: customers.csv (250k rows),
      transactions.parquet (4.2M rows), clickstream.parquet (8.1M rows), store_events.csv, product_catalog.json</li>
  <li><code>glue-job-skeleton.py</code> — AWS Glue PySpark skeleton</li>
  <li><code>feature-store-schema.md</code> — required feature group schema for Task 3</li>
</ul>

<h2>Tasks &amp; Point Breakdown</h2>
<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;width:100%">
  <tr><th>Task</th><th style="text-align:center">Points</th></tr>
  <tr><td>Task 1 — Data Ingestion Pipeline (2+ patterns: batch, streaming, event-driven)</td><td style="text-align:center">25</td></tr>
  <tr><td>Task 2 — Feature Engineering (5+ features with temporal leakage audit)</td><td style="text-align:center">25</td></tr>
  <tr><td>Task 3 — SageMaker Feature Store (northstar-churn-features group, online + offline)</td><td style="text-align:center">20</td></tr>
  <tr><td>Task 4 — Data Contract (POS transaction feed, SLAs, breaking change protocol)</td><td style="text-align:center">20</td></tr>
  <tr><td>Task 5 — Data Lineage Diagram (raw → ingestion → transform → features → store → training)</td><td style="text-align:center">10</td></tr>
  <tr><td><strong>Total</strong></td><td style="text-align:center"><strong>100</strong></td></tr>
</table>
<p>Full rubrics are in the Lab Guide page in this module.</p>

<h2>Submission</h2>
<p>Submit your GitHub repository link. Must include both working pipeline code and
<code>docs/lab2-data-contract.md</code>.</p>
"""

LAB_HTML[3] = """
<p><strong>Assigned:</strong> Thu Oct 1 &nbsp;|&nbsp; <strong>Due:</strong> Sat Oct 17, 11:59 PM MDT<br>
<strong>Chapters:</strong> <em>Model Development</em> (Fine-Tuning, RAG, Agents)<br>
<strong>Builds on:</strong> Labs 1–2 — models train on Feature Store features from Lab 2</p>

<h2>Objective</h2>
<p>Implement two of NorthStar's three AI systems: the churn prediction model (required) plus one
LLM-based system of your choice. This is where the platform starts doing something that matters
to the business.</p>

<h2>Track Selection</h2>
<p>All students complete <strong>Track A</strong>. Choose <strong>Track B or Track C</strong>
and declare your choice in <code>docs/lab3-model-design.md</code> before coding.</p>
<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;width:100%">
  <tr><th>Track</th><th>System</th><th>Approach</th></tr>
  <tr><td><strong>A (required)</strong></td><td>Churn Prediction</td><td>XGBoost on Feature Store features</td></tr>
  <tr><td><strong>B</strong></td><td>Offer Generation</td><td>RAG via Bedrock + product catalog / policy docs</td></tr>
  <tr><td><strong>C</strong></td><td>Customer Service Agent</td><td>ReAct agent via Bedrock Agents</td></tr>
</table>

<h2>Starter Kit</h2>
<ul>
  <li><code>evaluation-harness/</code> — Python RAGAS evaluation template</li>
  <li><code>churn-training-skeleton.py</code> — SageMaker XGBoost training script skeleton</li>
  <li><code>prompt-templates/</code> — example prompts for offer generation</li>
  <li><code>northstar-policy-docs/</code> — policy documents for RAG corpus</li>
</ul>

<h2>Tasks &amp; Point Breakdown</h2>
<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;width:100%">
  <tr><th>Task</th><th style="text-align:center">Points</th></tr>
  <tr><td>Task 1 — Churn Prediction Model: Track A (AUC-ROC ≥ 0.72, slice eval, Model Registry)</td><td style="text-align:center">35</td></tr>
  <tr><td>Task 2 — LLM System: Track B (RAGAS eval) or Track C (5 test scenarios with traces)</td><td style="text-align:center">35</td></tr>
  <tr><td>Task 3 — Approach Justification (~500 words: why XGBoost, why RAG/agent, what you'd change)</td><td style="text-align:center">20</td></tr>
  <tr><td>Task 4 — Repository Quality (parameterized, Lab 1 infra reused, README updated)</td><td style="text-align:center">10</td></tr>
  <tr><td><strong>Total</strong></td><td style="text-align:center"><strong>100</strong></td></tr>
</table>
<p>Full rubrics are in the Lab Guide page in this module.</p>

<h2>Submission</h2>
<p>Submit your GitHub repository link. Include a working demo notebook for your LLM system.</p>
"""

LAB_HTML[4] = """
<p><strong>Assigned:</strong> Thu Oct 15 &nbsp;|&nbsp; <strong>Due:</strong> Sat Oct 31, 11:59 PM MDT<br>
<strong>Chapters:</strong> <em>XOps Stack</em>, <em>Testing &amp; Evaluation</em>, <em>Continuous Delivery</em><br>
<strong>Builds on:</strong> Labs 1–3 — automates the lifecycle of your Lab 3 churn model</p>

<h2>Objective</h2>
<p>Automate everything. A model that requires manual steps to test, evaluate, and deploy is not
a production system — it is a science project. Build the pipeline that takes a code commit all
the way to a model approved for deployment, without human intervention in the happy path.</p>

<h2>Starter Kit</h2>
<ul>
  <li><code>buildspec.yml</code> — CodeBuild build specification skeleton</li>
  <li><code>pipeline.yaml</code> — CodePipeline definition starter</li>
  <li><code>tests/template/</code> — pytest test structure template</li>
</ul>

<h2>Tasks &amp; Point Breakdown</h2>
<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;width:100%">
  <tr><th>Task</th><th style="text-align:center">Points</th></tr>
  <tr><td>Task 1 — Test Suite (data, feature unit, model eval, fairness — runs via <code>pytest tests/</code>)</td><td style="text-align:center">30</td></tr>
  <tr><td>Task 2 — CI/CD Pipeline (5 stages: source → test → build → evaluate → register)</td><td style="text-align:center">30</td></tr>
  <tr><td>Task 3 — MLOps Configuration (champion-challenger, retraining triggers, lineage)</td><td style="text-align:center">20</td></tr>
  <tr><td>Task 4 — XOps Maturity Assessment (~400 words: DataOps + MLOps levels with evidence)</td><td style="text-align:center">20</td></tr>
  <tr><td><strong>Total</strong></td><td style="text-align:center"><strong>100</strong></td></tr>
</table>
<p>Full rubrics are in the Lab Guide page in this module.</p>

<h2>Submission</h2>
<p>Submit your GitHub repository link. TA will introduce a deliberate test failure and verify
the pipeline halts at the Test stage.</p>
"""

LAB_HTML[5] = """
<p><strong>Assigned:</strong> Thu Oct 29 &nbsp;|&nbsp; <strong>Due:</strong> Sat Nov 14, 11:59 PM MDT<br>
<strong>Chapters:</strong> <em>Deployment &amp; Scaling</em>, <em>Security, Privacy &amp; Compliance</em><br>
<strong>Builds on:</strong> Labs 1–4 — deploys the Lab 3 churn model to production</p>

<h2>Objective</h2>
<p>Ship the NorthStar churn model to production using a controlled deployment strategy, and document
the security and privacy posture required for enterprise customer data models. After this lab,
the churn model is live. No starter kit — you are building without templates.</p>

<h2>Tasks &amp; Point Breakdown</h2>
<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;width:100%">
  <tr><th>Task</th><th style="text-align:center">Points</th></tr>
  <tr><td>Task 1 — Production Deployment (canary or blue/green, auto-scaling, numeric rollback trigger)</td><td style="text-align:center">30</td></tr>
  <tr><td>Task 2 — Operational Deployment Plan (600–900 words, executable by a stranger)</td><td style="text-align:center">20</td></tr>
  <tr><td>Task 3 — Security Assessment (STRIDE threat model ≥5 threats + data classification)</td><td style="text-align:center">25</td></tr>
  <tr><td>Task 4 — Privacy &amp; Compliance Assessment (GDPR lawful basis, deletion workflow)</td><td style="text-align:center">15</td></tr>
  <tr><td>Task 5 — Repository Quality (no credentials, deployment as code, CI extended)</td><td style="text-align:center">10</td></tr>
  <tr><td><strong>Total</strong></td><td style="text-align:center"><strong>100</strong></td></tr>
</table>
<p>Full rubrics are in the Lab Guide page in this module.</p>

<h2>Submission</h2>
<p>Submit your GitHub repository link. Deployment config must be code, not console clicks.
<code>git log --all -S "AKIA"</code> returning any results = automatic 0.</p>
"""

LAB_HTML[6] = """
<p><strong>Assigned:</strong> Thu Nov 12 &nbsp;|&nbsp; <strong>Due:</strong> Sat Nov 28, 11:59 PM MDT<br>
<strong>Chapters:</strong> <em>Metrics, Benchmarks &amp; Guardrails</em>, <em>Monitoring &amp; Observability</em>, <em>Reliability Engineering</em><br>
<strong>Builds on:</strong> Labs 1–5 — instruments the production system deployed in Lab 5</p>

<h2>Objective</h2>
<p>A deployed model with no monitoring is a liability. Instrument the NorthStar platform end-to-end:
five monitoring layers, full alert architecture, SLOs with error budgets, and operational runbooks.
After this lab, your platform can fail gracefully and recover fast. No starter kit.</p>

<h2>Tasks &amp; Point Breakdown</h2>
<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;width:100%">
  <tr><th>Task</th><th style="text-align:center">Points</th></tr>
  <tr><td>Task 1 — Five-Layer Monitoring (infrastructure, pipeline, model, application, business) in CloudWatch Dashboard</td><td style="text-align:center">35</td></tr>
  <tr><td>Task 2 — Drift Detection Plan (drift types, statistical tests per feature, concept drift proxy)</td><td style="text-align:center">15</td></tr>
  <tr><td>Task 3 — Alert Architecture (≥6 alerts, P0–P3 tiers, ≥1 suppression rule)</td><td style="text-align:center">15</td></tr>
  <tr><td>Task 4 — SLO Design (4 SLOs: availability, latency, quality, fairness — with error budgets)</td><td style="text-align:center">15</td></tr>
  <tr><td>Task 5 — Runbooks (2 failure scenarios, full structure including graceful degradation)</td><td style="text-align:center">20</td></tr>
  <tr><td><strong>Total</strong></td><td style="text-align:center"><strong>100</strong></td></tr>
</table>
<p>Full rubrics are in the Lab Guide page in this module.</p>

<h2>Submission</h2>
<p>Submit your GitHub repository link. CloudWatch Dashboard JSON must be committed to
<code>monitoring/dashboards/northstar-dashboard.json</code>.</p>
"""

LAB_HTML[7] = """
<p><strong>Assigned:</strong> Thu Nov 19 &nbsp;|&nbsp;
<strong>Due: Tue Dec 1, 11:59 PM MDT</strong> ⚠️ Tuesday exception — see syllabus<br>
<strong>Chapters:</strong> <em>Metrics, Benchmarks &amp; Guardrails</em>, <em>AI Economics</em>, <em>Measuring Business Value</em><br>
<strong>Builds on:</strong> Labs 1–6 — measures the value and cost of the full platform</p>

<h2>Objective</h2>
<p>The NorthStar platform is live. Now answer the question every CFO and CDO will ask:
<em>Is it worth it?</em> Build the measurement infrastructure to answer rigorously — metric pyramid,
unit economics, and an executive scorecard tracing model outputs to business outcomes.
No starter kit.</p>

<h2>Tasks &amp; Point Breakdown</h2>
<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;width:100%">
  <tr><th>Task</th><th style="text-align:center">Points</th></tr>
  <tr><td>Task 1 — Metric Pyramid (2 systems × 4 layers × ≥2 metrics each, causal link analysis)</td><td style="text-align:center">25</td></tr>
  <tr><td>Task 2 — Unit Economics (cost/prediction, total platform cost, one quantified optimization)</td><td style="text-align:center">25</td></tr>
  <tr><td>Task 3 — Executive Value Scorecard (CFO/CDO audience, attribution method, recommendations)</td><td style="text-align:center">25</td></tr>
  <tr><td>Task 4 — Value Methodology Note (all 12 fields, specific counterfactual)</td><td style="text-align:center">15</td></tr>
  <tr><td>Task 5 — Measurement Reflection (~300 words: weak assumptions + experiments + least-observed layer)</td><td style="text-align:center">10</td></tr>
  <tr><td><strong>Total</strong></td><td style="text-align:center"><strong>100</strong></td></tr>
</table>
<p>Full rubrics are in the Lab Guide page in this module.</p>

<h2>Submission</h2>
<p>Submit your GitHub repository link by <strong>Tuesday Dec 1 at midnight</strong>.
This is an exception to the normal Saturday due date. Final project work begins after this deadline.</p>
"""


# ─────────────────────────────────────────────────────────────────────────────
# Lab Assignment Definitions
# ─────────────────────────────────────────────────────────────────────────────

LABS = [
    {
        "name":      "Lab 1 — Platform Foundation",
        "due_at":    due("2026-09-19"),
        "unlock_at": mdt("2026-09-03", 9, 0),
        "html":      LAB_HTML[1],
        "module":    "Week 01 — Introduction (Sep 3)",
    },
    {
        "name":      "Lab 2 — Data & Feature Engineering",
        "due_at":    due("2026-10-03"),
        "unlock_at": mdt("2026-09-17", 9, 0),
        "html":      LAB_HTML[2],
        "module":    "Week 03 — Platform II + Data Engineering I (Sep 15–17)",
    },
    {
        "name":      "Lab 3 — Model Development",
        "due_at":    due("2026-10-17"),
        "unlock_at": mdt("2026-10-01", 9, 0),
        "html":      LAB_HTML[3],
        "module":    "Week 05 — Model Dev II & III: RAG + Agents (Sep 29–Oct 1)",
    },
    {
        "name":      "Lab 4 — XOps, Testing & CI/CD Pipeline",
        "due_at":    due("2026-10-31"),
        "unlock_at": mdt("2026-10-15", 9, 0),
        "html":      LAB_HTML[4],
        "module":    "Week 07 — Testing & Evaluation (Oct 13–15)",
    },
    {
        "name":      "Lab 5 — Deployment & Scaling",
        "due_at":    due("2026-11-14"),
        "unlock_at": mdt("2026-10-29", 9, 0),
        "html":      LAB_HTML[5],
        "module":    "Week 09 — Deployment & Scaling (Oct 27–29)",
    },
    {
        "name":      "Lab 6 — Monitoring & Reliability",
        "due_at":    due("2026-11-28"),
        "unlock_at": mdt("2026-11-12", 9, 0),
        "html":      LAB_HTML[6],
        "module":    "Week 11 — Metrics + Monitoring (Nov 10–12)",
    },
    {
        "name":      "Lab 7 — Metrics, Economics & Business Value",
        "due_at":    due("2026-12-01"),
        "unlock_at": mdt("2026-11-19", 9, 0),
        "html":      LAB_HTML[7],
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
      <td>Identify at-risk customers 30 days before churn; trigger retention offers</td></tr>
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
                "description":          lab["html"],
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

def main():
    print(f"CS 401R Canvas Builder")
    print(f"Target: {BASE_URL}/courses/{COURSE_ID}\n")

    group_ids  = build_assignment_groups()
    module_ids = build_modules()

    build_labs(module_ids, group_ids)
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
    main()
