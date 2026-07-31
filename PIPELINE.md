# CS 401R Canvas Course Pipeline

Everything needed to build or update the CS 401R course on Canvas from scratch in four stages.

---

## Quick Start

```bash
cd /path/to/CS_401R_2026

# Install dependency
pip install requests pyyaml

# Set your Canvas API token (never hardcode this)
export CANVAS_API_TOKEN="7407~..."

# Run the full pipeline
python build_course.py
```

Done. All four stages run in order. The pipeline is **idempotent** — running it again updates existing items rather than creating duplicates.

---

## Prerequisites

| Tool | Install | Required by |
|------|---------|-------------|
| Python 3.11+ | System | All stages |
| `requests`, `pyyaml` | `pip install requests pyyaml` | All stages |
| pandoc | `brew install pandoc` | Stage 2 |
| xelatex (MacTeX) | `brew install --cask mactex-no-gui` | Stage 2 |
| Ghostscript | `brew install ghostscript` | Stage 2 (optional, compression) |
| zip | Built-in macOS | Stage 3 |
| `anthropic` | `pip install anthropic` | Stage 4 `--generate-questions` |
| git | Built-in macOS | Stage 5 |

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `CANVAS_API_TOKEN` | **Yes** (stages 1–4) | Canvas user API token — see below |
| `CANVAS_COURSE_ID` | No | Override the course ID from `course_config.yaml` |
| `ANTHROPIC_API_KEY` | Yes (`--generate-questions`) | Anthropic API key for AI quiz generation |
| `GITHUB_TOKEN` | Yes (stage 5) | GitHub PAT with `repo` + classroom scopes |
| `GITHUB_ORG` | Yes (stage 5) | GitHub org or user that owns the template repos |
| `GITHUB_CLASSROOM_ID` | Yes (stage 5) | Numeric ID from `github.com/classrooms` |

**Getting a Canvas API token:**
1. Canvas → Account → Settings → New Access Token
2. Give it a name, set an expiry
3. Copy the token — Canvas shows it only once
4. After the pipeline runs successfully, delete it: Canvas → Account → Settings → Approved Integrations → Delete

---

## File Structure

```
CS_401R_2026/
├── build_course.py          ← Main orchestrator (run this)
├── course_config.yaml       ← Single source of truth for all course data
├── requirements.txt
├── PIPELINE.md              ← This file
│
├── pipeline/                ← Pipeline stages (imported by build_course.py)
│   ├── __init__.py
│   ├── canvas_api.py        ← Idempotent Canvas REST API wrapper
│   ├── stage1_structure.py  ← Assignment groups, modules, pages, assignments, quizzes
│   ├── stage2_readings.py   ← Chapter PDF build + Canvas upload
│   ├── stage3_starters.py   ← Lab starter kit zip + Canvas upload
│   ├── stage4_quizzes.py    ← Quiz question population (hardcoded or AI-generated)
│   ├── stage5_github.py     ← GitHub Classroom: template repos + assignments
│   └── generate_questions.py ← AI quiz question generation via Claude API
│
├── Starter Kits/            ← Lab starter kit source files
│   ├── Lab 1/               ← Terraform IaC skeleton
│   ├── Lab 2/               ← Data pipeline skeleton
│   ├── Lab 3/               ← Model development skeleton
│   └── Lab 4/               ← CI/CD pipeline skeleton
│
└── (legacy scripts — kept for reference, superseded by pipeline/)
    ├── canvas_builder.py
    ├── chapter_uploader.py
    ├── upload_starter_kits.py
    └── upload_quiz_questions.py
```

---

## Pipeline Stages

### Stage 1 — Course Structure

**What it does:**
- Sets course start/end dates
- Creates assignment groups (Labs 60%, Final Project 25%, Reading Quizzes 10%, Participation 5%)
- Enables weighted grading
- Creates 16 weekly modules
- Creates three content pages (syllabus, NorthStar case overview, AWS setup guide)
- Sets the syllabus page as the course front page
- Creates 7 lab assignments (draft, linked to modules)
- Creates final project team sign-up + submission assignments
- Creates participation assignment
- Creates 12 reading quiz shells (draft, linked to modules)

**Idempotency:** Uses GET-before-POST. Existing items are updated, not duplicated.

```bash
python build_course.py --stage 1
```

---

### Stage 2 — Chapter Readings

**What it does:**
- Reads chapter definitions from `course_config.yaml → chapters`
- Converts each Markdown chapter to PDF using pandoc + xelatex
- Compresses PDFs with Ghostscript `/ebook` profile (~90% size reduction)
- Uploads PDFs to Canvas `Readings` folder (overwrites if present)
- Links each PDF into its target module(s)

**Idempotency:** Canvas `on_duplicate: overwrite` replaces existing files. PDFs already built locally are skipped unless `--rebuild` is passed.

```bash
python build_course.py --stage 2            # skip already-built PDFs
python build_course.py --stage 2 --rebuild  # force re-build all PDFs
```

**Source directory:** Controlled by `course_config.yaml → source.directory`. Change this to point at a different book project without touching any Python code.

**PDF output location:** `{source.directory}/{source.output_dir}/` (e.g., `EAIE/Build/canvas_chapters/`)

---

### Stage 3 — Lab Starter Kits

**What it does:**
- For each lab with a `starter_kit` path in `course_config.yaml`
- Zips the starter kit directory (preserving folder structure)
- Uploads the zip to Canvas `Lab Starter Kits` folder
- Links the zip into the lab's module

**Idempotency:** Canvas `on_duplicate: overwrite` replaces existing zips.

```bash
python build_course.py --stage 3
```

**Starter kit source:** Paths in `course_config.yaml → labs[].starter_kit` are relative to the `CS_401R_2026/` folder.

---

### Stage 4 — Quiz Questions

**What it does:**
- Looks up each quiz shell by title (created in Stage 1)
- Deletes any existing questions
- Uploads 5 fresh questions per quiz (2 pts each = 10 pts total)
- Mix of multiple choice and true/false

**Two question sources — you choose:**

**Option A — Hardcoded (default):** Questions in `pipeline/stage4_quizzes.py → QUESTION_BANK`. Fast, deterministic.
```bash
python build_course.py --stage 4
```

**Option B — AI-generated:** Calls Claude API to read each chapter and generate questions from the actual content. When you update a chapter, re-running regenerates questions that reflect the new material.
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
python build_course.py --stage 4 --generate-questions
```

**Preview before uploading:**
```bash
python build_course.py --preview-questions    # generate + print, no upload
```

**Fallback behavior:** If AI generation fails for a quiz (API error, missing chapter file, etc.) that quiz falls back to the hardcoded QUESTION_BANK automatically. Generation failures never block the upload.

**Idempotency:** Default clears and repopulates. Use `--no-replace` to skip quizzes that already have questions.
```bash
python build_course.py --stage 4 --no-replace  # skip quizzes that have questions
```

---

### Stage 5 — GitHub Classroom

**What it does:**
- Creates a private GitHub template repository for each lab (or gets the existing one)
- Pushes starter kit files into the template repo
- Creates a GitHub Classroom assignment linked to the template repo, with the lab deadline
- Prints the student invite link for each assignment

**Result:** Students click their lab's invite link → GitHub Classroom creates a private repo from the template, pre-populated with the starter kit, with the due date set.

**Setup (one-time):**
1. Create a GitHub organization for the course (e.g., `byu-cs401r-f26`)
2. Create a GitHub Classroom at [classroom.github.com](https://classroom.github.com) linked to that org
3. Create a GitHub personal access token with scopes: `repo`, `read:org`, `manage_billing:github`

```bash
export GITHUB_TOKEN="ghp_..."
export GITHUB_ORG="byu-cs401r-f26"
export GITHUB_CLASSROOM_ID="12345"   # from classroom.github.com URL or API

python build_course.py --stage 5
```

**Finding your Classroom ID:**
```bash
curl -H "Authorization: Bearer $GITHUB_TOKEN" https://api.github.com/classrooms
```

**Idempotency:** Existing repos and assignments are detected and skipped. Re-running only creates what's missing.

**After Stage 5:** Copy the printed invite links into Canvas module pages (one link per lab module). Students use these to accept their assignment repo.

---

## Selective Execution

```bash
python build_course.py              # stages 1–4 (full Canvas build)
python build_course.py --stage 1    # structure only
python build_course.py --stage 2    # chapter PDFs only
python build_course.py --stage 3    # starter kits only
python build_course.py --stage 4    # quiz questions only (hardcoded)
python build_course.py --stage 5    # GitHub Classroom only (no Canvas token needed)

# AI quiz generation
export ANTHROPIC_API_KEY="sk-ant-..."
python build_course.py --stage 4 --generate-questions
python build_course.py --preview-questions   # preview without uploading
```

Stages 2 and 3 accept the module ID map from Stage 1 to avoid redundant API calls. When running standalone, they fetch module IDs themselves. Stage 5 is fully independent — it needs no Canvas token.

---

## Updating the Course

### Changing course dates / grading weights
Edit `course_config.yaml`. Re-run Stage 1.

### Adding a new chapter
Add an entry to `course_config.yaml → chapters`. Re-run Stage 2.

### Pointing at a different book
Change `course_config.yaml → source.directory` to the new book's directory. Re-run Stage 2.

### Updating lab assignments
Edit `course_config.yaml → labs`. Re-run Stage 1.

### Updating quiz questions (hardcoded)
Edit `pipeline/stage4_quizzes.py → QUESTION_BANK`. Re-run Stage 4.

### Updating quiz questions (AI-generated)
Update chapter content. Re-run Stage 4 with `--generate-questions`. Claude reads the new chapters and generates fresh questions automatically.

### Adding a new lab starter kit
1. Add files to `Starter Kits/Lab N/`
2. Add or update the `starter_kit` field in `course_config.yaml → labs`
3. Re-run Stage 3

### Full rebuild from scratch
```bash
python build_course.py             # safe — all operations are idempotent
```

---

## What Was Deliberately Left Out

These require manual action in Canvas after the pipeline runs:

| Task | Why Manual |
|------|-----------|
| **Publishing** | All items are created as drafts. Publish each module when the week is ready. |
| **Lab Guide pages** | Lab-specific rubrics and instructions — editorial content, not config |
| **Final Project instructions page** | Same — editorial content |
| **Rubric attachments** | Canvas rubric API is complex; build rubrics in the UI |
| **Announcements** | Course-specific and time-sensitive; not suitable for a static pipeline |
| **Student enrollments** | Handled by BYU registrar via SIS integration |
| **Zoom links** | Generated per-session; add to module items manually |

---

## Security Notes

- **Never hardcode the API token** in any script. Always use `CANVAS_API_TOKEN`.
- **Revoke the token** after each use: Canvas → Account → Settings → Approved Integrations → Delete.
- **Never commit `.env` files.** Add `.env` to `.gitignore`.
- **AWS credentials in starter kits:** Double-check that no `.env`, `credentials`, or `terraform.tfvars` files containing real credentials are included. The lab instructions warn students that committed secrets = automatic 0.

---

## Troubleshooting

**401 Unauthorized (Canvas)**
→ Token expired or revoked. Generate a new token and export it.

**PDF build fails (LaTeX error)**
→ Check that xelatex is installed: `xelatex --version`
→ Check the chapter Markdown for unusual Unicode characters not in the `UNICODE_HEADER` map in `stage2_readings.py`

**Module not found warnings**
→ The module name in `course_config.yaml` doesn't match the Canvas module name exactly. Run Stage 1 first to create modules.

**Large PDF files (>5 MB)**
→ Ghostscript not installed. `brew install ghostscript` and re-run with `--rebuild`.

**Quiz questions not appearing**
→ Canvas requires the quiz to be published to show question counts in the instructor view. Questions are saved even on draft quizzes; click Edit Quiz to verify.

**AI generation returns malformed JSON**
→ Claude occasionally wraps output in prose on complex chapters. The pipeline retries parsing after stripping code fences. If it still fails, the quiz falls back to the hardcoded QUESTION_BANK automatically. Check the console for the specific quiz that failed.

**`anthropic` module not found**
→ `pip install anthropic` then retry.

**GitHub 404 on classroom endpoints**
→ The GitHub Classroom API requires the token owner to be an owner or teacher in the classroom. Verify at classroom.github.com → your classroom → Settings.

**GitHub 422 on repo creation**
→ The repo name already exists. The pipeline checks for existing repos and skips creation — this usually means a name collision with a non-template repo. Rename or delete the conflicting repo on GitHub.

**git push fails (authentication)**
→ Ensure `GITHUB_TOKEN` has `repo` scope (not just `public_repo`). The token is used in the HTTPS clone URL.
