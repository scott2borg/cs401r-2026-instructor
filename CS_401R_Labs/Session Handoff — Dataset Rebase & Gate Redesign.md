---
created: 2026-08-03
tags: [CS401R, handoff, metrics, gates, dataset]
supersedes: "Session Handoff — Labs 2-5 End-to-End Run"
purpose: The reference metrics were never reproducible. Root cause found and fixed, dataset rebased to 10k, promotion gates redesigned, everything re-verified on AWS.
---

# Session Handoff — Dataset Rebase & Gate Redesign

> **Read this before the next session.** It supersedes [[Session Handoff — Labs 2-5 End-to-End Run]] entirely on metrics, gates, dataset size and defects 39–48. That note's AWS-mechanics observations still stand.
>
> **The headline: the course's reference metrics were never reproducible, and the reason was one missing `ORDER BY`.** Fixing it exposed that a 360-row test set could not support any of the thresholds built on it. The dataset is now 10,000 customers, the absolute AUC gate is gone, and every number in Labs 2–7 has been re-measured on AWS.

---

## Canonical figures — use these, ignore everything older

`models/churn/train_reference.py`, Athena path, deterministic `ORDER BY customer_id`, 10,000-customer dataset, `seed=42`, `test_size=0.30`, 6,999 train / 3,000 test.

| Metric | Value |
|---|---|
| AUC-ROC | **0.7696** *(reported, not gated)* |
| Recency-only baseline AUC | **0.7233** |
| AUC lift over baseline | **+0.0464** |
| **Lift 95% CI** | **[0.0254, 0.0670]** — excludes zero, gate PASSES |
| Precision@10% | **0.6833** |
| Recall@10% | **0.3106** |
| Churn rate | **22.0%** |
| Recall@10% ceiling at 22% base rate | **~0.45** |
| `scale_pos_weight` | 3.545 |

**These reproduced byte-identically across a full teardown and rebuild** — fresh VPC, fresh bucket, fresh Glue run, fresh Feature Store, fresh offline store, on a different day. That is the determinism fix proven, not asserted.

Slice evaluation, 3,000-row test set:

| Tier | n | AUC | Churn |
|---|---|---|---|
| **Platinum** | 307 | **0.8483** | 6.8% |
| Gold | 483 | 0.7559 | 10.8% |
| Bronze | 1,071 | 0.7442 | 33.7% |
| **Silver** | 1,139 | **0.6935** | 19.8% |

---

## What changed conceptually — read this before touching Lab 3 or 4

**The absolute AUC gate is gone.** Measured across 200 splits of the same data, the reference model's AUC was mean 0.7120 sd 0.0291 on the old dataset and fell below the old ≥ 0.72 bar on **58% of splits**. The gate was grading the random seed. The old ≥ 0.03 lift threshold was worse — smaller than the metric's own standard deviation, failing on 21% of splits.

**The promotion gate is now an interval.** The 95% CI on (model AUC − recency-only baseline AUC), by paired bootstrap over the test set, must exclude zero. Fixed seed, so the same split always yields the same verdict. `precision_top10 ≥ 0.50` and `recall_top10 ≥ 0.25` survive unchanged; they were measured failing on 1.0% and 2.5% and are well calibrated.

**The dataset had to grow for that gate to work.** At 1,200 customers the lift CI excluded zero on only **30%** of splits — a 360-row test set genuinely cannot demonstrate the model beats recency. At 10,000 it is **100%**. AUC sd fell 0.0291 → 0.0078.

**Growing the dataset was free.** Both Glue jobs use *fewer* DPU-seconds at 8.3× the data, because Spark startup dominated at the old size. There is no cost argument against the larger dataset.

**The Platinum finding reversed.** The course taught "the model is worse than random on your most valuable segment, AUC 0.430" as a headline result. At 1,200 customers Platinum was ~33 test rows with ~2 churners; across 200 splits its AUC ranged 0.00–1.00 and came out worse-than-random on only 34.9%. At 307 rows Platinum is the model's **best** slice. Lab 3 now teaches the spread across tiers (villain: **Silver**, the largest tier) plus the sample-size lesson, and the rubric requires per-tier `n` and an explicit statement of which slices are too small to conclude from.

---

## Defects 44–48

| # | Defect | Status |
|---|---|---|
| 44 | **Evaluation metrics lived only inside the bucket teardown deletes.** The full blob, including slices, went to `s3://<data-bucket>/artifacts/evaluations/latest/` on a `force_destroy = true` bucket. The registry carried four scalars and no slice data | **Fixed.** `persist_metrics()` runs before registration and regardless of `--skip-register`, writing to the repo, the tfstate bucket, and the data bucket. Registry metadata went 4 → 16 pairs including `slice_worst_tier` / `slice_worst_auc` |
| 45 | **The reference metrics were never reproducible by construction.** No `ORDER BY` on the outer Athena `SELECT`; Athena returns rows in whatever order the parallel splits finish, and `train_test_split` is deterministic only for a given row order. Same data produced AUC 0.7276–0.7431 and Platinum 0.430–0.700 across runs | **Fixed** with `ORDER BY customer_id`. Verified byte-identical across three consecutive runs and again across a full rebuild |
| 46 | **`canary_deploy_realtime.py` failed for every student before its first AWS call.** `--sample-csv` defaulted to a cwd-relative `sample.csv` that nothing in the repo creates, while Lab 5 says to run from the repo root | **Fixed.** Default resolves against the script directory; a `sample.csv` ships beside it. Confirmed by a later deploy that passed no flag |
| 47 | **The starter kits taught the wrong comparison.** Lab 4's `test_model.py` required P@10 ≥ 0.40 / R@10 ≥ 0.35 while Lab 3 specified 0.50 / 0.25. The Lab 3 skeleton's "baseline" was `np.full_like(proba, y.mean())` — a constant predictor whose AUC is 0.5 by construction | **Fixed.** Gates aligned, AUC gate removed, and the skeleton now ships a real recency-only baseline plus the bootstrap CI. Verified: the skeleton reproduces `train_reference.py` exactly |
| 48 | **Batched invocation silently breaks Model Monitor.** More than one CSV row per request is captured as a single `endpointInput.data` string; the analyzer parses it as **1 column** and fails `missing_column_check`. Nothing in the error mentions batching | **Documented**, not fixable at the API level. Isolated against an identical baseline: 60 single-row records parsed at 12 columns, 211 batched records collapsed to 1 |

---

## Measured on AWS — every number below is observed

Three full runs on account `711457211658`, us-east-1, Studio Domain disabled.

| Stage | 10,000 customers | 1,200 customers |
|---|---|---|
| `terraform apply` | 43 added, 2 m 16 s | 2 m 16 s |
| Crawler | SUCCEEDED, 37.2 s, table `customers` | 54 s |
| Glue transform | 157,627 rows, **121 s / 242 DPU-s** | 139 s / 278 DPU-s |
| Glue feature-engineer | 9,999 rows, 0 nulls, **94 s / 188 DPU-s** | 106 s / 212 DPU-s |
| Feature Store ingest | 9,999 records, 0 failures | 1,200 |
| Offline store hydration | **3 m 53 s / 4 m 14 s** | 4 m 34 s |
| Endpoint `InService` | **423 s**, `ml.t2.medium`, 2 variants | 404 s |
| Invoke | 1,000-row batch in 1.4 s; singles p50 415 ms / p95 457 ms | p50 375 / p95 461 |
| Data capture | **32 s** behind invocation | ~4 min |
| Model Monitor baseline | **8 m 44 s** (11-col) / **9 m 44 s** (12-col), `ml.t3.large` | 5 m 46 s |
| Model Monitor analysis | **8 m 44 s** | — |
| `terraform destroy` | 43 destroyed, 1 m 14 s | — |
| All-region sweep, 8 regions | all zero | — |

Storage after a run: `raw/` 13,582,469 B (1 object), `processed/` 3,856,995 B (4), `features/` 317,006 B (2).

### Three Model Monitor traps, all verified

1. **The baseline must have the same column count as the capture.** `sagemakerCaptureJson` reads `endpointInput` **and** `endpointOutput`, so an 11-feature model captures **12** columns. Baseline on 11 and you get `extra_column_check`, which reads like a data problem and is a baseline problem.
2. **Batched invocation collapses to 1 column** (defect 48). Score one row per request for monitored traffic.
3. **A window under ~500 records manufactures drift.** 60 captured records against the 9,999-record baseline produced **8** `baseline_drift_check` violations at distances 0.215–0.762 against a 0.1 threshold — on data drawn from the baseline distribution. This is why the runbook says ≥ 500; it is now a measurement, not a round number.

---

## Lab 7 rebuilt

**Task 3 (the highest-value graded item), re-derived at R@10% = 0.3106:**

378,000 churners × 0.3106 = **117,407** reach the contactable decile → required save rate **84,000 / 117,407 = 71.5%**. At the 0.4545 ceiling it is 48.9%. Achievable at a 12% save rate: 14,089 saved/yr, **$4.79M**, ROI **19.7x**, churn moves **0.67 pp**, break-even save rate **0.608%** (714 customers/yr). **The CDO's 4-point target remains unreachable, by roughly 6x.**

**Task 2 cost model rebuilt.** The old derivation multiplied `1.0311 DPU-hr` by a 32.9× scale factor — but that 1.0311 is **July's cumulative Cost Explorer usage across every Glue run that month**, not one ETL pass. A monthly total scaled as a per-run cost.

| | Was | Now |
|---|---|---|
| Scale factor | 32.9× | **3.93×** (641,026/wk ÷ 163,255) |
| ETL per run | 1.0311 DPU-hr | **0.1194 DPU-hr** (242 + 188 DPU-s, measured) |
| Glue allocated to churn | $21.85 | **$0.60** |
| Churn total | $108.16 | **$86.92** |
| Per 1,000 predictions | $0.012 | **$0.010** |
| Platform total | $20,303 | **$20,240** (23.8% of budget) |

Accept band moves to **$0.006–$0.015 per 1,000**. TAs are now told to reject scaling a monthly usage total as a per-run cost — the mistake this answer key itself made.

---

## Where this was propagated

Labs 2, 3, 4, 6, 7 (standalone **and** master), the Lab 2/3/4/5/7 solution notes, `Starter Kits/Lab 3/churn_training_skeleton.py`, `Starter Kits/Lab 4/tests/test_model.py`, `Starter Kits/Lab 1/northstar-data-schema.md`, `Notes About Lab Creation.md`, plus `docs/lab6-runbook.md` and `monitoring/alerts/alert-architecture.md` in the live repo.

Verified: no stale figure survives outside the gitignored vault copy of `northstar-ai-platform` and deliberately historical text. Both starter kits parse. 19 commits across the two repos, working trees clean, everything pushed.

New reference documents in the live repo:
- **`docs/lab3-metric-stability.md`** — the full variance measurement, both dataset sizes, and the evidence for every decision above.
- **`data/lab3-reference-dataset.csv`** — the deduped 10k dataset, so the variance sweep reruns with no AWS.

---

## A correction, on the record

Mid-session I reported that 16 chunks of operational content were missing from the master `CS 401R Labs.md` — the `ModelLatency` microseconds trap, the burstable autoscaling constraint, and others. **That was wrong.** All 16 were cosmetic variants: `behaviours`/`behaviors`, `analyse`/`analyze`, `2am`/`2 am`, a comma. My comparison used exact string matching and could not distinguish a missing paragraph from a one-character difference. I acted on the bad analysis and inserted 16 duplicate paragraphs into the master before catching it; reverted with `git checkout`, nothing committed.

**Nothing of substance differs between the master and the standalone labs.** The remaining difference is spelling convention and blockquote wrapping.

---

## Open threads

1. **CodeStar connection — needs your one click.** `northstar-github` exists in `PENDING`. AWS Console → Developer Tools → Settings → Connections → Update pending connection → authorize GitHub. It stays `AVAILABLE` permanently after that. **This blocks thread 2.**
2. **Lab 4 CodePipeline — still never run.** The largest genuinely unexecuted path in the course. Needs thread 1 done, then `pipeline.yaml` deployed. Bundle it with any future AWS session so the NAT is paid once.
3. **The student path has never been run end to end on AWS.** The reference path is verified three times over, but nobody has filled in the skeleton's remaining `TODO`s and run Lab 4's CI tests against real output. The gates and the starter kits agree *by construction*; that is not the same as verified.
4. **Canvas re-upload.** Still needs `CANVAS_API_TOKEN` and `CANVAS_COURSE_ID`. Quizzes pushed before 2026-08-01 still carry old text, and now also old metrics.
5. **Bedrock quotas still 0.** Blocks Lab 3 Track B/C only. Unchanged. Still unanswered whether all 30 student accounts need individual grants; assume yes.
6. **A7's anomaly alarm cannot be demonstrated** in a lab session. Defined and correct, just not showable.
7. **Cosmetic normalisation of master vs standalone.** Pick en-US throughout and re-sync. Low priority — students receive the standalones. One real nit: the master quotes the AWS error as "a request delta of 1 instance**s**"; the live error says "1 Instance".
8. **Lab 6's cost figures were not re-derived at 10k.** The $0.1254/hr burn rate and the $10-breached-at-77-hours figure in `CLAUDE.md` predate the rebase.
9. Vault copy of `northstar-ai-platform` under `Sample Solutions/` is known-stale and gitignored. Unchanged.

---

## State of the account

**Clean.** 43 applied and 43 destroyed on each run; 8-region sweep returns zero endpoints, NAT gateways, feature groups, Glue jobs and processing jobs. Only `northstar-tfstate-711457211658` survives, which is correct.

**Model Registry: v1–v5 all `Rejected`.** Every `ModelDataUrl` points into a destroyed bucket, so none will deploy. v5 carries the canonical metrics in `CustomerMetadataProperties`. Re-running `train_reference.py` after the next apply registers a fresh version with a live artifact. Registry entries are metadata and cost nothing; they are the Lab 3/5 evidence trail.

**Cost Explorer shows ~$0.00 for August to date**, but it lags ~24 h and three NAT-bearing sessions ran on 2026-08-02/03. Check again before assuming zero.

---

## Notes for next session

- `train_reference.py` now writes `docs/lab3-evaluation-metrics.json` on every run. It is **gitignored on purpose** — a single-split metrics file in `docs/` invites exactly the citation error defect 45 was about. Cite `docs/lab3-metric-stability.md` instead.
- The variance sweep runs offline from `data/lab3-reference-dataset.csv`. No AWS needed to re-check any distributional claim in this note.
- Feature Store ingestion is now concurrent (16 threads) and asserts on partial ingest. A partial ingest fails the job rather than reporting success.
- `generate_raw_sample.py` defaults to `--customers 10000`. Regenerating with a different seed changes every metric in this document.
- The `ModelMonitorExecution` role is correctly least-privileged to `datacapture/` and `monitoring/`. Staging test data under any other prefix fails with `AccessDenied` — that is the role working, not a bug.
