# Lab 6: Monitoring & Reliability

**Assigned:** Thu Nov 12 | **Due:** Sat Nov 28, midnight
**Chapters:** *Metrics, Benchmarks & Guardrails*, *Monitoring & Observability*, *Reliability Engineering*
**Builds on:** Labs 1–5 — instruments the production system deployed in Lab 5

## Objective

A deployed model with no monitoring is a liability. This lab instruments the NorthStar platform end-to-end: five monitoring layers, a full alert architecture, SLOs with error budgets, and operational runbooks for failure scenarios. After this lab, your platform can fail gracefully and recover fast.

## Starter Kit

**None.** Labs 5–7 have no starter kit. Lab 6 instruments what Lab 5 deployed, using the IAM roles created in Lab 2 and the endpoint created in Lab 5.

## Read This First — Cost

**Lab 6 is the most expensive lab in this course.** Not because any one resource is costly, but because it is the only lab that asks you to leave an hourly-billing resource running while you wait for something to happen.

Lab 5 taught you that a SageMaker endpoint bills from `InService` until deletion. Lab 6 re-creates that endpoint *and* adds a second billing source:

| Resource | Rate | Notes |
|---|---|---|
| Endpoint — `ml.t2.medium` | **$0.056 / hr** | Where Lab 5 starts you |
| Endpoint — `ml.m5.large` | **$0.115 / hr** | Only if your Lab 5 quota increase came through |
| Model Monitor processing job | **$0.10 / hr** | `ml.t3.large`, billed per second, only while a job runs |
| CloudWatch alarm | $0.10 / alarm-month | Prorated hourly; 6 alerts ≈ $0.60/mo if left |
| CloudWatch custom metric | $0.30 / metric-month | **Not prorated** — you pay for the month |
| CloudWatch dashboard | free (first 3) | Then $3/mo |

A monitoring job costs more per hour than a `t2.medium` endpoint, but it only runs for minutes, so in practice it adds roughly 15% to your bill. **Measured 2026-07-31: a baseline job on `ml.t3.large` took 5 min 46 s of billed instance time and cost $0.010.**

What this actually costs you — the column that applies depends on which instance Lab 5 left you on:

| If you… | On `ml.t2.medium` | On `ml.m5.large` |
|---|---|---|
| Work in one focused session and tear down (3 h) | **$0.50** | **$0.68** |
| Leave it running overnight (14 h) | **$1.24** | **$2.07** |
| Forget for three days (72 h) | **$5.09** | **$9.34** |
| Forget for a week (168 h) | **$11.47** | **$21.38** |

Burn rate with the endpoint live and one analysis run per hour: **$0.0664/hr** on `t2.medium`, **$0.1254/hr** on `m5.large`.

> **A single forgotten Lab 6 endpoint breaches the entire course account's $10/month budget alarm in 146 hours (6.1 days) on `t2.medium`, or 77 hours (3.2 days) on `m5.large`.** You have a 16-day submission window, so either number is reachable by simply forgetting. Do the lab in one sitting and tear it down.

**The part that is new and catches people:** each analyzer run is a *separate* billable instance on top of the endpoint. The endpoint bills continuously; every analysis you launch adds ~6 minutes of `ml.t3.large` on top. Two or three runs is normal while you get the inputs right.

If you automate the analysis on a timer (EventBridge, a cron job, a loop), **that timer keeps launching billable jobs whether or not you are still working, and whether or not the endpoint still exists.** `scripts/teardown-lab5.sh` knows nothing about monitoring. **Use `scripts/teardown-lab6.sh`** — it stops in-flight processing jobs and removes any schedule before deleting the endpoint.

## Prerequisites — do this before Task 1

Three things must be true before you run the analyzer. Two of them fail *expensively* and *silently* — a misconfigured run burns 6-14 minutes of instance time before telling you anything useful, and the endpoint bills the whole while.

Run the pre-flight check:

```bash
bash scripts/preflight-lab6.sh
```

### 0. Use `ml.t3.large` for every Model Monitor job — not `ml.m5.large`, not `ml.t3.medium`

This is not a cost-tuning suggestion. It is the only instance type that both has quota and actually works.

**Your AWS account's processing-job quota is 0 for every non-burstable instance type.** Not low — zero. `ml.m5.large`, `ml.c5.*`, `ml.m4.*`, `ml.r5.*` and every other general-purpose family will reject the job immediately:

```
ResourceLimitExceeded: The account-level service limit
'ml.m5.large for processing job usage' is 0 Instances
```

Of the 126 processing instance types, exactly **three** have a non-zero AWS default, and all three are burstable: `ml.t3.medium` (4), `ml.t3.large` (4), `ml.t3.xlarge` (2). Verified against `get-aws-default-service-quota` on 2026-07-31.

Check your own before you start — these are the *defaults*, and an account accrues higher applied limits as it is used:

```bash
aws service-quotas get-service-quota --service-code sagemaker \
  --quota-code L-C076FA77 --query 'Quota.Value' --output text   # ml.t3.large processing
```

**And `ml.t3.medium` — the cheapest — does not work.** The Model Monitor analyzer is a Spark container and exhausts its 4 GB on a dataset of barely a thousand rows. Worse, it takes **13 min 43 s** to fail, and the error blames your data rather than the instance:

```
ClientError: Please use an instance type with more memory,
or reduce the size of job data processed on an instance.
```

That message will send you off shrinking your dataset, which is not the problem. **`ml.t3.large` (8 GB) is the floor.** Measured: baseline job completed in 5 min 46 s of billed instance time.

> **Note the inversion from Lab 5.** Lab 5's trap was that *burstable instances cannot be auto-scaling targets* — you were forced off `ml.t3.*` onto `ml.m5.large`. In Lab 6 the constraint runs exactly the other way: burstable is the only class with any default processing quota at all. Same instance family, opposite conclusion, one lab apart.
>
> **Endpoint quota, training quota and processing quota are three completely separate numbers**, and having one tells you nothing about the others. `ml.m5.large` has a *different* quota for each. The AWS default for all three on-demand families is 0; accounts accumulate higher applied limits through usage, which is why an endpoint that deployed fine in Lab 5 does not mean a processing job will run in Lab 6. Always check the specific quota for the specific job type.

If you want `ml.m5.large` for processing, you must file a Service Quotas increase (`L-8541302D`) and wait on an AWS Support case. **Do not put that on the critical path for this lab** — the lab is designed to complete on `ml.t3.large` with no quota request.

### 1. Your endpoint must have data capture enabled

Model Monitor analyses inference data that the endpoint captured to S3. **No capture means nothing to analyse**, and the failure is not obvious: the job is accepted, runs, and produces an empty or schema-confused report rather than saying "there was no input".

**Endpoint configs are immutable.** Capture cannot be switched on for a running endpoint. If your endpoint was deployed without it, you must create a new endpoint config and call `update-endpoint` (~3 min 47 s, zero downtime):

```bash
python deployment/configs/canary_deploy_realtime.py \
  --model-package-arn <arn> --role-arn <arn>
```

Capture lands under `s3://<bucket>/datacapture/<endpoint>/<variant>/<yyyy>/<mm>/<dd>/<hh>/`. It is written **asynchronously** and lags several minutes behind your first invocation. Baselining against an empty prefix fails with a confusing schema error, not a helpful "no input" error — so invoke the endpoint, wait, and confirm objects exist before you baseline.

### 2. Use the ModelMonitorExecution role, not the ModelMonitor role

The platform has two similarly named roles and they are **not interchangeable**:

| Role | What it is | Use for |
|---|---|---|
| `northstar-dev-ModelMonitor` | **Observer** identity. Read-only by design: no S3 write, no ECR pull. | Humans and automation that watch the platform |
| `northstar-dev-ModelMonitorExecution` | **Service execution** identity. Writes reports, pulls the analyzer container. | **Model Monitor schedules — this lab** |

A monitoring execution is a batch job whose entire purpose is to *write* its findings (`statistics.json`, `constraint_violations.json`) and it cannot start without pulling its container from ECR. Hand it the observer role and the job fails several minutes in as an opaque `ProcessingJobStatus: Failed`.

This distinction — an identity that observes versus an identity that executes — is the design point, not a technicality. Note it in your Task 3 deliverable.

## Tasks

### Task 1 — Five-Layer Monitoring Implementation (35 points)

Implement monitoring across all five layers for the NorthStar churn model. All layers must surface in a single **CloudWatch Dashboard** named `NorthStar-AI-Platform`.

| Layer | What to Monitor | Tool | Threshold |
|-------|----------------|------|-----------|
| **Infrastructure** | SageMaker endpoint CPU, memory | CloudWatch Metrics | CPU > 80% → alert |
| **Pipeline** | Glue job success/failure rate | CloudWatch Events | Any failure → P2 alert |
| **Model** | Data drift (PSI on top 3 features) | Model Monitor analyzer, run as a processing job | PSI > 0.2 → alert (metric published by you) |
| **Application** | Inference latency p50, p95, p99 | CloudWatch Metrics | p95 > 200 ms → alert (`ModelLatency` threshold `200000` — see note) |
| **Business** | Daily churn alert volume (proxy) | CloudWatch Custom Metric | Volume drop >30% vs. 7-day avg → alert |

> **`ModelLatency` is emitted in MICROSECONDS.** Every latency threshold in this lab is written in milliseconds because that is how humans and SLAs talk, but CloudWatch does not. 200 ms is `200000`; 500 ms is `500000`. Writing `200` builds an alarm that trips at 0.2 ms — well below a healthy endpoint's normal latency, measured at roughly **4,100 µs (4.1 ms)** on `ml.m5.large` in Lab 5. That alarm sits in `ALARM` permanently and any automation wired to it fires against a healthy system. Verified on AWS 2026-07-30. Check the `Unit` field in `get-metric-statistics` output before setting any threshold.
>
> Related: the **first invocation after a deploy runs ~6x slower** (~24,000 µs measured) as the container warms. An alarm with `EvaluationPeriods: 1` will trip on your own deployment.

> ### ⚠️ SageMaker Model Monitor **schedules** cannot be created on a new AWS account
>
> Both `CreateMonitoringSchedule` and `CreateDataQualityJobDefinition` now return:
>
> ```
> ValidationException: This operation is in maintenance mode and is not
> available to new customers. Existing customers are unaffected.
> ```
>
> This is **not** a quota, a permission, or a mistake in your configuration. AWS has closed the API to accounts that were not already using it, and every account in this course is new. Verified on AWS 2026-07-31. Do not spend time trying to work around it — you cannot.
>
> **What still works is everything that matters.** `CreateProcessingJob` is unaffected and the `model-monitor-analyzer` container runs normally. You will run the analyzer yourself as a processing job instead of having SageMaker run it for you on a schedule. You lose the managed cron; you keep the entire analysis.
>
> This is a better exercise than the one it replaces. A managed schedule is a checkbox. Invoking the analyzer directly means you have to understand what it actually consumes — captured data, a baseline, a dataset format — and what it emits.

**Requirements:**
- A **baseline** generated from your training feature set with `suggest_baseline`, on **`ml.t3.large`**, using the `ModelMonitorExecution` role. Commit `statistics.json` and `constraints.json`.
- A **monitoring analysis run** — the analyzer executed as a processing job against your captured inference data, producing `constraint_violations.json`. Commit it.
- At least one custom CloudWatch metric pushed programmatically (business layer)
- Dashboard JSON exported and committed to `monitoring/dashboards/northstar-dashboard.json`

**Running the analyzer manually.** Submit a processing job with image `156813124566.dkr.ecr.us-east-1.amazonaws.com/sagemaker-model-monitor-analyzer` and these environment variables:

```
dataset_source              /opt/ml/processing/input/endpoint
dataset_format              {"sagemakerCaptureJson":{"captureIndexNames":["endpointInput"]}}
output_path                 /opt/ml/processing/output
baseline_constraints        /opt/ml/processing/baseline/constraints/constraints.json
baseline_statistics         /opt/ml/processing/baseline/stats/statistics.json
analysis_type               DATA_QUALITY
publish_cloudwatch_metrics  Disabled
```

> **`publish_cloudwatch_metrics` must be `Disabled`.** Setting it to `Enabled` fails the job after roughly eight minutes with `AlgorithmError: CloudWatch publishing is available only for jobs from MonitoringSchedules.` — and since you cannot create a schedule, you cannot enable it. **This is why the model layer of your dashboard is your own job:** parse `constraint_violations.json` and publish your own metric with `put-metric-data`. That is the same work the managed schedule was doing for you.

Mount three inputs: your capture prefix to `/opt/ml/processing/input/endpoint`, `constraints.json` to `/opt/ml/processing/baseline/constraints`, and `statistics.json` to `/opt/ml/processing/baseline/stats`.

**Capture is partitioned per variant** — `datacapture/<endpoint>/<variant>/<yyyy>/<mm>/<dd>/<hh>/`. If you ran a two-variant canary in Lab 5, point the analyzer at one variant's prefix, and say in your write-up which one and why.

Reference numbers from a verified run: a baseline over 1,200 customers profiled 11 features (`days_since_last_purchase` mean 58.80, `completeness` 1.0, `inferred_type` `Fractional`); the analysis run consumed 174 captured records and returned `"violations": []`. Your numbers will differ; the *shape* of the output should not.

**Rubric:**

| Item | Points | Pass Criteria |
|------|--------|---------------|
| All 5 layers visible in CloudWatch Dashboard | 15 | TA can open the dashboard and see at least one metric per layer |
| Model Monitor baseline **and** analysis run | 10 | `statistics.json` + `constraints.json` from a baseline job, **and** a `constraint_violations.json` from an analyzer processing job over captured data. A schedule is NOT required and cannot be created — see the note above. |
| Custom metric pushed for business layer | 5 | `aws cloudwatch get-metric-statistics` returns data for the custom metric |
| Dashboard JSON committed | 5 | `monitoring/dashboards/northstar-dashboard.json` is valid CloudWatch Dashboard JSON |

> **Grading standard carried forward from Lab 5:** prefer *observed* evidence over configuration screenshots. A baseline statistics file with real numbers in it beats a console capture of a schedule that has never executed.

### Task 2 — Drift Detection Plan (15 points)

Write a drift detection plan for the NorthStar churn model in `docs/lab6-runbook.md`.

**Required content:**
1. **Drift types most likely for this domain**: Which of (data drift, concept drift, model degradation) are most likely for customer churn prediction in retail? Justify with reference to NorthStar's business context (seasonal promotions, catalog changes, economic shifts).
2. **Statistical tests chosen**: For each feature you monitor, specify the test (PSI, KS, or JSD), the baseline window, and the threshold.
3. **Concept drift detection**: The churn label is only observable after the full 90-day holdout window has elapsed, so ground truth for a prediction made today does not exist until three months from now. How will you detect concept drift in the meantime? Propose a proxy signal and state its lag.

**Rubric:**

| Item | Points | Pass Criteria |
|------|--------|---------------|
| Drift type analysis references NorthStar specifics | 5 | Mentions at least one NorthStar-specific driver (e.g., holiday promotions, catalog refresh) |
| Statistical test specified per feature with threshold | 5 | At least 3 features have named tests and numeric thresholds |
| Concept drift proxy proposed and reasoned | 5 | Proposes a specific observable signal (e.g., model score distribution shift, early return rate) |

### Task 3 — Alert Architecture (15 points)

Define the full alert set for the NorthStar churn model and offer generation system in `monitoring/alerts/`.

**Required deliverable:** An alert specification document or CloudWatch Alarms Terraform config covering:

- At least **6 alerts** with assigned P0–P3 severity tiers
- Escalation path for each tier (P0: wake on-call + page manager; P1: on-call; P2: Slack + ticket; P3: ticket only)
- At least **1 suppression rule** for a realistic alert-storm scenario (e.g., "suppress P2 model drift alerts during scheduled retraining window")

**Rubric:**

| Item | Points | Pass Criteria |
|------|--------|---------------|
| ≥6 alerts with severity tiers | 8 | All 6 alerts have P-tier assigned; distribution across P0–P3 is reasonable |
| Escalation paths documented | 4 | Each severity tier has a named escalation action |
| ≥1 suppression rule | 3 | Suppression rule names the condition and the alerts it suppresses |

### Task 4 — SLO Design (15 points)

Define SLOs for the NorthStar churn prediction model in `docs/lab6-runbook.md`.

**Required SLOs** (all four):

| SLO | Target | SLI (Good Events / Total Events) | Error Budget | Deployment Freeze Trigger |
|-----|--------|----------------------------------|-------------|--------------------------|
| Availability | 99.5% | Successful predictions / total requests | | |
| Latency (p95) | **< 20 ms** (`ModelLatency` ≤ `20000`) | Requests completing < 20 ms / total requests | | |
| Prediction Quality | Recall@10% ≥ 0.35 on weekly sample | Weekly sample passing threshold / total weekly samples | | |
| Fairness | Recall gap across loyalty tiers ≤ 10pp | Weeks within fairness threshold / total weeks | | |

Fill in the Error Budget (in minutes/month or events/month) and the Deployment Freeze Trigger for each SLO.

> **Why the latency SLO is 20 ms while the Task 1 alert fires at 200 ms.** These are different numbers doing different jobs, and conflating them is the most common SLO mistake in industry. An **SLO** is a promise measured over a month and spent down as an error budget. An **alert threshold** is the point at which you wake a human. Measured steady-state p95 on this endpoint is ~4.15 ms, so a 200 ms SLO would be met 48x over — free, unbreachable, and it would teach you nothing. At 20 ms you keep a healthy ~5x margin, but the ~24,000 µs cold start on every deployment *does* breach it. That is the intended lesson: your own deploys consume your error budget, which is precisely why error budgets govern deployment freezes.

**Rubric:**

| Item | Points | Pass Criteria |
|------|--------|---------------|
| All 4 SLOs complete with error budgets | 10 | Each row has a numeric error budget |
| Deployment freeze triggers are actionable | 5 | Each trigger is a specific condition (not "if SLO is at risk") |

### Task 5 — Runbooks (20 points)

Write complete runbooks for **two** failure scenarios in `docs/lab6-runbook.md`. Choose from:
- A: Data drift detected (PSI > 0.2 on `days_since_last_purchase`)
- B: Inference latency spike (p95 > 500 ms — `ModelLatency` > `500000` — for > 5 minutes)
- C: Feature Store unavailable (online store read failures)
- D: Fairness guardrail breach (recall gap exceeds 10pp between loyalty tiers)

**Each runbook must follow this structure:**

```markdown
## Runbook: [Failure Mode Name]

### Detection
- Alert name and threshold that triggers this runbook
- Secondary signals that confirm the failure

### Triage (< 5 minutes)
- Step 1: [specific action]
- Step 2: [specific action]

### Containment Options
- Option A: [what it does, when to choose it]
- Option B: [what it does, when to choose it — e.g., graceful degradation fallback]

### Escalation
- Trigger for escalating beyond on-call: [specific condition]
- Who is paged: [role, not person]
- SLA for response: [minutes]

### Resolution Verification
- How do you confirm the issue is resolved?
- What metric must return to normal range?

### Post-Incident Actions
- Within 24 hours: [specific action]
- Postmortem required: [yes/no — state the condition that requires one]
```

**Rubric:**

| Item | Points | Pass Criteria |
|------|--------|---------------|
| Both runbooks complete with all sections | 10 | No section is "TBD" or empty |
| Containment options include a graceful degradation fallback | 6 | At least one option describes what the system does when it cannot recover immediately |
| Resolution verification is observable | 4 | Names a specific metric or CloudWatch alarm state, not "the system feels normal" |

## Traps Already Mapped — do not rediscover

These cost previous runs of this course real time and real money. They are not hypothetical.

1. **Model Monitor SCHEDULES cannot be created on a new AWS account.** `CreateMonitoringSchedule` and `CreateDataQualityJobDefinition` are both in maintenance mode and closed to new customers. No quota or permission fixes it. Run the analyzer as a processing job instead — the container is unaffected. Verified 2026-07-31.
2. **`publish_cloudwatch_metrics` must be `Disabled`** on a manually-run analyzer. `Enabled` fails after ~8 minutes with *"CloudWatch publishing is available only for jobs from MonitoringSchedules"*, and you cannot create a schedule.
3. **Processing-job quota defaults to 0 for every non-burstable instance.** Not low — zero. Only `ml.t3.{medium,large,xlarge}` have a non-zero default. Endpoint, training and processing quotas are three separate numbers per instance type; one being fine says nothing about the others. Use `ml.t3.large`. Verified 2026-07-31.
4. **`ml.t3.medium` cannot run Model Monitor.** The analyzer is a Spark container and OOMs on ~1,400 rows after **13 min 43 s**, with an error that blames your data volume rather than the instance memory. `ml.t3.large` is the floor.
5. **`ModelLatency` is in microseconds.** 200 ms is `200000`. Every latency threshold in this lab depends on this. Verified both directions on AWS: `200000` stayed `OK`, `1000` alarmed in under a minute.
6. **Cold start is ~6x steady-state latency** (~24,000 µs vs ~4,150 µs). An alarm with `EvaluationPeriods: 1` trips on your own deployment.
7. **No data capture means no monitoring.** Model Monitor fails silently and late. Run `scripts/preflight-lab6.sh` first.
8. **`ModelMonitor` ≠ `ModelMonitorExecution`.** The observer role cannot run a monitoring job. Fails ~1 hour in, as an opaque `Failed`.
9. **Endpoint configs are immutable.** Data capture cannot be added to a running endpoint; you must roll a new config.
10. **Endpoints bill hourly until deleted.** Rolling back to weight 0 does not stop the charge.
11. **Monitoring schedules outlive endpoints** and keep launching billable jobs. Delete the schedule explicitly.
12. **Burstable instances cannot be auto-scaling targets** (carried from Lab 5).
13. **IAM propagation lag ~30 s** — re-running immediately shows the *old* error and looks like your fix failed.
14. **Non-ASCII in AWS-facing `description` fields** — some services reject em dashes, others accept them, so failures look arbitrary.
15. **Console Resource Explorer lags hours.** Verify against the live API.
16. **Auto-scaling does NOT orphan scalable targets** on endpoint deletion. Verified. Do not "fix" this non-problem.

## Teardown (required — read before you submit)

**Teardown is a gate, not a rubric line.** An endpoint or monitoring schedule still running after the deadline is a **10-point deduction**, applied on top of the gate.

```bash
bash scripts/teardown-lab6.sh
```

Order matters. Delete the **monitoring schedule first**, then the endpoint. A schedule left behind keeps launching processing jobs that bill on their own instances, and it will happily do so long after the endpoint it was pointed at is gone.

Teardown must remove, at minimum:
- Monitoring schedule(s)
- The endpoint, endpoint config, and both SageMaker Models
- CloudWatch alarms created for Task 1 and Task 3
- Any scaling target left from Lab 5

Then confirm with an independent all-region sweep, as in Labs 2–5. Custom CloudWatch metrics cannot be deleted — they expire after 15 months of no data. That is expected; the $0.30 metric-month charge is already accounted for.
