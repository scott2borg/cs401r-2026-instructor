# CS 401R 2026 — Course Constraints

Project-level context for the NorthStar Retail AI Platform lab series. Read this before proposing any change to lab design, AWS architecture, or student workflow.

## Hard constraints — do not propose solutions that violate these

### Student accounts are STANDALONE. No AWS Organizations.

Each of the ~30 students uses their own independent AWS account. **These accounts are completely independent of BYU.** BYU has no control over them, no responsibility for them, no billing relationship, and no account-team lever to pull on a student's behalf. There is no payer account, no Organizational Unit, no consolidated billing, and no shared control plane.

**Students get whatever the AWS default quota is for a brand-new account. That is the whole story.** There is no escalation path, no bulk grant, and no institutional relationship to fall back on. If a lab does not fit in default quota, the only remedy is 30 students each filing their own AWS Support case.

Ruled out permanently as a consequence:

- **Service Quotas request templates** (`put-service-quota-increase-request-into-template`) — these require an Organization and auto-apply quota increases to member accounts. Unavailable.
- **Centralized/instructor-owned shared account** — breaks the per-student isolation the course has assumed since Lab 1.
- **Any SCP, delegated admin, or org-wide guardrail.**
- **Bulk quota grants** through a single administrative action.

**The operative implication: every lab must complete inside AWS DEFAULT service quotas.** A lab that needs a quota increase needs 30 individual AWS Support cases with unknown turnaround, which is a deliverability risk on the same order as the Bedrock quota problem blocking Lab 3 Track B/C. Treat "fits in default quota" as a design requirement, not a preference.

The reference account `711457211658` is **not** representative. It has accrued elevated applied quotas through months of usage (endpoint 8, on-demand training 15, `ml.m5.large` processing 4 after a request filed 2026-07-31). AWS defaults for all three on-demand families are **0**. Always check `get-aws-default-service-quota`, never `get-service-quota`, when reasoning about what a student will experience.

## Known-good quota facts (us-east-1, verified 2026-07-31)

| Resource | AWS default | Notes |
|---|---|---|
| `ml.t3.medium` / `large` / `xlarge` **processing** | 4 / 4 / 2 | Only 3 of 126 processing types with a non-zero default |
| All non-burstable **processing** | 0 | |
| `ml.m5.large` **endpoint** | 0 | What Lab 5 currently requires |
| `ml.t2.medium` **endpoint** | 2 | Burstable — cannot be an auto-scaling target |
| `ml.m6g.large` / `ml.m6g.xlarge` **endpoint** | 2 / 1 | Graviton, non-burstable |
| All on-demand **training** | 0 | Spot training has non-zero defaults for 12 types |

## SageMaker Model Monitor scheduling is CLOSED to new accounts (2026-07-31)

`CreateMonitoringSchedule` **and** `CreateDataQualityJobDefinition` both return:

```
ValidationException: This operation is in maintenance mode and is not
available to new customers. Existing customers are unaffected.
```

Not a quota. Not a permission. The API is closed to accounts that were not already using it, and **every student account is new**. No workaround exists at the API level.

**Lab 6 no longer uses Model Monitor at all (changed 2026-08-07).** It runs **Evidently**, the open-source Python drift library, inside a plain SageMaker Processing Job. There is no managed control plane to be locked out of.

> **"Evidently" here always means the OSS library** (`pip install evidently`, `docs.evidentlyai.com`). It is **not** Amazon CloudWatch Evidently — an unrelated feature-flag/A-B service that never did model monitoring and which AWS shut down on **16 Oct 2025**. Do not reintroduce that confusion; it was already in these notes once and had to be cleaned out.

**Verified on the Evidently path 2026-08-07** (account `711457211658`, two processing jobs, ~$0.005):

| | Model Monitor (retired) | Evidently (current) |
|---|---|---|
| Instance floor | `ml.t3.large` (Spark, 8 GB) | **`ml.t3.medium` (pandas, 4 GB)** |
| On `ml.t3.medium` | OOM after 13 m 43 s | **1 m 59 s success** |
| Cost per run | $0.010 | **~$0.0017** |

**Three constraints on the Evidently path, all measured:**

- **The `py312` container tag is load-bearing.** Evidently needs Python ≥ 3.10; use `sagemaker-scikit-learn:1.4-2-py312-cpu-py3`. The older `1.2-1` image fails.
- **Pin the version** (`evidently==0.7.21`). The API broke at 0.7 — `column_mapping` → `DataDefinition`, and a bare DataFrame must now be wrapped in a `Dataset`.
- **PSI and KS invert.** PSI returns a statistic (drift when `>` threshold); KS returns a **p-value** (drift when `<` threshold). One comparison operator cannot serve both, and getting it wrong reports no drift on maximally drifted data, silently. This is the highest-value defect to look for in student work.

Installing Evidently upgrades `protobuf`/`urllib3` past the container's pins and pip prints a red `ERROR:` block. **The job still succeeds** — but `botocore` in that container is then unreliable, so publish CloudWatch metrics from the launcher, never from inside the job.

## Bedrock: Agents CLOSED, legacy models CLOSED, 4.5+ needs an inference profile (2026-08-07)

Verified on account `711457211658`, us-east-1. Three separate Bedrock traps, all hit by Lab 3 Track B/C:

| Call | Result |
|---|---|
| `CreateAgent` (managed Bedrock Agents) | **`AccessDeniedException: Bedrock Agents is in Maintenance Mode. New agent creation is not available for accounts without prior service usage.`** |
| `anthropic.claude-3-haiku-20240307-v1:0` | **`Access denied. This Model is marked by provider as Legacy and you have not been actively using the model in the last 30 days.`** |
| `anthropic.claude-haiku-4-5-20251001-v1:0` (bare) | `ValidationException: Invocation ... with on-demand throughput isn't supported. Retry with an inference profile.` |
| **`us.anthropic.claude-haiku-4-5-20251001-v1:0`** | ✅ works — this is the ID to use |
| `amazon.titan-embed-text-v2:0` | ✅ works, 1024 dims |

**Track C must be a client-side ReAct loop over `bedrock-runtime`, never managed Bedrock Agents.** `models/agent/customer_service_agent.py` is the working reference (verified end to end: 1 tool round, ~$0.0045/turn). `models/agent/bedrock_agent_setup.py` cannot run on any student account and now fails fast with an explanation.

**This is the fourth instance of the same pattern in this course** — after Model Monitor schedules, CloudWatch Evidently's shutdown, and legacy Bedrock model IDs. Assume any AWS capability may be closed to new accounts and **call the API to find out**; the reference account is not representative, and here even it is refused.

**Implication beyond Lab 6:** treat any AWS API this course depends on as possibly closed to new accounts, regardless of what documentation says. Verify on the reference account only after remembering it is *not* new — it has usage history the students' accounts will not have.

## Lab 3 starter-kit defects found by RUNNING it (2026-08-08)

`evaluation_harness.py` had never been executed. Four defects, all student-facing:

| Defect | Effect |
|---|---|
| Track C required `--agent-id`/`--agent-alias-id` | Only `CreateAgent` produces those, and it is blocked — **no student could run Track C evaluation** |
| `"escalate" in tool_calls` | Exact **list membership** vs a tool named `escalate_to_human` → always `False` |
| `"human_agent" in response` | Prose never contains that literal → escalation **never detected**, so every `should_escalate=True` scenario auto-failed, TC-005 included |
| `pip install ragas datasets langchain` | Installs fine, then `ModuleNotFoundError: langchain_community.chat_models.vertexai` |

Fixes: `LocalAgentEvaluator` (student-supplied `invoke_fn`), one shared `detect_escalation()` helper used by both evaluators, and the pin **`pip install ragas datasets "langchain-community<0.4"`** (ragas 0.4.3 + langchain-community 0.3.31 works; 0.4.2 does not — the package is being sunset).

**Reference agent scores 5/6, not 6/6.** TC-003 legitimately fails: on a 45-day boundary return it asks for an order ID instead of calling `query_policy` and escalating. Do not treat 6/6 as expected.

> **`pip install` succeeding is not evidence the package works.** Import it. Same class of error as "the model ID is documented" and "the API exists" — verify by executing, not by reading.

## Experiment tracking: MLflow App, NOT Experiments, NOT a Tracking Server (2026-08-07)

SageMaker Experiments is out of the labs. Its Python SDK tracking is Studio-Classic-only and AWS now directs everyone to MLflow. Labs 3, 4 and 6 use a **SageMaker MLflow App**.

> ## ⚠ There are TWO MLflow products and one will destroy the course budget
>
> | | **MLflow App** ✅ | MLflow **Tracking Server** ❌ |
> |---|---|---|
> | API | `CreateMlflowApp` | `CreateMlflowTrackingServer` |
> | Cost | **no additional charge** (serverless) | **$0.60/hr** from creation to deletion |
> | The $10 course budget | never | **breached in 16.7 hours**; ~$43/weekend |
>
> **Most documentation and search results describe the Tracking Server**, because it shipped first. If anything asks you to pick a size (`Small`/`Medium`), it is the wrong product. Never propose it for this course.

**Verified on AWS 2026-08-07** (account `711457211658`, us-east-1, created and torn down):

- `CreateMlflowApp` requires only **Name + ArtifactStoreUri + RoleArn**. `DefaultDomainIdList` is optional — **no SageMaker Studio domain needed**. Worked from a plain IAM user.
- Reached `Created` in **4 min 52 s**; served **MLflow 3.10.1**.
- Logged 3 runs via `mlflow.set_tracking_uri(APP_ARN)` and read them back with `mlflow.search_runs`, params and metrics intact.

**Two things that break it, both silently misleading:**

- **The API postdates many installed AWS CLIs.** `aws-cli 2.27.40` on this machine does **not** have `create-mlflow-app`; it reports `Invalid choice`, which reads like a typo. Needs a current CLI / `botocore` ≥ ~1.43.
- **`mlflow` alone is not enough** — you also need `sagemaker-mlflow`, the SigV4 auth plugin for `arn:aws:sagemaker:...` tracking URIs. Without it the failure never mentions credentials.

**SageMaker Pipelines auto-create Experiments regardless.** The reference account has `northstar-churn-pipeline` with 11 trials, `SourceType: SageMakerPipeline`. Lab 4 teaches this rather than hiding it: auto-generated lineage is free and nearly content-free; deliberate tracking is what earns marks.

**Guardrails in place:** `teardown-lab3.sh` and `teardown-lab6.sh` sweep for tracking servers; `preflight-lab6.sh` warns on one. The MLflow App is deliberately **not** torn down — it is free and Labs 4 and 6 log to it.

## Deployment-path facts (verified on AWS 2026-07-31)

| Question | Answer | Evidence |
|---|---|---|
| Does Application Auto Scaling accept a **Graviton** (`ml.m6g.large`) endpoint? | **YES** | `RegisterScalableTarget` accepted, target-tracking policy created, 2 `TargetTracking-*` alarms auto-created |
| Does the arm64 XGBoost container serve? | **YES** | `1.5-1-arm64` returned a prediction |
| `ml.m6g.large` deploy time | **4 min 04 s** | vs 6 min 47 s for `ml.m5.large` |
| `ml.m6g.large` price | **$0.0924/hr** | ~20% cheaper than `ml.m5.large` |
| Can a modern XGBoost model load in the **1.5.2** container? | **NO — neither JSON nor UBJ** | Blocks the Graviton path without a 2-major-version training downgrade |
| Can a 3.2.0 model load in the **1.7-1** container? | **YES** | Current Lab 3→5 path is safe; `xgboost>=2.0.0` is fine |
| Serverless Inference default quota | **5 endpoints / 10 concurrency** | Non-zero by default; no instance quota needed |
| Does Serverless support `DataCaptureConfig`? | Yes (config-level field) | API model — **not yet run** |

**Graviton is technically viable but blocked by XGBoost.** `inference_graviton` exists only for XGBoost 1.3-1 and 1.5-1; 1.5.2 has no Python 3.11 wheels. Downgrading is rejected.

## Verification standards

- **Verify on AWS. "It should work" has been wrong ~17 times on this project.** Test the thing you are about to assert.
- Prefer **observed** evidence over configuration screenshots.
- Verify against the live AWS API, never the console index (it lags hours).
- **`aws service-quotas list-service-quotas --query ...` applies `--query` PER PAGE** and silently returns partial results. Use `get-service-quota`/`get-aws-default-service-quota` with an explicit quota code, or a boto3 paginator. This bug produced a false finding on 2026-07-31.
- Tear down after every AWS session and confirm with an independent all-region sweep.
- AWS credentials: no `[default]` profile exists. Use `AWS_PROFILE=terraform-user` (IAM user `CS401RAdmin`, `us-east-1`).

## Cost posture

- Budget alarm is **$10/month** → scott@toborg.com. It is shared across the whole project.
- Endpoints bill hourly until deleted; rolling back to weight 0 does not stop the charge.
- Monitoring schedules keep launching billable processing jobs after the endpoint is gone.
- Lab 6 burn rate with endpoint + hourly schedule: **$0.1296/hr** on `ml.m5.large`, **$0.0706/hr** on `ml.t2.medium`; $10 breached at 75 and 137 hours respectively. Re-derived at the 10,000-customer dataset 2026-08-03. Job durations corrected 2026-08-06 against `describe-processing-job`: `nsc-baseline-1785768831` and `nsc-analysis-1785768831` each ran **5 m 36 s** of billable `ProcessingTime` on `ml.t3.large`; create-to-end wall clock was 6 m 27 s and 10 m 09 s. The previously recorded "9 m 44 s / 8 m 44 s" matched no job in the account.

## Authority rules

- The live repo `/Users/scott1/northstar-ai-platform` is authoritative **and is the only copy**. The old tree at `CS_401R_Labs/Sample Solutions/northstar-ai-platform/` is **retired and gitignored — do not sync to it, do not recreate it.** See `docs/GitHub Integration.md`. To browse the reference implementation, open the real repo.
- **Standalone `Lab_N--*.md` is authoritative over the master `CS 401R Labs.md`**, which is synced to match and verified byte-identical.

## Canvas

The Canvas course (**34609**) is built by `build_course.py` at the project root.
**Runbook: `Canvas Update Process.md`.** Read its "Canvas API gotchas" section
before debugging anything — Canvas silently ignores unknown parameters, applies
defaults, and returns success, which caused every hard bug on 2026-08-05/06.

- Canvas is a **derived artifact**. Source of truth is `CS_401R_Labs/*.md` and
  `course_config.yaml`. Never edit a lab description in the Canvas UI; the next
  run overwrites it.
- `Canvas LMS/_superseded/` holds the retired `canvas_builder.py`. Do not run it.
- For any file problem, start with `python debug_files.py`.
