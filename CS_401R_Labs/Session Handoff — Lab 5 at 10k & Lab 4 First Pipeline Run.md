---
created: 2026-08-06
tags: [CS401R, handoff, lab-4, lab-5, cicd, verification, defects]
supersedes: "Session Handoff — Last Canvas Migration & Course Build"
purpose: Lab 5 canary/rollback verified at 10k, Lab 4 CodePipeline executed end to end for the first time, and the model registry made honest. One apply paid the NAT once for all of it.
---

# Session Handoff — Lab 5 at 10k & Lab 4 First Pipeline Run

> **Read this before the next AWS session.** It supersedes
> [[Session Handoff — Last Canvas Migration & Course Build]] on open threads 3
> and 4, which are now closed. Everything that note says about Canvas, the
> Canvas API behaviour and the lecture-deck figures **still stands unchanged**.
>
> **The headline: two of the four things recorded as open were not what the note
> said they were.** Lab 6's Model Monitor had already been re-run at 10k on
> 2026-08-03. Model package v7 was never `Approved`. Reading the live API first
> would have closed both in five minutes.

---

## What ran

One continuous pass on account `711457211658`, us-east-1. Full platform rebuild
from an empty Terraform state, Labs 2→5 chain, Lab 4 CI/CD, then complete
teardown.

| Stage | Result | Measured |
|---|---|---|
| `terraform apply` — VPC + NAT + storage + IAM + Glue + Feature Store | **43 added, 0 errors** | 2 m 16 s; NAT 1 m 45 s |
| Raw CSV → S3 (committed `northstar-raw-sample.csv`, not regenerated) | 13 MB | 163,255 transactions / 11,435 customers |
| Glue crawler | SUCCEEDED | table `customers` catalogued |
| Glue transform → `processed/customers/` | SUCCEEDED | **122 s, 244 DPU-s** |
| Glue feature-engineer → `features/` + Feature Store | SUCCEEDED | **95 s, 190 DPU-s** |
| Feature Store online store | `GetRecord` → 16 features | immediate |
| Feature Store **offline** hydration | 41 Parquet objects | **~4 min** |
| **Athena → train → register** (`train_reference.py`) | **all gates PASS** | registry `northstar-churn-models/6` |
| Lab 5 canary deploy, 2 variants | `InService` | **6 m 50 s** on `ml.t2.medium` |
| Lab 5 traffic split + rollback | verified | see table below |
| **Lab 4 CodePipeline** | **Succeeded, all 3 stages** | first end-to-end run ever |
| `terraform destroy` | **43 destroyed** | matches 43 applied |
| All-region sweep, 8 regions | **0 billable resources** | — |

**Do not regenerate `data/northstar-raw-sample.csv`.** The committed file is the
one that produces the canonical metrics. A different seed changes every number
in this note.

---

## Lab 5 canary + rollback — verified at 10k (closes open thread 3)

Every reference number from the 2026-07-31 run reproduced on the 10k dataset.

| Measure | Reference (07-31, `ml.t2.medium`) | **This run (10k)** |
|---|---|---|
| create-endpoint → `InService`, 2 variants | 7 m 03 s / 7 m 33 s | **6 m 50 s** |
| observed split at 9:1 over 200 calls | 175/25 · 174/26 · 182/18 | **180/20** |
| weight-shift rollback | ~92 s | **~92 s** |
| observed split at 10:0 over 100 calls | 100/0 | **100/0** |
| ModelLatency steady state | ~3,793–4,628 µs | **4,901–5,133 µs** |
| ModelLatency first call after deploy | ~27,696 µs | **13,154 µs** |

**Data capture verified** at the documented layout, partitioned **per variant**
(`datacapture/northstar-churn-prod/{champion,canary}/…`), 6 objects. Lab 6's
analyzer input path works at 10k.

**What was NOT re-verified:** the alarm's `OK → ALARM` transition. The rollback
alarm was created at the microsecond-correct threshold **200000** and correctly
sat `OK` against healthy latency — which is the half that matters, since a wrong
threshold is what made it fire on every deploy. Driving it into `ALARM` (the
07-31 run did this with a threshold of `1000`) was not repeated. The rollback
itself was executed via `--rollback`, not triggered by the alarm.

---

## Lab 4 CodePipeline — executed end to end, first time (closes rebase thread 2)

Previously "the largest genuinely unexecuted path in the course." It was blocked
on the CodeStar connection, which now reads `AVAILABLE`.

| Stage | Result |
|---|---|
| Source (GitHub `scott2borg/northstar-ai-platform` @ `main` via CodeConnections) | **Succeeded** |
| Build (`northstar-ci`) — install 68 s, pre_build 7 s, build 236 s | **Succeeded** |
| SageMaker Pipeline `codebuild-e1b2c895` — `TrainChurnModel` → `RegisterChurnModel` | **both Succeeded** |
| ManualApproval | **Succeeded** |

The pipeline registered `northstar-churn-model-group/8` as
`PendingManualApproval` — correct: approval is the graded governance step.
Stage 4 (Deploy) is still a deliberate `TODO` in the template, to be implemented
in Lab 5.

**Stack deployed as `northstar-cicd`** with parameters: `GitHubOwner=scott2borg`,
`ArtifactsBucket=northstar-codepipeline-artifacts-711457211658` (created for this
run, since destroyed), `SageMakerRoleArn=…/northstar-dev-MLEngineer`,
`GitHubConnectionArn=…/d8864c98-baee-46f7-8712-b7af841532d0`.

---

## The Platinum reversal was already correct — this run is the third confirmation

Today's slice figures match the published ones **exactly**, on a fresh
VPC/bucket/Glue/Feature-Store rebuild:

| Tier | n | AUC | Churn |
|---|---|---|---|
| Platinum | 307 | 0.8483 | 6.8% |
| Gold | 483 | 0.7559 | 10.8% |
| Bronze | 1,071 | 0.7442 | 33.7% |
| **Silver** | 1,139 | **0.6935** | 19.8% |

Aggregate metrics likewise reproduced exactly: **AUC 0.7696 · baseline 0.7233 ·
lift +0.0464 CI [0.0254, 0.0670] · P@10% 0.6833 · R@10% 0.3106 · churn 22.0% ·
6,999 train / 3,000 test.** Gates: ALL PASS.

**Process note, and the mistake of this session.** This assistant read
[[Session Handoff — Labs 2-5 End-to-End Run]] — a note explicitly superseded
2026-08-03 — and reported its falsified prediction ("the Platinum finding is
structural and will survive a re-run") as a live finding, claiming Lab 3 and Lab
7 content needed rewriting. They did not; the rewrite happened on 2026-08-03.
Two superseded handoffs have now been banner-marked at the specific passages
their existing banners did not cover:

- `Session Handoff — Lab 3 to Lab 4.md` — the "Platinum finding" section. Its
  top banner covered only the aggregate metrics, so a TA reading that section
  would have taken away exactly the wrong lesson.
- `Session Handoff — Labs 2-5 End-to-End Run.md` — the falsified prediction, and
  the "decision waiting on you" item that was in fact decided and implemented.

**A `supersedes:` field in frontmatter is not enough.** Retract at the claim,
not just at the top of the note.

---

## Model registry — now honest (closes open thread 4)

The recorded problem — "v7 `Approved` with a dead `ModelDataUrl`" — was wrong in
both halves. v7 was `PendingManualApproval`, and the dead-artifact condition was
universal, not v7-specific: the whole `northstar-dev-data-711457211658` bucket
had been destroyed, so **all 12 packages across both groups** pointed at nothing.
There was never a deployable dead artifact.

**Final state: 14 packages, all `Rejected`, 0 `Approved` anywhere.** Verified by
read-back, not by trusting the write.

`northstar-churn-models/6` was legitimately `Approved` during this session with a
live artifact, deployed, and then set back to `Rejected` when teardown destroyed
its bucket — otherwise this session would have recreated the exact condition it
set out to fix. The metrics survive teardown in `CustomerMetadataProperties`,
including `slice_worst_tier=Silver` and `slice_worst_auc=0.6935`.

---

## Defects found and fixed

| # | Defect | Fix |
|---|---|---|
| 75 | **`teardown-lab5.sh` deleted CloudWatch alarms it did not own.** `--alarm-name-prefix northstar` matched `northstar-ci-build-failure` — the Lab 4 CI gate-failure alarm owned by the `northstar-cicd` stack. Running Lab 5 teardown silently disarmed a Lab 4 control and drifted the stack from its template. Now that Lab 4's pipeline actually runs, students would have hit this | **Fixed.** Prefix narrowed to `northstar-churn-rollback`. `TargetTracking-*` alarms are deliberately not listed — deregistering the scalable target deletes them |
| 76 | **`teardown-lab5.sh` reported a false failure on every clean teardown.** `--query` is applied **per page**, so `list-processing-jobs` returned `"0\n0"` on a clean account. That is not the string `"0"`, so the check printed `Processing jobs running  STILL PRESENT: 0` and the "resources may still be billing" warning — on the one script whose entire job is to tell you the account is clean. Same `--query`-per-page bug already documented in `CLAUDE.md` for `service-quotas` | **Fixed.** The check sums across lines instead of string-comparing. Correct for single- and multi-page. Re-ran the script: all six checks `OK`, correct completion message |

Both fixes verified by re-running `scripts/teardown-lab5.sh` against the live
account. Changes are **uncommitted** in `/Users/scott1/northstar-ai-platform`:
`scripts/teardown-lab5.sh` and the regenerated `docs/lab5-teardown-output.txt`.

---

## Open threads

1. **24 of 26 lecture decks have no figures.** Unchanged. Scott is generating
   them with an image-capable LLM from `Presentations/Figure_Descriptions/`.
   When they come back: insert into `Presentations/PowerPoint/*.pptx`, then
   `python build_course.py --stage 6`. **Do NOT re-run
   `generate_presentations.py`** — it would discard the inserted figures.
2. **The quota decision.** Unchanged, owned by Scott and his TA. Lab 4's
   TrainingStep needs on-demand training quota (AWS default **0**) and Lab 3
   Track B/C needs Bedrock. ~60 support cases across 30 independent accounts.
3. **NEW — `pipeline/cicd/pipeline.yaml:407` instructs approvers to check a
   retired gate.** The ManualApproval `CustomData` says *"Check: AUC-ROC ≥ 0.72,
   Precision@Top10 ≥ 0.40"*. The absolute AUC gate was removed 2026-08-02; the
   promotion gate is the bootstrap lift CI excluding zero. The sweep put the
   reference model at mean AUC 0.7120 (sd 0.0291), so this instruction sits
   **above the mean of the distribution it gates** — a student following it
   would reject a model that passes the real gate on ~58% of splits. Same drift
   pattern as the hardcoded syllabus grading table. **Not fixed; needs your
   call on the replacement wording.**
4. **Publish + finals presentation schedule.** Unchanged and correctly deferred.
   Modules are unpublished; the student finals schedule posts by Dec 1 and needs
   September team sign-ups first. **`CANVAS_API_TOKEN` is unset** — the old token
   was revoked 2026-08-06. Mint a fresh one and use the `printf`/`read -rs` form
   in the runbook.
5. **The student path has still never been run end to end.** The reference path
   is now verified four times over and Lab 4's CI ran against real output, but
   nobody has filled in the skeleton's remaining `TODO`s and run it as a student
   would. The gates and starter kits agree *by construction*; that is not the
   same as verified.
6. **A7's anomaly alarm cannot be demonstrated** in a lab session. Unchanged.
7. **Vault copy under `Sample Solutions/`** still stale and gitignored.
   Unchanged.
8. **Two duplicate pre-lab HTML files** in Canvas Files → `Lab Guides`, and three
   obsolete `.md` files in `Lab Starter Kits`. Cosmetic; Scott deleting by hand.

---

## State of the account

**Clean.** 43 applied and 43 destroyed. Independent sweep across 8 regions
(us-east-1/2, us-west-1/2, eu-west-1, eu-central-1, ap-southeast-1,
ap-northeast-1) returns **0** endpoints, endpoint configs, models, NAT gateways,
Glue jobs, feature groups and monitoring schedules. 0 CloudFormation stacks, 0
CloudWatch alarms. Only `northstar-tfstate-711457211658` survives, which is
correct.

**Cost.** Cost Explorer lags ~24 h and still reads ~$0.00 for August, so it is
**not** yet evidence of anything. Estimated from resources actually consumed:
NAT ~2 h, 434 Glue DPU-seconds, 2 × `ml.t2.medium` for ~14 min, one CodeBuild
run, one short training job — **well under $1**, against the $10/month budget
alarm. Check again in 24 h before assuming.

---

## Notes for next session

- **Read the live API before believing a handoff.** Two of four open items were
  already closed or misstated. `describe-model-package` and
  `list-processing-jobs` answered both in minutes.
- **`python` is not `python3` on this machine.** `python` resolves to
  `/Users/scott1/miniconda3/bin/python`, which has **no xgboost**;
  `/usr/local/bin/python3` has xgboost 3.2.0 but **no `sagemaker`**.
  `train_reference.py` needs the former set and imports no `sagemaker`, so run it
  with `python3`. The labs tell students `python …` — worth a note in the lab
  text or a venv in the repo.
- **Piping a long Python run through `| tail` hides all output until it exits.**
  Same block-buffering trap as `| tee` in the Canvas runbook. Poll the AWS API
  for progress instead of watching the pipe.
- **zsh does not word-split unquoted expansions.** Two ad-hoc sweep scripts
  written this session (`for r in $REGIONS`, and a `set -- $pair` loop) silently
  ran once with the whole string as a single item and printed a **false clean**
  and a **false "ARTIFACT ALIVE"**. Both were caught only by re-reading the
  output. Write the list literally in the `for`, or use an array.
- Feature Store offline hydration measured **~4 min** again. Lab 2's "~15 min
  lag" warning remains safe but pessimistic; poll rather than wait.
- Bundling was correct: one apply paid the NAT once for Lab 5, Lab 4 and the
  slice reproduction. Keep bundling AWS work.
