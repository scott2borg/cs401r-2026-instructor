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

**What still works:** `CreateProcessingJob`, and the `model-monitor-analyzer` container itself. Verified — the analyzer runs as a plain processing job against captured data and emits `constraints.json`, `statistics.json`, `constraint_violations.json`. Lab 6 Task 1 is built on that path now.

**Constraint on that path:** `publish_cloudwatch_metrics` must be `Disabled`; `Enabled` fails with *"CloudWatch publishing is available only for jobs from MonitoringSchedules"*. Students publish their own metric from the violations JSON.

**Implication beyond Lab 6:** treat any AWS API this course depends on as possibly closed to new accounts, regardless of what documentation says. Verify on the reference account only after remembering it is *not* new — it has usage history the students' accounts will not have.

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

- The live repo `/Users/scott1/northstar-ai-platform` is authoritative; `Sample Solutions/` is a copy kept in sync.
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
