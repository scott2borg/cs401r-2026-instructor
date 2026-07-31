---
lecture: L21
title: Monitoring, Observability & Model Lifecycle Management
date: Thursday, November 12, 2026
week: 11
arc: Operate
reading_due: "Operating AI Systems — Monitoring Architecture through Lifecycle Management"
lab_due: "Lab 5 due Sat Nov 14 (2 days); Lab 6 due Sat Nov 22 (10 days)"
slides_target: 16
---

# L21: Monitoring, Observability & Model Lifecycle Management
**Thursday, November 12, 2026 | CS 401R: Engineering Production AI Systems | Fall 2026**

> Monitoring tells you something is wrong. Observability tells you why. The difference is the difference between a smoke alarm and a fire inspector. Both matter — but only one helps you fix the problem.

**Reading Due:** *Operating AI Systems* — "Monitoring Architecture" through "Lifecycle Management"
**Lab 5 Due:** Sat Nov 14 (2 days)
**Lab 6 Due:** Sat Nov 22 (10 days)

---

## Slide 1 — Title
**Layout:** Left dark panel + right monitoring vs. observability contrast

**Content:**
- Monitoring, Observability & Model Lifecycle Management
- CS 401R · Lecture 21 · Thursday, November 12, 2026
- From Knowing Something Is Wrong to Knowing Why

**Figure:** *Monitoring vs. observability contrast.* Split visual. Left side (Monitoring): CloudWatch alarm dashboard with red alert: "Churn endpoint error rate 8.3% — THRESHOLD EXCEEDED." One-line notification. Right side (Observability): CloudWatch Logs Insights query results showing the root cause: a specific exception type (NullPointerException on feature 'category_diversity_score'), request payload excerpt, stack trace, model version, and timestamp. The contrast is stark: monitoring gives you the what; observability gives you the why.

**Notes:** "The monitoring/observability distinction is not semantic — it's the difference between knowing your system is failing and knowing how to fix it. 'Error rate is 8.3%' tells you nothing actionable. 'Feature category_diversity_score is returning null for 12% of requests because the Glue ETL job failed yesterday and didn't backfill the missing values' is actionable. Building observability is more expensive than monitoring — but it's what makes your on-call shift survivable."

---

## Slide 2 — The Three Pillars of AI System Observability
**Layout:** Metrics, logs, traces as the observability foundation

**Content:**
**The Three Pillars of Observability (adapted for AI systems):**

**Pillar 1 — Metrics:** Numerical time-series measurements
- Standard: latency, error rate, throughput, instance count
- AI-specific: AUC trend, PSI per feature, RAGAS faithfulness score, token count per request
- Tool: Amazon CloudWatch Metrics
- Strength: efficient aggregation; easy alerting; trending
- Weakness: high cardinality (many features) is expensive; no per-request context

**Pillar 2 — Logs:** Structured event records
- Standard: application logs, error logs, access logs
- AI-specific: per-prediction logs (input features + output + model version); agent trace logs; evaluation job logs; pipeline execution logs
- Tool: CloudWatch Logs + Logs Insights
- Strength: per-event detail; queryable; debugging context
- Weakness: volume can be expensive; requires structured format for effective querying

**Pillar 3 — Traces:** Distributed request traces spanning components
- Standard: request trace across microservices
- AI-specific: full pipeline trace from feature retrieval → model inference → response; agent reasoning trace
- Tool: AWS X-Ray + Bedrock trace logging
- Strength: end-to-end visibility of request path; identifies latency bottlenecks
- Weakness: overhead per request; complex setup for ML pipelines

**Figure:** *Three-pillar observability diagram.* Three columns (Metrics, Logs, Traces). Each column: definition, example NorthStar data, tool, and strength/weakness summary. At the bottom: "Observability = Metrics + Logs + Traces working together." A single request's journey is shown across all three pillars: the same churn prediction request appears as a metric point (28ms latency), a log entry (full input/output), and a trace span (feature retrieval: 5ms, inference: 18ms, serialization: 5ms). The three pillars provide complementary views of the same event.

**Notes:** "The three pillars are complementary — you need all three for full observability. Metrics tell you when to look. Logs tell you what happened. Traces tell you where the time went. When you get a latency alarm (metric): look at traces to find which component is slow. When a trace shows an unexpected path: look at logs to understand why. The workflow is: alarm → metrics → traces → logs. Each layer narrows the investigation."

---

## Slide 3 — SageMaker Model Monitor: Deep Dive
**Layout:** Model Monitor internals and configuration best practices

**Content:**
**How SageMaker Model Monitor Actually Works:**

Model Monitor runs as a SageMaker Processing Job on your schedule (daily in NorthStar). It:
1. Reads captured inference data from S3 (your endpoint's data capture)
2. Reads the training baseline statistics and constraints from S3 (created by `suggest_baseline()`)
3. For each feature in the captured data: computes the current distribution statistics
4. Compares current statistics to baseline constraints (PSI, missing value %, schema)
5. Writes a monitoring report to S3 with violations flagged
6. Publishes CloudWatch metrics: `feature_baseline_drift_metric` per feature

**Monitoring report structure:**
```json
{
  "monitoring_output": {
    "violation_details": [
      {
        "feature_name": "monetary_30d",
        "constraint_check_type": "numerical_statistics.psi",
        "description": "Numerical statistics - psi value 0.28 exceeds threshold 0.2",
        "metric_value": 0.28,
        "threshold": 0.2
      }
    ],
    "completeness_metrics": {
      "columns_constraints_satisfied": 5,
      "total_columns": 6
    }
  }
}
```

**Tuning the constraints:** The default constraints from `suggest_baseline()` are starting points. Tune them:
```python
# Load suggested constraints and modify
import json
with open('constraints.json') as f:
    constraints = json.load(f)

# Increase PSI threshold for monetary features (expected Q4 drift)
for feature in constraints['features']:
    if 'monetary' in feature['name']:
        feature['numerical_statistics']['psi']['threshold'] = 0.35  # Higher for Q4

# Save modified constraints back
monitor.update_monitoring_schedule(constraints=constraints)
```

**Figure:** *Model Monitor execution flow diagram.* Scheduled Processing Job (daily 6 AM) → reads from: Captured Data S3 (today's sample) and Baseline S3 (training statistics). Processing job: computes PSI per feature → compares PSI against constraints → writes a violation report to S3 → publishes CloudWatch metrics. CloudWatch metrics → alarm (if violation) → SNS → Lambda retraining trigger. The flow shows: Model Monitor is a pipeline, not a magic service. Understanding the pipeline helps you debug when it doesn't work.

**Notes:** "The Q4 threshold tuning is an important operational practice. In November, monetary features for a retail chain will drift significantly from the annual baseline — due to holiday shopping. If you don't increase the threshold, you'll retrain the model in early November (when the holiday drift is just starting), then again in mid-November (when it's accelerating), then again in December. Three unnecessary retraining cycles. Instead: raise the threshold for Q4, monitor for anomalous drift within the seasonal range, and retrain once after the holiday season."

---

## Slide 4 — LLMOps Observability: Watching What the LLM Does
**Layout:** LLMOps-specific observability patterns

**Content:**
**LLM System Observability: Different From Model Monitoring**

Traditional model monitoring tracks numerical feature distributions. LLM systems require:

**1. Token-level monitoring:**
```python
# Track tokens per request to detect prompt length drift or unusual inputs
def log_bedrock_invocation(request_body: dict, response_body: dict, 
                            duration_ms: float, customer_id: str):
    input_tokens = response_body['usage']['input_tokens']
    output_tokens = response_body['usage']['output_tokens']
    total_tokens = input_tokens + output_tokens
    
    cloudwatch.put_metric_data(
        Namespace='NorthStar/OfferGeneration',
        MetricData=[
            {'MetricName': 'InputTokens', 'Value': input_tokens, 'Unit': 'Count'},
            {'MetricName': 'OutputTokens', 'Value': output_tokens, 'Unit': 'Count'},
            {'MetricName': 'TotalTokens', 'Value': total_tokens, 'Unit': 'Count'},
            {'MetricName': 'LatencyMs', 'Value': duration_ms, 'Unit': 'Milliseconds'}
        ]
    )
    
    # Log full request/response for audit trail
    logger.info(json.dumps({
        'customer_id': customer_id,
        'input_tokens': input_tokens,
        'output_tokens': output_tokens,
        'latency_ms': duration_ms,
        'model_id': response_body['model'],
        'faithfulness_sampled': None  # Filled in by weekly RAGAS job
    }))
```

**2. Prompt drift monitoring:**
- Track: average system prompt length over time (flag if increases)
- Track: % of requests where context (retrieved documents) is shorter than minimum useful length
- Alert: if context < 200 tokens for > 10% of requests (RAG index may be stale or misconfigured)

**3. Output quality monitoring (RAGAS sampling):**
```python
# Weekly Lambda: sample 5% of production responses; run RAGAS
def weekly_ragas_evaluation(event, context):
    sampled_responses = get_sampled_responses_from_logs(
        start_date=last_week, percentage=0.05
    )
    ragas_results = evaluate_with_ragas(sampled_responses)
    
    cloudwatch.put_metric_data(
        Namespace='NorthStar/OfferGeneration/Quality',
        MetricData=[
            {'MetricName': 'Faithfulness', 'Value': ragas_results['faithfulness']},
            {'MetricName': 'AnswerRelevancy', 'Value': ragas_results['answer_relevancy']},
            {'MetricName': 'ContextRecall', 'Value': ragas_results['context_recall']}
        ]
    )
```

**Figure:** *LLMOps observability dashboard.* Four panels: Token count distribution (histogram over 30 days — bimodal: short inputs and long inputs, no unusual spike); Latency trend (P50/P90/P99 over 30 days, all stable); RAGAS metrics (faithfulness/relevancy/recall weekly trend, all above threshold); Cost/day (bar chart, stable with minor variance). One panel in amber: Context token length per request — declining trend over the last two weeks, annotated "RAG index may need refresh."

**Notes:** "The declining context token length is the signal that a RAG index is going stale. When the Knowledge Base contains fresh, relevant documents, retrieval returns rich context. As documents age, retrieval quality declines — fewer relevant documents are found, and the context passed to the LLM shrinks. This manifests as shorter context tokens, declining RAGAS context recall, and, eventually, lower offer quality. The leading indicator is context length; the lagging indicator is RAGAS recall score."

---

## Slide 5 — Agent Observability: Tracing the Reasoning Chain
**Layout:** Bedrock Agent trace analysis for operational insight

**Content:**
**Agent Observability: Reading the Trace**

Agent systems require trace-level observability — you need to see the full reasoning chain to understand why an agent made a particular decision.

**Querying agent traces in CloudWatch Logs Insights:**
```sql
-- Find sessions where the agent made more than 8 tool calls (potential loop risk)
fields @timestamp, @message
| filter trace_type = 'orchestrationTrace'
| stats count() as tool_call_count by session_id
| filter tool_call_count > 8
| sort tool_call_count desc
| limit 20
```

```sql
-- Find tool failures by tool name (identify which tool is most problematic)
fields trace_data.orchestrationTrace.observation.actionGroupInvocationOutput.text as tool_output
| filter trace_type = 'orchestrationTrace'
      AND trace_data.orchestrationTrace.observation.actionGroupInvocationOutput.text like /error/i
| stats count() as error_count by trace_data.orchestrationTrace.observation.actionGroupInvocationInput.actionGroupName
| sort error_count desc
```

**Agent health metrics to track:**
| Metric | Formula | Alert Threshold | Interpretation |
|--------|---------|----------------|----------------|
| Avg tool calls per session | total_tool_calls / total_sessions | > 8 | Agent is over-reasoning |
| Tool failure rate | failed_tool_calls / total_tool_calls | > 3% | Backend service degrading |
| Escalation rate | sessions_escalated / total_sessions | > 20% or < 4% | Agent under/over-confident |
| Session token count | avg tokens per session | > 4,000 | Prompt or context growing |
| Resolution rate | sessions_resolved / total_sessions | < 82% | Quality decline |

**Figure:** *Agent observability dashboard.* Five metric panels corresponding to the table above. Tool calls per-session histogram (distribution with an alert line at 8). Tool failure rate by tool name (bar chart: order_lookup_tool highlighted in amber at 2.8%). Escalation rate trend (line chart: stable at 8-9%). Session token count trend (stable at ~1,240). Resolution rate trend (stable at 91.7%). All within thresholds except order_lookup_tool.

**Notes:** "The 'over 8 tool calls' query is your loop-detection query." Run it daily. When you find sessions exceeding 8 tool calls, read the full trace for those sessions: what was the agent trying to accomplish? What kept it looping? This is agent debugging — it's different from model debugging because you're reading natural language reasoning, not numerical inputs and outputs."

---

## Slide 6 — Model Lifecycle Management: When to Act
**Layout:** Model lifecycle decision framework

**Content:**
**The Model Lifecycle: Four Decision Points**

Every model in production eventually faces one of four decisions:

**1. Maintain (routine operation):**
- Signal: AUC within ±2% of baseline; no significant drift; business metrics stable
- Action: routine monitoring; no intervention required
- Review frequency: weekly dashboard check

**2. Retrain (model refresh):**
- Signal: PSI > 0.20 on key features; AUC drops > 3% from baseline; seasonal drift anticipated
- Action: trigger retraining pipeline with updated data; evaluate against gate criteria; deploy via canary
- Typical frequency for NorthStar churn: quarterly + on-demand (triggered by drift)

**3. Redesign (model architecture change):**
- Signal: performance ceiling reached (AUC plateaus despite retraining); new business requirements; new data sources available; major feature engineering opportunity identified
- Action: new AISDLC cycle; not a retrain but a new project
- NorthStar trigger: new clickstream data available → add browsing behavior features → may require architecture change

**4. Retire (model decommission):**
- Signal: system is not creating business value (intervention effectiveness too low); replaced by a better system; use case eliminated
- Action: graceful deprecation; notify downstream consumers; remove infrastructure
- Data retention: maintain prediction logs and evaluation history per audit requirements

**Figure:** *Model lifecycle decision tree.* Root node: "Is the model performing within SLA?" YES → "Is business value being created?" YES → Maintain. NO → "Is drift the cause?" YES → Retrain. NO → "Is it an architecture limitation?" YES → Redesign. NO → Retire. The tree shows: lifecycle decisions are hierarchical — check the simplest intervention (retrain) before escalating to the more expensive one (redesign or retire).

**Notes:** "The 'retire' decision is the one teams are most reluctant to make. There's an emotional investment in a model that took months to build. But a model that isn't creating business value is consuming infrastructure budget and engineering attention that could be applied to something that does create business value. The discipline: if a model's ROI is negative (cost > value created), retire it. Don't maintain a zombie model."

---

## Slide 7 — Drift: The Full Taxonomy
**Layout:** Complete drift taxonomy with detection methods

**Content:**
**The Four Types of Drift in AI Systems:**

**1. Data drift (covariate shift):**
- Definition: the distribution of input features changes
- Detection: PSI per feature (Model Monitor)
- NorthStar example: monetary_30d distribution shifts upward in Q4 (holiday spending)
- Response: retrain if PSI > 0.20 and drift is not seasonal; adjust thresholds if seasonal

**2. Concept drift (label shift):**
- Definition: the relationship between inputs and outputs changes — the same inputs now predict different outputs
- Detection: compare predicted churn rate vs. observed churn rate on recent data (requires ground truth lag)
- NorthStar example: COVID-19-style event changes customer behavior fundamentally; historical patterns no longer predict churn correctly
- Response: urgent retraining; may require new feature engineering

**3. Model drift (prediction shift):**
- Definition: model's prediction distribution changes without obvious input cause
- Detection: monitor distribution of predicted probabilities (PSI on predictions, not features)
- NorthStar example: rare event — possible if model is loaded incorrectly after update; caught by smoke test
- Response: investigate deployment; check model artifact integrity; rollback if confirmed

**4. Upstream drift (pipeline drift):**
- Definition: a change in an upstream data system or ETL process changes the data that flows to the model
- Detection: compare ETL output schema and statistics vs. baseline
- NorthStar example: Glue ETL updated to fix a bug, but the fix changes how frequency_30d is computed
- Response: validate all upstream changes against feature contracts; test ETL changes against feature schema

**Figure:** *Drift taxonomy diagram.* Four-quadrant layout. Each quadrant: drift type, visual representation (distribution plots showing before/after), detection method, and NorthStar example. Data drift quadrant: two overlapping histograms (baseline vs. current; shifted right). Concept drift quadrant: scatter plot showing a changed decision boundary. Model drift quadrant: two prediction score distributions (shifted). Pipeline drift quadrant: flowchart showing ETL change affecting downstream feature values.

**Notes:** "Upstream drift is the most underdiagnosed form of drift. Teams carefully monitor model input distributions but don't notice when the ETL process generating those features changes. The model's input distribution looks fine in terms of schema compliance, but the semantic meaning of the features has changed. Feature contracts — enforced at the ETL → Feature Store boundary — are the primary defense against pipeline drift."

---

## Slide 8 — Retraining Strategy: When, How, and How Often
**Layout:** Retraining strategy design with NorthStar schedule

**Content:**
**Retraining Strategy: Three Approaches**

**Approach 1 — Scheduled retraining:**
- Train on a fixed schedule (e.g., monthly for NorthStar churn model)
- Pros: predictable; easy to plan; no drift monitoring required for trigger
- Cons: may retrain unnecessarily when the model is stable; may not retrain fast enough when urgent drift occurs
- Best for: models where business data changes at a known rate

**Approach 2 — Drift-triggered retraining:**
- Retrain when drift metrics exceed threshold (PSI > 0.20)
- Pros: responds to actual data changes; doesn't waste resources on unnecessary retraining
- Cons: requires Model Monitor setup; drift threshold tuning required; may trigger in false-positive cases (seasonal drift)
- Best for: production systems with variable update frequency; mature MLOps pipelines

**Approach 3 — Hybrid (recommended for NorthStar):**
- Scheduled: quarterly baseline refresh (ensures model doesn't get stale)
- Drift-triggered: emergency retrain when PSI > 0.20 on core features
- Business-triggered: retrain after major events (new store openings, loyalty program changes, pricing model changes)

**NorthStar Churn Retraining Calendar:**
- Q1 (Jan): Scheduled retraining (post-holiday period; baseline reset with Q4 holiday data)
- Q2 (Apr): Scheduled retraining (Q1 data included; spring shopping pattern refresh)
- Q3 (Jul): Scheduled retraining + school-year shopping pattern update
- Q4 (Oct): Scheduled retraining pre-holiday
- Drift-triggered: any time PSI > 0.20 on recency_days or monetary_30d outside seasonal windows
- Business-triggered: new loyalty program launch → retrain within 2 weeks

**Figure:** *Retraining calendar visualization.* 12-month calendar with: Scheduled retraining events marked (Jan, Apr, Jul, Oct). Drift-triggered events shown as conditional branches. Business events noted. Total estimated retraining events per year: 4-8. Cost estimate: 4-8 × $2.24/training run = $9-18/year in training compute. Monitoring compute (Model Monitor daily): ~$15/month. The cost view communicates that automated retraining is extremely cheap compared to the cost of operating a degraded model.

**Notes:** "The quarterly schedule with drift-triggered emergency retraining is the standard pattern for retail churn models. The quarterly schedule ensures you never fall more than 3 months behind the current data. The drift trigger catches unusual events (major competitor action, supply chain disruption, economic shock) that require faster response. The hybrid approach gives you both predictability and responsiveness."

---

## Slide 9 — Observability in the CI/CD Pipeline
**Layout:** Pipeline observability and debugging tools

**Content:**
**Observing the Training Pipeline (Not Just the Production System)**

The CI/CD training pipeline itself needs observability. Pipeline failures are the #1 source of operational overhead for ML teams.

**SageMaker Pipeline execution monitoring:**
```python
# Get execution status and step details
def check_pipeline_health():
    executions = sagemaker_client.list_pipeline_executions(
        PipelineName='northstar-churn-training-pipeline',
        MaxResults=10
    )
    
    for execution in executions['PipelineExecutionSummaries']:
        print(f"Execution: {execution['PipelineExecutionArn']}")
        print(f"Status: {execution['PipelineExecutionStatus']}")
        print(f"Started: {execution['StartTime']}")
        
        # Get step details for failed executions
        if execution['PipelineExecutionStatus'] == 'Failed':
            steps = sagemaker_client.list_pipeline_execution_steps(
                PipelineExecutionArn=execution['PipelineExecutionArn']
            )
            for step in steps['PipelineExecutionSteps']:
                if step['StepStatus'] == 'Failed':
                    print(f"  FAILED STEP: {step['StepName']}")
                    print(f"  Failure reason: {step['FailureReason']}")
```

**Common pipeline failure patterns and fixes:**

| Failure Type | Symptom | Root Cause | Fix |
|-------------|---------|-----------|-----|
| OOM in Training | TrainingJob status: Failed; reason: ResourceExhausted | Training data too large for instance type | Switch to ml.m5.2xlarge; or reduce batch size |
| S3 Access Denied | ProcessingJob status: Failed; 403 error | IAM role missing S3 permission | Add s3:GetObject to training role policy |
| Gate fails unexpectedly | ConditionStep goes to fail branch; AUC looks fine | evaluate.py output key doesn't match ConditionStep JSON path | Align key names exactly |
| Timeout | TrainingJob timeout after 24 hours | max_run too short for large dataset | Increase max_run; consider spot instances |

**Figure:** *Pipeline execution timeline dashboard.* 10 recent executions shown as a timeline (like GitHub Actions runs). Each execution: start time, duration, status (green=SUCCEEDED, red=FAILED). One failed execution highlighted, with step-level breakdown: Step 1 (PrepareFeatures: SUCCEEDED, 31 min), Step 2 (TrainingJob: FAILED, 12 min) with failure reason "ResourceExhausted: OOM." The detail view mirrors what SageMaker Studio shows and what students will use for debugging.

**Notes:** "The step-level failure details are what you want when debugging a pipeline failure. 'Pipeline failed' tells you nothing. 'Step TrainingJob failed at 12 minutes with ResourceExhausted' tells you: the training job ran out of memory, probably because the training data is larger than the instance can handle. Next action: `describe_training_job()` to get the CloudWatch Logs URL, read the logs for the last line before the OOM."

---

## Slide 10 — Building the Unified Dashboard (Lab 6 Part 2)
**Layout:** Dashboard architecture and implementation guidance

**Content:**
**Lab 6 Part 2: Building the NorthStar Unified Dashboard**

A unified dashboard tells the operator: what's the health of the whole platform, right now?

**Dashboard design principles:**
- **One page:** All critical metrics visible without scrolling. If you need to scroll, the dashboard is too busy.
- **Traffic-light status:** At a glance, every metric is green/amber/red. No mental math required.
- **Leading indicators prominent:** Feature drift, latency trends front and center. Business metrics in the corner for context.
- **Action-oriented:** Every amber/red metric should link to a runbook or action.

**NorthStar dashboard structure (CloudWatch Dashboard JSON):**
```python
dashboard_body = {
    "widgets": [
        # Row 1: Platform health summary (3 status tiles)
        {"type": "metric", "x": 0, "y": 0, "width": 8, "height": 4,
         "properties": {"title": "Churn Endpoint — Latency P99",
                        "metrics": [["AWS/SageMaker", "ModelLatencyP99",
                                     "EndpointName", "northstar-churn-prod"]],
                        "threshold": 200}},
        
        # Row 2: Data pipeline health
        {"type": "metric", "x": 0, "y": 4, "width": 12, "height": 4,
         "properties": {"title": "Glue Pipeline Success Rate",
                        "metrics": [["NorthStar/DataPipeline", "JobSuccessRate"]]}},
        
        # Row 3: LLM system health
        # Row 4: Agent health
        # Row 5: Platform economics (daily cost)
    ]
}

cw.put_dashboard(
    DashboardName='NorthStar-AI-Platform',
    DashboardBody=json.dumps(dashboard_body)
)
```

**Figure:** *NorthStar unified dashboard mockup.* Five-section CloudWatch dashboard layout. Section 1 (top row): three metric tiles — Churn endpoint P99 latency (142ms, green), Feature Store freshness (last updated 2h ago, green), Platform availability (99.97%, green). Section 2: Glue pipeline success rate (trend line). Section 3: Offer generation faithfulness + latency. Section 4: Agent resolution rate + escalation rate. Section 5: Daily cost by system (bar chart). Clean, operational, one-page view.

**Notes:** "The dashboard design principle of 'one page' is harder to follow than it sounds. Engineers love metrics and tend to add more and more until the dashboard requires scrolling. The discipline: if a metric doesn't help you decide what action to take right now, it doesn't belong on the main dashboard. Put it on a secondary 'deep dive' dashboard instead. The main dashboard should answer: 'Is everything OK?' in under 30 seconds."

---

## Slide 11 — The Runbook: Operationalizing Your Monitoring
**Layout:** Runbook structure for NorthStar AI platform

**Content:**
**The Runbook: What to Do When Alerts Fire**

A runbook documents what an operator should do for each type of alert. Without a runbook, every alert is a debugging exercise from scratch. With a runbook, most alerts are resolved in under 30 minutes.

**NorthStar Runbook Structure:**

**Runbook: Churn Endpoint Error Rate Alert**
```markdown
## Alert: NorthStar-Churn-ErrorRate-P2
**Threshold:** > 5% error rate for 2 consecutive 5-minute windows
**Severity:** P2 (Slack notification; acknowledge within 1 hour)

## Diagnostic Steps
1. Check the endpoint status: `aws sagemaker describe-endpoint --endpoint-name northstar-churn-prod`
   - If endpoint status != "InService": endpoint is unhealthy → Step 2
   - If endpoint status = "InService": investigate at request level → Step 3

2. Endpoint not InService:
   - Check for recent deployment: did a canary deploy just start?
   - If yes: check canary health gate; if hard failure triggered, rollback should auto-complete
   - If no recent deploy: check CloudWatch logs for the endpoint container → common: OOM, container crash

3. Endpoint InService but high error rate:
   - Query recent errors: CloudWatch Logs Insights → /aws/sagemaker/Endpoints/northstar-churn-prod
   - Common patterns:
     a. `ValueError: input shape mismatch` → feature schema changed; check ETL job
     b. `TimeoutError` → instance overloaded; trigger manual scale-out
     c. `NullPointerException on feature X` → feature missing in input; check Feature Store

## Escalation
If not resolved in 30 min → escalate to ML lead (on-call rotation)
If churn predictions are failing for > 1 hour → use rule-based fallback (predict churn if recency_days > 60)
```

**Figure:** *Runbook decision tree.* Alert fires → two branches (endpoint not InService / endpoint InService). Each branch: 3-4 diagnostic steps as a flowchart with actions. Resolution paths: auto-rollback (canary case), manual scale-out (overload case), ETL fix (feature schema case). Escalation path shown at bottom. The runbook flowchart is immediately actionable — a on-call engineer who's never seen the system before can follow it.

**Notes:** "The rule-based fallback in the escalation section — 'predict churn if recency_days > 60' — is the operational safety net. When the ML system is down, you don't stop doing business. You fall back to a simpler approach. The fallback should be documented, pre-coded, and ready to activate. 'We can't do churn prediction right now because the model endpoint is down' is not acceptable for a production business system."

---

## Slide 12 — Lifecycle Management for RAG and Agent Systems
**Layout:** Lifecycle management specific to LLM-based systems

**Content:**
**RAG System Lifecycle: The Living Knowledge Base**

RAG systems age differently from traditional ML models. The knowledge base becomes stale; the model doesn't. The operational lifecycle centers on index freshness:

**RAG Knowledge Base Lifecycle Events:**

| Event | Frequency | Trigger | Action |
|-------|-----------|---------|--------|
| Incremental index update | Weekly | New/updated documents in S3 source | Sync to staging KB; smoke test; blue/green swap |
| Full re-index | Monthly | Scheduled | Full corpus re-index in staging; quality check; swap |
| Emergency update | On-demand | Critical document correction | Direct update to active KB; immediate |
| Index retirement | When content source retired | Business decision | Delete KB; update routing to exclude |

**RAG system "decay" signals:**
- RAGAS context recall declining (retrieval finding less relevant content)
- User-facing: offer relevance score declining
- Context length per request declining (fewer/shorter retrieved chunks)

**Agent System Lifecycle:**

Agents have a different lifecycle challenge: tool contracts change over time. When the backend services that the agent calls are updated:
- Tool signature changes → agent tool call format may break
- Tool behavior changes → agent reasoning based on tool output may be wrong
- Tool retirement → agent may attempt to call a decommissioned tool

**Agent contract testing (continuous):**
```python
def test_agent_tool_contracts():
    """Verify each tool still behaves as the agent expects."""
    for tool_name, expected_schema in TOOL_CONTRACTS.items():
        actual_schema = get_tool_schema(tool_name)
        assert actual_schema == expected_schema, \
            f"Tool contract broken: {tool_name} schema changed"
```

**Figure:** *RAG and Agent lifecycle comparison table.* Two-column table: RAG System (left) vs. Agent System (right). Rows: Primary artifact, Lifecycle trigger, Common failure mode, Monitoring signal, Retirement signal. The comparison shows: RAG lifecycle is about index freshness; Agent lifecycle is about tool contract stability.

**Notes:** "The agent tool contract test is the canary in the coal mine for agent systems. Every time the backend team changes an API that your agent tools call, the agent could silently start failing — because it expects a JSON response with `order_status` and gets `status` instead. Run the tool contract test on every backend deployment, not just on agent deployments. The agent didn't change; the tool changed."

---

## Slide 13 — Incident Response Deep Dive: A Real Scenario
**Layout:** Full incident response walkthrough

**Content:**
**Incident Walkthrough: Churn Model Silent Degradation**

**Monday, Nov 9, 2026, 6:04 AM UTC — Model Monitor fires:**
Alarm: `northstar-churn-data-quality-violation`
Violation: `monetary_30d` PSI = 0.27 (threshold: 0.20)
Auto-response: Retraining Lambda triggered; SageMaker Pipeline execution started

**6:04 - 9:30 AM — Automated pipeline running:**
Pipeline executing: PrepareFeatures → Train (on-demand with updated data) → Evaluate

**9:31 AM — Gate check result:**
New model AUC: 0.69 — **FAILS gate (threshold: 0.72)**
ConditionStep goes to fail branch; alert fires to ML team

**10:15 AM — ML engineer investigates:**
Root cause analysis:
- `monetary_30d` drift was real (holiday shopping surge)
- But training on only the last 60 days of data (with holiday patterns) overfitted to holiday behavior
- The model generalizes poorly on non-holiday customers
- Fix: use rolling 12-month training window (not 60-day window) to balance seasonal and non-seasonal patterns

**11:30 AM — Fix implemented:**
Retraining pipeline triggered manually with 12-month rolling window
New model AUC: 0.74 — PASSES gate
Pipeline proceeds: model registered; canary deployment starts

**Wednesday, Nov 11 — Canary full rollout:**
Canary healthy for 48 hours; promoted to 100% traffic
Monitoring confirms: monetary_30d drift stabilized; AUC stable at 0.74

**Figure:** *Incident timeline diagram.* Horizontal timeline from Nov 9 6:04 AM to Nov 11. Key events marked: alarm (6:04), pipeline trigger (6:04), gate failure (9:31), investigation (10:15), fix (11:30), retrain (11:45), gate pass (14:00), canary start (14:30), canary full (Nov 11). MTTR from alarm to resolution: 2 days (canary included) or 8 hours (to fix deployment). The incident demonstrates that automated monitoring caught the problem, automated retraining attempted a fix, and human investigation was needed to fix the root cause.

**Notes:** "The key lesson from this incident: automated retraining is not always the right response to drift. The algorithm followed the rules perfectly — PSI exceeded threshold → retrain. But the automated retraining used the default 60-day window, which over-fitted to holiday patterns. The right fix required human judgment: understanding that 12 months of training data balances seasonal variation. This is why monitoring triggers human investigation, not just automated response. The human makes the judgment call; the automation executes."

---

## Slide 14 — Lab 6 Progress Check and Common Issues
**Layout:** Lab 6 status assessment and common issues

**Content:**
**Lab 6 — 10 Days Remaining: Status Check**

**What should be done by today:**
- [ ] Data capture enabled on churn endpoint (Part 1, Step 1) — must be running to accumulate data
- [ ] Lab 5 submitted Saturday (prerequisite for Lab 6 canary infrastructure)

**What to focus on this week:**
- Baseline creation (Part 1, Step 2) — requires at least 24 hours of captured data
- Dashboard design (Part 2) — independent of monitoring; can work in parallel

**Common Lab 6 issues:**

**Issue 1: Data capture not accumulating**
Check the S3 path: `s3://northstar-monitoring/data-capture/` — are there files in subdirectories?
If empty: verify the endpoint config includes DataCaptureConfig with `enable_capture=True`
Verify the endpoint was updated (not just the config created): `describe_endpoint()` should show capture enabled

**Issue 2: Baseline job fails with insufficient data**
Model Monitor's `suggest_baseline()` requires at least 50 rows in the baseline dataset.
Ensure `churn-features-baseline.csv` contains the correct features in the correct format.
The baseline must use the **same feature schema** as what the endpoint receives — not the raw feature store data.

**Issue 3: Dashboard metrics not appearing**
Custom metrics (NorthStar/OfferGeneration, NorthStar/DataPipeline) only appear after they've been published at least once.
If you haven't run the Glue pipeline or offer generation since adding CloudWatch.put_metric_data(), the namespace won't exist yet.
Trigger one Glue job run and one offer generation invocation to populate the metrics.

**Figure:** *Lab 6 checklist with status indicators.* Progress tracker: Part 1 (3 steps: capture enabled ✅/⬜/⬜), Part 2 (dashboard started ⬜), Part 3 (retraining Lambda ⬜), Part 4 (compliance report ⬜). Expected progress at Day 2: Part 1 Step 1 done; Parts 2-4 not started. "On track" vs. "behind" assessment. Specific action for tonight: "Enable data capture (15 minutes). Then start dashboard design."

**Notes:** "The single most important thing to do tonight for Lab 6: verify that data capture is enabled and files are appearing in S3. This is the dependency that everything else in Lab 6 Part 1 builds on. If you wait until next week to start Part 1, you won't have enough captured data to run a meaningful baseline and monitoring schedule. Enable it tonight."

---

## Slide 15 — The Monitoring Maturity Model
**Layout:** Monitoring maturity levels with NorthStar position

**Content:**
**Monitoring Maturity: Where Teams Are and Where They Should Be**

**Level 0 — Dark operation:**
- No monitoring; discover problems from customer complaints
- Common in: teams that "just got the model working"
- NorthStar after Lab 3 (pre-monitoring labs)

**Level 1 — Basic metrics:**
- Endpoint availability and latency monitored
- No model quality metrics; no business outcome tracking
- Most teams' starting point

**Level 2 — Full three-pillar:**
- Metrics: latency, error rate, drift PSI, quality metrics
- Logs: structured prediction logs; pipeline execution logs
- Alerts: configured for all critical failure conditions
- NorthStar target after Lab 6

**Level 3 — Proactive observability:**
- Leading indicators tracked and connected to business outcomes
- Runbooks for every alert type
- Automated incident response (retraining, rollback)
- Post-incident reviews with prevention measures
- NorthStar target after Lab 7

**Level 4 — Adaptive operations:**
- Self-healing systems (automated rollback, self-tuning thresholds)
- Predictive monitoring (ML predicts when intervention is needed before alert fires)
- Very few organizations at this level

**Figure:** *Monitoring maturity staircase.* Five steps (Level 0-4). Each step: name, characteristics, and a representative metric: "how long until you discover a production incident?" Level 0: 2-3 days (customer complaint). Level 1: 4-8 hours (SLA breach detected). Level 2: 30-60 minutes (alert fires). Level 3: < 15 minutes (leading indicator fires before incident). Level 4: pre-emptive (problem prevented before it occurs). The discovery latency metric makes the business value of each maturity level concrete.

**Notes:** "The discovery latency improvement from Level 0 (2-3 days) to Level 2 (30-60 minutes) is the most impactful jump in the maturity staircase. At Level 0, a customer notices the problem and calls customer service. At Level 2, your monitoring fires before the first customer is affected. The difference in customer impact: hundreds of affected customers vs. zero. Lab 6 moves NorthStar from Level 0-1 (where it sits after Labs 1-5) to Level 2-3."

---

## Slide 16 — Key Takeaways + What's Next
**Layout:** Takeaways + L22 preview

**Content:**
**Key Takeaways:**
1. Observability requires three pillars: metrics (what happened), logs (what the event contained), traces (where in the pipeline it happened) — all three are necessary; none is sufficient alone
2. Drift has four types: data drift (feature distribution), concept drift (label shift), model drift (prediction shift), pipeline drift (upstream changes) — detection methods differ for each
3. Retraining strategy should be hybrid: scheduled (quarterly) + drift-triggered (PSI threshold) + business-triggered (major events) — neither pure-scheduled nor pure-reactive is optimal
4. The runbook is the operational artifact that makes monitoring actionable — every alert type must have a documented response procedure before the system goes to production
5. Agent systems require tool contract testing in addition to standard observability — backend API changes break agents silently without this safeguard

**Next Session (Tue Nov 17):**
- Topic: Reliability Engineering — SLA design, error budgets, chaos engineering for AI, graceful degradation
- Reading due: *Reliability for AI Systems* — "SRE Principles" through "Graceful Degradation"
- Lab 6 due in 10 days — keep Part 1 moving; get data capture accumulating

**Figure:** *Five-takeaway summary card.* Lab 5 due Saturday (2 days, red). Lab 6 due in 10 days (amber). Monitoring maturity staircase thumbnail. Incident timeline thumbnail.

**Notes:** "Lab 5 is due in 2 days. If you have anything outstanding — the CloudWatch scale-out screenshot, the deployment runbook, any missing components — finish it tonight. After Saturday, context shifts fully to Lab 6. Reliability Engineering next Tuesday connects to what you're building in Lab 6: the combination of monitoring (Lab 6) and reliability patterns (L22) is what makes a production AI system trustworthy over time."
