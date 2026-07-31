---
lecture: L20
title: Metrics, Benchmarks & Guardrails
date: Tuesday, November 10, 2026
week: 11
arc: Operate
reading_due: "Operating AI Systems — Metrics and Measurement through Guardrails"
lab_assigned: "Lab 6 — Monitoring & Observability (due Sat Nov 22)"
lab_due: "Lab 5 due Sat Nov 14 (4 days)"
slides_target: 16
---

# L20: Metrics, Benchmarks & Guardrails
**Tuesday, November 10, 2026 | CS 401R: Engineering Production AI Systems | Fall 2026**

> You can't manage what you can't measure. The Operate arc begins with a fundamental question: what does "good" look like for a production AI system? How do you know if it's getting better or worse? And what guardrails prevent "worse" from becoming catastrophic?

**Reading Due:** *Operating AI Systems* — "Metrics and Measurement" through "Guardrails"
**Lab 6 Assigned Today:** Monitoring & Observability — due Sat Nov 22
**Lab 5 Due:** Sat Nov 14 (4 days)

---

## Slide 1 — Title
**Layout:** Left dark panel + right metrics dashboard visual

**Content:**
- Metrics, Benchmarks & Guardrails
- CS 401R · Lecture 20 · Tuesday, November 10, 2026
- Welcome to the Operate Arc: From "Does It Work?" to "Is It Working Well?"

**Figure:** *Operate arc metrics dashboard.* A four-panel CloudWatch-style dashboard: top-left: AUC trend line (weekly, last 12 weeks — stable around 0.74, slight uptick recently), top-right: churn recall at 0.4-precision (weekly, hovering around 0.78), bottom-left: offer acceptance rate (daily, trending upward from 18% to 23% over 8 weeks), bottom-right: agent resolution rate (daily, stable at 91%). All four metrics with thresholds marked and "healthy" status indicators. The dashboard communicates: the Operate arc is about watching these numbers and understanding what they mean.

**Notes:** "The Operate arc begins with a counterintuitive move: we stop looking at model metrics and start looking at business metrics. AUC is an engineering metric — it tells you about model quality. Churn rate reduction is a business metric — it tells you whether the model is creating value. The gap between those two views is what the Operate arc closes. The metrics you'll define today are the ones that go on the executive dashboard, not just the engineer's dashboard."

---

## Slide 2 — The Metrics Hierarchy for AI Systems
**Layout:** Three-tier metrics hierarchy from technical to business

**Content:**
**The AI Metrics Hierarchy:**

Production AI systems need metrics at three levels. Most teams only measure Level 1.

**Level 1 — Technical/Model Metrics (the engineer's view):**
- What: measures model quality and system performance
- Examples: AUC, RAGAS faithfulness, latency P99, error rate, drift PSI
- Who cares: ML engineers, platform team
- Update frequency: real-time to daily
- Action: debugging, retraining, optimization

**Level 2 — Operational Metrics (the operator's view):**
- What: measures whether the AI system is operating as designed
- Examples: prediction coverage (% of customers scored), offer generation success rate, agent resolution rate, data pipeline freshness
- Who cares: ML team lead, DevOps, product manager
- Update frequency: daily to weekly
- Action: operational incidents, pipeline fixes, reliability improvements

**Level 3 — Business Metrics (the executive's view):**
- What: measures the business outcomes the AI system is supposed to drive
- Examples: churn rate reduction (vs. control group), revenue retained from interventions, customer satisfaction score, cost per saved customer
- Who cares: VP Marketing, CFO, CTO, CEO
- Update frequency: weekly to monthly
- Action: strategy decisions, continued investment, scope changes

**Figure:** *Three-tier metrics pyramid.* Inverted pyramid (wide at the top = many metrics; narrow at the bottom = few metrics). Level 1 (Technical, top): 10+ metrics tracked continuously. Level 2 (Operational, middle): 5-7 metrics tracked daily. Level 3 (Business, bottom): 2-4 metrics tracked monthly. Arrows: Level 1 metrics feed Level 2 understanding; Level 2 operational status feeds Level 3 business outcomes. "Most teams stop here" marker at Level 1. "Executive reporting starts here" marker at Level 3.

**Notes:** "The biggest measurement gap in enterprise AI is between Level 1 and Level 3. Teams that only measure AUC cannot answer the question: 'Is our AI creating business value?' Teams that only measure business outcomes can't diagnose why performance is changing. You need all three levels — connected. When churn rate reduction drops (Level 3), you investigate operational metrics (Level 2) to see if coverage fell, then technical metrics (Level 1) to see if the model drifted. The pyramid gives you a diagnostic path."

---

## Slide 3 — Defining the NorthStar Metrics Framework
**Layout:** Complete three-tier metrics for all three NorthStar AI systems

**Content:**
**NorthStar Metrics Framework (all three systems):**

**Churn Prediction System:**
| Level | Metric | Target | Measurement |
|-------|--------|--------|-------------|
| Technical | AUC (validation set) | ≥ 0.72 | Weekly eval job |
| Technical | Recall@0.4-precision | ≥ 0.75 | Weekly eval job |
| Technical | PSI (all features) | < 0.20 | Daily Model Monitor |
| Operational | Prediction coverage | ≥ 98% of active customers scored | Daily |
| Operational | Batch job completion | ≤ 47 min | Monthly |
| Business | Churn rate (intervention group) | ≤ 7.5% vs. 9.1% control | Monthly |
| Business | Revenue retained per $1 intervention | ≥ $8 | Monthly |

**Offer Generation System:**
| Level | Metric | Target |
|-------|--------|--------|
| Technical | RAGAS Faithfulness | ≥ 0.95 |
| Technical | Format compliance | = 1.00 |
| Operational | Offer generation latency P90 | ≤ 3.0s |
| Business | Offer acceptance rate | ≥ 20% (baseline: 12% generic offers) |
| Business | Revenue per customer from personalized offers | ≥ $15 lift vs. generic |

**Customer Service Agent:**
| Level | Metric | Target |
|-------|--------|--------|
| Technical | Tool failure rate | ≤ 2% |
| Operational | Resolution rate | ≥ 85% |
| Operational | Human escalation rate | 5-20% |
| Business | Cost per resolved issue | ≤ $0.50 (vs. $8 human agent cost) |
| Business | CSAT | ≥ 4.2/5.0 |

**Figure:** *Three-system metrics dashboard.* Three card panels (one per system). Each card: three-level metrics with current values and status indicators (green/amber/red). All metrics are shown in a "healthy" state. The cards use the same format as real operational dashboards, making them directly applicable to a real enterprise AI platform.

**Notes:** "The '$0.50 cost per resolved issue vs. $8 human agent cost' for the Customer Service Agent is the business metric that justifies the entire agent investment. At 847 sessions/day, that's $6.81 saved per session vs. human agent, or $5,757/day in cost savings. Annually: $2.1M. That's the ROI calculation that covers the cost of the NorthStar AI platform. We'll build the full model in L23."

---

## Slide 4 — Leading vs. Lagging Indicators
**Layout:** Leading/lagging indicator framework for AI operations

**Content:**
**Leading Indicators: Warning Before the Problem**

A lagging indicator measures a problem after it has happened. A leading indicator predicts a problem before it becomes visible in business metrics.

**Lagging indicators (tell you something went wrong):**
- Churn rate increase (detected after 30-90 days)
- CSAT drop (detected after customer surveys, 1-2 weeks lag)
- Revenue decrease from AI-driven initiatives (detected monthly)

**Leading indicators (warn you before the problem compounds):**
- Feature distribution drift (PSI rising → indicates churn model will degrade before it actually degrades)
- Offer acceptance rate daily trend (declining → model relevance decreasing)
- Agent tool failure rate spike (precedes resolution rate decline by ~3 days)
- Prediction latency P99 trend (rising → approaching SLA violation before violation occurs)

**The monitoring principle:** Measure leading indicators aggressively. Measure lagging indicators to confirm your leading indicators were right.

**NorthStar Early Warning System:**

| Leading Indicator | Trigger Level | Predicted Problem | Lag |
|------------------|--------------|------------------|-----|
| Feature PSI > 0.15 | Alert (not yet action) | Model AUC will decline | 2-4 weeks |
| Feature PSI > 0.20 | Retrain trigger | Model AUC declining now | < 1 week |
| Offer acceptance rate < 18% (3-day avg) | Investigate | Offer relevance declining | 1-2 weeks |
| Agent escalation rate > 18% | Alert | Resolution rate about to decline | 2-3 days |
| Data pipeline latency +50% | Alert | Feature freshness risk | Same day |

**Figure:** *Leading/lagging indicator timeline diagram.* Horizontal timeline showing a hypothetical model degradation event. At week 0: Feature PSI crosses 0.15 (leading indicator fires). At week 2: AUC drops below 0.70 (model metric catches it). At week 6: Churn rate increases (business metric catches it). If only measuring the lagging indicator (churn rate), you're 6 weeks behind the problem. With leading indicators, you're 2 weeks ahead of the model problem. The timeline makes the value of leading indicators visceral.

**Notes:** "The 6-week lag before a churn rate increase appears in the business metrics is not hypothetical. Churn is typically defined as 'no purchase in 90 days' — you can't measure it until 90 days of inactivity have passed. If the model started degrading in October, you won't see it in the churn rate until January. By then, you've potentially misidentified thousands of customers as low-risk when they were actually high-risk. Leading indicators are the operational tool that breaks this delay."

---

## Slide 5 — Benchmarks: Establishing the Baseline
**Layout:** Benchmark methodology for AI systems

**Content:**
**What Is a Benchmark (and Why You Need One)?**

A benchmark is a reference point that makes your current metric meaningful. Without a benchmark, "AUC = 0.74" tells you nothing. With benchmarks, it tells you everything.

**Three types of benchmarks for NorthStar:**

**1. Historical baseline:** How does today's performance compare to a fixed historical reference?
- Benchmark: churn model AUC on Oct 1 holdout set (first production deployment): 0.741
- Today's AUC: 0.738 → -0.003 from baseline → acceptable drift within threshold

**2. Rule-based baseline:** How does the model compare to a simple rule?
- Rule-based benchmark: "Predict churn if recency_days > 60" → AUC: 0.64
- Model AUC: 0.74 → +15.6% over rule-based → model adds meaningful value

**3. Human baseline:** How does the model compare to expert human judgment?
- Human-labeled churn risk on 200 customers → human AUC: 0.69
- Model AUC: 0.74 → model outperforms human by 7.2% → model adds value beyond human judgment

**The benchmark calendar:**
- At Stage 6 (pre-deployment): establish all three baselines; document in model card
- Monthly (operational): compare to historical baseline
- On model update: new model must beat previous production model as its primary benchmark

**Figure:** *Benchmark comparison bar chart.* Three bars: Rule-based (0.64, labeled "simple threshold"), Human expert (0.69, labeled "domain expert panel"), NorthStar XGBoost v3.0 (0.74, labeled "current production"). Baseline from first deployment (0.741) marked as horizontal reference line. "Model ROI" annotation: "+15.6% over rule-based baseline." The chart makes the model's value concrete by comparison.

**Notes:** "The rule-based baseline is the most important benchmark to establish for every AI system. When someone asks 'what's the business value of the AI?', the benchmark answer is: 'It outperforms the best rule-based approach by 15.6% AUC, which translates to identifying 8,200 additional churners per year that the rule-based system would have missed.' That number has dollar value attached to it."

---

## Slide 6 — Guardrails as Operational Controls
**Layout:** Guardrails taxonomy and NorthStar implementation

**Content:**
**Guardrails: More Than Just Safety Filters**

Guardrails in AI systems serve three distinct functions:
1. **Safety guardrails:** Prevent harmful outputs (harmful content, PII disclosure, prompt injection)
2. **Quality guardrails:** Prevent low-quality outputs (hallucinations, format violations, off-topic responses)
3. **Business guardrails:** Enforce business rules (discount limits, offer eligibility, customer segment constraints)

**NorthStar Guardrail Architecture:**

**Bedrock Guardrails (Safety + some Quality):**
- Content filtering: hate speech, insults, prompt attacks → BLOCK
- Topic denial: competitor discussion, PII requests → BLOCK + LOG
- PII detection: EMAIL, PHONE → ANONYMIZE before response

**Application-level guardrails (Quality + Business):**
```python
class OfferGenerationGuardrails:
    
    MAX_DISCOUNT_PCT = 25  # Business rule: max discount 25%
    MIN_OFFER_EXPIRY_DAYS = 3  # Minimum: 3-day validity
    
    def validate_offer(self, offer_text: str) -> tuple[bool, str]:
        """Validate offer against business rules."""
        
        # Quality: format compliance
        if not re.match(OFFER_FORMAT_PATTERN, offer_text):
            return False, "FORMAT_VIOLATION"
        
        # Business: discount limit
        discount = extract_discount_pct(offer_text)
        if discount and discount > self.MAX_DISCOUNT_PCT:
            return False, f"DISCOUNT_EXCEEDS_MAX: {discount}% > {self.MAX_DISCOUNT_PCT}%"
        
        # Business: offer expiry
        expiry_days = extract_expiry_days(offer_text)
        if expiry_days and expiry_days < self.MIN_OFFER_EXPIRY_DAYS:
            return False, f"EXPIRY_TOO_SHORT: {expiry_days} days"
        
        return True, "VALID"
```

**Guardrail trigger metrics:**
- Safety guardrail trigger rate: < 0.5% of requests (higher → investigate attack or prompt issue)
- Quality guardrail trigger rate: < 1% (higher → prompt needs revision)
- Business guardrail trigger rate: < 0.1% (higher → model generating non-compliant offers)

**Figure:** *Guardrail architecture diagram.* Three-layer guardrail stack. Incoming offer text → Layer 1 (Bedrock Guardrails: content filter, topic denial, PII) → Layer 2 (Application quality guard: format validation, hallucination check) → Layer 3 (Business rules: discount limit, eligibility check) → Valid Offer → User. Each layer: trigger action (block/anonymize/rewrite/log). Metrics panel: trigger rate per layer with historical trend. The three-layer architecture shows defense-in-depth for output quality.

**Notes:** "Business guardrails are the guardrails that ML teams build but then forget to monitor. A discount cap of 25% sounds like a trivial constraint — until you discover that the LLM occasionally generates '50% off your entire next purchase' for high-value customers during the holiday season. Without the business guardrail, that offer goes out, customers redeem it, NorthStar loses margin. The guardrail catches it. The trigger rate metric tells you if the model is increasingly generating non-compliant offers — which might indicate prompt drift."

---

## Slide 7 — SLA Design for AI Systems
**Layout:** SLA framework with NorthStar targets

**Content:**
**Service Level Agreements for AI Systems:**

An SLA (Service Level Agreement) is a commitment about system behavior. For AI systems, SLAs have dimensions that traditional software SLAs don't:

**Availability SLA:** % of time the system is available to serve requests
- NorthStar Churn Endpoint: 99.9% (< 44 min/month downtime)
- NorthStar Offer Generation (Bedrock): 99.95% (inherits Bedrock SLA)
- NorthStar Agent (Bedrock): 99.95%

**Latency SLA:** Response time commitments
- Churn endpoint (real-time): P99 < 200ms
- Offer generation: P90 < 3s; P99 < 8s (long tail from LLM)
- Agent session: P90 < 15s; P99 < 60s (multi-turn reasoning)

**Quality SLA:** Model performance commitments (novel for AI)
- Churn model: AUC ≥ 0.70 in production (lower threshold than deployment gate to allow 2% degradation before alert)
- Offer generation: Faithfulness ≥ 0.92 (monitored weekly via RAGAS sampling)
- Agent: Resolution rate ≥ 82%

**Coverage SLA:** % of requests that receive a valid AI response (vs. fallback)
- Churn scoring: ≥ 98% of monthly customers scored in batch job
- Offer generation: ≥ 99.5% of offer requests receive a valid offer (vs. fallback to generic)
- Agent: ≥ 99% of sessions receive an initial response (vs. immediate escalation)

**Figure:** *SLA dashboard with gauges.* Four-panel gauge dashboard: Availability (gauge: 99.96% — above 99.9% target), Latency P99 (gauge: churn 142ms — within 200ms target; offer P90 2.8s — within 3s target), Quality (gauge: AUC 0.738 — above 0.70 production threshold), Coverage (gauge: 99.7% — above 99.5% target). All four gauges in green. The dashboard is what you'd show at a weekly operations review.

**Notes:** "The Quality SLA is the dimension that makes AI SLAs different from software SLAs. Traditional software doesn't have 'quality' SLAs — either the function returns the right answer, or it doesn't. AI systems produce outputs that are statistically correct on average, with known error rates and drift patterns. The Quality SLA commits to a minimum performance level and requires ongoing measurement to verify compliance."

---

## Slide 8 — Error Budgets: Quantifying Tolerable Imperfection
**Layout:** Error budget framework for AI systems

**Content:**
**The Error Budget: How Much Imperfection Can You Afford?**

An error budget (from SRE practice) makes the SLA concrete: if your availability SLA is 99.9%, your error budget is 0.1% of time — about 44 minutes/month of allowable downtime.

**Adapting Error Budgets to AI Systems:**

**Availability error budget:** Standard SRE concept.
- 99.9% availability → 44 minutes/month downtime budget
- If you've used 30 minutes in a month: slow down risky deploys; protect remaining budget

**Quality error budget (AI-specific):**
- If model must maintain AUC ≥ 0.70 in production (Production Quality SLA)
- And the model is currently at 0.738 AUC (current measured)
- Error budget: 0.738 - 0.70 = 0.038 AUC "units" of tolerable degradation
- If monitoring shows AUC trending to 0.71 over 3 weeks: budget is nearly exhausted → retrain now

**Prediction error budget:**
- Churn model: at 0.75 recall@0.4-precision, 25% of churners are missed
- Business tolerance: acceptable to miss up to 25% of churners (25 per 100 actual churners)
- If model recall drops to 0.65: 35% missed → exceeds error budget → retrain

**Error budget policy:**
- > 80% remaining: proceed with normal operations; routine deploys approved
- 50-80% remaining: caution; high-risk changes require additional review
- < 50% remaining: freeze non-critical changes; prioritize reliability work
- Budget exhausted: declare incident; all hands on root cause and fix

**Figure:** *Error budget visualization.* Three gauges (Availability, Quality, Coverage) showing current budget consumption as a percentage. Availability: 32% consumed (comfortable). Quality (AUC): 68% consumed (approaching threshold — amber warning). Coverage: 10% consumed (comfortable). Each gauge has policy zones colored green (>50% remaining), amber (20-50%), and red (<20%). The quality gauge in amber communicates: the model is approaching its quality error budget — attention required.

**Notes:** "The error budget concept is the most practically powerful idea in SRE practice. Without it, reliability decisions are arbitrary: 'should we deploy this risky change?' With error budgets, the decision is mechanical: 'we have 32% availability budget remaining this month, and this change carries 15% risk — that would leave us at 17%, below the safety threshold. Postpone to next month.' The error budget makes the decision objective, not political."

---

## Slide 9 — Monitoring Guardrails: Automated Quality Defense
**Layout:** Monitoring as a quality guardrail system

**Content:**
**Monitoring as the Operational Guardrail:**

Beyond pre-prediction guardrails, production AI systems need post-hoc monitoring guardrails — automated checks that run continuously and catch quality degradation before it reaches the user.

**NorthStar Monitoring Guardrail Stack:**

**Layer 1 — Real-time endpoint monitoring:**
```python
# CloudWatch alarm: churn endpoint error rate
cw.put_metric_alarm(
    AlarmName='northstar-churn-error-rate',
    MetricName='ModelLatencyError',
    Namespace='aws/sagemaker/Endpoints/InvocationsPerInstance',
    Statistic='Sum',
    Period=300,       # 5-minute evaluation window
    EvaluationPeriods=2,  # Alert if high for two consecutive periods
    Threshold=0.05,   # > 5% error rate
    ComparisonOperator='GreaterThanThreshold',
    AlarmActions=[SNS_TOPIC_ARN]  # → PagerDuty
)
```

**Layer 2 — Daily quality evaluation (scheduled):**
- SageMaker Processing Job runs daily
- Computes AUC on yesterday's prediction sample (with ground truth from Feature Store)
- If AUC < 0.70: CloudWatch alarm → retrain trigger

**Layer 3 — Weekly RAGAS sampling (for RAG offers):**
- Sample 5% of production offer responses
- Run RAGAS evaluation (faithfulness, relevancy, recall)
- If any metric < threshold: Slack alert to ML team + JIRA ticket

**Layer 4 — Monthly business metric audit:**
- Connect prediction IDs to business outcomes (churn events)
- Compute: precision and recall at the intervention threshold in production
- Report to business stakeholders with trend analysis

**Figure:** *Monitoring guardrail architecture.* Four layers shown vertically. Each layer: trigger type (real-time/daily/weekly/monthly), monitoring mechanism, alert destination, and action taken on alert. Arrows connect layers: Layer 2 daily check can trigger a canary rollback; Layer 3 weekly RAGAS can trigger a prompt review; Layer 4 monthly audit can trigger a model replacement project. The architecture shows monitoring as a continuous, multi-frequency quality defense system.

**Notes:** "Layer 4 — connecting predictions to outcomes — is the most valuable and least commonly implemented. It closes the feedback loop: you predicted a 73% probability of churn for customer C001 on October 1. Did C001 actually churn? If yes: the prediction was correct. If no: was the intervention successful? This is the data that tells you whether the model is driving business value, not just making statistically accurate predictions."

---

## Slide 10 — Lab 6 Overview: Building the Monitoring Platform
**Layout:** Lab 6 complete requirements

**Content:**
**Lab 6: Monitoring, Observability & Lifecycle Management**
*(Assigned Today | Due Sat Nov 22 | 12 days)*

**What you'll build:**

**Part 1: SageMaker Model Monitor (required)**
- Enable data capture on churn endpoint (20% sampling)
- Create baseline from training data using `suggest_baseline()`
- Schedule daily monitoring with PSI thresholds (0.20 for action, 0.15 for alert)
- CloudWatch alarm for monitoring violations

**Part 2: Unified CloudWatch Dashboard (required)**
- 5-section NorthStar AI platform dashboard:
  - Section 1: Data pipeline health (Glue success rate, feature freshness)
  - Section 2: Churn model health (endpoint latency, AUC trend, drift PSI)
  - Section 3: Offer generation health (latency, faithfulness score, token cost)
  - Section 4: Agent health (resolution rate, tool failure rate, escalation rate)
  - Section 5: Platform economics (daily cost by system, vs. budget)
- Dashboard must be shareable (public URL disabled; access via IAM)

**Part 3: Retraining Trigger (required)**
- Lambda function that monitors CloudWatch for PSI violation alarm
- On alarm: triggers SageMaker Pipeline (Lab 4) automatically
- Notification: SNS email to ML team with drift report

**Part 4: Monthly Compliance Report (required)**
- Lambda function triggered monthly (EventBridge)
- Generates: prediction count, drift status, SHAP summary, fairness metrics
- Outputs to S3 as JSON + PDF-format markdown
- Sends summary email to governance stakeholder

**Figure:** *Lab 6 architecture diagram.* Existing NorthStar platform with Lab 6 additions highlighted in a different color: Model Monitor → CloudWatch (drift alarms) → Retraining Lambda → SageMaker Pipeline (Lab 4). Unified Dashboard covering all four systems. Compliance Report Lambda (monthly EventBridge trigger) → S3 report → SNS email. Clean architecture showing Lab 6 as the operational intelligence layer.

**Notes:** "Lab 6 is 12 days — shorter window than Labs 4 and 5 but less complex. The critical path is: data capture enabled → baseline created → monitoring schedule configured → alarm triggers Lambda → Lambda triggers pipeline. Test each step before connecting the next. The Unified Dashboard (Part 2) is architecturally independent — build it in parallel with Part 1."

---

## Slide 11 — Metrics Anti-Patterns
**Layout:** Five metrics anti-patterns with NorthStar consequences

**Content:**
**Metrics Anti-Patterns That Lead Teams Astray:**

**1. Goodhart's Law: Optimizing the metric, not the outcome**
"When a measure becomes a target, it ceases to be a good measure." — Goodhart
Example: The team optimizes churn recall (catching 85% of churners) by flagging all high-spend customers as at churn risk. Recall is high; precision is terrible; retention budget is wasted on low-risk customers.
Fix: Measure multiple metrics that together constrain optimization. Precision and recall, not recall alone.

**2. Vanity Metrics: Metrics that feel good but don't drive decisions**
Example: "We scored 500,000 customers this month." OK, but did the scores drive interventions? Did the interventions reduce churn? Prediction count is a vanity metric if it's not connected to outcomes.
Fix: Every metric must connect to an action or decision. If nobody acts on a metric, stop measuring it.

**3. Metric Mismatch: Technical metrics disconnected from business outcomes**
Example: AUC is 0.74 and stable. Churn rate is increasing. Team declares "AI is working." Business declares "AI isn't helping." Both are right with different metrics.
Fix: Map technical metrics explicitly to business metrics. If AUC is stable but churn is rising, investigate non-model causes (intervention strategy, offer quality).

**4. Alert Fatigue: Too many alerts, all the same urgency**
If 47 alerts fire per day and all are P2 severity, engineers learn to ignore them. A real P1 incident gets lost in the noise.
Fix: Ruthless alert prioritization: P1 (PagerDuty at 2 am), P2 (Slack), P3 (daily digest). Fewer alerts, higher signal quality.

**5. Missing the Counter-Metric: Optimizing without constraining**
Example: Optimize for offer acceptance rate. Team discovers that sending 20 offers per customer session maximizes the acceptance rate (volume metric). But customer satisfaction tanks.
Fix: Counter-metrics — add CSAT as a constraint metric alongside acceptance rate.

**Figure:** *Five anti-patterns table.* Five rows with anti-pattern name, example, consequence, and fix. "Goodhart's Law" row includes the quote. "Alert Fatigue" row has a metric: "Teams with > 20 P2 alerts/day have 60% lower incident response rates." Clean, direct format.

**Notes:** "Alert fatigue is the most operationally dangerous anti-pattern. I've seen production ML systems where the monitoring sends 150 alerts per day. Engineers triage by checking whether anything is on fire, not by carefully reading alerts. The cure: every alert must pass the '2 am test' — would you wake up the on-call engineer at 2 am for this? If not, it's not P1. Be ruthless about alert severity."

---

## Slide 12 — Production Metrics Reporting: The Weekly Operations Review
**Layout:** Weekly operations review structure for NorthStar

**Content:**
**The Weekly AI Operations Review:**

High-performing AI teams hold a weekly operations review — not to review dashboards (that's async), but to discuss: what changed, what decisions need to be made, what's at risk.

**NorthStar Weekly Operations Review Agenda (30 minutes):**

**1. Metrics summary (5 min):**
- Dashboard reviewed async before the meeting
- Meeting opens with: anything in red or amber this week?
- Action items from last week: closed?

**2. Drift report (5 min):**
- Model Monitor PSI status for all features
- Any features approaching alert threshold?
- Retraining recommendation?

**3. Business metrics update (5 min):**
- Offer acceptance rate trend
- Agent resolution rate trend
- Any anomalies vs. prior week?

**4. Incident review (5 min):**
- Any incidents in the past week?
- Root cause determined?
- Prevention measures in place?

**5. Forward risk (5 min):**
- What's coming up? Holiday shopping approaching (Q4 drift risk)
- Any planned changes that could impact metrics?
- Resource needs?

**6. Action items (5 min):**
- Capture owners and due dates

**Figure:** *Weekly operations review agenda card.* A meeting agenda card with time allocations, sections, and example discussion points pre-populated for a hypothetical week. Key items highlighted: "PSI for monetary_30d at 0.17 — approaching alert threshold (0.20). Discuss: retrain ahead of Q4?" and "Agent resolution rate dipped to 83% Monday. Root cause: order_lookup_tool latency spike. Fixed Tuesday. No recurring risk." The agenda card communicates: structured operations review is more efficient than ad hoc monitoring.

**Notes:** "The weekly operations review is where the three-tier metrics hierarchy comes to life. You start with Level 3 (business metrics trend), drill into Level 2 (operational anomalies), and focus deep investigation on Level 1 (technical root cause) only when needed. The meeting should rarely need to go below Level 2 — most weeks are 'all green, monitoring is healthy.' The weeks when you need Level 1 are the weeks with incidents or declining trends."

---

## Slide 13 — Metric Connection: AUC to Revenue
**Layout:** Metric chain connecting AUC to business outcomes for NorthStar

**Content:**
**The Metric Chain: Connecting Technical to Business**

Every technical metric should have a documented chain to business impact. Without this chain, your team can't justify continued investment.

**NorthStar Churn Model Metric Chain:**

```
AUC (0.74)
    ↓
Recall@0.4-precision (0.78)
    → 78% of actual churners identified correctly
    ↓
Intervention coverage (churn score > 0.6 → intervention triggered)
    → 520 customers per month above threshold (estimated)
    ↓
Intervention effectiveness (historical: 32% of intervened customers retained)
    → 520 × 0.32 = 166 customers retained per month
    ↓
Revenue retained per customer (average: $287/year)
    → 166 × $287 = $47,642 in annual revenue per month of retention
    ↓
Monthly value of churn model: $47,642
    Cost of churn model: ~$610/month (platform + inference)
    ↓
Monthly ROI: ($47,642 - $610) / $610 = 77× return
Annual value: $571,704 in retained revenue
```

**Figure:** *Metric chain waterfall diagram.* Vertical waterfall showing each step in the chain above, with values and conversion rates at each step. Starting at top: AUC (0.74). Ending at bottom: Annual value ($571,704). Each step: metric name, value, and conversion rate. "Model cost" arrow pointing into the chain at the correct level. The waterfall makes the business case for the churn model visible from first principles.

**Notes:** "This metric chain is the answer to 'prove that your AI is creating value.' It's built from publicly discussable assumptions (intervention effectiveness, revenue per customer), model metrics, and business data. Every step should be verifiable and defensible. When the CFO challenges the ROI number, you should be able to defend each conversion rate with data. The weakest assumption in this chain is typically the intervention effectiveness rate — invest in A/B testing to get a rigorous measurement."

---

## Slide 14 — Lab 6 Walkthrough: Model Monitor Configuration
**Layout:** Detailed Model Monitor setup walkthrough for Lab 6

**Content:**
**Lab 6 Part 1: Model Monitor Setup (Step by Step)**

**Step 1: Enable data capture on the endpoint**
```python
# Update endpoint to capture 20% of requests
from sagemaker.model_monitor import DataCaptureConfig

data_capture_config = DataCaptureConfig(
    enable_capture=True,
    sampling_percentage=20,
    destination_s3_uri='s3://northstar-monitoring/data-capture/',
    capture_options=['REQUEST', 'RESPONSE'],  # Capture both input and output
    csv_content_types=['text/csv'],
    json_content_types=['application/json']
)

# Update existing endpoint (not replace!)
sagemaker_client.update_endpoint(
    EndpointName='northstar-churn-prod',
    EndpointConfigName=new_config_name_with_capture
)
```

**Step 2: Generate baseline from training data**
```python
from sagemaker.model_monitor import DefaultModelMonitor
from sagemaker.model_monitor.dataset_format import DatasetFormat

monitor = DefaultModelMonitor(
    role=SAGEMAKER_ROLE_ARN,
    instance_count=1,
    instance_type='ml.m5.xlarge',
    volume_size_in_gb=20
)

baseline_job = monitor.suggest_baseline(
    baseline_dataset='s3://northstar-processed/training/churn-features-baseline.csv',
    dataset_format=DatasetFormat.csv(header=True),
    output_s3_uri='s3://northstar-monitoring/baseline/',
    wait=True
)
```

**Step 3: Schedule monitoring (runs daily at 6 AM UTC)**
```python
from sagemaker.model_monitor import CronExpressionGenerator

monitor.create_monitoring_schedule(
    monitor_schedule_name='northstar-churn-daily-monitor',
    endpoint_input=EndpointInput(endpoint_name='northstar-churn-prod'),
    output_s3_uri='s3://northstar-monitoring/reports/',
    statistics=baseline_job.baseline_statistics(),
    constraints=baseline_job.suggested_constraints(),
    schedule_cron_expression=CronExpressionGenerator.daily()
)
```

**Figure:** *Lab 6 Model Monitor setup flow.* Three-step flow: Step 1 (data capture config → endpoint update), Step 2 (baseline job → S3 baseline stats + constraints), Step 3 (monitoring schedule → daily processing job → CloudWatch violations). S3 bucket structure shown: `/data-capture/` (captured requests), `/baseline/` (statistics.json + constraints.json), `/reports/` (daily monitoring output). Each step is labeled with the Lab 6 file that implements it.

**Notes:** "The most common Lab 6 Part 1 failure: forgetting to update the endpoint to enable data capture (Step 1), then running the monitoring schedule (Step 3), and seeing no data in CloudWatch. The monitoring schedule only produces results when there's captured data to monitor. Step 1 is the prerequisite — verify that captured data is appearing in S3 before moving to Steps 2 and 3."

---

## Slide 15 — Key Takeaways + What's Next
**Layout:** Takeaways + L21 preview

**Content:**
**Key Takeaways:**
1. The metrics hierarchy has three levels: Technical (model quality), Operational (system health), Business (value created) — most teams only measure Level 1; all three are required for full operational intelligence
2. Leading indicators predict problems before they appear in business metrics — measure PSI drift, latency trends, and offer acceptance rate daily, not just AUC weekly
3. Error budgets make SLA decisions objective: when < 50% of quality budget remains, freeze non-critical changes; when budget is exhausted, declare incident
4. Guardrails operate at three levels: safety (harmful content), quality (hallucinations, format), and business (discount limits, eligibility) — monitor trigger rates for all three
5. Every technical metric needs a chain to business value: AUC → recall → intervention coverage → effectiveness → revenue retained; without this chain, you can't justify AI investment

**Next Session (Thu Nov 12):**
- Topic: Monitoring, Observability & Model Lifecycle Management — deep dive on SageMaker Model Monitor; LLMOps observability; when to retrain vs. retire
- Lab 6 due in 12 days — get Part 1 (data capture) enabled today
- **Lab 5 due Saturday** — final check: is everything submitted?

**Figure:** *Five-takeaway summary card.* Lab 5 due Saturday (4 days, red). Lab 6 countdown (12 days, amber). Metric chain waterfall thumbnail. Weekly operations review agenda thumbnail.

**Notes:** "Lab 5 is due Saturday. Make sure the submission is complete: canary endpoint is active, auto-scaling policy is attached, batch transform job has completed at least once, deployment runbook is written, CloudWatch scale-out screenshot is included. After Saturday, focus entirely on Lab 6. Enable data capture on the endpoint today (Lab 6 Part 1, Step 1) — it takes 15 minutes, and you need the captured data to accumulate before you can run the baseline and monitoring schedule."
