---
lecture: L11
title: XOps II — LLMOps & AgentOps
date: Thursday, October 8, 2026
week: 6
arc: Build
reading_due: "The XOps Stack — LLMOps through Key Takeaways"
lab_due: "Lab 3 due Sat Oct 17"
slides_target: 16
---

# L11: XOps II — LLMOps & AgentOps
**Thursday, October 8, 2026 | CS 401R: Engineering Production AI Systems | Fall 2026**

> Foundation model systems are not just models — they're pipelines of prompts, indexes, and tool calls. LLMOps and AgentOps are the operational disciplines that keep them reliable, safe, and measurable in production.

**Reading Due:** *The XOps Stack* — "LLMOps" through "Key Takeaways"

---

## Slide 1 — Title
**Layout:** Left dark panel + right split showing prompt → response flow with monitoring overlays

**Content:**
- XOps II: LLMOps & AgentOps
- CS 401R · Lecture 11 · Thursday, October 8, 2026
- Operating Foundation Model Systems at Production Scale

**Figure:** *LLM production pipeline with monitoring overlay.* Horizontal pipeline: User Query → Prompt Template → Context Injection (RAG) → LLM API Call → Response Filter → User Response. Below the pipeline: four monitoring overlays — latency tracker, cost meter, faithfulness evaluator, guardrail alert. Colors: pipeline steps in teal, monitoring in amber. Communicates: LLM production isn't just calling an API — it's a pipeline with operational requirements at every step.

**Notes:** "Last session covered DataOps and MLOps — the operational disciplines for traditional ML. Today we extend to the newer layers of the XOps stack: LLMOps for RAG and foundation model systems, and AgentOps for autonomous agents. If you're doing Lab 3 options A or B, this is the operational layer you'll need for Lab 5."

---

## Slide 2 — Why LLMOps Is Distinct from MLOps
**Layout:** Side-by-side comparison of MLOps and LLMOps operational requirements

**Content:**
**The Key Differences:**

| Dimension | MLOps (Traditional ML) | LLMOps (Foundation Models) |
|-----------|------------------------|---------------------------|
| **Model** | Your model; full control | Vendor model (Bedrock/OpenAI); black box |
| **Training** | Train, retrain, version | Prompt, few-shot, fine-tune rarely |
| **Primary artifact** | Model weights | Prompt templates + RAG index |
| **Failure modes** | Drift, accuracy decay | Hallucination, prompt injection, latency spikes |
| **Evaluation** | AUC, F1, MSE | Faithfulness, relevancy, citation accuracy |
| **Cost driver** | Compute (training) | Token usage (inference) |
| **State** | Stateless prediction | Stateful conversations + memory |
| **Versioning** | Model version → Registry | Prompt version + index version |

**The operational implication:** Most MLOps tooling doesn't handle LLM systems well. LLMOps requires specialized observability for prompt pipelines, token economics, and output quality dimensions that traditional ML monitoring doesn't address.

**Figure:** *Two-column comparison visual.* Left (MLOps): traditional model diagram with training → evaluation → deploy arc. Right (LLMOps): prompt template + RAG index + LLM API + guardrail diagram. Connecting arrow between the columns: "Both need: versioning, monitoring, CI/CD, cost governance." The differences are highlighted in the rows of the table above.

**Notes:** "The key insight is: when you use Bedrock, you don't own the model. You own the prompt template, the RAG index, and the configuration. These become your primary artifacts — they need versioning, testing, and CI/CD just like model weights do in traditional MLOps. 'Prompt drift' is just as real as 'model drift.'"

---

## Slide 3 — Prompt Engineering as an Engineering Discipline
**Layout:** Prompt versioning and testing framework

**Content:**
**Prompt Templates Are Production Artifacts:**

```yaml
# prompts/offer_generation_v3.2.yaml
version: "3.2"
created: "2026-10-08"
author: "ml-team"
system_prompt: |
  You are a retail marketing specialist for NorthStar stores.
  You generate personalized promotional offers based on customer data.
  
  RULES:
  - Always ground offers in the retrieved customer history
  - Never fabricate purchase history
  - Always include a specific discount amount (never vague "discount")
  - Format: [Offer type] | [Amount] | [Expiry] | [Reason]
  - If customer history is insufficient, respond: "INSUFFICIENT_DATA"

user_template: |
  Customer Segment: {segment}
  Purchase History (last 90 days): {purchase_history}
  Recent Browse History: {browse_history}
  Similar Customer Offers Accepted: {retrieved_context}
  
  Generate 3 personalized offers. Follow the required format.

test_cases: [...]  # 20 test cases with expected format/content
evaluation_criteria:
  format_compliance: 1.0   # 100% — exact format required
  factual_grounding: ≥0.95  # at most 5% hallucinated claims
  offer_specificity: ≥0.90  # at least 90% include specific amounts
```

**The discipline:**
- Every prompt change is a version bump
- Prompt versions stored in Git (not S3)
- Test suite runs on every version before production
- A/B testing for major prompt changes

**Figure:** *Prompt version control diagram.* Git commit history for a prompt template file. Commit messages: "v3.0: Add RULES block", "v3.1: Add INSUFFICIENT_DATA handling", "v3.2: Add citation format requirement." Branch `main` shows the production version; branch experiment/offer-v4-concise shows an A/B test in progress. Below: evaluation metric trend for each version (format compliance improving from 82% to 100% across versions).

**Notes:** "The YAML schema for prompt templates is not hypothetical — it's the actual pattern used by teams at Anthropic and other LLM-first companies. Your prompt is a contract between your system and the model. When you change it, you change the contract. Version control and testing are not optional."

---

## Slide 4 — RAG Index Operations: The Living Knowledge Base
**Layout:** RAG index lifecycle management diagram

**Content:**
**The RAG Index Is a Production Artifact:**

NorthStar Offer Generation RAG index contains:
- 2,847 historical offer documents
- 1,203 product catalog entries
- 892 customer segment profiles
- Total: 4,942 documents; ~8M tokens; refreshed weekly

**RAG Index Operations Requirements:**

| Operation | Frequency | Tool | Risk |
|-----------|-----------|------|------|
| Full re-index | Monthly | Bedrock Knowledge Base sync | 2-4 hour downtime if not planned |
| Incremental update | Weekly | S3 → Bedrock sync job | New/updated docs only; faster |
| Emergency update | On-demand | Manual trigger | Use for critical doc corrections |
| Index health check | Daily | Lambda → Bedrock query | Verifies index is serving |
| Index rollback | On failure | Snapshot restore | Requires prior snapshot policy |

**Common RAG index failure modes:**
- Stale index: new offers not appearing in recommendations
- Partial sync: some documents indexed, others missed (check CloudWatch for sync errors)
- Embedding model change: index built with old model, queries with new model → relevance collapse
- Document duplication: same document indexed twice; over-weights certain content

**Figure:** *RAG index lifecycle diagram.* S3 knowledge base bucket → Bedrock Knowledge Base sync → Vector index. Weekly cron trigger at top. Below the index: five operational boxes: Full Re-index, Incremental Update, Emergency Update, Health Check, Rollback. Each box: frequency, trigger mechanism, approximate duration, risk level color (green/amber/red). This communicates: the index is not set-and-forget — it's an operational system with its own lifecycle.

**Notes:** "The embedding model change failure mode is the sneaky one. You update the Bedrock Knowledge Base to use a new embedding model, but you forget to re-index the existing documents. Now your query embeddings and document embeddings are in different vector spaces — relevance scores are meaningless. Always re-index the full corpus when you change embedding models."

---

## Slide 5 — LLMOps Monitoring: What to Measure
**Layout:** LLMOps metrics framework with NorthStar thresholds

**Content:**
**LLMOps Monitoring Dimensions:**

**Performance metrics (latency, availability):**
- P50/P90/P99 response latency (target: P90 < 3s for offer generation)
- Availability: % of requests that complete without error (target: ≥ 99.5%)
- Timeout rate: % of requests that exceed latency threshold (alert: > 2%)

**Cost metrics (token economics):**
- Tokens per request: input + output; trend over time
- Cost per request: tokens × token cost; per-system budget tracking
- Top users / use cases by token spend: identify outlier patterns

**Quality metrics (output quality):**
- Faithfulness score: RAGAS automated evaluation on sampled responses (sample 5% of production responses)
- Format compliance: does the response match the expected format? (deterministic check)
- Citation accuracy: does the offer cite a document that actually supports it? (automated verification)
- Guardrail trigger rate: % of responses that triggered a guardrail block

**Safety metrics:**
- Prompt injection attempts: detected by guardrails; alert if > threshold
- Guardrail block rate: too high = legitimate requests blocked; too low = gaps in coverage

**NorthStar CloudWatch Dashboard for RAG Offer Generation:**
- 4 panels: Latency (P50/P90/P99 trend), Cost (daily token spend + budget tracking), Quality (faithfulness + format compliance running avg), Safety (guardrail trigger rate)

**Figure:** *LLMOps CloudWatch dashboard mockup.* Four-panel dashboard. Top-left: latency time series (P50 blue, P90 teal, P99 orange; P99 spike on Oct 3 highlighted with annotation "Bedrock throttling"). Top-right: cost bar chart by day (green bars below budget line; one day exceeds budget in amber). Bottom-left: quality trend (faithfulness and format compliance as dual line chart, both above thresholds). Bottom-right: guardrail trigger rate as area chart (mostly near-zero; spike on Oct 5 highlighted "prompt injection attempt detected"). Professional dashboard layout.

**Notes:** "The guardrail trigger rate spike is important. On Oct 5 in this example, an unusual spike of prompt injection attempts was detected — someone was trying to override the system prompt via crafted user input. The guardrail caught it. Without this monitoring, you'd never know the attack happened. With it, you know within minutes."

---

## Slide 6 — Guardrails: Safety in Production
**Layout:** Bedrock Guardrails configuration diagram

**Content:**
**Amazon Bedrock Guardrails for NorthStar:**

Guardrails are the safety layer applied to every LLM request and response:

```python
import boto3
bedrock = boto3.client('bedrock')

guardrail_config = {
    "name": "northstar-offer-guardrail",
    "contentPolicyConfig": {
        "filtersConfig": [
            {"type": "HATE", "inputStrength": "HIGH", "outputStrength": "HIGH"},
            {"type": "INSULTS", "inputStrength": "MEDIUM", "outputStrength": "HIGH"},
            {"type": "PROMPT_ATTACK", "inputStrength": "HIGH", "outputStrength": "NONE"}
        ]
    },
    "topicPolicyConfig": {
        "topicsConfig": [
            {
                "name": "CompetitorDiscussion",
                "definition": "Discussion of competitor stores or their pricing",
                "examples": ["Walmart has a better deal", "Amazon Prime is cheaper"],
                "type": "DENY"
            },
            {
                "name": "PersonalInformation",
                "definition": "Requests to reveal or discuss other customers' data",
                "type": "DENY"
            }
        ]
    },
    "sensitiveInformationPolicyConfig": {
        "piiEntitiesConfig": [
            {"type": "EMAIL", "action": "ANONYMIZE"},
            {"type": "PHONE", "action": "ANONYMIZE"},
            {"type": "US_SOCIAL_SECURITY_NUMBER", "action": "BLOCK"}
        ]
    }
}
```

**NorthStar Guardrail Architecture:**
- Applied at request ingestion (input guardrail)
- Applied at response generation (output guardrail)
- Violations logged to CloudWatch; severe violations alert on-call

**Figure:** *Guardrail flow diagram.* User Request → Input Guardrail → (if pass) → LLM → Output Guardrail → (if pass) → User Response. Two failure paths: "Input blocked" → "BLOCKED_REQUEST" response with reason code. "Output blocked" → "FILTERED_RESPONSE" response with safe fallback. Below the diagram: metrics: 0.1% of requests blocked at input; 0.05% filtered at output; 99.85% pass-through rate.

**Notes:** "Notice that the input guardrail is separate from the output guardrail. The input guardrail catches prompt injection attempts and inappropriate inputs before they consume expensive tokens. The output guardrail catches cases where the model produced something that shouldn't reach the user, even if the input was benign. You need both."

---

## Slide 7 — AgentOps: The New Frontier
**Layout:** AgentOps requirements vs. MLOps/LLMOps

**Content:**
**Why Agents Need Their Own Operational Discipline:**

Agents are different from both ML models and RAG systems:
- **Non-deterministic execution paths:** The same input can produce different tool call sequences on different runs
- **Side effects:** Agents take actions (write to database, send email, call API) — errors have real consequences
- **Long-running:** Agents can run for seconds to minutes, consuming tokens and making decisions throughout
- **Authority concerns:** Agents operate with tool permissions; prompt injection → unauthorized actions
- **Audit requirements:** Every tool call must be logged with: timestamp, tool name, inputs, outputs, agent reasoning trace

**The AgentOps Monitoring Requirements:**
1. **Trace capture:** Full reasoning trace for every agent invocation (Thought → Action → Observation → ...)
2. **Tool call audit log:** Every tool call with inputs/outputs; tamper-evident (append-only log)
3. **Authority monitoring:** Alert when an agent attempts a tool call outside its defined authority matrix
4. **Loop detection:** Alert when an agent executes more than N tool calls in a single invocation
5. **Escalation tracking:** Monitor human-in-the-loop escalation rate; too low = agent overconfident
6. **Cost tracking:** Tokens × tool calls × compute = total agent run cost; track per invocation and aggregate

**Figure:** *AgentOps monitoring layer diagram.* ReAct agent trace on left (Thought → Action → Observation → Thought → ...). On the right, four monitoring sidecars: Trace Capture (records every step), Tool Audit Log (append-only), Authority Monitor (checks each tool call against authority matrix), Loop Detector (counts tool calls per invocation). Each sidecar connects to CloudWatch. This visualizes AgentOps as a set of monitoring overlays on the agent execution trace.

**Notes:** "Loop detection is the one teams forget until it burns them. An agent with a bug in its tool-call logic can enter a loop—calling the same tool with the same arguments 40 times, spending 20,000 tokens, and achieving nothing. At 40 loops × 500 tokens each = 20,000 tokens × $0.003/token = $60 per stuck agent invocation. At scale, this is catastrophic. Set a hard limit: max 15 tool calls per agent run."

---

## Slide 8 — Bedrock Agents: Trace Logging in Practice
**Layout:** Trace capture implementation with CloudWatch integration

**Content:**
**Capturing Bedrock Agent Traces:**

```python
import boto3
import json
import time
from datetime import datetime

bedrock_agent = boto3.client('bedrock-agent-runtime')
logs = boto3.client('logs')

def invoke_with_full_trace(agent_id, alias_id, session_id, input_text):
    """Invoke Bedrock Agent with full trace capture."""
    response = bedrock_agent.invoke_agent(
        agentId=agent_id,
        agentAliasId=alias_id,
        sessionId=session_id,
        inputText=input_text,
        enableTrace=True  # CRITICAL: must be True for trace capture
    )
    
    trace_events = []
    final_response = ""
    
    for event in response['completion']:
        if 'chunk' in event:
            final_response += event['chunk']['bytes'].decode()
        
        if 'trace' in event:
            trace = event['trace']['trace']
            trace_events.append({
                'timestamp': datetime.utcnow().isoformat(),
                'trace_type': list(trace.keys())[0],
                'trace_data': trace
            })
            
            # Log to CloudWatch Logs for audit trail
            logs.put_log_events(
                logGroupName='/northstar/agents/customer-service',
                logStreamName=session_id,
                logEvents=[{
                    'timestamp': int(time.time() * 1000),
                    'message': json.dumps(trace_events[-1])
                }]
            )
    
    return final_response, trace_events
```

**Key design decision:** `enableTrace=True` doubles the response payload size and adds ~200ms latency. For NorthStar, this is acceptable — audit completeness is a requirement, not a nice-to-have.

**Figure:** *Agent trace in CloudWatch Logs Insights.* Screenshot-style mockup showing CloudWatch Logs Insights query results. Query: `fields @timestamp, trace_type, trace_data.orchestrationTrace.rationale.text | filter trace_type = 'orchestrationTrace' | sort @timestamp asc`. Results: table showing three rows — rationale text for each Thought step in the agent's ReAct trace. Demonstrates that the agent's full reasoning is captured and queryable.

**Notes:** "Storing full traces in CloudWatch Logs gives you a queryable audit trail. When a customer service agent makes a decision that a customer disputes, you can run this Logs Insights query and reconstruct the agent's reasoning step by step. This is your legal protection and your debugging tool."

---

## Slide 9 — NorthStar AgentOps: The Customer Service Agent Dashboard
**Layout:** Operational dashboard for the NorthStar Customer Service Agent

**Content:**
**NorthStar Customer Service Agent — Operational Dashboard:**

**Session-level metrics (per agent run):**
- Session duration: P50: 4.2s, P90: 12.8s, P99: 47.3s
- Tool calls per session: P50: 3, P90: 7, P99: 14 (hard limit: 15)
- Tokens per session: P50: 1,240, P90: 3,100, P99: 8,900
- Cost per session: P50: $0.004, P90: $0.009, P99: $0.027

**System-level metrics (rolling 24h):**
- Total sessions: 847
- Sessions exceeding 15 tool calls (loop detection): 2 (0.2%) — both investigated
- Human escalation rate: 8.3% — within target (5-15%)
- Tool failure rate (tool call returned error): 1.1%
- Resolution rate (session completed without escalation): 91.7%

**Alerts active:**
- 🔴 HIGH: Session ID a7f3e2 — 47s duration, 14 tool calls — investigating
- 🟡 WARN: Tool failure rate trending up (1.1% vs. 0.7% last week) — order_lookup_tool

**Figure:** *AgentOps operational dashboard mockup.* Six metric panels in a 2×3 grid. Top row: session duration distribution (histogram), tool calls per session (histogram), cost per session (box plot). Bottom row: 24h sessions timeline (area chart by hour), human escalation rate (gauge: green zone 5-15%), tool failure rate by tool (bar chart highlighting order_lookup_tool in amber). Two alert banners at the top in red and amber. Professional operational look.

**Notes:** "The order_lookup_tool failure rate increase is exactly the kind of signal that AgentOps monitoring surfaces. Without this dashboard, you'd never notice that a backend service is starting to degrade — you'd just see customer satisfaction scores drop in a few weeks. With this dashboard, you catch it today and fix the underlying issue before it becomes a customer-facing problem."

---

## Slide 10 — The XOps CI/CD Landscape: All Four Layers
**Layout:** Unified CI/CD view across all XOps layers

**Content:**
**What CI/CD Looks Like for Each XOps Layer:**

**DataOps CI/CD:**
- Trigger: Glue job code change in Git
- Pipeline: Unit tests → integration test (sample data) → staging deploy → production deploy
- Artifact: Glue job scripts in S3
- Rollback: Previous Glue job script version

**MLOps CI/CD:**
- Trigger: New data available or model code change
- Pipeline: Train → evaluate → gate check → register → (manual approval) → deploy
- Artifact: Model artifact in Model Registry
- Rollback: Previous model version in registry → endpoint update

**LLMOps CI/CD:**
- Trigger: Prompt template change or RAG index update
- Pipeline: Prompt test suite (RAGAS evaluation on test set) → staging evaluate → production deploy
- Artifact: Prompt version in Git + RAG index in Bedrock Knowledge Base
- Rollback: Previous prompt version + previous index snapshot

**AgentOps CI/CD:**
- Trigger: Agent configuration change, tool code change, or authority matrix update
- Pipeline: Integration tests (test agent with simulated tool responses) → trace review → staging evaluate → production deploy
- Artifact: Agent version in Bedrock Agents console
- Rollback: Previous agent alias pointing to previous agent version

**Figure:** *Four-layer CI/CD comparison table.* Same structure as above, formatted as a visual table with four rows (DataOps, MLOps, LLMOps, AgentOps) and five columns (Trigger, Pipeline, Artifact, Rollback, Approver). Color-coded by XOps layer. The table communicates: each layer has its own CI/CD pattern, but they follow the same principles.

**Notes:** "The key insight is that every layer has the same CI/CD structure: trigger, pipeline, artifact, rollback. What changes is what the artifact is and how you evaluate it. For MLOps, the artifact is a model, and you evaluate AUC. For LLMOps, the artifact is a prompt template, and you evaluate RAGAS faithfulness. The discipline is the same; the tools differ."

---

## Slide 11 — LLMOps Evaluation: Automated Quality Checks
**Layout:** RAGAS evaluation in a CI/CD pipeline

**Content:**
**Running RAGAS in CI/CD for NorthStar Offer Generation:**

```python
# In the prompt CI/CD pipeline — evaluate before production deploy
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_recall
from datasets import Dataset

def evaluate_prompt_version(prompt_version: str, test_set: list[dict]):
    """Gate check: evaluate new prompt before production deploy."""
    
    # Generate responses using new prompt version
    responses = []
    for test_case in test_set:
        response = run_offer_generation(
            customer_data=test_case['customer_data'],
            prompt_version=prompt_version
        )
        responses.append({
            'question': test_case['query'],
            'answer': response.text,
            'contexts': response.retrieved_contexts,
            'ground_truths': [test_case['expected_answer']]
        })
    
    # RAGAS evaluation
    dataset = Dataset.from_list(responses)
    results = evaluate(dataset, metrics=[
        faithfulness,       # hallucination check
        answer_relevancy,   # relevance to customer query
        context_recall      # RAG retrieval coverage
    ])
    
    # Gate criteria
    gate_pass = (
        results['faithfulness'] >= 0.95 and
        results['answer_relevancy'] >= 0.85 and
        results['context_recall'] >= 0.80
    )
    
    print(f"Faithfulness: {results['faithfulness']:.3f} (gate: ≥0.95)")
    print(f"Answer Relevancy: {results['answer_relevancy']:.3f} (gate: ≥0.85)")
    print(f"Context Recall: {results['context_recall']:.3f} (gate: ≥0.80)")
    print(f"Gate: {'PASS ✅' if gate_pass else 'FAIL ❌'}")
    
    return gate_pass, results
```

**Figure:** *RAGAS CI/CD gate diagram.* Prompt template change in Git → trigger pipeline → RAGAS evaluation on test set (50 test cases) → metrics computed → gate check (≥0.95 / ≥0.85 / ≥0.80) → pass → production deploy / fail → alert to ML team. Sample output shown: "faithfulness: 0.97 ✅, answer_relevancy: 0.91 ✅, context_recall: 0.83 ✅ → GATE PASSED."

**Notes:** "The 50-test-case test set is the LLMOps equivalent of your unit test suite. When you change the prompt template, these 50 cases run automatically and gate the deploy. The gate criteria (0.95 faithfulness) were set during the AISDLC Stage 6 evaluation — they're not arbitrary. They're the minimum performance that the business use case requires."

---

## Slide 12 — The XOps Observability Stack for NorthStar
**Layout:** Complete observability architecture across all three NorthStar AI systems

**Content:**
**NorthStar XOps Observability Architecture:**

| System | Primary Monitoring | Quality Monitoring | Cost Monitoring |
|--------|-------------------|-------------------|----------------|
| XGBoost Churn | Model Monitor (data drift, quality drift) | AUC tracked weekly; SHAP drift | SageMaker endpoint cost/hour |
| RAG Offer Gen | Response latency, error rate | RAGAS faithfulness (sampled 5%) | Daily token spend + budget alert |
| ReAct Agent | Session duration, tool call count, escalation rate | Resolution rate; trace quality review | Per-session cost tracking |

**Unified CloudWatch Dashboard — NorthStar AI Platform:**
- **Section 1 — Data Platform Health:** Glue pipeline success rate, Feature Store freshness, data quality gate pass rate
- **Section 2 — Model Health:** Churn model AUC trend, endpoint latency, endpoint availability
- **Section 3 — LLM System Health:** RAG latency, faithfulness score, token cost
- **Section 4 — Agent Health:** Session volume, escalation rate, tool failure rate, cost per session
- **Section 5 — Platform Economics:** Total daily AI cost vs. budget, cost breakdown by system

**Figure:** *NorthStar unified monitoring dashboard architecture.* Five-section layout (matching the content above). Each section: 2-3 representative metric tiles. System-health indicators: traffic-light status for each section (all green for normal state). Total platform cost in bottom-right: "$47.23 today vs. $52.00 budget (90.8%)" in green. This is the "single pane of glass" view for the platform operator.

**Notes:** "The unified dashboard is the operational target. Right now, after Labs 1-3, you have three separate AI systems with no shared observability. By Lab 6, you'll have this unified view. The platform operator — whether that's you, a future ML engineer, or a DevOps team — should be able to see the health of the entire platform in one place."

---

## Slide 13 — When Things Go Wrong: XOps Incident Response
**Layout:** Incident response playbook for each XOps layer

**Content:**
**AI System Incident Response by Layer:**

**DataOps Incident: Data pipeline failure**
1. Alert fires: Glue job failed (CloudWatch alarm)
2. Triage: Check CloudWatch logs for error; identify failing step
3. Impact assessment: Is downstream data stale? How long has it been stale?
4. Remediation: Fix the root cause; manually trigger missed run; verify data quality gate passes
5. Post-incident: Add test case to prevent recurrence; update runbook

**MLOps Incident: Model quality degradation**
1. Alert fires: AUC dropped below 0.68 threshold (10% below gate)
2. Triage: Data drift? Model drift? Feature drift? Check Model Monitor report
3. Impact assessment: How many churn predictions affected? What's the business impact?
4. Remediation: Option A: rollback to previous model version; Option B: trigger emergency retraining
5. Post-incident: Root cause analysis; adjust monitoring thresholds if needed

**LLMOps Incident: RAG faithfulness drop**
1. Alert fires: RAGAS faithfulness score drops below 0.90 on sampled evaluation
2. Triage: Prompt change? Index update? Model change? Context window issue?
3. Impact assessment: What % of offers affected? Customer impact?
4. Remediation: Roll back prompt version or index version (whichever changed most recently)
5. Post-incident: Add failing test cases to evaluation suite

**Figure:** *Incident response timeline diagram.* Three horizontal swim lanes (DataOps, MLOps, LLMOps). Each lane: a timeline from Alert to Resolved, with named steps. Time estimates: DataOps incident: 45 min typical resolution; MLOps incident: 2-4 hours; LLMOps incident: 1-2 hours. MTTR (Mean Time to Recover) shown for each layer as a metric.

**Notes:** "Every AI system has incidents. The question is how fast you recover and whether you learn from them. The post-incident step is not optional — if you don't add a test case to prevent recurrence, you'll have the same incident again in 3 months. In production systems, your test suite is your institutional memory of what has gone wrong before."

---

## Slide 14 — XOps Tooling Landscape
**Layout:** Complete tool map for the NorthStar XOps stack

**Content:**
**NorthStar XOps Tooling by Layer:**

**DataOps Tools:**
- AWS Glue: ETL jobs, orchestration, crawlers
- AWS EventBridge: Event-driven triggers
- Amazon CloudWatch: Pipeline monitoring and alerts
- SageMaker Feature Store: Feature versioning and dual-path serving
- AWS Glue Data Catalog: Data lineage and schema registry

**MLOps Tools:**
- MLflow (on SageMaker): Experiment tracking and model comparison
- SageMaker Pipelines: Automated training pipeline
- SageMaker Model Registry: Model versioning and approval workflow
- SageMaker Model Monitor: Data drift and quality drift detection
- AWS CodePipeline + CodeBuild: CI/CD orchestration

**LLMOps Tools:**
- Amazon Bedrock: Foundation model API (Claude 3.5 Sonnet)
- Bedrock Knowledge Bases: RAG index management
- Bedrock Guardrails: Safety filtering
- RAGAS: Automated RAG evaluation
- Git (prompt templates): Prompt version control

**AgentOps Tools:**
- Bedrock Agents: Agent orchestration
- CloudWatch Logs: Full trace capture and storage
- CloudWatch Logs Insights: Trace query and analysis
- Step Functions: Complex workflow coordination

**Cross-cutting:**
- AWS IAM: Access control across all layers
- Amazon S3: Artifact storage for all layers
- AWS Terraform: IaC for all infrastructure

**Figure:** *XOps tool map.* Four columns (DataOps, MLOps, LLMOps, AgentOps), each with tool cards. Cross-cutting tools at the bottom spanning all columns. Color-coded: AWS services in orange/black, open-source tools (MLflow, RAGAS, Git) in teal. This is the NorthStar technology map for XOps.

**Notes:** "This tool map is the technology architecture for your labs. Every tool in this diagram appears in at least one lab. The cross-cutting tools — IAM, S3, Terraform — are in every lab. When you look at this map, you should be able to point to which lab you configured each tool. By Lab 7, you'll have configured all of them."

---

## Slide 15 — XOps Maturity: Where This Course Takes You
**Layout:** Before/after XOps maturity comparison for NorthStar

**Content:**
**NorthStar XOps: Before vs. After the Lab Sequence**

| Layer | After Lab 3 (today) | After Lab 7 (end of semester) |
|-------|---------------------|-------------------------------|
| **DataOps** | Scheduled jobs, basic alerts | + Testing, quality contracts, drift alerts |
| **MLOps** | Manual training, registry | + CI/CD pipeline, automated retraining, rollback |
| **LLMOps** | Bedrock KB deployed | + Prompt versioning, RAGAS CI/CD, cost tracking |
| **AgentOps** | Agent deployed, no monitoring | + Full trace logging, authority monitoring, loop detection |
| **FinOps** | No cost governance | + Per-system budgets, cost/value ratio tracked |
| **Business Value** | No ROI measurement | + Churn reduction tracked, offer lift measured |

**Figure:** *XOps maturity radar chart (dual view).* Same radar chart as L10 Slide 9, now showing all four XOps layers as dimensions. After Lab 3 (light blue): strong data capabilities, weak automation. After Lab 7 (navy): full polygon approaching Level 3 on all dimensions. The visual progress between the two states tells the story of the lab sequence.

**Notes:** "This radar is the 'before' state you're currently in. By Lab 7, the goal is to have closed every gap. When you go to your first job as a production ML engineer or AI platform engineer, this is the XOps maturity map you'll use to assess your employer's systems and identify where to focus improvement effort."

---

## Slide 16 — Key Takeaways + What's Next
**Layout:** Takeaways + L12 preview

**Content:**
**Key Takeaways:**
1. LLMOps requires its own operational discipline — MLOps tooling doesn't cover prompt versioning, RAG index operations, or LLM-specific evaluation (RAGAS)
2. Prompt templates and RAG indexes are production artifacts — they require version control, CI/CD, and automated evaluation gates, just like model weights
3. AgentOps must address agent-specific risks: trace logging, authority monitoring, loop detection, and escalation rate tracking
4. Guardrails are not optional for production LLM systems — implement at both input and output; monitor trigger rates to detect attacks
5. The NorthStar XOps stack spans 13+ tools across 4 operational layers — unified observability (single CloudWatch dashboard) is the operational goal

**Next Session (Tue Oct 13):**
- Topic: Testing & Evaluation I — testing strategy for AI systems; unit, integration, and system tests
- Reading due: *Testing AI Systems* — "Principles" through "Integration Testing"
- Lab 3 due Sat Oct 17 — 9 days; please attend office hours if you're blocked

**Figure:** *XOps stack recap visual.* Four-layer stack (DataOps, MLOps, LLMOps, AgentOps) with the key operational tool for each layer highlighted. Five takeaways as a numbered list alongside the stack. Lab 3 countdown in amber.

**Notes:** Final Lab 3 check-in: "Show of hands — who has successfully invoked the SageMaker endpoint and gotten a churn prediction back?" This is the minimum viability check for Lab 3. For Lab 3 Options A/B (RAG and Agent): "Who has a working Knowledge Base with at least one successful query?" Assess where the cohort is and announce office hours support.
