# Legacy reference artifacts

**Rescued 2026-08-07. Nothing here is authoritative. Do not build on it.**

## What this is

These files were the only surviving copies of material that lived in the
retired tree at `Sample Solutions/northstar-ai-platform/`. That tree was a
drifted duplicate of the real reference implementation, was gitignored, and
`docs/GitHub Integration.md` says plainly: *"retired and gitignored — do not
recreate it."*

The tree has now been deleted. Everything in it that also exists in the live
repo went with it. Everything that existed **nowhere else** was moved here
first, which is this folder.

## Why it was kept

These 20 files were in no git history — not in `cs401r-2026-instructor`, not
in `northstar-ai-platform`. Deleting the retired tree would have destroyed
them permanently. They are preserved here pending a decision on each, not
because they are known to be worth keeping.

## Where the real thing lives

**`~/northstar-ai-platform`** — a separate private repo with its own remote.
It is the single authoritative copy of the reference implementation. To browse
it, open that repo. Do not copy it back into the vault.

## Contents

> **The four worked deliverables have been promoted out of here (2026-08-07).**
> They now live in `Lab Solution Notes/` as `Lab N - … (Sample Deliverable).md`,
> with frontmatter and a header distinguishing them from the TA grading guides.
> `docs/` is gone. Only superseded *code* remains below.

| Path | What it appears to be |
|---|---|
| `models/churn/` | Superseded training code (live repo restructured this) |
| `models/agent/`, `models/offers/` | Track B/C Bedrock agent and RAG code |
| `pipeline/` | Superseded pipeline + tests (tests now live at `tests/`) |
| `monitoring/custom_metrics.py` | Superseded by `monitoring/publish_metrics.py` |
| `monitoring/alerts/alerts.tf` | Superseded by `monitoring/alerts/alarms.tf` |
| `deployment/security/kms_config.tf` | KMS config not present in the live repo |
| `_retired-old-lab2-architecture/` | Was already marked retired inside the retired tree |

The worked deliverables were the part worth keeping, and they have been moved.
What is left is superseded code. It is probably safe to drop once someone
confirms the live repo covers it — nothing here is referenced by any lab.

## Provenance

The `monitoring/custom_metrics.py` here is the ancestor of the current
`publish_metrics.py`. It predates the 2026-08-07 move from SageMaker Model
Monitor to Evidently and parses `constraint_violations.json`, which nothing
produces any more. Kept for history only.
