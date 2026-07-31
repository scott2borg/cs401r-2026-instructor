# L21: Monitoring, Observability & Model Lifecycle Management — Figures

## Slide 1 — Title

**Figure:** *Monitoring vs. observability contrast.* Split visual. Left side (Monitoring): CloudWatch alarm dashboard with red alert: "Churn endpoint error rate 8.3% — THRESHOLD EXCEEDED." One-line notification. Right side (Observability): CloudWatch Logs Insights query results showing the root cause: a specific exception type (NullPointerException on feature 'category_diversity_score'), request payload excerpt, stack trace, model version, and timestamp. The contrast is stark: monitoring gives you the what; observability gives you the why.

---

## Slide 2 — The Three Pillars of AI System Observability

**Figure:** *Three-pillar observability diagram.* Three columns (Metrics, Logs, Traces). Each column: definition, example NorthStar data, tool, and strength/weakness summary. At the bottom: "Observability = Metrics + Logs + Traces working together." A single request's journey is shown across all three pillars: the same churn prediction request appears as a metric point (28ms latency), a log entry (full input/output), and a trace span (feature retrieval: 5ms, inference: 18ms, serialization: 5ms). The three pillars provide complementary views of the same event.

---

## Slide 3 — SageMaker Model Monitor: Deep Dive

**Figure:** *Model Monitor execution flow diagram.* Scheduled Processing Job (daily 6 AM) → reads from: Captured Data S3 (today's sample) and Baseline S3 (training statistics). Processing job: computes PSI per feature → compares PSI against constraints → writes a violation report to S3 → publishes CloudWatch metrics. CloudWatch metrics → alarm (if violation) → SNS → Lambda retraining trigger. The flow shows: Model Monitor is a pipeline, not a magic service. Understanding the pipeline helps you debug when it doesn't work.

---

## Slide 4 — LLMOps Observability: Watching What the LLM Does

**Figure:** *LLMOps observability dashboard.* Four panels: Token count distribution (histogram over 30 days — bimodal: short inputs and long inputs, no unusual spike); Latency trend (P50/P90/P99 over 30 days, all stable); RAGAS metrics (faithfulness/relevancy/recall weekly trend, all above threshold); Cost/day (bar chart, stable with minor variance). One panel in amber: Context token length per request — declining trend over the last two weeks, annotated "RAG index may need refresh."

---

## Slide 5 — Agent Observability: Tracing the Reasoning Chain

**Figure:** *Agent observability dashboard.* Five metric panels corresponding to the table above. Tool calls per-session histogram (distribution with an alert line at 8). Tool failure rate by tool name (bar chart: order_lookup_tool highlighted in amber at 2.8%). Escalation rate trend (line chart: stable at 8-9%). Session token count trend (stable at ~1,240). Resolution rate trend (stable at 91.7%). All within thresholds except order_lookup_tool.

---

## Slide 6 — Model Lifecycle Management: When to Act

**Figure:** *Model lifecycle decision tree.* Root node: "Is the model performing within SLA?" YES → "Is business value being created?" YES → Maintain. NO → "Is drift the cause?" YES → Retrain. NO → "Is it an architecture limitation?" YES → Redesign. NO → Retire. The tree shows: lifecycle decisions are hierarchical — check the simplest intervention (retrain) before escalating to the more expensive one (redesign or retire).

---

## Slide 7 — Drift: The Full Taxonomy

**Figure:** *Drift taxonomy diagram.* Four-quadrant layout. Each quadrant: drift type, visual representation (distribution plots showing before/after), detection method, and NorthStar example. Data drift quadrant: two overlapping histograms (baseline vs. current; shifted right). Concept drift quadrant: scatter plot showing a changed decision boundary. Model drift quadrant: two prediction score distributions (shifted). Pipeline drift quadrant: flowchart showing ETL change affecting downstream feature values.

---

## Slide 8 — Retraining Strategy: When, How, and How Often

**Figure:** *Retraining calendar visualization.* 12-month calendar with: Scheduled retraining events marked (Jan, Apr, Jul, Oct). Drift-triggered events shown as conditional branches. Business events noted. Total estimated retraining events per year: 4-8. Cost estimate: 4-8 × $2.24/training run = $9-18/year in training compute. Monitoring compute (Model Monitor daily): ~$15/month. The cost view communicates that automated retraining is extremely cheap compared to the cost of operating a degraded model.

---

## Slide 9 — Observability in the CI/CD Pipeline

**Figure:** *Pipeline execution timeline dashboard.* 10 recent executions shown as a timeline (like GitHub Actions runs). Each execution: start time, duration, status (green=SUCCEEDED, red=FAILED). One failed execution highlighted, with step-level breakdown: Step 1 (PrepareFeatures: SUCCEEDED, 31 min), Step 2 (TrainingJob: FAILED, 12 min) with failure reason "ResourceExhausted: OOM." The detail view mirrors what SageMaker Studio shows and what students will use for debugging.

---

## Slide 10 — Building the Unified Dashboard (Lab 6 Part 2)

**Figure:** *NorthStar unified dashboard mockup.* Five-section CloudWatch dashboard layout. Section 1 (top row): three metric tiles — Churn endpoint P99 latency (142ms, green), Feature Store freshness (last updated 2h ago, green), Platform availability (99.97%, green). Section 2: Glue pipeline success rate (trend line). Section 3: Offer generation faithfulness + latency. Section 4: Agent resolution rate + escalation rate. Section 5: Daily cost by system (bar chart). Clean, operational, one-page view.

---

## Slide 11 — The Runbook: Operationalizing Your Monitoring

**Figure:** *Runbook decision tree.* Alert fires → two branches (endpoint not InService / endpoint InService). Each branch: 3-4 diagnostic steps as a flowchart with actions. Resolution paths: auto-rollback (canary case), manual scale-out (overload case), ETL fix (feature schema case). Escalation path shown at bottom. The runbook flowchart is immediately actionable — a on-call engineer who's never seen the system before can follow it.

---

## Slide 12 — Lifecycle Management for RAG and Agent Systems

**Figure:** *RAG and Agent lifecycle comparison table.* Two-column table: RAG System (left) vs. Agent System (right). Rows: Primary artifact, Lifecycle trigger, Common failure mode, Monitoring signal, Retirement signal. The comparison shows: RAG lifecycle is about index freshness; Agent lifecycle is about tool contract stability.

---

## Slide 13 — Incident Response Deep Dive: A Real Scenario

**Figure:** *Incident timeline diagram.* Horizontal timeline from Nov 9 6:04 AM to Nov 11. Key events marked: alarm (6:04), pipeline trigger (6:04), gate failure (9:31), investigation (10:15), fix (11:30), retrain (11:45), gate pass (14:00), canary start (14:30), canary full (Nov 11). MTTR from alarm to resolution: 2 days (canary included) or 8 hours (to fix deployment). The incident demonstrates that automated monitoring caught the problem, automated retraining attempted a fix, and human investigation was needed to fix the root cause.

---

## Slide 14 — Lab 6 Progress Check and Common Issues

**Figure:** *Lab 6 checklist with status indicators.* Progress tracker: Part 1 (3 steps: capture enabled ✅/⬜/⬜), Part 2 (dashboard started ⬜), Part 3 (retraining Lambda ⬜), Part 4 (compliance report ⬜). Expected progress at Day 2: Part 1 Step 1 done; Parts 2-4 not started. "On track" vs. "behind" assessment. Specific action for tonight: "Enable data capture (15 minutes). Then start dashboard design."

---

## Slide 15 — The Monitoring Maturity Model

**Figure:** *Monitoring maturity staircase.* Five steps (Level 0-4). Each step: name, characteristics, and a representative metric: "how long until you discover a production incident?" Level 0: 2-3 days (customer complaint). Level 1: 4-8 hours (SLA breach detected). Level 2: 30-60 minutes (alert fires). Level 3: < 15 minutes (leading indicator fires before incident). Level 4: pre-emptive (problem prevented before it occurs). The discovery latency metric makes the business value of each maturity level concrete.

---

## Slide 16 — Key Takeaways + What's Next

**Figure:** *Five-takeaway summary card.* Lab 5 due Saturday (2 days, red). Lab 6 due in 10 days (amber). Monitoring maturity staircase thumbnail. Incident timeline thumbnail.
