# L15: Continuous Delivery II — Infrastructure, Scaling & Multi-Region — Figures

## Slide 1 — Title

**Figure:** *Multi-region AI platform overview.* Two AWS region boxes (us-east-1 as primary, us-west-2 as secondary). Each region: SageMaker endpoint, Bedrock KB, CloudWatch monitoring. Global Traffic Manager (Route 53) at top routing traffic: 100% to primary normally, failover arrow to secondary. Data replication arrow between regions: "Feature Store replicated; Model artifacts synced." The diagram communicates: production AI at enterprise scale requires thinking beyond a single region.

---

## Slide 2 — SageMaker Endpoint Scaling Architecture

**Figure:** *Auto-scaling response diagram.* X-axis: time (minutes 0-20). Y-axis: invocations/minute (left) and instance count (right). Traffic spike at minute 5: invocations jump from 50 to 180/min. After 60 seconds: instance count increases from 1 to 3. Traffic decreases at minute 12: invocations drop to 60/min. After 300 seconds: instance count decreases back to 1. The asymmetric cooldown (60s scale-out, 300s scale-in) visually apparent.

---

## Slide 3 — SageMaker Batch Transform: Scaling for Batch Workloads

**Figure:** *Batch Transform scaling diagram.* S3 input (500K records) → Batch Transform job (fan-out to 10 parallel instances) → each instance processes ~50K records → S3 output (500K predictions). Timeline shows: 45-minute total duration. Below: cost breakdown: 10 instances × $0.30/hr × 0.75 hr = $2.25. Compare: "Real-time endpoint alternative: 6 hours × 1 instance × $0.30/hr = $1.80, but processes serially and blocks the endpoint for 6 hours." Batch Transform wins on throughput, not cost.

---

## Slide 4 — CI/CD Infrastructure: AWS CodePipeline Architecture

**Figure:** *CodePipeline 6-stage visual.* Each stage is shown as a horizontal panel with the stage name, tool (GitHub/CodeBuild/SageMaker/Lambda), and a status indicator (green checkmark or amber clock). Manual Approval stage shown with email icon and "Approval pending" status. The full pipeline visualizes the process from code commit to production deployment as 6 structured stages, with gates at stages 2, 4, and optionally 5.

---

## Slide 5 — Infrastructure as Code for CI/CD: The Terraform Layer

**Figure:** *Terraform module dependency graph.* Module boxes: codepipeline, codebuild, sagemaker_pipeline. Arrows: codepipeline depends on codebuild (build stage), codepipeline depends on sagemaker_pipeline (train stage). Environment boxes: dev and prod both instantiate all three modules with different variable values. The graph shows: CI/CD infrastructure has its own dependency structure, managed by Terraform.

---

## Slide 6 — SageMaker Real-Time Inference: Performance Architecture

**Figure:** *Latency breakdown waterfall chart.* Horizontal waterfall showing total request time (~35ms). Segments: Network (client→LB): 8ms, Internal routing: 2ms, Container (deserialization + inference + serialization): 20ms, Network (LB→client): 5ms. Largest segment: container time (57%). Cold start bar shown separately: 30,000ms (30 seconds) — visually dwarfs the warm request bar, communicating: cold starts are the latency outlier, not model inference.

---

## Slide 7 — Bedrock Latency and Throughput: Operating Foundation Models

**Figure:** *Bedrock latency comparison chart.* Bar chart: three model tiers (Haiku, Sonnet, Opus) × two scenarios (without prompt cache, with prompt cache). Haiku: 0.8s / 0.6s. Sonnet: 1.8s / 1.3s. Opus: 4.2s / 3.0s. NorthStar SLA (3s) marked as a horizontal line. Only Haiku and Sonnet (with cache) consistently meet the SLA. Sonnet (without cache) occasionally exceeds. Opus: always exceeds. Decision: use Sonnet with prompt caching.

---

## Slide 8 — Multi-Region Architecture: When You Need It and Why

**Figure:** *Multi-region architecture diagram.* Primary (us-east-1) and secondary (us-west-2) side by side. Route 53 at top with health check arrows to both regions. Replication arrows between regions: S3 (continuous), Feature Store (hourly), Bedrock KB (weekly). Failover path: Route 53 detects a primary failure → DNS TTL is 60s → all traffic reroutes to the secondary → 5-minute RTO. RPO annotation: "1 hour data loss acceptable for churn use case."

---

## Slide 9 — Infrastructure Cost Modeling for CI/CD

**Figure:** *Infrastructure cost breakdown bar chart.* Stacked bar with two categories: CI/CD (running costs) and Platform (inference costs). CI/CD costs: ~$17/month. Platform inference: ~$430/month. Inference dominates. Breakdown by system: Churn ($110), RAG ($90), Agent ($230). Key insight: inference costs >> CI/CD costs for this AI workload.

---

## Slide 10 — Lab 5 Walkthrough: Architecture and Deliverables

**Figure:** *Lab 5 deliverable checklist.* Five-part list with required/optional labels. Architecture diagram thumbnail showing where each deliverable fits in the NorthStar platform. Timeline: 23 days → start now. "Dependency: Lab 4 must be working before Lab 5 can begin."

---

## Slide 11 — Deployment Security: IAM and Network Controls

**Figure:** *IAM role separation diagram.* Four boxes (CodePipeline, CodeBuild, SageMaker Pipeline, Deployment Lambda), each with their specific IAM role. Arrows show what each role can access (permitted resources in green, blocked resources in red). "Trust boundary" line between CI/CD roles and production resources — only Deployment Lambda can cross it, and only with explicit endpoint update permissions. The diagram communicates: least privilege is enforced at every stage of the pipeline.

---

## Slide 12 — Monitoring the Pipeline Itself

**Figure:** *Pipeline health dashboard mockup.* Four metric panels: Execution Success Rate (trend line, last 30 days: 87% average, one FAILED execution highlighted), Average Duration (trend: 45 min → 62 min, rising trend alert), Days Since Last Deploy (3 days, green), Test Failure Rate (12%, amber warning). Clean, operational dashboard view.

---

## Slide 13 — The DORA Metrics Applied to NorthStar

**Figure:** *DORA performance level matrix.* Four rows (Deployment Frequency, Lead Time, Change Failure Rate, MTTR) × four columns (Low, Medium, High, Elite). NorthStar "Before" position circled in each row (Low or Medium). NorthStar "After Labs 4-5" position marked (Medium to High). "Elite" column highlighted in teal — the aspiration. The matrix communicates: the labs move NorthStar toward Elite performance, not the full way, but significantly forward.

---

## Slide 14 — Putting It Together: The Full NorthStar Deployment Pipeline

**Figure:** *Full NorthStar platform architecture including CI/CD.* The complete NorthStar architecture (from Lab 1 foundation) with the CI/CD overlay: CodePipeline connecting to SageMaker Pipeline, canary deployment to endpoints, health gate Lambda, auto-scaling, batch transform trigger. Also: RAG blue/green KB management, agent alias management. Large, detailed architecture diagram — the "capstone" view of what the lab sequence builds.

---

## Slide 15 — Key Takeaways + What's Next

**Figure:** *Five-takeaway summary card.* Lab 4 countdown (9 days, amber). Lab 5 launch card (23 days, teal). DORA matrix thumbnail showing NorthStar's trajectory from Low to Medium-High.
