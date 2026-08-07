---
created: 2026-07-06
tags:
  - cs401r
  - sample-solution
  - lab6
  - monitoring
  - slos
  - cloudwatch
  - drift-detection
  - evidently
  - runbooks
lab_number: 6
status: rewritten for the Evidently path against a verified AWS run
rewritten: 2026-08-07
verified_on: 2026-08-07
account: "711457211658"
---

# Lab 6 — Monitoring & Reliability (Solution Notes)

**Rewritten 2026-08-07. The model-monitoring tool changed.** This lab no longer uses SageMaker Model Monitor. Model Monitor *schedules* cannot be created on a new AWS account, and every student account is new. The lab now uses **Evidently**, the open-source Python drift library, run inside a SageMaker Processing Job.

If you are holding a copy that tells students to create a monitoring schedule, or to run the `model-monitor-analyzer` container, discard it.

> **Terminology — you will be asked about this.** "Evidently" here means the open-source library at `docs.evidentlyai.com`, installed with `pip install evidently`. It is **not** Amazon CloudWatch Evidently, which was an unrelated AWS feature-flag and A/B-testing service that never did model monitoring and which **AWS shut down on 16 October 2025**. A student who finds AWS docs for "Evidently" has found the wrong thing. Expect this confusion at least once per section and correct it early.

---

## Reference Run

Endpoint, dashboard and latency figures executed against account `711457211658`, `us-east-1`, on **2026-07-31**. **Drift analysis re-verified on the Evidently path 2026-08-07.**

| What | Result |
|---|---|
| Endpoint | `ml.t2.medium`, two variants (champion/canary), data capture on |
| create-endpoint → InService | **7 min 03 s** |
| Observed traffic split at 9:1 | **174 champion / 26 canary** over 200 invocations |
| **Evidently drift job (`ml.t3.medium`)** | **1 min 59 s billed**, 10,000 baseline rows vs 800 captured |
| **Drift job cost** | **~$0.0017 per run** |
| Dashboard | 15 widgets, 5 layers, **zero** validation messages |
| Custom metrics | `ChurnAlertVolume`, `DriftDetected`, `DriftViolationCount` |
| Teardown | All 8 regions clean, verified independently |

`ModelLatency` re-confirmed as **microseconds**: champion averaged **3,793 µs** and **4,489 µs** across two hourly buckets. Cold start measured at **27,696 µs vs 4,628 µs** steady state — a **6.0x ratio**, independently reproducing the Lab 5 finding on a different instance type.

Reference implementation: `monitoring/evidently_drift.py`, `monitoring/run_evidently_job.py`, `monitoring/publish_metrics.py`, `monitoring/build_dashboard.py`, `monitoring/dashboards/northstar-dashboard.json`, `scripts/preflight-lab6.sh`, `scripts/teardown-lab6.sh`.

---

## Six findings that will hit students before anything else

### 1. Model Monitor SCHEDULES are closed to new AWS accounts — this is why the tool changed

```
ValidationException: This operation is in maintenance mode and is not
available to new customers. Existing customers are unaffected.
```

Returned by **both** `CreateMonitoringSchedule` and `CreateDataQualityJobDefinition`.

This is not a quota, not a permission, and not something the student did wrong. AWS closed the API to accounts that were not already using it. **Every student account is new, so no student can create a monitoring schedule.**

The lab routes around this entirely: Evidently has no managed control plane to be locked out of. `CreateProcessingJob` is unaffected and is all the lab needs.

**Grading:** a student who went looking for Model Monitor, hit this error, and documented it has learned the actual lesson — that a documented AWS capability can be closed to you with no recourse. Give credit for the finding. **Do not** tell them to "try again with the right permissions"; no permission fixes it.

If a student on an older account gets a Model Monitor schedule working and produces equivalent drift analysis, accept it. It is the same analysis by a different trigger. Do not require them to redo it in Evidently.

### 2. PSI and KS move in OPPOSITE directions — the highest-value defect in the lab

This replaces the old `publish_cloudwatch_metrics` finding and it is far more interesting.

Evidently returns a different *kind* of number depending on the test:

- **PSI** returns a distance **statistic**. It **rises** with drift. Drift means `value > threshold`.
- **KS** returns a **p-value**. It **falls** with drift. Drift means `value < threshold`.

Measured 2026-08-07 as mean shift increases (n_ref=2000, n_cur=800):

| mean shift | `ks` (p-value) | `psi` (statistic) |
|---|---|---|
| 0 | 0.272552 | 0.0235 |
| 2 | 0.000000 | 0.0472 |
| 5 | 0.000000 | 0.2757 |
| 15 | 0.000000 | 2.3176 |

**A student who loops over mixed tests with a single `if value > threshold` inverts KS and reports no drift on maximally drifted data** — `0.0` is not greater than `0.05`. Nothing errors. The report looks clean and the job exits 0.

**This is the thing to look for when grading Task 1.** It is a reasoning error, not an infrastructure error, so no amount of AWS debugging surfaces it. Check the comparison logic directly. A student who wrote a `drift_direction()`-style function that branches on the test type has understood something real about statistical tests, not just about AWS — say so. A student whose KS features *never* show drift across every run is displaying the symptom.

Note also the row at shift=2: **KS screams (p=0.000) while PSI is quiet (0.047, under a 0.2 threshold).** That disagreement is not a bug. KS is sensitive to sample size and detects any distributional difference; PSI measures magnitude and ignores commercially trivial shifts. A student who notices the two tests disagree and can explain why has earned a comment in Task 2.

### 3. `ml.t3.medium` is now sufficient — the old memory trap is gone

**Verified 2026-08-07: Evidently completed a 10,000-row baseline against 800 captured records in 1 min 59 s of billed time on `ml.t3.medium` (4 GB).**

This is a deliberate improvement over the retired path. Model Monitor's analyzer is a **Spark** container; on the same `ml.t3.medium` it exhausted 4 GB, took **13 min 43 s** to fail, and blamed the data rather than the instance (*"use an instance type with more memory, or reduce the size of job data"*). That message sent students off shrinking datasets that were never the problem. Evidently is pandas, and the trap no longer exists.

Practical consequences for grading:

- **`ml.t3.large` is no longer required.** A student using it is not wrong, just paying double for nothing. Worth a note, not a deduction.
- **No student should be filing a quota increase for this lab.** If one did, something upstream misled them — find out what.
- Processing-job quota still defaults to **0** for every non-burstable instance type. Of 126 processing instance types, exactly three have a non-zero AWS default, and all three are burstable: `ml.t3.medium` (4), `ml.t3.large` (4), `ml.t3.xlarge` (2).

Note the inversion from Lab 5, and expect sharp students to spot it: Lab 5 forces you *off* burstable (no auto-scaling); Lab 6 forces you *onto* it (only class with default quota).

### 3b. Two container facts that will break a student's job

**The `py312` image tag is load-bearing.** Evidently requires **Python ≥ 3.10**. The image the lab specifies is `sagemaker-scikit-learn:1.4-2-py312-cpu-py3`. A student who copies an older `1.2-1` URI from a tutorial gets an install failure that reads like a network problem.

**The pip dependency warnings are noise, not failure.** Installing Evidently upgrades `protobuf` and `urllib3` past the sklearn container's pins, and pip prints a red `ERROR:` block saying so. **The job succeeds anyway** — verified. Expect students to report this as a failure. It is not.

The real consequence is subtler and worth teaching: `botocore` inside that container is now on an unsupported `urllib3`, so **AWS SDK calls from inside the job are unreliable.** Students must publish CloudWatch metrics from the launcher after the job returns, not from inside it. A student who tried to `put_metric_data` in-container and hit strange TLS errors has found a real dependency-hell lesson.

### 4. Data capture fails silently without an endpoint-role S3 write

The endpoint writes captured data using its **endpoint execution role**. If that role cannot write to `datacapture/`, capture fails with **no error anywhere**: the endpoint reports `InService`, `describe-endpoint-config` reports `EnableCapture: true` at 100% sampling, and zero objects are ever written.

Verified: 41 invocations over 7 minutes produced nothing. Lab 6 then finds no data and fails later, two layers away from the cause.

Fixed in the platform's `MLEngineer` policy (`S3DataCaptureWrite`). If a student is on an older checkout, this is the first thing to check — `scripts/preflight-lab6.sh` catches it. The fix takes effect **without redeploying**; IAM propagation alone is enough.

### 5. CloudWatch silently discards backfilled metrics

`put-metric-data` with a **past timestamp** returns **HTTP 200** and the datapoint is then never queryable.

Verified twice: eight points aged 1–8 days, then a single control point aged 2 days. Every call returned 200. None of the data was retrievable by `get-metric-statistics` at 1-hour or 1-day granularity, checked at 15 and 20 minutes after the put. Only points written at the **current** timestamp appear. The response carries no rejected-datapoint count, so there is no way to distinguish stored from discarded.

**Consequence for grading:** the business-layer rule — "volume drop >30% vs the 7-day average" — **cannot be demonstrated firing on live data inside a lab session.** A student cannot manufacture seven days of history.

Grade the alarm *definition* and the arithmetic, not a time series. A student who publishes a current value, defines the comparison correctly, and explains what would trigger it has met the requirement. A student claiming to have "generated 7 days of history" has either been running the lab for a week or is misreporting — ask to see timestamps.

### 6. Two CLI traps that produce misleading empty results

**Percentiles are not `--statistics`.** `get-metric-statistics --statistics p95` does not work; percentiles require `--extended-statistics p95`. A student checking their p95 SLO with the wrong flag concludes they have no latency data.

**zsh does not word-split unquoted variables.** On macOS (zsh is the default shell), this fails:

```bash
D="Name=EndpointName,Value=northstar-churn-prod Name=VariantName,Value=champion"
aws cloudwatch get-metric-statistics --dimensions $D ...
# Error parsing parameter '--dimensions': Second instance of key "Value"
```

In bash the variable splits into two arguments; in zsh it arrives as one malformed string. Any student or TA copying bash-style examples will hit this. Pass dimensions as separate arguments.

Both traps produce **empty results rather than errors**, which is the worst failure mode in a monitoring lab — it looks exactly like missing data.

---

## Task 1 — Five-Layer Monitoring Implementation (35 points)

### All 5 layers visible in the dashboard (15 pts)

Dashboard must be named `NorthStar-AI-Platform` with at least one metric per layer. Verify data actually exists rather than trusting the widget:

```bash
EP=Name=EndpointName,Value=northstar-churn-prod
VAR=Name=VariantName,Value=champion
S=$(date -u -v-3d +%Y-%m-%dT%H:%M:%S); E=$(date -u +%Y-%m-%dT%H:%M:%S)

aws cloudwatch get-metric-statistics --namespace /aws/sagemaker/Endpoints \
  --metric-name CPUUtilization --dimensions $EP $VAR \
  --start-time $S --end-time $E --period 3600 --statistics Average
```

Confirmed sources, all returning data in the reference run:

| Layer | Namespace | Metric |
|---|---|---|
| Infrastructure | `/aws/sagemaker/Endpoints` | `CPUUtilization`, `MemoryUtilization` |
| Pipeline | `AWS/SageMaker` (or `Glue`) | `Invocation4XX/5XXErrors`, Glue task counts |
| Model | `NorthStar/ChurnModel` | `DriftDetected`, `DriftViolationCount` |
| Application | `AWS/SageMaker` | `ModelLatency` p50/p95/p99 |
| Business | `NorthStar/ChurnModel` | `ChurnAlertVolume` |

**The Glue widget will be empty** unless Lab 2's jobs ran recently. That is correct and should not be penalised — an empty widget advertises a blind spot, a missing one hides it. Give credit for the widget existing with the right metric bound to it.

**Award 15/15** if every layer has a widget bound to a real metric. **Deduct 3 per missing layer.** A dashboard with five widgets all pointing at `ModelLatency` is one layer, not five.

**Look for the microsecond conversion.** A strong submission uses metric math (`m1/1000`) so the latency axis reads in milliseconds and the SLO annotation lines up. A student plotting raw microseconds against a "200 ms" annotation has a chart off by 1000x and will misread their own SLO. Note it favourably; not worth points on its own.

### Evidently baseline and drift analysis run (10 pts)

**A Model Monitor schedule is not required and cannot be created.** See finding 1.

Required evidence:
1. A **baseline CSV** over the **11 features the endpoint receives**, in `monitoring/baseline/`
2. `drift_report.json` **and** `drift_violations.json` from an Evidently processing job over captured data

```bash
aws s3 ls s3://northstar-dev-data-<account>/monitoring/baseline/
aws s3 ls s3://northstar-dev-data-<account>/monitoring/reports/
```

Reference run, verified 2026-08-07 on `ml.t3.medium`, 10,000 baseline rows vs 800 captured records, 1 min 59 s billed:

```
feature                      test         value   thresh  drift
days_since_last_purchase     psi         0.0227      0.2    no
purchase_frequency_30d       psi         6.8354      0.2   YES
avg_order_value              psi         1.3880      0.2   YES
category_diversity_score     ks          0.8945     0.05    no
total_spend_90d              ks          0.7629     0.05    no
```

That run injected a deliberate "holiday promotion" shift — more frequent purchases at lower order value — and Evidently flagged **exactly** the two features that were shifted and nothing else. **This is the shape of a correct submission.** Drift on every feature, or drift on none across every run, both suggest a defect rather than a finding.

**Grade the comparison logic, not just the artifact.** Per finding 2, open their code and check how they decide `drifted`. If they use one operator for both PSI and KS, their KS results are inverted and meaningless even though the JSON looks fine. This is the highest-value check in Task 1.

**Zero violations is a PASS.** If a student replays inputs drawn from the same distribution as the baseline, there is nothing to report and an empty violations list proves the comparison ran. Students who fabricate drift to "get a result" should be marked down for the fabrication, not rewarded for the output.

**Watch the feature count.** The baseline must describe the 11 features the *endpoint receives* — not the full training frame. `churn_label` is the target and `churn_risk_score` is the Lab 3 recency baseline; neither is a model input. A baseline over 12 or 13 columns produces schema noise.

**Small windows manufacture drift.** Under ~500 captured records, clean data will show violations. `evidently_drift.py` sets `underpowered_window: true` in the summary when this happens. If a student reports dramatic drift, check that flag before believing it.

**Capture is partitioned per variant** — `datacapture/<endpoint>/<variant>/<yyyy>/<mm>/<dd>/<hh>/`. A canary student must point the job at one variant and say which. Either choice is defensible; an unstated choice is not.

**Batched invocation ruins the window.** A multi-row payload is captured as one string, so 200 batched predictions become one comparison row. A student reporting a suspiciously tiny `captured_records` against many invocations did this.

**Award 10/10** for both artifacts with real content and correct per-test comparison logic. **7/10** if the artifacts are right but KS is inverted. **5/10** for a baseline only. **0** for neither.

### Custom metric pushed programmatically (5 pts)

```bash
aws cloudwatch get-metric-statistics --namespace NorthStar/ChurnModel \
  --metric-name ChurnAlertVolume \
  --dimensions Name=EndpointName,Value=northstar-churn-prod \
  --start-time $S --end-time $E --period 3600 --statistics Average
```

Must return at least one datapoint. Per finding 5, expect **one current datapoint, not a history** — do not require a time series.

"Programmatically" means code in the repo, not a console click. A committed script calling `put_metric_data` earns this; a screenshot does not.

### Dashboard JSON committed (5 pts)

`monitoring/dashboards/northstar-dashboard.json` must be valid CloudWatch dashboard JSON:

```bash
python3 -c "import json;d=json.load(open('monitoring/dashboards/northstar-dashboard.json'));print(len(d['widgets']),'widgets')"
```

The strongest check is that it round-trips — `put-dashboard` accepts it with no `DashboardValidationMessages`. The reference build produced 15 widgets with zero messages.

---

## Task 2 — Drift Detection Plan (15 points)

Written deliverable in `docs/lab6-runbook.md`. **Gradable with no AWS run** — a student blocked on infrastructure can still earn all 15.

| Item | Pts | What passes |
|---|---|---|
| Drift analysis references NorthStar specifics | 5 | A concrete driver: holiday promotions shifting `purchase_frequency_30d`, a catalog refresh moving `category_diversity_score`, an economic shift changing `avg_order_value`. Generic "data can drift over time" earns 2. |
| Statistical test per feature with threshold | 5 | ≥3 features, each with a named test (PSI/KS/JSD), a baseline window, and a numeric threshold. "We will monitor for drift" earns 0. |
| Concept drift proxy proposed and reasoned | 5 | The label is unobservable for 90 days. A good answer proposes an observable proxy and **states its lag** — score distribution shift (immediate, weak), early-return rate (~2 weeks), partial-holdout labels at 30 days (strong, one third of the window). |

The concept-drift item is the intellectual core of this task. A student who notices that the 90-day holdout means *today's prediction cannot be evaluated for three months*, and designs around that rather than ignoring it, has understood the hardest idea in the lab. Note it.

---

## Task 3 — Alert Architecture (15 points)

Deliverable in `monitoring/alerts/` — a spec document or Terraform alarm config.

| Item | Pts | What passes |
|---|---|---|
| ≥6 alerts with P0–P3 tiers | 8 | All six tiered, distribution sane. Everything-P0 is not an architecture; it is a pager storm. Expect roughly one P0 and one or two P1. |
| Escalation path per tier | 4 | Each tier names an action and a **role**, not a person. "Page the on-call ML engineer, escalate to platform lead after 15 min" passes; "notify the team" does not. |
| ≥1 suppression rule | 3 | Names the condition and the alerts suppressed. "Suppress P2 drift alerts during the scheduled retraining window" passes. |

**Check the units on every latency alarm.** A `ModelLatency` threshold of `200` instead of `200000` sits in `ALARM` permanently against a healthy endpoint. This is the most common defect in the course and it recurs here even though Lab 5 warned about it. **Deduct 2 within this task** for a wrong-unit threshold and say so — do not silently accept it.

Strong submissions connect an alert to the identity distinction from the prerequisites: the observer role watches, the execution role acts. A student who notes that their drift alarm cannot itself remediate has understood something real.

---

## Task 4 — SLO Design (15 points)

| Item | Pts | What passes |
|---|---|---|
| All 4 SLOs with numeric error budgets | 10 | Availability, latency, prediction quality, fairness — each with a number in minutes/month or events/month. 99.5% availability = **216 min/month**; accept 3.6 h or ~0.5%. |
| Deployment freeze triggers actionable | 5 | A specific condition. "Freeze when 75% of the monthly error budget is consumed before day 20" passes. "Freeze if the SLO is at risk" earns 0. |

**The latency SLO is p95 < 20 ms, not 200 ms.** Measured steady state is ~4.1 ms, so a 200 ms target is met 48x over and teaches nothing. At 20 ms there is still a healthy ~5x margin, but the ~24,000 µs cold start **does** breach it — so a student's own deployments consume their error budget, which is precisely why error budgets gate deploys.

Watch for the conflation this is designed to surface: **an SLO target and an alert threshold are different numbers doing different jobs.** The SLO is a monthly promise spent down as budget; the alarm is the point you wake someone. A student who sets both to the same value has missed the distinction — worth a comment even when the numbers are otherwise fine.

---

## Task 5 — Runbooks (20 points)

Two runbooks in `docs/lab6-runbook.md`, following the required structure.

| Item | Pts | What passes |
|---|---|---|
| Both complete, no empty sections | 10 | Every section filled. Any "TBD" costs 2 each. |
| Graceful degradation fallback | 6 | At least one containment option describes what the system does when it **cannot** recover immediately — serve the previous model version, fall back to the recency-only baseline, degrade to cached scores, or suppress the offer rather than send a bad one. "Roll back and investigate" is not degradation. |
| Resolution verification observable | 4 | Names a metric or alarm state. "`ModelLatency` p95 back under 20,000 µs for 15 consecutive minutes and the alarm returns to `OK`" passes. "The system feels normal" earns 0. |

The recency-only baseline from Lab 3 is the obvious degradation target and almost nobody proposes it. A student who writes "if the model is unavailable, rank by `days_since_last_purchase` — it scores AUC 0.67 against the model's 0.71, so we lose accuracy but keep the retention programme running" has produced the best possible answer to this item. Flag it.

---

## Teardown — gate, not points

Same standing as Lab 5. An endpoint or drift-automation trigger alive after the deadline is a **10-point deduction on top of the gate**.

```bash
bash scripts/teardown-lab6.sh
```

**Order matters and the script enforces it:** student-built triggers and in-flight processing jobs first, then the endpoint. Anything on a timer keeps launching billable jobs after the endpoint is gone. SageMaker schedules are unavailable, but a student's own EventBridge rule has the identical failure mode.

Verify against `docs/lab6-teardown-output.txt` and an independent sweep. Do **not** accept console screenshots — the console's resource views lag by hours and have shown deleted resources as present in this course before.

Captured data under `datacapture/` is **retained by design** (7-day lifecycle) and is evidence. Do not penalise students for leaving it. Custom CloudWatch metrics cannot be deleted; they expire after 15 months, and the $0.30 metric-month charge is expected.

---

## Rubric Summary (100 points)

| Task | Item | Pts |
|---|---|---|
| 1 | All 5 layers in the dashboard | 15 |
| 1 | Evidently baseline **and** drift analysis run | 10 |
| 1 | Custom metric pushed programmatically | 5 |
| 1 | Dashboard JSON committed and valid | 5 |
| 2 | Drift analysis references NorthStar specifics | 5 |
| 2 | Statistical test per feature with threshold | 5 |
| 2 | Concept drift proxy proposed and reasoned | 5 |
| 3 | ≥6 alerts with severity tiers | 8 |
| 3 | Escalation paths documented | 4 |
| 3 | ≥1 suppression rule | 3 |
| 4 | All 4 SLOs with numeric error budgets | 10 |
| 4 | Deployment freeze triggers actionable | 5 |
| 5 | Both runbooks complete | 10 |
| 5 | Graceful degradation fallback | 6 |
| 5 | Resolution verification observable | 4 |
| | **Total** | **100** |

**65 of 100 points (Tasks 2–5) are written deliverables gradable with no AWS access at all.** If a student is blocked on quota, on the closed Model Monitor API, or on a billing problem, they can still earn a passing grade on reasoning alone. Grade those tasks on their merits and do not let an infrastructure blocker cascade into the written work.

---

## Connections to prior labs

- **Lab 2** created the IAM roles. Lab 6 needs `ModelMonitorExecution` — the *execution* identity, not the read-only `ModelMonitor` observer. That distinction is a teaching point, not a technicality. Lab 2's feature set is also the **source of the Evidently baseline**; students export the 11 endpoint features to CSV rather than generating a baseline with a managed job.
- **Lab 3** produced the model and the recency-only baseline that makes the best degradation answer possible.
- **Lab 4** built the CI/CD gate. The SLO error budget is what should freeze that pipeline.
- **Lab 5** deployed the endpoint and enabled data capture. **Without capture there is no Lab 6** — endpoint configs are immutable, so a student who deployed without it must redeploy.
