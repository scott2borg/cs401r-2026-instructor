# Superseded — do not run these

Retired **2026-08-04**. `build_course.py` at the project root owns the Canvas
course now.

## Why

These files and `build_course.py` were two systems describing one course
(34609), with byte-identical module lists, the same 7 labs and the same 12
quizzes. `build_course.py` won on three counts:

- **Config-driven.** The course lives in `course_config.yaml`, not in Python.
- **Idempotent by construction.** `canvas_api.py` exposes `ensure_assignment`,
  `ensure_module`, `ensure_page`, `ensure_quiz` — every write is create-or-update.
  `canvas_builder.py` was not; its documented recovery from a double-run was
  *Reset Course Content*, which destroys the course. The `--sync` mode added on
  2026-08-04 was reinventing what `ensure_*` already did.
- **Wider.** It also covers chapter readings (stage 2) and GitHub Classroom
  (stage 5), which `canvas_builder.py` never had.

## Where the work went

| Was here | Now |
|---|---|
| Generated lab HTML from markdown | `pipeline/lab_content.py`, called by `pipeline/stage1_structure.py` |
| Pre-Lab 3 / Pre-Lab 4 assignments | `prelabs:` in `course_config.yaml`, created by stage 1 |
| Lab + pre-lab guides → Canvas Files | `upload_guides()` in stage 1, via `canvas_api.upload_file` |
| Office Hours page | `office_hours_html()` in stage 1 |
| Starter-kit upload | stage 3 (which already did this — the 2026-08-04 uploader was a duplicate) |
| Points/retired-content/missing-file gates | `validate_content()` in `build_course.py`, runs before any Canvas write |

`verify_canvas_sync.py` is kept for reference; its checks are worth porting to a
post-run verifier for the pipeline, but it targets the retired builder's
assumptions and is not wired to anything.

Kept rather than deleted because the vault is not version-controlled.
