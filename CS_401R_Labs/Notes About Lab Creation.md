**Prompt:** Syllabus looks good. Now let's design the Labs. Create a separate document under the CS_401R_2026 directory that describes each Lab. The emphasis should be on hands-on development of a complete, production-ready system based on the Retail use case. You can draw from the "Apply It" sections at the end of each chapter. Ask me questions.

**Structure:** One evolving `northstar-ai-platform/` GitHub repository with 7 folders added across the semester — infrastructure → data → models → pipeline → deployment → monitoring → docs. Each lab has a clearly numbered folder and a corresponding written deliverable in `docs/`.

**Starter kit strategy — scaffolding fades:**

- Lab 1: Terraform module structure template + AWS setup guide
- Lab 2: Full synthetic dataset (4 sources, ~12M rows combined), Glue skeleton
- Lab 3: Evaluation harness (RAGAS), training script skeleton, prompt templates
- Lab 4: CodePipeline/buildspec starters, test template
- Labs 5–7: Nothing — students are on their own

**Track B/C design in Lab 3** — all students build the churn model (traditional ML), then choose offer generation (RAG) or the customer service agent. This ensures everyone works with classical ML _and_ gets hands-on with either foundation models or agentic systems.

**TA grading rubrics** — every task has a table with specific pass/fail criteria. No subjective "good job" items. Examples: `terraform apply` completes clean, `pytest tests/` passes, `git log` shows no committed secrets, `get_record()` returns correct values.

**Lab 7 is intentionally leaner** — 12-day window, scoped to metrics + economics + the value scorecard. The heavy governance work moves to the team project, which has until Dec 17.

## Starter Kits

All four lab starter kits are complete. Here's what was built:

### Lab 2 — Data & Feature Engineering

- **`generate_northstar_data.py`** — Full synthetic data generator. Produces all 5 datasets with realistic statistical properties: 15% churn rate, tier-correlated spend/frequency, seasonal transaction boost in Nov-Dec, ~2% date format inconsistencies in store events, ~35% anonymous clickstream, PII injection in 0.5% of search queries. Supports `--small` flag (1% scale) for fast local testing.
- **`glue_job_skeleton.py`** — Glue PySpark ETL with 6 clearly labeled steps: read, schema validation with quarantine, cleaning (store_id normalization, date parsing), quality gates that fail loudly, write to processed zone, CloudWatch metrics (TODO). Students complete the null checks and partitioning.

### Lab 3 — Model Development

- **`churn_training_skeleton.py`** — Full SageMaker training entry point. Feature Store Athena query pattern with `local-data-path` bypass for dev, XGBoost with class imbalance handling (`scale_pos_weight=5.5`), evaluation thresholds (AUC ≥ 0.72, precision@top10 ≥ 0.40, recall@top10 ≥ 0.35), slice evaluation stub, Model Registry registration (PendingManualApproval, never auto-approved).
- **`evaluation_harness.py`** — Dual-track harness. Track B: RAGAS evaluation (faithfulness ≥ 0.80, answer_relevancy ≥ 0.75, context_recall ≥ 0.70) with 3 test cases including the Platinum/low-LTV edge case. Track C: 5 agent scenarios (2 happy path, 2 boundary, 1 adversarial prompt injection) with tool-call and escalation verification via Bedrock trace inspection.
- **`prompt_templates/offer_generation_prompts.md`** — 5 templates with intentional documented weaknesses for students to fix: tier-blind system prompt, missing Platinum/promo-sensitivity rule, retrieval query variants (A/B/C) to compare, guardrail block, and a pass/fail evaluation checklist.

### Lab 4 — CI/CD Pipeline

- **`buildspec.yml`** — Full CodeBuild spec: install → test (data/feature/model) → package → SageMaker pipeline trigger → poll with timeout (45 min) → model quality gate via metrics JSON → CloudWatch publish (TODO) → Slack notification.
- **`pipeline.yaml`** — CloudFormation for the full CodePipeline stack: GitHub connection (CodeStar), CodeBuild project, 4-stage pipeline (Source → Build → Manual Approval → Deploy stub). IAM roles scoped to least privilege. The manual approval stage blocks model promotion until a human reviews metrics — intentional.
- **`tests/test_data.py`** — 22 tests across all 5 datasets: schema, uniqueness, referential integrity, churn rate bounds, date range, guest checkout rate, PII masking (enforced stub). Two `TODO` stubs for students to implement.
- **`tests/test_features.py`** — Unit tests against isolated feature functions: recency correctness, frequency monotonicity (180d ≥ 90d), monetary aggregation, category diversity bounds, engagement zero-handling. Tests use small fixture DataFrames, not the full 250K dataset — runs in seconds.
- **`tests/test_model.py`** — Model contract tests: loading, feature count, probability range, NaN handling, churner-vs-retainer discrimination, AUC on synthetic data, monotonicity on recency feature, determinism, stored metrics quality gate (reads from `eval_metrics.json` in CI).

Every `TODO` in these files is intentional student work — not something I left unfinished. Let me be precise about what each one is and why it's there.

**Three distinct categories:**

**1. Core lab deliverables** — The main thing the student is supposed to build. The skeleton provides structure and context; the TODO is the assignment.

Example from `glue_job_skeleton.py`:

```python
# TODO: Add a null check for customer_id and transaction_id
valid_df = raw_df  # Replace this with your null-check filter
```

python

This is Lab 2's primary task. If I wrote the null check, the lab is pointless.

**2. Progressive complexity** — Things introduced in a later lab are explicitly flagged so students understand why they're not there yet.

Example from `storage/main.tf` (Lab 1):

```hcl
# TODO: Switch to SSE-KMS in Lab 5 (security hardening)
```


Lab 1 uses SSE-S3 to keep cost and complexity down. Lab 5 is where encryption gets hardened. The TODO is a deliberate breadcrumb, not a gap.

**3. Extension tasks** — Correct but incomplete implementations that students must finish to earn full rubric points.

Example from `test_data.py`:

```python
def test_email_is_hashed(self, customers_df):
    has_at = customers_df["email"].str.contains("@", na=False).sum()
    # TODO: assert has_at == 0
    pass  # Remove this line when you implement the assertion
```

The test structure is given. The student adds the assertion. The rubric awards points for implementing it correctly.

---
## Ways I Can Help Build the Canvas Course:

### 1. ✅ Canvas API Scripts (Recommended)

Write Python scripts using the Canvas LMS REST API that build the entire course from scratch:

- Create all 15 modules + module items
- Create all 7 lab assignments with rubrics, point values, submission types, and due dates
- Create the final project assignment
- Create 28 reading quiz shells (pre-configured: open 48h before class, auto-close)
- Create all content pages (syllabus, lab guides, NorthStar case)
- Wire up the grade book weights

**Result:** You run `python build_canvas_course.py` and the course is built in minutes. Idempotent — safe to re-run.

### 2. ✅ Common Cartridge Package

Generate a `.imscc` file you import directly in Canvas → Settings → Import Course Content. No API token needed, but less control over grading config.

## What I Need From You to Proceed with Option 1

|Item|Where to Find It|
|---|---|
|**Canvas instance URL**|Likely `byu.instructure.com`|
|**API token**|Canvas → Account (avatar) → Settings → Approved Integrations → New Access Token|
|**Course ID**|Already have a shell? URL will show `/courses/XXXXXX`. Or I generate a new shell.|

**What you've forgotten:**

1. **Lab 2 synthetic data** — `generate_northstar_data.py` exists but was never run. Students can't do Lab 2 without the actual CSV/parquet files.
2. **Canvas grading rubrics** — We put rubric text inside assignment descriptions. Canvas has actual rubric objects that TAs click to grade; those don't exist yet.
3. **Idempotency** — The current scripts create duplicates if run twice. Updates require a reset-and-rebuild. Fixable in the pipeline.
4. **Course dates** — Canvas start/end dates aren't set, so the course calendar is off.
5. **AI-generated quiz questions** — The 60 questions are hardcoded. When you update chapters, questions should regenerate from the new content.
6. **Announcements** — Welcome message, lab release reminders, nothing scheduled.
7. **Student groups** — Canvas Groups for team project management.
8. **TA enrollment** — No mechanism to add course staff.
9. **GitHub Classroom** — Lab submission workflow isn't integrated.

## What was built

```
CS_401R_2026/
├── build_course.py           ← Run this
├── course_config.yaml        ← Single source of truth (edit here, re-run to push)
├── PIPELINE.md               ← Full operator documentation
├── requirements.txt          ← requests + pyyaml
└── pipeline/
    ├── __init__.py
    ├── canvas_api.py         ← Idempotent Canvas API wrapper (ensure_* pattern)
    ├── stage1_structure.py   ← Groups, modules, pages, assignments, quizzes
    ├── stage2_readings.py    ← Chapter Markdown → PDF → Canvas upload
    ├── stage3_starters.py    ← Zip starter kits → Canvas upload
    └── stage4_quizzes.py     ← 60 questions (5×12 quizzes), keyed by title
```

---

## How to run

```bash
pip install requests pyyaml
export CANVAS_API_TOKEN="7407~..."

python build_course.py              # all 4 stages
python build_course.py --stage 2    # just chapter PDFs
python build_course.py --stage 2 --rebuild   # force re-build PDFs
python build_course.py --stage 4 --no-replace  # add questions without clearing
```

bash

---

## Key design decisions

**Idempotent by default.** Every stage uses GET-before-POST. Running the full pipeline against a course that's already built updates items, not duplicates them.

**Config-driven, not code-driven.** To point at a different book: change `source.directory` in `course_config.yaml`. Zero Python changes needed.

**Quiz questions keyed by title, not hardcoded ID.** The old `upload_quiz_questions.py` had quiz IDs hardcoded from a specific run. Stage 4 looks up IDs by title at runtime — it works against any course shell.

**Module ID sharing.** When running all stages together, Stage 1 returns the module ID map and passes it to Stages 2 and 3, saving ~3 API round-trips.

---

## What I flagged as intentionally manual

|Item|Reason|
|---|---|
|**Publishing items**|Everything is created as a draft — you control when students see it|
|**Lab Guide pages**|Rubrics and detailed instructions are editorial, not pipeline content|
|**Final Project instructions**|Same|
|**Rubrics**|Canvas Rubric API is gnarly; build in the UI|
|**Zoom links**|Session-specific; add to modules weekly|

## AI-Generated Quiz Questions

**`pipeline/generate_questions.py`** — a new module that:

- Maps each quiz to its source chapters via the shared module name in `course_config.yaml`
- Reads the chapter Markdown content (up to 64K chars)
- Calls Claude to generate exactly 5 questions per quiz (3–4 MC, 1–2 T/F) with a prompt calibrated for graduate-level engineering judgment
- Returns structured dicts in the same format as `QUESTION_BANK`

**Integration with Stage 4:**

```bash
# Preview without uploading
python build_course.py --preview-questions

# Generate and upload
export ANTHROPIC_API_KEY="sk-ant-..."
python build_course.py --stage 4 --generate-questions
```

bash

**Fallback:** If generation fails for any quiz (API error, malformed JSON, missing chapter), that quiz automatically falls back to the hardcoded `QUESTION_BANK`. It never blocks the upload.

**The key value:** When you update a chapter, running `--generate-questions` produces questions that reflect the new content — no manual editing of the question bank.

---

## Item 9 — GitHub Classroom Integration

**`pipeline/stage5_github.py`** — a new stage that:

- Creates a private template repository per lab in your GitHub org (e.g., `cs401r-lab1-template`)
- Pushes the starter kit files from `Starter Kits/Lab N/` into the template repo via git
- Creates a GitHub Classroom assignment linked to that template, with the lab deadline set
- Prints the student invite link for each assignment

```bash
export GITHUB_TOKEN="ghp_..."
export GITHUB_ORG="byu-cs401r-f26"
export GITHUB_CLASSROOM_ID="12345"
python build_course.py --stage 5
```

bash

Students click the invite link → GitHub Classroom creates a private fork of the template repo in their account, pre-loaded with the starter kit. Labs 5–7 (no starter kit) get an empty shell repo students can still submit to.