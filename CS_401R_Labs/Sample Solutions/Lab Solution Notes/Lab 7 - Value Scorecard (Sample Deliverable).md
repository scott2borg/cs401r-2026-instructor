---
tags: [CS401R, lab-solution, lab-7, sample-deliverable, economics, business-value]
course: CS 401R
lab: 7
status: sample-deliverable
source: rescued from the retired Sample Solutions/northstar-ai-platform tree, 2026-08-07
---

> **Worked sample deliverable — not a grading guide.** This is an example of what a
> strong Lab 7 submission looks like. The TA grading rubric lives in the companion
> file `Lab 7 - … (Solution).md`. For instructor use; not distributed to students.

# Lab 7 Value Scorecard — NorthStar AI Platform

**Platform:** NorthStar Retail AI Platform  
**Systems evaluated:** Churn Prediction (Track A) + Offer Generation RAG (Track B, staging)  
**Reporting period:** Q4 2026  
**Audience:** CDO, ML Lead, CFO (Section 3); ML Engineering team (Sections 1, 2, 4, 5)  
**Date:** 2026-07-06

---

## Section 1: Metric Pyramid

The metric pyramid organizes NorthStar's measurements from technical system health at the base to business outcomes at the top. Each layer depends on the layer below it — a healthy infrastructure is necessary (but not sufficient) for a healthy model, which is necessary (but not sufficient) for positive business outcomes.

### 1A. Churn Prediction Metric Pyramid

| Layer | Metric | Calculation                                                                                                                                     | Owner | Reporting Frequency | Decision Triggered By |
|-------|--------|-------------|-------|--------------------|-----------------------|
| **Model/System Health** | AUC-ROC | Area under ROC curve on weekly holdout sample (10% of customers, not in training set)                                                           | ML Engineer | Weekly | Retrain if AUC < 0.70 for 2 consecutive weeks |
| **Model/System Health** | p95 Batch Transform Duration | `BatchTransformDurationSeconds` p95, CloudWatch, NorthStar/Inference namespace                                                                  | ML Engineer | Nightly | Instance resize if p95 > 5,400 seconds (90 min) |
| **Model/System Health** | Feature Drift PSI (top-5 features) | Population Stability Index, Evidently Monitor vs. 90-day training baseline                                                                      | ML Engineer | Daily | P2 alert if PSI > 0.20; retrain if PSI > 0.30 |
| **Model Output Quality** | Precision@10% (Calibration Check) | Of the top 10% of customers by predicted churn score, what fraction actually churned within 30 days? Measured monthly on 30-day lagged holdout. | ML Engineer | Monthly | Retrain if Precision@10% < 0.40 for 2 consecutive months |
| **Model Output Quality** | Churn Alert Rate | Customers with churn_probability ≥ 0.60 / total customers scored                                                                                | Analytics team | Daily | Marketing capacity planning input; alert if volume anomaly > ±30% of 7-day baseline |
| **Model Output Quality** | Score Calibration Error | Expected churn rate (mean of top-decile scores) vs. actual observed churn rate in top decile                                                    | ML Engineer | Monthly | Flag for calibration refit if error > 5 percentage points |
| **User Experience** | Offer Delivery Rate | Offers sent to flagged customers (churn_probability ≥ 0.60) / total customers flagged                                                           | Retention team | Daily | Pipeline health check; alert if < 85% (indicates offer generation or email delivery failure) |
| **User Experience** | Offer Click-Through Rate (CTR) | Offer emails opened and clicked / offers delivered                                                                                              | Marketing team | Daily | Offer relevance proxy; alert if CTR drops > 20% vs. prior 7-day average |
| **User Experience** | Offer Opt-Out Rate | Customers unsubscribing after receiving retention offer / total offer recipients                                                                | Marketing team | Weekly | High opt-out rate signals offer targeting is wrong (wrong customers flagged or offers irrelevant) |
| **Business Outcome** | 30-Day Retention Rate (Intervention Group) | Flagged customers who made a purchase within 30 days of receiving an offer / total flagged customers who received offers                        | CDO | Monthly | Primary ROI metric; input to budget decision |
| **Business Outcome** | Incremental Retention Rate | Retention rate (intervention group) − Retention rate (holdout group, 20% of flagged customers who received no offer)                            | CDO | Monthly | True causal measure of AI impact (requires holdout) |
| **Business Outcome** | Prevented Churn Revenue | Incremental retained customers × average customer LTV                                                                                           | CFO | Monthly | Business case validation; determines budget allocation for next quarter |

### 1B. Offer Generation RAG Metric Pyramid (Track B — Staging)

| Layer | Metric | Calculation | Owner | Reporting Frequency | Decision Triggered By |
|-------|--------|-------------|-------|--------------------|-----------------------|
| **System Health** | RAG Pipeline Latency (p95) | Time from churn score input to offer text generation, p95, CloudWatch | ML Engineer | Daily | Investigate if p95 > 30 seconds per customer batch |
| **System Health** | Bedrock API Error Rate | Failed Bedrock InvokeModel calls / total calls | ML Engineer | Daily | Page on-call if error rate > 5% in any 1-hour window |
| **Retrieval Quality** | RAGAS Context Recall | Fraction of answer that is grounded in retrieved product catalog context | ML Engineer | Weekly | Retune retrieval if Context Recall < 0.75 |
| **Retrieval Quality** | RAGAS Faithfulness | Fraction of offer claims attributable to retrieved context (no hallucinations) | ML Engineer | Weekly | Block promotion to production if Faithfulness < 0.85 |
| **Generation Quality** | Offer Relevance Score | Human evaluator rating (1–5) of offer relevance to customer segment, weekly sample of 50 offers | ML Lead + Marketing | Weekly | Retune prompts if average relevance < 3.5/5 |
| **User Experience** | Offer CTR (RAG-generated vs. template) | A/B test: RAG-generated offer CTR vs. legacy template CTR | Marketing team | Weekly (during A/B test) | Promote RAG to production if CTR > template by ≥ 5pp with statistical significance (p < 0.05) |
| **Business Outcome** | Incremental Retention Attributed to RAG Offers | Retention rate (RAG offer group) − Retention rate (template offer group) | CDO | Monthly | Budget expansion decision; requires 90-day A/B test for statistical power |

### 1C. Causal Chain Assessment

Not all metric connections are validated. Below is an explicit audit of assumed vs. validated causal links.

**Churn Prediction:**

| Causal Link | Status | Validation Method | Gap |
|-------------|--------|------------------|-----|
| AUC-ROC → Precision@10% | Validated | ROC measures ranking quality; Precision@10% measures the consequence of acting on that ranking. Both measured on same holdout set. | None — both are output of the same evaluation pipeline |
| Precision@10% → Score Calibration | Validated | Monthly calibration check compares predicted top-decile churn rate to actual 30-day churn rate | None |
| Churn Alert Rate → Offer Delivery Rate | Validated | Every flagged customer is routed to offer generation; delivery rate measures pipeline completeness | None — 100% routing enforced in code |
| Offer CTR → 30-Day Retention | **Assumed** | Experiment needed: 90-day randomized holdout. Send offers to 80% of flagged customers; withhold from 20%. Compare 30-day purchase rates between groups. n = ~3,500 per cohort (retention team flags ~3,500/day); 80/20 split gives n=2,800 treatment, n=700 control. | **Active gap — holdout A/B test in progress, results Q1 2027** |
| 30-Day Retention → Prevented Revenue | **Assumed** | Assumes retained customers' LTV is unchanged by the retention event. Validates via 6-month LTV tracking on the retained cohort vs. organic-retained customers. | **Active gap — 6-month LTV tracking not yet instrumented** |

---

## Section 2: Unit Economics

### Cost Per 1,000 Predictions (Churn Model)

Calculation basis: 250,000 customers scored nightly on ml.m5.xlarge (~$0.269/hr). Transform duration: ~45 minutes (0.75 hr).

| Cost Component | Calculation | Cost per Run | Cost per 1,000 Customers |
|----------------|-------------|-------------|--------------------------|
| Inference compute | $0.269/hr × 0.75 hr | $0.202 | $0.202 / 250 = $0.0008 |
| Amortized training | $0.269/hr × 1 hr/week ÷ 7 days = $0.038/day | $0.038 | $0.038 / 250 = $0.0002 |
| Glue pipeline (data prep) | 10 DPUs × $0.44/DPU-hr × 0.5 hr ÷ 250K customers | $2.20 | $2.20 / 250 = $0.0088 |
| Feature Store (offline reads) | $0.00025/1,000 GetRecord calls × 250K = $0.063 (offline store) | $0.063 | $0.063 / 250 = $0.0003 |
| CloudWatch custom metrics | $0.30/metric/month ÷ 30 days × 6 metrics | $0.06 | negligible |
| **Total per run** | | **~$2.56** | **~$0.011 per 1,000 customers** |

**Monthly inference cost for 250K customers (30 runs):** ~$76.80 compute + Glue = ~$91/month for inference + data pipeline.

### Full Platform Monthly Cost Breakdown

| Cost Category | Monthly Cost | Assumptions |
|---------------|-------------|-------------|
| Compute — training | $45 | Weekly XGBoost retraining, ml.m5.xlarge, 1 hr/run × 4.3 weeks |
| Compute — inference (Batch Transform) | $12 | Nightly, ml.m5.xlarge, 45 min/run × 30 days |
| Data storage + transfer | $38 | ~1TB S3 across 4 buckets (raw, processed, features, artifacts); $23/TB/month standard; Glue DPU-hours included in pipeline row |
| Data pipeline (Glue ETL) | $29 | 10 DPUs × $0.44/hr × 0.5 hr/day × 30 days |
| Third-party APIs (generative AI) | $65 | Bedrock for offer generation (Track B, staging): Claude 3 Haiku, ~150K tokens/day at $0.00025/1K input tokens; RAGAS evaluation: ~$10/week |
| Human labor (maintenance) | $480 | 6 hrs/month (model monitoring review, incident response, ad hoc analysis) × $80/hr (graduate student equivalent rate) |
| Platform and tooling | $28 | SageMaker Feature Store ($0.25/GB offline + $0.00014/read), CloudWatch ($0.30/metric/month × 12 custom metrics), CodePipeline ($1/pipeline/month) |
| **Total** | **$697/month** | Single-region, no HA NAT, student account pricing |

### Cost Optimization Analysis

**Identified optimization: Switch inference instance to ml.c5.2xlarge**

The XGBoost Batch Transform job is CPU-bound, not memory-bound. ml.m5.xlarge (4 vCPUs, 16 GB RAM) allocates more memory than XGBoost uses during inference. ml.c5.2xlarge (8 vCPUs, 16 GB RAM) offers the same memory at lower cost ($0.384/hr) and higher vCPU count — which can be leveraged via SageMaker's multi-instance or parallel batch processing.

Wait: ml.c5.2xlarge is more expensive per hour than ml.m5.xlarge ($0.384 vs. $0.269/hr). The optimization is in completion time: ml.c5.2xlarge completes the 250K-customer transform in approximately 28 minutes (vs. 45 minutes for ml.m5.xlarge, due to higher vCPU count and compute-optimized architecture).

| Instance | Cost/hr | Duration | Cost/run | Monthly (30 runs) |
|----------|---------|---------|---------|-------------------|
| ml.m5.xlarge (current) | $0.269 | 45 min | $0.202 | $6.06 |
| ml.c5.2xlarge (proposed) | $0.384 | 28 min | $0.179 | $5.37 |

**Savings: $0.69/month on inference compute.** This is not the primary motivation for the switch. The real benefit is a 17-minute reduction in batch duration — the nightly job completes earlier, reducing the window where downstream offer generation must wait.

**Tradeoff:** ml.c5.2xlarge requires re-testing the transform job to validate output correctness on the new instance type. Estimated effort: 1 hour. Do this as part of the next scheduled retraining run, not as an emergency change.

**Other optimizations evaluated and not recommended:**

| Optimization | Estimated Savings | Why Not Recommended |
|--------------|------------------|---------------------|
| Switch to Spot Instances for training | ~60% training cost reduction ($27/month → $11/month) | Spot interruption during training requires checkpoint/resume infrastructure — 2+ week engineering effort. Savings: $16/month. Not worth it at this scale. |
| Reduce CloudWatch custom metric count | $5/month | Removing business metrics (Layer 5) would blind the team to the most important signals. Not recommended. |
| Eliminate weekly retraining (retrain monthly) | ~$35/month | Risk: model quality degrades between retrains as seasonal drift accumulates. Quality cost exceeds compute savings. |

---

## Section 3: Executive Value Scorecard (Q4 2026)

> **Audience:** CDO, CFO. No ML jargon. All claims backed by a number.

---

### NorthStar AI Platform — Q4 2026 Value Scorecard

**What the platform does:**
NorthStar's AI Platform identifies customers who are at risk of stopping their relationship with NorthStar, generates personalized retention offers for those customers, and measures whether the offers are working. The goal is to keep customers who would otherwise leave — increasing their long-term value to the business.

**How it works (without the jargon):**
Every night, the system scores all 250,000 active customers on a scale of 0 to 1 representing their probability of not making a purchase in the next 30 days. Customers above 0.60 on that scale are flagged for retention outreach. The offer generation system then creates a personalized offer based on that customer's purchase history and loyalty tier.

---

### Systems in Production

| System | What It Does | Key Business Metric | Current Performance | vs. Q4 Projection | Status |
|--------|-------------|---------------------|---------------------|-------------------|--------|
| Churn Prediction | Identifies at-risk customers | % of actual churners correctly identified in top 10% of alerts (Recall@10%) | 39% of customers who churned were in the top 10% of scores | Projection: 35% | On Track |
| Offer Generation | Generates personalized retention offers | Retention offer click-through rate | 22% of offers delivered resulted in a click | Projection: 15% | Exceeds Projection |

---

### How We Measure Business Impact

**Important: CTR is not the same as retention.** A customer clicking an offer has not yet been retained. The team is currently running a controlled experiment to measure the true causal impact:

- 80% of flagged customers receive a retention offer (treatment group)
- 20% of flagged customers receive no offer (holdout control group)
- After 30 days, the retention rate in each group is compared

The difference between the two groups is the impact attributable to the AI system — customers who would have stayed anyway are in both groups and cancel out.

**Current experiment status:** Running. Statistically significant results available Q1 2027 (90 days of data needed to observe full churn signal).

**Interim result (early, not statistically significant):** The treatment group is showing a 4.2 percentage point higher 30-day retention rate than the holdout group. At 250K customers with approximately 3,500 flagged daily, a 4.2pp improvement would represent approximately 147 additional retained customers per day. At an average LTV of $340, that is approximately $50,000 per month in prevented revenue loss — before subtracting offer costs.

**This number is preliminary and should not be used for budget decisions until the 90-day experiment completes.**

---

### Investment Recommendations

| System | Recommendation | Rationale | Investment Required |
|--------|----------------|-----------|---------------------|
| Churn Prediction | **Expand: increase scoring frequency from nightly to 3× per week for high-value (Platinum) customers** | Platinum customers have higher LTV and churn faster when dissatisfied — 72-hour detection lag is too slow. Nightly scoring of all 250K is appropriate for Bronze/Silver; Platinum tier (approximately 8,000 customers) warrants tighter monitoring. | 1 day engineering to add a separate scoring job for Platinum customers; $2/month additional compute |
| Offer Generation | **Hold: maintain current staging deployment, complete 90-day A/B test before expanding budget** | Click-through rate exceeds projection, but clicks do not yet demonstrate retention impact. Expanding offer generation budget before confirming causal retention impact is premature investment. Complete the holdout experiment first. | No additional investment until Q1 2027 results |

---

### Open Questions (Decisions Pending Data)

1. **Does offer CTR translate to 30-day retention?** Holdout A/B test in progress. Results expected Q1 2027. Do not expand offer generation investment until answered.

2. **Does the model perform equally well for customers with < 180 days of tenure?** New customers have shorter purchase history — the model's 90-day features may not generalize. Slice evaluation pending; ML Lead to report at next quarterly review.

3. **What is the true cost per prevented churn?** Requires 6-month LTV tracking on the retained cohort. Without this, the ROI calculation uses assumed LTV ($340) that may not reflect actual behavior of retained customers (some may churn again within 6 months, reducing LTV).

4. **What is the optimal churn probability threshold for offer targeting?** Currently 0.60. Lowering to 0.50 would flag more customers (increasing retention team workload and offer costs); raising to 0.70 would miss borderline-risk customers. Threshold optimization requires the 90-day causal experiment results to determine which threshold maximizes incremental retention per dollar of offer spend.

---

## Section 4: Value Methodology — Churn Prediction System

The following table documents the complete measurement methodology for the churn prediction business case. All 12 fields are required before a business ROI claim can be made.

| Field | Value |
|-------|-------|
| **System name** | NorthStar Churn Prediction |
| **Business problem being solved** | Customers at risk of churning are not receiving retention outreach until they've already left, because there is no systematic way to identify them before they stop purchasing. Approximately 12% of the customer base churns in any 90-day window; the top 10% by predicted churn risk accounts for ~39% of actual churners. |
| **Decision the system enables** | Which customers to contact with a retention offer in the next 24 hours, and with what priority. Without the model, the retention team uses last-purchase date only — no probability ranking. |
| **Who makes the decision** | Retention marketing team (day-to-day); CDO (budget allocation); CFO (LTV investment authorization) |
| **Counterfactual (what happens without the system)** | Retention team manually segments customers by last purchase date (> 60 days = outreach). This captures approximately 15% of actual churners in the top-10%-of-effort segment — versus 39% with the AI model. |
| **Primary outcome metric** | Incremental 30-Day Retention Rate: (Retention rate, offer recipients) − (Retention rate, holdout group) |
| **How primary metric is measured** | Randomized holdout: 20% of customers flagged by the model receive no offer. 30-day purchase behavior tracked in POS system. Groups compared after 30 days. |
| **Secondary outcome metrics** | (1) Prevented Churn Revenue = incremental retained customers × avg LTV; (2) Retention team cost per retained customer (offer cost + labor) |
| **Time to observe outcome** | 30 days (churn observation window) + 14 days data processing = 44 days minimum per cohort |
| **Attribution approach** | Randomized holdout (strongest available method short of a true RCT). The holdout group is randomly assigned from the population flagged by the model — selection bias is minimal because both groups are drawn from the same model-flagged pool. |
| **Known limitations** | (1) Holdout is 20% — statistical power to detect a 2pp improvement requires n=3,500 per cohort, met after ~1 week of daily scoring. (2) Spillover: if flagged customers discuss offers with non-flagged friends who then purchase, the holdout effect is understated. (3) Hawthorne effect: retention team may work harder knowing some customers have no offer — partially mitigated by blind assignment (team does not know which customers are in holdout). |
| **Confidence level** | **Medium** — holdout design is rigorous, but only 60 days of data accumulated. Statistical significance at α=0.05 requires 90 days. Current point estimate (4.2pp incremental retention) is directionally encouraging but not yet decision-quality evidence. |

---

## Section 5: Measurement Reflection

**Two weakest assumptions in the NorthStar measurement framework:**

### Assumption 1: Offer CTR implies retention intent

The measurement framework uses click-through rate as the primary user-experience metric between offer delivery and 30-day retention. This assumes that clicking an offer is a meaningful signal of retention intent — that customers who click are more likely to complete a purchase than those who do not click.

This assumption fails in at least two scenarios. First, a customer may click out of curiosity, not purchase intent — particularly for offers with deceptive subject lines or generic discounts that don't match the customer's preferences. Second, a customer planning to purchase anyway (regardless of the offer) will click if the offer is visible — making CTR a poor measure of offer causal impact for already-committed customers.

**Experiment to validate:** Track 30-day purchase rate for three groups — (a) customers who received the offer and clicked, (b) customers who received the offer and did not click, and (c) customers who received no offer. If group (a) has meaningfully higher retention than group (b), and both have higher retention than group (c), CTR is a valid intermediate signal. If group (a) and group (b) have similar retention rates, CTR has no value as a metric.

Design: 90 days, n = 5,000 per group, primary metric = 30-day purchase rate, power = 80% at α = 0.05 for a 3 percentage point difference.

### Assumption 2: The 90-day churn definition is the right optimization target

The model is trained to predict "no purchase in the next 30 days" as the churn label, with features computed over a 90-day lookback window. This definition is operationally convenient — it matches the retention team's planning horizon — but it is not obviously the correct definition of churn for the business.

A customer who takes 95 days between purchases is not meaningfully different from one who takes 89 days — yet the label treats them as churn vs. not-churn. More importantly, a customer who makes one small purchase every 28 days to avoid the "churn" label is not a healthy customer by revenue standards. The model optimizes for purchase frequency, not purchase value.

Alternative hypothesis: A revenue-weighted churn definition (e.g., "probability that a customer's next-90-day spend is less than 50% of their prior-90-day spend") would better capture the business's actual loss from at-risk customers, and would not be gamed by small-purchase behavior.

**Experiment to validate:** Retrain two model variants — current (binary churn label) and a revenue-weighted regression model. Score a test cohort with both. After 90 days, compare which model's high-risk customers produced more incremental revenue when targeted with retention offers. Run for two full quarters to capture seasonality.

### Least-Observed Layer: User Experience

The user experience layer (offer delivery rate, CTR, opt-out rate) is the least instrumented layer in the current system. The chain from model output to customer interaction passes through the email marketing platform, which is a separate system operated by the Marketing team. Currently:

- NorthStar's AI system writes a customer_id + offer_text to an S3 file.
- Marketing's email system reads that file and sends emails — but does not write back to NorthStar's data systems.
- CTR and opt-out data live in the email platform's database, not in NorthStar's analytics environment.

This means the causal chain from `churn_probability` → `offer delivered` → `offer clicked` → `purchase made` cannot currently be traced in a single data system. The ML team sees model outputs; the Marketing team sees email performance; neither team sees the end-to-end chain.

**Instrumentation needed:**

1. A tracking pixel in each offer email that fires a CloudWatch event with `{customer_id, offer_id, event_type: "delivered|opened|clicked|converted"}` — linking email behavior back to the customer_id that triggered the offer.
2. A purchase-completion webhook from the POS system that fires when a customer makes a purchase within 30 days of receiving an offer, updating the offer record with the conversion event.
3. A joined view in Athena: `churn_score INNER JOIN offer_events INNER JOIN purchase_events` — allowing the full causal chain to be queried.

**Estimated implementation effort:** 2 weeks engineering (tracking pixel + webhook + Athena view), 1 week QA (validating event delivery under load, testing opt-out compliance). Total: 3 weeks.

**Business impact of closing this gap:** The end-to-end instrumentation would convert the measurement framework from "assumed causal chain" to "measured causal chain" — enabling precise attribution of revenue impact to specific offer types, customer segments, and model score bands. This would directly inform the Q1 2027 budget decision for offer generation expansion.
