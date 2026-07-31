# L20: Metrics, Benchmarks & Guardrails — Figures

## Slide 1 — Title

**Figure:** *Operate arc metrics dashboard.* A four-panel CloudWatch-style dashboard: top-left: AUC trend line (weekly, last 12 weeks — stable around 0.74, slight uptick recently), top-right: churn recall at 0.4-precision (weekly, hovering around 0.78), bottom-left: offer acceptance rate (daily, trending upward from 18% to 23% over 8 weeks), bottom-right: agent resolution rate (daily, stable at 91%). All four metrics with thresholds marked and "healthy" status indicators. The dashboard communicates: the Operate arc is about watching these numbers and understanding what they mean.

---

## Slide 2 — The Metrics Hierarchy for AI Systems

**Figure:** *Three-tier metrics pyramid.* Inverted pyramid (wide at the top = many metrics; narrow at the bottom = few metrics). Level 1 (Technical, top): 10+ metrics tracked continuously. Level 2 (Operational, middle): 5-7 metrics tracked daily. Level 3 (Business, bottom): 2-4 metrics tracked monthly. Arrows: Level 1 metrics feed Level 2 understanding; Level 2 operational status feeds Level 3 business outcomes. "Most teams stop here" marker at Level 1. "Executive reporting starts here" marker at Level 3.

---

## Slide 3 — Defining the NorthStar Metrics Framework

**Figure:** *Three-system metrics dashboard.* Three card panels (one per system). Each card: three-level metrics with current values and status indicators (green/amber/red). All metrics are shown in a "healthy" state. The cards use the same format as real operational dashboards, making them directly applicable to a real enterprise AI platform.

---

## Slide 4 — Leading vs. Lagging Indicators

**Figure:** *Leading/lagging indicator timeline diagram.* Horizontal timeline showing a hypothetical model degradation event. At week 0: Feature PSI crosses 0.15 (leading indicator fires). At week 2: AUC drops below 0.70 (model metric catches it). At week 6: Churn rate increases (business metric catches it). If only measuring the lagging indicator (churn rate), you're 6 weeks behind the problem. With leading indicators, you're 2 weeks ahead of the model problem. The timeline makes the value of leading indicators visceral.

---

## Slide 5 — Benchmarks: Establishing the Baseline

**Figure:** *Benchmark comparison bar chart.* Three bars: Rule-based (0.64, labeled "simple threshold"), Human expert (0.69, labeled "domain expert panel"), NorthStar XGBoost v3.0 (0.74, labeled "current production"). Baseline from first deployment (0.741) marked as horizontal reference line. "Model ROI" annotation: "+15.6% over rule-based baseline." The chart makes the model's value concrete by comparison.

---

## Slide 6 — Guardrails as Operational Controls

**Figure:** *Guardrail architecture diagram.* Three-layer guardrail stack. Incoming offer text → Layer 1 (Bedrock Guardrails: content filter, topic denial, PII) → Layer 2 (Application quality guard: format validation, hallucination check) → Layer 3 (Business rules: discount limit, eligibility check) → Valid Offer → User. Each layer: trigger action (block/anonymize/rewrite/log). Metrics panel: trigger rate per layer with historical trend. The three-layer architecture shows defense-in-depth for output quality.

---

## Slide 7 — SLA Design for AI Systems

**Figure:** *SLA dashboard with gauges.* Four-panel gauge dashboard: Availability (gauge: 99.96% — above 99.9% target), Latency P99 (gauge: churn 142ms — within 200ms target; offer P90 2.8s — within 3s target), Quality (gauge: AUC 0.738 — above 0.70 production threshold), Coverage (gauge: 99.7% — above 99.5% target). All four gauges in green. The dashboard is what you'd show at a weekly operations review.

---

## Slide 8 — Error Budgets: Quantifying Tolerable Imperfection

**Figure:** *Error budget visualization.* Three gauges (Availability, Quality, Coverage) showing current budget consumption as a percentage. Availability: 32% consumed (comfortable). Quality (AUC): 68% consumed (approaching threshold — amber warning). Coverage: 10% consumed (comfortable). Each gauge has policy zones colored green (>50% remaining), amber (20-50%), and red (<20%). The quality gauge in amber communicates: the model is approaching its quality error budget — attention required.

---

## Slide 9 — Monitoring Guardrails: Automated Quality Defense

**Figure:** *Monitoring guardrail architecture.* Four layers shown vertically. Each layer: trigger type (real-time/daily/weekly/monthly), monitoring mechanism, alert destination, and action taken on alert. Arrows connect layers: Layer 2 daily check can trigger a canary rollback; Layer 3 weekly RAGAS can trigger a prompt review; Layer 4 monthly audit can trigger a model replacement project. The architecture shows monitoring as a continuous, multi-frequency quality defense system.

---

## Slide 10 — Lab 6 Overview: Building the Monitoring Platform

**Figure:** *Lab 6 architecture diagram.* Existing NorthStar platform with Lab 6 additions highlighted in a different color: Model Monitor → CloudWatch (drift alarms) → Retraining Lambda → SageMaker Pipeline (Lab 4). Unified Dashboard covering all four systems. Compliance Report Lambda (monthly EventBridge trigger) → S3 report → SNS email. Clean architecture showing Lab 6 as the operational intelligence layer.

---

## Slide 11 — Metrics Anti-Patterns

**Figure:** *Five anti-patterns table.* Five rows with anti-pattern name, example, consequence, and fix. "Goodhart's Law" row includes the quote. "Alert Fatigue" row has a metric: "Teams with > 20 P2 alerts/day have 60% lower incident response rates." Clean, direct format.

---

## Slide 12 — Production Metrics Reporting: The Weekly Operations Review

**Figure:** *Weekly operations review agenda card.* A meeting agenda card with time allocations, sections, and example discussion points pre-populated for a hypothetical week. Key items highlighted: "PSI for monetary_30d at 0.17 — approaching alert threshold (0.20). Discuss: retrain ahead of Q4?" and "Agent resolution rate dipped to 83% Monday. Root cause: order_lookup_tool latency spike. Fixed Tuesday. No recurring risk." The agenda card communicates: structured operations review is more efficient than ad hoc monitoring.

---

## Slide 13 — Metric Connection: AUC to Revenue

**Figure:** *Metric chain waterfall diagram.* Vertical waterfall showing each step in the chain above, with values and conversion rates at each step. Starting at top: AUC (0.74). Ending at bottom: Annual value ($571,704). Each step: metric name, value, and conversion rate. "Model cost" arrow pointing into the chain at the correct level. The waterfall makes the business case for the churn model visible from first principles.

---

## Slide 14 — Lab 6 Walkthrough: Model Monitor Configuration

**Figure:** *Lab 6 Model Monitor setup flow.* Three-step flow: Step 1 (data capture config → endpoint update), Step 2 (baseline job → S3 baseline stats + constraints), Step 3 (monitoring schedule → daily processing job → CloudWatch violations). S3 bucket structure shown: `/data-capture/` (captured requests), `/baseline/` (statistics.json + constraints.json), `/reports/` (daily monitoring output). Each step is labeled with the Lab 6 file that implements it.

---

## Slide 15 — Key Takeaways + What's Next

**Figure:** *Five-takeaway summary card.* Lab 5 due Saturday (4 days, red). Lab 6 countdown (12 days, amber). Metric chain waterfall thumbnail. Weekly operations review agenda thumbnail.
