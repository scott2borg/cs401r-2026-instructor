# L17: Deployment & Scaling II — Security, Compliance & Lab 5 Deep Dive — Figures

## Slide 1 — Title

**Figure:** *AI system security layers diagram.* Concentric circle model: innermost (Model artifacts in Model Registry), then (SageMaker endpoint in VPC), then (IAM access control boundary), then (network perimeter: VPC + private subnets), then (compliance controls: CloudTrail, Config, GuardDuty). The outermost layer: Business governance (access reviews, deployment approvals). Each layer labeled. The concentric model communicates: security is defense-in-depth — multiple independent layers, not a single perimeter.

---

## Slide 2 — The AI Security Threat Model

**Figure:** *Threat model diagram.* STRIDE model adapted for AI: Spoofing (fake prediction requests), Tampering (model artifact modification), Repudiation (no audit trail for decisions), Information Disclosure (PII in model output), Denial of Service (endpoint flooding), Elevation of Privilege (prompt injection to bypass guardrails). Each STRIDE category: one NorthStar example threat, one mitigation. The STRIDE model gives structure to AI security analysis.

---

## Slide 3 — IAM Deep Dive: NorthStar Security Architecture

**Figure:** *IAM role relationship diagram.* Three tiers: Human Roles (4 roles, top tier), Service Roles (5 roles, middle tier), Resources (S3, SageMaker, Bedrock, bottom tier). Arrows: each role → permitted resources (colored arrows). "Cannot access" shown with X marks. The diagram reveals the access control structure at a glance — no role has unrestricted access; every arrow represents a deliberate, documented permission.

---

## Slide 4 — Network Security: VPC Architecture for AI Systems

**Figure:** *VPC architecture diagram.* NorthStar VPC box (10.0.0.0/16). Two AZ columns (us-east-1a, us-east-1b) with private subnets. Resources in private subnets: SageMaker Training, Processing, Endpoints, Lambda. VPC Endpoints shown as connection points from private subnets to AWS services (S3, Bedrock, CloudWatch, etc.) without going through the internet. No Internet Gateway attached to private subnets. Security group icons on each resource. The diagram is the NorthStar network security architecture.

---

## Slide 5 — Data Encryption and Privacy at Deployment Time

**Figure:** *NorthStar data flow with encryption overlay.* Customer data (with PII) → ETL (PII removed) → Feature Store (PII-free features, encrypted at rest). Feature Store → Training Job (encrypted in transit, in VPC) → Model Artifact (encrypted at rest). Inference: customer_id → Feature Store lookup → Endpoint (in VPC) → Prediction score. PII never enters the model training or inference path — it stops at the ETL boundary. Encryption symbols on every storage and transit component.

---

## Slide 6 — Compliance and Audit Logging for AI Deployments

**Figure:** *Audit trail architecture diagram.* Four audit sources: CloudTrail (API calls), Model Registry (approval records), Data Capture (prediction logs), CloudWatch Logs (operational logs). All four feed into: S3 audit archive (7-year retention, write-once Glacier Deep Archive). Query layer: Amazon Athena for ad hoc queries on audit logs. Access: only `NorthStarGovernance` role can query audit logs. The diagram shows: complete, queryable, immutable audit trail.

---

## Slide 7 — Model Governance: The Approval Workflow

**Figure:** *Governance workflow swimlane diagram.* Three lanes: ML Engineer, Automated System, Governance Officer. Each stage placed in the appropriate lane with the actions taken. Status progression: PendingManualApproval → QualityGatePassed → Approved → Deploying → Live. Timestamps shown at each status change. The swimlane shows: no single person controls the full pipeline; multiple roles are required at different stages.

---

## Slide 8 — Lab 5 Deep Dive: Architecture and Common Issues

**Figure:** *Lambda health gate state machine.* States: WAITING → (after 15 min data) → HEALTHY/HOLDING/ROLLBACK. Transitions: Healthy gate → ADVANCE (progress to next weight). Hold → RETRY_NEXT_CYCLE. Rollback → ROLLBACK_COMPLETE → notify. State machine diagram communicates the Lambda decision logic as a flow.

---

## Slide 9 — Lab 5 Part 2: Auto-Scaling and Load Test

**Figure:** *Auto-scaling event diagram for Lab 5.* Two-panel figure. Left: CloudWatch metric `InvocationsPerInstance` — starts at 20/min (1 instance), ramps to 75/min at minute 5, scale-out event at minute 6 (instance count 1→2), metric drops to 37/min (shared across 2 instances). Right: instance count metric — flat at 1 from minutes 0-5, spikes to 2 at minute 6, then remains at 2. The figures show exactly what the load test should demonstrate.

---

## Slide 10 — Lab 5 Part 3: Batch Transform (Monthly Scoring)

**Figure:** *Batch Transform execution timeline.* Gantt chart: EventBridge trigger (Day 1, 2:00 AM) → SageMaker Batch Transform job (2:00-2:47 AM, 47 minutes) → Output to S3 (2:47 AM) → Business reporting reads S3 (6:00 AM, when business opens). Annotations: job duration, instance count (2), records processed (10K for lab, 500K for production). The timeline indicates that batch scoring runs overnight and that results are ready before business opens.

---

## Slide 11 — Building Secure Deployment Patterns: Putting It Together

**Figure:** *Security control matrix.* 5-column table: Security Control, Where it Lives, What It Protects, Who Configured It, Who Audits It. Each row: one control from the list above. Color-coded by security layer (code, pipeline, model, endpoint, LLM). The matrix communicates: security controls span every layer, are configured by the ML/platform team, and are audited by the governance officer.

---

## Slide 12 — Compliance Frameworks for Enterprise AI

**Figure:** *Compliance framework applicability matrix.* NorthStar AI systems (rows: Churn, Offers, Agent) × compliance frameworks (columns: SOC 2, PCI DSS, GDPR, EU AI Act). Each cell: applicability level (Applies, Partially Applies, Not Applicable) and key requirement. Color-coded: green (applicable, controls in place), amber (applicable, partial controls), red (applicable, controls needed). The matrix communicates: compliance is multi-framework and system-specific.

---

## Slide 13 — Production Readiness Review: Before Lab 5 Goes Live

**Figure:** *PRR checklist card.* Four sections (Reliability, Observability, Security, Operational) with checkboxes. Current Lab 5 state assessment: Reliability: 3/4 ✅ (missing: rollback tested). Observability: 2/4 ⚠️ (missing: runbook, trace logging). Security: 3/4 ✅ (missing: GuardDuty). Operational: 2/4 ⚠️ (missing: capacity plan, runbook). Overall: 10/16 = 63% production-ready. Honest assessment communicating what the labs achieve and what remains.

---

## Slide 14 — The Build Arc: What You've Accomplished

**Figure:** *NorthStar platform capability map.* The complete Lab 1-5 architecture diagram. Each component labeled with which lab built it. Capability summary card alongside: 5 core capabilities listed. "Platform maturity level: 3" indicator (from the Slide 9 maturity model in L10). The diagram is a capstone view — everything you've built, on one page.

---

## Slide 15 — Key Takeaways + What's Next: The Operate Arc

**Figure:** *Course arc visual.* Full 15-week arc with color coding: Build (Weeks 1-9, teal), Bridge (Weeks 9-10, gradient), Operate (Weeks 11-13, navy), Project (Weeks 14-15, gold). Current position marked at end of Build arc. "Level 3 MLOps Platform Achieved" badge on the Build section. Operate section titles previewed: Metrics, Monitoring, Reliability, Economics, Business Value. The visual communicates: you've built the engine; now you'll learn to drive it.
