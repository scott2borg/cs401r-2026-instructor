---
created: 2026-08-03
tags: [CS401R, handoff, lab4, cicd, pipeline, defects, serving, determinism]
supersedes: "Session Handoff — Lab 4 Pipeline Rebuild"
purpose: Lab 4 CodePipeline now runs Source → Build → ManualApproval on AWS. Getting there took six more defects, two of which made the registered model unloadable and undeployable.
---

# Session Handoff — Lab 4 Runs End to End

> **Read this before the next session.** It supersedes [[Session Handoff — Lab 4 Pipeline Rebuild]] and closes **threads 1, 6, 7 and 8**. It adds defects **65–72**. Everything the earlier notes say about the gate redesign, the dataset rebase and the Model Monitor traps still stands.
>
> **The headline: Lab 4 ran end to end for the first time — Source → Build → ManualApproval, all Succeeded.** It took **five builds** and six more defects to get there. **Two of them meant the model the pipeline registered could not be loaded by any modern XGBoost, and could not be deployed at all.** Both were invisible to every test that runs before an actual deploy.

---

## The one-line summary

The rebuilt pipeline was correct on paper and wrong in six more places on AWS.
It now runs, and a model trained by it deploys to an endpoint and predicts.

---

## Lab 4 — the run

| Stage | Result |
|---|---|
| Source (CodeStar → GitHub `main`) | **Succeeded** — first build, no retries |
| Build (CodeBuild → SageMaker Pipeline) | **Succeeded** on build 5, **4 m 49 s** |
| SageMaker Pipeline (Train → Register) | **Succeeded**, ~210 s |
| ManualApproval | **Succeeded** (approved via `put-approval-result`) |
| Model Registry | **v5, `PendingManualApproval`** with `ModelMetrics` correctly wired |

**Tests inside CI, against real Glue Parquet:** `test_data.py` **26 passed**,
`test_features.py` **18 passed**, `test_model.py` **17 passed / 1 skipped**
against the artifact the pipeline had just registered.

---

## Defects 65–72

| # | Defect | Status |
|---|---|---|
| 65 | **`ArtifactsBucket` is a required stack parameter and nothing in the course creates that bucket.** Lab 4's prose never mentions it; CodePipeline also requires it to be versioned | **Worked around** — created by hand this session. **Needs a real home** (thread 3) |
| 66 | **`${VAR:0:8}` is a bashism and CodeBuild runs `/bin/sh`.** The build died at the first substring expansion with `exit status 2` and no useful message. The **original** buildspec used it in four places, so it would have failed identically had it ever reached the build phase | **Fixed.** `cut -c1-8`; `post_build` re-derives `COMMIT_SHA` because CodeBuild does not carry `export`s across phases |
| 67 | **`MLEngineer` could not `iam:PassRole` to itself.** A pipeline assumes the role and then creates a training job passing that same role. A direct `CreateTrainingJob` from a user principal never hits this — Lab 4 is the first thing to drive training through an assumed role. One layer down: **`sagemaker:AddTags`**, because Pipelines tag every resource they create, so `CreateTrainingJob` fails on `AddTags` before the job exists | **Fixed** in the IAM module, scoped: `PassRole` conditioned on `iam:PassedToService=sagemaker.amazonaws.com`, one role |
| 68 | **The SDK uploads `sourcedir.tar.gz` to `s3://<bucket>/<pipeline-name>/code/`** — a top-level prefix `MLEngineer` cannot read, since its S3 grant is deliberately scoped to `artifacts/*` and `features/*`. The container failed downloading its own code | **Fixed** by pinning `code_location` to `artifacts/code`, **not** by widening the role |
| 69 | **The canonical figures are XGBoost-version-dependent, and the docs do not say so.** See below | **Documented here.** Needs a doc fix (thread 5) |
| 70 | **The CI gate got metrics but no model artifact**, so `TestModelLoading` failed in CI while passing locally | **Fixed.** CI now downloads and extracts the `model.tar.gz` the pipeline just registered |
| 71 | **The registered model was in a format nothing modern can load.** XGBoost picks save format from the **file extension**; `.xgb` is not recognised, so XGBoost 1.7 (the training container) fell back to the **legacy binary format — deprecated in 1.6, removed in 3.1**. Locally on 3.2.0 the identical call silently defaults to UBJSON, which is exactly why it never surfaced until the model was built in a container instead of on a laptop | **Fixed.** Explicit `model.ubj`, plus a copy named `xgboost-model` — the name the **serving** container requires and the convention `train_reference.py` already uses. Verified: saved under 1.7.6, loads under 3.2.0, identical bytes, 11 features |
| 72 | **The model trained, gated, registered clean — and would not deploy.** `/opt/ml/model` is tarred into `model.tar.gz`, and the XGBoost container's algorithm mode **enumerates that directory and tries to load every file as a booster**. `evaluation_metrics.json` was sitting there: `RuntimeError: Model /opt/ml/model/evaluation_metrics.json cannot be loaded: Pickle load error=invalid load key, '{'`. gunicorn's worker exits 3, `/ping` 502s, and **the endpoint sits in `Creating` for ~25 minutes before failing** | **Fixed.** `model_dir` now holds exactly one file. Metrics and metadata go to `output_data_dir` and to the deterministic S3 prefix the registry already cites |

---

## Defect 69 — the canonical numbers move with the XGBoost version

This one deserves its own section because it changes what Lab 3 should claim.

Three of the four headline metrics **change** between XGBoost 3.2.0 (local, what
every published figure was produced on) and XGBoost 1.7 (the SageMaker training
container, which is what Lab 4's pipeline uses):

| Metric | 3.2.0 — published | 1.7.6 local | 1.7-1 container |
|---|---|---|---|
| Baseline AUC | 0.7233 | **0.7208** | **0.7208** |
| Precision@10% | 0.6833 | **0.6933** | **0.6933** |
| Recall@10% | 0.3106 | **0.3152** | **0.3152** |
| Full-model AUC | 0.7696 | 0.7683 | 0.7724 |

The 1.7.6 local run and the 1.7-1 container agree **exactly** on the first
three, and both differ from the published 3.2.0 values. The split is identical
(6,999/3,000), the slice sizes are identical (307/483/1,071/1,139), and
`scale_pos_weight` is identical at 3.545 — so this is the estimator, not the
data or the ordering.

**What this means.** "Four independent reproductions, byte-identical, treat
determinism as settled" is true **only at a fixed XGBoost version**. All four
of those reproductions ran on the same local 3.2.0. A student who trains
through Lab 4's pipeline will get different numbers from Lab 3's published
table and reasonably conclude they broke something. **The published figures
need an XGBoost version stamp, and Lab 3 needs a sentence saying the container
and the laptop will not agree to four decimal places.**

The gate is unaffected — the lift CI excludes zero in every configuration
tested — so this is an expectations defect, not a broken gate.

---

## Lab 5 — the deploy path, partially re-verified

Done **because defect 71 changed the artifact format**, which made a real
serving test necessary rather than optional:

- Registered model → `create-model` → endpoint on `ml.m5.large`
- **`InService` in 3 m 12 s** (vs 6 m 47 s documented — but this is a
  model-package deploy, not the Lab 5 canary path, so do not overwrite the
  published figure with it)
- Invoked with six real offline-store rows: three most recent buyers scored
  **0.0027 / 0.0127 / 0.0417**; three dormant customers (362–365 days) scored
  **0.9917 / 0.9955 / 0.9968**. Clean separation, correct direction

**Not done:** the Lab 5 canary/rollback path, auto-scaling, and the whole of
Lab 6's Model Monitor re-run. Thread 2 stays open, narrowed.

---

## Thread 8 — closed

The live `FeatureGroup.athena_query()` path was exercised against a real
offline store, twice:

- `catalog=AwsDataCatalog database=sagemaker_featurestore table=northstar_dev_customer_features_1785787612`
- **9,999 rows, 9,999 unique customers** on both runs
- **Identical row order, frames byte-identical** — the SDK path is reproducible
- `loyalty_tier` present with all four tiers, confirming defect 57's fix against real infrastructure
- Positive rate **0.2200**, matching canonical

The specific thing this thread doubted — whether the bare
`FROM "{query.table_name}"` with no database qualifier resolves — **it does**:
`.run()` supplies catalog and database through `QueryExecutionContext`.

---

## Measured on AWS 2026-08-03 (second session of the day)

| Stage | This run | Previous |
|---|---|---|
| `terraform apply` | 43 added, **2 m 17 s** | 43 added, 2 m 37 s |
| Crawler | SUCCEEDED, `customers`, 9 cols | same |
| Glue transform | **97 s / 194 DPU-s** | 107 s / 214 DPU-s |
| Glue feature-engineer | **93 s / 186 DPU-s** | 93 s / 186 DPU-s |
| `terraform destroy` | 43 destroyed | 43 destroyed |

Storage **byte-identical again**: `raw/` 13,582,469 B, `processed/` 3,856,995 B,
`features/` 317,006 B.

**Glue DPU-s is now measured at 430 / 400 / 380 across three runs** — a 12%
spread. The Lab 7 Task 2 accept band should absorb that; treating 430 as exact
is wrong.

---

## State of the account

**Clean.** 43 applied, 43 destroyed. CFN stack deleted, SageMaker Pipeline
deleted, endpoint/config/model deleted, the hand-made CI/CD artifacts bucket
purged of all 24 object versions and removed. Independent **8-region sweep
returns zero** endpoints, feature groups, NAT gateways, in-progress processing
jobs and in-progress training jobs. Only `northstar-tfstate-711457211658`
survives, which is correct.

**Model Registry: v1–v5.** v4 and v5 were approved during the deploy test and
have been **set back to `Rejected`** — their `ModelDataUrl`s died with the
bucket.

**Cost:** budget still reads **$0.726 / $10** (Cost Explorer lags ~24 h, so
today's two NAT sessions are not in it yet). The separate **$1** budget is at
73% and will breach when this lands.

---

## Git state

**Clean, `main` is the truth.** Six commits, all merged and pushed.
`origin/main` moved `b2c62d2 → b1c3243`. Nothing unmerged, no stale branches.

---

## Open threads

1. ~~Lab 4 end-to-end~~ — **CLOSED.** Runs Source → Build → ManualApproval.
2. **Lab 5 canary/rollback + auto-scaling, and Lab 6 Model Monitor, still not re-run.** Narrowed: the deploy-and-predict path is now verified at 10k, so what remains is specifically the canary weights, the rollback alarm, and the Lab 6 analyzer-as-processing-job.
3. **NEW — `ArtifactsBucket` has no owner (defect 65).** It is a required parameter that nothing creates and no lab mentions. Either add it to the Terraform storage module or write the `create-bucket --versioning` step into Lab 4's prose. **A student cannot deploy the stack without it and has no way to know.**
4. **Canvas re-upload.** Unchanged. Needs `CANVAS_API_TOKEN` / `CANVAS_COURSE_ID`.
5. **NEW — Lab 3's published metrics need an XGBoost version stamp (defect 69).** See the section above. Also decide whether Lab 3's "SageMaker training jobs — fine, train freely" line survives, given default training quota is 0.
6. **Bedrock quotas still 0.** Unchanged.
7. **A7's anomaly alarm** still not demonstrable in a lab session. Unchanged.
8. ~~Live `athena_query()`~~ — **CLOSED.**
9. Vault copy under `Sample Solutions/` still stale and gitignored. Unchanged.
10. **The quota decision is still outstanding, and is now the single biggest deliverability risk.** Lab 4's TrainingStep needs on-demand training quota (**default 0**; the reference account has 15, which is why it passed here). Lab 3 Track B/C needs Bedrock. That is ~60 individual support cases across 30 independent accounts. **Nothing in this session reduced that risk — it only proved the code works on an account that already has the quota.**
11. **The metric vocabulary is still forked** (`baseline_auc_roc` vs `baseline_auc`, etc.). `train_sagemaker.py` still emits both as a deliberate shim. Unchanged.

---

## Notes for next session

- **The lesson, third refinement.** The last two sessions learned "re-run the sweep against the starter kit" and "never run ≠ ready to run." This session adds the sharpest version: **defects 71 and 72 were both invisible to every check that stops short of a real deployment.** The model trained, the gate passed, the registry entry was valid and well-formed — and the artifact was in a dead format and could not boot a container. **Registering a model is not evidence that it can be served. Deploy it.**
- Both of those defects also only appear **in the container**. On a laptop with xgboost 3.2.0 the identical `save_model` call silently does the right thing. Where the code runs is part of the test.
- Five builds to green, and each failure was a different layer: shell dialect → IAM PassRole → IAM AddTags → S3 prefix scoping → artifact format → artifact contents. **Budget several iterations for anything that has never executed**; the first green build is not the finish line, it is where deployment testing starts.
- `terraform destroy` needs a generous timeout — it exceeded 900 s once and had to be re-run. It is idempotent, so re-running is safe.
- The CI/CD artifacts bucket is versioned, so `s3 rm --recursive` will not empty it. Delete object **versions** and delete markers, or the bucket delete fails with `BucketNotEmpty`.
- `put-approval-result` needs `--result` as JSON; the `summary=...,status=...` shorthand splits on the comma inside the summary text and fails validation.
