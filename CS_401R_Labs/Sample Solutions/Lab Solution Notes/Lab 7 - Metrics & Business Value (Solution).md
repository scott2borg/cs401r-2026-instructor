---
created: 2026-07-06
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
status: complete
---

# Lab 7 — Metrics & Business Value (Solution Notes)

## Key Decisions Made and Why

### Decision 1: Holdout design over pre/post comparison for attribution

The executive scorecard attributes business impact via a randomized holdout (20% of flagged customers receive no offer). This is the strongest available attribution method for an operational system.

The alternative students often propose is a pre/post comparison: "30-day retention before the system vs. after." This is a weak design because:
- Pre/post conflates the AI intervention with seasonal effects (Q4 retention is always better than Q1)
- Pre/post conflates the AI intervention with other operational changes made in the same period
- Pre/post cannot separate "customers who would have stayed anyway" from "customers the AI saved"

The holdout design is not a perfect RCT — there is potential Hawthorne bias (marketing team may unconsciously work harder for the offer group) and potential spillover (non-offer customers hear about offers from friends). But these are acknowledged limitations in the methodology, not reasons to abandon the design. A holdout with acknowledged limitations is better than a pre/post with unacknowledged limitations.

### Decision 2: Conservative confidence level ("Medium") in the scorecard

The executive scorecard explicitly labels the confidence level as "Medium" and explains why: 60 days of data, 90 days needed for statistical significance. The preliminary number (4.2pp incremental retention) is included but labeled as non-decision-quality evidence.

Students who present preliminary results as "the system generates $50K/month in value" without caveats are making a scientific communication error. The correct approach is to present the number with its confidence interval and the conditions under which it becomes actionable (90-day experiment completion).

This is a professional skill: knowing when to present data and when to present data with appropriate uncertainty is what separates junior analysts from senior ones. The scorecard models this correctly.

### Decision 3: Cost per 1,000 predictions as the unit economics anchor

Unit economics could be presented in many units: cost per customer, cost per prediction, cost per retained customer, cost per dollar of prevented revenue loss. The sample solution anchors on cost per 1,000 predictions ($0.011) because:
- It is the lowest-level unit (most comparable across systems)
- It separates inference cost from business impact (which may or may not be captured)
- It allows comparison to alternatives (e.g., "a human analyst reviewing 1,000 customer accounts costs $X")

The cost per retained customer is also calculable ($668/month ÷ estimated 147 retained customers/day × 30 days = $1.52/retained customer) but requires the holdout experiment to complete. Including it as a projection with a note that it's model-dependent is appropriate.

### Decision 4: Distinguishing "assumed" from "validated" causal links

The metric pyramid explicitly labels each causal link as Validated or Assumed. This is one of the most important intellectual habits the lab is designed to teach.

AUC-ROC → Precision@10% is Validated because both are measured on the same holdout set in the same evaluation pipeline.

Offer CTR → 30-Day Retention is Assumed because clicking is not purchasing. The experiment to validate this link is described in Section 5.

Students who build metric pyramids without distinguishing assumed from validated links are building measurement frameworks that cannot be falsified. If every link is assumed, the pyramid is a theory, not a measurement system.

---

## How Each Rubric Item Is Satisfied

### Metric Pyramid (Section 1)
- `docs/lab7-value-scorecard.md` Section 1 contains pyramids for both Track A (Churn Prediction) and Track B (Offer Generation RAG)
- Each pyramid row has: Layer, Metric, Calculation, Owner, Frequency, Decision Triggered By
- Causal chain assessment explicitly labels each link as Validated or Assumed with experiment designs for the assumed links

### Unit Economics (Section 2)
- Cost per 1,000 predictions calculated from first principles (not estimated)
- Full monthly platform cost breakdown in a table with 7 cost categories
- One concrete optimization proposed (ml.c5.2xlarge) with cost-per-run comparison table
- Two other optimizations evaluated and rejected with stated reasons (Spot Instances: insufficient savings for engineering cost; fewer metrics: removes critical monitoring)

### Executive Scorecard (Section 3)
- No ML jargon — "churn probability" replaced by "risk of not making a purchase in the next 30 days"
- Attribution section explicitly explains the holdout design to non-technical audience
- Preliminary number ($50K/month) included but explicitly labeled as preliminary and non-decision-quality
- Separate "Investment Recommendation" section with specific asks and rationale (expand Platinum scoring; hold on RAG expansion pending experiment results)
- "Open Questions" section — models intellectual honesty about what is not yet known

### Value Methodology (Section 4)
- All 12 required fields completed for the Churn Prediction system
- "Known limitations" field is substantive (3 specific limitations, each with partial mitigation)
- "Confidence level" is explicitly Medium with justification — not "High" by default
- Counterfactual defined precisely ("retention team manually segments by last purchase date > 60 days, captures ~15% of churners in top effort decile")

### Measurement Reflection (Section 5)
- Two weakest assumptions identified with specific reasoning
- Experiment designs for both assumptions include: design type, duration, sample size, power/significance levels, primary metric
- Least-observed layer identified: User Experience (instrumentation gap between AI output and customer interaction)
- Implementation effort for closing the gap: 3 weeks (specific, not vague)

---

## Common Student Mistakes to Watch For

### Metric Pyramid
- **All metrics at one layer.** A pyramid with 8 model quality metrics and no business outcome metrics is a model evaluation report, not a metric pyramid.
- **Metrics without owners.** Every metric needs a human who is accountable for it. "The team" is not an owner.
- **Metrics without decision triggers.** A metric you monitor but never act on is a vanity metric. Every metric should have a "decision triggered if X" entry.
- **Not distinguishing assumed vs. validated causal links.** The whole point of the causal chain section is to identify where measurement assumptions live. Labeling all links "validated" is intellectually dishonest.
- **Offer CTR labeled as a business outcome.** CTR is a user experience metric — it measures user interaction with the offer, not the business impact of the offer. 30-day retention is the business outcome. Getting this wrong misplaces the causal chain.

### Unit Economics
- **Only computing inference cost.** Infrastructure cost, training cost, pipeline cost, human labor, and tooling are all real costs. A cost analysis that only includes GPU/CPU compute underestimates platform cost by 5–10x.
- **Using list price without justification.** SageMaker pricing varies significantly by instance type, region, and reserved instance usage. Students should state their pricing source and assumptions.
- **Proposing an optimization without a tradeoff.** "Use Spot Instances" is not a recommendation — "use Spot Instances, which reduces training cost by 60% but requires checkpoint/resume infrastructure (2+ weeks engineering, not worth it at this scale)" is a recommendation.
- **Cost per customer instead of cost per 1,000 predictions.** At $0.011/1,000 predictions, the unit economics look cheap and scalable. Students who compute $0.0000108 per prediction or $2.56 per run are not wrong, but they are presenting the number at the wrong unit for business communication.

### Executive Scorecard
- **ML jargon in the executive-facing sections.** "AUC-ROC," "PSI," "feature drift," and "KS statistic" should not appear anywhere in Section 3. If it would confuse a CFO, translate it.
- **Presenting preliminary numbers as final.** "The system generates $50K/month" before the holdout experiment completes is a misleading claim. The number must be labeled as preliminary with a confidence caveat.
- **Missing the "open questions" section.** An executive scorecard that only shows positive results is marketing, not reporting. The CDO needs to know what is not yet proven.
- **No attribution explanation.** Executives who don't understand how the impact is being measured cannot evaluate whether the claim is credible. The holdout design must be explained in plain language.
- **Investment recommendation without rationale.** "We recommend expanding the system" without citing the metric that supports expansion is a conclusion without evidence.

### Value Methodology
- **Counterfactual is vague** ("without AI" is not a counterfactual; "manual segmentation by last purchase date > 60 days captures 15% of churners" is).
- **Confidence level defaulted to "High."** Almost no early-stage ML system has High confidence on its business impact. The appropriate level depends on: sample size, experiment duration, confound controls, and whether the holdout is running. Default to Medium until proven otherwise.
- **"Time to observe outcome" treated as negligible.** Churn is a 30-day label. You cannot evaluate a retention intervention in 7 days. Getting this wrong leads to premature success claims.

### Measurement Reflection
- **Weak assumption #1 is just "the model might be wrong."** That is not a specific assumption — every model might be wrong. The weakest assumptions are specific causal links (CTR → retention, definition of churn, LTV of retained customers) where the assumption is falsifiable.
- **Experiments proposed without sample sizes or power calculations.** A proposed experiment without n, power, and α is not a real experiment design — it is an idea. Students at the graduate level should be able to sketch a power calculation.
- **Least-observed layer is identified but not instrumentable.** The reflection should answer: what specific data is missing, what engineering would capture it, and how long would that take.

---

## Key AWS Services and Patterns Used

| Service | Pattern | Why This Pattern |
|---------|---------|-----------------|
| CloudWatch Metric Insights | Query `DailyChurnAlertsGenerated` per cohort with RunDate dimension | Enables per-batch-run metric analysis without building a custom analytics pipeline |
| Amazon Athena | Join churn_score + offer_events + purchase_events | End-to-end causal chain measurement (currently an instrumentation gap) |
| SageMaker Batch Transform | Holdout group implementation: flag all customers, send offers to 80%, suppress for 20% | Holdout is enforced in the offer generation downstream step, not the model — the model scores all 250K customers |
| AWS SSM Parameter Store | Store holdout group membership (customer IDs not receiving offers) | Decouples holdout assignment from model scoring logic |
| Amazon SNS | Publish business metric alerts to CDO email | Closes the loop: business metric anomaly → automated notification → human review |

---

## Connections to Prior Labs

- Lab 5's deployment runbook mentions the 48-hour monitoring window — Lab 7's metric pyramid is the framework that structures what to watch during that window
- Lab 6's SLOs are the technical reliability metrics at the base of the Lab 7 pyramid
- Lab 6's `DailyChurnAlertsGenerated` CloudWatch metric is the Layer 3 (Model Output) metric in Lab 7's pyramid
- Lab 7's "least-observed layer" gap (User Experience instrumentation) is the engineering work that would close the causal chain that Lab 7's value methodology currently labels as "Assumed"
- The holdout design in Lab 7 is what makes Lab 6's "30-Day Retention Rate" metric credible — monitoring without attribution produces activity metrics, not business value metrics

## Course Arc Observation

Labs 5–7 complete the production AI system lifecycle:
- Lab 5: Deploy it safely (canary, rollback, security)
- Lab 6: Monitor it reliably (five layers, SLOs, runbooks)
- Lab 7: Measure whether it creates value (metric pyramid, unit economics, attribution)

A student who completes all three has built and operated a production ML system with the discipline that distinguishes senior ML engineers from junior ones: cost awareness (Batch Transform decision), safety engineering (canary + rollback), operational reliability (SLOs + runbooks), and business accountability (holdout design + causal chain audit).
