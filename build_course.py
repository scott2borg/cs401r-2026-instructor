#!/usr/bin/env python3
"""
CS 401R Canvas Course Builder — Main Orchestrator
==================================================
Runs the pipeline that creates/updates the Canvas course.

Usage:
    export CANVAS_API_TOKEN="7407~..."
    python build_course.py                              # run all Canvas stages (1–4)
    python build_course.py --stage 1                   # structure only
    python build_course.py --stage 2                   # chapter PDFs only
    python build_course.py --stage 3                   # starter kits only
    python build_course.py --stage 4                   # quiz questions only
    python build_course.py --stage 5                   # GitHub Classroom only
    python build_course.py --stage 2 --rebuild         # force PDF re-build
    python build_course.py --stage 4 --no-replace      # add questions, don't clear
    python build_course.py --stage 4 --generate-questions  # AI-generate from chapters
    python build_course.py --config my_config.yaml     # use different config

Stages:
    1 — Course Structure    Assignment groups, modules, pages, assignments, quizzes
    2 — Chapter Readings    Markdown → PDF → Canvas Readings folder
    3 — Starter Kits        Zip and upload lab starter kits
    4 — Quiz Questions      Populate quiz shells (hardcoded or AI-generated)
    5 — GitHub Classroom    Create template repos + Classroom assignments

Flags:
    --generate-questions    (Stage 4) Use Claude to generate quiz questions from
                            chapter content instead of hardcoded questions.
                            Requires: ANTHROPIC_API_KEY
    --rebuild               (Stage 2) Force re-build of PDFs even if they exist.
    --no-replace            (Stage 4) Skip quizzes that already have questions.
    --preview-questions     Run AI generation and print questions; do NOT upload.

Environment variables:
    CANVAS_API_TOKEN     Required for stages 1–4
    CANVAS_COURSE_ID     Optional override for course_config.yaml canvas.course_id
    ANTHROPIC_API_KEY    Required for --generate-questions
    GITHUB_TOKEN         Required for stage 5
    GITHUB_ORG           Required for stage 5
    GITHUB_CLASSROOM_ID  Required for stage 5
"""

import argparse
import os
import sys
import yaml

from pipeline.canvas_api import CanvasAPI
from pipeline import stage1_structure
from pipeline import stage2_readings
from pipeline import stage3_starters
from pipeline import stage4_quizzes
from pipeline import stage5_github
from pipeline import generate_questions


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def load_config(path: str) -> dict:
    if not os.path.exists(path):
        sys.exit(f"Config not found: {path}")
    with open(path) as f:
        return yaml.safe_load(f)


def build_api(cfg: dict) -> CanvasAPI:
    token = os.environ.get("CANVAS_API_TOKEN", "").strip()
    if not token:
        sys.exit(
            "ERROR: Set CANVAS_API_TOKEN environment variable.\n"
            "  export CANVAS_API_TOKEN='7407~...'\n"
            "  (Never hardcode tokens in source files.)\n"
            "  After use: Canvas → Account → Settings → Approved Integrations → Delete"
        )
    canvas    = cfg["canvas"]
    course_id = os.environ.get("CANVAS_COURSE_ID", canvas["course_id"]).strip()
    return CanvasAPI(canvas["base_url"], course_id, token)


def parse_args():
    p = argparse.ArgumentParser(
        description="Build or update the CS 401R Canvas course.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        "--stage", type=int, choices=[1, 2, 3, 4, 5], default=None,
        help="Run only this stage (omit to run stages 1–4)",
    )
    p.add_argument(
        "--config", default="course_config.yaml",
        help="YAML config file (default: course_config.yaml)",
    )
    p.add_argument(
        "--rebuild", action="store_true",
        help="Stage 2: force re-build of PDFs even if they already exist",
    )
    p.add_argument(
        "--no-replace", dest="replace", action="store_false", default=True,
        help="Stage 4: skip quizzes that already have questions",
    )
    p.add_argument(
        "--generate-questions", dest="generate_questions", action="store_true",
        help="Stage 4: call Claude API to generate quiz questions from chapter content "
             "(requires ANTHROPIC_API_KEY). Falls back to hardcoded bank on failure.",
    )
    p.add_argument(
        "--preview-questions", dest="preview_questions", action="store_true",
        help="Generate and print quiz questions without uploading to Canvas. "
             "Implies --generate-questions.",
    )
    return p.parse_args()


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    args = parse_args()
    cfg  = load_config(args.config)

    course = cfg["course"]
    canvas = cfg["canvas"]

    # --preview-questions: just generate and print, no Canvas or GitHub
    if args.preview_questions:
        print(f"\n{'='*60}")
        print("Quiz Question Preview (no Canvas upload)")
        print(f"{'='*60}")
        generate_questions.run(cfg, preview=True)
        return

    # Stage 5 (GitHub) doesn't need Canvas auth
    if args.stage == 5:
        print(f"\n{'='*60}")
        print(f"CS 401R Canvas Pipeline — Stage 5: GitHub Classroom")
        print(f"{'='*60}")
        stage5_github.run(cfg)
        return

    # All other stages need Canvas API token
    api = build_api(cfg)

    stages = [args.stage] if args.stage else [1, 2, 3, 4]

    print(f"\n{'='*60}")
    print(f"CS 401R Canvas Pipeline")
    print(f"Course : {course['title']}")
    print(f"Canvas : {canvas['base_url']}/courses/{canvas['course_id']}")
    print(f"Config : {args.config}")
    print(f"Stages : {stages}")
    if args.generate_questions:
        print(f"         + AI question generation (ANTHROPIC_API_KEY)")
    print(f"{'='*60}")

    module_ids     = None   # passed from stage 1 → 2, 3 to avoid redundant fetches
    generated_bank = None   # AI-generated questions, used by stage 4

    # AI question generation runs before stage 4 if requested
    if args.generate_questions and (4 in stages or args.stage == 4):
        generated_bank = generate_questions.run(cfg)

    if 1 in stages:
        module_ids = stage1_structure.run(cfg, api)

    if 2 in stages:
        stage2_readings.run(cfg, api,
                            module_ids=module_ids,
                            rebuild=args.rebuild)

    if 3 in stages:
        stage3_starters.run(cfg, api, module_ids=module_ids)

    if 4 in stages:
        stage4_quizzes.run(cfg, api,
                           replace=args.replace,
                           generated_bank=generated_bank)

    print(f"\n{'='*60}")
    print(f"Pipeline complete.")
    print(f"Review: {canvas['base_url']}/courses/{canvas['course_id']}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
