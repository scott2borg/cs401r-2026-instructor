---
tags: [CS401R, lab-solution, lab-5, deployment, security, privacy, TA-guide]
course: CS 401R
lab: 5
status: answer-key
total_points: 100
verified_on_aws: 2026-07-30
---

# Lab 5 — Deployment & Scaling + Security: TA Grading Guide

> **For TA use only.** Do not distribute to students.
> Total points: 100. Tasks: Production Deployment (30) · Operational Deployment Plan (20) · Security Assessment (25) · Privacy & Compliance (15) · Repository Quality (10).

---

## Reference Run

The full Lab 5 deployment path was executed against account `711457211658` on **2026-07-30**: model registered and approved, two-variant canary endpoint deployed, traffic split observed, auto-scaling registered, rollback alarm fired, rollback executed, everything torn down and verified across all 17 regions. Total cost of the run: **under $0.20**.

**Timings — give these to students who ask how long the lab takes.**

| Operation | Measured |
|---|---|
| `create-endpoint` → `InService` (2 variants) | **6 min 47 s** |
| `update-endpoint` to a new config | **3 min 47 s**, zero downtime, served throughout |
| `update-endpoint-weights-and-capacities` (rollback) | **~85 s**, status `Updating`, no dropped requests |
| Alarm `OK` → `ALARM` after breach | **< 60 s** |

**Observed traffic split at 9:1 weights, 200 invocations:**

```
champion 175  /  canary 25        (87.5% / 12.5%)
```

**After rollback to 10:0 weights, 100 invocations:**

```
champion 100  /  canary 0
```

**Measured `ModelLatency` on `ml.m5.large`:**

```
Average    4,151 us   (4.15 ms)
Maximum    7,821 us
Unit       Microseconds
```

> ### The model used for the reference run is not the Lab 3 reference model
>
> To verify deployment mechanics without re-running the whole Lab 2 data platform, the reference deployment used a model trained locally from `data/northstar-raw-sample.csv` through the verified pandas `feature_engineering.py`. Its metrics were **AUC 0.7444, baseline 0.7175, lift +0.0268, precision@10 0.70, recall@10 0.3387** on 1,200 customers at a 20.8% churn rate.
>
> **That lift of +0.0268 is below Lab 4's ≥0.03 gate — this model would have failed the Lab 4 build.** That is fine for Lab 5's purposes, because deployment mechanics are model-agnostic, but do not quote these numbers to students as targets. **The canonical Lab 3 Track A metrics are AUC 0.7276 / baseline 0.6298 / lift +0.0978 / precision@10 0.6944 / recall@10 0.3333** (`train_reference.py`, Athena path, measured 2026-08-01, registry v2). Earlier figures around 0.747 / 0.293 are superseded.

---

## Four findings that will hit students before anything else

### 1. `ml.t2.medium` cannot be an auto-scaling target — and as of 2026-07-31 this is INTENTIONAL

**Read this before grading anything in Task 1. The design changed and the old grading guidance is inverted.**

The spec now **instructs students to start on `ml.t2.medium`.** Hitting the auto-scaling wall is the assignment, not a mistake. Students are then meant to diagnose it, switch to `ml.m5.large`, and discover that their account has no quota for it either.

#### Why burstable instances are rejected

```
An error occurred (ValidationException) when calling the RegisterScalableTarget operation:
You cannot register a variant with ml.t2.medium instance type as a scalable target.
This is because the burstable performance of these instances can lead to unpredictable
behavior with Auto Scaling.
```

The reason is in the last sentence of AWS's own message, and it is worth being able to explain to a student who asks.

Burstable instances (`ml.t2.*`, `ml.t3.*`) do not deliver sustained CPU. They earn **CPU credits** while idle and spend them while busy; when the credit balance hits zero the instance is throttled to a low baseline — for `ml.t2.medium`, roughly 20% of a vCPU. Auto Scaling makes decisions by reading a performance signal such as `SageMakerVariantInvocationsPerInstance` or CPU utilisation and inferring "this instance is saturated, add another."

On a burstable instance that inference is unsound. High CPU may mean genuine load, or it may mean the instance has exhausted its credits and is being throttled while doing very little real work. Scaling out in the second case adds instances that will themselves burn through credits and throttle. The control loop would be reacting to an artefact of the credit system rather than to demand, so **AWS refuses to manage them rather than let you build a scaling policy that oscillates.**

The short version for a student: *auto-scaling assumes performance is a function of load; on burstable instances performance is a function of credit balance, so the assumption breaks.*

#### The two walls, in order

| Wall | Trigger | Error |
|---|---|---|
| 1 | `register-scalable-target` on `ml.t2.medium` | `ValidationException ... cannot register a variant with ml.t2.medium` |
| 2 | Redeploy on `ml.m5.large` | `ResourceLimitExceeded ... 'ml.m5.large for endpoint usage' is 0 Instances` |

**Wall 2 will hit essentially every student.** Verified 2026-07-31: of 251 endpoint instance types, only three have a non-zero AWS default — `ml.t2.medium` (2), `ml.m6g.large` (2), `ml.m6g.xlarge` (1). `ml.m5.large` defaults to **0**.

Note that the reference account (`711457211658`) has an *applied* quota of 8 and therefore **cannot reproduce what students see.** Do not test a student's claim against the reference account and conclude they are wrong. Check defaults with `get-aws-default-service-quota`, not `get-service-quota`.

The quota is `ml.m5.large for endpoint usage`, code **`L-614B09FD`**, adjustable, regional. Students are told to request a value of **2** and to file it on day one.

#### Grading

**Both outcomes earn full marks on the 5-point auto-scaling item.**

- **Path A — quota approved in time:** a live scaling policy on a non-burstable instance. Standard evidence.
- **Path B — quota still pending:** the `register-scalable-target` rejection captured, a one-sentence correct explanation of *why* burstable is refused, evidence of a filed quota request, and the scaling configuration they would have applied.

Path B is **not** a partial-credit path. A student who correctly diagnosed a platform constraint, filed the right request, and documented the intended design has demonstrated exactly what this task is testing. Turnaround on the AWS side is outside their control and has ranged from minutes to several business days.

**Do deduct** when a student:
- reports "auto-scaling didn't work" with no diagnosis of *why*
- blames their own configuration for what is a platform constraint
- never filed a quota request and offers no evidence of trying
- claims a scaling policy exists but shows no `describe-scaling-policies` output

**Do not deduct** for a student who completed the whole lab on `ml.t2.medium`. That is the designed path. It also fully supports `DataCaptureConfig`, so it does not compromise their Lab 6.

**Flag favourably** any student who notices that `ml.m6g.large` has non-zero default quota *and* is a valid auto-scaling target, and either uses it or explains why they did not. It is a legitimate solution — Graviton is non-burstable, 20% cheaper, and deploys faster (verified: scalable target accepted, 4 min 04 s to InService, $0.0924/hr). The catch is that the SageMaker XGBoost container only publishes arm64 images for versions 1.3-1 and 1.5-1, so our 1.7-1 model artifact will not load on it. A student who finds that themselves has done genuinely excellent work.

### 2. `ModelLatency` is in microseconds — this one costs 8 points

The single highest-value thing to check in this lab.

The spec, the chapter, and every SLO table in Lab 6 talk in milliseconds: "p95 < 200 ms". The CloudWatch metric is emitted in **microseconds**. A student who writes the obvious thing:

```json
{"MetricName": "ModelLatency", "Threshold": 200}
```

has built an alarm that trips at 0.2 ms against an endpoint whose healthy latency is ~4.15 ms. Verified: an alarm at threshold `1000` went to `ALARM` in under a minute under normal traffic and never recovered. A rollback wired to that alarm rolls back a healthy deployment on every single deploy.

**Check every rollback threshold against the metric's actual unit.** The correct value for 200 ms is `200000`.

```bash
# The check that settles it
aws cloudwatch get-metric-statistics --namespace AWS/SageMaker --metric-name ModelLatency \
  --dimensions Name=EndpointName,Value=<ep> Name=VariantName,Value=<variant> \
  --start-time "$(date -u -v-20M +%Y-%m-%dT%H:%M:%SZ)" --end-time "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --period 60 --statistics Average --output table
# The Unit column reads "Microseconds"
```

A student who caught this unprompted and said so in their plan should get explicit written credit. It is the most professionally realistic mistake in the lab.

### 3. Cold start spikes latency ~6x — expect false alarms on the first invocation

Measured on the first invocation after deployment, and again after `update-endpoint`:

```
23:32  23,331 us   <- first call after create-endpoint
23:38  24,192 us   <- first call after update-endpoint
steady  ~4,100 us
```

A p95 alarm with `EvaluationPeriods: 1` will trip on the deployment itself. The reference config uses `EvaluationPeriods: 2` with `TreatMissingData: notBreaching`. A student whose alarm fired immediately after deploying and who diagnosed it as cold start rather than a model problem has demonstrated the actual skill. A student with `EvaluationPeriods: 1` who never noticed should be told why their trigger is unusable in production — but this is a **comment, not a deduction**; the spec does not mandate an evaluation-period count.

### 4. The XGBoost save warning is benign — do not let students chase it

XGBoost 3.x prints, on every save:

```
WARNING: Saving model in the UBJSON format as default. You can use a file extension:
`json` or `ubj` to choose between formats.
```

`requirements.txt` pins `xgboost>=2.0.0`, so students get 3.x, while the inference container is `sagemaker-xgboost:1.7-1`. This looks like a forward-compatibility problem and is not one. **Verified end to end:** the 1.7 container loaded the UBJSON artifact and returned correct predictions (`0.0142` for a customer 15 days since last purchase — a plausible low-churn score). If a student reports "my model won't deploy," the cause is elsewhere — check the execution role and the `ModelDataUrl` first.

---

## Correction to prior guidance

Earlier drafts of the Lab 5 material claimed that an Application Auto Scaling **scalable target survives endpoint deletion** and orphans. **This was tested directly and is false.** A target and policy were registered, only the endpoint was deleted, and within 90 seconds the scalable target, its scaling policies, and the auto-created `TargetTracking-*` alarms were all gone.

There is no auto-scaling orphan class. `scripts/teardown-lab5.sh` still deletes them explicitly so the teardown is deterministic and its verification block is meaningful when a student has created resources by hand — but **do not deduct** for a student who deleted the endpoint without separately deregistering the target. They are not leaving anything behind.

---

## Task 1 — Production Deployment (30 points)

### Deployment approach justified (5 pts)

Either approach is acceptable. What is graded is whether the justification engages **NorthStar's scoring frequency**, not generic latency-vs-throughput talk.

- *Batch Transform* is the defensible default: NorthStar scores its customer base nightly, has no sub-minute latency requirement, and an always-on endpoint idles ~23 hours a day. A student who reasons this through and still deploys real-time **because the lab requires an auto-scaling policy** has spotted a genuine tension in the assignment — give full credit and note it.
- *Real-time* is fully acceptable when justified by a forward-looking requirement (live scoring at checkout, an agent calling the model per session).

Generic answers — "real-time is faster" — earn 2 of 5.

### Canary / blue-green / batch parallel run (12 pts)

**Require observed evidence, not a config field.** The strongest artifact is an invocation count:

```python
import boto3, collections
rt = boto3.client("sagemaker-runtime", region_name="us-east-1")
c = collections.Counter()
for _ in range(200):
    r = rt.invoke_endpoint(EndpointName="<ep>", ContentType="text/csv", Body=body)
    c[r["InvokedProductionVariant"]] += 1
print(c)
```

At 9:1 the reference observed 175/25 over 200 calls. Anything roughly consistent with the configured weights passes; binomial noise at n=200 is wide, so do not quibble about 82/18 vs 90/10.

| What you see | Award |
|---|---|
| Observed split from ≥100 invocations matching configured weights | 12 |
| Two variants configured with weights, but no invocation evidence | 8 |
| Blue/green with a second endpoint plus smoke-test output before cutover | 12 |
| Batch shadow run with a score-distribution comparison artifact | 12 |
| Batch shadow run, outputs produced but never compared | 6 |
| Direct `update-endpoint` swap with no parallel running model | 0 |

A student can smoke-test a specific variant without waiting for routing by passing `--target-variant`. Seeing that in their notes is a good sign they understand what blue/green validation actually requires.

### Rollback trigger with numeric threshold, present as code (8 pts)

Three things must all be true:

1. A named metric and a numeric threshold — `ModelLatency` p95, `Invocation5XXErrors`, or a custom accuracy proxy
2. **Correct units** — see finding 2 above; `200` on `ModelLatency` fails this item outright
3. The alarm exists **as code** in `deployment/configs/`, not only as prose

| What you see | Award |
|---|---|
| Alarm as code, correct units, sensible evaluation periods | 8 |
| Alarm as code, correct units, `EvaluationPeriods: 1` | 8 (comment on cold start) |
| Alarm as code but `ModelLatency` threshold in ms (e.g. `200`) | 3 |
| Threshold stated in prose only, nothing wired up | 2 |
| "We would roll back if latency degrades" | 0 |

Reference artifacts live in `deployment/configs/`: `rollback-alarm.json`, `autoscaling-policy.json`, `endpoint-config-canary.json`, `rollback-action.sh`.

### Auto-scaling configured; window compression documented (5 pts)

Auto-scaling requires a **non-burstable** instance, and reaching one requires a quota increase most students will not have on day one. **See finding 1 — both Path A and Path B earn full credit.**

Path A, verify the live policy with:

```bash
aws application-autoscaling describe-scaling-policies --service-namespace sagemaker \
  --query 'ScalingPolicies[*].[PolicyName,TargetTrackingScalingPolicyConfiguration.TargetValue]' --output table
```

Path B, verify the quota request is real rather than claimed:

```bash
# Student runs this in their own account; ask for the output
aws service-quotas list-requested-service-quota-change-history \
  --service-code sagemaker --region us-east-1 \
  --query 'RequestedQuotas[].[QuotaName,DesiredValue,Status,Created]' --output text
```

Any of `PENDING`, `CASE_OPENED` or `APPROVED` against `ml.m5.large for endpoint usage` is acceptable evidence. A `Created` timestamp close to the due date is worth a comment about starting earlier, but is **not** grounds for deduction — the spec's instruction to file on day one is advice, not a graded requirement.

The compression half of this item asks students to state that they planned a 48-hour canary but observed 60 minutes, and what that trades away. Good answers name something concrete: a 48-hour window spans a full diurnal traffic cycle and at least one batch feature refresh; 60 minutes catches infrastructure faults and gross scoring errors but cannot catch drift, time-of-day load patterns, or anything requiring label feedback. A student who says "we shortened it to save money" and stops there earns 2 of 5 — true, but not the point.

**Batch Transform students:** auto-scaling does not apply. Award the 5 points on the compression documentation and a stated concurrency/instance-count plan for the batch job.

---

## Task 2 — Operational Deployment Plan (20 points)

`docs/lab5-deployment-plan.md`, 600–900 words, seven required sections.

### Executable by a stranger (10 pts)

Read it as though you have never seen the repo. The disqualifying pattern is **undefined names**: "deploy the canary endpoint" without saying which endpoint, config, or model version.

| Signal | Effect |
|---|---|
| Commands are copy-pasteable with real resource names | full credit |
| Names the model **approval** step and who performs it | required — this is new in Lab 5 and half of students will omit it |
| Rollback section says who makes the call, by role | required |
| Sections present but generic ("monitor the metrics") | 5 of 10 |
| Missing ≥2 of the 7 required sections | 3 of 10 |

The pre-deployment checklist must include model approval. Nothing in Labs 1–4 ever moves a package off `PendingManualApproval`, so a plan that assumes an approved model has skipped a governance gate — the exact thing this task exists to teach.

### Rollback criteria numeric and unambiguous (6 pts)

Must match the alarm in `deployment/configs/` — including units. A plan saying "roll back above 200 ms" alongside an alarm at `200` (microseconds) is **internally inconsistent**; award 3 and explain that the plan and the control disagree.

### Stakeholder notification list complete (4 pts)

Roles, not names, and something specific at each of deployment start / promotion / rollback. "Notify the team" earns 1.

---

## Task 3 — Security Assessment (25 points)

### STRIDE, ≥5 threats across ≥3 categories (10 pts)

Every row needs all six fields. Threats that recur in strong submissions:

| Threat | Category | Notes |
|---|---|---|
| Membership inference via repeated endpoint queries | Information Disclosure | The signature threat for a deployed model; expect it |
| Model theft by systematic querying (extraction) | Information Disclosure | |
| Poisoned transactions upstream shifting the feature distribution | Tampering | Strong answers connect this to Lab 6 drift detection |
| Unauthenticated endpoint invocation | Spoofing | Must name IAM auth / VPC endpoint / private link |
| Inference log accumulation of customer scores | Information Disclosure | Ties directly to Task 4's erasure workflow |
| Flooding the endpoint to force auto-scaling cost blowup | Denial of Service | Economic DoS — excellent answer, connects to the auto-scaling `MaxCapacity` they just set |

The spec requires at least one mitigation to reference which of the **Lab 2 IAM roles** (`MLEngineer`, `DataEngineer`, `ModelMonitor`) contains the blast radius, and at least one to name a gap those roles do **not** close. Real gaps: none of the three roles constrains *inference-time* access to the endpoint, and `ModelMonitor`'s read-only artifact access does not prevent model extraction through legitimate invocation.

A student who only lists threats without engaging the existing role boundary earns 6 of 10 regardless of table quality.

### Mitigations name specific AWS services (5 pts)

"Use encryption" is 0 for that row. "SSE-KMS with a customer-managed key, key policy restricting `kms:Decrypt` to the `MLEngineer` role" is full credit. Any mitigation naming a service and the control earns it.

### All 7 data assets classified (10 pts)

Assets: customer PII, transaction history, behavioural clickstream, product catalogue, model weights, inference logs, Feature Store records.

Each needs tier, encryption standard, IAM policy, third-party shareability. **The graded distinction is SSE-KMS vs SSE-S3 with a stated reason** — customer-managed keys buy a CloudTrail audit trail of every `Decrypt`, key-policy-level access control, and rotation. A table that marks everything SSE-KMS with no reasoning earns 6; correct tiering with justified per-asset encryption choices earns 10.

Two rows separate strong from average work:

- **Product catalogue** is the only genuinely Public/Internal asset. A student who classifies all seven as Confidential or Restricted has not classified anything — over-classification is a real failure mode with real cost, and worth a comment.
- **Model weights** are Confidential at minimum: the model encodes customer behaviour and is extractable. Students who mark it Internal because "it's just numbers" have missed the membership-inference threat they probably listed in 3a. Point at the contradiction.

---

## Task 4 — Privacy & Compliance Assessment (15 points)

### Lawful basis justified (5 pts)

**Legitimate interests** is the strongest answer for churn prediction on existing customer purchase history, and it must come with the balancing test: NorthStar has a genuine commercial interest in retention, the processing uses data customers already provided transactionally, and it is within reasonable expectation.

**Contractual necessity** is defensible but weaker — churn prediction is not *necessary* to perform the sales contract.

**Consent** is acceptable only if the student acknowledges the operational consequence: consent is withdrawable, so the pipeline needs a suppression list and the model needs retraining without those customers.

Naming a basis with no reasoning earns 2.

### Deletion workflow covers all 4 stores (6 pts)

Raw S3, Feature Store, model training data, inference logs — 1.5 points each, concrete step required.

**The Feature Store answer must distinguish online from offline.** Online store supports `DeleteRecord`. The offline store is **append-only on S3**; `DeleteRecord` writes a tombstone and does not remove the historical rows. A student who says "call DeleteRecord" and stops has answered a third of the question.

### Hardest step correctly identified (4 pts)

The intended answer is the **trained model** (or, equivalently, the offline Feature Store's append-only history): deletion there is not a delete operation. The customer's data is diffused into the model weights, and honouring erasure means either retraining without them or accepting that the model retains their influence. Strong answers connect this to the retraining trigger they defined in Lab 4 and note the cost asymmetry — one deletion request cannot economically force a retrain, so real systems batch them.

| What you see | Award |
|---|---|
| Model weights / offline store, with the "not a delete operation" reasoning | 4 |
| Correct store named, thin reasoning | 2 |
| "Raw S3 is hardest because there's a lot of data" | 0 |

---

## Task 5 — Repository Quality (10 points)

| Item | Pts | Check |
|---|---|---|
| No credentials in code | 4 | `git log --all -S "AKIA"` returns nothing; `.env` in `.gitignore` |
| Deployment config is code | 3 | Endpoint config, scaling policy, **and** rollback alarm in `deployment/configs/`. All three = 3; two = 2; console-only = 0 |
| CI extended with a security check | 3 | See below |

**On the security check:** `requirements-dev.txt` already ships `bandit` with the comment *"the buildspec has this stage commented out until Lab 5 introduces it."* Uncommenting that stage and getting a clean CodeBuild run is full credit. **CodePipeline is not required** — the verified path in this course is CodeBuild with an S3 source, and no GitHub connection exists. Do not deduct for its absence. A `detect-secrets`, `pip-audit`, or IAM policy lint step is equally acceptable.

---

## Teardown — gate, not points

```bash
bash scripts/teardown-lab5.sh
```

Produces `docs/lab5-teardown-output.txt`. Expected clean output:

```
  SageMaker endpoints              OK
  Endpoint configs                 OK
  SageMaker models                 OK
  Auto-scaling targets             OK
  Transform jobs running           OK
  Processing jobs running          OK

==> Lab 5 teardown complete. No billable inference resources remain.
```

**Task 1 is capped at half credit until this file is produced.** A live endpoint after the deadline is an additional **−10**, on top of the cap.

Verify against the live API, never the console — the console has shown deleted resources as present in this course before.

```bash
aws sagemaker list-endpoints --query 'length(Endpoints)' --output text   # must be 0
```

**CLI trap for TAs cleaning up after a cohort:** `delete-model-package` takes an ARN but the flag is `--model-package-name`, not `--model-package-arn`. The obvious spelling errors out. A package group also cannot be deleted until every package inside it is gone.

---

## Rubric Summary (100 points)

| # | Item | Pts |
|---|---|---|
| 1 | Deployment approach justified against scoring frequency | 5 |
| 2 | Canary / blue-green / batch parallel run, observed | 12 |
| 3 | Rollback trigger, numeric, correct units, as code | 8 |
| 4 | Auto-scaling on non-burstable; window compression documented | 5 |
| 5 | Deployment plan executable by a stranger | 10 |
| 6 | Rollback criteria numeric and consistent with the alarm | 6 |
| 7 | Stakeholder notification list complete | 4 |
| 8 | ≥5 STRIDE threats across ≥3 categories, engaging IAM roles | 10 |
| 9 | Mitigations name specific AWS services | 5 |
| 10 | All 7 data assets classified, SSE-KMS vs SSE-S3 justified | 10 |
| 11 | Lawful basis justified with specifics | 5 |
| 12 | Deletion workflow covers all 4 stores | 6 |
| 13 | Hardest deletion step correctly identified | 4 |
| 14 | No credentials in code | 4 |
| 15 | Deployment config is code | 3 |
| 16 | CI extended with a security check | 3 |
| — | **Teardown evidence** | **gate** |
| — | Endpoint live after deadline | **−10** |
| | **Total** | **100** |
