#!/usr/bin/env bash
#
# publish_student_repo.sh
#
# Publishes student-facing course material to the PUBLIC repo
# (scott2borg/cs401r-2026-labs) from this PRIVATE instructor repo.
#
# ── WHY THIS IS AN ALLOWLIST ──────────────────────────────────────────────────
#
# This repo contains answer keys (Sample Solutions/), TA grading guides
# (Lab Solution Notes/), and TA tooling. The public repo must never receive
# them.
#
# A denylist (".gitignore the solutions") fails open: add a folder, forget to
# ignore it, and the answers ship. An allowlist fails closed: anything not
# named explicitly below is simply never copied. A new folder appearing in
# this repo cannot leak, because this script would have to be edited to
# include it.
#
# There is no shared git history between the two repos. The public repo is
# built from a clean staging directory every run, so a file removed from the
# allowlist disappears from the public repo on the next publish instead of
# lingering in history.
#
# Usage:
#   bash scripts/publish_student_repo.sh --dry-run    # show what would ship
#   bash scripts/publish_student_repo.sh              # stage + diff + confirm
#   bash scripts/publish_student_repo.sh --push       # ...and push

set -euo pipefail

INSTRUCTOR_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PUBLIC_REPO="${PUBLIC_REPO:-$HOME/Repos/cs401r-2026-labs}"
STAGING="${INSTRUCTOR_ROOT}/.publish-staging"

DRY_RUN=0; DO_PUSH=0
for a in "$@"; do
  case "$a" in
    --dry-run) DRY_RUN=1 ;;
    --push)    DO_PUSH=1 ;;
    *) echo "unknown flag: $a" >&2; exit 2 ;;
  esac
done

green() { printf "\033[32m%s\033[0m\n" "$1"; }
red ()  { printf "\033[31m%s\033[0m\n" "$1"; }
bold()  { printf "\033[1m%s\033[0m\n" "$1"; }

# ── THE ALLOWLIST ─────────────────────────────────────────────────────────────
# Paths are relative to the instructor repo root. Directories copy recursively.
# ADD NOTHING HERE WITHOUT CHECKING IT CONTAINS NO SOLUTIONS.
ALLOW=(
  "CS_401R_Labs/CS 401R Labs.md"
  "CS_401R_Labs/Lab_1--Platform Foundation.md"
  "CS_401R_Labs/Lab_2--Data & Feature Engineering.md"
  "CS_401R_Labs/Lab_3--Model Development.md"
  "CS_401R_Labs/Lab_4--XOps & CICD.md"
  "CS_401R_Labs/Lab_5--Deployment & Security.md"
  "CS_401R_Labs/Lab_6--Monitoring & Reliability.md"
  "CS_401R_Labs/Lab_1 Architecture_Diagram_Description.md"
  "CS_401R_Labs/Lab_1 LocalStack_Check.md"
  "CS_401R_Labs/Fix Credentials Problem.md"
  "CS_401R_Labs/Pre-Lab 3 — Bedrock Access Setup.md"
  "CS_401R_Labs/Starter Kits"
)

# ── THE DENYLIST (belt and braces) ────────────────────────────────────────────
# Even inside allowlisted directories, these patterns are never published.
# This exists because Starter Kits/ is copied recursively and a solution file
# dropped in there by accident must not ship.
DENY_PATTERNS=(
  "*Solution*" "*solution*" "*ANSWER*" "*answer_key*"
  "*TA Tools*" "*TA Procedure*" "*Grading*" "*Rubric_internal*"
  "*Session Handoff*" "*Cost Model*" "*Blockers*"
  ".DS_Store" "*.pyc" "__pycache__" ".env" "*.tfstate*" "*.tfvars"
  '~$*'          # Office lock/temp files — SINGLE quotes: "~$*" would
  '.~lock*'      # expand \$* to the script's positional parameters
)

bold "CS 401R — publish to public student repo"
echo "  source : ${INSTRUCTOR_ROOT}"
echo "  target : ${PUBLIC_REPO}"
echo

# ── Build staging from the allowlist ──────────────────────────────────────────
rm -rf "${STAGING}"; mkdir -p "${STAGING}"

MISSING=0
for item in "${ALLOW[@]}"; do
  src="${INSTRUCTOR_ROOT}/${item}"
  if [ ! -e "${src}" ]; then
    red "  MISSING from allowlist: ${item}"; MISSING=$((MISSING+1)); continue
  fi
  dest="${STAGING}/${item}"
  mkdir -p "$(dirname "${dest}")"
  if [ -d "${src}" ]; then cp -R "${src}" "$(dirname "${dest}")/"
  else cp "${src}" "${dest}"; fi
done
if [ "${MISSING}" -gt 0 ]; then
  red "  ${MISSING} allowlisted path(s) missing — fix before publishing."
fi

# ── Apply the denylist ────────────────────────────────────────────────────────
PURGED=0
for pat in "${DENY_PATTERNS[@]}"; do
  while IFS= read -r -d '' hit; do
    rm -rf "${hit}"; red "  purged by denylist: ${hit#${STAGING}/}"; PURGED=$((PURGED+1))
  done < <(find "${STAGING}" -name "${pat}" -print0 2>/dev/null)
done

# ── Leak check: scan staged content for solution/secret markers ───────────────
bold "Leak check"
LEAKS=0
# Terms that indicate INSTRUCTOR-ONLY material. Deliberately excludes rubric
# vocabulary ("pass criteria", "points", "rubric") — students are supposed to
# see the rubric, and a check that fires on every lab spec is a check everyone
# learns to ignore.
while IFS= read -r -d '' f; do
  if grep -qiE "answer key|model answer|reference solution|grading guide|do not distribute|instructor only|TA note" "$f" 2>/dev/null; then
    red "  SUSPECT (instructor-only language): ${f#${STAGING}/}"
    grep -inE "answer key|model answer|reference solution|grading guide|do not distribute|instructor only|TA note" "$f" | head -2 | sed 's/^/        /'
    LEAKS=$((LEAKS+1))
  fi
done < <(find "${STAGING}" -type f -name "*.md" -print0)

while IFS= read -r -d '' f; do
  if grep -qE "AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY|sk-[A-Za-z0-9]{32,}|ghp_[A-Za-z0-9]{36}" "$f" 2>/dev/null; then
    red "  SECRET MATERIAL: ${f#${STAGING}/}"; LEAKS=$((LEAKS+1))
  fi
done < <(find "${STAGING}" -type f -print0)

# The instructor AWS account id is not a secret, but it should not be
# advertised in a public repo. Warn rather than block.
# `|| true` is required: grep exits 1 when it finds nothing, and under
# `set -o pipefail` that failure propagates through the pipe and `set -e`
# kills the script silently — the no-leaks case would abort the publish.
ACCT_HITS=$(grep -rl "711457211658" "${STAGING}" 2>/dev/null | wc -l | tr -d ' ' || true)
if [ "${ACCT_HITS}" -gt 0 ]; then
  printf "\033[33m  WARN\033[0m  instructor AWS account id appears in %s file(s)\n" "${ACCT_HITS}"
fi

if [ "${LEAKS}" -gt 0 ]; then
  red "ABORTED — ${LEAKS} leak-check failure(s). Nothing was published."
  exit 1
fi
green "  no solution or secret markers found"

FILES=$(find "${STAGING}" -type f | wc -l | tr -d ' ')
SIZE=$(du -sh "${STAGING}" | cut -f1)
echo
bold "Staged: ${FILES} files, ${SIZE} (${PURGED} purged by denylist)"

if [ "${DRY_RUN}" -eq 1 ]; then
  find "${STAGING}" -type f | sed "s|${STAGING}/|  |" | sort
  echo; green "Dry run complete — nothing copied to the public repo."
  rm -rf "${STAGING}"; exit 0
fi

# ── Sync into the public repo ─────────────────────────────────────────────────
if [ ! -d "${PUBLIC_REPO}/.git" ]; then
  red "Public repo not found at ${PUBLIC_REPO}"
  echo "  git clone git@github.com:scott2borg/cs401r-2026-labs.git ${PUBLIC_REPO}"
  echo "  (or set PUBLIC_REPO=/path/to/clone)"
  rm -rf "${STAGING}"; exit 1
fi

# --delete makes the public repo an exact mirror of the allowlist. A file
# dropped from ALLOW is removed from the public repo on the next publish.
rsync -a --delete --exclude ".git" --exclude "README.md" "${STAGING}/" "${PUBLIC_REPO}/"
rm -rf "${STAGING}"

cd "${PUBLIC_REPO}"
git add -A
if git diff --cached --quiet; then
  green "No changes — public repo already up to date."; exit 0
fi

bold "Changes to publish:"
git diff --cached --stat | tail -20
echo
read -r -p "Commit and $( [ "${DO_PUSH}" -eq 1 ] && echo "PUSH" || echo "stage" ) these changes? [y/N] " ans
[ "${ans}" = "y" ] || { red "Aborted. Changes remain staged in ${PUBLIC_REPO}."; exit 1; }

git commit -q -m "content(labs): publish student-facing material $(date +%Y-%m-%d)

Generated by scripts/publish_student_repo.sh from the private instructor
repo. Allowlist-based: only explicitly listed paths are copied."
green "Committed."

if [ "${DO_PUSH}" -eq 1 ]; then
  git push origin main && green "Pushed to origin/main."
else
  echo "Run 'git -C ${PUBLIC_REPO} push origin main' when ready, or re-run with --push."
fi
