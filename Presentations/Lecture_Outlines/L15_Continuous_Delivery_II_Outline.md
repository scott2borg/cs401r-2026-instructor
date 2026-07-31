---
lecture: L15
title: Continuous Delivery II — Infrastructure, Scaling & Multi-Region
date: Thursday, October 22, 2026
week: 8
arc: Build
reading_due: "Continuous Delivery for AI — Infrastructure through Key Takeaways"
lab_assigned: "Lab 5 — Deployment & Scaling (due Sat Nov 14)"
lab_due: "Lab 4 due Sat Oct 31"
slides_target: 15
---

# L15: Continuous Delivery II — Infrastructure, Scaling & Multi-Region
**Thursday, October 22, 2026 | CS 401R: Engineering Production AI Systems | Fall 2026**

> A deployment pipeline is only as reliable as the infrastructure beneath it. Learn how to build deployment infrastructure that scales under load, survives region failures, and keeps AI systems running when the underlying platform has problems.

**Reading Due:** *Continuous Delivery for AI* — "Infrastructure" through "Key Takeaways"
**Lab 5 Assigned Today:** Deployment & Scaling — due Sat Nov 14
**Lab 4 Due:** Sat Oct 31 (9 days)

---

## Slide 1 — Title
**Layout:** Left dark panel + right multi-region architecture diagram

**Content:**
- Continuous Delivery II: Infrastructure, Scaling & Multi-Region
- CS 401R · Lecture 15 · Thursday, October 22, 2026
- ⚠️ Lab 5 Assigned Today — Due November 14

**Figure:** *Multi-region AI platform overview.* Two AWS region boxes (us-east-1 as primary, us-west-2 as secondary). Each region: SageMaker endpoint, Bedrock KB, CloudWatch monitoring. Global Traffic Manager (Route 53) at top routing traffic: 100% to primary normally, failover arrow to secondary. Data replication arrow between regions: "Feature Store replicated; Model artifacts synced." The diagram communicates: production AI at enterprise scale requires thinking beyond a single region.

**Notes:** "Last session covered deployment patterns — how you move traffic from old versions to new. Today we cover the infrastructure that makes those patterns work reliably: how endpoints scale automatically, how pipelines stay healthy under load, and what it takes to operate an AI system that must survive an AWS region going down."

---

## Slide 2 — SageMaker Endpoint Scaling Architecture
**Layout:** Auto-scaling configuration for NorthStar endpoints

**Content:**
**How SageMaker Endpoint Scaling Works:**

SageMaker endpoints scale in two dimensions:
1. **Horizontal scaling:** Add/remove instances based on load
2. **Vertical scaling:** Change instance type (manual; requires endpoint update)

**Auto-scaling policy for NorthStar Churn Endpoint:**
```python
autoscaling = boto3.client('application-autoscaling')

# Register the endpoint variant as a scalable target
autoscaling.register_scalable_target(
    ServiceNamespace='sagemaker',
    ResourceId='endpoint/northstar-churn-prod/variant/Production-v3-0',
    ScalableDimension='sagemaker:variant:DesiredInstanceCount',
    MinCapacity=1,   # Always at least 1 instance
    MaxCapacity=8    # Max 8 instances
)

# Target-tracking policy: maintain avg invocations/instance
autoscaling.put_scaling_policy(
    PolicyName='northstar-churn-scaling',
    ServiceNamespace='sagemaker',
    ResourceId='endpoint/northstar-churn-prod/variant/Production-v3-0',
    ScalableDimension='sagemaker:variant:DesiredInstanceCount',
    PolicyType='TargetTrackingScaling',
    TargetTrackingScalingPolicyConfiguration={
        'TargetValue': 70.0,  # Target: 70 invocations per instance per minute
        'PredefinedMetricSpecification': {
            'PredefinedMetricType': 'SageMakerVariantInvocationsPerInstance'
        },
        'ScaleInCooldown': 300,   # Wait 5 min before scaling in
        'ScaleOutCooldown': 60    # Scale out quickly (60 sec)
    }
)
```

**Scale-out is fast (60s); scale-in is slow (300s):** Asymmetric cooldown protects against scale-in during legitimate traffic spikes.

**Figure:** *Auto-scaling response diagram.* X-axis: time (minutes 0-20). Y-axis: invocations/minute (left) and instance count (right). Traffic spike at minute 5: invocations jump from 50 to 180/min. After 60 seconds: instance count increases from 1 to 3. Traffic decreases at minute 12: invocations drop to 60/min. After 300 seconds: instance count decreases back to 1. The asymmetric cooldown (60s scale-out, 300s scale-in) visually apparent.

**Notes:** "The asymmetric cooldown is a lesson learned from production incidents. If you scale in as fast as you scale out, you can enter an oscillation loop: traffic spikes → scale out → traffic drops slightly → scale in → traffic spikes again → scale out. The 5-minute scale-in cooldown breaks the oscillation. Scale out fast to protect latency; scale in slowly to prevent thrashing."

---

## Slide 3 — SageMaker Batch Transform: Scaling for Batch Workloads
**Layout:** Batch Transform architecture for NorthStar monthly churn scoring

**Content:**
**When Real-Time Endpoints Aren't the Right Tool:**

For the NorthStar monthly batch churn scoring (500K customers), running a real-time endpoint would:
- Require many instances running for hours (expensive)
- Process customers serially (slow)
- Leave the endpoint idle between monthly runs

**SageMaker Batch Transform:**
- Spins up a fleet of instances for the batch job
- Processes all records in parallel across instances
- Terminates all instances when done (no ongoing cost)
- Handles large datasets natively via S3 input/output

```python
transformer = Transformer(
    model_name='northstar-churn-v3-0',
    instance_count=10,        # 10 instances in parallel
    instance_type='ml.m5.xlarge',
    output_path='s3://northstar-artifacts/batch-scoring/2026-10/',
    strategy='MultiRecord',   # Process multiple customers per batch
    max_payload=6,            # MB per batch (tune for throughput)
    max_concurrent_transforms=100  # Concurrent transformation requests
)

transformer.transform(
    data='s3://northstar-processed/customers/scoring-2026-10/',
    content_type='text/csv',
    split_type='Line',
    job_name='northstar-churn-batch-2026-10',
    wait=True
)
```

**Performance:** 500K customers scored in ~45 minutes (vs. 6+ hours with a single instance). Cost: 10 × ml.m5.xlarge × 0.75 hours = ~$2.25 for the batch run.

**Figure:** *Batch Transform scaling diagram.* S3 input (500K records) → Batch Transform job (fan-out to 10 parallel instances) → each instance processes ~50K records → S3 output (500K predictions). Timeline shows: 45-minute total duration. Below: cost breakdown: 10 instances × $0.30/hr × 0.75 hr = $2.25. Compare: "Real-time endpoint alternative: 6 hours × 1 instance × $0.30/hr = $1.80, but processes serially and blocks the endpoint for 6 hours." Batch Transform wins on throughput, not cost.

**Notes:** "Batch Transform is the pattern for any workload that processes a known fixed dataset rather than responding to individual requests in real time. The monthly churn scoring is the perfect use case: 500,000 customers, process once per month, results needed by morning. Batch Transform scales out to 10 instances, finishes in 45 minutes, and costs $2.25. Elegant."

---

## Slide 4 — CI/CD Infrastructure: AWS CodePipeline Architecture
**Layout:** Full CI/CD pipeline architecture for NorthStar

**Content:**
**The NorthStar CI/CD Infrastructure:**

```
GitHub (model code, prompt templates, Terraform)
    ↓ (push to main branch)
AWS CodePipeline
    ├── Stage 1: Source
    │   └── Pull from GitHub; store source artifact to S3
    │
    ├── Stage 2: Test
    │   └── CodeBuild: run unit tests + integration tests
    │   └── Fail pipeline if tests fail
    │
    ├── Stage 3: Build
    │   └── CodeBuild: package model artifacts, Docker image (if needed)
    │
    ├── Stage 4: Train & Evaluate (SageMaker Pipeline)
    │   └── PrepareFeatures → Train → Evaluate → Gate (AUC ≥ 0.72)
    │   └── Fail pipeline if gate fails
    │
    ├── Stage 5: Manual Approval (optional gate for high-risk releases)
    │   └── Email notification to ML lead: "New model ready — approve?"
    │   └── Deploy proceeds only after approval
    │
    └── Stage 6: Deploy (Canary)
        └── Update SageMaker endpoint canary variant
        └── Lambda health gate monitors for 3 days
        └── Auto-promote or auto-rollback
```

**CodeBuild environment for NorthStar:**
```yaml
# buildspec.yml
version: 0.2
phases:
  install:
    runtime-versions:
      python: 3.11
    commands:
      - pip install -r requirements.txt
  pre_build:
    commands:
      - echo "Running unit tests..."
      - pytest tests/unit/ -v --tb=short
  build:
    commands:
      - echo "Running integration tests..."
      - pytest tests/integration/ -v --tb=short
  post_build:
    commands:
      - echo "Triggering SageMaker Pipeline..."
      - python scripts/trigger_pipeline.py
```

**Figure:** *CodePipeline 6-stage visual.* Each stage is shown as a horizontal panel with the stage name, tool (GitHub/CodeBuild/SageMaker/Lambda), and a status indicator (green checkmark or amber clock). Manual Approval stage shown with email icon and "Approval pending" status. The full pipeline visualizes the process from code commit to production deployment as 6 structured stages, with gates at stages 2, 4, and optionally 5.

**Notes:** "The Manual Approval stage at Stage 5 is optional but worth keeping in the pipeline definition even when disabled. When you're developing, you want fully automated deployments. When you're releasing a major change to a production system for the first time, having a human approval gate gives the team a moment to review the evaluation report and make a deliberate decision. Toggle it on for high-stakes releases."

---

## Slide 5 — Infrastructure as Code for CI/CD: The Terraform Layer
**Layout:** Terraform modules for CI/CD infrastructure

**Content:**
**Why CI/CD Infrastructure Needs IaC:**

Your CI/CD pipeline is itself infrastructure. Without IaC:
- CodePipeline configured by clicking through the console
- Configuration is not repeatable
- "Rebuild the CI/CD pipeline" after an incident is a manual, error-prone process
- Team members can't tell what the pipeline does without logging into the console

**NorthStar Terraform module structure for CI/CD:**
```
terraform/
├── modules/
│   ├── codepipeline/
│   │   ├── main.tf      # CodePipeline resource
│   │   ├── iam.tf       # Required roles and policies
│   │   └── variables.tf # Configurable parameters
│   ├── codebuild/
│   │   ├── main.tf      # CodeBuild project
│   │   └── iam.tf       # CodeBuild execution role
│   └── sagemaker_pipeline/
│       ├── main.tf      # SageMaker Pipeline definition
│       └── iam.tf       # SageMaker Pipeline execution role
└── environments/
    ├── dev/
    │   └── main.tf      # Dev environment: CI/CD + dev endpoints
    └── prod/
        └── main.tf      # Prod environment: CI/CD + prod endpoints
```

**Key Terraform variables for CI/CD:**
```hcl
variable "model_evaluation_threshold" {
  description = "Minimum AUC for deployment gate"
  default     = 0.72
}
variable "canary_initial_weight" {
  description = "Initial canary traffic percentage"
  default     = 10
}
variable "canary_observation_hours" {
  description = "Hours to observe at each traffic level"
  default     = 24
}
```

Making the gate threshold a Terraform variable means that changing the deployment criteria is a code change, tracked in Git and reviewed via pull request.

**Figure:** *Terraform module dependency graph.* Module boxes: codepipeline, codebuild, sagemaker_pipeline. Arrows: codepipeline depends on codebuild (build stage), codepipeline depends on sagemaker_pipeline (train stage). Environment boxes: dev and prod both instantiate all three modules with different variable values. The graph shows: CI/CD infrastructure has its own dependency structure, managed by Terraform.

**Notes:** "Making the evaluation gate threshold a Terraform variable is a governance decision. When someone wants to lower the AUC gate from 0.72 to 0.68 because 'the deadline is approaching,' they have to submit a pull request. The pull request is reviewed by the team. The change is recorded in Git with the reviewer's name. This is the difference between a governance control and a dashboard knob that anyone can change."

---

## Slide 6 — SageMaker Real-Time Inference: Performance Architecture
**Layout:** Endpoint performance architecture and latency breakdown

**Content:**
**Anatomy of a SageMaker Endpoint Request:**

```
Client Request (features JSON)
    ↓ (network)
SageMaker Endpoint (load balancer)
    ↓ (internal routing)
Container instance (running model server)
    ├── Request deserialization: ~2ms
    ├── Feature preprocessing (if any): ~1ms
    ├── Model inference: ~5-15ms (XGBoost)
    ├── Response serialization: ~2ms
    └── ─────────────────────────────────
        Total container time: ~10-20ms
    ↓ (network return)
Client receives response: ~25-40ms total
```

**Latency optimization techniques:**
1. **Instance placement:** `ml.m5.xlarge` vs. `ml.c5.xlarge` for CPU-bound XGBoost inference: `c5` is ~15% faster
2. **Model loading:** Model loaded into memory at container startup (not per request). Cold start (new instance): 15-30 seconds. Warm request: < 5ms model load time
3. **Batching:** For high-throughput batch requests, SageMaker supports batching via `max_payload`; amortizes fixed overhead across multiple records
4. **Data locality:** Endpoint in same region as client. Avoid cross-region inference calls (adds 50-100ms latency)

**SageMaker Inference Recommender:**
Automatically benchmarks your model across instance types and reports cost/latency tradeoffs. Use it before choosing an instance type for a new model.

**Figure:** *Latency breakdown waterfall chart.* Horizontal waterfall showing total request time (~35ms). Segments: Network (client→LB): 8ms, Internal routing: 2ms, Container (deserialization + inference + serialization): 20ms, Network (LB→client): 5ms. Largest segment: container time (57%). Cold start bar shown separately: 30,000ms (30 seconds) — visually dwarfs the warm request bar, communicating: cold starts are the latency outlier, not model inference.

**Notes:** "Cold starts are the SageMaker latency problem that surprises teams most. The first request after a new instance starts takes 30 seconds. If you auto-scale to 0 instances between uses (to save cost) and then the first morning request hits a cold instance, your users experience a 30-second response time. Fix: keep at least 1 warm instance running at all times (`MinCapacity=1` in your auto-scaling policy)."

---

## Slide 7 — Bedrock Latency and Throughput: Operating Foundation Models
**Layout:** Bedrock latency architecture with NorthStar tuning

**Content:**
**Bedrock Inference Architecture (what you don't control):**

When you call Bedrock, you're calling Anthropic's Claude hosted on AWS infrastructure. You don't control:
- Model size (though you choose the model tier)
- Infrastructure scaling
- Cold starts (Bedrock manages this)

**What you do control:**
1. **Model choice:** Claude 3 Haiku (fast, cheap) vs. Claude 3.5 Sonnet (better quality, 2× latency) vs. Claude 3 Opus (best quality, 3× latency)
2. **Prompt length:** Every additional token in the prompt adds latency. Optimize prompt length.
3. **Max tokens:** Set `max_tokens` to the minimum needed. Don't set 4096 when your responses are always < 500 tokens.
4. **Streaming:** For user-facing applications, use Bedrock streaming to show tokens as they generate (perceived latency much lower even if total latency is the same)
5. **Caching:** Bedrock Prompt Caching caches the system prompt across requests. For NorthStar's long system prompt, this can reduce input token cost by 90% and latency by 30%

**NorthStar Bedrock configuration for offer generation:**
```python
response = bedrock_runtime.invoke_model(
    modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
    body=json.dumps({
        'anthropic_version': 'bedrock-2023-05-31',
        'max_tokens': 512,  # Offers are brief; don't overprovision
        'system': system_prompt,
        'messages': [{'role': 'user', 'content': user_message}]
    })
)
```

**Figure:** *Bedrock latency comparison chart.* Bar chart: three model tiers (Haiku, Sonnet, Opus) × two scenarios (without prompt cache, with prompt cache). Haiku: 0.8s / 0.6s. Sonnet: 1.8s / 1.3s. Opus: 4.2s / 3.0s. NorthStar SLA (3s) marked as a horizontal line. Only Haiku and Sonnet (with cache) consistently meet the SLA. Sonnet (without cache) occasionally exceeds. Opus: always exceeds. Decision: use Sonnet with prompt caching.

**Notes:** "Bedrock Prompt Caching is one of the highest-value optimizations for RAG systems with long system prompts. NorthStar's offer generation system prompt is 800 tokens. Without caching, every request pays 800 input tokens. With caching, the system prompt is cached for 5 minutes — 90% of requests in a 5-minute window pay only 1 input token for the cached portion. Cost reduction: 80-90% on input tokens."

---

## Slide 8 — Multi-Region Architecture: When You Need It and Why
**Layout:** NorthStar multi-region decision and architecture

**Content:**
**When Do You Need Multi-Region AI?**

Multi-region adds significant complexity. You need it when:
1. **Compliance requires data residency:** EU customer data cannot leave the EU (GDPR)
2. **Latency requirements are global:** Users in Asia can't tolerate 200ms of cross-Atlantic latency
3. **Business requires ≥ 99.99% availability:** Single-region availability ≈ 99.95% (3 hours downtime/year); multi-region achieves 99.99%+ 
4. **Regulatory requires disaster recovery:** Many financial and healthcare regulations require a geographically separate DR site

**NorthStar Multi-Region Architecture (hypothetical scale-up):**
- **Primary region:** us-east-1 (NorthStar HQ, main data center)
- **Secondary region:** us-west-2 (DR site, active-passive)
- **Trigger for failover:** Route 53 health check detects primary unhealthy → automatic DNS failover to secondary
- **RTO (Recovery Time Objective):** < 5 minutes (automated failover via Route 53)
- **RPO (Recovery Point Objective):** < 1 hour (Feature Store data replicated hourly to secondary)

**What's replicated:**
- Model artifacts in S3 (cross-region replication enabled on artifact bucket)
- Feature Store data (Glue ETL runs in both regions; secondary is 1 hour behind)
- Bedrock Knowledge Bases (re-indexed in secondary; updated on same schedule)
- Prompt templates in SSM Parameter Store (replicated via custom Lambda)
- **NOT replicated:** Live request state, active agent sessions (acceptable: agent sessions can restart)

**Figure:** *Multi-region architecture diagram.* Primary (us-east-1) and secondary (us-west-2) side by side. Route 53 at top with health check arrows to both regions. Replication arrows between regions: S3 (continuous), Feature Store (hourly), Bedrock KB (weekly). Failover path: Route 53 detects a primary failure → DNS TTL is 60s → all traffic reroutes to the secondary → 5-minute RTO. RPO annotation: "1 hour data loss acceptable for churn use case."

**Notes:** "Multi-region is where AI platform complexity increases dramatically. You're not just running one platform — you're running two, kept in sync, with automated failover. For a course project, this is well out of scope. For a $3.2B retailer with PCI compliance requirements, it's table stakes. Lab 5 covers single-region canary deployment; multi-region is a design exercise in Lab 7's architecture discussion."

---

## Slide 9 — Infrastructure Cost Modeling for CI/CD
**Layout:** CI/CD infrastructure cost breakdown for NorthStar

**Content:**
**What Does the NorthStar CI/CD Infrastructure Cost?**

**Per-pipeline-run costs (triggered daily or on code change):**
| Component | Cost per run | Runs/month | Monthly cost |
|-----------|-------------|-----------|-------------|
| CodePipeline executions | $1.00/pipeline | ~10 | $10.00 |
| CodeBuild (test stage) | $0.05/build-minute × 8 min | ~10 | $4.00 |
| SageMaker Processing Job (feature prep) | ml.m5.xlarge × 30 min × $0.28/hr | ~4 | $0.56 |
| SageMaker Training Job | ml.m5.xlarge × 2 hr × $0.28/hr | ~4 | $2.24 |
| SageMaker Processing Job (evaluation) | ml.m5.large × 15 min × $0.14/hr | ~4 | $0.14 |

**Ongoing infrastructure costs (always running):**
| Component | Configuration | Monthly cost |
|-----------|--------------|-------------|
| Churn endpoint (prod) | 1× ml.m5.large, on-demand | ~$100 |
| Churn endpoint (canary, during deploy) | 1× ml.m5.large, 3 days/month | ~$10 |
| RAG endpoint (Bedrock) | Token-based; ~$0.003/request × 1,000 req/day | ~$90 |
| Agent endpoint (Bedrock) | Token-based; ~$0.009/session × 847 sessions/day | ~$230 |
| Lambda (health gates, cron) | < $1/month | $1 |

**Total NorthStar CI/CD + Platform infrastructure: ~$450-500/month**

**Figure:** *Infrastructure cost breakdown bar chart.* Stacked bar with two categories: CI/CD (running costs) and Platform (inference costs). CI/CD costs: ~$17/month. Platform inference: ~$430/month. Inference dominates. Breakdown by system: Churn ($110), RAG ($90), Agent ($230). Key insight: inference costs >> CI/CD costs for this AI workload.

**Notes:** "The asymmetry between CI/CD costs ($17/month) and inference costs ($430/month) is important for your future budget conversations. When someone asks 'is the CI/CD automation worth it?' the answer is: the automation costs $17/month to run. The incidents it prevents cost $10K each. The ROI is obvious. The budget discussion is about inference economics, not CI/CD overhead."

---

## Slide 10 — Lab 5 Walkthrough: Architecture and Deliverables
**Layout:** Lab 5 complete requirements

**Content:**
**Lab 5: Deployment & Scaling**
*(Assigned Today | Due Sat Nov 14 | 23 days)*

**What you'll build:**

**Part 1: Canary Deployment Infrastructure (required)**
- SageMaker endpoint with Production + Canary variants (from Lab 4 deployment)
- Lambda health gate function: checks metrics every 15 minutes during canary window
- CloudWatch alarms for hard failure criteria (error rate, latency)
- Auto-promotion logic: advance canary to 30%, 50%, 100% if metrics pass
- Auto-rollback logic: set canary to 0% if hard failure criteria met

**Part 2: Auto-Scaling Configuration (required)**
- Auto-scaling policy on churn endpoint (target: 70 invocations/instance/minute)
- Min: 1 instance, Max: 8 instances
- Load test: demonstrate endpoint scales out under simulated load

**Part 3: Batch Transform (required)**
- SageMaker Batch Transform job for monthly 500K customer scoring
- Triggered by monthly EventBridge schedule
- Output to S3 with results format for business reporting

**Part 4: Option A — RAG Deployment (if doing Option A from Lab 3)**
- Blue/Green Knowledge Base deployment
- Parameter Store pointer management with rollback capability
- Smoke test suite for Knowledge Base validation

**Part 5: Option B — Agent Deployment (if doing Option B from Lab 3)**
- Bedrock Agent versioning and alias management
- Agent canary via alias traffic split
- Trace-based health gate for agent quality monitoring

**Figure:** *Lab 5 deliverable checklist.* Five-part list with required/optional labels. Architecture diagram thumbnail showing where each deliverable fits in the NorthStar platform. Timeline: 23 days → start now. "Dependency: Lab 4 must be working before Lab 5 can begin."

**Notes:** "Lab 5 has a hard dependency on Lab 4: the canary deployment in Part 1 extends the Lab 4 CodePipeline to deploy to the canary variant instead of directly to production. If Lab 4 isn't working, come to office hours this week. Lab 5 starts where Lab 4 ends."

---

## Slide 11 — Deployment Security: IAM and Network Controls
**Layout:** Security architecture for CI/CD and deployment infrastructure

**Content:**
**Securing the Deployment Pipeline:**

**Principle of least privilege for CI/CD:**

| Role | Allowed Actions | NOT Allowed |
|------|----------------|------------|
| CodePipeline execution role | `sagemaker:StartPipelineExecution`, `s3:GetObject`/`PutObject` (artifacts bucket) | Model Registry write; endpoint creation |
| CodeBuild execution role | `sagemaker:DescribePipelineExecution`, `logs:CreateLogGroup` | Any production resource modification |
| SageMaker Pipeline execution role | `sagemaker:CreateTrainingJob`, `sagemaker:CreateModel`, `sagemaker:RegisterModel` | Endpoint update (deployment is separate) |
| Deployment Lambda role | `sagemaker:UpdateEndpoint`, `sagemaker:DescribeEndpoint` | Training; Model Registry write |

**Why separate deployment from training:**
- Training role and deployment role are different IAM roles
- A compromised training job cannot directly modify production endpoints
- Deployment must be explicitly approved (via pipeline) — not callable from arbitrary code

**Network security:**
- CodeBuild runs in VPC (same VPC as NorthStar platform)
- No public internet access during build/test (all AWS calls via VPC endpoints)
- S3 artifact bucket: no public access, encrypted at rest (AES-256), encrypted in transit

**Secrets management:**
- No credentials in buildspec.yml or pipeline config
- All secrets in AWS Secrets Manager; accessed via IAM role permissions
- Pipeline logs scrubbed of sensitive values

**Figure:** *IAM role separation diagram.* Four boxes (CodePipeline, CodeBuild, SageMaker Pipeline, Deployment Lambda), each with their specific IAM role. Arrows show what each role can access (permitted resources in green, blocked resources in red). "Trust boundary" line between CI/CD roles and production resources — only Deployment Lambda can cross it, and only with explicit endpoint update permissions. The diagram communicates: least privilege is enforced at every stage of the pipeline.

**Notes:** "The separation between training and deployment is a security control, not just an operational pattern. If the training environment is compromised — a malicious package installed in the training container, for example — the blast radius is limited: the attacker can corrupt the model artifact, but they cannot modify production endpoints. The deployment Lambda is the only role with that permission, and it only activates via the approved pipeline."

---

## Slide 12 — Monitoring the Pipeline Itself
**Layout:** CI/CD pipeline health monitoring

**Content:**
**Meta-Monitoring: Watching the Watcher**

Your CI/CD pipeline is itself a system that can fail. Monitor it.

**Pipeline health metrics to track:**
| Metric | Alert Threshold | Meaning |
|--------|----------------|---------|
| Pipeline execution success rate | < 80% | Too many pipeline failures |
| Pipeline execution duration | > 2× historical average | Something is slowing down |
| Days since last successful deploy | > 14 days | Pipeline may be broken or blocked |
| CodeBuild test failure rate | > 30% | Test suite may be flaky |
| Model training job failure rate | > 15% | Training instability |

**NorthStar Pipeline Health Dashboard:**
```python
# EventBridge rule: capture all pipeline state changes
{
  "source": ["aws.codepipeline"],
  "detail-type": ["CodePipeline Pipeline Execution State Change"],
  "detail": {
    "state": ["SUCCEEDED", "FAILED", "STOPPED"]
  }
}
# → Lambda → log to CloudWatch → dashboard
```

**Common pipeline failure causes and fixes:**
- CodeBuild: flaky test (depends on external service) → mock the external service
- SageMaker Pipeline: insufficient permissions → review IAM policy for training role
- SageMaker Pipeline: job timeout → increase `max_run` in training job config
- Canary health gate: lambda timeout → increase timeout in Lambda config

**Figure:** *Pipeline health dashboard mockup.* Four metric panels: Execution Success Rate (trend line, last 30 days: 87% average, one FAILED execution highlighted), Average Duration (trend: 45 min → 62 min, rising trend alert), Days Since Last Deploy (3 days, green), Test Failure Rate (12%, amber warning). Clean, operational dashboard view.

**Notes:** "The 'days since last successful deploy' metric is the one that catches the insidious failure mode: a CI/CD pipeline that's running but always failing. Teams sometimes accept 'oh the pipeline fails sometimes, we deploy manually when we need to.' That's a broken pipeline masquerading as a working one. If the automated pipeline isn't deploying successfully, fix it — don't work around it."

---

## Slide 13 — The DORA Metrics Applied to NorthStar
**Layout:** DORA metrics target state after Labs 4-5

**Content:**
**DORA Metrics: NorthStar Target State**

| DORA Metric | Before Labs 4-5 | After Labs 4-5 | Elite Benchmark |
|-------------|-----------------|----------------|----------------|
| **Deployment Frequency** | Monthly (manual) | Bi-weekly (automated) | On-demand |
| **Lead Time for Changes** | 2-3 weeks | 5-7 days | < 1 day |
| **Change Failure Rate** | ~40% (manual error-prone) | < 15% (gated) | < 5% |
| **MTTR** | 4-8 hours (manual) | < 15 minutes (auto-rollback) | < 1 hour |

**What the labs buy:**
- Lab 4 (CI/CD): Deployment Frequency ↑, Lead Time ↓, Change Failure Rate ↓
- Lab 5 (Canary + Rollback): Change Failure Rate ↓, MTTR ↓

**The DORA research finding:** Elite DORA performers (on-demand deploy, < 15min MTTR) have:
- 127× more frequent deployments than low performers
- 2,604× faster lead times
- 3× lower change failure rates
- **7× better business outcomes** (revenue growth, market share, profitability)

The correlation between operational excellence and business outcomes is not coincidental.

**Figure:** *DORA performance level matrix.* Four rows (Deployment Frequency, Lead Time, Change Failure Rate, MTTR) × four columns (Low, Medium, High, Elite). NorthStar "Before" position circled in each row (Low or Medium). NorthStar "After Labs 4-5" position marked (Medium to High). "Elite" column highlighted in teal — the aspiration. The matrix communicates: the labs move NorthStar toward Elite performance, not the full way, but significantly forward.

**Notes:** "The 7× better business outcomes from the DORA research is the executive-level argument for investing in CI/CD and deployment automation. This is what you say when your VP asks why you're spending two weeks building a deployment pipeline: 'Organizations with Elite DORA performance have 7× better business outcomes. This pipeline is the foundation of Elite performance.'"

---

## Slide 14 — Putting It Together: The Full NorthStar Deployment Pipeline
**Layout:** End-to-end NorthStar deployment pipeline architecture

**Content:**
**The NorthStar Deployment Pipeline After Labs 1-5:**

```
GitHub (code + prompts + Terraform)
    ↓ (push to main)
CodePipeline
    ├── Source: pull artifacts
    ├── Test: pytest unit + integration (CodeBuild)
    ├── Build: package artifacts (CodeBuild)
    ├── Train & Evaluate: SageMaker Pipeline
    │   └── PrepareFeatures → Train → Evaluate → Gate
    └── Deploy: canary deployment
        ├── Update canary variant (10% traffic)
        ├── Lambda health gate (15-min checks, 24-hour window)
        ├── If healthy: advance to 30% → 50% → 100%
        └── If unhealthy: auto-rollback to 0% canary
        
SageMaker Auto-Scaling
    └── Endpoint scales 1-8 instances based on traffic

Monthly Batch Transform (EventBridge schedule)
    └── 500K customers scored; results to S3

Blue/Green RAG Index Updates (weekly)
    └── Staging KB updated; smoke tested; pointer swapped

Agent Alias Management (Bedrock)
    └── New agent version → alias canary → promote or rollback
```

**This is what a production AI platform's CI/CD looks like.**

**Figure:** *Full NorthStar platform architecture including CI/CD.* The complete NorthStar architecture (from Lab 1 foundation) with the CI/CD overlay: CodePipeline connecting to SageMaker Pipeline, canary deployment to endpoints, health gate Lambda, auto-scaling, batch transform trigger. Also: RAG blue/green KB management, agent alias management. Large, detailed architecture diagram — the "capstone" view of what the lab sequence builds.

**Notes:** "This architecture diagram is the capstone view of what you're building across Labs 1-5. If you print nothing else from this course to keep, print this diagram. It represents the full production AI platform architecture for a real enterprise AI system. Being able to explain every component in this diagram — what it does, why it's there, how it connects — is what differentiates a production ML engineer from someone who can train models in a notebook."

---

## Slide 15 — Key Takeaways + What's Next
**Layout:** Takeaways + L16 preview

**Content:**
**Key Takeaways:**
1. SageMaker endpoint auto-scaling requires asymmetric cooldowns (scale-out fast, scale-in slow) to prevent oscillation under variable load
2. Batch Transform is the right tool for large, periodic batch workloads — scales to 10+ instances, terminates when done, far more efficient than real-time endpoints for batch
3. The full CI/CD infrastructure (CodePipeline + CodeBuild + SageMaker Pipeline + Canary Lambda) costs ~$17/month to run — a trivial cost compared to the operational risk it mitigates
4. DORA metrics (deployment frequency, lead time, change failure rate, MTTR) measure deployment quality — Labs 4-5 move NorthStar from Low to Medium-High DORA performance
5. Separate IAM roles for training vs. deployment is a security control, not just an operational pattern — it limits blast radius from compromised training environments

**Next Session (Tue Oct 27):**
- Topic: Deployment & Scaling I — deep dive into endpoint optimization, SageMaker Inference Recommender, and multi-model endpoints
- Reading due: *Deployment at Scale* — "Inference Architecture" through "Multi-Model Endpoints"
- Lab 4 due Sat Oct 31 — 9 days; Lab 5 assigned today

**Lab 5 Start Advice:** "Get Part 1 (canary deployment) working first — it's the foundational component. Once the canary infrastructure is in place, Parts 2 (auto-scaling) and 3 (batch transform) are relatively independent. Parts 4 and 5 depend on your Lab 3 option."

**Figure:** *Five-takeaway summary card.* Lab 4 countdown (9 days, amber). Lab 5 launch card (23 days, teal). DORA matrix thumbnail showing NorthStar's trajectory from Low to Medium-High.

**Notes:** "Two labs active simultaneously (Lab 4 due Oct 31, Lab 5 just assigned) means time management is critical for the next 2 weeks. Prioritize Lab 4 completion — it's due first and Lab 5 depends on it. If Lab 4 isn't done by Oct 28, focus everything there and plan to start Lab 5 on Nov 1 with 2 weeks remaining."
