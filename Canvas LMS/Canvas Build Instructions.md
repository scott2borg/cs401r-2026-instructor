---
created: 2026-06-26
tags: [course, canvas, CS401R, setup]
title: "Canvas Build Instructions — CS 401R"
---

# Canvas Build Instructions — CS 401R

One-time setup to populate the Canvas course shell from the syllabus and lab guide.

---

## Prerequisites

- Python 3.9+
- A Canvas API token (instructions below)
- Your course shell ID

---

## Step 1 — Get Your Course ID

Open your course shell in Canvas. The URL will look like:
```
https://byu.instructure.com/courses/123456
```
The number at the end is your course ID.

---

## Step 2 — Create a Canvas API Token

1. Log into Canvas at `byu.instructure.com`
2. Click your avatar (top-left) → **Account** → **Settings**
3. Scroll down to **Approved Integrations**
4. Click **New Access Token**
5. Purpose: `CS 401R Course Builder`
6. Expiration: leave blank or set 30 days out
7. Copy the token — **it is shown only once**

Keep this token private. Do not paste it in chat, commit it to git, or share it.

---

## Step 3 — Install Dependencies

From Terminal, in the `CS_401R_2026` project folder (or anywhere):

```bash
pip install requests
```

---

## Step 4 — Run the Script

```bash
export CANVAS_API_TOKEN="your_token_here"
export CANVAS_COURSE_ID="123456"
python canvas_builder.py
```

The script will print progress as it creates each item. Typical runtime: 2–3 minutes.

**Output when complete:**
```
✓ Labs group (id=...)
✓ Final Project group (id=...)
✓ Reading Quizzes group (id=...)
✓ Participation group (id=...)
✓ Week 01 — Introduction (id=...)
... (16 modules)
✓ Lab 1 — Platform Foundation (id=...)
... (7 labs)
✓ Final Project — NorthStar AI Platform Design (id=...)
✓ Reading Quizzes (12 quizzes)
✓ Course Syllabus page
✓ NorthStar Retail — Case Overview page
✓ AWS Educate Setup Guide page

✓ Done. All items created as DRAFTS.
```

---

## Step 5 — What the Script Creates

| Item | Count | Details |
|------|-------|---------|
| Modules | 16 | Start Here + 15 weekly modules |
| Assignment groups | 4 | Labs 60%, Project 25%, Quizzes 10%, Participation 5% |
| Lab assignments | 7 | 100 pts each, GitHub URL submission, correct due dates |
| Final project | 2 | Team sign-up (Nov 25) + submission (Dec 17) |
| Participation | 1 | 100 pts, manual grading |
| Reading quizzes | 12 | Weeks 2–13, 10 pts each, 15 min, 1 attempt |
| Pages | 3 | Syllabus, NorthStar Overview, AWS Setup Guide |
| Syllabus tab | 1 | Canvas built-in Syllabus tab populated |

All items are created as **drafts** (unpublished). You control when students can see them.

---

## Step 6 — What You Still Need to Do Manually

These cannot be automated without additional setup:

1. **Quiz questions** — 12 quiz shells exist with no questions. Add 5–10 questions per quiz in Canvas → Quizzes.
2. **Starter kit files** — Upload to Canvas Files:
   - Lab 1: `northstar-overview.md`, Terraform templates, `aws-educate-setup.md`, `northstar-data-schema.md`
   - Lab 2: `northstar-data/` folder (synthetic datasets), `glue-job-skeleton.py`, `feature-store-schema.md`
   - Lab 3: `evaluation-harness/`, `churn-training-skeleton.py`, `prompt-templates/`, `northstar-policy-docs/`
   - Lab 4: `buildspec.yml`, `pipeline.yaml`, `tests/template/`
3. **Chapter PDFs** — Upload to Canvas Files → Readings (one per chapter, named by week)
4. **Office hours** — Add to the Start Here module as a page or announcement
5. **Presentation schedule** — Post by Dec 1 in the Finals week area
6. **Publish** — When ready, publish modules in order via Canvas → Modules → Publish All

---

## If Something Goes Wrong

**Script creates duplicates:** The script is not idempotent. If you ran it twice, go to Course Settings → Reset Course Content → Reset, then re-run from scratch.

**API errors (401):** Your token expired or was entered incorrectly. Create a new one (Step 2).

**API errors (404):** Course ID is wrong. Double-check the URL.

**Module items missing:** The module name in the script must exactly match the created module name. If you edited `MODULE_NAMES` in the script, the `add_to_module()` calls will fail silently. Re-run after fixing.

---

## Deleting Your API Token When Done

After the script runs successfully, delete the token:
Canvas → Account → Settings → Approved Integrations → Delete the `CS 401R Course Builder` token.
