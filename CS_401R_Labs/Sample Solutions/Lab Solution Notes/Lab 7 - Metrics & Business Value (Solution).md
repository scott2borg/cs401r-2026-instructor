---
created: 2026-07-06
updated: 2026-08-01
tags:
  - cs401r
  - sample-solution
  - lab7
  - metrics
  - business-value
  - unit-economics
  - executive-scorecard
  - roi
lab_number: 7
status: rewritten-against-measured-numbers
supersedes: version dated 2026-07-06 (see "What changed" below)
---

# Lab 7 — Metrics & Business Value (Solution Notes)

**This note was rewritten on 2026-08-01 against the audited Lab 7 spec.** The prior version predated any measured cost or model data and contained figures that are now known to be wrong or unexecutable. See *What changed and why* at the end before grading against anything you remember.

Every number below is derived from the AWS Price List API (verified 2026-08-01, us-east-1) or from Cost Explorer usage quantities on account `711457211658` for July 2026. Arithmetic is reproducible; the script is at the end.

---

## Grading posture

Lab 7 produces prose and arithmetic, not infrastructure. That makes it the easiest lab to grade generously and the easiest to grade badly.

**The discriminator is not whether the student's numbers match these.** Reasonable assumptions produce a wide spread. The discriminator is whether **every number is traceable to a stated assumption and a published rate**, and whether the student noticed the things the platform is actually telling them.

Three findings separate a strong submission from a competent one. All three fall out of the data if the student does the work:

1. The AWS bill is $0.00 and the platform still costs real money.
2. Bedrock is roughly **two-thirds** of platform cost; the ML system everyone spent six labs building is **0.4%**.
3. **The CDO's stated churn target is arithmetically unreachable** with the deployed model.

A submission that reports all three, with arithmetic, is an A. A submission with clean tables and none of them is a B.

---

## Task 1 — Metric Pyramid (25 points)

### Reference churn pyramid

| Layer | Metric | Calculation | Owner | Frequency | Decision |
|---|---|---|---|---|---|
| Model/System | AUC-ROC | Holdout eval, `evaluation_harness.py` | ML Engineer | Per training run | < 0.70 → block promotion (Lab 4 gate) |
| Model/System | p95 inference latency | CloudWatch `ModelLatency` p95 | VP Technology (James Wu) | Continuous | > 20 ms sustained → error budget burn (Lab 6 SLO) |
| Model Output | Recall@10% | Churners in top decile / all churners, weekly sample | ML Engineer | Weekly | < 0.25 → deployment freeze (Lab 6 SLO) |
| Model Output | Daily alert volume | Count of customers scored into top decile | ML Engineer | Daily | Drop > 30% vs 7-day avg → P2 (Lab 6 business layer) |
| User Experience | Offer open rate | Offers opened / offers sent | VP Marketing (David Park) | Weekly | < 15% → creative review |
| User Experience | Offer redemption rate | Offers redeemed / offers sent | VP Marketing | Weekly | < 6% (current baseline) → program review |
| Business Outcome | 90-day retention, treated vs holdout | 1 − (churned / contacted), by arm | CDO (Maya Chen) | Quarterly, 90-day lag | Gap not significant at 90 days → redesign |
| Business Outcome | Prevented churn revenue | Incremental retained × $340 LTV | CFO (Robert Hess) | Quarterly | < platform cost → decommission |

### Causal link classification — the graded part

| Link | Label | Why |
|---|---|---|
| AUC → Recall@10% | **Validated** | Same holdout, same population, same pipeline, same run |
| Recall@10% → alert volume | **Validated** | Alert volume *is* the decile count; mechanical |
| Alert volume → offer open rate | **Assumed** | No join exists between `churn_score` and `offer_events`. An instrumentation gap, not an inference. |
| Offer redemption → 90-day retention | **Assumed** | Redeeming a discount is not remaining a customer. The most consequential assumption in the platform. |
| 90-day retention → prevented churn revenue | **Assumed** | Assumes every retained customer realises full $340 LTV, and that retention is incremental rather than displaced |

**Grading:** full marks on the 7-point item require the student to notice that the UX layer is *not instrumented at all* in the platform as built. The pipeline stops at the model output. Any student who labels `alert volume → offer open rate` as Validated has not checked whether the join exists — it does not.

Accept a Track B or C second pyramid built purely on the case material. Bedrock quotas are zero on new accounts and most students will not have deployed Track B/C. Do not penalise a design-only second pyramid; the spec explicitly permits it.

**Common failures**

- All eight metrics at the model layer. That is an evaluation report, not a pyramid.
- Owner given as "the team." Reject; the case supplies six named stakeholder roles.
- Offer CTR placed at Business Outcome. CTR is user experience. Misplacing it collapses the causal chain and usually indicates the student did not think about layers at all.
- Every link labelled Validated. If nothing is assumed, the pyramid cannot be falsified, and the exercise had no content.

---

## Task 2 — Unit Economics (25 points)

### 2a — Rate card (5 pts)

Verified 2026-08-01, us-east-1, via `aws pricing get-products`:

| Item | Rate |
|---|---|
| Hosting `ml.m5.large` / `ml.t2.medium` / `ml.m6g.large` | $0.115 / $0.056 / $0.0924 per hr |
| Processing `ml.t3.large` / `ml.t3.medium` | $0.10 / $0.05 per hr |
| Serverless Inference 2 GB | $0.00004 / sec |
| Glue ETL and Crawler / Glue Flex | $0.44 / $0.29 per DPU-hr |
| Feature Store write / read / online storage | $1.25 per M / $0.25 per M / $0.45 per GB-mo |
| S3 storage / PUT / GET | $0.023 GB-mo / $0.005 per 1k / $0.0004 per 1k |
| CloudWatch alarm / custom metric / API | $0.10 / $0.30 (first 10k) / $0.01 per 1k |

Award the 5 points for four or more resources with the command and a stated pull date. **Deduct if the student quotes `CW:MetricMonitorUsage` as $0.02** — that is the over-1,000,000-metrics tier the API returns by default, and it is a 15x error. The spec warns about it explicitly; a student who reproduces it did not read the `description` field.

### 2b — Cost per 1,000 predictions (8 pts)

Scale: 2.1M customers × 52/12 = **9,100,000 predictions/month**.

| Component | Arithmetic | Monthly |
|---|---|---|
| Inference compute | 730.5 hr × $0.115 (persistent `ml.m5.large`) | **$84.01** |
| Feature Store online reads | 9.1M RU × $0.25/M | **$2.28** |
| Amortized training | 0.25 hr × $0.115, monthly retrain | **$0.03** |
| Glue allocated to churn | see below | **$21.85** |
| **Total** | | **$108.16** |

**$108.16 / 9,100 = $0.0119 → `$0.012 per 1,000 predictions`.**

Glue scale derivation — this is where students diverge, and it is the graded judgment:
$3.2B revenue ÷ ~$96 blended AOV = 33.3M transactions/yr = **641,026/week**. Lab dataset = 19,500 rows → scale factor **32.9x**. ETL 1.0311 × 32.9 = 33.9 DPU-hr, crawler ~0.48 (near-constant) → 34.4 DPU-hr × $0.44 = **$15.12/run** × 4.333 runs/mo = **$65.54/mo**, ÷ 3 models served = **$21.85**.

**Accept $0.008–$0.020 per 1,000 with shown work.** The scale factor is a defensible judgment and different AOV or allocation choices move it. **Reject** any answer that applies the raw 1.51 lab DPU-hours to a 2.1M-customer business without a scale factor — that is a 33x understatement and the spec warns about it directly.

The amortized-training row is a trap with a correct answer: students who trained locally via `models/churn/train_local.py` will get $0.00. Full credit **only if they say why** — the cost moved to their laptop, i.e. into human labor, and did not disappear. A silent $0 loses part of the 8 points.

### 2c — Platform cost, six categories (7 pts)

| Category | Monthly | Basis |
|---|---|---|
| Compute (training) | **$1** | Churn retrain; XGBoost on 2.1M × 11 features is minutes |
| Compute (inference) | **$84** | Churn endpoint 24×7 |
| Data pipeline, storage and transfer | **$68** | Glue $65.54 + S3 50 GB $1.15 + Feature Store online 2.1 GB $0.95 |
| Third-party APIs (Bedrock) | **$13,705** | Offers $9,555 + agent $4,150 |
| Human labor | **$6,400** | 80 hr/mo × $80 |
| Platform and tooling | **$46** | NAT $32.87, IPv4 $3.65, metrics $3.00, KMS $3, alarms $1.50, Secrets $0.80, CodeBuild $1 |
| **Total** | **$20,303** | **23.9% of the $85,000 budget** |

Bedrock basis: offers = 10% of 2.1M weekly = 910,000/mo × (2.0k in × $0.003 + 0.3k out × $0.015) = $9,555. Agent = 14,000 contacts/day × 50% automated × 30.4 days = 212,800/mo × (4.0k in × $0.003 + 0.5k out × $0.015) = $4,150. Token counts and the $15/M output rate are **assumptions the student must state** — the Price List API has no Bedrock output-token pricing in us-east-1.

**The finding worth points:** Bedrock is **67.5%** of platform cost. The churn model — six labs of Terraform, Feature Store, CI/CD, canary deployment and five-layer monitoring — is **0.4%**. Two API-based systems that required no infrastructure at all dominate the budget by more than two orders of magnitude. Any student who builds this table and does not remark on it has produced a spreadsheet rather than an analysis.

Second finding: total is under a quarter of the budget. Correct response is *"cost is not the binding constraint on this platform; measurement is,"* not *"we have $65,000 of headroom."*

The `docs/lab7-cost-model.csv` artifact is a gate within this item: if it is missing, or its rows do not sum to the stated total, the student loses the arithmetic credit regardless of how good the prose is.

### 2d — One optimization (5 pts)

**The strongest answer: replace the persistent real-time endpoint with SageMaker Batch Transform.**

The case specifies weekly batch scoring ("scores by Monday 6 AM ET"). Labs 5 and 6 built a 24×7 real-time endpoint — correctly, because they were teaching canary deployment and latency monitoring. For *this* workload it is the wrong architecture and it is 99.9% waste.

| | Monthly |
|---|---|
| Current: `ml.m5.large` 730.5 hr × $0.115 | $84.01 |
| Batch Transform: 4.33 runs × 0.2 hr × $0.115 | $0.10 |
| **Saving** | **$83.91 (99.9% of inference, 77.6% of total churn cost)** |

**The tradeoff is the graded part, and it is severe:** batch scoring destroys two of the four SLOs the student wrote in Lab 6.

| Lab 6 SLO | Under Batch Transform |
|---|---|
| Availability 99.5% of prediction requests | **Void** — there are no requests |
| Latency p95 < 20 ms | **Void** — there is no online path |
| Recall@10% ≥ 0.25 | Survives unchanged |
| Fairness gap ≤ 10pp | Survives unchanged |

Both void SLOs must be replaced by a batch-completion SLO: *scores present in S3 by Monday 06:00 ET, 51 of 52 weeks.* A student who proposes Batch Transform and notices this gets full marks. One who proposes it without noticing gets 3 of 5 — the number is right and the operational reasoning is absent.

**Also fully acceptable: Serverless Inference.** 9.1M × 5 ms × $0.00004/s = **$1.82/mo**, a 97.8% saving, and it preserves the real-time path so both SLOs survive. Tradeoffs: cold starts breach the 20 ms latency SLO on first call, and the default quota is 5 endpoints / 10 concurrency.

**Reject any optimization requiring a non-burstable processing or training instance.** Those quotas are 0 by AWS default on every student account. "Move the analyzer to `ml.c5.2xlarge`" is not an optimization; it is an unexecutable instruction.

---

## Task 3 — Executive Value Scorecard (25 points)

### The feasibility arithmetic (10 pts — the highest-value item in the lab)

The CDO's target: churn 18% → 14% within one year, contacting only the top 10% of customers by risk.

| Step | Value |
|---|---|
| Customers to retain for a 4pp move | 2.1M × 4% = **84,000/yr** |
| Churners per year | 2.1M × 18% = **378,000** |
| Churners reaching the contactable decile at measured Recall@10% = 0.293 | **110,754** |
| **Required save rate on contacted customers** | 84,000 / 110,754 = **75.8%** |
| Same, at the theoretical recall ceiling of 0.48 | 84,000 / 181,440 = **46.3%** |

**A retention offer that converts 76% of would-be churners does not exist.** Published retention and win-back campaign save rates sit in the single digits to mid-teens; students should cite a source, and any sourced benchmark under ~25% supports the conclusion.

The constraint is structural, not a modelling shortfall. Maximum achievable churn-point reduction = 18pp × recall × save rate:

| Save rate | Recall 0.293 (measured) | Recall 0.48 (ceiling) | Recall 1.0 (impossible) |
|---|---|---|---|
| 5% | 0.26 pp | 0.43 pp | 0.90 pp |
| 12% | 0.63 pp | 1.04 pp | 2.16 pp |
| 25% | 1.32 pp | 2.16 pp | 4.50 pp |

**Even contacting 100% of the customer base at a 12% save rate yields 2.16 pp.** The 4 pp target requires a save rate above 22% at perfect recall. It was set before anyone measured the model, and it is not reachable by tuning.

### The verdict students must reach — and the one they must not

What is actually achievable at a plausible 12% save rate:

| | Value |
|---|---|
| Customers saved per year | 13,290 |
| Value at $340 LTV | **$4.52M/yr** |
| Platform cost | $20,303/mo = **$0.24M/yr** |
| **ROI** | **18.5x** |
| Churn rate moves | 18% → **17.37%** (0.63 pp) |
| **Break-even save rate** | **0.647%** — 717 customers/yr |

**Both statements are true and the scorecard must carry both:**

> The platform is an excellent investment — it breaks even if the retention offer saves fewer than 7 in 1,000 contacted customers — **and** it will miss the CDO's stated 4-point target by roughly a factor of six.

The correct recommendation is **Expand**, paired with renegotiating the target to ~0.6–0.8 pp, or changing the *program* (wider decile coverage, better offer conversion, higher recall) rather than the model.

**Grading the 10 points:**

| Outcome | Award |
|---|---|
| Derives the required save rate, compares to a sourced benchmark, states the target is unreachable, quantifies what is | 10 |
| Derives it and states it is unreachable, no achievable alternative quantified | 7 |
| Notes the target "may be optimistic," no arithmetic | 3 |
| Reports the target as On Track | **0** |

The last row is not harsh. A scorecard that tells a CDO a structurally impossible target is on track is the specific professional failure this task exists to prevent.

### Readability (8 pts) and attribution (7 pts)

Readability: no AUC, PSI, recall, drift, or F1 anywhere in Section 3. "Churn probability" becomes "risk of going quiet over the next three months." Recall@10% becomes "of every 10 customers who will leave, our top-risk list catches about 3."

Attribution: the reference answer is a **randomized holdout** — flag all customers, suppress offers for a randomly selected 20%, compare 90-day retention between arms. Superior to pre/post because pre/post conflates the intervention with seasonality (Q4 retention always beats Q1) and with any other operational change in the window, and cannot separate customers who would have stayed anyway.

Acknowledged limitations that a strong answer names: Hawthorne effect on the marketing team, spillover between arms, and the 90-day lag before the first read. Confidence level should be **Medium** at best, with the reason stated. **A student claiming High confidence before a holdout has run has misunderstood the entire lab.**

**Reject pre/post comparison as the primary method** unless the student explicitly argues why a holdout is unavailable and then names the confounders they cannot control.

---

## Task 4 — Value Methodology Note (15 points)

13 fields, all substantive. The two that carry the weight:

**Counterfactual (field 7).** Must be operational. Acceptable: *"the retention team manually segments on days-since-last-purchase > 60, which surfaces roughly 15% of the churners the model finds, at ~20 analyst-hours per week."* Unacceptable: "without AI," "nothing," "the status quo."

**Time to observe outcome (field 9) is 90 days**, because that is the label Lab 2 derives. If the student's measurement window (field 8) is shorter than 90 days, the methodology reports outcomes that have not occurred. Full credit requires either a window ≥ 90 days or an explicit statement of how the gap is handled (leading indicators, interim readouts labelled non-decision-quality).

**Any submission using a 30-day churn window loses the 5-point consistency item.** Every source now says 90 days — case overview, data schema, Labs 2, 3, 6 and 7 — so a 30-day answer is a student error rather than a documentation trap. The likely cause is conflating the forward-looking 90-day *label* with the backward-looking 30-day *features* (`purchase_frequency_30d`) that sit in the same table. Say so in the feedback; it is a genuine conceptual confusion worth correcting.

Confidence level should be Medium. Almost no early-stage ML system has High confidence on business impact.

---

## Task 5 — Measurement Reflection (10 points)

Reference weakest assumptions:

1. **Offer redemption → 90-day retention.** Redeeming a discount is not remaining a customer; the discount may simply have pulled forward a purchase from someone who was staying anyway. Experiment: the randomized holdout, 20% suppression, 90-day window, n ≈ 40,000 per arm to detect a 2 pp difference at 80% power and α = 0.05.
2. **Every retained customer realises the full $340 LTV.** $340 is a population average; customers the model flags are by construction below-average engagement, so their realised LTV is likely lower. Experiment: 12-month revenue tracking on the treated cohort against the population mean.

**Least-observed layer: User Experience.** The platform has no join between `churn_score`, `offer_events`, and `purchase_events` — Athena can express the query, but the offer-event table is not being written. Closing it is roughly 3 weeks: instrument the offer service to emit events carrying the originating `churn_score` run ID, land them in S3, register in Glue Catalog, add the join.

**Grading:** "the model might be wrong" is not an assumption — deduct. An experiment with no n, no duration, and no success criterion is an idea, not a design; at graduate level a power sketch is expected for full marks.

---

## What changed and why — read before reusing old material

The 2026-07-06 version of this note is superseded. Defects found in the audit of 2026-08-01, numbered from the project's running list:

| # | Defect in prior Lab 7 material | Resolution |
|---|---|---|
| 28 | Task 1 required the second system to be "your Track B/C choice from Lab 3" — Bedrock quotas are 0 on every student account, so most students have no Track B/C system | Second pyramid is now explicitly a design exercise; deployment not required |
| 29 | Scorecard and methodology template used a **30-day** retention window; Lab 2 derives a **90-day** label and Lab 6's drift plan depends on it | **Fixed at source across the whole course** — scenario overview, data schema, quiz bank, Canvas builder, lecture outlines L01/L02/L07 |
| 29a | `northstar-scenario-overview.md` headline of **$140M** did not reconcile with its own inputs | **Corrected to $128.5M** with the arithmetic shown in the case document |
| 29b | `northstar-data-schema.md` claimed a **~15%** `churn_label` positive rate against a measured **21.2%** | Corrected to ~21%; a 15% base rate would put the Recall@10% ceiling at ~0.65 instead of 0.48 |
| 30 | Methodology template listed **13** fields; rubric said "all 12 fields" | Template numbered 1–13; rubric corrected |
| 31 | Prior optimization example was `ml.c5.2xlarge` — **processing quota is 0 by AWS default for every non-burstable instance**, so it cannot be executed | Replaced with Batch Transform and Serverless Inference, both quota-feasible |
| 32 | Cost per 1,000 predictions of $0.011 was asserted, not derived, and predated any measured rate or usage | Derived: **$0.012**, from usage × Price List rates, with arithmetic shown |
| 33 | Deliverable location unspecified for Tasks 1 and 2 (Tasks 3–5 named a file) | All five sections in `docs/lab7-value-scorecard.md`, plus `docs/lab7-cost-model.csv` |
| 34 | Cost-category taxonomy had no home for Glue pipeline compute — students split it three ways or dropped it | Row 3 renamed "Data pipeline, storage and transfer" with explicit instruction |
| 35 | **The CDO's stated success metric (18% → 14%) is unreachable** with the deployed model: it requires a 75.8% offer save rate | Turned into the highest-value graded item in Task 3 rather than silently propagated |
| 36 | No lab material anywhere noted that **Cost Explorer reports $0.00** for the entire platform because free tier absorbs it | New "Your AWS Bill Is Not Your Cost" section, with the July 2026 usage table as evidence |
| 37 | Nothing warned that the **Price List API returns a single pricing tier** — `CW:MetricMonitorUsage` returns $0.02 (over-1M tier) against an actual $0.30 | Documented in the spec's rate-card section and in the traps list |
| 38 | Nothing warned that **Bedrock output-token prices are absent from the Price List API** in us-east-1 and its Claude coverage is stale | Documented; students directed to the pricing page with a cited date |

Defect 35 is the same family as the Lab 6 Recall@10% error (an SLO set above the model's ceiling), one layer up: a *business* target set above what the measured model can structurally deliver. It survived every prior review of this lab.

### Both source-document defects are now closed (2026-08-01)

**Churn window standardised on 90 days at source.** `northstar-scenario-overview.md` now states 90-day churn probability, `northstar-data-schema.md` describes the label as forward-looking over 90 days, and the quiz bank, Canvas builder and lecture outlines L01/L02/L07 were corrected to match. There is no longer any 30-day churn-label text anywhere in the course. The remaining 30-day references are all legitimate and unrelated: the return-policy window in the RAG corpus, `purchase_frequency_30d` and `spend_30d` feature lookbacks, and S3 lifecycle rules.

**The $140M headline is now $128.5M and is derivable.** `northstar-scenario-overview.md` states the figure and shows the arithmetic (2.1M × 18% × $340). Students are no longer asked to reconcile it — they are expected to reproduce it. **A submission whose business math does not tie back to $128.5M has an arithmetic error, not a defensible alternative assumption.** This is a change from the prior grading posture; do not accept $140M.

**Also corrected:** `northstar-data-schema.md` claimed a **~15%** positive rate for `churn_label`. The measured rate is **~21%** (21.2%), which is what Lab 2 states and what the Recall@10% ceiling of 0.48 is derived from. The schema doc now says ~21%. Any student analysis built on 15% will produce a recall ceiling near 0.65 and overstate achievable value by roughly a third.

---

## Reproducing the arithmetic

```python
HRS = 730.5; CUST = 2_100_000
preds = CUST * 52/12                                   # 9,100,000/mo
inf   = HRS * 0.115                                    # $84.01
fs    = preds * 0.25/1e6                               # $2.28
train = 0.25 * 0.115                                   # $0.03
scale = (3.2e9/96/52) / 19_500                         # 32.9x
glue  = (1.031111*scale + 0.478611) * 0.44 * 52/12     # $65.54/mo
churn_total = inf + fs + train + glue/3                # $108.16
per_1k = churn_total/preds*1000                        # $0.0119

capt = CUST*0.18*0.293                                 # 110,754 churners in decile
required_save = (CUST*0.04)/capt                       # 0.758  <-- the finding
breakeven = (20_303*12)/(capt*340)                     # 0.00647
```

Usage figures from `aws ce get-cost-and-usage --metrics UsageQuantity --group-by Type=DIMENSION,Key=USAGE_TYPE`, July 2026, account `711457211658`. Rates from `aws pricing get-products`, us-east-1, 2026-08-01.
