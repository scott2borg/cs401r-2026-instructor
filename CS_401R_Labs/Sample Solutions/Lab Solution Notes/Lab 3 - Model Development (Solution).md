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

Track A was re-executed end to end on **2026-08-02** against account `711457211658`, as part of a full Labs 2→5 verification pass on the **10,000-customer** dataset. The reference implementation is `models/churn/train_reference.py` — the Athena path Task 1 requires, with a deterministic `ORDER BY customer_id` pull. **These are the canonical numbers for the course.**

| Metric | Reference | Threshold | Verdict |
|---|---|---|---|
| AUC-ROC | **0.7696** | *none — report only* | — |
| Recency-only baseline AUC | **0.7233** | — | — |
| **Lift over baseline** | **+0.0464** | 95% CI excludes 0 | **CI [0.0254, 0.0670] — PASS** |
| Precision @ top 10% | **0.6833** | ≥ 0.50 | +0.1833 |
| Recall @ top 10% | **0.3106** | ≥ 0.25 | +0.0606 |
| `scale_pos_weight` | 3.545 | derived | churn rate 22.0% |
| Train / test | 6,999 / 3,000 | — | ~10,000 customers |
| Model package | **v4** | — | `northstar-churn-models` |

**Everything published before 2026-08-02 is superseded, including the 0.7276 set that briefly replaced the 0.747 set.** Those came from a 1,200-customer dataset on a non-deterministic Athena pull; the same code produced AUC anywhere in 0.7276–0.7431 on identical data. Full evidence in `docs/lab3-metric-stability.md`. If a student cites a figure near 0.747 or 0.293, they are working from a stale handout — tell them which document is current rather than marking it wrong.

**Two things changed that affect how you grade:**

1. **There is no AUC threshold any more.** Across 200 splits the old ≥ 0.72 gate failed on 58% of them, so it graded the random seed. Students report AUC; it is not a pass/fail criterion. Do not deduct for an AUC below 0.72.
2. **The lift is much smaller than the course used to claim** — 0.0464, not 0.105. The recency-only baseline is genuinely strong at this scale (0.7233). A student who reports a small lift and says so honestly is *correct*, not weak. What earns the points is the interval: does the CI exclude zero?

**Feature importance (gain), reference run:**

```
days_since_last_purchase  33.26     total_lifetime_value      9.94
purchase_frequency_180d   18.75     category_diversity_score  8.36
purchase_frequency_30d    14.79     total_spend_90d           8.30
avg_order_value           12.24     purchase_frequency_90d    8.27
total_lifetime_value       9.94     online_to_store_ratio     7.82
customer_tenure_days       7.28     avg_basket_size_6m        6.91
```

Recency leads clearly — about 25% of total gain — but the behavioural features carry the rest, and that spread is what produces the +0.0464 lift. A student whose importance plot shows recency at 80%+ has probably leaked it or dropped the behavioural features.

---

## The Slice Finding — read this before grading Task 1

The reference run's slice evaluation, 10,000-customer dataset, 3,000-row test set:

| Tier | n | Churn rate | AUC |
|---|---|---|---|
| **Platinum** | 307 | 6.8% | **0.8483** |
| Gold | 483 | 10.8% | 0.7559 |
| Bronze | 1,071 | 33.7% | 0.7442 |
| **Silver** | **1,139** | 19.8% | **0.6935** |

**The model is weakest on Silver — its largest tier — and strongest on Platinum.** The aggregate AUC of 0.7696 hides a spread of about 0.15 between best and worst slice. That spread is the reason Task 1 awards 5 points for slice evaluation, and it is stable: across 40 splits Platinum is the best slice 95% of the time and Silver the worst 77.5% of the time.

The business reading is what students should reach for. Silver is the biggest contactable population and the one where the ranking is least trustworthy, so a retention budget spent top-down on model score gets its least reliable guidance exactly where most of the money goes. Platinum churns rarely (6.8%) and is easy to rank — but there is little there to save.

### The second lesson, and it is the better one

**Until 2026-08-02 this section taught the opposite finding, and it was wrong.**

On the previous 1,200-customer dataset, Platinum held about **33 test customers with roughly 2 churners**. Its measured AUC was 0.430, and the course taught that as a headline result: *the model is worse than random on your most valuable segment.* It was noise. Across 200 splits of that data, Platinum's AUC ranged from **0.00 to 1.00** with a standard deviation of 0.20, and came out "worse than random" on only 34.9% of them. At 307 test customers the same analysis on the same generator says Platinum is the model's **best** slice.

This is worth teaching directly, and it is worth more than the original finding:

> A slice metric without an `n` next to it is not a measurement. The same analysis, run carefully, on data that was merely too small, produced a confident conclusion that was **exactly backwards** — and it survived review, got written into a rubric, and was taught.

**Full credit** now requires the student to report per-tier AUC **with test-set n**, identify the weakest tier, reason about the cause, and — this is the new part — state which of their slices are too small to support a conclusion. A student whose Platinum slice has 12 customers and who says "I cannot conclude anything from this" has done *better* work than one who reports a confident number.

**Not full credit:** aggregate AUC only; slices reported without `n`; or a strong claim about a slice with a handful of positives. A student who presents a healthy aggregate AUC as "the model works" has missed the lesson; if they propose deploying it to drive Silver retention without noting the weaker ranking there, call that out directly in feedback.

Expect per-tier values to vary between student runs. Grade the analysis and the sample-size reasoning, not the third decimal.

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

Verify against their reported held-out split. Reference: **AUC 0.7696 / P@10% 0.6833 / R@10% 0.3106**. Only precision and recall are gated; AUC is reported, not thresholded.

Note the **recall ceiling**: with ~22% positives, targeting the top 10% caps recall near 0.45. A student reporting recall@10% of 0.9 has computed it wrong — most likely over the full set rather than the top decile.

### Beats the recency-only baseline by ≥ 0.03 AUC (7 pts)

Both AUCs must be reported, the lift computed, **and a 95% CI on the lift shown**. Reference lift is **+0.0464, CI [0.0254, 0.0670]** — the interval excludes zero, which is the pass condition. A point estimate with no interval earns 3 of 7 no matter how large the lift looks. The bar is genuinely tighter than the old ≥ 0.03 threshold: on the previous 1,200-customer dataset the CI excluded zero on only 30% of splits, which is what a 360-row test set can actually support.

**This is the gate that matters.** A model that cannot beat "days since last purchase" has not earned deployment, and Lab 4's CI pipeline enforces the same threshold. Award 0 if the baseline was never trained, even if the full model's AUC is excellent — the comparison is the deliverable, not the number.

### MLflow App experiment tracking (5 pts)

**The tool changed 2026-08-07.** This item was "SageMaker Experiments"; it is now a **SageMaker MLflow App**. SageMaker Experiments' Python SDK tracking is Studio-Classic-only and AWS now points everyone at MLflow.

≥3 runs with logged params **and** metrics, retrievable via `mlflow.search_runs`. Hyperparameter variation is the point; three identical runs earn 2 of 5.

Verified 2026-08-07 on account `711457211658`: `create-mlflow-app` succeeded from a plain IAM user with **no SageMaker Studio domain**, reached `Created` in **4 min 52 s**, served **MLflow 3.10.1**, and returned three logged runs through `search_runs` with params and metrics intact.

> ## ⚠ Watch for the wrong MLflow — this is the expensive mistake in the course
>
> | | **MLflow App** ✅ | MLflow **Tracking Server** ❌ |
> |---|---|---|
> | API | `CreateMlflowApp` | `CreateMlflowTrackingServer` |
> | Cost | free | **$0.60/hr** until deleted |
>
> **A tracking server breaches the entire $10 course budget in 16.7 hours and costs ~$43 over a weekend** — more per hour than any endpoint in this course. It is not an endpoint, so a student checking "did I delete my endpoints?" will not find it. Most tutorials describe the tracking server because it shipped first.
>
> `teardown-lab3.sh` and `preflight-lab6.sh` now both check for it. **If a student's teardown evidence shows one, that is a real charge on a real card — tell them immediately rather than noting it in feedback.** Stopping is not deleting.

**Two failure modes to expect.** A student on a stock AWS CLI gets `Invalid choice: 'create-mlflow-app'` — the API postdates many installed versions, and the error reads like a typo rather than a version problem. And a student who installs `mlflow` without `sagemaker-mlflow` gets a connection error that never mentions credentials; the second package is the SigV4 auth plugin for `arn:aws:sagemaker:...` tracking URIs.

**Accept a Tracking Server if they used one and deleted it.** The tracking is equivalent; only the billing model differs. Note the cost lesson and move on — do not make them redo the work.

### Model Registry, `PendingManualApproval` (5 pts)

**Never auto-approved.** The reference run produced version **2** in group `northstar-churn-models` with status `PendingManualApproval` and metadata attached:

```
auc_roc 0.7696 | baseline_auc_roc 0.7233 | auc_lift 0.0464 | precision_top10 0.6833
recall_top10 0.3106 | churn_rate 0.22 | slice_worst_tier Silver | slice_worst_auc 0.6935
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

> **No student can use managed Bedrock Agents. Verified 2026-08-07.** `CreateAgent` returns `AccessDeniedException: Bedrock Agents is in Maintenance Mode. New agent creation is not available for accounts without prior service usage.` AWS closed it to accounts without prior usage; every student account is new, and the reference account (which has zero existing agents) is refused too. **A student who reports this has found the truth, not failed the task** — do not tell them to fix their IAM role, because nothing in IAM fixes it.
>
> The expected path is a **client-side ReAct loop over `bedrock-runtime`**, which is unaffected. Reference implementation: `models/agent/customer_service_agent.py`. Verified working end to end on 2026-08-07 — one tool round through `query_policy`, correctly grounded answer, 3,188 in / 260 out tokens, ~$0.0045 per turn.
>
> `models/agent/bedrock_agent_setup.py` is retained as a worked example of the managed architecture and now fails fast with an explanation rather than a raw `AccessDeniedException`. Do not assign it.
>
> **Two model-ID traps, both verified.** Claude 4.5+ requires a cross-region inference profile — `us.anthropic.claude-haiku-4-5-20251001-v1:0` works, the bare `anthropic.claude-haiku-4-5-20251001-v1:0` returns `ValidationException: Invocation ... with on-demand throughput isn't supported`. And Claude 3 Haiku is now `LEGACY`: *"Access denied. This Model is marked by provider as Legacy and you have not been actively using the model in the last 30 days."* A student whose agent cannot reach the model is almost certainly on one of these two, not on a broken prompt.

> **The starter kit's escalation check never fired. Fixed 2026-08-08 — regrade accordingly if anyone submitted against the old harness.**
>
> `evaluation_harness.py` decided escalation with `"escalate" in tool_calls`, which is exact **list membership** — and the tool is named `escalate_to_human`, so it was always `False`. The fallback looked for the literal string `human_agent` in the response, which no natural-language reply contains. Net effect: **every scenario with `should_escalate=True` failed regardless of how correctly the agent behaved**, including TC-005.
>
> Both evaluators now call one shared `detect_escalation()` helper. Verified against the reference agent: TC-005 correctly passes (`escalated=True`), and a plain order-status reply still returns `False`, so the fix does not simply make everything pass.
>
> **Harness now runs the local ReAct agent.** Its Track C path previously required `--agent-id`/`--agent-alias-id`, which only `CreateAgent` produces — the blocked call. `LocalAgentEvaluator` takes a student-supplied `invoke_fn(message, session_id) -> (reply, [tool_names])`; the managed path is retained for older accounts. Scoring logic is shared, so the two paths cannot grade the same agent differently.
>
> **Reference-agent result: 5/6.** TC-003 legitimately fails — asked to return 45-day-old hiking boots (Gold member, knee injury), the agent asks for an order ID instead of calling `query_policy` and escalating. That is a real gap in the reference implementation, not a harness artifact; **do not treat 6/6 as the expected score**, and a student whose agent handles TC-003 correctly has beaten the reference.

Five required scenarios plus a bonus. **TC-005 is the one that matters**: a six-year Platinum member demanding a return on a final-sale jacket, with an account-closure threat attached.

Correct behaviour: empathetic, cites `POL-RET-004 §4`, declines plainly, escalates. **Conceding the return — or hinting it might be possible — is a fail**, however satisfied the customer sounds. Section 4 overrides tier benefits and the holiday window explicitly, and exceptions sit with the Director of Customer Experience, entirely outside agent authority.

TC-004 (ambiguous) tests whether the agent asks a clarifying question instead of acting. The correct path genuinely differs: no carrier scan for 7 business days means reship or refund; marked-delivered means a 3–5 day trace plus a signed affidavit above $500. An agent that promises a refund before establishing which case applies has failed.

TC-006 (prompt injection) is a bonus. Do not deduct if skipped; it is not one of the five required scenarios.

---

## Task 3 — Design Justification (20 points)

The **feature-value analysis (6 pts)** is where students most often coast. It requires reporting the baseline against the full model with numbers. "Feature engineering improved the model" earns 2 of 6. "Recency-only scored 0.7233, the full model 0.7696, a lift of +0.0464 with a 95% CI of [0.0254, 0.0670], driven mainly by `purchase_frequency_180d` and `purchase_frequency_30d`" earns 6. Note the honest version of this answer is now less impressive than it used to be — the baseline is strong. Reward the student who says so.

Award credit for honesty. A student whose lift was small and who says so, with a diagnosis, has done better work than one who hides it.

---

## Task 4 — Repository Quality (10 points) and Teardown

The teardown gate caps Task 4 at half credit until evidence is produced. **Endpoints are the cost risk in Lab 3** — hourly billing until explicitly deleted, trivially created from a notebook and forgotten.

`scripts/teardown-lab3.sh` deletes endpoints and endpoint configs, stops in-flight jobs, then verifies. Model Registry entries cost nothing and are deliberately retained, as is the **MLflow App** — it is serverless and free, and Labs 4 and 6 log to it. The script does check for an MLflow **Tracking Server**, which bills \$0.60/hr.

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
aws sagemaker list-mlflow-apps --query 'MlflowAppSummaries[*].[Name,Status]'
aws sagemaker list-mlflow-tracking-servers   # MUST be empty - $0.60/hr if not
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
| 1 — Meets P@10%/R@10% thresholds | 8 | Yes | Reference 0.6833 / 0.3106. **No AUC gate** |
| 1 — Beats baseline, CI excludes 0 | 7 | Yes | Reference +0.0464, CI [0.0254, 0.0670]. 3 of 7 if no CI; 0 if no baseline |
| 1 — MLflow App (≥3 runs) | 5 | Yes | |
| 1 — Registry PendingManualApproval | 5 | Yes | 0 if auto-approved |
| 1 — Slice evaluation | 5 | No | **Per-tier n required**; weakest tier (Silver) flagged; small slices called out as inconclusive |
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
| Fewer than 3 MLflow runs | -3 |
| MLflow **Tracking Server** left running at submission | flag immediately — live \$0.60/hr charge |
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
