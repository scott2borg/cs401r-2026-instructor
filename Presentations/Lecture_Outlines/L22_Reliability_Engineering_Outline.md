---
lecture: L22
title: Reliability Engineering for AI Systems
date: Tuesday, November 17, 2026
week: 12
arc: Operate
reading_due: "Reliability for AI Systems — SRE Principles through Graceful Degradation"
lab_due: "Lab 6 due Sat Nov 22 (5 days)"
slides_target: 15
---

# L22: Reliability Engineering for AI Systems
**Tuesday, November 17, 2026 | CS 401R: Engineering Production AI Systems | Fall 2026**

> Every AI system will fail. The question is not whether it fails, but how it fails, how fast you recover, and whether users experience it. Reliability engineering is the discipline of designing failure modes before they happen.

**Reading Due:** *Reliability for AI Systems* — "SRE Principles" through "Graceful Degradation"
**Lab 6 Due:** Sat Nov 22 (5 days)

---

## Slide 1 — Title
**Layout:** Left dark panel + right reliability engineering concepts

**Content:**
- Reliability Engineering for AI Systems
- CS 401R · Lecture 22 · Tuesday, November 17, 2026
- Designing Systems That Fail Gracefully

**Figure:** *Reliability spectrum visual.* Horizontal axis: System availability (0% to 100%). Three zones marked: "Always down" (left, red), "Fails sometimes" (center, amber), "Highly available" (right, green). Above the axis: the famous nine nines: 90% = 36.5 days/year downtime, 99% = 3.65 days, 99.9% = 8.7 hours, 99.99% = 52.6 minutes, 99.999% = 5.3 minutes. NorthStar target: 99.9% marked on the axis. The visual establishes that reliability is quantified, not qualitative — and that the difference between "99%" and "99.9%" is significant.

**Notes:** "The gap between 99% and 99.9% availability is 3.6 days per year of downtime — 3.6 days when your churn predictions aren't running, your offers aren't generating, and your agents aren't serving customers. For NorthStar, that's 3.6 days when the retention campaign goes dark. The engineering effort to go from 99% to 99.9% availability is significant — but the business impact of that 3.6-day difference is more significant."

---

## Slide 2 — SRE Principles Applied to AI Systems
**Layout:** SRE principles adapted for ML/AI context

**Content:**
**Site Reliability Engineering: Four Core Principles (adapted for AI)**

SRE (Google, 2003) established engineering principles for reliable services. Applied to AI:

**1. Embrace risk:** Perfect reliability is not the goal — appropriate reliability for the use case is. 99.9% is the right target for NorthStar's churn endpoint; 99.999% would cost 10× more, and the additional reliability isn't worth it.

**2. Service Level Objectives (SLOs):** Define reliability targets explicitly before building the system. An SLO is a target; an SLA is a commitment. For NorthStar: SLO = 99.9% availability; SLA = what we promise to the business.

**3. Eliminate toil:** Toil is repetitive manual work that scales linearly with system size. In AI systems: manual model deployment is toil (eliminated by Lab 4 CI/CD); manual drift monitoring is toil (eliminated by Lab 6 Model Monitor). The goal is to eliminate toil and redirect engineers to higher-value work.

**4. Monitoring and alerting:** Already covered in L21. The SRE principle: alert on symptoms (user-visible impact), not causes (internal metrics). Don't alert on "CPU > 80%" — alert on "latency P99 > 200ms" (the symptom users experience).

**AI-specific SRE additions:**
- **Model quality as a reliability dimension:** Traditional SRE tracks availability and latency. AI systems need model quality tracked with the same rigor — a "running but wrong" model is an invisible failure mode.
- **Data dependency reliability:** AI systems depend on data pipelines. Data reliability = pipeline reliability + data quality = an additional reliability dimension.

**Figure:** *SRE principles diagram.* Four quadrant layout: Embrace Risk (top-left), SLOs (top-right), Eliminate Toil (bottom-left), Monitoring (bottom-right). Each quadrant: principle name, 1-sentence definition, NorthStar application example. AI-specific additions shown as a fifth element overlaying the four quadrants. The layout communicates: SRE is a complete framework, not just monitoring.

**Notes:** "The 'alert on symptoms, not causes' principle is the one that teams consistently get wrong. You configure 47 internal metrics alerts. The on-call engineer gets 47 alerts and has to triage: which one matters? The right approach: configure a small number of user-visible symptom alerts (latency > SLO, error rate > threshold, model quality below gate). When a symptom fires, you investigate causes. Symptoms are what on-call engineers need to know about at 2 am."

---

## Slide 3 — Designing for Failure: The Failure Mode Analysis
**Layout:** Failure mode analysis for NorthStar AI systems

**Content:**
**Failure Mode Analysis: Enumerate Failures Before They Happen**

**Churn Prediction System — Failure Modes:**

| Failure Mode | Probability | Impact | Detection | Recovery |
|-------------|-------------|--------|-----------|----------|
| Endpoint unavailable | Low | High (no predictions) | CloudWatch error rate alarm | Auto-scale restart; rollback |
| Feature Store unavailable | Low | High (stale/no features) | CloudWatch Glue job failure | Use cached features; fallback rules |
| Model drift (silent) | Medium | Medium (wrong predictions) | Model Monitor PSI alarm | Trigger retraining |
| Prediction latency spike | Medium | Low-Medium (SLA miss) | P99 latency alarm | Auto-scale; investigate |
| Batch job failure (monthly) | Low | Low (delayed scoring) | EventBridge job status | Re-trigger; manual fallback |

**Offer Generation System — Failure Modes:**

| Failure Mode | Probability | Impact | Detection | Recovery |
|-------------|-------------|--------|-----------|----------|
| Bedrock API unavailable | Low | High (no offers) | Error rate alarm | Use cached offers; generic fallback |
| RAG index stale | Medium | Medium (irrelevant offers) | RAGAS recall decline | Emergency index refresh |
| Guardrail blocking too many | Low | Medium (users see error) | Guardrail trigger rate alarm | Review guardrail config |
| Token budget exhausted | Low | Low (truncated responses) | Token count alarm | Increase budget; optimize prompt |

**Figure:** *Failure mode risk matrix.* 5×5 risk matrix: x-axis: Impact (Low to High), y-axis: Probability (Low to High). Each failure mode from the tables plotted as a labeled dot. High-priority failures (high probability + high impact) in the top-right quadrant, highlighted in red. "Mitigation priority" zone circled. The matrix communicates: focus reliability investment on the high-probability, high-impact quadrant.

**Notes:** "The failure mode analysis forces you to think about failures before they happen — not during an incident at 2 am. The most important column in the table is 'Recovery' — before going to production, every failure mode must have a documented recovery procedure. If the recovery procedure is 'unknown,' that failure mode must be investigated and the recovery designed before launch."

---

## Slide 4 — Graceful Degradation: Failing with Style
**Layout:** Graceful degradation patterns for NorthStar

**Content:**
**Graceful Degradation: The AI System Should Fail Gracefully**

When an AI component fails, the system should degrade gracefully — not fail catastrophically. This means having explicit fallback behaviors for every failure mode.

**NorthStar Graceful Degradation Hierarchy:**

**Churn Prediction Fallback Chain:**
1. **Full AI (Primary):** XGBoost model endpoint → personalized churn probability for each customer
2. **Stale Predictions (Fallback Level 1):** Serve yesterday's batch predictions from S3 cache (acceptable: churn doesn't change overnight)
3. **Segment-Based Predictions (Fallback Level 2):** Use customer segment average churn rates (medium-value customers → 8.5% churn rate) — statistical, not individual
4. **Rule-Based Fallback (Fallback Level 3):** `churn_risk = HIGH if recency_days > 60 else LOW` — simple but functional
5. **No Prediction (Terminal Fallback):** All customers treated as medium risk; all eligible for standard retention offer

**Offer Generation Fallback Chain:**
1. **Full RAG (Primary):** Personalized offer via Bedrock + Knowledge Base
2. **Cached Offers (Fallback Level 1):** Pre-computed offers for each customer segment, refreshed weekly
3. **Template Offers (Fallback Level 2):** Fill-in-the-blank template offers based on segment (e.g., "As a Premium customer, here's a special offer")
4. **Generic Offers (Fallback Level 3):** Site-wide promotion, same for all customers

**Figure:** *Degradation hierarchy diagram.* Vertical stack for Churn system: Primary (full AI) at top (bright teal), cascading down through Fallback 1 (lighter), Fallback 2 (lighter still), Fallback 3 (pale), Terminal (near-white). Each level: description, quality score (100%, 85%, 70%, 55%, 30%), and trigger condition. Arrow down the right side: "Degradation path — entered automatically when upstream level fails." The cascade communicates: graceful degradation is a pre-designed, pre-tested path, not an ad hoc response.

**Notes:** "The 'stale predictions' fallback is the most operationally valuable one for the churn model. When the real-time endpoint is down, yesterday's predictions are almost as good as today's — churn prediction doesn't need sub-second freshness. Caching yesterday's batch predictions in S3 (or ElastiCache) means your retention campaign keeps running at 98% quality even when the endpoint is unavailable. Build this fallback cache before you need it, not during the incident."

---

## Slide 5 — Error Budgets in Practice: The Reliability Investment Decision
**Layout:** Error budget tracking and decision framework

**Content:**
**Managing Error Budgets: The Reliability Investment Decision**

Error budget tracking turns abstract reliability goals into concrete engineering decisions.

**NorthStar Error Budget Tracking (November):**

| System | SLO | Monthly Budget | Consumed | Remaining | Policy |
|--------|-----|----------------|---------|-----------|--------|
| Churn Endpoint | 99.9% availability | 44.0 min | 8.2 min | 35.8 min (81%) | Green: proceed normally |
| Churn Model Quality | AUC ≥ 0.72 | 0.019 AUC "units" | 0.003 | 0.016 (84%) | Green |
| Offer Generation | 99.5% availability | 3.6 hours | 0.4 hours | 3.2 hours (89%) | Green |
| Agent | 99.5% availability | 3.6 hours | 0.8 hours | 2.8 hours (78%) | Green |

**Error budget consumption events this month:**
- Nov 3: Churn endpoint restart after OOM — 6 min downtime (incident)
- Nov 9: Data capture config update caused 2.2 min blip (planned maintenance)

**Error budget policy in action:**
- 8.2 minutes consumed, 35.8 remaining → **Normal operations**; risky changes approved
- If the Nov 15 Lab 6 deployment (data capture update) causes > 25 min downtime → budget drops below 50% → freeze risky changes for the rest of the month

**Figure:** *Error budget consumption gauge dashboard.* Four gauges (one per system). Each gauge: monthly budget, consumed (shown as filled sector), remaining (unfilled sector). Traffic-light zones: green (> 50% remaining), amber (20-50%), red (< 20%). All four gauges in green with labels showing % consumed. Small annotation: "Nov 3 incident: 6 min" with arrow pointing to the churn endpoint gauge's filled sector. The gauges make budget consumption visceral and trackable.

**Notes:** "The error budget is the tool that makes the conversation between engineering and operations objective. When a product manager asks 'can we do a major deployment this week?' the answer is: 'We've consumed 19% of our availability budget this month. The proposed deployment carries a 15% risk of a 10-minute outage. That would take us to 34% consumed — still within Green. Approved.' Without error budgets, that conversation is a negotiation. With error budgets, it's math."

---

## Slide 6 — Chaos Engineering for AI: Breaking Things on Purpose
**Layout:** Chaos engineering principles adapted for AI systems

**Content:**
**Chaos Engineering: Controlled Failure to Build Confidence**

Chaos engineering (Netflix's Chaos Monkey) deliberately injects failures to:
1. Verify that your fallback mechanisms actually work
2. Discover failure modes you hadn't anticipated
3. Build operational confidence before unplanned failures expose the gaps

**AI-specific chaos experiments for NorthStar:**

**Experiment 1: Churn endpoint cold start resilience**
- Hypothesis: When the endpoint auto-scales from 1 to 2 instances, the first request to the new instance returns in < 5 seconds
- Method: Scale endpoint to 0 instances (temporarily); send a burst of 5 requests; measure response times
- Expected result: 1 cold-start response takes ~30 seconds; subsequent requests ~28ms
- Pass criterion: application falls back to cached predictions during cold start (< 30s); no user-visible error
- NorthStar finding: the fallback cache isn't populated for new instances → cold start causes 100% error for ~30 seconds → **BUG FOUND**

**Experiment 2: Feature Store latency injection**
- Hypothesis: When Feature Store latency exceeds 500ms, offer generation degrades gracefully to cached segment offers
- Method: Add artificial 600ms delay to Feature Store queries (Lambda throttling)
- Expected result: timeout fires; fallback to cached segment offers; user sees segment offer, not personalized offer
- Pass criterion: no timeout error surfaced to user; fallback metric increments in CloudWatch

**Experiment 3: Bedrock API unavailability**
- Hypothesis: When Bedrock API returns errors, the offer generation system falls back to template offers
- Method: Temporarily point offer generation at a mock endpoint that returns HTTP 503
- Expected result: fallback to template offers; alert fires to ML team; no user-visible failure

**Figure:** *Chaos experiment log.* Three experiments as cards. Each card includes: hypothesis, method, expected result, actual result, pass/fail status, and action taken. Experiment 1: FAIL (bug found). Experiments 2-3: PASS. "Bug found" card highlighted in amber — this is the value of chaos engineering: finding the bug in a controlled experiment, not during a real incident.

**Notes:** "The cold-start bug found in Experiment 1 is exactly the kind of bug that chaos engineering is designed to find. The team assumed the fallback cache was populated when a new instance came up. It wasn't — the cache is populated lazily on first successful prediction, which means the first 30 seconds after a new instance starts have no cache. The fix: pre-populate the cache when the instance starts (warm-up Lambda). Chaos engineering found this before a customer experienced a 30-second error response."

---

## Slide 7 — The Fallback Cache Pattern: Building the Safety Net
**Layout:** Fallback cache implementation for NorthStar

**Content:**
**Implementing the Fallback Cache:**

```python
# ElastiCache (Redis) for fallback prediction storage
import boto3
import json
import redis

# Redis client (ElastiCache endpoint)
redis_client = redis.Redis(
    host='northstar-ai-cache.abc123.cache.amazonaws.com',
    port=6379, ssl=True
)

def get_churn_prediction_with_fallback(customer_id: str) -> dict:
    """Get churn prediction with cascading fallback."""
    
    # Try Level 1: Real-time endpoint
    try:
        prediction = invoke_churn_endpoint(customer_id, timeout=0.5)
        
        # Cache successful prediction for fallback (TTL: 25 hours)
        cache_key = f'churn_pred:{customer_id}'
        redis_client.setex(cache_key, 90000, json.dumps(prediction))
        
        return {'source': 'realtime', 'prediction': prediction}
    
    except (EndpointUnavailable, TimeoutError):
        pass  # Fall through to Level 2
    
    # Try Level 2: Cached prediction (stale but available)
    cache_key = f'churn_pred:{customer_id}'
    cached = redis_client.get(cache_key)
    if cached:
        prediction = json.loads(cached)
        return {'source': 'cache_stale', 'prediction': prediction,
                'cache_age_hours': get_cache_age(cache_key)}
    
    # Try Level 3: Segment-based prediction
    segment = get_customer_segment(customer_id)
    if segment:
        segment_rate = SEGMENT_CHURN_RATES.get(segment, 0.085)
        return {'source': 'segment_avg', 'prediction': {'churn_probability': segment_rate}}
    
    # Level 4: Generic default
    return {'source': 'default', 'prediction': {'churn_probability': 0.085}}

SEGMENT_CHURN_RATES = {
    'High-Value': 0.042,
    'Premium': 0.058,
    'Medium-Value': 0.085,
    'Low-Value': 0.142,
    'New-Customer': 0.112
}
```

**Figure:** *Fallback cache hit rate dashboard.* Stacked bar chart (last 30 days). Daily bars showing: % Real-time (primary, teal, ~95%), % Cache (fallback 1, lighter teal, ~3%), % Segment (fallback 2, amber, ~1%), % Default (fallback 3, red, <1%). One day with elevated cache usage (Nov 3 incident — 6-min endpoint outage causing ~8% cache fallback that day). The chart shows: fallbacks are rarely needed but always available.

**Notes:** "The `source` field in the response is critical for operational visibility. When you aggregate predictions, you want to know: what % of today's churn predictions came from the real-time model, and what % from fallbacks? If fallback usage is trending up, it's a leading indicator that the primary endpoint is experiencing reliability issues. The fallback is working — but you should investigate why the primary is failing."

---

## Slide 8 — Multi-Component Reliability: Cascading Failure Prevention
**Layout:** Cascading failure patterns and circuit breakers

**Content:**
**Cascading Failures in AI Systems:**

AI systems are composed of multiple components (data pipeline → feature store → endpoint → application). Cascading failure occurs when one component's failure overloads adjacent components.

**NorthStar Cascading Failure Scenario:**
1. Feature Store becomes slow (high latency)
2. Churn endpoint calls Feature Store for each prediction request
3. Requests queue in the endpoint (waiting for Feature Store)
4. Endpoint request queue fills; new requests begin timing out
5. Application layer retries timed-out requests (retry storm)
6. Retry storm doubles load on Feature Store (already slow)
7. Feature Store crashes under double load
8. Endpoint crashes from connection pool exhaustion
9. Application crashes from cascading failures

**Prevention 1: Circuit Breaker Pattern**
```python
from circuitbreaker import circuit

@circuit(failure_threshold=5,    # Open after 5 failures
         recovery_timeout=30,     # Try again after 30 seconds
         expected_exception=FeatureStoreTimeoutError)
def get_customer_features(customer_id: str) -> dict:
    """Get features from Feature Store with circuit breaker."""
    return feature_store_client.get_record(customer_id, timeout=0.5)
```

When the circuit is "open": requests immediately fall back to cached features without attempting Feature Store — breaking the cascade.

**Prevention 2: Retry with Exponential Backoff (not blind retry)**
```python
def retry_with_backoff(fn, max_retries=3, base_delay=0.5):
    for attempt in range(max_retries):
        try:
            return fn()
        except TransientError:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt)  # 0.5s, 1s, 2s
            time.sleep(delay)
```

**Prevention 3: Bulkhead Pattern**
Isolate components so one failing component can't exhaust resources of another.
NorthStar: feature store connection pool is separate from the inference connection pool.

**Figure:** *Circuit breaker state diagram.* Three states: CLOSED (normal), OPEN (failing fast), HALF-OPEN (testing). Transitions: CLOSED → OPEN (after 5 failures), OPEN → HALF-OPEN (after 30 seconds), HALF-OPEN → CLOSED (success) or HALF-OPEN → OPEN (failure). Request flow in each state: CLOSED → try Feature Store. OPEN → immediately return fallback (no Feature Store call). HALF-OPEN → try one test request. The state machine diagram shows how the circuit breaker works.

**Notes:** "The circuit breaker is the most important pattern for preventing cascading failures in AI systems. Without it, one slow component triggers retry storms that take down the whole system. With it, the circuit opens after 5 failures and immediately falls back to cached predictions for 30 seconds — breaking the cascade before it propagates. The circuit breaker pays for itself the first time it prevents a cascading failure from becoming a full platform outage."

---

## Slide 9 — SLA Design for the Business: What to Promise
**Layout:** SLA design methodology with NorthStar examples

**Content:**
**How to Design AI System SLAs:**

SLAs should be designed from business requirements, not engineering capabilities. The process:

**Step 1: Start with the business requirement**
"Churn campaign requires predictions to be available during business hours (8 AM - 10 PM ET, M-F)."
→ Availability requirement: 100% during business hours; < 99.9% downtime acceptable overnight

**Step 2: Translate to technical SLA**
"Available during business hours" → 99.97% availability (99.9% annualized)
"Predictions within 200ms" → SageMaker endpoint P99 < 200ms

**Step 3: Verify achievability**
Current infrastructure achieves: 99.96% availability (cloud infrastructure baseline)
Auto-scaling handles peak load within P99 target

**Step 4: Define measurement**
Measurement: CloudWatch uptime monitoring, 1-minute intervals
Reporting: monthly uptime percentage to business stakeholders

**Step 5: Set consequences**
SLA breach → incident review + engineering priority escalation for the following month

**NorthStar AI Platform SLA Summary:**

| System | Availability SLA | Latency SLA | Quality SLA | Coverage SLA |
|--------|-----------------|-------------|------------|--------------|
| Churn (real-time) | 99.9% | P99 < 200ms | AUC ≥ 0.70 | 99%+ scored |
| Churn (batch) | Complete within 4h | N/A | AUC ≥ 0.70 | 100% of customers |
| Offer Generation | 99.5% | P90 < 3s | Faithfulness ≥ 0.92 | 99.5%+ get an offer |
| Agent | 99.5% | P90 < 15s | Resolution ≥ 82% | 99%+ get a response |

**Figure:** *SLA design process flowchart.* Five steps (Business Requirement → Technical SLA → Verify → Measure → Consequences) as a horizontal flow with arrows. For NorthStar churn: each step filled in with the specific values from the content above. The flowchart communicates: SLAs are derived from business requirements through a deliberate process.

**Notes:** "The Quality SLA column is what makes this SLA table uniquely AI-native. Traditional web service SLAs don't have 'AUC ≥ 0.70' or 'Faithfulness ≥ 0.92.' These are AI-specific reliability commitments — commitments that the system will perform at a certain quality level, not just that it will respond quickly. Building Quality SLAs requires ongoing evaluation infrastructure (Model Monitor, RAGAS sampling) — which is exactly what Lab 6 delivers."

---

## Slide 10 — Reliability Patterns in the Lab Sequence
**Layout:** How reliability patterns appear across Labs 1-6

**Content:**
**Reliability Patterns Built in the Lab Sequence:**

**Lab 1 (IaC):** Reliability foundation
- Pattern: Infrastructure as Code ensures environments are reproducible
- Reliability impact: eliminates "works in dev, fails in prod" as a failure mode

**Lab 2 (Data Engineering):** Data reliability
- Pattern: Glue Workflow orchestration; CloudWatch pipeline monitoring; data quality gates
- Reliability impact: data pipeline failures detected within minutes; bad data gates prevent corrupt training

**Lab 3 (Model Development):** Model quality baseline
- Pattern: Evaluation gate (AUC ≥ 0.72); SHAP analysis; Model Registry with metadata
- Reliability impact: only quality-verified models can be deployed

**Lab 4 (CI/CD):** Deployment reliability
- Pattern: Automated CI/CD; gate checks; evaluation report as artifact
- Reliability impact: human error in manual deployments eliminated; consistent deployment process

**Lab 5 (Deployment & Scaling):** Runtime reliability
- Pattern: Canary deployment; automated rollback; auto-scaling; batch fallback
- Reliability impact: deployment failures auto-rollback in < 2 minutes; traffic spikes handled automatically

**Lab 6 (Monitoring):** Operational reliability
- Pattern: Model Monitor drift detection; unified dashboard; retraining trigger; runbooks
- Reliability impact: silent degradation detected within hours (not weeks)

**The Labs collectively implement the DORA Elite reliability patterns:**
- Deployment frequency: Lab 4 enables bi-weekly deployments
- Change failure rate: Labs 4-5 reduce to < 15%
- MTTR: Lab 5 canary rollback achieves < 15 min MTTR
- Lead time: Labs 4-5 reduce from weeks to days

**Figure:** *Lab sequence reliability maturity chart.* After each lab: reliability capability added and MTTR impact. Starting point (before Lab 1): undefined reliability; 4-8 hour MTTR. After Lab 5: 15-minute MTTR. After Lab 6: proactive monitoring; problem detected before users experience it. Staircase chart showing MTTR declining across labs. The chart makes the reliability impact of each lab concrete.

**Notes:** "When you interview for an ML engineering role and they ask about your experience with production AI systems, this lab sequence is the story you tell. Not 'I trained models in notebooks' — 'I built a production AI platform with CI/CD, canary deployment, auto-scaling, Model Monitor drift detection, and automated retraining. Here's the architecture, here's the reliability impact, and here's the MTTR before and after each capability was added.'"

---

## Slide 11 — The Reliability Stack for NorthStar: Full Picture
**Layout:** Complete reliability architecture for NorthStar after all labs

**Content:**
**NorthStar Reliability Stack (after Labs 1-6):**

**Prevention (reduce failures):**
- IaC (Terraform): eliminates configuration drift between environments
- Evaluation gate (Lab 4): prevents bad models from reaching production
- Canary deployment (Lab 5): limits blast radius of bad deployments to 10%
- Input validation + guardrails: prevents bad inputs from reaching models

**Detection (catch failures fast):**
- CloudWatch endpoint alarms: P99 latency and error rate (< 5 min detection)
- Model Monitor: drift detection (< 24-hour detection for daily monitoring)
- RAGAS sampling: LLM quality degradation (< 7 day detection)
- Agent trace monitoring: tool failure and loop detection (< 1 hour detection)

**Recovery (restore service fast):**
- Automated rollback (Lab 5): < 2 min to restore previous model
- Fallback cache: < 1 second to switch to cached predictions
- Graceful degradation: < 1 second to switch to segment-based predictions
- Manual override: < 5 min for human-initiated rollback

**Prevention of recurrence:**
- Post-incident review (mandatory for P1/P2 incidents)
- Test case added for every production bug
- Runbook updated after every incident
- Chaos experiments verify fixes work

**Figure:** *Reliability stack diagram.* Four horizontal layers (Prevention, Detection, Recovery, Prevention of Recurrence). Each layer: 3-4 control items with the lab that implemented them labeled. Detection layer: detection latency annotations (P99 alarm: < 5 min; Model Monitor: < 24 hours; RAGAS: < 7 days; agent traces: < 1 hour). Recovery layer: recovery time annotations (rollback: 2 min; cache: 1 sec). The stack communicates: reliability is depth of control, not a single mechanism.

**Notes:** "The layered reliability architecture is the core concept: no single control is sufficient. Evaluation gates prevent most bad models; canary deployment catches the ones that pass the gate but fail in production; automated rollback restores service quickly when the canary fails; a fallback cache bridges the rollback window; graceful degradation serves users even if all ML components are down. Each layer has a different failure mode it catches."

---

## Slide 12 — Lab 6 Final Preparation: 5 Days Out
**Layout:** Lab 6 final guidance and critical path

**Content:**
**Lab 6 Due Saturday — 5 Days: What You Should Have**

**By now (critical path):**
- [ ] Data capture enabled on churn endpoint (Part 1, Step 1) — MUST be running for 48+ hours before baseline
- [ ] Baseline job run successfully (generates statistics.json + constraints.json in S3)
- [ ] Dashboard started (Part 2) — at least 2-3 metrics panels live in CloudWatch

**This week (remaining work):**
- [ ] Monitoring schedule created (Part 1, Step 3) — schedule the daily monitoring job
- [ ] CloudWatch alarm on monitoring violation → SNS topic (connects monitoring to alerting)
- [ ] Retraining Lambda created (Part 3) — subscribe Lambda to SNS topic
- [ ] Monthly compliance report Lambda (Part 4) — most flexible; can be simplified if time is short

**Where to simplify if time is tight:**

Part 4 (compliance report) is the most flexible component. A minimum viable compliance report:
```python
# Monthly Lambda: write basic compliance metrics to S3
def generate_compliance_report(event, context):
    report = {
        'report_date': datetime.utcnow().isoformat(),
        'model_version': get_current_model_version(),
        'auc_latest': get_latest_auc_from_cloudwatch(),
        'drift_status': get_model_monitor_status(),
        'prediction_count': get_monthly_prediction_count(),
        'generated_by': 'northstar-compliance-lambda'
    }
    
    # Write to S3
    s3.put_object(
        Bucket='northstar-artifacts',
        Key=f'compliance-reports/{datetime.utcnow().strftime("%Y-%m")}.json',
        Body=json.dumps(report)
    )
```

This minimum viable report satisfies the Lab 6 requirement. The full report (PDF, stakeholder email, SHAP summary) is the extended version.

**Figure:** *Lab 6 critical path Gantt chart.* 5-day timeline (Tue-Sat). Critical path in red: Data capture → Baseline → Monitoring schedule → Alarm → Lambda. Parallel track in blue: Dashboard (can be done independently). Part 4 (compliance report) at end, labeled "simplify if needed." Weekend contingency: "Sunday morning buffer if needed." The Gantt communicates: what must be sequential vs. what can be done in parallel.

**Notes:** "The most common Lab 6 failure is getting stuck on Part 3 (retraining Lambda) because Part 1 (Model Monitor) isn't done yet. The Lambda can be tested independently of Model Monitor — write a Lambda that you can trigger manually (test event: simulated SNS message with drift notification format). Once it works manually, connect it to the SNS topic. Don't wait for Model Monitor to produce a real violation before testing the Lambda."

---

## Slide 13 — AI Reliability in Context: Real Cases
**Layout:** Real-world AI reliability failures and lessons

**Content:**
**Real AI Reliability Failures (Anonymized but Real Patterns):**

**Case 1: The Silent Scoring Failure**
A major bank's credit-scoring model went silent for 3 weeks due to a pipeline failure. Thousands of credit decisions were made on month-old scores. Impact: $12M in regulatory penalties for stale risk data.
Lesson: Prediction freshness monitoring (in the Lab 6 data pipeline health section) is a regulatory requirement for some use cases, not just a nice-to-have.

**Case 2: The Retry Storm**
A large e-commerce company's recommendation engine went down on Black Friday when the feature store was slow. The application retried failed requests with no backoff. The retry storm completely took down the feature store. The recommendation engine was dark for 4 hours during peak traffic.
Lesson: Circuit breakers and exponential backoff with retry limits are non-negotiable for production AI.

**Case 3: The Ignored Alert**
A healthcare AI system had 200+ alerts configured. On-call teams learned to filter/ignore them. A critical model drift went undetected for 6 weeks because the alert fired daily and was ignored. Patient care was affected.
Lesson: Alert fatigue kills. Fewer, higher-signal alerts. Every alert must have a documented response procedure.

**Case 4: The Missing Fallback**
A travel company's pricing AI was down for 45 minutes during an AWS region issue. The system had no fallback — it returned HTTP 500 for all pricing requests. The booking engine was completely non-functional for 45 minutes during peak booking time.
Lesson: Every AI system must have a graceful degradation path. "Pricing AI is down → no prices available" is never acceptable.

**Figure:** *Four case study cards.* Each card: company type (anonymized), failure description (2 sentences), impact (monetary or customer), and lesson learned (1 sentence). Cards formatted like incident report summaries. The "alert fatigue" card has a specific impact: "6-week undetected drift." The "missing fallback" card has a specific impact: "45 min, $2.3M in lost bookings." Real consequences make the reliability principles stick.

**Notes:** "Case 4 — the missing fallback in travel pricing — is the pattern I've seen most commonly in my experience with enterprise AI. Teams build the AI system and assume it will work. They don't build the fallback because 'we hope we'll never need it.' The reliability discipline: assume you will need the fallback; build it before the primary; test it before launch. The fallback is the safety net that lets the primary system be improved without catastrophic risk."

---

## Slide 14 — Reliability Engineering Career Perspective
**Layout:** Reliability skills and career path

**Content:**
**Why Reliability Engineering Matters for Your Career:**

**The Production Gap:**
Most computer science graduates (and many data scientists) can build AI models. Very few can build AI systems that are reliable in production. This gap is widening — AI deployment is accelerating faster than AI operations maturity.

**What Reliability Engineering Means for ML Career Paths:**

**ML Engineer (what this course trains you to do):** Builds and deploys models. Understands reliability as a design constraint. Implements basic monitoring, CI/CD, and fallback patterns.

**ML Reliability Engineer / AI Platform Engineer:** Specializes in reliability of AI systems. Builds the platform that other ML engineers deploy to. Deep expertise in SRE applied to AI. High demand, premium salary.

**ML Lead / Principal ML Engineer:** Sets reliability standards for the team. Designs SLAs. Reviews failure mode analyses. Makes build-versus-buy decisions for reliability infrastructure.

**The skills this course gives you:**
- Failure mode analysis and mitigation design
- SLA design from business requirements
- Error budget tracking and reliability investment decisions
- Circuit breaker, fallback cache, and graceful degradation patterns
- Chaos engineering methodology
- Monitoring and observability architecture

**These skills are rare.** The ML engineer who says "I built a production AI platform with 99.9% availability, automated rollback, and graceful degradation" is in the top 10% of candidates in most AI hiring pools.

**Figure:** *Career path diagram.* Three roles (ML Engineer, ML Reliability Engineer, ML Lead) with salary ranges and demand growth rates (2026). ML Reliability Engineer: highest growth in demand (45% YoY). Skill overlap diagram showing: all three roles need this lecture's content; the Reliability Engineer role goes deeper; the ML Lead role adds business/leadership. The diagram communicates: reliability skills differentiate you in the market.

**Notes:** "I want to be direct: the reliability engineering content in this lecture — SLAs, error budgets, fallback patterns, circuit breakers — is what makes the difference between a junior ML engineer who trains models and a senior ML engineer who builds production systems. Build the habit now of thinking about failure modes before building the happy path. It will define your career trajectory."

---

## Slide 15 — Key Takeaways + What's Next
**Layout:** Takeaways + L23 preview

**Content:**
**Key Takeaways:**
1. Reliability is designed, not hoped for: enumerate failure modes before launch, design recovery for each, and test the recovery procedures — not during incidents
2. Graceful degradation is a hierarchy: real-time AI → stale cache → segment-based → rule-based → generic; design and test each level; the fallback must be ready before the primary launches
3. Circuit breakers prevent cascading failures: when a component degrades, open the circuit and serve fallback immediately — don't let retry storms amplify a partial failure into a total outage
4. Error budgets make reliability decisions objective: when < 50% budget remains, freeze risky changes; when exhausted, declare an incident and prioritize reliability work over new features
5. Chaos engineering validates your assumptions: deliberately inject failures to verify that fallbacks, rollbacks, and circuit breakers work before an unplanned incident proves they don't

**Next Session (Thu Nov 19):**
- Topic: AI Economics — the full cost model for enterprise AI; ROI framework; FinOps for AI
- Reading due: *AI Economics* — "Cost Model" through "ROI Frameworks"
- Lab 6 due Saturday — 5 days — are you on the critical path?
- **Lab 7 assigned Thursday** — Economics and Business Value (the final lab)

**Figure:** *Five-takeaway summary card.* Lab 6 countdown (5 days, red). Lab 7 preview: "Assigned Thursday — the final lab, focuses on economic analysis and business value." Reliability stack diagram thumbnail.

**Notes:** "Lab 6 is due Saturday. If you haven't enabled data capture yet, that's tonight's task. If you have data capture running and the baseline created, focus on the monitoring schedule and alarm (the critical path). After Lab 6 comes Lab 7 — the economics lab. Thursday's lecture (AI Economics) is direct preparation for Lab 7. Come to Thursday's class with an idea of what your cost and value numbers look like for NorthStar."
