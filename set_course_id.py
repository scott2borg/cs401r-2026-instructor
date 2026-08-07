#!/usr/bin/env python3
"""Point course_config.yaml at a different Canvas course.

Canvas "Reset Course Content" DELETES the course and creates a new equivalent
one with a NEW ID. Every script here reads the id from course_config.yaml, so
that id has to be updated once after a reset or everything silently targets the
dead course.

    python set_course_id.py 34987
"""
import pathlib, re, sys

if len(sys.argv) != 2 or not sys.argv[1].isdigit():
    sys.exit("Usage: python set_course_id.py <new_course_id>")
new = sys.argv[1]
p = pathlib.Path(__file__).parent / "course_config.yaml"
s = p.read_text()
m = re.search(r'(\n\s*course_id:\s*")(\d+)(")', s)
if not m:
    sys.exit("Could not find canvas.course_id in course_config.yaml")
old = m.group(2)
if old == new:
    print(f"Already set to {new}; nothing to do.")
    sys.exit(0)
p.write_text(s[:m.start(2)] + new + s[m.end(2):])
print(f"course_id: {old} -> {new}")
print("Verify:  grep -A2 '^canvas:' course_config.yaml")
