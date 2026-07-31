---
lecture: L17
title: Deployment & Scaling II — Security, Compliance & Lab 5 Deep Dive
date: Thursday, October 29, 2026
week: 9
arc: Build
reading_due: "Deployment at Scale — Security through Key Takeaways"
lab_due: "Lab 4 due Sat Oct 31 (2 days); Lab 5 due Sat Nov 14"
slides_target: 15
---

# L17: Deployment & Scaling II — Security, Compliance & Lab 5 Deep Dive
**Thursday, October 29, 2026 | CS 401R: Engineering Production AI Systems | Fall 2026**

> Deployment at enterprise scale is not just a technical problem — it's a security and governance problem. What you deploy, who authorized it, and what it can access are as important as how you deploy it.

**Reading Due:** *Deployment at Scale* — "Security" through "Key Takeaways"
**Lab 4 Due:** Sat Oct 31 (2 days)
**Lab 5 Reminder:** Due Sat Nov 14 (16 days)

---

## Slide 1 — Title
**Layout:** Left dark panel + right security architecture overview

**Content:**
- Deployment & Scaling II: Security, Compliance & Lab 5
- CS 401R · Lecture 17 · Thursday, October 29, 2026
- ⚠️ Lab 4 Due Saturday — 2 Days

**Figure:** *AI system security layers diagram.* Concentric circle model: innermost (Model artifacts in Model Registry), then (SageMaker endpoint in VPC), then (IAM access control boundary), then (network perimeter: VPC + private subnets), then (compliance controls: CloudTrail, Config, GuardDuty). The outermost layer: Business governance (access reviews, deployment approvals). Each layer labeled. The concentric model communicates: security is defense-in-depth — multiple independent layers, not a single perimeter.

**Notes:** "We've spent several lectures on how to deploy. Today we focus on what secures what you've deployed. AI systems have a larger attack surface than traditional software — they have model artifacts, prompt templates, knowledge bases, and agent tools, each of which is a potential security target. Defense in depth means protecting every layer."

---

## Slide 2 — The AI Security Threat Model
**Layout:** Threat model for NorthStar AI systems

**Content:**
**AI System Threat Model: What Are We Protecting Against?**

**Asset inventory (what we're protecting):**
- Model artifacts (ML intellectual property)
- Training data (customer PII)
- Prompt templates (system design IP)
- Knowledge Base documents (proprietary content)
- Agent tool access (business system integration points)
- Inference outputs (customer data in prediction context)

**Threat actors:**
- External attackers: trying to extract model IP, steal customer data, or disrupt service
- Malicious insiders: rogue employee with legitimate access attempting unauthorized actions
- Compromised supply chain: malicious dependency in training code or serving container
- AI-specific: prompt injection attackers trying to override system behavior

**Attack vectors specific to AI:**
| Attack | Target | Defense |
|--------|--------|---------|
| Model extraction | Model artifacts | Private endpoints; rate limiting |
| Training data extraction | Customer PII | Output filtering; data minimization |
| Prompt injection | Agent/LLM behavior | Guardrails; input validation |
| Model poisoning | Training data quality | Data validation; lineage tracking |
| Adversarial inputs | Model predictions | Input validation; outlier detection |

**Figure:** *Threat model diagram.* STRIDE model adapted for AI: Spoofing (fake prediction requests), Tampering (model artifact modification), Repudiation (no audit trail for decisions), Information Disclosure (PII in model output), Denial of Service (endpoint flooding), Elevation of Privilege (prompt injection to bypass guardrails). Each STRIDE category: one NorthStar example threat, one mitigation. The STRIDE model gives structure to AI security analysis.

**Notes:** "Model extraction is the AI-specific threat that traditional security models don't address. A sophisticated attacker can query your model endpoint thousands of times with crafted inputs, observe the outputs, and train a 'shadow model' that approximates your model's behavior. Your model IP — the expensive training run — walks out the door via the API. Rate limiting and adversarial detection on the endpoint input distribution can detect and limit this attack."

---

## Slide 3 — IAM Deep Dive: NorthStar Security Architecture
**Layout:** Complete IAM role hierarchy for NorthStar

**Content:**
**NorthStar IAM Architecture: The Principle of Least Privilege in Practice**

**User-level roles (human access):**

| Role | Who Gets It | Allowed |
|------|------------|---------|
| `NorthStarMLEngineer` | ML team (4 people) | Train models; access Feature Store; read Model Registry; develop in Studio |
| `NorthStarDataEngineer` | Data team (2 people) | Author Glue jobs; read/write S3 (raw/processed zones); no model access |
| `NorthStarGovernance` | ML lead; compliance officer | Approve Model Registry; read-only access to all resources; cannot deploy |
| `NorthStarReadOnly` | Business stakeholders | Read CloudWatch dashboards; no data or model access |

**Service-level roles (machine access):**

| Role | Used By | Allowed |
|------|---------|---------|
| `GlueExecutionRole` | Glue ETL jobs | S3 read (raw) → write (processed); no SageMaker |
| `SageMakerTrainingRole` | Training jobs | S3 read (processed/features) → write (artifacts); no endpoint |
| `SageMakerPipelineRole` | SageMaker Pipelines | Assume training/processing roles; create training jobs; no endpoint update |
| `DeploymentLambdaRole` | Canary Lambda | Update endpoints; read Model Registry; no training; no data access |
| `MonitoringRole` | Model Monitor | Read captured data; write monitor output; no endpoint modification |

**Key security principle:** The training role cannot update endpoints. The deployment role cannot write training data. The data role cannot access models. Each role is strictly scoped.

**Figure:** *IAM role relationship diagram.* Three tiers: Human Roles (4 roles, top tier), Service Roles (5 roles, middle tier), Resources (S3, SageMaker, Bedrock, bottom tier). Arrows: each role → permitted resources (colored arrows). "Cannot access" shown with X marks. The diagram reveals the access control structure at a glance — no role has unrestricted access; every arrow represents a deliberate, documented permission.

**Notes:** "The `NorthStarGovernance` role is the one that surprises students: it has read-only access to everything, cannot deploy anything, but approves Model Registry entries. This is the separation of concerns: the ML engineer builds and trains; the governance officer reviews and approves; the deployment automation executes. No single person can unilaterally push a model from notebook to production."

---

## Slide 4 — Network Security: VPC Architecture for AI Systems
**Layout:** VPC design for NorthStar AI platform security

**Content:**
**VPC Architecture: Why Private Subnets Matter for AI**

By default, SageMaker resources can egress to the internet. For a production AI system handling customer data, this is unacceptable:
- Training job could exfiltrate training data to an external server
- Model container could be updated with malicious code via internet connectivity
- Bedrock calls would leave the AWS network boundary

**NorthStar VPC Security Architecture:**
```
VPC: 10.0.0.0/16 (NorthStar AI Platform)
├── Private Subnets: 10.0.1.0/24, 10.0.2.0/24 (2 AZs)
│   ├── SageMaker Training Jobs (no public internet access)
│   ├── SageMaker Processing Jobs
│   ├── SageMaker Endpoints
│   └── Lambda functions (health gates, monitoring)
│
└── VPC Endpoints (private connectivity to AWS services):
    ├── com.amazonaws.us-east-1.sagemaker.api
    ├── com.amazonaws.us-east-1.sagemaker.runtime
    ├── com.amazonaws.us-east-1.s3 (Gateway endpoint - free)
    ├── com.amazonaws.us-east-1.bedrock-runtime
    ├── com.amazonaws.us-east-1.glue
    └── com.amazonaws.us-east-1.cloudwatch
```

**What VPC endpoints do:** Enable private connectivity to AWS services without requiring an internet gateway. All traffic stays within the AWS network — it never hits the public internet.

**SageMaker training job VPC configuration:**
```python
estimator = XGBoost(
    ...
    subnets=['subnet-0abc123', 'subnet-0def456'],  # Private subnets
    security_group_ids=['sg-0ghi789'],
    # No internet access: cannot call external URLs
    # Can access S3 via VPC endpoint; SageMaker API via VPC endpoint
)
```

**Figure:** *VPC architecture diagram.* NorthStar VPC box (10.0.0.0/16). Two AZ columns (us-east-1a, us-east-1b) with private subnets. Resources in private subnets: SageMaker Training, Processing, Endpoints, Lambda. VPC Endpoints shown as connection points from private subnets to AWS services (S3, Bedrock, CloudWatch, etc.) without going through the internet. No Internet Gateway attached to private subnets. Security group icons on each resource. The diagram is the NorthStar network security architecture.

**Notes:** "The VPC endpoint for Bedrock is the one students most often miss. If you deploy your Lambda or processing job in a VPC private subnet and call Bedrock without a VPC endpoint, the call fails — there's no internet route. Add the `com.amazonaws.us-east-1.bedrock-runtime` VPC endpoint and the call works over the private AWS network. This is in the Lab 1 Terraform template."

---

## Slide 5 — Data Encryption and Privacy at Deployment Time
**Layout:** Encryption architecture for NorthStar in transit and at rest

**Content:**
**NorthStar Encryption Architecture:**

**At rest:**
- S3 buckets: AES-256 encryption with AWS KMS (customer-managed key `northstar-ai-kms-key`)
- SageMaker Feature Store: encrypted at rest using the same KMS key
- Model artifacts in S3: encrypted (same KMS key)
- CloudWatch Logs: encrypted with KMS key for security-sensitive log groups

**In transit:**
- All S3 traffic: HTTPS (enforced via S3 bucket policy denying HTTP)
- SageMaker API calls: TLS 1.2 minimum (AWS enforced)
- VPC endpoints: traffic never leaves AWS network; encrypted at application layer
- Bedrock API calls: TLS 1.2 minimum; traffic via VPC endpoint (private)

**PII handling in AI systems:**

*Problem:* Training data contains customer PII (name, email, transaction history). The model may inadvertently memorize PII from the training data. Inference requests include PII.

*NorthStar PII controls:*
- Training data: all direct identifiers removed before training; customer represented by `customer_id` (synthetic key)
- Feature Store: PII-free features only (RFM values, segment labels — no name/email)
- Inference requests: `customer_id` → features lookup in Feature Store (PII never passes through ML inference path)
- Model output: probability score only; `customer_id` returned, but no PII reconstructed

**Figure:** *NorthStar data flow with encryption overlay.* Customer data (with PII) → ETL (PII removed) → Feature Store (PII-free features, encrypted at rest). Feature Store → Training Job (encrypted in transit, in VPC) → Model Artifact (encrypted at rest). Inference: customer_id → Feature Store lookup → Endpoint (in VPC) → Prediction score. PII never enters the model training or inference path — it stops at the ETL boundary. Encryption symbols on every storage and transit component.

**Notes:** "The PII architecture decision — using customer_id as the identifier throughout the ML pipeline and only resolving to PII at the business application layer — is the right design for any AI system handling personal data. It means that even if someone gains unauthorized access to model artifacts or the feature store, they get only synthetic IDs and aggregated behavioral features, not customer names and emails. Minimize PII exposure at every point."

---

## Slide 6 — Compliance and Audit Logging for AI Deployments
**Layout:** Audit trail architecture for NorthStar

**Content:**
**The Compliance Requirement: Audit Every AI Decision**

Enterprise AI systems must answer these audit questions:
- Who deployed this model? When? From which code version?
- Who approved the deployment? What were the evaluation results?
- What predictions did the model make? On what data? On what date?
- If a prediction was wrong, which input features produced it?

**NorthStar Audit Architecture:**

**1. CloudTrail:** Captures all AWS API calls
- Every SageMaker action logged: who called it, when, from which IP
- Every Model Registry action: who registered, who approved
- Retained: 7 years (compliance requirement for retail)

**2. Model Registry metadata:**
```python
# Required metadata at Model Registry registration
model_package.create_model_package(
    ModelPackageDescription=f"NorthStar Churn Model v3.0",
    ModelApprovalStatus='PendingManualApproval',
    CustomerMetadataProperties={
        'git_commit': GIT_SHA,
        'training_job_name': TRAINING_JOB_NAME,
        'dataset_version': FEATURE_GROUP_VERSION,
        'evaluation_report_s3_path': EVALUATION_REPORT_S3_URI,
        'trained_by': TEAM_MEMBER_NAME,
        'training_date': datetime.utcnow().isoformat()
    }
)
```

**3. Prediction logging:**
Every churn prediction is logged to S3 (via SageMaker data capture):
```json
{"timestamp": "2026-10-29T14:32:00Z", "customer_id": "C123456",
 "input_features": {"recency": 30, "frequency": 5, "monetary": 250.0, ...},
 "prediction": {"churn_probability": 0.73, "model_version": "v3.0"}}
```

**4. Human decision audit:** When the Model Registry approval is given, the governance officer's name and approval timestamp are recorded in the approval workflow.

**Figure:** *Audit trail architecture diagram.* Four audit sources: CloudTrail (API calls), Model Registry (approval records), Data Capture (prediction logs), CloudWatch Logs (operational logs). All four feed into: S3 audit archive (7-year retention, write-once Glacier Deep Archive). Query layer: Amazon Athena for ad hoc queries on audit logs. Access: only `NorthStarGovernance` role can query audit logs. The diagram shows: complete, queryable, immutable audit trail.

**Notes:** "Seven-year retention for audit logs is not arbitrary — retail companies with customer financial transactions are often subject to regulations requiring financial record retention of 5-7 years. Your AI prediction logs that feed into marketing offers are linked to financial transactions (e.g., discount offers). When in doubt, retain longer. Storage in S3 Glacier Deep Archive costs $0.00099/GB/month — for NorthStar's prediction volume, this is < $5/month for 7 years of predictions."

---

## Slide 7 — Model Governance: The Approval Workflow
**Layout:** Model governance workflow from training to production

**Content:**
**The NorthStar Model Governance Workflow:**

```
Stage 1: Model Trained
└── ML Engineer submits model to Registry (status: PendingManualApproval)
└── Evaluation report linked; all metadata required

Stage 2: Automated Quality Gate (Lambda)
└── Checks: metadata complete? Evaluation report present? AUC ≥ 0.72?
└── If all pass → status: QualityGatePassed
└── If fail → status: Rejected; notification to ML Engineer

Stage 3: Manual Review (NorthStarGovernance role only)
└── Governance officer reviews evaluation report
└── Checks: segment performance, calibration, fairness metrics
└── Approves → status: Approved
└── Rejects with comments → status: Rejected
└── SLA: review within 48 hours

Stage 4: Automated Deployment (triggered on Approved status)
└── CodePipeline deployment stage activates
└── Canary deployment begins (10% traffic)
└── Health gate monitoring starts

Stage 5: Deployment Record
└── Deployment timestamp, deployed-by (automation role), reviewer name,
    model version is all written to the audit log
```

**Figure:** *Governance workflow swimlane diagram.* Three lanes: ML Engineer, Automated System, Governance Officer. Each stage placed in the appropriate lane with the actions taken. Status progression: PendingManualApproval → QualityGatePassed → Approved → Deploying → Live. Timestamps shown at each status change. The swimlane shows: no single person controls the full pipeline; multiple roles are required at different stages.

**Notes:** "The 48-hour governance review SLA is real. At enterprise companies with AI governance boards, model approvals take days, not minutes. Part of your job as an ML engineer is to make the evaluation report so clear that the governance officer can review it in 30 minutes and make a confident decision. An evaluation report that requires the reviewer to ask 10 clarifying questions is a poorly written evaluation report."

---

## Slide 8 — Lab 5 Deep Dive: Architecture and Common Issues
**Layout:** Lab 5 architecture details and anticipated issues

**Content:**
**Lab 5: Deployment & Scaling — Architecture Deep Dive**

**Part 1: Canary Deployment — The Lambda Health Gate**

The most complex component in Lab 5 is the Lambda health gate:
```python
import boto3
import json

def lambda_handler(event, context):
    """Health gate: check canary metrics; advance or rollback."""
    sagemaker = boto3.client('sagemaker')
    cw = boto3.client('cloudwatch')
    
    endpoint_name = 'northstar-churn-prod'
    
    # Get current canary weight
    endpoint_desc = sagemaker.describe_endpoint(EndpointName=endpoint_name)
    variants = endpoint_desc['ProductionVariants']
    canary = next(v for v in variants if 'Canary' in v['VariantName'])
    current_weight = canary.get('CurrentWeight', 0)
    
    # Get metrics for the past hour
    canary_error_rate = get_cw_metric(cw, endpoint_name, 'Canary-v3-0', 
                                      'ModelLatencyErrorRate', minutes=60)
    prod_error_rate = get_cw_metric(cw, endpoint_name, 'Production-v2-3',
                                    'ModelLatencyErrorRate', minutes=60)
    
    # Decision logic
    if canary_error_rate is None or prod_error_rate is None:
        print("Insufficient data — waiting for next check cycle")
        return {'status': 'WAITING', 'reason': 'insufficient_data'}
    
    if canary_error_rate > prod_error_rate * 2.0:
        # Hard failure: rollback
        update_variant_weights(sagemaker, endpoint_name, canary_weight=0)
        notify_on_call("Canary rollback triggered", canary_error_rate)
        return {'status': 'ROLLBACK'}
    
    if canary_error_rate <= prod_error_rate * 1.1:
        # Healthy: advance to next weight
        next_weight = advance_canary_weight(current_weight)
        update_variant_weights(sagemaker, endpoint_name, canary_weight=next_weight)
        return {'status': 'ADVANCED', 'new_weight': next_weight}
    
    # Soft warning: hold current weight
    return {'status': 'HOLD', 'reason': 'elevated_error_rate'}
```

**Common Lab 5 issues:**
- Lambda `update_variant_weights` fails: check `sagemaker:UpdateEndpointWeightsAndCapacities` in Lambda role
- CloudWatch metric lag: metrics take 2-3 minutes to appear; add retry logic with backoff
- Canary weight = 0 at start: first health check at 10% must occur after 15 minutes of traffic

**Figure:** *Lambda health gate state machine.* States: WAITING → (after 15 min data) → HEALTHY/HOLDING/ROLLBACK. Transitions: Healthy gate → ADVANCE (progress to next weight). Hold → RETRY_NEXT_CYCLE. Rollback → ROLLBACK_COMPLETE → notify. State machine diagram communicates the Lambda decision logic as a flow.

**Notes:** "The CloudWatch metric lag is the most confusing Lab 5 issue. You deploy the canary; your Lambda runs 15 minutes later and returns 'insufficient data' because CloudWatch hasn't collected enough data points for the metric. Add a minimum data points check: only evaluate if CloudWatch returns at least 10 data points for the metric period. Fewer than 10: return WAITING."

---

## Slide 9 — Lab 5 Part 2: Auto-Scaling and Load Test
**Layout:** Auto-scaling lab requirements and load test setup

**Content:**
**Lab 5 Part 2: Auto-Scaling and Load Test**

**What you'll configure:**
```python
# Register scalable target
autoscaling.register_scalable_target(
    ServiceNamespace='sagemaker',
    ResourceId=f'endpoint/northstar-churn-prod/variant/Production-v3-0',
    ScalableDimension='sagemaker:variant:DesiredInstanceCount',
    MinCapacity=1,
    MaxCapacity=4  # Reduced from 8 for course lab (cost control)
)

# Target tracking policy
autoscaling.put_scaling_policy(
    PolicyName='northstar-churn-lab5-scaling',
    ServiceNamespace='sagemaker',
    ResourceId=f'endpoint/northstar-churn-prod/variant/Production-v3-0',
    ScalableDimension='sagemaker:variant:DesiredInstanceCount',
    PolicyType='TargetTrackingScaling',
    TargetTrackingScalingPolicyConfiguration={
        'TargetValue': 50.0,  # Lower target for lab (easier to trigger scaling)
        'PredefinedMetricSpecification': {
            'PredefinedMetricType': 'SageMakerVariantInvocationsPerInstance'
        },
        'ScaleInCooldown': 120,
        'ScaleOutCooldown': 60
    }
)
```

**Load test deliverable:** Use Locust (Python) or Apache Bench to demonstrate:
1. Start at 1 instance (baseline metric: < 50 invocations/instance/minute)
2. Ramp to 75 invocations/instance/minute (should trigger scale-out)
3. Capture CloudWatch screenshot showing instance count increase from 1 to 2

**Lab 5 grading note:** The load test screenshot is worth 10 points. CloudWatch shows instance count and invocations/instance — screenshot both metrics during the scale-out event.

**Figure:** *Auto-scaling event diagram for Lab 5.* Two-panel figure. Left: CloudWatch metric `InvocationsPerInstance` — starts at 20/min (1 instance), ramps to 75/min at minute 5, scale-out event at minute 6 (instance count 1→2), metric drops to 37/min (shared across 2 instances). Right: instance count metric — flat at 1 from minutes 0-5, spikes to 2 at minute 6, then remains at 2. The figures show exactly what the load test should demonstrate.

**Notes:** "For the load test, a simple Python script using threading and the boto3 SageMaker Runtime client is sufficient — you don't need to install Locust. Send requests at a controlled rate (e.g., 5 requests/second using a time.sleep loop) for 10 minutes. Watch CloudWatch in another window. When you see instance count increase, take the screenshot. That screenshot is your Lab 5 Part 2 deliverable."

---

## Slide 10 — Lab 5 Part 3: Batch Transform (Monthly Scoring)
**Layout:** Batch Transform implementation for monthly churn scoring

**Content:**
**Lab 5 Part 3: Batch Transform for Monthly Scoring**

**What you'll build:**
1. A SageMaker Batch Transform job that scores 10,000 test customers (not 500K — cost control)
2. An EventBridge rule that triggers the batch job on a monthly schedule
3. Output to S3 with a specific format for business reporting

**Batch Transform job configuration:**
```python
from sagemaker.transformer import Transformer

transformer = Transformer(
    model_name='northstar-churn-v3-0',
    instance_count=2,  # 2 instances for lab (5× real scale)
    instance_type='ml.m5.xlarge',
    output_path=f's3://northstar-artifacts/batch-scoring/{MONTH_TAG}/',
    strategy='MultiRecord',
    assemble_with='Line',
    accept='text/csv'
)

transformer.transform(
    data='s3://northstar-processed/customers/monthly-scoring-10k.csv',
    content_type='text/csv',
    split_type='Line',
    job_name=f'northstar-monthly-scoring-{MONTH_TAG}',
    wait=True
)
```

**EventBridge monthly trigger:**
```python
events_client.put_rule(
    Name='northstar-monthly-scoring-trigger',
    ScheduleExpression='cron(0 2 1 * ? *)',  # First of each month at 2:00 AM UTC
    State='ENABLED'
)
```

**Expected output format:**
```csv
customer_id,churn_probability,prediction_date,model_version
C001,0.73,2026-10-01,v3.0
C002,0.22,2026-10-01,v3.0
...
```

**Figure:** *Batch Transform execution timeline.* Gantt chart: EventBridge trigger (Day 1, 2:00 AM) → SageMaker Batch Transform job (2:00-2:47 AM, 47 minutes) → Output to S3 (2:47 AM) → Business reporting reads S3 (6:00 AM, when business opens). Annotations: job duration, instance count (2), records processed (10K for lab, 500K for production). The timeline indicates that batch scoring runs overnight and that results are ready before business opens.

**Notes:** "The cron expression `cron(0 2 1 * ? *)` — first of each month at 2:00 AM UTC — uses AWS EventBridge cron syntax. The `?` in the day-of-week position is required when you specify a day of the month. Common mistake: `cron(0 2 1 * * *)` — the extra `*` is invalid in AWS cron format and the rule will fail to create."

---

## Slide 11 — Building Secure Deployment Patterns: Putting It Together
**Layout:** Secure deployment architecture combining all security layers

**Content:**
**The Secure NorthStar Deployment Pipeline (All Layers Combined):**

**Code security:**
- All code in Git; PRs reviewed before merge to main
- Dependencies: pinned versions in requirements.txt; Dependabot scans for vulnerabilities
- Secrets: none in code; all in AWS Secrets Manager

**Pipeline security:**
- CodePipeline in VPC; all CodeBuild builds in private subnet
- IAM: separate roles per pipeline stage; least privilege
- Artifact signing: CodeBuild generates checksums for artifacts; SageMaker verifies before use

**Model security:**
- Model Registry: approval required before deployment
- Audit trail: CloudTrail captures every Registry action
- Artifacts: encrypted in S3 (KMS); accessible only via training/deployment roles

**Endpoint security:**
- Private subnet; accessible only within VPC or via PrivateLink
- API authentication: caller must have SageMaker runtime invoke permissions
- Data capture: 20% of requests logged to encrypted S3

**LLM/Agent security:**
- Bedrock Guardrails: input + output filtering on all LLM invocations
- Agent: authority matrix enforced; tool calls logged
- Prompt templates: version-controlled; no customer PII in prompts

**Figure:** *Security control matrix.* 5-column table: Security Control, Where it Lives, What It Protects, Who Configured It, Who Audits It. Each row: one control from the list above. Color-coded by security layer (code, pipeline, model, endpoint, LLM). The matrix communicates: security controls span every layer, are configured by the ML/platform team, and are audited by the governance officer.

**Notes:** "The security control matrix is the deliverable for a security review. When a CISO or security team asks 'how is your AI system secured?', this matrix is the evidence. Each row maps to a real configuration in your Terraform code, your IAM policies, or your Bedrock Guardrails configuration. It's not just a documentation exercise — every item in this matrix must be verifiable in the actual system."

---

## Slide 12 — Compliance Frameworks for Enterprise AI
**Layout:** Compliance framework overview relevant to NorthStar

**Content:**
**Compliance Frameworks That Apply to NorthStar:**

**SOC 2 Type II (most relevant for SaaS AI):**
- Trust Service Criteria: Security, Availability, Processing Integrity, Confidentiality, Privacy
- For NorthStar AI: model outputs must be accurate and complete (Processing Integrity); customer data must be protected (Privacy/Confidentiality); system available per SLA (Availability)

**PCI DSS (payment card industry — relevant for retail):**
- Requirement 6: Develop secure software (security testing of AI)
- Requirement 10: Implement logging and monitoring (audit logs)
- Requirement 12: Information Security Policy (AI governance policy)

**GDPR / CCPA (data privacy — relevant for customer data):**
- Right to explanation: if AI churn prediction affects a customer's treatment, they may have a right to know why
- SHAP values support explainability requirements
- Data minimization: only use the customer data needed for the AI function

**EU AI Act (emerging — relevant for high-risk AI systems):**
- NorthStar Customer Service Agent: likely classified as "limited risk" (disclosure required)
- If churn prediction affects credit decisions: could be "high risk" (requires conformity assessment)

**Figure:** *Compliance framework applicability matrix.* NorthStar AI systems (rows: Churn, Offers, Agent) × compliance frameworks (columns: SOC 2, PCI DSS, GDPR, EU AI Act). Each cell: applicability level (Applies, Partially Applies, Not Applicable) and key requirement. Color-coded: green (applicable, controls in place), amber (applicable, partial controls), red (applicable, controls needed). The matrix communicates: compliance is multi-framework and system-specific.

**Notes:** "The EU AI Act is the emerging compliance framework most likely to affect your career. Passed in 2024, it creates four risk categories for AI systems — unacceptable (banned), high-risk (strict requirements), limited-risk (transparency requirements), minimal risk (no requirements). Understanding where your AI system sits in this classification is a professional responsibility. The churn model alone is probably minimal/limited risk. If it feeds into credit decisions or employment decisions, it becomes high-risk."

---

## Slide 13 — Production Readiness Review: Before Lab 5 Goes Live
**Layout:** Production readiness review framework

**Content:**
**What Does "Production Ready" Mean for an AI System?**

Production readiness is not binary — it's a maturity assessment. Use this framework before declaring any AI system production-ready:

**Production Readiness Review (PRR) Checklist:**

**Reliability:**
- [ ] Auto-scaling configured with appropriate min/max capacity
- [ ] Canary deployment in place with automated rollback
- [ ] Rollback procedure tested (not just written — actually tested)
- [ ] SLA defined and monitored (CloudWatch alarm)

**Observability:**
- [ ] CloudWatch dashboard showing key operational metrics
- [ ] Alerting configured for all critical failure conditions
- [ ] Trace/audit logging enabled for all AI decisions
- [ ] On-call runbook written and current

**Security:**
- [ ] All resources in VPC with least-privilege IAM
- [ ] Audit logging enabled (CloudTrail + data capture)
- [ ] No credentials in code; secrets in Secrets Manager
- [ ] Guardrails enabled for all LLM endpoints

**Operational:**
- [ ] Deployment runbook documented and tested
- [ ] Monitoring runbook: what to do for each alert type
- [ ] Capacity plan: when to add instances as traffic grows
- [ ] Cost budget set with alerts

**Figure:** *PRR checklist card.* Four sections (Reliability, Observability, Security, Operational) with checkboxes. Current Lab 5 state assessment: Reliability: 3/4 ✅ (missing: rollback tested). Observability: 2/4 ⚠️ (missing: runbook, trace logging). Security: 3/4 ✅ (missing: GuardDuty). Operational: 2/4 ⚠️ (missing: capacity plan, runbook). Overall: 10/16 = 63% production-ready. Honest assessment communicating what the labs achieve and what remains.

**Notes:** "The PRR checklist is the honest answer to 'is this system production-ready?' For a course lab, the target is not 100% — it's understanding which items matter most and why. The most important items: rollback tested, alerting configured, no credentials in code. Everything else is important but can be addressed post-launch for a non-critical system. For a system that handles financial transactions or medical decisions, all 16 must be complete before launch."

---

## Slide 14 — The Build Arc: What You've Accomplished
**Layout:** Build arc retrospective — 9 weeks of progress

**Content:**
**The Build Arc: Weeks 1-9 in Review**

You started Lab 1 with an empty AWS account and a Terraform template. After 9 weeks and 5 labs (Labs 1-5 by Saturday), you have:

**Infrastructure (Lab 1):** S3 4-zone architecture; VPC with private subnets and VPC endpoints; SageMaker Domain; IAM 3-role design; Terraform IaC

**Data Engineering (Lab 2):** Glue ETL pipelines; Feature Store with RFM features; Data quality gates; Feature lineage tracking; Scheduled Glue Workflow

**Model Development (Lab 3):** XGBoost Churn Model trained with SageMaker; MLflow experiment tracking; SHAP explainability; Model Registry registration; Bedrock RAG (Option A); Bedrock Agent (Option B)

**CI/CD Pipeline (Lab 4):** SageMaker Pipeline (5-step automated training); CodePipeline integration; Test suite (unit + integration + evaluation gate); Evaluation report as artifact

**Deployment & Scaling (Lab 5):** Canary deployment with automated health gate; Auto-scaling (1-4 instances); Batch Transform monthly scoring; Rollback mechanism

**What this platform can do:**
- Score 500K customers overnight for monthly churn campaign
- Serve real-time churn predictions in < 200ms
- Generate personalized offers using RAG (if Option A)
- Handle customer service interactions autonomously (if Option B)
- Update its own models via CI/CD when new data arrives
- Self-monitor and roll back if performance degrades

**Figure:** *NorthStar platform capability map.* The complete Lab 1-5 architecture diagram. Each component labeled with which lab built it. Capability summary card alongside: 5 core capabilities listed. "Platform maturity level: 3" indicator (from the Slide 9 maturity model in L10). The diagram is a capstone view — everything you've built, on one page.

**Notes:** "When you present this platform architecture in a job interview, you're showing a production-grade AI system, not a toy project. Every component exists for a reason. Be able to explain each one: what it does, why it's there, what would break if it were missing. That conversation — walking through this diagram component by component — is what a senior ML engineering interview looks like."

---

## Slide 15 — Key Takeaways + What's Next: The Operate Arc
**Layout:** Takeaways + Operate arc preview

**Content:**
**Key Takeaways:**
1. AI security is defense-in-depth: threat model first, then controls at each layer (IAM, VPC, encryption, audit logging, guardrails)
2. Model governance requires separation of roles: ML engineer trains, governance officer approves, automation deploys — no single person controls the full pipeline
3. Compliance frameworks (SOC 2, PCI DSS, GDPR, EU AI Act) create specific requirements for AI systems that must be addressed in architecture and operations
4. Production readiness is a checklist, not a feeling: use the PRR framework to objectively assess readiness before launch
5. By Lab 5, the NorthStar platform achieves MLOps Level 3: automated CI/CD, canary deployment, auto-scaling, monthly batch scoring, and rollback capability

**Next Session (Tue Nov 3):**
- Topic: Security, Privacy & Compliance I — deep dive into AI-specific compliance; the EU AI Act; responsible AI frameworks
- Reading due: *AI Governance* — "Regulation Overview" through "Technical Controls"
- **Lab 4 due Saturday** — two days; finish strong

**The Operate Arc begins Week 10 (Nov 3):**
- 4 weeks of Build gave you a platform
- 4 weeks of Operate gives you a platform that *earns its keep*: monitoring, economics, business value, reliability

**Figure:** *Course arc visual.* Full 15-week arc with color coding: Build (Weeks 1-9, teal), Bridge (Weeks 9-10, gradient), Operate (Weeks 11-13, navy), Project (Weeks 14-15, gold). Current position marked at end of Build arc. "Level 3 MLOps Platform Achieved" badge on the Build section. Operate section titles previewed: Metrics, Monitoring, Reliability, Economics, Business Value. The visual communicates: you've built the engine; now you'll learn to drive it.

**Notes:** "The transition from Build to Operate is conceptually important. In Build, the question was: does the system work? In Operate, the question is: is the system working *well*, and is it *worth* what it costs? The Operate arc introduces the disciplines that determine whether an AI platform creates business value — which is the only metric that ultimately matters in enterprise AI."
