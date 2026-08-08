---
created: 2026-08-05
tags: [CS401R, canvas, runbook, process]
purpose: The complete procedure for updating the CS 401R Canvas course. Supersedes Canvas LMS/Canvas Build Instructions.md.
course_id: 34609
---

# Canvas Update Process — CS 401R

**Canvas is a derived artifact.** The source of truth is the markdown in
`CS_401R_Labs/` and the settings in `course_config.yaml`. You edit those and run
the pipeline; you never edit a lab description in Canvas.

Everything below runs from **`Efforts/Projects/Active/CS_401R_2026/`** — the
project root, *not* `Canvas LMS/`, which now holds only retired code.

---

## Before you paste anything — one-time zsh fix

**Every command block in this document has `# explanatory comments`, and zsh
does not understand them by default.** Unlike bash, zsh leaves
`interactive_comments` **off** in interactive shells, so pasting

```
unset CANVAS_API_TOKEN        # drop the stale one
```

passes `#`, `drop`, `the`, `stale`, `one` to `unset` as arguments and fails with
`unset: #: invalid parameter name`. Nothing is wrong with the command.

Fix it once:

```bash
echo 'setopt interactive_comments' >> ~/.zshrc
exec zsh
```

Verify with `setopt | grep interactivecomments` — it should now be listed.

Without this, either retype commands without their comments, or paste only the
part before the `#`.

---

## The short version

```bash
cd "/Users/scott1/Documents/Vault/Efforts/Projects/Active/CS_401R_2026"

python canvas_login.py            # ONCE, ever. Stores in the macOS Keychain.

python build_course.py            # validates, then stages 1-4
python verify_course.py           # independent read-back
```

**There is no `export` step any more.** `canvas_login.py` validates the token
against Canvas *before* storing it, and both scripts find it themselves. It
survives new shells and new terminal tabs.

If `verify_course.py` ends with `FAIL 0`, you are done. Everything is created
**unpublished**; students see nothing until you publish modules.

---

## What owns what

| Thing | Lives in | Reaches Canvas via |
|---|---|---|
| Lab content, rubrics, task points | `CS_401R_Labs/Lab_N--*.md` | parsed by `pipeline/lab_content.py`, stage 1 |
| Pre-lab guides | `CS_401R_Labs/Pre-Lab N — *.md` | stage 1, uploaded to Files |
| Starter kits | `CS_401R_Labs/Starter Kits/Lab N/` | stage 3, zipped |
| Chapter readings | `EAIE/Part N/*.md` → `EAIE/Build/canvas_chapters/*.pdf` | stage 2 |
| Lecture slides | `Presentations/PowerPoint/*.pptx` | stage 6 |
| Quiz questions | `pipeline/stage4_quizzes.py` | stage 4 |
| Dates, weights, modules, structure | `course_config.yaml` | stage 1 |
| Syllabus grading table | **generated** from `grading.groups` | stage 1 |

**Do not edit lab descriptions, the syllabus, or assignment settings in the
Canvas UI.** The next run overwrites them without warning. Edit the source.

---

## Step 1 — Token (once, then never again)

Canvas → avatar → **Account** → **Settings** → **Approved Integrations** →
**New Access Token**. Copy it with the **copy button**; Canvas shows it once.

```bash
python canvas_login.py
```

It prompts with input hidden, **validates the token against Canvas and the
course**, and only then stores it in the macOS Keychain. A truncated paste
fails here, in two seconds, instead of halfway through a build.

| Command | Does |
|---|---|
| `python canvas_login.py` | store it (refuses to clobber an existing entry) |
| `python canvas_login.py --status` | is one stored, and does it still work? |
| `python canvas_login.py --replace` | overwrite after regenerating in Canvas |
| `python canvas_login.py --forget` | remove it |

**Where the token comes from, in order:** `$CANVAS_API_TOKEN` → Keychain →
prompt. Every script prints which one it used, e.g.
`[token from macOS Keychain]`.

> **`$CANVAS_API_TOKEN` beats the Keychain.** That is deliberate — an explicit
> export should win — but it is the one sharp edge left. If a shell still has
> an old token exported and you have since regenerated it in Canvas, that
> shell keeps using the dead one. **This is exactly what happened on
> 2026-08-07.** The preflight now names the source and tells you to
> `unset CANVAS_API_TOKEN`.

Two rules that still hold:

- **Never paste it into a chat.** It is a full-privilege credential on a live
  course. If it is ever exposed, revoke first and ask questions after.
- **Never type it on a command line.** `export CANVAS_API_TOKEN="7407~..."`
  lands verbatim in `~/.zsh_history`. `canvas_login.py` uses `getpass`, and
  writes to the Keychain via `security -i` so the token never appears in this
  process's `argv` where `ps` could read it.

When the course is done: revoke the token in Canvas, then
`python canvas_login.py --forget`.

<details>
<summary>If you are not on macOS, or want a one-off shell</summary>

```bash
printf 'Canvas token: '; read -rs CANVAS_API_TOKEN; echo; export CANVAS_API_TOKEN
```

Paste the token line **by itself** — pasting the whole block makes `read`
consume the next line instead of waiting. And do **not** use
`read -rsp "prompt" VAR`: that is the bash idiom, and in zsh `-p` means *read
from the coprocess*, so it prompts for nothing, sets the variable **empty**,
and appears to succeed.
</details>

---

## Step 2 — Build

```bash
python -u build_course.py 2>&1 | tee build.log
```

**`-u` is not optional when piping.** Python block-buffers stdout when it is not
a terminal, so `python build_course.py | tee log` shows *nothing* until a 4-8 KB
buffer fills. Stage 6 uploads 73 MB of slides; that is minutes of total silence
that looks exactly like a hang. `python -u` forces line buffering. If you do not
need the log, drop the pipe entirely — straight to the terminal is line-buffered
and shows progress live.

`| tee build.log` is otherwise not optional in practice. Stages return early on failure
**without changing the exit code**, so a stage can do nothing at all and the run
still exits 0. The log is the only place that says so, and the run now prints
`=== stages that executed: ... ===` at the end.

### Stages

| # | Does | Notes |
|---|---|---|
| 1 | Groups, modules, pages, labs, pre-labs, AWS Academy, quizzes, guide uploads | The big one |
| 2 | Chapter reading PDFs → Files → linked into modules | Uses pre-built PDFs if present |
| 3 | Starter kits zipped → Files → linked | One zip per lab with a `starter_kit` path |
| 4 | Quiz questions into the 12 shells | Idempotent: clears then re-uploads |
| 5 | GitHub Classroom | Not part of the default run; needs `GITHUB_TOKEN` |
| 6 | Lecture decks → Files → linked into weekly modules | 26 .pptx, ~73 MB. **Uploads only — never regenerates** |

Run one stage with `--stage N`. Default is **1, 2, 3, 4, 6**.

**Re-running is safe.** Every write goes through `ensure_*` in
`pipeline/canvas_api.py`, which creates or updates rather than duplicating.

### The gate

`validate_content()` runs before anything touches Canvas and **refuses to push**
if:

- any lab's task points do not sum to **100**
- a **retired gate or stale figure** appears in a generated description — the
  0.72 AUC gate, the 0.03 lift gate, "train freely", "5 stages", the
  1,200-customer dataset, DPU-s as a point value
- a **starter kit promises a file it does not contain**
- a **starter_kit path does not resolve**
- a **pre-lab guide** named in the config is missing
- a **chapter PDF** is not staged

Every one of those has reached students or silently skipped work at least once.

---

## Step 3 — Verify

```bash
python -u verify_course.py 2>&1 | tee verify.log
```

Independent read-back. It exists because the build reports what it *attempted*.
Checks, in order of what has actually gone wrong:

1. **Duplicate assignments** — `ensure_*` matches on name; an item created under
   a different name gets a second copy rather than an update
2. **Duplicate module items** — the same assignment or page linked into a module
   more than once. Invisible in the build output and the most likely duplicate
   you will actually see
2. Every expected lab, pre-lab and Academy assignment exists exactly once
3. Lab descriptions have a generated points table and a **real** guide link, not
   the "see the course repository" fallback
4. Pre-labs are 0 points, due Sep 30, and link to their guides
5. **Retired-content sweep** across every assignment description and page body
6. **Module placement** — assignments created but orphaned
7. Files: exact expected filenames per folder, reported as `MISSING` vs `STRAY`
8. Chapter readings and starter kits present by name
9. Quizzes exist **and have questions**
10. **Grading weights** match config, total 100, and **no weighted group is
    empty** — Canvas drops an empty group's weight and scales the rest up
11. All four pages including Office Hours

---

## Troubleshooting

Every row below is a failure that actually happened.

| Symptom | Cause | Fix |
|---|---|---|
| `unset: #: invalid parameter name` (or a `#` treated as an argument) | **zsh does not treat `#` as a comment interactively.** `interactive_comments` is off by default, so pasting any command with a trailing `# note` passes the comment as arguments | `setopt interactive_comments` — see below. Or retype the command without the comment |
| `can't open file '.../Canvas LMS/build_course.py'` | Running from the wrong directory | `cd` to the project root |
| Terminal looks hung after the token line | `read -rs` is silent by design | Paste and press Enter |
| Long silence during a build, looks hung | Python block-buffers stdout when piped to `tee` | Use `python -u`, or drop the pipe |
| `Invalid access token` right after setting it | Variable empty — whole block pasted at once, or the zsh `-rsp` trap | `python check_token.py` |
| `Invalid access token` on a token that worked | Not exported in *this* shell | Re-export |
| `TypeError: list indices must be integers` | `/folders/by_path/` returns the folder **hierarchy as a list** | Fixed in `canvas_api.py` |
| `Cannot create Readings folder` | `parent_folder_path: "/"` is not a Canvas path; the root is `course files` | Fixed in `canvas_api.py` |
| Groups all named "Assignments", weight 0.0 | Assignment-groups endpoint takes **flat** params, not a nested wrapper | Fixed; `fix_assignment_groups.py` repairs existing |
| Weights stuck at old values | `ensure_assignment_group` returned on name match and never checked the weight | Fixed — it reweights now |
| Starter kits never upload | `starter_kit` paths did not resolve; stage 3 skipped silently | Fixed in config; gate now catches it |
| `✓ Start/end dates set` right after a 401 | Stage 1 never checked the result | Fixed — aborts cleanly |
| Assignments vanish after a run | Deleting a group deletes its assignments unless `move_assignments_to` is passed | Fixed — refuses to delete without a destination |
| Same assignment listed several times in a module | `add_module_item` was a bare POST with no existence check — one extra copy per run | Fixed; `dedupe_course.py` cleans existing |

### The pattern

**Almost every failure printed success for something that had not happened.**
False success on the dates PUT, group names echoed from intent rather than from
Canvas, a weight never read back, a folder helper that never worked so two
stages never ran. When something looks fine but the result is wrong, suspect the
report before the request.

---

## "There are duplicates!" — check before you act

Two things look like duplication and are not:

- **Quiz shadow assignments.** Every Canvas quiz *also* appears in the
  Assignments list with the same title. 12 quizzes legitimately show up twice.
  This is Canvas working correctly.
- **A stale browser tab.** Canvas caches assignment and module pages hard. A run
  that changes things underneath an open tab shows a mixed picture until you
  refresh.

```bash
python find_duplicates.py     # read-only, reads the API, cannot be fooled by cache
```

It scans assignment groups, quizzes, assignments, modules, module items per
module, pages, and files by folder, and excludes quiz shadows. `TOTAL redundant
objects: 0` means the course is clean.

**Do not reset the course on the strength of what a page looks like.** Reset
deletes the course and issues a new ID, and on 2026-08-05 it was nearly done on
a course that turned out to have zero duplicates.

## Proving the pipeline is idempotent

The property worth re-checking whenever a stage changes:

```bash
python build_course.py >/dev/null 2>&1
python find_duplicates.py          # must still be 0
```

A second run must add nothing. `add_module_item` and `add_module_page` were bare
POSTs until 2026-08-05 and would have failed this.


## Canvas API gotchas — read this before debugging anything

**Canvas silently ignores unknown parameters, applies its defaults, and returns
success.** Every hard bug on 2026-08-05/06 was this one behaviour. The API said
`200 OK` and handed back a real object id in every single case. Reading the
build output can never catch these; only reading back what Canvas *stored* can.

| Endpoint | Wrong | Right | What the wrong version did |
|---|---|---|---|
| `POST /courses/:id/files` | `folder_id` | **`parent_folder_id`** | All 55 uploads landed in `unfiled` while every target folder sat empty |
| `POST /courses/:id/assignment_groups` | `{"assignment_group": {...}}` | **flat** `name`, `group_weight`, `position` | Created 7 groups all named "Assignments" at weight 0.0 |
| `POST /courses/:id/folders` | `parent_folder_path: "/"` | **`parent_folder_id`** of `/folders/root`, or path `"course files"` | Folder creation failed, so stages 2 and 3 aborted and had never once run |
| `GET /folders/by_path/X` | treat as a dict | **it is a LIST** — the hierarchy, root first, target last | `TypeError: list indices must be integers` |
| `DELETE /assignment_groups/:id` | no `move_assignments_to` | **always pass it** | Deletes every assignment inside the group |
| Any `GET` collection | no `per_page` | **`per_page=100`** | Canvas defaults to 10; endpoints without a Link header return exactly 10 with no sign anything is missing |

**Quiz shadow assignments.** Every quiz also appears in `/assignments` with the
same title. Normal. Not a duplicate.

**`on_duplicate: overwrite` is per-folder.** Re-uploading the same filename into
a different folder creates a second copy rather than replacing the first.

### The debugging order that actually works

1. `python debug_files.py` — what does Canvas actually hold?
2. `python survey_course.py` — what assignments/groups exist?
3. `python find_duplicates.py` — is anything genuinely duplicated?

Only then read the build log. On 2026-08-06 the answer was visible in step 1 and
was instead inferred through four rounds of downstream symptoms.

## Repair scripts

Read-only unless you pass `--apply`. Each has a dry run.

| Script | Use when |
|---|---|
| `debug_files.py` | **Start here** for any file problem. Prints per-endpoint counts, Link-header presence, and every folder with its file count |
| `survey_course.py` | "What is actually in the course?" Read-only |
| `find_duplicates.py` | Every entity type scanned for duplicates; excludes quiz shadows |
| `canvas_login.py` | Store/replace/forget the Keychain token; `--status` tests it |
| `check_token.py` | Auth failing. Reports the token's shape without revealing it |
| `set_course_id.py` | Point the config at a different course (needed after a Reset) |
| `fix_assignment_groups.py` | Duplicate/misnamed groups, wrong weights |
| `fix_unfiled.py` | Files stuck in `unfiled` — moves rather than re-uploads |
| `fix_stray_guides.py` | A guide file in the wrong folder |
| `fix_leftovers.py` | Redundant unfiled copies and obsolete kit files |
| `clean_lab_guides.py` | Non-lab-guide files in `Lab Guides` |
| `dedupe_course.py` | Duplicate module items |

All are dry-run by default; pass `--apply` to act. **If a cleanup script does not
do what you expect, delete the file by hand in Canvas → Files.** Several of these
were written under time pressure to fix one specific mess and are not worth
debugging a second time.


---

## Editing the course

| To change | Edit | Then |
|---|---|---|
| Lab tasks, points, rubrics, prose | `CS_401R_Labs/Lab_N--*.md` | `python build_course.py --stage 1` |
| Grading weights | `course_config.yaml` → `grading.groups` | Must total 100, or the build refuses |
| Quiz points, dates | `course_config.yaml` → `quizzes` | |
| Quiz questions | `pipeline/stage4_quizzes.py` | `--stage 4` |
| Due dates | `course_config.yaml` | |
| Chapter readings | `EAIE/Part N/*.md`, rebuild PDFs | `--stage 2` |
| Starter kit contents | `CS_401R_Labs/Starter Kits/Lab N/` | `--stage 3` |
| Lecture slides | edit the `.pptx` directly in `Presentations/PowerPoint/` | `--stage 6` |
| Office hours | `stage1_structure.office_hours_html()` | `--stage 1` |

Preview generated lab content without touching Canvas:

```bash
python pipeline/lab_content.py     # every task + points per lab; non-zero exit on failure
```

---

## Chapter reading PDFs

Chapters are **extracted from the built manuscript**, not re-rendered, so page
numbers and running heads match the book exactly.

```bash
cd "/Users/scott1/Documents/Vault/Efforts/Projects/Active/EAIE"
python3 Build/build_book.py                                    # ~25 min
python3 Build/extract_chapter.py --chapter "Model Development" \
        --out-dir ../CS_401R_2026/Build/chapters
```

Then copy each into `EAIE/Build/canvas_chapters/` under the filename
`course_config.yaml` expects (`chapters[].pdf`), and run `--stage 2`.

**Compression is off on purpose.** `source.compress_pdfs: null`. Ghostscript
`/ebook` took Ch01 from 18.5 MB to 1.1 MB but downsampled the worst figure to
**12% of its pixels** — and these chapters are full of architecture diagrams with
small text labels. 16 chapters at full resolution is **143 MB** against a
**500 MB** course quota. `/printer` is the middle ground if that ever changes.

Check the quota:

```bash
curl -s -H "Authorization: Bearer $CANVAS_API_TOKEN" \
  "https://byu.instructure.com/api/v1/courses/34609/files/quota" | python3 -m json.tool
```

---

## Grading

| Group | Weight |
|---|---|
| Labs | 49% |
| Final Project | 30% |
| Reading Quizzes | 10% |
| AWS Academy Courses | 11% |

The syllabus table is **generated** from this block; it used to be hardcoded HTML
and drifted. The build refuses if the weights do not total 100.

**A weighted group with no assignments is silently dropped by Canvas** and its
weight redistributed. `verify_course.py` fails on this.

---

## Still manual

1. **Presentation schedule** (student final presentations) — post by Dec 1 in the Finals week area. Distinct from the lecture decks, which stage 6 handles
2. **Publish** — Canvas → Modules → Publish All, when ready
3. **Revoke the API token**

---

## Notes

- Pre-labs are **0 points by design**, graded inside the lab each gates. The due
  date is the payload: it puts them on the calendar early enough for AWS
  approvals to land.
- Both **AWS Academy** assignments open on day one and overlap Lab 1 deliberately.
- **Lecture decks are the source of truth.** `generate_presentations.py` built
  them once; do not re-run it to change Canvas, or hand edits are lost.
  Stage 6 uploads whatever is in `Presentations/PowerPoint/`.
- Two decks per week, except Week 01, Week 13 (Thanksgiving) and Weeks 14-15,
  which have one each. 26 total.
- `Canvas LMS/_superseded/` holds the retired `canvas_builder.py` and its
  verifier. Do not run them; they target a different design and are not
  idempotent.
