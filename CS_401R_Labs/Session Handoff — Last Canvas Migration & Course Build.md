---
created: 2026-08-06
tags: [CS401R, handoff, canvas, pipeline, course-build, defects]
supersedes: "Session Handoff — Lab 4 Verified Clean-Slate"
purpose: The Canvas course is built and verified. Ownership moved to build_course.py. Records the API behaviour that caused a day of debugging.
course_id: 34609
---

# Session Handoff — Canvas Migration & Course Build

> **Read this before touching Canvas.** The course is built. The runbook is
> [[Canvas Update Process]] at the project root. This note records what changed,
> what is still open, and the one API behavior behind almost every failure.
>
> **The headline: `Canvas silently ignores unknown parameters, applies defaults, and returns success.`** Four separate bugs, all the same shape, all reporting `200 OK` with a valid object id. No amount of reading build output catches these — only reading back what Canvas stored.

---

## Course state — course 34609

**53 of 55 checks passing.** Everything student-facing is correct and verified
against the live API.

| | |
|---|---|
| Labs | 7, descriptions generated from markdown, each linking its full guide |
| Pre-labs | 2, 0 pts, due Sep 30, linked to guides |
| AWS Academy | 2, 50 pts each, open Sep 3, due Sep 12 / Sep 19 |
| Final Project + Team Sign-Up | present |
| Quizzes | 12 shells, **all populated**, 5 pts each |
| Modules | 16, no duplicate items |
| Pages | 4 incl. Office Hours (Tu/Th after class or by appointment) |
| Chapter readings | 16 PDFs, full resolution, 143 MB |
| Presentations | 26 decks, mapped 2/week except Weeks 01, 13, 14, 15 |
| Starter kits | 4 zips |
| Guides | 7 lab + 2 pre-lab, HTML |
| Grading | Labs 49 / Final Project 30 / Reading Quizzes 10 / AWS Academy 11 = 100 |
| Storage | ~241 MB of 500 MB |

**Everything is unpublished.** Nothing is student-visible.

**Outstanding, manual:** two duplicate pre-lab HTML files in Files → `Lab Guides`
(the correct copies are in `Pre-Lab Guides`); three obsolete `.md` files in
`Lab Starter Kits`. Cosmetic. Scott is deleting these by hand — several cleanup
scripts failed to and are not worth further debugging.

---

## Ownership moved to `build_course.py`

There were **two systems targeting course 34609** with byte-identical module
lists, the same 7 labs and the same 12 quizzes. `build_course.py` won:
config-driven, and already idempotent via `ensure_*` — the `--sync` mode built
for `canvas_builder.py` was reinventing what `ensure_*` already did.

`canvas_builder.py` and its verifier are in `Canvas LMS/_superseded/` with a
README. **Do not run them.**

Everything that lived only in the retired builder moved across: markdown-derived
lab HTML (`pipeline/lab_content.py`), pre-labs, guide uploads, office hours, and
the validation gates.

---

## The API behavior that cost the day

| Endpoint | Wrong | Right | Effect |
|---|---|---|---|
| `POST /files` | `folder_id` | `parent_folder_id` | **All 55 uploads went to `unfiled`** while every target folder sat empty |
| `POST /assignment_groups` | nested wrapper | flat params | 7 groups named "Assignments" at weight 0.0 |
| `POST /folders` | `parent_folder_path: "/"` | root id, or `"course files"` | **Stages 2 and 3 had never run** |
| `GET /folders/by_path/X` | dict | **list** (hierarchy) | `TypeError` |
| `DELETE /assignment_groups/:id` | no destination | `move_assignments_to` | Deletes the assignments inside |
| Any collection `GET` | no `per_page` | `per_page=100` | Silently returns 10 |

All six are fixed. The `per_page` default is now in `_get_all`, so it applies to
every call site.

### Other defects fixed

- `add_module_item` / `add_module_page` were bare POSTs — **one duplicate link
  per run**. Now idempotent on `(type, content_id)`.
- `ensure_assignment_group` matched on name and never checked the weight, so
  groups kept old weights after the config changed.
- Stage 1 printed `✓ Start/end dates set` immediately after a 401.
- `starter_kit` paths in config did not resolve; stage 3 skipped all four labs
  silently.
- Stage 2 hardcoded Ghostscript `/ebook`; now `source.compress_pdfs`, set to
  `null`.
- `--stage 6` was rejected by argparse after stage 6 was added everywhere else.

---

## Course content decisions made

- **Grading reweighted** to 49/30/10/11; Participation removed entirely. The
  syllabus grading table is now **generated** from `grading.groups` — it was
  hardcoded HTML and had drifted. The build refuses if weights ≠ 100.
- **Reading quizzes 10 → 5 points.** Weighted grading means this changes what
  students see per quiz, not what they earn.
- **AWS Academy** added as a graded category with two assignments, deliberately
  overlapping Lab 1.
- **Chapter PDFs kept at full resolution.** Ghostscript `/ebook` took Ch01 from
  18.5 MB to 1.1 MB but downsampled the worst figure to **12% of its pixels**,
  and these chapters are full of architecture diagrams with small labels.
- **Lecture decks are the source of truth.** `generate_presentations.py` built
  them once; stage 6 only uploads. Do not re-run the generator to change Canvas.

---

## Open threads

1. **NEW — 24 of 26 lecture decks have no figures.** L01 has 39 images and L02
   has 45; L03–L26 have **zero**. They are not stubs (15–16 slides, ~200 text
   elements each) but they are text-only. `Presentations/Figure_Descriptions/`
   holds detailed per-slide figure specs for all 26 that were never built —
   `generate_presentations.py` has only 6 figure-related lines.
   **Decided 2026-08-06: Scott is generating the figures with a separate,
   image-capable LLM from the `Figure_Descriptions/` specs.** Not a task for this
   assistant.

   **When the images come back**, the remaining work is: insert them into the
   `.pptx` files in `Presentations/PowerPoint/`, then `python build_course.py
   --stage 6`. Uploads now overwrite by name (the `parent_folder_id` fix), so
   re-running replaces the decks in place rather than duplicating them. Do NOT
   re-run `generate_presentations.py` — it would discard the inserted figures.
2. **The quota decision — assigned to Scott and his TA (2026-08-06).** Still the
   largest deliverability risk, now owned rather than open. Lab 4's
   TrainingStep needs an on-demand training quota (AWS default **0**), and Lab 3
   Track B/C needs Bedrock. ~60 support cases across 30 independent accounts.
   Pre-Lab 4 gets students filing in September, which helps but does not remove
   the dependency. Four sessions have proven the code works on an account that
   already has the quota.
3. **Lab 5 canary/rollback and Lab 6 Model Monitor** never re-run at 10k.
4. **Model package v7** still `Approved` with a dead `ModelDataUrl`.
5. **Publish** — modules are unpublished; presentation schedule (student finals)
   still to post by Dec 1.
6. ~~Revoke the Canvas API token~~ — **done 2026-08-06.** The token exposed in
   chat on 2026-08-05 has been revoked. Mint a fresh one for the next run and
   use the `printf`/`read -rs` form in the runbook.
7. Vault copy under `Sample Solutions/` still stale and gitignored.

---

## Notes for next session

- **`python debug_files.py` is step one for any Canvas file problem.** On
  2026-08-06 the answer was in its output and was instead inferred through four
  rounds of downstream symptoms. The tool existed before it was used.
- **Verification code needs the same scrutiny as the code it checks.**
  `verify_course.py` reported 0 presentations seconds after 26 successful
  uploads — it was reading the first 10 files in the course. A false failure
  sends you chasing problems that do not exist.
- **Run the exact command before handing it over.** `--stage 6` was rejected by
  argparse; `| tee` made Python block-buffer so a working build looked hung;
  `read -rsp` silently sets an empty variable in zsh. Each was a one-second
  check that was not done.
- Several cleanup scripts (`fix_leftovers.py`, `clean_lab_guides.py`) did not
  work as intended. **Deleting a file by hand in Canvas is a legitimate fix** and
  usually faster than debugging a single-use script.
- The book manuscript is at 833 pages with the unclosed-fence fix, restoring 45
  pages of *Measuring Business Value* and *Closing the Loop* that had been
  rendered inside a code block.
