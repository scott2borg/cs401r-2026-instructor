---
lecture: L14
title: Continuous Delivery I — Deployment Patterns
date: Tuesday, October 20, 2026
week: 8
arc: Build
reading_due: "Continuous Delivery for AI — Introduction through Deployment Patterns"
lab_due: "Lab 4 due Sat Oct 31"
slides_target: 16
---

# L14: Continuous Delivery I — Deployment Patterns
**Tuesday, October 20, 2026 | CS 401R: Engineering Production AI Systems | Fall 2026**

> Every AI system eventually meets its deployment moment. How you deploy determines how much risk you carry, how quickly you can recover, and whether your users experience the transition. Learn the patterns that let you deploy with confidence.

**Reading Due:** *Continuous Delivery for AI* — "Introduction" through "Deployment Patterns"
**Lab 4 Due:** Sat Oct 31 (11 days)

---

## Slide 1 — Title
**Layout:** Left dark panel + right canary deployment diagram

**Content:**
- Continuous Delivery I: Deployment Patterns
- CS 401R · Lecture 14 · Tuesday, October 20, 2026
- From "It Works on My Machine" to "It's Running in Production"

**Figure:** *Canary deployment diagram.* Traffic flowing in from the left, hitting a traffic splitter, with 95% routing to "Production v2.3" (large box, solid) and 5% routing to "Canary v3.0" (smaller box, dashed border). Both pointing to the same downstream (Response to User). Metrics panel on the right, showing Canary latency (green), Canary error rate (green), and Canary prediction quality (green). "Canary healthy → expand to 20%" action at bottom. The diagram communicates that canary deployment is a controlled, measurable risk exposure.

**Notes:** "The deployment moment is where months of AISDLC work either succeed or fail in front of real users. Today we cover deployment patterns that protect you when something goes wrong — because something always does. Thursday we cover the infrastructure and automation that makes those patterns practical."

---

## Slide 2 — The Deployment Problem: Why It's Different for AI
**Layout:** AI deployment challenges vs. traditional software deployment

**Content:**
**Why AI Deployment Is Harder Than Web App Deployment:**

**Traditional web app:** Ship new code → same logic runs → users see updated UI → if broken, rollback is instant.

**AI system deployment complexity:**
1. **Model artifact + code must stay in sync:** A model artifact is separate from serving code. Mismatched versions cause silent failures.
2. **Performance is probabilistic:** A new model might perform worse on production distribution even if it passed offline evaluation. No way to know until production traffic hits it.
3. **Rollback is not free:** Rolling back to a previous model may require re-serving a large artifact and warming up a cold endpoint.
4. **Business outcomes are delayed:** For churn, the "outcome" (did the intervention work?) won't be known for 4-8 weeks after deployment.
5. **Multiple coupled components:** Deploying a new churn model while also updating the feature engineering pipeline creates compound risk. Deploy components independently.

**The deployment risk matrix:**
- Low risk: Code change with no model change (serving code update)
- Medium risk: Model update with unchanged features
- High risk: Feature change + model update simultaneously
- Extreme risk: Feature change + model update + RAG index update + agent configuration change

**Figure:** *AI deployment risk matrix.* 2×2 matrix: x-axis: "Model Change?" (No/Yes), y-axis: "Feature/Prompt/Index Change?" (No/Yes). Four quadrants: No/No (Low: code update only), Yes/No (Medium: model retraining), No/Yes (Medium: data/prompt changes), Yes/Yes (High: compound changes). Examples in each quadrant from NorthStar. "Never do High risk all at once" label on the Yes/Yes quadrant.

**Notes:** "The compound risk quadrant is where production incidents live. Teams that combine a model update with a feature store schema change in the same deployment are setting themselves up for a difficult debugging session. When something fails, they can't tell whether it's the model change, the feature change, or their interaction. Deploy one thing at a time."

---

## Slide 3 — Deployment Patterns Taxonomy
**Layout:** Six deployment patterns with risk/complexity comparison

**Content:**
**The Six Deployment Patterns for AI Systems:**

| Pattern | Risk | Complexity | When to Use |
|---------|------|-----------|------------|
| **Big Bang (replace-all)** | High | Low | Never for production AI |
| **Blue/Green** | Medium | Medium | Major model architecture changes |
| **Canary** | Low-Medium | Medium | Standard model updates |
| **Shadow** | Lowest | Medium | Validating before any user exposure |
| **Feature Flag** | Low | High | Gradual user group rollouts |
| **A/B** | Low-Medium | High | Comparing model variants on business metrics |

**NorthStar deployment pattern selection:**
- Routine churn model update: **Canary** (10% → 30% → 100% over 3 days if metrics stable)
- Major model architecture change (XGBoost → LightGBM): **Shadow** first, then **Blue/Green**
- New customer segment rollout: **Feature Flag** (enable for premium segment first)
- Model comparison experiment: **A/B** (over 4-week window)

**General recommendation for enterprise AI:**
- Default to Canary for all model updates
- Use Shadow before exposing any traffic to an untested major change
- Avoid Big Bang for any production AI system regardless of urgency

**Figure:** *Six-pattern risk/complexity scatter plot.* X-axis: Deployment Complexity (Low to High). Y-axis: User Risk Exposure (Low to High). Six labeled dots: Big Bang (high risk, low complexity), Blue/Green (medium risk, medium complexity), Canary (low-medium risk, medium complexity), Shadow (lowest risk, medium complexity), Feature Flag (low risk, high complexity), A/B (medium risk, high complexity). "Recommended zone" circle around Canary and Shadow. The scatter plot communicates: the optimal patterns are not the simplest ones.

**Notes:** "Why do teams use Big Bang deploys despite the high risk? Because it's the simplest to implement. 'Stop the old container, start the new one' is three commands. Canary is a significant engineering investment. But the asymmetry of outcomes — 5 minutes of Big Bang savings vs. 8 hours of Big Bang incident response — makes the engineering investment in Canary worthwhile every time."

---

## Slide 4 — Canary Deployment Deep Dive
**Layout:** Canary deployment mechanics with NorthStar implementation

**Content:**
**Canary Deployment: Controlled Exposure with Fast Rollback**

**How it works:**
1. New model version deployed to a small traffic slice (canary group)
2. Canary group monitored for: error rate, latency, prediction quality, business metrics
3. If canary is healthy over the observation window → expand traffic to next slice
4. If canary shows anomalies → immediate automatic rollback to previous version

**NorthStar Churn Endpoint Canary Configuration (SageMaker):**
```python
endpoint_config = {
    "EndpointConfigName": "northstar-churn-canary-config",
    "ProductionVariants": [
        {
            "VariantName": "Production-v2-3",
            "ModelName": "northstar-churn-v2-3",
            "InitialVariantWeight": 9,  # 90% traffic
            "InstanceType": "ml.m5.large",
            "InitialInstanceCount": 2
        },
        {
            "VariantName": "Canary-v3-0",
            "ModelName": "northstar-churn-v3-0",
            "InitialVariantWeight": 1,  # 10% traffic
            "InstanceType": "ml.m5.large",
            "InitialInstanceCount": 1
        }
    ]
}
```

**Canary progression schedule for NorthStar:**
- Day 0: 90/10 split (10% canary) — observe for 24h
- Day 1: 70/30 split (30% canary) — observe for 24h
- Day 2: 50/50 split — observe for 24h
- Day 3: 100% canary (v3.0 becomes production) — archive v2.3

**Canary monitoring criteria (automated check every 15 min):**
- Error rate: canary error rate ≤ production error rate × 1.1 (within 10%)
- Latency: canary P99 ≤ production P99 × 1.2 (within 20%)
- Prediction distribution: PSI between canary and production predictions < 0.15

**Figure:** *Canary progression timeline.* Four-panel horizontal timeline: Day 0 (90/10), Day 1 (70/30), Day 2 (50/50), Day 3 (100%). Each panel shows: traffic split pie chart, monitoring metrics (all green), decision (advance/hold/rollback). Rollback arrow shown going from Day 1 back to Day 0 with annotation "Auto-rollback if error rate spikes." The timeline communicates: canary is a measured, multi-day process.

**Notes:** "The 24-hour observation window at each step is important for AI systems. For a web app, you might advance the canary every 15 minutes. For a churn model, the 'interesting' prediction patterns don't manifest in 15 minutes — they emerge over a full day's worth of diverse customer requests. A 24-hour window gives you statistical confidence before advancing."

---

## Slide 5 — Blue/Green Deployment for AI
**Layout:** Blue/green pattern with instant rollback mechanics

**Content:**
**Blue/Green Deployment: Two Full Environments**

In blue/green, two complete, identical deployment environments exist simultaneously:
- **Blue:** Current production (serving all live traffic)
- **Green:** New version (deployed, tested, ready, but receiving no traffic)

**Switch:** When ready, route 100% of traffic from Blue to Green. Blue remains active for instant rollback.

**NorthStar Blue/Green for Major Releases:**
```
Traffic Router
    |
    ├── Blue: SageMaker Endpoint "northstar-churn-blue"
    │         Model: v2.3, Instances: 2× ml.m5.large
    │         Status: LIVE (100% traffic)
    │
    └── Green: SageMaker Endpoint "northstar-churn-green"
              Model: v3.0, Instances: 2× ml.m5.large
              Status: WARM (0% traffic, passing smoke tests)
```

**Blue/Green switch (Lambda function):**
```python
def switch_blue_to_green(event, context):
    """Atomic traffic switch from blue to green."""
    sagemaker = boto3.client('sagemaker')
    
    # Verify green endpoint is healthy before switching
    green_status = check_endpoint_health('northstar-churn-green')
    if not green_status['healthy']:
        raise Exception(f"Green endpoint not healthy: {green_status}")
    
    # Update API Gateway or ALB to route to green
    update_routing_rule(from='northstar-churn-blue', to='northstar-churn-green')
    
    # Log the switch for audit trail
    log_deployment_event('blue-green-switch', old='v2.3', new='v3.0')
```

**Rollback is instantaneous:** Call `switch_blue_to_green()` again in reverse. No new deployment, no cold start, no delay.

**Cost:** Running two full endpoints doubles infrastructure cost during the transition window. Acceptable for planned releases; too expensive for always-on operation.

**Figure:** *Blue/green architecture diagram.* Traffic Router in the center with two arrows: one pointing left to "Blue" endpoint box (green/active border, "LIVE" badge), one pointing right to "Green" endpoint box (dashed border, "READY" badge). Switch arrow below the router: "Traffic switch (atomic, < 1s)." Rollback arrow: reverse direction, "Instant rollback." Cost annotation: "Cost: 2× endpoint hours during transition." Comparison to canary: "canary = days; blue/green = seconds."

**Notes:** "Blue/green is the right pattern when you need instantaneous rollback and the cost of running two endpoints for a few hours is acceptable. For a SageMaker ml.m5.large endpoint, that's roughly $0.30/hour × 2 hours = $0.60. That's nothing for a major release. Use canary for routine model updates; blue/green for major architecture changes where you want instant rollback if something breaks."

---

## Slide 6 — Feature Flag Deployment for AI
**Layout:** Feature flag pattern for gradual user rollouts

**Content:**
**Feature Flags in AI Systems: Controlled User-Group Rollouts**

Feature flags allow you to deploy code to production but control which users see new behavior — independently of deployment.

**NorthStar Use Case:** The new offer generation system (v2.0 with improved RAG) is ready, but you want to roll it out to premium customers first before all segments.

```python
# Feature flag check in the offer generation service
def generate_customer_offer(customer_id: str, customer_data: dict) -> str:
    
    # Check feature flag for this customer
    flag_service = boto3.client('appconfig')
    flags = get_feature_flags(customer_id)
    
    if flags.get('use_rag_offer_v2', False):
        # New RAG-based offer generation
        return generate_rag_offer_v2(customer_data)
    else:
        # Legacy rule-based offers
        return generate_rule_based_offer(customer_data)
```

**NorthStar Feature Flag Rollout Plan (Offer Generation v2):**
```yaml
# AWS AppConfig feature flag configuration
northstar-offer-v2:
  enabled: true
  targeting:
    - rule: customer_segment == "Premium"
      percentage: 100  # All premium customers
    - rule: customer_segment == "High-Value"
      percentage: 25   # 25% of high-value customers
    - rule: default
      percentage: 0    # All others: still on v1
```

**AWS AppConfig:** Managed feature flag service; integrates with Lambda; supports gradual rollouts, emergency kill switches, and targeting rules.

**Figure:** *Feature flag rollout diagram.* Customer request arrives with customer_id. Feature Flag Service evaluates: "Is this customer in the rollout group?" Premium: YES → v2 offer system. High-Value + lucky 25%: YES → v2. Others: NO → v1. Both paths serve a response. Rollout percentage dial on the right: starts at 0%, then moves to Premium (100%) → HV (25%) → HV (100%) → All (100%). The dial communicates: gradual, controllable rollout.

**Notes:** "Feature flags are powerful but add operational complexity. Every flag that stays enabled long-term becomes a potential source of confusion — 'is this behavior for all users or just flagged users?' Establish a discipline: feature flags are temporary scaffolding for rollouts, not permanent configuration. Once rollout is complete (or abandoned), remove the flag and clean up the code path."

---

## Slide 7 — Deployment Health Gates: Automated Promotion and Rollback
**Layout:** Automated health gate logic for canary progression

**Content:**
**The Deployment Health Gate: Automate the Decision**

Manual monitoring of a canary deployment requires someone to watch the dashboards. Automated health gates make the decision for you.

**NorthStar Canary Health Gate (CloudWatch Alarms + Lambda):**

```python
# Lambda function: triggered every 15 minutes during canary deployment
def check_canary_health(event, context):
    cw = boto3.client('cloudwatch')
    
    # Get metrics for canary and production variants
    canary_error_rate = get_metric('CanaryVariant', 'ModelLatencyErrorRate', minutes=60)
    prod_error_rate = get_metric('ProductionVariant', 'ModelLatencyErrorRate', minutes=60)
    
    canary_p99_latency = get_metric('CanaryVariant', 'ModelLatencyP99', minutes=60)
    prod_p99_latency = get_metric('ProductionVariant', 'ModelLatencyP99', minutes=60)
    
    # Health gate criteria
    error_rate_ok = canary_error_rate <= prod_error_rate * 1.1
    latency_ok = canary_p99_latency <= prod_p99_latency * 1.2
    
    if error_rate_ok and latency_ok:
        print(f"Canary HEALTHY — advancing deployment")
        advance_canary_traffic()  # 10% → 30% → 50% → 100%
    else:
        print(f"Canary UNHEALTHY — rolling back")
        rollback_canary()  # Set canary traffic to 0%
        send_alert(f"Canary rollback triggered: error_rate={canary_error_rate:.3f}")
```

**Gate criteria hierarchy:**
1. **Hard failure gate:** Triggers immediate rollback (error rate > 5%, P99 latency > 2× production)
2. **Soft warning gate:** Pauses advancement, alerts on-call (error rate 1.5-5%, latency 1.5-2×)
3. **Healthy gate:** Advances to next traffic slice (all metrics within bounds)

**Figure:** *Canary health gate flowchart.* Scheduled Lambda (every 15 min) → check metrics → three branches: Hard failure (red, immediate rollback + alert), Soft warning (amber, pause + alert), Healthy (green, advance to next percentage). The health gate check shows: metrics comparison with thresholds, decision, and action. This is the automation that makes canary practical.

**Notes:** "The immediate rollback on hard failure is non-negotiable. Don't make the on-call engineer look at a dashboard and decide whether to roll back at 2 am. If the hard failure criteria are met, the system rolls back automatically, and the engineer wakes up to a notification that says 'Canary rolled back at 02:14 am — error rate was 8.3% vs. production 0.4%.' The engineer can investigate in the morning."

---

## Slide 8 — Deployment for LLM Systems: Prompt Deployment
**Layout:** Prompt deployment patterns for RAG systems

**Content:**
**Deploying Prompt Changes: Different from Model Deployment**

When you update a prompt template for the RAG system, the deployment is:
- **No artifact to copy:** The prompt template is just text, stored in Git and served from a parameter store
- **Instant switch:** Prompt change takes effect on the next invocation
- **Rollback is easy:** Roll back to the previous Git commit, redeploy the parameter
- **Risk is still real:** A bad prompt change will instantly affect 100% of users unless you implement a flag

**NorthStar Prompt Deployment Architecture:**
```
AWS Systems Manager Parameter Store:
  /northstar/offer-generation/prompt/active-version → "v3.2"
  /northstar/offer-generation/prompt/v3.2 → [prompt text]
  /northstar/offer-generation/prompt/v3.1 → [previous prompt text]
```

```python
# Offer generation service: reads active prompt version from Parameter Store
def get_active_prompt() -> str:
    ssm = boto3.client('ssm')
    active_version = ssm.get_parameter(
        Name='/northstar/offer-generation/prompt/active-version'
    )['Parameter']['Value']
    
    prompt = ssm.get_parameter(
        Name=f'/northstar/offer-generation/prompt/{active_version}'
    )['Parameter']['Value']
    
    return prompt

# Rollback: change the active-version pointer to v3.1
# Takes effect on next invocation — no restart required
```

**Prompt canary (feature flag approach):**
- Route 10% of requests to new prompt version; 90% to current
- Monitor RAGAS faithfulness score for both groups in CloudWatch
- Auto-promote or auto-rollback based on faithfulness gate

**Figure:** *Prompt deployment architecture diagram.* Parameter Store at center with active-version pointer. Offer generation service reads active version → fetches prompt → invokes Bedrock. Rollback: change the active-version pointer (single-parameter update). Prompt canary: 10% of requests use v3.2; 90% use v3.1; RAGAS evaluation running on both groups. The diagram communicates: prompt deployment is simpler than model deployment but still requires gates and rollback mechanisms.

**Notes:** "Storing prompts in AWS Systems Manager Parameter Store instead of hardcoding them in the application has a major operational advantage: you can change the prompt without redeploying the application. This is the prompt management equivalent of environment variables. The application reads the prompt at request time, so a parameter update takes effect instantly on the next request."

---

## Slide 9 — Deployment for RAG Index Updates
**Layout:** RAG index update deployment with zero-downtime strategy

**Content:**
**The RAG Index Update Problem:**

Updating the Bedrock Knowledge Base index is not instantaneous — it takes 30-60 minutes to re-index the full corpus. During that time:
- Option A: Serve from the old index (stale content) — acceptable for most cases
- Option B: Take the system offline — unacceptable for production
- Option C: Use two indexes and switch (blue/green for indexes) — the right approach for critical updates

**NorthStar Blue/Green Index Strategy:**

```python
class RAGIndexManager:
    def __init__(self):
        self.active_kb_id = get_parameter('/northstar/rag/active-kb-id')
        self.staging_kb_id = get_parameter('/northstar/rag/staging-kb-id')
    
    def deploy_new_index(self, new_documents: list):
        """Zero-downtime index update using blue/green."""
        # 1. Sync new documents to staging Knowledge Base
        sync_documents_to_kb(self.staging_kb_id, new_documents)
        
        # 2. Wait for staging sync to complete
        wait_for_sync(self.staging_kb_id)
        
        # 3. Run smoke tests on staging KB
        smoke_test_results = test_kb_retrieval(self.staging_kb_id, TEST_QUERIES)
        if not all(r['relevant'] for r in smoke_test_results):
            raise Exception("Staging KB smoke tests failed — aborting deploy")
        
        # 4. Atomic switch: staging → active
        old_active = self.active_kb_id
        set_parameter('/northstar/rag/active-kb-id', self.staging_kb_id)
        set_parameter('/northstar/rag/staging-kb-id', old_active)
        
        # 5. Rollback: if issues detected, switch back
        # (old active is now 'staging' and available for instant rollback)
```

**Figure:** *Blue/green RAG index diagram.* Two Bedrock Knowledge Base boxes: "Active KB (v7)" and "Staging KB (v8, syncing)." Offer generation service → active KB (100% traffic). Sync process: S3 new docs → Staging KB (background, 30-45 min). Smoke test → if pass, swap pointers. After swap: "Active KB (v8)" → Staging KB (old v7, available for rollback). Zero downtime indicated throughout.

**Notes:** "The key to zero-downtime index updates is the pointer swap pattern. You never take the active index offline — you build the new index in staging, test it, then atomically switch the pointer. The 'old active' becomes the new 'staging' — it's now your rollback target. This pattern works for any large artifact that takes time to build and can't be updated in-place."

---

## Slide 10 — Deployment Strategy for NorthStar: The Full Picture
**Layout:** Deployment strategy summary for all three NorthStar AI systems

**Content:**
**NorthStar Deployment Strategy Matrix:**

| System | Routine Update | Major Change | Emergency |
|--------|----------------|-------------|-----------|
| **Churn Model** | Canary (10→30→100%) | Shadow + Blue/Green | Rollback to registry version |
| **Offer Gen (prompt)** | Prompt canary (10% flag) | Full RAGAS eval + prompt canary | Rollback pointer in 30 seconds |
| **Offer Gen (RAG index)** | Blue/Green index swap | Blue/Green index swap + A/B | Rollback pointer in 30 seconds |
| **Customer Service Agent** | Shadow mode first, then canary | Shadow + HITL review + canary | Agent alias rollback |

**Decision criteria for deployment pattern selection:**
1. How reversible is this change if something goes wrong? (reversibility determines pattern)
2. How long does the observation window need to be? (determines canary duration)
3. What's the blast radius if the new version is wrong? (determines initial traffic %)
4. Are there downstream systems that need to be aware of this change? (determines coordination requirements)

**Figure:** *Deployment decision tree.* Root question: "Is this a routine update or major change?" → branches. "Routine" → "How reversible?" → "Easy (prompt/index): Pointer swap with canary." "Moderate (model weights): Canary deployment." "Hard (architecture change): Shadow first." "Major change" branch → "Shadow mode → evaluate → Blue/Green → Canary to 100%." Emergency branch: immediate rollback to last known good version. Clean decision tree logic.

**Notes:** "Notice that Shadow mode appears as a step in the 'major change' path, not as a standalone deployment pattern. Shadow is a *pre-deployment evaluation technique* — it tells you whether the new version is safe before you expose any users. Canary is the actual deployment pattern — it controls the traffic exposure. Major changes use both: shadow first to validate, then canary to deploy."

---

## Slide 11 — Deployment Readiness Checklist
**Layout:** Pre-deployment checklist for NorthStar releases

**Content:**
**Before You Deploy to Production:**

**Model Release Checklist:**
- [ ] Evaluation report complete and gate passed (AUC ≥ 0.72, all segments)
- [ ] Shadow mode run complete (≥ 24 hours, metrics acceptable)
- [ ] Model registered in Model Registry with all required metadata
- [ ] Rollback version identified and tested
- [ ] CloudWatch canary monitoring configured (alarms active)
- [ ] On-call engineer notified of deployment window
- [ ] Database/Feature Store migration (if any) verified
- [ ] Smoke test ready to run post-deployment

**Prompt/Index Release Checklist:**
- [ ] RAGAS evaluation passed on test set
- [ ] Staging Knowledge Base smoke tested with representative queries
- [ ] Parameter Store pointing to correct version
- [ ] Rollback procedure verified (can switch back in < 1 minute)
- [ ] Monitoring dashboard open during deployment window

**The "Don't Deploy Friday" Rule:**
Don't deploy production AI systems on Fridays (or before a holiday weekend). If something goes wrong, you need the full team available to respond — not a skeleton crew from a hotel room.

**Figure:** *Deployment readiness checklist card.* Two-section checklist card: "Model Release" (8 items) and "Prompt/Index Release" (5 items). All items shown unchecked. "DON'T DEPLOY FRIDAY" rule shown in red at the bottom with a calendar showing Friday highlighted. Clean, printable format. The checklist communicates: deployment is a process, not a button push.

**Notes:** "The 'Don't Deploy Friday' rule has been around in software engineering for decades, but it's especially important for AI systems because the feedback loop is slower. A website bug appears in the error logs within minutes. A model quality issue might not surface in business metrics until the following week. Deploy Tuesday or Wednesday — you have the full week to monitor and respond."

---

## Slide 12 — Deployment Incident: What Good Rollback Looks Like
**Layout:** Rollback incident timeline with decision points

**Content:**
**Case Study: NorthStar Churn Model Canary Rollback (Hypothetical)**

**Scenario:** v3.0 canary deployed at 10% traffic at 09:00 on a Tuesday. At 09:47, the automated health gate detects an elevated error rate.

**Incident Timeline:**
- 09:00 — Canary v3.0 deployed at 10% traffic (90/10 split)
- 09:15 — Metrics check: all green ✅
- 09:30 — Metrics check: all green ✅
- 09:45 — Metrics check: Error rate rising (canary: 3.2%, production: 0.3%)
- 09:47 — Hard failure gate triggered: error rate exceeds 10× production
- 09:47 — **Automatic rollback initiated:** canary traffic set to 0%
- 09:47 — **Alert fired:** on-call engineer receives PagerDuty alert
- 09:48 — All traffic back on production v2.3
- 09:52 — On-call engineer acknowledges; begins root cause analysis
- 10:15 — Root cause identified: v3.0 training included a deprecated feature that fails when the feature is missing in production
- 10:30 — Fix developed; v3.1 candidate built
- Nov 2 — v3.1 passes evaluation gate; canary deployment begins

**Key observations:**
- Blast radius: 47 minutes of 10% traffic → ~4-5% of total user impact before rollback
- Rollback time: 1 minute from detection to full rollback
- Resolution time: 2.5 weeks (retrain required)
- User-facing error window: < 2 minutes (most requests during that window served by v2.3)

**Figure:** *Incident timeline diagram.* Horizontal timeline from 09:00 to 10:30. Key events marked. Between 09:45-09:48: red zone "Canary error spike detected + rollback." After 09:48: green zone "Production v2.3 100% traffic." Error rate graph overlaid on the timeline: production flat at 0.3%, canary spikes to 3.2%, then canary is removed. The diagram communicates that the automated rollback limited the user impact to a 3-minute window.

**Notes:** "The 47-minute period before rollback was not wasted — the automated health gate caught the problem on the 3rd 15-minute check cycle. With Big Bang deployment, this error would have hit 100% of traffic at 09:00 with no automatic rollback. With canary, 90% of traffic was always on the safe version. That's the concrete value of the canary pattern."

---

## Slide 13 — Deployment and AISDLC: Stage 7 in Detail
**Layout:** AISDLC Stage 7 (Deploy) artifacts and gate

**Content:**
**AISDLC Stage 7 — Deploy: What It Encompasses**

Stage 7 is not a single moment — it's a multi-step process:

**Stage 7 artifacts:**
1. **Deployment plan:** Which pattern (canary/blue-green), traffic schedule, monitoring setup, rollback procedure
2. **Smoke test results:** Endpoint health check post-deployment; 10 representative prediction requests verified
3. **Canary health log:** Metrics captured at each traffic increment; gate pass/fail at each step
4. **Deployment record:** Formal record of what was deployed, when, by whom, to which environment
5. **Rollback procedure:** Documented and tested (you must test rollback before the first deployment)

**Stage 7 gate:** Deployment approved for full traffic when:
- Canary has been at each traffic level for the required observation window
- All canary health gate checks have passed
- Business metrics (if measurable in the window) are acceptable
- Rollback procedure verified

**Connection to Stage 8 (Monitor):**
Stage 7 ends when full traffic is on the new version. Stage 8 begins immediately. The deployment doesn't "complete" — it transitions to ongoing monitoring.

**Figure:** *AISDLC Stage 7 detail diagram.* Stage 7 box expanded to show internal steps: Deployment Plan → Pre-Deploy Checks → Canary Start (10%) → Health Gate → Traffic Advance → Health Gate → Traffic Advance → Full Rollout → Stage 7 Gate → Stage 8 (Monitor). Return loops shown: from Health Gate "FAIL" back to "Rollback and Investigate." The diagram shows Stage 7 is a process with gates and return loops, not a single action.

**Notes:** "The rollback procedure must be documented and tested before the first production deployment. You do not want to be reading documentation for the first time during an incident at 2 am. Run a dry rollback in staging: deploy v3.0, rollback to v2.3, verify traffic is back on v2.3. The rollback drill takes 30 minutes and gives you confidence that the rollback works when you need it."

---

## Slide 14 — Lab 5 Preview: What You'll Deploy
**Layout:** Lab 5 deployment scope overview

**Content:**
**Lab 5: Deployment & Scaling (Assigned Thu Oct 29 | Due Sat Nov 14)**

**Lab 5 builds on Lab 4 (CI/CD Pipeline) by adding deployment patterns:**

**Deliverable 1: Canary deployment for Churn Model**
- SageMaker endpoint with two production variants (Production + Canary)
- Lambda health gate (checks every 15 min during canary window)
- Automated rollback on hard failure criteria

**Deliverable 2: RAG system deployment (if doing Option A)**
- Blue/Green Knowledge Base deployment
- Parameter Store pointer management
- Smoke test suite for Knowledge Base validation

**Deliverable 3: Agent deployment (if doing Option B)**
- Bedrock Agent versioning and alias management
- Agent canary deployment via alias traffic routing
- Trace-based health gate for agent quality

**Deliverable 4: Deployment runbook**
- Documented deployment procedure
- Rollback procedure (tested)
- Emergency contact and escalation path

**Figure:** *Lab 5 architecture preview.* Three-lane diagram: Churn (canary endpoint), RAG (blue/green KB), Agent (alias-based canary). Each lane shows the current version (blue), the new version (green/canary), traffic percentage, and health gate lambda. The full NorthStar deployment architecture in a single diagram. Lab 5 is the lab that connects to this architecture.

**Notes:** "Lab 5 is assigned Thursday. The canary deployment component builds directly on Lab 4's CodePipeline — instead of deploying directly to the endpoint, the Lab 5 pipeline deploys to the canary variant first, runs the health gate, and only promotes to full traffic if the gate passes. You're not replacing Lab 4; you're extending it."

---

## Slide 15 — Deployment Metrics: What to Track
**Layout:** Deployment metrics framework for NorthStar

**Content:**
**Measuring Deployment Quality:**

**Deployment frequency:** How often do you successfully deploy to production?
- Industry benchmark (DORA Elite): on-demand, multiple per week
- NorthStar target: bi-weekly model updates, weekly prompt/index updates
- NorthStar current state: monthly (manual deployments) → target: bi-weekly with CI/CD

**Lead time for changes:** From code commit to production deployment. Measures velocity.
- NorthStar target (model): ≤ 5 days (train → evaluate → 3-day canary → full)
- NorthStar target (prompt): ≤ 1 day (evaluate → 1-hour canary → full)

**Change failure rate:** % of deployments that result in a rollback or incident.
- Target: < 15% for model deployments; < 5% for prompt deployments

**MTTR (Mean Time to Restore):** How quickly can you recover from a failed deployment?
- Target: < 15 minutes (with automated rollback)
- Current state (manual): 2-4 hours

**These are the DORA metrics adapted for AI systems.** DORA (DevOps Research and Assessment) is the industry standard for measuring deployment health.

**Figure:** *DORA metrics dashboard for NorthStar.* Four metric gauges: Deployment Frequency (current vs. target), Lead Time (days, current vs. target), Change Failure Rate (%, current: 30% / target: 15%), MTTR (hours, current: 3h / target: 15min). Arrow from "current state" to "target state" for each metric. Lab 4 and Lab 5 impact shown: which lab closes which gap.

**Notes:** "DORA metrics are how your future engineering leadership will measure deployment performance. 'Elite' DORA performance (by DORA's research) correlates with lower incident rates, higher team satisfaction, and better business outcomes. When you're building CI/CD pipelines and canary deployment in these labs, you're building the infrastructure that moves an organization from Low to Medium to Elite DORA performance."

---

## Slide 16 — Key Takeaways + What's Next
**Layout:** Takeaways + L15 preview

**Content:**
**Key Takeaways:**
1. AI deployment patterns are chosen based on risk and reversibility: Canary for routine updates, Blue/Green for major changes, Shadow for pre-deployment validation, Feature Flags for user-group rollouts
2. Automated health gates make canary deployments practical: automated monitoring + automatic rollback eliminates the need for 24/7 human monitoring during canary windows
3. Prompts and RAG indexes are deployed differently from model weights but still require gates, rollback procedures, and monitoring
4. The deployment readiness checklist is not bureaucracy — it's the difference between a smooth deployment and a 2 am incident
5. DORA metrics (deployment frequency, lead time, change failure rate, MTTR) measure deployment quality — aim for Elite performance

**Next Session (Thu Oct 22):**
- Topic: Continuous Delivery II — deployment infrastructure; scaling; multi-region; Lab 5 deep dive
- Reading due: *Continuous Delivery for AI* — "Infrastructure" through "Key Takeaways"
- Lab 4 due in 9 days — where are you?

**Figure:** *Five-takeaway summary card.* Lab 4 countdown (9 days) in amber. Lab 5 preview: "Assigned Thursday — start thinking about canary deployment architecture now."

**Notes:** Quick Lab 4 check-in: "Who has a working SageMaker Pipeline that runs end-to-end?" If fewer than half have this, extend office hours immediately. The SageMaker Pipeline is the critical path for Lab 4. Without a working pipeline, nothing else in Lab 4 connects. Students who are stuck on the pipeline at this point need urgent support.
