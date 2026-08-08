#!/usr/bin/env python3
"""
CS 401R Canvas Course Builder — Main Orchestrator
==================================================
Runs the pipeline that creates/updates the Canvas course.

Usage:
    python canvas_login.py          # once; stores in the macOS Keychain
    (or export CANVAS_API_TOKEN for a one-off shell)
    python build_course.py                              # run all Canvas stages (1-4, 6)
    python build_course.py --stage 1                   # structure only
    python build_course.py --stage 2                   # chapter PDFs only
    python build_course.py --stage 3                   # starter kits only
    python build_course.py --stage 4                   # quiz questions only
    python build_course.py --stage 5                   # GitHub Classroom only
    python build_course.py --stage 6                   # lecture presentations only
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
    6 — Presentations       Upload lecture decks, link into weekly modules

Flags:
    --generate-questions    (Stage 4) Use Claude to generate quiz questions from
                            chapter content instead of hardcoded questions.
                            Requires: ANTHROPIC_API_KEY
    --rebuild               (Stage 2) Force re-build of PDFs even if they exist.
    --no-replace            (Stage 4) Skip quizzes that already have questions.
    --preview-questions     Run AI generation and print questions; do NOT upload.

Environment variables:
    CANVAS_API_TOKEN     Optional. Overrides the Keychain (canvas_login.py).
                         Stages 1-4 and 6 need a token from one source or the other.
    CANVAS_COURSE_ID     Optional override for course_config.yaml canvas.course_id
    ANTHROPIC_API_KEY    Required for --generate-questions
    GITHUB_TOKEN         Required for stage 5
    GITHUB_ORG           Required for stage 5
    GITHUB_CLASSROOM_ID  Required for stage 5
"""

import argparse
import pathlib
import os
import sys
import yaml

from pipeline.canvas_api import CanvasAPI
from pipeline import canvas_token
from pipeline import stage1_structure
from pipeline import stage2_readings
from pipeline import stage3_starters
from pipeline import stage4_quizzes
from pipeline import stage5_github
from pipeline import stage6_presentations
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
    """Resolve the token, then PROVE it works before any stage runs.

    Writes go through CanvasAPI._post/_put, which print `✗ <status>` and return
    None rather than raise -- so one bad item does not abandon a long run. The
    side effect is that a bad TOKEN is indistinguishable from hundreds of bad
    items: on 2026-08-07 a rejected token produced a wall of `✗ 401`, wrote
    nothing, and still exited 0. The preflight below turns that into one clear
    error before the first write.
    """
    canvas    = cfg["canvas"]
    course_id = os.environ.get("CANVAS_COURSE_ID", "").strip() or canvas["course_id"]

    token, source = canvas_token.resolve()
    who = canvas_token.preflight(canvas["base_url"], token, source, course_id)
    print(f"Authenticated as {who}  [token from {source}]")

    return CanvasAPI(canvas["base_url"], course_id, token)


def parse_args():
    p = argparse.ArgumentParser(
        description="Build or update the CS 401R Canvas course.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        "--stage", type=int, choices=[1, 2, 3, 4, 5, 6], default=None,
        help="Run only this stage (omit to run stages 1-4 and 6)",
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

def validate_content(cfg) -> None:
    """Refuse to push if the source markdown is structurally wrong.

    Three classes of failure, all of which have actually shipped to students
    on this course at least once:

      1. Task points that do not sum to 100.
      2. A retired gate or stale figure surviving in a generated description.
         On 2026-08-04 "AUC-ROC >= 0.72" reached Canvas two days after being
         retired, because a hand-written copy was never updated.
      3. A starter kit promising a file it does not contain. Lab 1 advertised
         `northstar-overview.md` (the file is northstar-scenario-overview.md)
         and a `terraform-module-template/` that had never been written.

    Failing here is cheap. Failing in front of thirty students is not.
    """
    from pipeline import lab_content
    import re

    problems = []
    RETIRED = [
        (r"AUC[- ]?ROC\s*(&ge;|>=|≥)\s*0\.72", "retired absolute AUC 0.72 gate"),
        (r"(&ge;|>=|≥)\s*0\.03\s*(lift|AUC)",   "retired fixed 0.03 lift gate"),
        (r"[Tt]rain freely",                      "'train freely' — training quota is 0 by default"),
        (r"5 stages",                             "superseded '5 stages' wording"),
        (r"1,200[- ]customer",                    "retired 1,200-customer dataset"),
    ]

    for n in sorted(lab_content.LAB_FILES):
        parsed = lab_content.parse_lab(n)
        problems += lab_content.validate(parsed)

        html = lab_content.lab_summary_html(parsed)
        for pat, label in RETIRED:
            if re.search(pat, html):
                problems.append("Lab %d: generated description contains %s" % (n, label))

        _, missing = lab_content.check_starter_kit(parsed)
        for miss in missing:
            problems.append(
                "Lab %d: starter kit promises '%s' but it is not in "
                "Starter Kits/Lab %d/" % (n, miss, n))

    base = pathlib.Path(__file__).resolve().parent
    for pl in cfg.get("prelabs", []):
        if not (base / pl["guide"]).exists():
            problems.append("Pre-Lab %s: guide not found at %s" % (pl["number"], pl["guide"]))

    # Paths that do not resolve made stage 3 skip every kit silently: the
    # config said "Starter Kits/Lab 1" but the directories live under
    # CS_401R_Labs/. Stage 3 printed a not-found line per lab and carried on,
    # so the run "succeeded" having uploaded nothing.
    for l in cfg["labs"]:
        sk = l.get("starter_kit") or ""
        if sk and not (base / sk).is_dir():
            problems.append("Lab %s: starter_kit path does not resolve: %s"
                            % (l["number"], sk))

    for d in cfg.get("presentations", []):
        if not (base / d["file"]).exists():
            problems.append("Presentation missing: %s (%s)" % (d["file"], d["title"]))
    mod_names = set(cfg["modules"])
    for d in cfg.get("presentations", []):
        if d["module"] not in mod_names:
            problems.append("Presentation '%s' names an unknown module: %s"
                            % (d["title"], d["module"]))

    for ch in cfg.get("chapters", []):
        pdf = base.parent / "EAIE" / cfg["source"]["output_dir"] / ch["pdf"]
        if not pdf.exists():
            problems.append("Chapter PDF not staged: %s" % ch["pdf"])

    if problems:
        print("\nREFUSING TO PUSH — source content failed validation:")
        for pr in problems:
            print("  !!", pr)
        sys.exit(1)
    print("Content validated: %d labs sum to 100 pts, no retired gates, "
          "all promised files present" % len(lab_content.LAB_FILES))


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

    # Nothing reaches Canvas until the source content is sound.
    validate_content(cfg)

    # All other stages need Canvas API token
    api = build_api(cfg)

    stages = [args.stage] if args.stage else [1, 2, 3, 4, 6]

    print(f"\n{'='*60}")
    print(f"CS 401R Canvas Pipeline")
    print(f"Course : {course['title']}")
    print(f"Canvas : {canvas['base_url']}/courses/{api.course_id}")
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

    # Per-stage outcome, printed at the end. Individual stages return early on
    # failure (stage 2 does this when the Readings folder cannot be made), so
    # a stage can do nothing at all and the run still exits 0 -- which is how
    # "everything uploaded?" stayed unanswerable for several rounds.
    import atexit
    _ran = []
    atexit.register(lambda: print("\n=== stages that executed: "
                                  + (", ".join(_ran) if _ran else "NONE") + " ==="))

    if 1 in stages:
        _ran.append("1")
        module_ids = stage1_structure.run(cfg, api)

    if 2 in stages:
        _ran.append("2")
        stage2_readings.run(cfg, api,
                            module_ids=module_ids,
                            rebuild=args.rebuild)

    if 3 in stages:
        _ran.append("3")
        stage3_starters.run(cfg, api, module_ids=module_ids)

    if 4 in stages:
        _ran.append("4")
        stage4_quizzes.run(cfg, api,
                           replace=args.replace,
                           generated_bank=generated_bank)

    if 6 in stages:
        _ran.append("6")
        stage6_presentations.run(cfg, api, module_ids)

    print(f"\n{'='*60}")
    print(f"Pipeline complete.")
    print(f"Review: {canvas['base_url']}/courses/{api.course_id}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
