"""
AI-powered quiz question generation using Claude.

Maps each quiz to its source chapters via shared module name,
reads the chapter Markdown, and calls the Anthropic API to generate
5 questions in the same dict format used by stage4_quizzes.QUESTION_BANK.

Results are merged with the hardcoded bank — AI-generated questions
take precedence; missing quizzes fall back to hardcoded questions.

Environment:
    ANTHROPIC_API_KEY   Required for generation

Usage (standalone preview):
    python -m pipeline.generate_questions

Usage (integrated — called by build_course.py --generate-questions):
    from pipeline.generate_questions import run
    generated_bank = run(cfg)
"""

import json
import os
import re


# ─────────────────────────────────────────────────────────────────────────────
# Chapter lookup helpers
# ─────────────────────────────────────────────────────────────────────────────

def _chapters_for_quiz(quiz: dict, chapters: list, source_dir: str) -> list[str]:
    """Return file paths of chapters whose modules include this quiz's module."""
    quiz_module = quiz["module"]
    paths = []
    for ch in chapters:
        if quiz_module in ch["modules"]:
            fp = os.path.join(source_dir, ch["file"])
            if os.path.exists(fp):
                paths.append(fp)
    return paths


def _read_content(paths: list[str], max_chars: int = 64_000) -> str:
    """Read and concatenate chapter content, truncated to max_chars."""
    parts = []
    total = 0
    for path in paths:
        with open(path, encoding="utf-8", errors="replace") as f:
            text = f.read()
        if total + len(text) > max_chars:
            remaining = max_chars - total
            if remaining > 2000:
                parts.append(text[:remaining] + "\n\n[Chapter truncated — content continues]")
            break
        parts.append(text)
        total += len(text)
    return "\n\n---\n\n".join(parts)


# ─────────────────────────────────────────────────────────────────────────────
# Claude API call
# ─────────────────────────────────────────────────────────────────────────────

_SYSTEM = """\
You write reading quiz questions for CS 401R — Engineering Production AI Systems, \
a graduate-level course at Brigham Young University. \
The audience is senior CS students and technology professionals. \
Questions test conceptual understanding and engineering judgment, not trivia."""

_USER_TMPL = """\
Quiz title: "{title}"

Chapter content:
<chapter>
{content}
</chapter>

Generate exactly 5 quiz questions. Rules:
- All questions must be answerable from the chapter content above
- Mix: 3–4 multiple choice (type "mc"), 1–2 true/false (type "tf")
- MC distractors must be plausible, not obviously wrong
- T/F statements must be unambiguous
- Test: key concepts, engineering tradeoffs, case study lessons, why things work
- Do NOT test: page numbers, headings, author names, or trivia
- Difficulty: appropriate for a 15-minute timed quiz

Return ONLY valid JSON — no preamble, no explanation:
[
  {{
    "type": "mc",
    "text": "Question ending with a question mark?",
    "correct": "The correct answer",
    "wrong": ["Plausible wrong 1", "Plausible wrong 2", "Plausible wrong 3"]
  }},
  {{
    "type": "tf",
    "text": "A precise statement that is clearly true or false.",
    "correct": "True"
  }}
]"""


def _extract_json(text: str) -> str:
    """Strip markdown code fences if present."""
    match = re.search(r"```(?:json)?\s*([\s\S]+?)```", text)
    if match:
        return match.group(1).strip()
    return text.strip()


def _generate(quiz_title: str, content: str, model: str = "claude-opus-4-5") -> list[dict] | None:
    """Call Claude and return 5 structured question dicts, or None on failure."""
    try:
        import anthropic
    except ImportError:
        print("    ✗ anthropic not installed. Run: pip install anthropic")
        return None

    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        print("    ✗ ANTHROPIC_API_KEY not set")
        return None

    client = anthropic.Anthropic(api_key=api_key)
    try:
        message = client.messages.create(
            model=model,
            max_tokens=2500,
            system=_SYSTEM,
            messages=[{
                "role": "user",
                "content": _USER_TMPL.format(title=quiz_title, content=content),
            }],
        )
        raw = message.content[0].text
        parsed = json.loads(_extract_json(raw))

        # Validate structure
        if not isinstance(parsed, list):
            print(f"    ✗ Response is not a list")
            return None
        for q in parsed:
            if q.get("type") not in ("mc", "tf"):
                print(f"    ✗ Unknown question type: {q.get('type')}")
                return None
            if q["type"] == "mc" and len(q.get("wrong", [])) < 2:
                print(f"    ✗ MC question has fewer than 2 distractors")
                return None
        return parsed

    except json.JSONDecodeError as e:
        print(f"    ✗ JSON parse error: {e}")
        return None
    except Exception as e:
        print(f"    ✗ API error: {type(e).__name__}: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Public interface
# ─────────────────────────────────────────────────────────────────────────────

def run(cfg: dict, preview: bool = False,
        model: str = "claude-opus-4-5") -> dict[str, list[dict]]:
    """
    Generate quiz questions for all quizzes defined in cfg.

    Returns:
        {quiz_title: [question_dicts, ...]}
        Only includes quizzes for which generation succeeded.
        Quizzes not in this dict should fall back to QUESTION_BANK.

    Args:
        cfg:     Full course config dict.
        preview: Print questions to stdout after generation.
        model:   Anthropic model to use.
    """
    print("\n[AI Generation] Generating quiz questions from chapter content")

    source_dir = cfg["source"]["directory"]
    chapters   = cfg["chapters"]
    quizzes    = cfg["quizzes"]
    generated  = {}
    ok = 0

    for quiz in quizzes:
        title = quiz["title"]
        print(f"\n  {title}")

        chapter_paths = _chapters_for_quiz(quiz, chapters, source_dir)
        if not chapter_paths:
            print(f"    ✗ No chapter files mapped to module '{quiz['module']}'")
            print(f"       → Using hardcoded fallback")
            continue

        print(f"    Reading {len(chapter_paths)} chapter(s)...")
        content = _read_content(chapter_paths)
        print(f"    {len(content):,} chars — calling {model}...")

        questions = _generate(title, content, model=model)
        if questions is None:
            print(f"    → Using hardcoded fallback")
            continue

        generated[title] = questions
        ok += 1
        print(f"    ✓ {len(questions)} questions generated")

        if preview:
            for i, q in enumerate(questions, 1):
                qtype = "MC" if q["type"] == "mc" else "T/F"
                print(f"\n      Q{i} ({qtype}): {q['text'][:90]}{'...' if len(q['text']) > 90 else ''}")
                if q["type"] == "mc":
                    print(f"        ✓ {q['correct'][:70]}")
                    for w in q["wrong"]:
                        print(f"        ✗ {w[:70]}")
                else:
                    print(f"        ✓ {q['correct']}")

    print(f"\n  Generated: {ok}/{len(quizzes)} quizzes")
    if ok < len(quizzes):
        skipped = len(quizzes) - ok
        print(f"  Fallback:  {skipped} quiz(zes) will use hardcoded QUESTION_BANK")
    return generated


# ─────────────────────────────────────────────────────────────────────────────
# Standalone preview mode
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    import yaml

    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "course_config.yaml")
    with open(config_path) as f:
        cfg = yaml.safe_load(f)

    results = run(cfg, preview=True)
    print(f"\nDone. {len(results)} quizzes generated.")
    print("Pass these to stage4_quizzes.run() via the generated_bank argument.")
