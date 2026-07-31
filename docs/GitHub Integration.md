---
tags: [CS401R, git, github, setup]
created: 2026-07-31
purpose: Repo fingerprint and commit workflow for the CS 401R course project
---

# GitHub Integration — CS 401R 2026

Read this before running any `git` command in this project. It mirrors the EAIE setup pattern.

## The three repositories

| Repo | Visibility | Contents | Where it lives |
|---|---|---|---|
| `scott2borg/cs401r-2026-instructor` | **PRIVATE** | Everything: lab specs, sample solutions, TA grading guides, TA tools, slide sources, syllabus | Working tree `CS_401R_2026/`, git dir `~/.git-repos/CS_401R` |
| `scott2borg/cs401r-2026-labs` | **PUBLIC** | Student-facing only: lab specs + starter kits | Clone at `~/Repos/cs401r-2026-labs` |
| `scott2borg/northstar-ai-platform` | **PRIVATE** | Reference implementation (the working AWS platform) | `~/northstar-ai-platform` |

## Repo fingerprint — verify before every git command

```bash
cd /Users/scott1/Documents/Vault/Efforts/Projects/Active/CS_401R_2026
git rev-parse --show-toplevel    # → .../CS_401R_2026
git rev-parse --git-dir          # → /Users/scott1/.git-repos/CS_401R
git remote -v                    # → git@github.com:scott2borg/cs401r-2026-instructor.git
```

If any of those return something else, **stop**. Do not guess.

### Why `--separate-git-dir`

The vault is on iCloud. iCloud sync corrupts git internals — it will happily sync a half-written packfile. The git directory therefore lives outside iCloud at `~/.git-repos/CS_401R`, and `CS_401R_2026/.git` is a one-line pointer file, not a directory:

```
gitdir: /Users/scott1/.git-repos/CS_401R
```

**If `.git` is ever a directory here, someone ran `git init` in the wrong place.** That creates a rogue repo shadowing the real one. Delete the stray `.git` directory and re-point.

### The EAIE overlap — important

`CS_401R_2026/` sits *inside* the EAIE repo's working tree (`Efforts/Projects/Active/`). It is excluded by a `CS_401R_2026/` rule in that repo's `.gitignore`, added 2026-07-31.

**Never remove that rule.** Without it, a `git add -A` run from `Active/` sweeps 156 MB of course material — including every answer key — into the public-facing book repo's history.

## Committing to the instructor repo

Conventional Commits, scope `cs401r`:

```
content(cs401r): <what changed>     # lab specs, solutions, course material
build(cs401r):   <what changed>     # scripts, tooling
chore(cs401r):   <what changed>     # gitignore, config, housekeeping
docs(cs401r):    <what changed>     # notes, handoffs, this file
```

```bash
cd /Users/scott1/Documents/Vault/Efforts/Projects/Active/CS_401R_2026
git add <specific paths>
git commit -m "content(cs401r): ..."
git push origin main
```

Push immediately. Do not let local commits accumulate — the vault is on iCloud and the GitHub remote is the only durable backup.

## Publishing to the public student repo

**Never push to the public repo by hand.** Use the allowlist script:

```bash
bash scripts/publish_student_repo.sh --dry-run   # show exactly what would ship
bash scripts/publish_student_repo.sh             # sync + confirm + commit
bash scripts/publish_student_repo.sh --push      # ...and push
```

### Why an allowlist rather than a gitignore

A denylist fails **open**: add a folder, forget to ignore it, and the answer keys ship. An allowlist fails **closed**: anything not named explicitly in `ALLOW` is never copied, so a new folder cannot leak without someone editing the script.

There is no shared git history between the two repos. The public repo is rebuilt from a clean staging directory each run and synced with `rsync --delete`, so removing a path from `ALLOW` removes it from the public repo on the next publish.

Three independent layers:
1. **`ALLOW`** — only these paths are copied.
2. **`DENY_PATTERNS`** — applied *inside* copied directories, catching e.g. a solution file dropped into `Starter Kits/`.
3. **Leak check** — greps staged content for instructor-only phrasing and secret material; aborts the publish on any hit.

Verified 2026-07-31: adding a solution file to `ALLOW` was caught and purged by layer 2.

### Adding to the allowlist

Open the file, confirm it contains no solutions, and add its path to `ALLOW`. Re-run with `--dry-run` and read the file list before publishing.

## The reference implementation

`~/northstar-ai-platform` is a **separate repo with its own remote.** It is authoritative.

The old copy at `CS_401R_Labs/Sample Solutions/northstar-ai-platform/` is **retired and gitignored.** It had silently drifted: different `.gitignore`, missing `Dockerfile.terraform`, `Requirements.txt` vs `requirements.txt`. Do not recreate it. To browse the reference implementation, open the real repo.

## Known failure modes

| Symptom | Cause | Fix |
|---|---|---|
| `.git` is a directory, not a file | `git init` run inside `CS_401R_2026/` | Remove the stray `.git` dir; the real one is `~/.git-repos/CS_401R` |
| Course files appear in EAIE's `git status` | `CS_401R_2026/` rule removed from the EAIE `.gitignore` | Restore the rule; check nothing was committed |
| Publish script exits silently after "Leak check" | A `grep` returning 1 under `set -o pipefail` | Already fixed with `|| true`; if reintroduced, look for unguarded pipelines |
| `~$*.pptx` lock files published | Denylist pattern written in double quotes | Must be single-quoted `'~$*'` — double quotes expand `$*` |
| Push rejected, unrelated histories | Remote initialized with a README | `git push -u origin main --force` on the very first push only, after confirming the remote is empty |

## Setup provenance

Established 2026-07-31. Baseline: 156 MB on disk → 132 tracked files, 9.2 MB, after excluding `Presentations/` binaries (~81 MB, regenerable from `generate_presentations.py`; the 52 slide-source `.md` files *are* tracked) and the drifted reference-implementation copy.

Secret scan before first commit: no AWS access keys, no private keys, no API tokens. The one grep hit in `Fix Credentials Problem.md` is a commented placeholder.
