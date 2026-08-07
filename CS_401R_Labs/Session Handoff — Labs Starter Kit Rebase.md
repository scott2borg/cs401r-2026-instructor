---
created: 2026-08-03
tags: [CS401R, handoff, starter-kits, gates, dataset, defects]
supersedes: "Session Handoff — Dataset Rebase & Gate Redesign"
purpose: The gate redesign was validated against the reference implementation only. The artifact students actually run had never inherited it — including the ORDER BY fix the previous session existed to make.
---

# Session Handoff — Starter Kit Rebase

> **Read this before the next session.** It supersedes [[Session Handoff — Dataset Rebase & Gate Redesign]] on the starter kits, Lab 6 cost figures, defects 44–48, and open threads 3, 7 and 8. Everything that note says about the canonical metrics, the gate design, the dataset rebase  **still stands and was re-confirmed on AWS today**.
>
> **The headline: the previous session fixed `train_reference.py` and never checked the file students actually run.** The shipped Lab 3 skeleton failed the promotion gate on **28% of splits**, its Athena query was still missing the `ORDER BY` that the entire previous session was about, and the Lab 2 starter kit still shipped the retired 1,200-customer dataset.

---

## The one-line summary

The gate redesign was correct. Its propagation was not. Six defects (49–54), all in
artifacts students receive, all now fixed and verified on AWS.

---

## Canonical figures — unchanged, and re-confirmed today

Every figure in the previous handoff reproduced **byte-identically** on a fresh
43-resource stack built and destroyed on 2026-08-03 — new VPC, new bucket, new
Glue run, new Feature Store, different day, different operator path.

| Metric | Value |
|---|---|
| AUC-ROC | **0.7696** *(reported, not gated)* |
| Recency-only baseline AUC | **0.7233** |
| AUC lift over baseline | **+0.0464** |
| Lift 95% CI | **[0.0254, 0.0670]** — excludes zero, gate PASSES |
| Precision@10% | **0.6833** |
| Recall@10% | **0.3106** |
| `scale_pos_weight` | 3.545 |
| Slices | Platinum 307/**0.8483**, Gold 483/0.7559, Bronze 1071/0.7442, Silver 1139/**0.6935** |

That is now the **fourth** independent reproduction. Treat determinism as settled.

---

## Defects 49–54

| # | Defect | Status |
|---|---|---|
| 49 | **The shipped Lab 3 skeleton failed the promotion gate on 28% of splits.** `eval_metric` was `["auc", "logloss"]`; XGBoost early-stops on the **last** metric, so the criterion was silently logloss. Under `scale_pos_weight` the reweighted logloss keeps improving past peak ranking quality, so `early_stopping_rounds=20` never fired — 199 of 200 rounds, val AUC 0.7603 instead of 0.7822. A student doing everything right was told their features did not beat recency | **Fixed.** Reordered to `["logloss", "auc"]`, which keeps logloss in the training log while making AUC the stopping criterion. 50-split sweep: **72% → 100%** gate pass rate |
| 50 | **`pytest_addoption` sat in a test module.** Pytest only collects it from `conftest.py` or a plugin, so the command printed in `test_model.py`'s own docstring died with `unrecognized arguments: --model-path` before collecting a single test. Same class as defect 46 | **Fixed.** Added `tests/conftest.py`; also registers `--eval-metrics-path` |
| 51 | **`test_data.py` asserted `5_000 < rows < 60_000`**, a bound derived from the retired 1,200-customer sample. The correct 10k dataset has 163,255 raw rows and **failed the test** | **Fixed.** Now asserts transactions-per-customer in [5, 40], which survives any regeneration at a different `--customers` |
| 52 | **The Lab 2 starter kit still shipped the 1,200-customer dataset.** 19,692 rows / 1,376 customers, while Lab 2's own prose described "~163,000 rows across ~11,400 customers". Students would have run the entire course on the dataset the rebase explicitly retired — where the lift CI excludes zero on only **30%** of splits | **Fixed.** Replaced with the 163,255-row / 11,434-customer sample. Verified the deliberate defects survive: 3,265 null `customer_id`, 2,412 duplicate `transaction_id`, 4,912 slashed dates |
| 53 | **The verified "43 resources" reference run was not reproducible from the repo.** `enable_sagemaker_domain` defaults to **true** and nothing set it false; the three verified runs used an undocumented CLI `-var`. `terraform.tfvars` is gitignored, so the reproducible path was unreproducible. A plain `terraform apply` gives 45 resources, ~10 extra minutes each way, and leftover EFS/NFS security groups | **Fixed.** Pinned `enable_sagemaker_domain = false` in `terraform.tfvars.example` with the rationale |
| 54 | **The skeleton's Athena query had no `ORDER BY customer_id`.** Defect 45 — the whole reason the previous session existed — was fixed in `train_reference.py` and left in the student template. Every student would have reproduced the original irreproducibility | **Fixed** and verified against a live offline store: two consecutive queries through the completed student path returned identical metrics |

---

## The 50-split sweep — why defect 49 is a measurement, not an opinion

10,000-customer dataset, bootstrap n=1000, gates as shipped.

| Configuration | AUC mean | sd | mean lift | CI excludes 0 | all gates |
|---|---|---|---|---|---|
| **A — skeleton as shipped** | 0.7627 | 0.0078 | +0.0304 | **72%** | **72%** |
| B — A but `eval_metric` fixed | 0.7813 | 0.0086 | +0.0490 | 100% | 100% |
| C — B plus `test_size=0.30` | 0.7794 | 0.0077 | +0.0488 | 100% | 100% |
| D — C plus computed `spw`, baseline `colsample 0.9` | 0.7798 | 0.0077 | +0.0493 | 100% | 100% |
| E — `train_reference.py` | 0.7697 | 0.0076 | +0.0391 | 100% | 100% |

**Config D was adopted.** The `eval_metric` fix alone is what rescues the gate; the
other three alignments exist so the skeleton's split and baseline match every
published figure.

### On "the skeleton reproduces `train_reference.py` exactly"

Defect 47 claimed this. **It was never true and it was never the right goal.** The
skeleton deliberately ships depth-6 hyperparameters as a student starting point;
the reference uses depth 4. What now matches exactly is the **split** (3,000 test
rows), the **baseline** (0.7233, identical), and the **gates**. The correct claim
is: *the skeleton and the reference are judged by the same gate on the same split,
and the skeleton passes it on 100% of splits.* State it that way.

---

## Lab 6 cost figures, re-derived at 10k (closes old thread 8)

The old figures were built on a 5 min 46 s baseline job at 1,200 customers. At
10,000 the jobs are longer, so **a forgotten endpoint breaches the budget sooner**.

The cost model was reverse-engineered and **validated against the shipped table
to within a cent on every cell** before being applied to the new measurements:
`cost(t) = $0.30 non-prorated custom metric + one baseline job + (endpoint + one
analysis run per hour) × t`.

| | Was (1,200) | Now (10,000) |
|---|---|---|
| Baseline job | 5 m 46 s, $0.010 | **9 m 44 s, $0.016** |
| Analysis run | ~6 min, $0.010 | **8 m 44 s, $0.015** |
| Burn `ml.t2.medium` | $0.0664/hr | **$0.0706/hr** |
| Burn `ml.m5.large` | $0.1254/hr | **$0.1296/hr** |
| $10 breached, `t2.medium` | 146 h (6.1 d) | **137 h (5.7 d)** |
| $10 breached, `m5.large` | 77 h (3.2 d) | **75 h (3.1 d)** |
| Monitoring as % of endpoint cost | ~15% | **~25%** |

Scenario table now reads $0.53 / $1.30 / $5.40 / $12.17 on `t2.medium` and
$0.70 / $2.13 / $9.64 / $22.08 on `m5.large` at 3 / 14 / 72 / 168 hours.

---

## Measured on AWS 2026-08-03 — account `711457211658`, us-east-1

| Stage | This run | Previous handoff |
|---|---|---|
| `terraform apply` | 43 added, **2 m 37 s** | 43 added, 2 m 16 s |
| Crawler | SUCCEEDED, table `customers`, 9 cols | SUCCEEDED |
| Glue transform | 157,627 rows, **107 s / 214 DPU-s** | 121 s / 242 DPU-s |
| Glue feature-engineer | 9,999 rows, **93 s / 186 DPU-s** | 94 s / 188 DPU-s |
| Offline store hydration | **3 m 8 s** | 3 m 53 s / 4 m 14 s |
| `terraform destroy` | 43 destroyed, **1 m 25 s** | 1 m 14 s |
| All-region sweep, 8 regions | all zero | all zero |

Storage after the run was **byte-identical** to the previous handoff: `raw/`
13,582,469 B, `processed/` 3,856,995 B, `features/` 317,006 B.

> **Note for Lab 7 Task 2.** This run measured **214 + 186 = 400 DPU-s** against the
> published **242 + 188 = 430**. Both are real single-pass measurements; Glue DPU-s
> varies ~7% run to run. The published 0.1194 DPU-hr figure is sound, but the
> accept band should absorb this variance rather than treat 430 as exact.

### Test results against real infrastructure

- **18/18** `test_model.py` against real skeleton output
- **44/44** `test_data.py` + `test_features.py` against real Glue Parquet
- **62 total**, zero failures. Previously these had *never* been run against real output.

---

## Open threads

1. **Lab 4 CodePipeline — still never run. This is now the largest genuinely unexecuted path in the course, and it is no longer blocked.** The CodeStar connection `northstar-github` was authorized on 2026-08-03 and verified `AVAILABLE`; it stays that way permanently. What remains is deploying `pipeline.yaml` and running the pipeline end to end. **Bundle this with the next AWS session so the NAT is paid once** — ideally the same session that re-runs Lab 5/6 (thread 2).
2. **Lab 5 and Lab 6 were not re-run today.** Deliberate: both were verified three times on 2026-08-02 and re-running them would have burned NAT and endpoint time to re-confirm settled results. The Lab 6 *cost* figures above are re-derived arithmetic from those measurements, **not** a fresh Lab 6 execution.
3. **Canvas re-upload.** Still needs `CANVAS_API_TOKEN` and `CANVAS_COURSE_ID`. Quizzes pushed before 2026-08-01 carry old text and old metrics.
4. **Bedrock quotas still 0.** Blocks Lab 3 Track B/C only. Unchanged. Still unknown whether all 30 student accounts need individual grants; assume yes.
5. **A7's anomaly alarm cannot be demonstrated** in a lab session. Defined and correct, just not showable.
6. **The skeleton's commented Feature Store solution references an undefined `bucket`.** `load_features_from_feature_store(feature_group_name, start_date, end_date)` has no bucket in scope, but the commented `query.run(...)` line interpolates one. A student pasting it gets `NameError`. Minor, but it is the third instance of "the commented-out answer does not run." Not yet fixed.
7. **The skeleton's query does not select `loyalty_tier`**, so a student following the template cannot do the Task 1 slice evaluation without noticing and adding it. This may be deliberate; decide and either document it as part of the exercise or add the column.
8. **`sagemaker` SDK is not installed locally**, so the skeleton's `FeatureGroup.athena_query()` path was verified via an equivalent boto3 implementation of the same SQL, not via the SDK call itself. The SQL, the dedup, and the `ORDER BY` are verified; the SDK wrapper is not.
9. Vault copy of `northstar-ai-platform` under `Sample Solutions/` is known-stale and gitignored. Unchanged.

---

## State of the account

**Clean.** 43 applied, 43 destroyed. Independent 8-region sweep returns zero
endpoints, feature groups, NAT gateways, Glue jobs, and in-progress processing
jobs. Only `northstar-tfstate-711457211658` survives, which is correct.

**Model Registry unchanged at v1–v5, all `Rejected`.** Today's run used
`--skip-register` deliberately: the stack was torn down immediately, so
registering would only have added a sixth entry with a dead `ModelDataUrl`.

**Cost:** one NAT-bearing session of roughly 75 minutes, plus two Glue job pairs
and Athena scans. Cost Explorer lags ~24 h, and there are now four NAT-bearing
sessions across 2026-08-02/03 — **check before assuming the $10 budget is safe.**

---

## Where this was propagated

- `Starter Kits/Lab 3/churn_training_skeleton.py` — `eval_metric` order, `ORDER BY`, `test_size` 0.30, computed `scale_pos_weight`, baseline `colsample` 0.9, stale "0.03 lift" text, duplicate `BASELINE_FEATURE`
- `Starter Kits/Lab 4/tests/conftest.py` — **new**
- `Starter Kits/Lab 4/tests/test_model.py` — hook removed, "12 features" corrected to 11
- `Starter Kits/Lab 4/tests/test_data.py` — row-count bound made size-relative
- `Starter Kits/Lab 2/northstar-raw-sample.csv` — **replaced with the 10k sample**
- `Lab_6--Monitoring & Reliability.md` and master — all cost figures
- `CS_401R_2026/CLAUDE.md` — Lab 6 burn rate line
- Live repo: `docs/lab3-metric-stability.md`, `infrastructure/environments/dev/terraform.tfvars.example`, `models/churn/analysis/` (**new** — three reproducible scripts)

**Live repo: merged to `main` and pushed.** `origin/main` moved `91b09b3 → b2c62d2`.
The vault is not version-controlled, so those edits are live on disk.

---

## Git state — read this before starting work

**`main` is now the truth, for the first time in three sessions.**

Until 2026-08-03, all of this work lived on a branch called
`lab5-deployment-verification`, and **`main` was 20 commits stale**. Everything
from the Lab 5/6 verification, defects 39–54, the entire dataset rebase, and gate
redesign existed only on that branch. Anything reading the default branch — a
fresh clone, CI, a student pointed at `main`, a future agent session — was
getting the pre-Lab-5 course and would have had no way to know.

That branch has been fast-forwarded into `main` (no merge commit, all 20 commits
individually intact) and **deleted, locally and on origin**. Only `main` remains.

**Rules going forward:**

- **Branch fresh from `main`** for each new piece of work. Do not resurrect a
  long-running branch and do not accumulate multiple sessions on one branch.
- **Name the branch for the work**, not for the lab that happened to start it.
  `lab5-deployment-verification` ended up carrying the dataset rebase and the
  starter-kit fixes, which is how it went unnoticed.
- **Merge to `main` at the end of every session**, not when a theme feels
  finished. The staleness above was three sessions deep before anyone looked.
- If a session ends mid-work, that is fine — but say so explicitly in the
  handoff, including the branch name and what is unmerged.

---

## Notes for next session

- **The lesson of this session is narrower and sharper than the last one's.** The previous session fixed the reference implementation and propagated numbers into prose. It did not re-verify the executable artifacts students receive. Every one of defects 49–54 lives in a file a student runs, and none would have been caught by re-reading documentation. **When a gate changes, re-run the sweep against the starter kit, not just the answer key.**
- Config sweeps are rerun offline from `data/lab3-reference-dataset.csv` via `models/churn/analysis/skeleton_config_sweep.py`. No AWS needed.
- `train_reference.py` still writes `docs/lab3-evaluation-metrics.json`, and it is still gitignored on purpose. Cite `docs/lab3-metric-stability.md`.
- `enable_sagemaker_domain = false` is pinned in `terraform.tfvars.example` **and** was added to the local gitignored `terraform.tfvars` on 2026-08-03 (verified). A bare `terraform apply` on this machine now gives the reference 43 resources. On any *other* machine, the local tfvars must be recreated from the example, or the Domain comes back.
- The en-US normalization is done: zero en-GB spellings across master and standalones, and the master's AWS error quote now matches the live error ("1 Instance"). Two paragraphs still differ, both deliberate blockquote wrapping.
