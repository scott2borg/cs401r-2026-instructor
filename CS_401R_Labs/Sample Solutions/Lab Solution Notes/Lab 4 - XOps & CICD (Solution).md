---
tags: [CS401R, lab-solution, lab-4, testing, cicd, mlops, TA-guide]
course: CS 401R
lab: 4
status: answer-key
total_points: 100
---

# Lab 4 — XOps + CI/CD + Testing: TA Grading Guide

> **For TA use only.** Do not distribute to students.
> Total points: 100. Tasks: Test Suite (30) · CI/CD Pipeline (30) · MLOps Configuration (20) · XOps Maturity (20).

---

## Reference Run

A CodeBuild integration test was executed against account `711457211658` on 2026-07-30 using the shipped `buildspec.yml` with an S3 source. These are the real measured results.

```
PROVISIONING     SUCCEEDED     3s
DOWNLOAD_SOURCE  SUCCEEDED     2s
INSTALL          SUCCEEDED   232s     pip install from requirements.txt
PRE_BUILD        SUCCEEDED    14s     test_data 26 passed · test_features 18 passed
BUILD            SUCCEEDED     1s     quality gate 4/4 PASS
```

Passing gate output, using the verified Lab 3 Track A metrics (`train_reference.py`, 2026-08-02, 10k dataset, registry v4):

```
auc_roc            0.7696   (reported, not gated)
precision_top10    0.6833   (min: 0.5)   PASS
recall_top10       0.3106   (min: 0.25)  PASS
auc lift          +0.0464   95% CI [0.0254, 0.0670] excludes 0  PASS
```

**The blocking case, which is the point of the lab.** A second build was run with a model scoring AUC 0.800 — *better* than the reference — but only +0.005 over the recency baseline:

```
auc_roc            0.8000   (reported, not gated)
precision_top10    0.7000   (min: 0.5)   PASS
recall_top10       0.4000   (min: 0.25)  PASS
auc lift          +0.0050   95% CI [-0.0121, 0.0223] includes 0   FAIL

Model quality gate FAILED:
  - auc lift 95% CI [-0.0121, 0.0223] includes zero: no evidence the
    model beats the recency-only baseline
Model will NOT be promoted to the registry.

BUILD STATUS: FAILED
```

**This case is sharper under the CI gate than it was under the old ≥ 0.03 threshold.** Previously a student could argue the 0.03 bar was arbitrary — and they would have had a point, since the threshold was smaller than the metric's own standard deviation. Now the failure is not "you missed a number we picked," it is "your measurement cannot distinguish your model from the baseline." That is the lesson: **a high AUC with no separation from the trivial model is not a shippable model**, and the highest-AUC candidate is not automatically the best one.

A student whose pipeline promotes that model has not built a gate. Reproducing this specific case is the fastest way to grade Task 2.

---

## Two defects that will hit students before anything else

### 1. The colon-in-echo YAML trap (fixed in the shipped kit, but students will reintroduce it)

An unquoted colon inside a command makes YAML parse it as a mapping rather than a string:

```yaml
- echo "=== BUILD PHASE: Package & Deploy ==="
```
parses as `{'echo "=== BUILD PHASE': 'Package & Deploy ==="'}`, and CodeBuild rejects the **entire file**:

```
YAML_FILE_ERROR: Expected Commands[0] to be of string type: found subkeys instead
```

Nothing runs. The error names a line number, not the colon, so students lose an afternoon. This was present in the shipped starter kit and is now fixed — but any student who adds a decorative `echo "Step 3: training"` reintroduces it.

**Diagnosis one-liner:**
```bash
python3 -c "
import yaml,sys; d=yaml.safe_load(open('buildspec.yml'))
bad=[(p,i,c) for p,b in d['phases'].items() for i,c in enumerate(b.get('commands',[])) if not isinstance(c,str)]
print(bad or 'all commands are strings')"
```

### 2. `terraform apply` fails on the first attempt after a teardown

Reproducible. After `terraform destroy`, the next apply errors:

```
Error: reading S3 Object (artifacts/glue/feature_engineer.py): couldn't find resource
```

The `aws_s3_object` refresh looks for an object the destroy already removed. **Re-running the apply succeeds.** Students hit this at the start of every lab cycle. Do not deduct for it, and tell them to just re-run.

---

## Task 1 — Test Suite (30 points)

### All 4 test categories implemented (12 pts)

Required: `test_data.py`, `test_features.py`, `test_model.py`, `test_fairness.py`, each with ≥2 passing tests.

Reference counts from the shipped kit: **test_data 26 passed, test_features 18 passed**. `test_fairness.py` is not shipped — students write it.

**The thing to check first: does a missing dataset FAIL or SKIP?**

The original starter kit called `pytest.skip` when data was absent, which meant `pytest tests/` went green having validated nothing. That was fixed; `test_data.py` now fails loudly and requires `ALLOW_MISSING_DATA=1` to defer.

If a student weakened that back to a skip, their pipeline gate is decorative. Verify:

```bash
mv data/features /tmp/stash && python3 -m pytest tests/test_data.py -q ; mv /tmp/stash data/features
```
Expected: errors, not "skipped". The reference produces **12 errors**. A green run here is worth **-6** and a comment explaining why a gate that cannot fail is not a gate.

### ≥5 feature unit tests with edge cases (10 pts)

Must cover normal, boundary (customer with zero purchases), and edge (single transaction) cases.

**Watch for the schema trap.** Lab 2's processed output is `purchase_date`, `order_value`, `num_items`, `product_category`. An earlier kit version used a retired schema (`transaction_amount`, `net_amount`, `promotion_code`, `product_categories`). A student who copied an old fixture is testing a contract that does not exist — the tests pass while validating nothing real. Check fixture column names against the processed schema.

**The pandas extraction is the assignment.** Lab 2's logic is PySpark, which needs a JVM and is impractical in CI. Students must extract the computation into testable pandas functions in `data/feature_engineering.py`. Reference implementation exists in the live repo and is **verified equivalent to the Glue job** on identical input:

```
1,200 customers · 0 nulls
category_diversity_score 0.1250 - 1.0000
tiers Bronze 417 / Silver 456 / Gold 216 / Platinum 111   (exact match to the Spark run)
```

A student whose pandas and Spark implementations disagree has two sources of truth. Ask which one production uses.

### Regression test compares against champion (8 pts)

Must retrieve champion AUC from the Model Registry and fail if the new model regresses beyond tolerance. A hardcoded champion AUC earns 3 of 8 — the point is reading live registry state.

---

## Task 2 — CI/CD Pipeline (30 points)

### All 5 stages present and sequenced (12 pts)

Source → Test → Build → Evaluate → Register.

`pipeline.yaml` validates against CloudFormation with 8 parameters resolving. Two things students commonly get wrong:

- **`ArtifactsBucket` is CodePipeline's own working bucket**, not the NorthStar data bucket. Reusing the data bucket works but muddles the boundary; note it rather than deduct.
- **`SageMakerRoleArn` must be passed directly.** An earlier template read it from SSM at `/northstar/sagemaker-role-arn`, which nothing in the course creates, so the stack failed at parameter resolution. If a student's stack won't launch, check this first.

### Pipeline halts correctly on test failure (10 pts)

Introduce a deliberate failure and confirm the pipeline stops at the Test stage rather than continuing. The cheapest check:

```bash
# in the student's repo
sed -i 's/assert n == 0, f"{n} rows with null customer_id/assert n == 999, f"{n} rows with null customer_id/' tests/test_data.py
```
Then trigger a build. It must fail in PRE_BUILD, and no model may reach the registry.

### Model Registry promotion only on green gates (8 pts)

**This is where the quality gate earns its points.** Verified behaviour above: a model with a strong absolute AUC but no lift over the recency baseline **fails the build**.

Check the student's gate actually enforces all four thresholds — AUC, precision@10, recall@10, and lift. A gate checking only AUC is worth 3 of 8, because AUC alone passes a model that learned nothing beyond `days_since_last_purchase`.

Also confirm the gate fails when `baseline_auc_roc` is **absent**, not just when it is low. Reference gate blocks on a missing field and on an empty metrics file. A gate that treats missing metrics as passing is the most dangerous failure mode in the lab — an S3 fetch error would silently promote an unevaluated model.

---

## Task 3 — MLOps Configuration (20 points)

| Item | Pts | Grading note |
|---|---|---|
| Champion-challenger criterion numeric and binary | 5 | "New model replaces champion if AUC ≥ champion + 0.01 **and** no tier slice regresses more than 0.05" is full credit. "If it performs better" is 0. |
| Both retraining triggers defined and automatable | 8 | Needs a scheduled trigger *and* a performance trigger, each naming the AWS service that fires it (EventBridge rule, CloudWatch alarm). "We would retrain monthly" without a mechanism earns 3. |
| Experiment tracking ≥3 runs | 4 | Three *identical* runs earn 2 — hyperparameter variation is the point. |
| Model lineage metadata in Registry | 3 | `describe_model_package()` must show training data URI and commit SHA. The Lab 3 reference attaches `auc_roc`, `baseline_auc_roc`, `auc_lift`, `feature_count`. |

**A good champion-challenger criterion should reference the Platinum finding from Lab 3** — aggregate AUC improving while a high-value slice regresses is exactly the case a naive criterion misses. Students who caught that deserve explicit credit.

---

## Task 4 — XOps Maturity Assessment (20 points)

Graded on specificity, not on the maturity level claimed. A student who honestly assesses their platform as Level 2 with evidence scores higher than one claiming Level 4 with generic language.

- **Evidence (10):** must cite specific files and configs in their repo — `buildspec.yml` gate thresholds, `teardown-lab2.sh`, the Feature Store definition. Generic maturity-model prose earns ≤4.
- **Gap analysis (6):** "No automated drift detection; Model Monitor is not configured until Lab 6" is full credit. "Need more automation" is 1.
- **Priority investment (4):** must name a specific tool or practice.

---

## Automated Grading Workflow

```bash
git clone <student-repo> && cd <student-repo>

# 1. Does the buildspec even parse? (the colon trap)
python3 -c "
import yaml; d=yaml.safe_load(open('buildspec.yml'))
bad=[(p,i) for p,b in d['phases'].items() for i,c in enumerate(b.get('commands',[])) if not isinstance(c,str)]
print('NON-STRING COMMANDS:', bad or 'none')"

# 2. Template validity
aws cloudformation validate-template --template-body file://pipeline.yaml

# 3. Do the tests fail when data is missing?
mv data/features /tmp/stash 2>/dev/null
python3 -m pytest tests/test_data.py -q ; mv /tmp/stash data/features 2>/dev/null
# expect errors, NOT "skipped"

# 4. Does the gate enforce all four thresholds?
grep -E "MIN_AUC_ROC|MIN_PRECISION|MIN_RECALL|LIFT" buildspec.yml

# 5. Gate behaviour, offline - no AWS needed
echo '{"auc_roc":0.80,"baseline_auc_roc":0.795,"precision_top10":0.7,"recall_top10":0.4}' > /tmp/eval_metrics.json
# extract and run their gate; must exit non-zero

# 6. Registry state (if their stack is still up)
aws sagemaker list-model-packages --model-package-group-name <group> \
  --query 'ModelPackageSummaryList[*].[ModelPackageVersion,ModelApprovalStatus]'
```

**If the student has torn down**, AWS checks return nothing. That is correct and required. Grade from their submitted build logs, `pipeline.yaml`, and test output. Do not penalise following the teardown instruction.

---

## Grading Summary Sheet

| Task | Max | Automated? | Notes |
|---|---|---|---|
| 1 — 4 test categories | 12 | Yes | **Check fail-not-skip** |
| 1 — ≥5 feature tests with edge cases | 10 | Partial | Check fixture schema is current |
| 1 — Regression vs champion | 8 | Partial | Must read live registry |
| 2 — 5 stages sequenced | 12 | Partial | CFN validate + read template |
| 2 — Halts on test failure | 10 | Yes | Inject a failure, trigger a build |
| 2 — Promotion only on green gates | 8 | Yes | **The no-lift case** |
| 3 — Champion-challenger criterion | 5 | No | Must be a number |
| 3 — Retraining triggers | 8 | No | Must name the firing service |
| 3 — Experiments ≥3 runs | 4 | Yes | |
| 3 — Lineage metadata | 3 | Yes | |
| 4 — Maturity evidence | 10 | No | Specificity over level claimed |
| 4 — Gap analysis | 6 | No | |
| 4 — Priority investment | 4 | No | |
| **Total** | **100** | | |

---

## Score Deduction Reference

| Issue | Deduction |
|---|---|
| **Tests skip instead of fail on missing data** | **-6 and flag; the gate is decorative** |
| **Gate treats missing metrics as passing** | **-8; an S3 error would promote an unevaluated model** |
| Gate checks AUC only, no baseline lift | -5 |
| Gate does not enforce all four thresholds | -3 per missing threshold |
| Pipeline continues past a failing test stage | -10 (full item) |
| Model auto-approved rather than PendingManualApproval | -5 |
| Feature test fixtures use the retired schema | -4; tests validate a contract that does not exist |
| Hardcoded champion AUC instead of registry lookup | -5 |
| Champion-challenger criterion not numeric | -5 |
| Retraining triggers with no firing mechanism | -5 |
| Three identical Experiments runs | -2 |
| Maturity assessment with no repo evidence | cap at 4/10 |
| `terraform.tfstate` or `.tfvars` in git | -5 + security flag |
| AWS key (`AKIA*`) in git history | -5 + security flag; notify Scott |

---

## What Has Not Been Verified

Honest scope note, so nobody over-claims when a student reports trouble.

**Verified on AWS:** the full CodeBuild path — source download, `pip install` from `requirements.txt`, S3 data staging, all test suites executing in the container, and the quality gate both passing and **failing the build**.

**Not verified:** CodePipeline orchestration itself. No GitHub repo or CodeStar connection was created, so the Source stage, stage-to-stage sequencing, and the SageMaker Pipeline trigger in the `build` phase have never run. `pipeline.yaml` validates against CloudFormation but has not been deployed.

If a student reports a failure in stage wiring or the GitHub trigger, **reproduce before assuming student error** — that path is unproven on our side.

---

## Security Escalation Protocol

If `git log --all -S "AKIA" --oneline` returns results:

1. Note the commit hash
2. Award 0 for the affected task and flag in Canvas comments
3. Email Scott immediately: scott@toborg.com
