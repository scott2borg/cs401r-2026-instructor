---
tags: [CS401R, lab-solution, lab-3, sagemaker, xgboost, rag, agents, TA-guide]
course: CS 401R
lab: 3
status: answer-key
total_points: 100
---

# Lab 3 — Model Development: TA Grading Guide

> **For TA use only.** Do not distribute to students.
> Total points: 100. Track A (35) is required; students choose Track B or C (35). Tasks 3 and 4 are common.

---

## Reference Run

Track A was executed end to end on 2026-07-28 against account `711457211658`. The reference implementation is `models/churn/train_reference.py` in the live repo. These are the actual measured numbers.

| Metric | Reference | Threshold | Margin |
|---|---|---|---|
| AUC-ROC | **0.747** | ≥ 0.72 | +0.027 |
| Recency-only baseline AUC | **0.642** | — | — |
| **Lift over baseline** | **+0.105** | ≥ 0.03 | +0.075 |
| Precision @ top 10% | **0.611** | ≥ 0.50 | +0.111 |
| Recall @ top 10% | **0.293** | ≥ 0.25 | +0.043 |
| `scale_pos_weight` | 3.828 | derived | churn rate 20.75% |
| Train / test | 840 / 360 | — | 1,200 customers |

Every threshold clears with margin, but none trivially. A student who skips feature engineering and trains on recency alone lands at 0.642 and fails the AUC gate outright.

**Feature importance (gain), reference run:**

```
days_since_last_purchase   6.15     avg_order_value          3.54
purchase_frequency_180d    4.62     avg_basket_size_6m       3.37
total_spend_90d            4.49     purchase_frequency_90d   3.00
category_diversity_score   4.44     online_to_store_ratio    2.96
total_lifetime_value       3.68     customer_tenure_days     2.87
purchase_frequency_30d     3.68
```

Recency leads but does not dominate — the spread across the other ten features is what produces the +0.105 lift. A student whose importance plot shows recency at 80%+ has probably leaked it or dropped the behavioural features.

---

## The Platinum Finding — read this before grading Task 1

The reference run's slice evaluation:

| Tier | n | Churn rate | AUC |
|---|---|---|---|
| Bronze | 118 | 25.4% | **0.809** |
| Gold | 59 | 17.0% | 0.745 |
| Silver | 142 | 22.5% | 0.688 |
| **Platinum** | **41** | **7.3%** | **0.430** |

**The model is worse than random on Platinum customers** — the most valuable segment NorthStar has. An aggregate AUC of 0.747 hides it completely.

This is not a defect to fix before shipping the lab. It is the most valuable thing in Lab 3, and it is why Task 1 awards 5 points for slice evaluation.

The cause is visible in the table: Platinum has 41 test customers at a 7.3% churn rate, so roughly **three** positive examples. There is not enough signal to learn from, and `scale_pos_weight` is tuned on the pooled 20.75% rate, which is wrong for this slice.

**Full credit:** the student reports per-tier numbers, flags Platinum explicitly, and reasons about the cause — small sample, class imbalance differing by slice, possibly needing a separate model or a business rule for high-value accounts. Naming the cause matters more than fixing it.

**Not full credit:** aggregate AUC only, or slices reported without comment. A student who presents 0.747 as "the model works" has missed the lesson; if they propose deploying it to drive Platinum retention, call that out directly in feedback.

Expect the exact Platinum AUC to vary between student runs — small n makes it unstable. Any value near or below 0.5 is the expected result. Grade the analysis, not the number.

---

## Task 1 — Churn Prediction Model (35 points)

### Training data from the offline store via Athena (5 pts)

**Pass:** the data-loading path issues an Athena query against the offline store table. No `read_csv` of a feature export, no direct read of `features/customers/` Parquet.

**Two failure modes to expect,** both documented in the skeleton:

1. `TYPE_MISMATCH: Cannot check if double is BETWEEN varchar(10) and varchar(10)` — `event_time` is `Fractional` (epoch seconds) and they compared it to an ISO date string. This fails loudly, so it is usually already fixed by submission.
2. **Duplicate customers.** The offline store is append-only; every re-run of the Lab 2 feature job writes a second record per customer. Without `ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY event_time DESC)` they train on duplicates.

An earlier skeleton draft used `write_time >= (SELECT MAX(write_time) ...)`, which is globally scoped and returns almost nothing — measured at **29 of 1,200 customers**. If a student's row count is implausibly small, this is why.

**Grading note:** award full marks if the Athena path works. If they fell back to reading Parquet directly because Athena fought them, award 2 of 5 and explain that the offline store is the interface Labs 4–6 depend on.

### Meets AUC, precision, recall thresholds (8 pts)

Verify against their reported held-out split. Reference: 0.747 / 0.611 / 0.293.

Note the **recall ceiling**: with ~21% positives, targeting the top 10% caps recall near 0.48. A student reporting recall@10% of 0.9 has computed it wrong — most likely over the full set rather than the top decile.

### Beats the recency-only baseline by ≥ 0.03 AUC (7 pts)

Both AUCs must be reported and the lift computed. Reference lift is **+0.105**, so the bar is not tight — but it is only clearable if the behavioural features are doing real work.

**This is the gate that matters.** A model that cannot beat "days since last purchase" has not earned deployment, and Lab 4's CI pipeline enforces the same threshold. Award 0 if the baseline was never trained, even if the full model's AUC is excellent — the comparison is the deliverable, not the number.

### SageMaker Experiments (5 pts)

≥3 runs visible as trials with logged metrics. Hyperparameter variation is the point; three identical runs earn 2 of 5.

### Model Registry, `PendingManualApproval` (5 pts)

**Never auto-approved.** The reference run produced version 1 in group `northstar-churn-models` with status `PendingManualApproval` and metadata attached:

```
auc_roc 0.747 | baseline_auc_roc 0.642 | auc_lift 0.1051 | feature_count 11
```

Metadata is not required for the points, but a student who attached metrics to the model package has understood why a registry exists. Note it positively.

Award 0 for `Approved` status — that defeats the gate and is exactly the behaviour Lab 5 depends on not happening.

### Slice evaluation (5 pts)

See the Platinum finding above. Requires per-tier AUC and recall plus explicit discussion of any underperforming tier.

---

## Task 2 — Track B or C (35 points)

### Track B: Offer Generation (RAG)

**Corpus reality check.** `northstar-policy-docs/` contains four policy documents and **no product catalog**. Students who wrote retrieval queries for products ("top-rated products", "new arrivals") will show poor context recall and hallucinated product recommendations. The corrected templates warn about this; a student who hit it anyway and diagnosed it in their report has done the right thing — that is a legitimate documented failure case, not a deduction.

**The three planted errors** in `prompt_templates/offer_generation_prompts.md` Template 3:

| Planted | Correct |
|---|---|
| Gold `$2,000 - $9,999.99` | `$2,000 - $4,999.99` |
| Platinum `$10,000+` | `$5,000+` |
| Gold "free expedited shipping on orders over $200" | No tier receives free expedited shipping |

The evaluation checklist scores finding all three. A student who injected Template 3 unchanged will show depressed faithfulness — check whether they diagnosed why.

**RAGAS targets:** faithfulness ≥ 0.80, answer relevance ≥ 0.75, context recall ≥ 0.70.

**Automatic faithfulness failures**, regardless of score: promising a 60-day return window to a non-Platinum customer; offering free expedited shipping; implying final sale is returnable; quoting free shipping on a Mexico order.

**The tier trap.** Test case `CUST-10000588` is Silver at $1,985 lifetime value, $15 below Gold. `POL-LOY-011` defines tier by trailing 12-month spend while Lab 2 derives it from lifetime value, so the two can disagree. A student who noticed and handled it conditionally deserves explicit credit — this is a real production failure mode, not a puzzle.

### Track C: Customer Service Agent

Five required scenarios plus a bonus. **TC-005 is the one that matters**: a six-year Platinum member demanding a return on a final-sale jacket, with an account-closure threat attached.

Correct behaviour: empathetic, cites `POL-RET-004 §4`, declines plainly, escalates. **Conceding the return — or hinting it might be possible — is a fail**, however satisfied the customer sounds. Section 4 overrides tier benefits and the holiday window explicitly, and exceptions sit with the Director of Customer Experience, entirely outside agent authority.

TC-004 (ambiguous) tests whether the agent asks a clarifying question instead of acting. The correct path genuinely differs: no carrier scan for 7 business days means reship or refund; marked-delivered means a 3–5 day trace plus a signed affidavit above $500. An agent that promises a refund before establishing which case applies has failed.

TC-006 (prompt injection) is a bonus. Do not deduct if skipped; it is not one of the five required scenarios.

---

## Task 3 — Design Justification (20 points)

The **feature-value analysis (6 pts)** is where students most often coast. It requires reporting the baseline against the full model with numbers. "Feature engineering improved the model" earns 2 of 6. "Recency-only scored 0.642, the full model 0.747, a lift of +0.105, driven mainly by `purchase_frequency_180d` and `total_spend_90d`" earns 6.

Award credit for honesty. A student whose lift was small and who says so, with a diagnosis, has done better work than one who hides it.

---

## Task 4 — Repository Quality (10 points) and Teardown

The teardown gate caps Task 4 at half credit until evidence is produced. **Endpoints are the cost risk in Lab 3** — hourly billing until explicitly deleted, trivially created from a notebook and forgotten.

`scripts/teardown-lab3.sh` deletes endpoints and endpoint configs, stops in-flight jobs, then verifies. Model Registry entries and Experiments are metadata only, cost nothing, and are deliberately retained.

**Run `aws sagemaker list-endpoints` yourself** when grading. If a student has one running past the deadline, tell them immediately regardless of grading status — it bills against credits they need for Labs 4–7.

---

## Bedrock Access — TA Canary Account

**Students onboard their own AWS accounts. There is no course-managed Bedrock account.** That makes the TA canary account the only early warning you have.

### Why a canary account is necessary

Scott's development account is not representative. It has been used all semester, has billing history, and may have entitlements a fresh Free Tier account does not. Measured on that account on 2026-07-28:

- **400 of 411** Bedrock inference quotas were **zero**
- Anthropic models returned `ResourceNotFoundException: Model use case details have not been submitted`
- Other models returned `ThrottlingException: Too many tokens per day` — which does **not** mean the allowance was used, it means the allowance is zero

A genuinely new student account may behave differently again, in either direction. Assume nothing.

### Setting up the canary

Create a **new** AWS Free Tier account that has never been used, exactly as a student would. Do not reuse an existing account, do not link it to an organisation with pre-approved quotas, and do not enable anything before testing. Its entire value is being indistinguishable from a student's starting position.

### Run the canary before the Pre-Lab 3 exercise is released

Work through `Pre-Lab 3 — Bedrock Access Setup.md` on the canary exactly as written, and record:

| Measure | Why it matters |
|---|---|
| Wall-clock time for the Anthropic use-case form to take effect | Doc claims ~15 minutes; verify |
| Wall-clock time for each quota increase to be approved | **The critical number.** The exercise assumes under two weeks |
| Whether any request was denied or questioned | Students will hit the same and will need guidance |
| Whether the Step 4 verification script passes unmodified | Catches doc rot in model IDs |
| Actual Bedrock spend for one full Track B evaluation run | Doc estimates under $2 |

**If quota approval takes longer than the Sep 17 → Sep 30 window, the exercise dates must move before release.** That is the single decision the canary exists to inform, and it needs answering before the semester starts, not during it.

### During the semester

Keep the canary. When a student reports "Bedrock doesn't work," reproduce on the canary before escalating. It distinguishes a student mistake from an AWS-side change — and AWS changes model availability, inference profile IDs, and default quotas without notice.

---

## Environment Note for macOS Students

XGBoost fails to import on macOS without OpenMP:

```
XGBoostError: Library not loaded: @rpath/libomp.dylib
```

Fix: `brew install libomp`. This hit the reference run and will hit every macOS student who trains locally. It does **not** occur inside SageMaker training jobs, which run Linux containers — so a student who trains only in SageMaker never sees it.

---

## Automated Grading Workflow

```bash
git clone <student-repo> && cd <student-repo>

# 1. Static checks - no AWS needed
grep -rn "read_csv\|read_parquet" models/ | grep -i feature   # should be empty; Athena required
grep -rn "ModelApprovalStatus" models/                        # must be PendingManualApproval
grep -rn "baseline" models/ docs/                             # baseline must exist

# 2. Metrics
cat docs/lab3-model-design.md      # AUC, baseline, lift, precision, recall, slices
# Verify lift = auc_roc - baseline_auc_roc >= 0.03

# 3. AWS state (only if their stack is still up)
aws sagemaker list-model-packages --model-package-group-name <their-group> \
  --query 'ModelPackageSummaryList[*].[ModelPackageVersion,ModelApprovalStatus]'
aws sagemaker list-experiments --query 'ExperimentSummaries[*].ExperimentName'
aws sagemaker list-endpoints    # must be empty at submission

# 4. Track B/C artifacts
ls docs/ notebooks/    # RAGAS scores, or the five agent traces
```

**If the student has torn down** (which the lab requires), the AWS checks return nothing. That is correct. Grade Tasks 1–2 from their submitted metrics, code, and traces. Do not penalise a student for following the teardown instruction.

---

## Grading Summary Sheet

| Task | Max | Automated? | Notes |
|---|---|---|---|
| 1 — Athena offline store | 5 | Partial | Read the data-loading code |
| 1 — Meets thresholds | 8 | Yes | Reference 0.747 / 0.611 / 0.293 |
| 1 — Beats baseline ≥ 0.03 | 7 | Yes | Reference +0.105. 0 if no baseline |
| 1 — Experiments (≥3 trials) | 5 | Yes | |
| 1 — Registry PendingManualApproval | 5 | Yes | 0 if auto-approved |
| 1 — Slice evaluation | 5 | No | **Platinum must be flagged** |
| 2 — System runs end to end | 10 | No | Demo notebook |
| 2 — Evaluation documented | 15 | Partial | RAGAS table or 5 traces |
| 2 — Failure cases + mitigations | 10 | No | ≥2, named and specific |
| 3 — Design justification | 20 | No | Feature-value analysis is the tell |
| 4 — Repo quality | 10 | Partial | Teardown gate applies |
| **Total** | **100** | | |

---

## Score Deduction Reference

| Issue | Deduction |
|---|---|
| **No recency baseline trained** | **-7 (full baseline item)** |
| Model auto-approved in Registry | -5 |
| Aggregate metrics only, no slices | -5 |
| Platinum underperformance not flagged | -3 |
| Features read from Parquet/CSV instead of Athena | -3 |
| Duplicate customers (no per-customer dedup) | -3 and flag; metrics unreliable |
| `churn_label` used as an input feature | -8, leakage; metrics meaningless |
| `churn_risk_score` included with no with/without comparison | -2 |
| recall@10% computed over the full set | -2 |
| Fewer than 3 Experiments trials | -3 |
| Offer promises a benefit the tier lacks (Track B) | -4 per distinct violation |
| Agent concedes the final-sale return (Track C) | -8; TC-005 is the point of the scenario |
| Endpoint still running at submission | -5 and notify the student immediately |
| No teardown evidence | Task 4 capped at 5/10 |

---

## Security Escalation Protocol

If `git log --all -S "AKIA" --oneline` returns results:

1. Note the commit hash
2. Award 0 for Task 4 and flag the violation in Canvas comments
3. Email Scott immediately: scott@toborg.com
