---
created: 2026-08-03
tags: [CS401R, handoff, lab4, cicd, pipeline, defects, starter-kits]
supersedes: "Session Handoff — Starter Kit Rebase"
purpose: Thread 1 recorded Lab 4 CodePipeline as "never run". It was not runnable. Six blockers, found by inspection before any NAT spend.
---

# Session Handoff — Lab 4 Pipeline Rebuild

> **Read this before the next session.** It supersedes [[Session Handoff — Labs Starter Kit Rebase]] on **open threads 1, 6, 7 and 8** and adds defects **55–64**. Everything that note says about the canonical metrics, the gate redesign, the dataset rebase.
>
> **The headline: thread 1 said the Lab 4 pipeline had "never been run." That was the wrong diagnosis. It could not run.** Six independent blockers, every one of them in an artifact a student receives, none requiring an AWS session to find. **No AWS session was spent.**

---

## The one-line summary

The pipeline that "just needed running" was missing its source stage's
connection model, its notification topic, its buildspec, its test suite, and
the SageMaker Pipeline it existed to trigger. All six fixed and locally
verified. Still unrun on AWS, deliberately.

---

## Decision recorded this session

Blocker (e) forced a course-design choice, and **Scott chose to write a real
SageMaker Pipeline** (TrainingStep + RegisterModel) rather than train inside
the CodeBuild container.

**The accepted tradeoff, stated plainly:** the TrainingStep runs a real
SageMaker training job. Per `CS_401R_2026/CLAUDE.md`, **AWS default on-demand
training quota is 0 for every instance family**. The reference account has an
applied quota of 15 and will therefore succeed while **every one of the ~30
student accounts fails with `ResourceLimitExceeded`**. There is no bulk grant —
this is 30 individual AWS Support cases, the same deliverability risk class as
the Bedrock block on Lab 3 Track B/C.

This is now the **second** known lab gated on per-student quota requests. It
needs a decision at the course level, not the lab level. Flagged as thread 10.

---

## Defects 55–64

| # | Defect | Status |
|---|---|---|
| 55 | **`sagemaker>=2.200.0` resolves to 3.18.0, which deleted the `feature_store` package outright** (3.x ships only `ai_registry`, `core`, `lineage`, `mlops`, `serve`, `train`). A clean `pip install -r requirements.txt` makes `from sagemaker.feature_store.feature_group import FeatureGroup` raise ImportError; the skeleton swallows it and prints *"sagemaker not available — running in local test mode"*, so the student is sent hunting for a missing install that is not missing while the Feature Store path Task 1 asks them to build reports itself unavailable | **Fixed.** Pinned `<3.0.0`. Skeleton's import guard now separates "not installed" from "installed but 3.x" and names the fix |
| 56 | **The skeleton's commented Feature Store solution referenced an undefined `bucket`** (old thread 6). Pasting it gives `NameError` | **Fixed.** `artifacts_bucket` is now a parameter, threaded from `--artifacts-bucket`; caller updated |
| 57 | **The skeleton's query did not select `loyalty_tier`** (old thread 7), so Task 1's slice evaluation was impossible from the template | **Fixed** per Scott's decision to add the column. Added `SLICE_COLUMN`, kept it *out* of `FEATURE_COLUMNS` (it correlates with spend — feeding it in both leaks and makes the fairness check circular), and documented carrying it through `train_test_split` as a third array |
| 58 | **`pipeline.yaml` created a CodeStar connection named `northstar-github`** — a name already taken on the account. Worse, **a CFN-created connection is born `PENDING` and can only be completed by a human in the console**, so the stack could report success with a source stage that can never pull | **Fixed.** Takes an already-authorized `GitHubConnectionArn` as a parameter |
| 59 | **The ManualApproval stage published to `northstar-model-approvals`, which nothing created.** `aws sns list-topics` returned **empty** on the reference account | **Fixed.** Topic + access policy are now stack resources, with a subscribe command in the outputs |
| 60 | **`buildspec.yml` and `pipeline.yaml` existed only in the vault starter kit, never in the live repo**, and the repo had **no `tests/` directory** — while the buildspec runs `pytest tests/`. CodeBuild, sourcing GitHub `main`, would not have found a buildspec at all | **Fixed.** All three landed in the repo |
| 61 | **`northstar-churn-pipeline` had never been defined by anything, anywhere.** `pipeline.yaml` cited a `pipeline_definition.py` that did not exist. The Build stage's core action was `start-pipeline-execution` against a pipeline that was never created | **Fixed.** Wrote `pipeline_definition.py` + `train_sagemaker.py` |
| 62 | **The buildspec re-implemented the model quality gate in inline Python and had drifted from `tests/test_model.py` three ways at once:** it still enforced the **retired fixed 0.03 lift threshold**; it gated AUC at 0.72 (AUC is *reported, not gated*); and it read `metrics["baseline_auc_roc"]` while the training script emits **`baseline_auc`** — so it failed **every build** with *"baseline_auc_roc missing"* on models that were perfectly fine | **Fixed by deletion.** `tests/test_model.py` is now the single gate implementation, driven from CodeBuild via `EVAL_METRICS_PATH` exactly as `conftest.py` was built to do |
| 63 | **The deploy header said `--capabilities CAPABILITY_IAM`.** The template uses named roles; AWS reports `CAPABILITY_NAMED_IAM`. The documented deploy command would have failed | **Fixed** and confirmed by `validate-template` |
| 64 | **`pre_build` ran `test_model.py` before any model existed.** Its gate tests skip on missing inputs, and **a skip reads as a pass** — so the promotion gate never actually ran in CI | **Fixed.** Moved to the build phase, against real metrics |

---

## The fifth reproduction — through an entirely new code path

`train_sagemaker.py` is a new file, reading a staged channel instead of Athena,
and it lands on the canonical table **byte-identically**:

| Metric | This run | Canonical |
|---|---|---|
| AUC-ROC | **0.7696** | 0.7696 |
| Baseline AUC | **0.7233** | 0.7233 |
| Lift | **+0.0464** | +0.0464 |
| Lift 95% CI | **[0.0254, 0.0670]** | [0.0254, 0.0670] |
| Precision@10% | **0.6833** | 0.6833 |
| Recall@10% | **0.3106** | 0.3106 |
| `scale_pos_weight` | **3.545** | 3.545 |
| Test rows | **3,000** | 3,000 |

Determinism is settled, and now settled across two independent implementations.

---

## What was verified locally, and what was not

**Verified:**
- Skeleton runs clean under **three** SDK states — no sagemaker, 2.257.5, 3.18.0 — AUC 0.7796 in all three, gates pass in all three
- `sagemaker` 2.257.5 installed; `athena_query()` / `.run()` / `.wait()` / `.as_dataframe()` signatures match the skeleton's commented block exactly
- **`.run()` supplies catalog + database via `QueryExecutionContext`**, which is what thread 8 actually doubted — so the skeleton's bare `FROM "{query.table_name}"` with no database qualifier resolves correctly
- `pipeline_definition.py` builds a valid 2-step definition: image `sagemaker-xgboost:1.7-1`, `PendingManualApproval`, and the `ModelMetrics` URI `Join()`s identically on both sides
- `pipeline.yaml` passes `validate-template`
- `buildspec.yml` parses as YAML
- `tests/test_model.py` — **17 passed, 1 skipped** against the pipeline's own emitted metrics
- Full suite from repo root: **39 passed**, 22 errors, all of them "data not found" — correct, that data is staged from S3 by `pre_build`

**Not verified — this is the honest list:**
- **Nothing in Lab 4 has been executed on AWS.** No stack deployed, no pipeline upserted, no build run
- The live `FeatureGroup.athena_query()` call against a real offline store (the remaining half of old thread 8)
- Whether the CodeBuild role's permissions are actually sufficient — they were derived by reading the code, which is exactly the reasoning this project has been wrong about ~17 times
- Lab 5 and Lab 6 were **not** re-run (old thread 2, unchanged)

---

## Cost

**Effectively zero.** No NAT, no endpoint, no Glue, no training job. A handful
of read-only API calls, plus one `sourcedir.tar.gz` written to the tfstate
bucket during definition validation and **deleted immediately** (verified).

Budget at session start: **$0.726 actual against the $10 cap.** Note the
separate **$1 "My Monthly Cost Budget" is at 73%** and will breach on the next
real session — that is a different budget from the course's $10 one.

---

## Git state

**Clean, and `main` is the truth.** Work was done on `lab4-pipeline-execution`,
branched fresh from `main`, **merged fast-forward and pushed, branch deleted
locally and on origin.** `origin/main` moved `b2c62d2 → 66638ad`.

Nothing is unmerged. The vault is not version-controlled, so the starter-kit
edits are live on disk.

---

## Open threads

1. **Lab 4 end-to-end run — now genuinely unblocked, and now genuinely worth doing.** The artifacts finally exist. Deploy `pipeline/cicd/pipeline.yaml` with `CAPABILITY_NAMED_IAM`, passing the authorized connection ARN `arn:aws:codeconnections:us-east-1:711457211658:connection/d8864c98-baee-46f7-8712-b7af841532d0` (verified `AVAILABLE`) and the ML engineer role ARN. Then push a commit and watch a build. **Expect failures** — none of this has met AWS. **Bundle with Lab 5/6 so the NAT is paid once.**
2. **Lab 5 and Lab 6 still not re-run.** Unchanged from the previous handoff; both were verified three times on 2026-08-02.
3. **Canvas re-upload.** Still needs `CANVAS_API_TOKEN` and `CANVAS_COURSE_ID`. Unchanged.
4. **Bedrock quotas still 0.** Blocks Lab 3 Track B/C only. Unchanged.
5. **A7's anomaly alarm cannot be demonstrated** in a lab session. Unchanged.
6. ~~Undefined `bucket`~~ — **closed, defect 56.**
7. ~~Missing `loyalty_tier`~~ — **closed, defect 57.**
8. **Half-closed.** The SDK is installed and the wrapper verified at API level (defect 55 came out of it). The **live** `athena_query()` call against a real offline store still has not happened — fold it into the session that does thread 1.
9. Vault copy of `northstar-ai-platform` under `Sample Solutions/` is known-stale and gitignored. Unchanged.
10. **NEW — two labs now require per-student quota increases.** Lab 3 Track B/C needs Bedrock; Lab 4's TrainingStep needs on-demand training (default **0**). With ~30 independent accounts and no Organization, that is 60 support cases with unknown turnaround. **This needs a course-level decision before either lab can be called deliverable**, and it should be made before more build effort goes into either path.
11. **NEW — the metric vocabulary is forked and the fork is papered over.** `train_reference.py` says `baseline_auc_roc` / `auc_lift_over_baseline` / `auc_lift_ci_low|high`; the skeleton and `test_model.py` say `baseline_auc` / `auc_vs_baseline` / `lift_ci_low|high`. This is what made defect 62 fail every build. `train_sagemaker.py` currently **emits both**, which is a deliberate shim, not a fix. One vocabulary, one rename, with doc fallout — its own change.

---

## Notes for next session

- **The lesson generalises the last two.** The previous session's rule was *"when a gate changes, re-run the sweep against the starter kit, not just the answer key."* This session found that the starter kit contained artifacts that had **never been executed at all, by anyone** — a CFN template that could not deploy, a buildspec with no repo to run in, a pipeline that did not exist. The sharper rule: **an artifact's status is "unverified" until something has run it, and "never run" is not the same as "ready to run."** Thread 1 had assumed the second.
- All six blockers were found by **reading the artifacts against live AWS state** (`list-connections`, `list-topics`, `find`) for the cost of a few API calls. None needed a NAT session. **Do that pass first, always** — it would have saved the previous session's assumption too.
- `pipeline_definition.py` deliberately uses `PipelineSession`, not `Session`. With a plain `Session` the estimator's `.fit()` executes a real training job at definition time instead of being captured as a step.
- `source_dir` **cannot** be a pipeline parameter — the SDK urlparses it at definition time (`'ParameterString' object has no attribute 'decode'`) and wants a `.tar.gz`, not the `.zip` the old buildspec produced. The buildspec now upserts per build, which pins the commit more directly than the old `TrainingCodeS3Uri` ever did.
- `FRAMEWORK_VERSION = "1.7-1"` is load-bearing. A 3.x XGBoost model will not load in the 1.5.2 container in either JSON or UBJ. Do not bump without re-running that check.
- The XGBoost 1.7-1 container already ships pandas, numpy, scikit-learn, pyarrow and xgboost, so `source_dir` is `models/churn` rather than the repo root — otherwise every training job uploads `localstack-data/` and `data/`.
