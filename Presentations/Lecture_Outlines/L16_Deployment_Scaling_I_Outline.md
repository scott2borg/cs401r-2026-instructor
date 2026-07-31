---
lecture: L16
title: Deployment & Scaling I — Inference Architecture
date: Tuesday, October 27, 2026
week: 9
arc: Build
reading_due: "Deployment at Scale — Inference Architecture through Multi-Model Endpoints"
lab_due: "Lab 4 due Sat Oct 31 (4 days); Lab 5 due Sat Nov 14"
slides_target: 15
---

# L16: Deployment & Scaling I — Inference Architecture
**Tuesday, October 27, 2026 | CS 401R: Engineering Production AI Systems | Fall 2026**

A model that can't reliably serve predictions at scale isn't a production AI system — it's a prototype with a SageMaker endpoint attached. Learn to design inference architecture that meets latency SLAs, handles traffic spikes, and minimizes cost.

**Reading Due:** *Deployment at Scale* — "Inference Architecture" through "Multi-Model Endpoints"
**Lab 4 Due:** Sat Oct 31 (4 days)

---

## Slide 1 — Title
**Layout:** Left dark panel + right inference serving architecture diagram

**Content:**
- Deployment & Scaling I: Inference Architecture
- CS 401R · Lecture 16 · Tuesday, October 27, 2026
- ⚠️ Lab 4 Due Saturday — 4 Days

**Figure:** *Inference serving architecture overview.* Client request → API Gateway → SageMaker Endpoint (load balancer) → Instance pool (3 instances shown). One instance box expanded to show internals: Model Server, Memory-loaded model, CPU core allocation. Request/response times annotated: network: 8ms, container processing: 20ms, total: 28ms. The diagram establishes the anatomy of the serving architecture for the lecture.

**Notes:** "Lab 4 is due Saturday. Four days. If you have a working SageMaker Pipeline but aren't yet connected to CodePipeline, you're in a manageable position — the CodePipeline connection is the final integration step and typically takes 2-3 hours with the starter code. If you don't have a working pipeline at all, come to office hours today."

---

## Slide 2 — The Inference Architecture Decision Tree
**Layout:** Decision framework for inference architecture selection

**Content:**
**Choosing the Right Inference Architecture:**

**Question 1: Real-time or batch?**
- Need response in < 5 seconds: Real-time endpoint
- Processing a fixed dataset (daily/weekly/monthly): Batch Transform
- Need response in < 1 hour, but not instant: Async Inference

**Question 2 (if real-time): How variable is the traffic?**
- Steady, predictable traffic: Fixed instance count (cheaper)
- Variable/spiky traffic: Auto-scaling endpoint
- Unpredictable with long idle periods: Serverless Inference

**Question 3: How many models?**
- One model, one endpoint: Standard endpoint
- Multiple related models (same framework, similar size): Multi-model endpoint (MME)
- Models for different customers/tenants: Multi-model endpoint with tenant routing

**NorthStar Inference Architecture Choices:**
| System | Pattern | Reason |
|--------|---------|--------|
| Churn Model (real-time) | Auto-scaling endpoint | Variable daily traffic; 1-8 instances |
| Churn Model (batch) | Batch Transform | Monthly 500K scoring; cost-efficient |
| Offer Generation | Bedrock (managed) | No endpoint to manage; token pricing |
| Agent | Bedrock (managed) | Stateful; managed by Bedrock |

**Figure:** *Decision tree flowchart.* Binary decision tree with three levels: Real-time/Batch (Level 1), Traffic variability (Level 2, real-time branch), Number of models (Level 3). Each leaf node: endpoint type with NorthStar example. Four outcome leaves: Standard endpoint, Auto-scaling endpoint, Batch Transform, Serverless Inference. The decision tree is clean, readable, and actionable.

**Notes:** "The decision tree is the first thing to work through when designing a new AI system's inference architecture. Starting with 'we'll use a SageMaker endpoint' without working through the decision tree leads to over-provisioned, expensive infrastructure or under-provisioned, unreliable serving. Work through the tree first."

---

## Slide 3 — Serverless Inference: The Low-Traffic Option
**Layout:** Serverless Inference architecture and NorthStar use case

**Content:**
**SageMaker Serverless Inference:**

Serverless endpoints scale to zero when idle and spin up on demand. Unlike auto-scaling, there are no instances running when traffic is zero.

**Cost model:**
- Standard endpoint: Instance cost × hours (even when idle)
- Serverless: Pay per invocation + compute time only

**NorthStar Serverless Use Case:** The Customer Service Agent endpoint (if not using Bedrock) has highly variable traffic: peak 100 requests/hour during business hours, near-zero overnight.

```python
from sagemaker.serverless import ServerlessInferenceConfig

serverless_config = ServerlessInferenceConfig(
    memory_size_in_mb=2048,  # Memory allocated per invocation
    max_concurrency=20       # Max concurrent requests (not instances)
)

predictor = model.deploy(
    serverless_inference_config=serverless_config,
    endpoint_name='northstar-agent-serverless'
)
```

**Serverless tradeoffs:**
- ✅ Zero cost when idle (large saving for overnight hours)
- ✅ No instance management; scales automatically
- ❌ Cold start latency (1-5 seconds for first request after idle period)
- ❌ Memory limited (max 6GB); not suitable for large models
- ❌ Not suitable for consistent high-throughput (instance-based is cheaper above ~50 req/min)

**Figure:** *Serverless vs. instance-based cost comparison.* Dual-axis chart. X-axis: requests per minute (0 to 500). Y-axis: hourly cost. Serverless line: starts at $0 (when idle), rises linearly with request rate, flattens at $0.15/hr at 500 req/min. Instance-based (1× ml.m5.large) line: flat at $0.115/hr regardless of load. Intersection point: ~200 req/min. "Serverless better" region (left of intersection), "Instance-based better" region (right). The crossover communicates: choose based on load profile.

**Notes:** "For NorthStar's Customer Service Agent, which uses Bedrock (not a custom model endpoint), serverless isn't directly applicable — Bedrock is already managed. But the cost model comparison applies to any custom model you deploy. The key question is: what percentage of the time is your endpoint idle? If > 30% idle, serverless is likely cheaper."

---

## Slide 4 — Async Inference: The Middle Ground
**Layout:** Async inference architecture for large-model workloads

**Content:**
**SageMaker Asynchronous Inference:**

Async inference accepts requests, queues them, processes in the background, and writes outputs to S3. The client polls for completion or receives an SNS notification.

**When to use Async Inference:**
- Large payloads (> 6MB) that exceed synchronous limits
- Long processing times (1-15 minutes) — too long for synchronous timeout
- Batch-like workloads with SLA measured in minutes, not seconds
- Models with high per-request compute cost that justify queueing and processing in batches

**NorthStar potential Async use case:** If NorthStar deploys a large multimodal model (image + text) for product recommendation, processing one high-res product image might take 45 seconds. Async is the right pattern.

```python
predictor = model.deploy(
    async_inference_config=AsyncInferenceConfig(
        output_path='s3://northstar-artifacts/async-inference-output/',
        notification_config={
            'SuccessTopic': 'arn:aws:sns:us-east-1:...:northstar-inference-complete',
            'ErrorTopic': 'arn:aws:sns:us-east-1:...:northstar-inference-error'
        },
        max_concurrent_invocations_per_instance=4
    )
)

# Client invokes and gets a job handle
response = predictor.predict_async(data=payload)
job_handle = response.output_path  # S3 path where result will appear

# Client polls or waits for SNS notification
```

**Figure:** *Async inference flow diagram.* Client → POST to endpoint (returns immediately with job handle) → SageMaker queue. Background: SageMaker pulls from queue → processes → writes to S3. SNS notification fires → client reads result from S3. Timeline: client wait time = near-zero (just the POST). Processing time: 1-5 min (async). Contrasts with synchronous: client blocks for entire processing duration.

**Notes:** "Async inference solves the 30-second timeout problem that AWS API Gateway imposes on synchronous HTTP calls. If your model takes 2 minutes to process a request, you can't use a synchronous endpoint — the API Gateway will time out after 29 seconds. Async moves the result delivery out-of-band via S3 + SNS, allowing arbitrarily long processing times."

---

## Slide 5 — Multi-Model Endpoints: Serving at Scale
**Layout:** Multi-model endpoint architecture for multi-tenant AI

**Content:**
**The Multi-Model Endpoint (MME) Pattern:**

Problem: NorthStar runs 5 regional churn models (Northeast, Southeast, Midwest, Southwest, Pacific), each trained on regional customer data. Hosting 5 separate endpoints would cost 5× the endpoint price.

Multi-model endpoints serve multiple models behind a single endpoint, loading and unloading model artifacts dynamically from S3 based on traffic.

```python
# Upload 5 regional models to a single S3 prefix
for region in ['NE', 'SE', 'MW', 'SW', 'PAC']:
    model_path = f's3://northstar-artifacts/models/churn-{region}/model.tar.gz'
    upload_model(f'models/churn-{region}.tar.gz', model_path)

# Single endpoint serves all 5 models
multi_model_predictor = deploy_multi_model_endpoint(
    model_data_prefix='s3://northstar-artifacts/models/',
    instance_type='ml.m5.2xlarge',  # Larger instance for multiple models in memory
    instance_count=2
)

# Request routing: specify which model to invoke
response = multi_model_predictor.predict(
    data=customer_features,
    target_model='churn-NE.tar.gz'  # Routes to Northeast churn model
)
```

**MME economics for NorthStar:**
- 5 separate endpoints: 5× $0.115/hr = $0.575/hr = $414/month
- Multi-model endpoint (2× ml.m5.2xlarge): $0.46/hr = $332/month
- Savings: $82/month (20% cost reduction)

**Figure:** *Multi-model endpoint architecture diagram.* Single SageMaker endpoint with two instances. Model cache in each instance: up to 4 models loaded in memory simultaneously. S3 model library: 5 model artifacts (churn-NE, churn-SE, churn-MW, churn-SW, churn-PAC). Request comes in with target_model header → endpoint routes to correct model → if model not in cache (cache miss) → load from S3 (cold load: ~2-5 seconds). The diagram shows: MME = shared infrastructure with dynamic model routing.

**Notes:** "The cache miss cold load is the MME gotcha. When a model is in the cache, request latency is normal (<50ms). When a model needs to be loaded from S3 (on the first request or after being evicted from the cache), latency spikes to 2-5 seconds. For high-traffic models, this is fine — they stay in cache. For rarely-requested models (e.g., the Pacific region model), the first request after a long idle period will experience this spike. Pre-warm by sending a warm-up request after each deployment."

---

## Slide 6 — Inference Optimization: Reducing Latency and Cost
**Layout:** Inference optimization techniques with NorthStar benchmarks

**Content:**
**The Inference Optimization Toolkit:**

**1. Model compilation (Neuron / TorchScript / ONNX):**
Compile your model to an optimized binary format before deployment. For XGBoost: use ONNX export to reduce inference time by 20-30%.
```python
import onnxmltools
onnx_model = onnxmltools.convert_xgboost(xgb_model)
onnxmltools.save_model(onnx_model, 'model.onnx')
# Compiled model: 18ms inference vs. 24ms native
```

**2. Instance type selection:**
For CPU-bound models (XGBoost), compute-optimized instances (ml.c5) outperform general-purpose (ml.m5) by 15-20% at similar cost.

**3. Feature preprocessing:** Move feature preprocessing off the serving path. Store precomputed feature vectors in the Feature Store; retrieve them at prediction time. Avoid re-computing RFM at every request.

**4. Caching predictions:** For low-cardinality customer segments, cache predictions for the segment. Cache miss: full inference (~25ms). Cache hit: < 1ms. Trade-off: stale predictions if model updates.

**5. Batch request handling:** Use SageMaker's `MultiRecord` strategy in Batch Transform to process multiple records per container invocation, amortizing fixed overhead.

**NorthStar optimization results (XGBoost Churn Model):**

| Optimization | P50 Latency | P99 Latency | Cost/1M requests |
|-------------|------------|------------|-----------------|
| Baseline (ml.m5.large, native) | 28ms | 145ms | $3.20 |
| + ONNX compilation | 21ms | 112ms | $3.20 |
| + ml.c5.large instance | 18ms | 92ms | $3.05 |
| + Feature caching (50% hit rate) | 12ms | 80ms | $1.80 |

**Figure:** *Latency optimization waterfall.* Four bars: Baseline (28ms), ONNX (21ms, -25%), c5 instance (18ms, -36%), Feature caching (12ms, -57%). Each step labeled with the optimization applied and % improvement. Horizontal SLA line at 200ms — all optimizations well within SLA. Secondary chart: cost/1M requests showing parallel reduction. The visual story: each optimization layers on the previous, compounding improvements.

**Notes:** "Feature caching has the biggest single impact in this example — going from 28ms to 12ms — but it only works for workloads with predictable, recurring feature requests (same customer ID queried repeatedly). For NorthStar's churn use case, the same customer is scored daily with updated features, so cache hit rates depend on how frequently features change. In practice, daily customers with stable features might have 40-60% cache hit rates."

---

## Slide 7 — SageMaker Inference Recommender
**Layout:** Inference Recommender workflow and NorthStar results

**Content:**
**SageMaker Inference Recommender: Data-Driven Instance Selection**

Instead of guessing the right instance type, Inference Recommender benchmarks your model across a range of instance types and gives you a cost/latency tradeoff chart.

**How to run it:**
```python
sagemaker_client = boto3.client('sagemaker')

# Register your model in Model Registry first (required)
# Then run Inference Recommender
job = sagemaker_client.create_inference_recommendations_job(
    JobName='northstar-churn-recommender-v3',
    JobType='Default',  # 'Advanced' for extended benchmarking
    RoleArn=SAGEMAKER_ROLE_ARN,
    InputConfig={
        'ModelPackageVersionArn': model_package_arn,
        'SupportedEndpointType': 'RealTime',
        'TrafficPattern': {
            'TrafficType': 'PHASES',
            'Phases': [
                {'InitialNumberOfUsers': 1, 'SpawnRate': 1, 'DurationInSeconds': 120},
                {'InitialNumberOfUsers': 5, 'SpawnRate': 5, 'DurationInSeconds': 120}
            ]
        },
        'ResourceLimit': {'MaxNumberOfTests': 10, 'MaxParallelOfTests': 3}
    }
)
```

**Hypothetical NorthStar Inference Recommender results:**

| Instance Type | P50 Latency | P99 Latency | Cost/hr | Recommended? |
|--------------|------------|------------|---------|-------------|
| ml.t2.medium | 35ms | 210ms | $0.058 | ❌ P99 SLA miss |
| ml.m5.large | 28ms | 145ms | $0.115 | ✅ Baseline |
| ml.c5.large | 21ms | 98ms | $0.110 | ✅ Better latency, same cost |
| ml.c5.xlarge | 18ms | 82ms | $0.220 | ⚠️ 2× cost for modest gain |
| ml.c5.2xlarge | 16ms | 75ms | $0.440 | ❌ 4× cost for 5% gain |

**Recommendation:** ml.c5.large — best P99 latency within SLA at lowest cost.

**Figure:** *Inference Recommender scatter plot.* X-axis: cost/hour. Y-axis: P99 latency (ms). Each instance type plotted as a labeled dot. Horizontal line: P99 SLA (200ms). Vertical line: cost budget ($0.20/hr). "Ideal zone" highlighted (bottom-left quadrant). ml.c5.large in ideal zone, labeled "Recommended." ml.t2.medium above SLA line (fail). ml.c5.2xlarge right of cost budget line. The scatter plot is exactly the output format of Inference Recommender.

**Notes:** "Run Inference Recommender once for each model before making the instance selection decision. It takes 30-60 minutes and gives you data-driven justification for your choice. The results belong in your deployment documentation: 'We chose ml.c5.large based on Inference Recommender benchmark results showing P99 latency of 98ms at $0.110/hr — the best cost/latency tradeoff within our SLA.'"

---

## Slide 8 — Load Testing AI Endpoints
**Layout:** Load testing strategy and tooling for NorthStar

**Content:**
**Why Load Test Before Production?**

Load testing answers: Can this endpoint handle peak production traffic? What breaks first?

**NorthStar Peak Traffic Estimate:**
- 400 stores × 1,000 customers/store × 5% who trigger real-time scoring event = 20,000 real-time requests/day
- Peak: Monday morning (store opening, weekend purchase events processed): ~500 requests in the first 15 minutes = ~33 req/min
- Stress test target: 2× peak = 66 req/min (safety margin)

**Load testing with Locust:**
```python
# locustfile.py
from locust import HttpUser, task, between
import json

class ChurnPredictionUser(HttpUser):
    wait_time = between(0.5, 2.0)  # Think time between requests
    
    @task
    def predict_churn(self):
        payload = {
            "features": [[
                30, 5, 250.0, 3, 0.75, 4  # [recency, freq, monetary, cat_div, ...]
            ]]
        }
        with self.client.post(
            "/invocations",
            json=payload,
            headers={"Content-Type": "application/json"},
            catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"Got status {response.status_code}")
            elif response.elapsed.total_seconds() > 0.2:
                response.failure(f"Response too slow: {response.elapsed.total_seconds():.2f}s")

# Run: locust -f locustfile.py --host=https://endpoint-url --users=50 --spawn-rate=5
```

**Load test results to look for:**
- At what request rate does P99 latency exceed 200ms? (Latency saturation point)
- At what request rate does error rate exceed 1%? (Error saturation point)
- Does auto-scaling engage before saturation? (Should it engage first?)

**Figure:** *Load test results chart.* X-axis: requests per minute (0 to 120). Y-axis (left): P99 latency (ms); Y-axis (right): error rate (%). Two series: Latency (rises from 85ms at 10 req/min to 210ms at 90 req/min, SLA violation zone marked). Error rate (near 0% up to 80 req/min, spikes at 90+ req/min). Auto-scaling trigger point marked at 70 req/min — latency stays below SLA because scaling engages before saturation. The chart validates: auto-scaling keeps the endpoint within SLA under expected peak load.

**Notes:** "The auto-scaling engagement point in the load test is the critical validation. If auto-scaling engages at 70 req/min and latency starts degrading at 90 req/min, you have a 20 req/min buffer before SLA violation. If auto-scaling doesn't engage until 90 req/min (same as saturation), you have no buffer and will violate SLA during scaling events. The 60-second scale-out cooldown means you have 60 seconds of potential SLA violation during a scale-out event — that's acceptable if your peak ramp is gradual."

---

## Slide 9 — SageMaker Model Monitor: Production Quality Gates
**Layout:** Model Monitor setup and NorthStar configuration

**Content:**
**SageMaker Model Monitor: Automated Production Quality Surveillance**

Model Monitor runs as a scheduled SageMaker Processing Job, comparing production data and predictions to a training baseline.

**Monitor types:**
1. **Data Quality Monitor:** Detects drift in input feature distributions (PSI, Jensen-Shannon divergence)
2. **Model Quality Monitor:** Detects changes in prediction quality (requires labels — delayed)
3. **Bias Drift Monitor:** Detects changes in fairness metrics across demographic groups
4. **Feature Attribution Drift Monitor:** Detects changes in which features drive predictions (SHAP drift)

**NorthStar Data Quality Monitor setup:**
```python
from sagemaker.model_monitor import DataCaptureConfig, DefaultModelMonitor

# Step 1: Enable data capture on the endpoint
data_capture_config = DataCaptureConfig(
    enable_capture=True,
    sampling_percentage=20,  # Capture 20% of requests
    destination_s3_uri='s3://northstar-monitoring/data-capture/'
)

# Step 2: Create baseline from training data
monitor = DefaultModelMonitor(role=SAGEMAKER_ROLE_ARN)
baseline_job = monitor.suggest_baseline(
    baseline_dataset='s3://northstar-processed/training/churn-features-baseline.csv',
    dataset_format=DatasetFormat.csv(header=True)
)

# Step 3: Schedule monitoring (runs daily)
monitor.create_monitoring_schedule(
    monitor_schedule_name='northstar-churn-data-quality',
    endpoint_input=EndpointInput(
        endpoint_name='northstar-churn-prod',
        destination='/opt/ml/processing/input/endpoint'
    ),
    output_s3_uri='s3://northstar-monitoring/model-monitor-output/',
    statistics=baseline_job.baseline_statistics(),
    constraints=baseline_job.suggested_constraints(),
    schedule_cron_expression='cron(0 * ? * * *)'  # Hourly
)
```

**Figure:** *Model Monitor pipeline diagram.* SageMaker Endpoint (with data capture at 20%) → captured data to S3. Daily: Monitor Processing Job reads captured data + training baseline → computes PSI for each feature → compares to constraints → if violation: CloudWatch alert fires. Alert connects to SNS notification and retraining trigger (optional). Clean operational flow showing the automated surveillance loop.

**Notes:** "The 20% capture rate is a deliberate trade-off: high enough to detect drift (statistical power), low enough to not double your storage costs. At 500 requests/day, 20% capture = 100 samples/day. For PSI computation, 100 samples is statistically meaningful for most feature distributions. If you have very low traffic, increase capture rate to 50% or 100%."

---

## Slide 10 — Drift Detection: Reading the Monitor Output
**Layout:** Model Monitor output interpretation with NorthStar examples

**Content:**
**How to Read Model Monitor Output:**

Model Monitor produces two types of violations:
1. **Feature drift violation:** A feature distribution has changed significantly (PSI > threshold)
2. **Schema violation:** A feature is missing, has the wrong type, or has unexpected values

**Sample Model Monitor report for NorthStar:**
```json
{
  "monitoring_output": {
    "feature_drift": [
      {
        "feature": "recency_days",
        "baseline_mean": 42.3,
        "current_mean": 38.7,
        "psi": 0.08,
        "status": "InBounds"  // PSI < 0.10: no action needed
      },
      {
        "feature": "monetary_30d",
        "baseline_mean": 287.40,
        "current_mean": 412.80,
        "psi": 0.28,
        "status": "VIOLATION"  // PSI > 0.20: retrain trigger
      }
    ],
    "schema_issues": [],
    "recommendation": "RETRAIN — significant drift in monetary_30d"
  }
}
```

**Interpreting the monetary_30d drift:**
- Baseline (training) mean spend: $287 → Current mean: $413 (+44%)
- This is November — holiday shopping is driving higher spend
- Expected seasonal drift: this happens every year in Q4
- Response: **do NOT retrain** (the model should handle this; it's seasonal) → adjust drift alert thresholds for Q4

**The drift response decision framework:**
- Unexpected drift: investigate → retrain if root cause is distribution change
- Expected seasonal drift: document → adjust thresholds → monitor for anomalies within the seasonal range
- Missing feature drift: data pipeline issue → investigate ETL → fix source

**Figure:** *Drift report dashboard.* Model Monitor output shown as a feature table with: feature name, baseline mean/std, current mean/std, PSI value, status (green/red). monetary_30d row highlighted in red (violation). Below: time series chart of monetary_30d mean over 90 days, showing the seasonal Q4 spike. Annotation: "Expected Q4 seasonal spike — adjust threshold." The visual communicates: drift must be interpreted in context, not acted on mechanically.

**Notes:** "The Q4 seasonal drift is a real operational challenge for retail AI systems. Your churn model was trained on 12 months of data, including last Q4 — so it 'knows' about holiday shopping patterns. But Model Monitor will still flag the November spending spike as drift because it's comparing to the 12-month average baseline, not to last November specifically. Add a seasonal baseline comparison to your monitoring: compare November 2026 to November 2025."

---

## Slide 11 — Scaling Bedrock: Throughput and Cost Management
**Layout:** Bedrock scaling and cost controls for NorthStar

**Content:**
**Bedrock Scaling Considerations:**

Unlike SageMaker endpoints, you don't manage Bedrock scaling — AWS handles it. But you manage:

**Throughput limits (Bedrock Quotas):**
- Claude 3.5 Sonnet default: 50 requests/minute in us-east-1
- NorthStar peak: ~847 agent sessions/day ÷ 8 business hours = ~105 sessions/hour = ~1.75 sessions/minute (well within limit)
- For higher-throughput use cases: request quota increase through AWS console

**Token cost management:**
```python
# Token budget enforcement per session
MAX_TOKENS_PER_SESSION = 5000  # Hard limit per agent session
MAX_TOKENS_PROMPT = 2000       # System prompt + context
MAX_TOKENS_RESPONSE = 500      # Per response

def invoke_bedrock_with_budget(session_tokens_used: int, prompt: str) -> str:
    if session_tokens_used >= MAX_TOKENS_PER_SESSION:
        return "SESSION_BUDGET_EXCEEDED: Please contact a human agent."
    
    available_tokens = MAX_TOKENS_PER_SESSION - session_tokens_used
    max_response_tokens = min(MAX_TOKENS_RESPONSE, available_tokens)
    
    response = bedrock_runtime.invoke_model(
        modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
        body=json.dumps({
            'max_tokens': max_response_tokens,
            'system': SYSTEM_PROMPT,
            'messages': messages
        })
    )
    return response

# Track tokens per session in DynamoDB
```

**Cost alert configuration:**
```python
# CloudWatch budget alarm: daily Bedrock token spend
cloudwatch.put_metric_alarm(
    AlarmName='northstar-bedrock-daily-budget',
    MetricName='EstimatedCharges',
    Namespace='AWS/Billing',
    Statistic='Maximum',
    Period=86400,  # 24 hours
    EvaluationPeriods=1,
    Threshold=60.0,  # Alert if daily Bedrock cost > $60
    AlarmActions=[SNS_TOPIC_ARN]
)
```

**Figure:** *Bedrock cost tracking dashboard.* Daily cost chart (last 30 days): Offer Generation ($2.90/day average), Agent Sessions ($7.60/day average), Total ($10.50/day average). Budget alert line: $60/day. All days well below alert. Week of Oct 13 highlighted: cost spike to $18.50/day — investigation: NorthStar ran agent load tests that week. The chart communicates: proactive budget monitoring catches cost anomalies before they become surprises.

**Notes:** "The token budget enforcement per session is a cost control that also serves as a guardrail against infinite loops. If an agent is looping (tool call → same tool call → same tool call), the session token budget will eventually trigger the budget limit and return the 'SESSION_BUDGET_EXCEEDED' message to the user, who can then connect with a human agent. It's both a cost control and a loop-break mechanism."

---

## Slide 12 — The Inference Cost Model: Optimizing at Scale
**Layout:** Cost model for NorthStar inference at various scales

**Content:**
**NorthStar Inference Cost Scaling:**

Current scale: 400 stores, ~500K active customers.

**Scenario A: NorthStar current scale**
- Churn endpoint: 1× ml.c5.large = $0.110/hr = $80/month
- Batch scoring: monthly run × $2.25 = $2.25/month
- RAG Offer Generation: 5,000 offers/day × $0.002/offer = $300/month
- Agent: 847 sessions/day × $0.009/session = $230/month
- **Total: ~$612/month**

**Scenario B: NorthStar at 10× scale (4,000 stores)**
- Churn endpoint: auto-scale to 3-4× ml.c5.large = $240/month
- Batch: $22.50/month
- RAG: 50,000 offers/day × $0.002 = $3,000/month
- Agent: 8,470 sessions/day × $0.009 = $2,300/month
- **Total: ~$5,560/month**

**Scenario C: Optimization at 10× scale**
- Offer Generation with prompt caching (-80% input tokens): $600/month
- Agent with session caching common tools: $1,840/month
- Batch pricing for high-volume training: -20%
- **Optimized total: ~$3,200/month (vs. $5,560 unoptimized)**

**Key insight:** LLM inference (RAG + Agent) dominates cost at scale. Optimization effort should focus on token efficiency.

**Figure:** *Cost scaling chart.* Three bars (Current, 10× scale, 10× scale optimized). Each bar stacked by cost component (Churn endpoint, Batch, RAG, Agent). Colors: Churn (teal), Batch (small, barely visible), RAG (orange), Agent (red). At a 10× scale, RAG and Agent together account for 95% of the cost. Optimization bar shows RAG and Agent shrinking significantly. The visual communicates: optimize where the money is.

**Notes:** "The cost scaling exercise reveals a counterintuitive truth: the traditional ML components (SageMaker endpoint, batch transform) are relatively cheap and don't dominate at scale. The LLM inference components (RAG offers, agent sessions) are what drives cost. Every optimization dollar for NorthStar at 10× scale should go into token efficiency: prompt caching, prompt compression, response length limits, and aggressive caching of deterministic computations."

---

## Slide 13 — Deployment Anti-Patterns: The Production Hall of Shame
**Layout:** Five deployment anti-patterns with consequences

**Content:**
**Production Deployment Anti-Patterns:**

1. **The Friday Big Bang:** Deploy a new model to 100% of traffic on Friday afternoon. Gone camping for the weekend. The model has a bug that shows up on Saturday morning in production. On-call engineer who barely knows the system gets the 2 am alert.
   *Fix:* Deploy Tuesday-Thursday. Always canary. Never Big Bang.

2. **The Undocumented Rollback:** Team deploys v3.0. v3.0 fails. Team tries to roll back. Nobody knows how. "The endpoint was deployed manually through the console." Three hours of debugging to restore service.
   *Fix:* Rollback procedure documented AND tested before first production deployment.

3. **The Missing Smoke Test:** New model deployed. Endpoint exists and responds to health checks. But the model artifact is corrupted — every prediction returns NaN. Discovered by customer complaints two hours later.
   *Fix:* Smoke test immediately after deployment by sending 5 representative requests and asserting valid responses.

4. **The Ignored Auto-Scaling:** Auto-scaling configured but min capacity = 0. Monday morning, first request hits a cold endpoint: 30-second response time. Customer-facing system appears "down."
   *Fix:* Always set min capacity = 1. Never scale to zero for production endpoints.

5. **The Version Number Lie:** Model registered in Model Registry as "v3.0." But what training code, what dataset, what hyperparameters? Nobody knows. Model Registry has no Git SHA, no dataset version, no reproducibility metadata.
   *Fix:* Model Registry registration requires: git_commit, dataset_version, training_job_name, evaluation_report_link.

**Figure:** *Five-anti-pattern Hall of Shame board.* Five cards, each: anti-pattern name, icon (red X), one-sentence story, and "Fix" in green. "Friday Big Bang" card has a cartoon calendar with Friday crossed out. Clean, memorable format. The "Hall of Shame" framing communicates: these are real failure modes, not theoretical risks.

**Notes:** "The Version Number Lie is the one that haunts teams 6 months later. 'Which model is in production? v3.0. Which v3.0? The one from October or the one from November? What was the training data? I don't know — the person who trained it left the company.' You cannot manage what you cannot trace. The Model Registry metadata requirements are your traceability controls."

---

## Slide 14 — Lab 4 Final Preparation: Common Issues
**Layout:** Lab 4 final guidance with common failure points

**Content:**
**Lab 4 Due Saturday — Final Guidance:**

**Most common Lab 4 failures:**

**Issue 1: ConditionStep not reading AUC correctly**
```python
# WRONG: AUC is a float but you're comparing a string
ConditionGreaterThanOrEqualTo(left=auc_score, right="0.72")

# CORRECT: Compare float to float
ConditionGreaterThanOrEqualTo(left=auc_score, right=0.72)
```

**Issue 2: CodePipeline can't trigger SageMaker Pipeline**
- Check IAM: CodePipeline execution role needs `sagemaker:StartPipelineExecution`
- Check ARN: pipeline ARN in CodePipeline action config must exactly match the SageMaker Pipeline ARN

**Issue 3: CodeBuild test stage failing with import errors**
- Check `requirements.txt`: all test dependencies must be listed
- Check Python version: CodeBuild environment must use the same Python version as test code

**Issue 4: SageMaker Pipeline stuck in "Executing" state**
- Check CloudWatch Logs for the failing step
- Check IAM: training job role needs S3 access to both input and output paths
- Check S3 paths: all S3 URIs in pipeline config must exist

**Checklist for Saturday submission:**
- [ ] SageMaker Pipeline runs end-to-end (console trigger test)
- [ ] CodePipeline triggers on GitHub push
- [ ] Unit tests and integration tests pass in CodeBuild
- [ ] ConditionStep correctly gates deployment (test both pass and fail cases)
- [ ] Evaluation report included in submission
- [ ] ADR written and included

**Figure:** *Lab 4 final checklist.* Six checkbox items (from above) with status indicators: 3 checked (assuming typical student progress), 3 unchecked. Tips for each unchecked item. "Time estimate to complete: 4-6 hours from a working SageMaker Pipeline." Encouragement tone: "You've got this."

**Notes:** The ConditionStep type error (Issue 1) is the most common issue this week. The `right` parameter in `ConditionGreaterThanOrEqualTo` must be a Python float (0.72), not a string ("0.72"). This is not well documented in the SageMaker SDK docs and catches everyone out. Test your ConditionStep explicitly: train a model you know will fail the gate (use a tiny training set), verify the pipeline goes to the fail branch.

---

## Slide 15 — Key Takeaways + What's Next
**Layout:** Takeaways + L17 preview

**Content:**
**Key Takeaways:**
1. Inference architecture selection follows a decision tree: real-time vs. batch vs. async; variable vs. steady traffic; single vs. multi-model — work through the tree before choosing
2. Auto-scaling requires asymmetric cooldowns and a minimum of 1 instance (never scale to zero for production endpoints — cold starts destroy user experience)
3. SageMaker Inference Recommender provides data-driven instance type selection — use it; don't guess the right instance
4. Model Monitor enables automated drift surveillance; drift requires interpretation (seasonal drift vs. distribution shift) before acting on alerts
5. At scale, LLM inference (RAG + agents) dominates cost — optimization effort should focus on token efficiency, not compute efficiency

**Next Session (Thu Oct 29):**
- Topic: Deployment & Scaling II — security, compliance, and Lab 5 deep dive
- Reading due: *Deployment at Scale* — "Security" through "Key Takeaways"
- **Lab 4 due Saturday** — finish strong
- **Lab 5 assigned Thursday** — already assigned; start reviewing spec

**Figure:** *Five-takeaway summary card.* Lab 4 countdown (4 days, red urgency). Cost scaling chart thumbnail. Inference architecture decision tree thumbnail.

**Notes:** "Four days to Lab 4. The most important thing you can do tonight is to ensure you have a working SageMaker Pipeline; that is your entire focus. Everything else in Lab 4 (CodePipeline, tests, evaluation report) flows from a working pipeline. Don't spend tonight polishing the evaluation report if the pipeline isn't running."
