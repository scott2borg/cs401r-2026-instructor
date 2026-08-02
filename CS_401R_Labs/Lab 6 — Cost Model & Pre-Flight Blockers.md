---
created: 2026-07-30
tags: [CS401R, lab-6, cost, blockers]
status: cost model complete; two blockers confirmed in code, not yet fixed
purpose: Close the "Model Monitor has never been costed" gap and record pre-flight defects found before the Lab 6 AWS run
---

# Lab 6 — Cost Model & Pre-Flight Blockers

Produced from the Lab 5 → Lab 6 handoff, first moves #1 and #2. All pricing pulled live from the AWS Pricing API on 2026-07-30, account `711457211658`, `us-east-1`, profile `terraform-user`. No AWS resources were created; this session's spend is **$0.00**.

---

## 1. Model Monitor cost model (the gap the handoff flagged)

### Verified unit prices

| Item | Price | Source |
|---|---|---|
| `ml.m5.large` endpoint hosting | **$0.115 / hr** | Pricing API `USE1-Host:ml.m5.large` |
| `ml.m5.large` **processing** (Model Monitor jobs) | **$0.115 / hr** | Pricing API `USE1-Processing:ml.m5.large` |
| `ml.m5.xlarge` processing | $0.230 / hr | Pricing API |
| `ml.t3.medium` processing | $0.050 / hr | Pricing API |
| CloudWatch alarm, standard resolution | $0.10 / alarm-month | `CW:AlarmMonitorUsage` |
| CloudWatch custom metric | $0.30 / metric-month (first 10k) | `CW:MetricMonitorUsage` |
| CloudWatch dashboard | free up to 3, then $3 / mo | AWS free tier |

**Headline: a Model Monitor processing instance costs exactly the same per hour as the endpoint it monitors.** Model Monitor roughly doubles the marginal cost of every hour the lab is live — but only for the minutes each job actually runs, so in practice it adds ~13% to the endpoint bill, not 100%.

### Scenarios (per student, 8-minute job duration assumed)

| Scenario | Endpoint | Processing | Alarms | Custom metric | **Total** |
|---|---|---|---|---|---|
| **A — disciplined**: 3 h live, baseline + 2 scheduled jobs | $0.35 | $0.05 | $0.00 | $0.30 | **$0.69** |
| **B — leaves overnight**: 14 h, 15 jobs | $1.61 | $0.23 | $0.01 | $0.30 | **$2.15** |
| **C — forgets 3 days**: 72 h, 73 jobs | $8.28 | $1.12 | $0.06 | $0.30 | **$9.76** |
| **D — forgets a week**: 168 h, 169 jobs | $19.32 | $2.59 | $0.14 | $0.30 | **$22.35** |

Class of 30, all disciplined: **~$21**. All leaving it overnight once: **~$65**.

> **The 8-minute job duration is the one number in this table that is not verified.** Realistic range is 5–12 min for a dataset this small, which moves the totals by roughly ±40% on the processing column only — it does not change any conclusion below. Pin it during the AWS run.

### The finding that matters

**A single student who forgets to tear down breaches the $10/month budget alarm in 74 hours — 3.1 days.** Lab 6 is assigned Thu Nov 12 and due Sat Nov 28. That is a 16-day window in which any one of 30 students can quietly exceed the entire account's budget alarm on their own.

Two structural reasons Lab 6 is worse than Lab 5 here, both new:

1. **Lab 5's live window was 60 minutes. Lab 6's is open-ended by design** — the lab asks students to leave the endpoint running long enough to generate baseline statistics and let a monitoring schedule fire.
2. **The monitoring schedule keeps spawning billable processing jobs on its own cadence**, independent of whether the student is still working. Deleting the endpoint does not delete the schedule.

`scripts/teardown-lab5.sh` does not delete monitoring schedules. **Lab 6 needs its own teardown script and it is not optional** — it is the difference between a $21 class and a $600 one.

### Recommendation

Run the monitoring schedule **hourly, not daily**, and require students to tear down within the same working session. An hourly schedule gets a student to a graded artifact in ~2 hours; a daily schedule forces a 24-hour billing window on every student and multiplies the class cost by roughly 8x for no pedagogical gain.

---

## 2. Blocker #1 — the `ModelMonitor` IAM role cannot run a Model Monitor job

The handoff states the role "exists since Lab 2 — Lab 6 Task 1 needs it." Two corrections:

**It does not exist in the account.** `aws iam list-roles` returns zero roles matching `northstar` or `Monitor`. The Terraform stack was destroyed after the Lab 5 run, so all three platform roles exist only in code (`infrastructure/modules/iam/main.tf`). That is expected and fine — but "exists" was the wrong word and a TA reading the handoff would go looking for it.

**More seriously, the role as written cannot execute a Model Monitor job.** The code comment is explicit about the design intent:

```
# Can:    publish CloudWatch metrics and alarms, manage monitoring
#         schedules, read artifacts/
# Cannot: write to S3 at all, invoke endpoints, modify models
#
# This is the most tightly scoped role in the platform. It observes;
# it never mutates. Lab 6 builds on it.
```

The policy has exactly four statements: `CloudWatchMetrics`, `ModelMonitoringSchedules`, `S3ArtifactsReadOnly`, `CloudWatchLogs`. A SageMaker Model Monitor execution needs at minimum:

| Required | Present? | Consequence if missing |
|---|---|---|
| `s3:PutObject` to the monitoring output prefix | ❌ **no S3 write at all** | Baseline job and every monitoring execution fail — they exist to write `statistics.json` and `constraint_violations.json` |
| `s3:GetObject` on the **data-capture** prefix | ❌ scoped to `artifacts/*` only | Job cannot read the captured inference data it is supposed to analyse |
| `ecr:GetAuthorizationToken` + `BatchGetImage` + `GetDownloadUrlForLayer` | ❌ **absent from this role** (present on `ml_engineer`, a different role) | Cannot pull the `model-monitor-analyzer` container image; job fails before it starts |
| `sagemaker:CreateProcessingJob` | ❌ only `DescribeProcessingJob` | Cannot launch the execution |

The role's stated design principle — "it observes; it never mutates" — is architecturally sound for a human observer role and **wrong for a service execution role.** Model Monitor is a batch job that must write its own findings. These are two different things that got the same name.

**Impact:** Task 1's 10 points for "SageMaker Model Monitor configured" are unachievable as the platform currently stands. Worse, the failure mode is expensive: the schedule is accepted, the endpoint bills, and the first failed execution surfaces ~1 hour later as an opaque `ProcessingJobStatus: Failed`.

**Fix:** either add a distinct execution role (`northstar-dev-ModelMonitorExecution`) with the four capabilities above, or widen this one and update the comment that promises it never writes. Recommend a **separate execution role** — it keeps the least-privilege observer role honest and gives Lab 6 a genuine teaching moment about the difference between an observer identity and a service execution identity.

---

## 3. Blocker #2 — Lab 5 deploys endpoints with no data capture

`grep -rn "DataCapture\|data_capture\|CaptureOption" deployment/ scripts/ docs/` returns **nothing**. Neither `canary_deploy_realtime.py` (the verified path) nor `endpoint-config-canary.json` enables `DataCaptureConfig`.

SageMaker Model Monitor **data quality monitoring reads captured inference data from S3.** With capture disabled there is nothing to read. A student following Lab 5 exactly and then attempting Lab 6 Task 1 gets a monitoring schedule that produces no violations report — and it will look like their configuration is wrong when the actual cause is upstream, in the previous lab.

The sharp edge: **endpoint configs are immutable.** Capture cannot be switched on for an already-deployed endpoint. Fixing this requires creating a new endpoint config and calling `update-endpoint` — a 3 min 47 s operation per Lab 5's measured numbers, plus a full rebuild if the student has already torn down.

**Recommendation:** add `DataCaptureConfig` to Lab 5 Task 1's endpoint config, with a one-line note that it costs nothing extra beyond S3 storage and exists so Lab 6 has data to monitor. This is the cleanest fix — it removes a cross-lab trap entirely rather than documenting it. It does mean re-verifying Lab 5's deploy path on AWS, since Lab 5's verified run did not include capture.

---

## 4. Smaller corrections to the handoff

- **`monitoring/` is not empty.** `monitoring/alerts/`, `monitoring/dashboards/` and `monitoring/runbooks/` all exist as empty directories. The handoff says neither exists; the files inside are what is missing, not the directories.
- The `runbooks/` directory exists but the spec sends Task 2, 4 and 5 deliverables to `docs/lab6-runbook.md`. Task 3 alone writes to `monitoring/alerts/`. Worth deciding whether `monitoring/runbooks/` is dead weight or where the runbooks actually belong — right now the repo structure and the spec disagree.

---

## 5. The p95 SLO question (handoff open thread)

Measured p95 is ~4.15 ms against a 200 ms target — a **48x margin**. The SLO is free and teaches nothing.

**Recommendation: tighten the latency SLO to p95 < 20 ms (`ModelLatency` ≤ `20000`) and leave the alert threshold at 200 ms.** This is the right answer rather than adding a load-test requirement, for three reasons:

1. It preserves the teaching point that **an SLO target and an alert threshold are different numbers with different jobs** — the SLO is a promise measured over a month, the alarm is a page-worthy emergency. Students routinely conflate these.
2. A 20 ms target against a 4.15 ms steady state is still a healthy ~5x margin, but it is now a margin the **~24,000 µs cold start actually violates** — so a student's error budget gets consumed by their own deployments, which is exactly the real-world lesson.
3. A load-test requirement adds invocation volume, wall-clock time and cost to a lab that is already the most expensive in the course. Rejected on cost grounds.

---

## 5b. AWS RUN 2026-07-31 — results

Total spend: **~$0.02.** No endpoint was ever created. All-region sweep after the run: zero endpoints, zero running jobs, zero schedules, zero notebooks.

### Both blockers closed by evidence

**Blocker 1 — proven real, then proven fixed.** `iam simulate-principal-policy` against the deployed roles:

| Action | `ModelMonitor` (observer) | `ModelMonitorExecution` |
|---|---|---|
| `s3:GetObject` on `datacapture/*` | **DENY** | ALLOW |
| `s3:PutObject` on `monitoring/*` | **DENY** | ALLOW |
| `ecr:GetAuthorizationToken` | **DENY** | ALLOW |
| `ecr:BatchGetImage` | **DENY** | ALLOW |
| `s3:ListBucket`, `cloudwatch:PutMetricData`, `logs:PutLogEvents` | ALLOW | ALLOW |

The observer role was denied exactly the four capabilities predicted. Then a **real baseline job completed** using the execution role, writing `statistics.json` (151.7 KiB, 12 features, 1,377 rows) and `constraints.json` (2.5 KiB) to `monitoring/baseline/`. Trust policy, ECR pull, S3 read and S3 write are all confirmed in a live run, not simulated.

### THE COURSE-LEVEL FINDING — SageMaker quotas are 0

The first baseline attempt failed instantly:

```
ResourceLimitExceeded: The account-level service limit
'ml.m5.large for processing job usage' is 0 Instances
```

#### ⚠️ First reading was partly wrong — corrected below

My initial audit used `aws service-quotas list-service-quotas --query ...`. **The CLI applies `--query` per pagination page**, so a filtered list silently returns partial results. I read "every training quota is 0" off that truncated output and it was **false**. Re-audited with a boto3 paginator over all 2,004 quotas. Corrected figures:

| Quota (us-east-1) | **AWS default** | **This account (applied)** |
|---|---|---|
| `ml.m5.large` **processing** | **0** | 4 ← raised by my request this session |
| `ml.t3.medium` / `large` / `xlarge` processing | **4 / 4 / 2** | 10 / 10 / 5 |
| `ml.m5.large` **endpoint** | **0** | 8 |
| `ml.m5.large` **on-demand training** | **0** | **15** |
| `ml.m5.large` **spot** training | 4 | 10 |
| Processing types with default > 0 | **3 of 126** (all `ml.t3.*`) | 17 |
| On-demand training types with default > 0 | **0** | 76 |

**Retraction 1: "every training job quota is 0" is wrong.** On-demand training on this account is **15**, not 0. The Labs 2→5 end-to-end run is **not** quota-blocked here and could be executed today.

**Retraction 2: "endpoint quota is 4" understated it** — it is 8, and more importantly its *default* is 0.

### The actual finding, restated correctly

The pattern is not "processing is special." It is:

> **Every on-demand SageMaker quota this course depends on has an AWS default of 0. This account works only because it has accumulated applied increases through usage history.**

AWS raises an account's applied quotas as it demonstrates usage. `711457211658` has been running this project for months, so it now has endpoint 8, training 15, processing 4. A **brand-new student account starts at 0 for all three on-demand families** and has non-zero default quota *only* for `ml.t3.{medium,large,xlarge}` processing and spot training.

That makes the exposure **wider than Lab 6**. On a fresh account, Lab 5's `ml.m5.large` endpoint has a default quota of 0 too — so the risk covers Lab 5 as much as Lab 6, and nobody noticed because every run has happened on this seasoned account.

**Important caveat — this is not yet proven.** `get-aws-default-service-quota` returns AWS's documented default; it does not prove what a newly created account is actually granted, because AWS frequently auto-approves the first request. **The only way to know is to create one throwaway account and read its applied quotas.** That is cheap and it should happen before the term starts. Until then, treat "students will have 0" as a strong hypothesis, not a verified fact.

What *is* verified beyond doubt: `CreateProcessingJob` on `ml.m5.large` was **rejected outright** by this account earlier today with `ResourceLimitExceeded ... is 0 Instances`. The zero was real.

**I changed account state.** Filing `L-8541302D` took `ml.m5.large` processing from 0 → 4, so **this account no longer reproduces the original failure.** The request still shows `CASE_OPENED` while the value is already applied.

### Measured numbers (replace the estimates in §1)

| Instance | Result | Wall clock | Billed instance time | Cost |
|---|---|---|---|---|
| `ml.t3.medium` (4 GB) | **FAILED — out of memory** | 13 m 43 s | 13.7 min @ $0.05/hr | $0.011 |
| `ml.t3.large` (8 GB) | **Completed** | 7 m 36 s (SDK) | **5 m 46 s** @ $0.10/hr | $0.010 |

**`ml.t3.medium` cannot run Model Monitor.** The analyzer is a Spark container and OOMs on a 1,377-row CSV — and takes nearly 14 minutes to say so, with a message that blames the data rather than the instance ("use an instance type with more memory, or reduce the size of job data"). A student on the cheapest available instance burns 14 minutes and gets pointed at the wrong cause.

**`ml.t3.large` is the floor**, and given the quota table it is also effectively the only choice. My §1 cost model assumed `ml.m5.large` at $0.115/hr for 8 min; the reality is `ml.t3.large` at $0.10/hr for 5 m 46 s — **about 40% cheaper per job than modelled.** The §1 scenario totals are therefore slightly conservative, and no conclusion in §1 changes.

### Irony worth teaching

Lab 5's trap #4 is "burstable instances cannot be auto-scaling targets." Lab 6's trap is the exact inverse: **burstable is the only instance class with any processing quota at all.** Same instance family, opposite lesson, one lab apart.

### Still unverified — needs an endpoint

The endpoint half did not run: there is no model artifact and no Model Package Group in the account, so it would require rebuilding the full Lab 3→5 chain (which *is* the Labs 2→5 integration run). Open:

- Data capture S3 layout and lag
- Monitoring schedule cron syntax and first-execution lag
- Whether a schedule outlives a deleted endpoint and keeps billing (drives teardown ordering)
- `scripts/teardown-lab6.sh` still unwritten

### Minor

`data/northstar-raw-sample.csv` yields 1,377 feature rows from 1,376 unique `customer_id` values — there is one NaN `customer_id` in the raw sample, which becomes a `"nan"` customer in the feature set. Cosmetic for Lab 6, but it is in the shipped sample data.

## 6. Unverified assertions now sitting in the Lab 6 spec

`Lab_6--Monitoring & Reliability.md` was extracted and audited 2026-07-30. **No part of Lab 6 has been executed on AWS.** Everything below is asserted from code review, the AWS Pricing API, or the boto3 API model — never from a live run. Confirm each during the reference run:

- **Model Monitor job duration** (assumed 8 min, range 5–12) — every cost figure depends on it
- Whether enabling data capture changes Lab 5's measured 6 min 47 s `create-endpoint` time
- That captured objects land at the documented `<endpoint>/<variant>/<yyyy>/<mm>/<dd>/<hh>/` path
- That the new `ModelMonitorExecution` policy is **sufficient** — it validates and is scoped from documented requirements, but `terraform validate` has never caught a single one of this project's 17 AWS defects
- Monitoring schedule cron syntax, and the real lag between creating a schedule and its first execution
- Whether a schedule pointed at a deleted endpoint still launches billable jobs (assumed yes; drives the teardown ordering)

Verified without spend, so these are **not** open:
- All unit prices (Pricing API, live)
- `DataCaptureConfig` field names and the `Input`/`Output` enum (validated against the boto3 service model)
- `terraform validate` passes on the dev environment; `terraform fmt` clean
- `preflight-lab6.sh` runs against the live account and exits correctly when no endpoint exists

## Status and next step

Costing is closed. Two blockers are confirmed in code and neither has been fixed. **Both should be fixed before the Lab 6 AWS run**, not discovered during it — Blocker #1 in particular fails an hour into a billing window.

Sequence from here:
1. Add the Model Monitor execution role to `modules/iam/`
2. Add `DataCaptureConfig` to the Lab 5 endpoint config
3. Write `Lab_6--Monitoring & Reliability.md` as a standalone spec, auditing while extracting
4. Then the AWS run — redeploy, capture, baseline, schedule, custom metric, dashboard, export, tear down
5. Rewrite the Lab 6 TA guide against the real run
