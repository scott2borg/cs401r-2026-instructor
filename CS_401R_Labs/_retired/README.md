---
created: 2026-08-02
tags: [CS401R, retired, housekeeping]
purpose: Explain what is in this folder and why it is kept rather than deleted
---

# `_retired/` — what these files are

Neither file here is dead weight, and neither has a copy anywhere else. They are
kept deliberately. This note exists so the folder stops being an open question on
the handoff list.

## `generate_northstar_data.py`

The **original, larger course dataset design** — not a superseded version of
anything currently in use. It generates five datasets:

| Output | Scale |
|---|---|
| `customers.csv` | 250,000 records |
| `transactions.parquet` | ~4.2M rows, 18 months |
| `clickstream.parquet` | ~8.1M events, 90 days |
| `store_events.csv` | ~14,400 events, 400 stores |
| `product_catalog.json` | 12,000 SKUs |

**Why it is retired.** The course shipped a far smaller transaction-level sample
instead — 19,692 rows over 1,377 customers — because the labs must complete
inside AWS default service quotas on standalone student accounts, and a 4.2M-row
Glue job does not. See `CLAUDE.md` at the project root for the quota constraint
that forced this.

**Why it is kept.** It is the only record of the full-scale design. If the course
ever gets a shared or sponsored account, this is the starting point, not a
rewrite. It also documents the statistical properties the small sample was built
to imitate.

**Do not confuse it with** `data/generate_raw_sample.py` in the live repo, which
is what actually produces `northstar-raw-sample.csv`. Different scope, different
output, both current in their own way.

## `glue_job_skeleton.py`

An early single-file Glue job template from before the ETL split into two jobs.
Superseded by `data/glue-scripts/transform.py` (transaction-level in, transaction-
level out) and `data/glue-scripts/feature_engineer.py` (collapses to one row per
customer). Kept only as a reference for how the split came about — the grain
distinction between those two jobs is the single most damaging thing students get
wrong in Lab 2, and this file is where that lesson originated.

## Status

Retired, not deleted, and not scheduled for deletion. Both files are tracked in
git, so history would preserve them anyway; keeping them in the tree with this
note is cheaper than rediscovering why they vanished.
