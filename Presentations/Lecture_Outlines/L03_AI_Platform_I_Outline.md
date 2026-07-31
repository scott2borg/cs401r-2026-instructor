---
lecture: L03
title: AI Platform & Cloud Architecture I
date: Thursday, September 10, 2026
week: 2
arc: Build
reading_due: "AI Platform & Cloud Architecture — Motivation through Core Platform Components"
lab_due: "Lab 1 due Sat Sep 19"
slides_target: 16
---

# L03: AI Platform & Cloud Architecture I
**Thursday, September 10, 2026 | CS 401R: Engineering Production AI Systems | Fall 2026**

> What is an AI platform, and why does it exist? This lecture establishes the architectural foundation for the entire course: platform vs. point solution, reference architectures, core components, and the compound-returns case for platform investment. Students leave knowing what they're building in Lab 1 and why.

**Reading Due:** *AI Platform & Cloud Architecture* — "Motivation" through "Core Platform Components"  
**Lab 1 Due:** Saturday, September 19, midnight

---

## Slide 1 — Title
**Layout:** Left dark panel + right architecture visualization

**Content:**
- AI Platform & Cloud Architecture I
- CS 401R · Lecture 03 · Thursday, September 10, 2026
- What is a platform? Reference architectures. Core components.

**Figure:** *Multi-tier AWS architecture diagram.* Clean, professional-quality AWS architecture diagram showing three horizontal tiers: (1) Data Tier — S3 buckets, Glue ETL, Feature Store; (2) Compute/Model Tier — SageMaker training, endpoints, Bedrock; (3) Operational Tier — CloudWatch, CodePipeline, IAM. Arrow flows show data moving up through tiers. AWS official service icons. Light gray background. The diagram is the NorthStar platform they'll build this semester — a preview of Lab 1 and beyond.

**Notes:** "Thursday's lectures in this course tend to go deep on a specific architectural topic. Tuesday's lectures are more conceptual. Today is about architecture — be ready to think in systems." Ask: "Before we start: how many of you have provisioned an AWS service before?" Calibrate the room. Most students will have some experience but not production-grade architecture experience. "That's fine — you don't need experience, you need judgment. That's what this lecture gives you."

---

## Slide 2 — What Is an AI Platform (and Why Does It Exist)?
**Layout:** Problem → Solution framing, with a real cost comparison

**Content:**
**The Point-Solution Trap:**
- Team A spins up their own SageMaker environment. Team B does the same. Team C does too.
- Result: 4 teams with 4 siloed environments, no shared data, no shared tooling, no shared governance
- The same pipeline problem is solved 4 different ways
- One model breaks. No runbook. No shared monitoring. Team runs forensics in isolation.
- 18 months in: 12 proof-of-concepts. 0 shared infrastructure. Cost scales linearly with teams.

**The Platform Alternative:**
- A shared, governed infrastructure for building, deploying, and operating AI systems at scale
- Enables: shared data assets, reusable pipeline components, consistent governance, compound cost reduction
- "A platform makes building the second AI system dramatically cheaper than the first"

**The compound-returns thesis:** Platform investment pays off at AI system #3 or #4. Most organizations give up at system #2.

**Figure:** *Cost comparison chart.* X-axis: Number of AI systems deployed. Y-axis: Total cost. Two lines: "Point Solutions" (linear, steep upward slope) and "Platform Approach" (high initial investment, then flattening curve). Lines cross at ~3 systems. Shaded area between the lines labeled "Platform ROI" — widens with each additional system. Data points marked at 1, 3, 5, 10 systems with illustrative cost values. Clean, white background, two-color.

**Notes:** "The economic argument for a platform is not abstract. It is math." The single-system case is almost always cheaper with a point solution — the overhead of standing up a proper platform is real. The case for the platform becomes compelling at system #2-3, and decisive at system #4+. "NorthStar has three AI systems. That's exactly the point where platform investment starts paying off — which is why the CDO chose to build one platform instead of three separate environments."

---

## Slide 3 — Platform Maturity Model
**Layout:** Five-level maturity stack with characteristics at each level

**Content:**
**Level 0 — Ad Hoc:** Individual notebooks, no shared infrastructure, no governance, no reproducibility. Typical for early exploration.

**Level 1 — Shared Infrastructure:** Common AWS account, shared S3 structure, some IAM policies. Pipelines are still manual. Typical for first 1-2 production systems.

**Level 2 — Automated Pipelines:** Training and evaluation automated, model registry in use, some CI/CD. Most enterprise teams land here and stall.

**Level 3 — Self-Service Platform:** Engineers can deploy new AI systems without infrastructure tickets. Governance built into the platform. Feature store in use.

**Level 4 — Compound Platform:** Platform learns from operational data across all systems. Cost optimization is automated. Cross-system feature sharing. Few enterprises reach this level.

**NorthStar Goal for this course: Level 2 → early Level 3**

**Figure:** *Staircase maturity model.* Five steps from lower-left to upper-right, each step wider and taller. Step color progresses from gray (Level 0) to bright blue (Level 4). Each step labeled with level number, name, and 2-3 word description. A gold arrow sits at the Level 2→3 transition, labeled "Course target." A "You are here" marker at Level 1 (where most student projects start). The visual makes the progression clear and the goal specific.

**Notes:** "Most enterprise teams are at Level 1 or Level 2. Reaching Level 3 is the meaningful threshold — that's where the platform starts delivering self-service, which is where the compound returns really kick in. Your labs will bring NorthStar from Level 1 (Lab 1) to approximately Level 2 with Level 3 characteristics (Lab 7)." This framework is useful for the team project: where is the company they're designing for on this maturity model, and where does the system they're building push them?

---

## Slide 4 — Three Reference Architectures for Enterprise AI
**Layout:** Three-column comparison with architecture type, strengths, and when to use

**Content:**
**Architecture 1 — Hub and Spoke**
- Central AI platform team owns infrastructure; business units plug in
- Strengths: governance, cost efficiency, expertise concentration
- Weakness: bottleneck, slower time-to-production for teams
- When to use: regulated industries, early platform maturity, high governance requirements

**Architecture 2 — Federated**
- Each business unit owns its own ML environment; central team sets standards
- Strengths: speed, autonomy, domain-optimized tooling
- Weakness: governance inconsistency, cost duplication, siloing
- When to use: large enterprises with distinct business lines, mature ML teams in each unit

**Architecture 3 — Full-Stack Self-Service**
- A single platform with embedded guardrails; any team ships AI without platform team approval
- Strengths: maximum speed, self-service, compound returns
- Weakness: requires significant upfront investment and cultural maturity
- When to use: technology-first companies with centralized AI governance culture

**Figure:** *Three architecture comparison diagram.* Three side-by-side panels, each showing a simplified architecture diagram for one model. Hub-and-Spoke: central hexagon connected to 5 outer nodes. Federated: 4 separate clusters with thin connections between them. Full-Stack: single layered diagram with self-service portals at top. Color-coded: Hub-and-Spoke in navy, Federated in teal, Full-Stack in gold. Below each diagram: a 3-word descriptor, a "Best for:" label, and a "Risk:" label.

**Notes:** "NorthStar is using a Hub-and-Spoke architecture because it's a single retailer with a central data team and three AI systems. That's the right call at this scale and maturity level." For the team project, students should consider which architecture makes sense for their chosen company: "A bank with strict governance requirements uses Hub-and-Spoke. A media conglomerate with 5 separate business units might use Federated. A startup trying to move fast uses Full-Stack." The architecture choice has implications for every layer above it.

---

## Slide 5 — Core Platform Component 1: Data Foundation
**Layout:** Component diagram with descriptions

**Content:**
**Every production AI platform needs a data foundation with four layers:**

1. **Raw Data Zone (S3 `raw/`)** — Immutable landing zone. Data arrives here from source systems. Never transformed in place. Lifecycle policy: delete after 90 days unless promoted.

2. **Processed Data Zone (S3 `processed/`)** — Cleaned, standardized, validated. Output of Glue ETL jobs. Schema-enforced. Data contracts govern what can be written here.

3. **Feature Zone (S3 `features/` + Feature Store)** — Engineered features, versioned, with online and offline access paths. This is what models consume at both training time and inference time.

4. **Artifacts Zone (S3 `artifacts/`)** — Trained model artifacts, evaluation reports, experiment logs. Versioned. The Model Registry points here.

**Key principle:** Every transformation is an auditable pipeline step. No manual intervention on production data.

**Figure:** *Four-zone data architecture diagram.* Four S3 bucket icons arranged vertically (raw → processed → features → artifacts), connected by downward arrows. Between each pair of buckets: the transformation step that connects them (Glue ETL: raw→processed; Feature Engineering Pipeline: processed→features; Training Pipeline: features→artifacts). Color coding: raw=gray, processed=blue, features=teal, artifacts=gold. Lifecycle policy icons beside each bucket. The diagram is the exact structure students build in Lab 1 (S3) and Lab 2 (pipelines).

**Notes:** "This four-zone structure is the data backbone for NorthStar. You'll provision the S3 buckets in Lab 1 and fill them with working pipelines in Lab 2. Every bucket has a purpose, and the purpose is defined by the governance rules: what can be written to it, by whom, and what happens to it over time." Emphasize the lifecycle rule on `raw/`: "Delete after 90 days — because raw data is expensive to store and once it's been processed, you don't need the original. You need the audit trail of how it was processed."

---

## Slide 6 — Core Platform Component 2: Compute Infrastructure
**Layout:** Three compute tiers with NorthStar usage examples

**Content:**
**Training Compute:**
- SageMaker Training Jobs — managed, spot-instance-capable, distributed training support
- Instance selection: `ml.m5.xlarge` (standard), `ml.p3.2xlarge` (GPU for large models)
- Cost tip: Spot instances save 60-80% for non-time-sensitive training runs
- NorthStar churn model: `ml.m5.xlarge` on 18 months of transaction data (~2 hours training time)

**Inference Compute:**
- SageMaker Real-Time Endpoints — for the Customer Service Agent (requires <200ms latency)
- SageMaker Batch Transform — for the Churn Model (runs nightly on all 250K customers)
- Bedrock Managed Endpoints — for Offer Generation (LLM calls, pay-per-token pricing)

**Experimental/Interactive Compute:**
- SageMaker Studio — managed Jupyter environment for development
- SageMaker Processing Jobs — data validation, feature engineering, evaluation

**Figure:** *Compute topology diagram.* Three horizontal rows: "Training" (SageMaker Training Job boxes, spot instance icon, cost tag), "Inference" (endpoint boxes: Real-Time, Batch Transform, Bedrock), "Development" (Studio icon, Processing Job icon). Arrows show flow from development → training → inference. NorthStar use case labels beside relevant compute components. Instance type labels where relevant. Color: training in blue, inference in teal, development in gray.

**Notes:** "Compute decisions are cost decisions. Every instance type choice has a monthly cost implication. In Lab 1, your deliverable includes a monthly cost estimate — you need to justify why you chose the instance types you chose. A `ml.p3.2xlarge` for a simple XGBoost model is not justified; a `ml.m5.xlarge` with spot pricing is." This connects to L23 (AI Economics) later in the semester — students are building cost intuition from day one.

---

## Slide 7 — Core Platform Component 3: Model Registry
**Layout:** Registry workflow diagram with metadata fields

**Content:**
**What is a Model Registry?**
- A versioned, governed catalog of all trained model artifacts in the organization
- Every model that might be deployed lives in the registry
- Enables: traceability (which data trained this model?), governance (who approved this deployment?), and rollback (if the new model breaks, revert to the last registered version)

**SageMaker Model Registry — key concepts:**
- **Model Package:** A versioned artifact (model + metadata + evaluation report)
- **Model Group:** A collection of packages for a given use case (e.g., "churn-prediction")
- **Status:** Pending Review → Approved → Deployed → Deprecated
- **Metadata:** Training data version, feature set used, evaluation metrics, approval chain

**The rule:** Nothing gets deployed that isn't in the registry. No exceptions.

**Figure:** *Model Registry workflow.* A vertical flow: (1) Training Job completes → (2) Model Package created in Registry (status: Pending) → (3) Evaluation metrics auto-attached → (4) Human approval step (status: Approved) → (5) CI/CD pipeline triggers deployment → (6) Status: Deployed. Beside each step: the required artifact or action. A "Rejected" path shows a model being returned to the Development stage. Clean, readable. Connects directly to Lab 4 (CI/CD) content.

**Notes:** "The Model Registry is the governance backbone of your MLOps practice. Without it, you have no answer to the question: which version of the model is currently in production? Which data was it trained on? Who approved it?" Common failure mode: teams trained models in notebooks, deployed them ad hoc, and had no idea what was running in production when something went wrong. "With a registry, 'what is in production?' is a one-click answer, not a forensics exercise."

---

## Slide 8 — Core Platform Component 4: Feature Store
**Layout:** Online vs. offline path comparison diagram

**Content:**
**The Feature Store Problem:**
Training/serving skew — the features used to train the model are computed differently from the features served at inference time → the model sees something in production it was never trained on.

**The Solution: A Feature Store**
- Single source of truth for engineered features
- **Offline store:** Batch access for model training (read full feature history from S3/Redshift)
- **Online store:** Low-latency access for real-time inference (read latest feature values from DynamoDB)
- Both stores are written by the same feature computation pipeline → skew is architecturally eliminated

**SageMaker Feature Store key concepts:**
- Feature Group: a collection of related features (e.g., "customer-churn-features")
- Event time: features are versioned by time → can reconstruct the exact feature state at any past moment
- Ingestion API: ingest in batch (Glue) or streaming (Kinesis)

**Figure:** *Training/Serving Architecture with Feature Store.* Two paths shown from the same Feature Store: (1) Training path → batch read from offline store → training job → model artifact; (2) Inference path → online read from online store → endpoint → prediction. Both paths connect to the SAME feature computation pipeline feeding the SAME Feature Store. A "Training/Serving Skew" warning icon sits between the two paths, marked with a red X and labeled "This is what we're eliminating." Clear, explanatory, technically accurate.

**Notes:** "Training/serving skew is responsible for more silent model degradation in production than almost any other cause. You train the model with feature X computed one way; at inference time, feature X is computed slightly differently. The model has never seen this input distribution. It quietly performs worse." The Feature Store is the architectural solution. In Lab 2, students build a SageMaker Feature Store with at least three engineered features. The Store is used in Lab 3 (model training) and Lab 5 (deployment). This architectural decision in Lab 2 echoes through the rest of the semester.

---

## Slide 9 — Core Platform Component 5: Experiment Tracking
**Layout:** MLflow dashboard mockup with key tracked dimensions

**Content:**
**Why experiment tracking matters:**
- Stage 5 (Develop) involves many experiments: different hyperparameters, different feature sets, different model architectures
- Without tracking, you cannot: reproduce a result, compare runs systematically, or prove to a gate reviewer that you found the best approach
- "We tried a bunch of things, and this one worked" is not an engineering argument

**What to track (every experiment):**
1. **Parameters:** All hyperparameters and configuration values
2. **Metrics:** All performance metrics (AUC, precision, recall, F1, latency)
3. **Data version:** Hash or pointer to the exact dataset used
4. **Model artifact:** The trained model saved to S3
5. **Environment:** Python version, library versions, compute specs

**MLflow on SageMaker:** SageMaker natively integrates MLflow as the experiment tracking backend. All SageMaker Training Jobs can auto-log to MLflow.

**Figure:** *MLflow experiment tracking UI mockup.* A clean table showing 6 experiment runs for "churn-prediction-v2." Columns: Run ID, Date, AUC, Precision@0.4, F1, n_estimators, max_depth, Data Version, Status. Rows are sorted by AUC descending. Best run highlighted in gold. Click-through to artifact shows: model.pkl, evaluation_report.json, feature_importance.png. This is exactly what students will produce in Lab 3.

**Notes:** "Every experiment that isn't tracked doesn't exist. If you can't reproduce it, you can't defend it, you can't audit it, and you can't learn from it." The practical consequence: when you're at Stage 6 (Evaluate) and the gate reviewer asks, "Show me the three experiments that led to this model selection," you should be able to pull them up in 30 seconds from MLflow. If you can't, the gate doesn't open. "Experiment logging is not busywork — it is the evidence that your engineering decisions were sound."

---

## Slide 10 — Core Platform Component 6: CI/CD Pipeline
**Layout:** Pipeline stages with test categories and AWS services

**Content:**
**CI/CD for AI systems includes everything software CI/CD includes — and more:**

**Standard CI/CD:**
- Code tests (unit, integration, end-to-end)
- Code quality checks (linting, type checking, security scanning)
- Build + artifact creation
- Environment promotion (dev → staging → production)

**AI-specific additions:**
- **Data validation:** Does the input data match the expected schema and distribution?
- **Model quality gate:** Does the new model meet the evaluation criteria?
- **Training pipeline test:** Can the pipeline run end-to-end on a sample dataset?
- **Inference contract test:** Does the model's prediction API match the expected interface?
- **Bias/fairness check:** Does the model pass fairness evaluation across protected attributes?

**AWS services:** CodePipeline (orchestration), CodeBuild (test execution), SageMaker Pipelines (training pipeline), Model Registry (model promotion gate)

**Figure:** *CI/CD pipeline diagram.* Horizontal pipeline with 6 stages represented as connected boxes: (1) Code Commit → (2) Data Validation → (3) Training Pipeline → (4) Model Evaluation Gate → (5) Staging Deployment → (6) Production Promotion. Colored indicators at each stage (green = pass, red = fail, amber = gate decision). Below the pipeline: AWS service icons mapped to each stage. The gate at stage 4 shows: "AUC ≥ 0.72? → Yes: promote. No: alert." This maps directly to Lab 4.

**Notes:** "The AI-specific additions are where most teams drop the ball. They build a CI/CD pipeline that tests their code — good! — but forget to test their data and their model. A new data ingestion job introduces a schema change that the model's preprocessing code doesn't handle. The pipeline tests pass (no code changed). The model inference silently breaks on new data." This is a real failure mode. In Lab 4, students build this pipeline with the model quality gate as a required component.

---

## Slide 11 — The Build vs. Buy Decision Framework
**Layout:** Decision matrix with four quadrant analysis

**Content:**
**The Decision Variables:**
- **Differentiation potential:** Is this component a source of competitive advantage, or table stakes?
- **Build cost:** Engineering time, maintenance overhead, opportunity cost
- **Buy cost:** Licensing, integration, vendor lock-in, ongoing fees
- **Strategic control:** How much does this matter to own long-term?

**The Four Zones:**
| Quadrant | Differentiation | Complexity | Decision |
|----------|----------------|-----------|----------|
| Buy/Subscribe | Low | High | AWS Bedrock, SageMaker managed services |
| Configure | Low | Low | IAM, CloudWatch (configure, don't build) |
| Build (carefully) | High | Low | Custom feature engineering, proprietary models |
| Build (investment) | High | High | Proprietary training infrastructure (rare, for giants only) |

**NorthStar default rule:** Buy infrastructure, build models, configure governance.

**Figure:** *2×2 decision matrix.* X-axis: "Differentiation Potential" (low→high). Y-axis: "Complexity" (low→high). Four-quadrant labels: Buy/Subscribe (top-left), Configure (bottom-left), Build Carefully (bottom-right), Build as an Investment (top-right). NorthStar component examples placed in each quadrant (S3/SageMaker in Buy, IAM in Configure, XGBoost model in Build Carefully). A diagonal arrow from top-left to bottom-right labeled "In-house build increases as strategic value increases." Clean 2×2 format.

**Notes:** "Every architectural decision in your labs should be justifiable against this framework. Why are we using SageMaker instead of building our own training infrastructure? Because training infrastructure is not a source of competitive advantage for NorthStar — SageMaker is a mature, cheap, reliable solution. What's the equivalent decision for your team project? That's the ADR question you need to answer." The ADR structure from L02 applies directly here.

---

## Slide 12 — NorthStar Platform Architecture: Full View
**Layout:** Complete AWS architecture diagram for the NorthStar platform

**Content:**
**NorthStar Retail AI Platform on AWS — components and connections:**
- **Foundation (Lab 1):** VPC, IAM, S3 structure, SageMaker domain (Terraform)
- **Data Layer (Lab 2):** Glue ETL → S3 processed zone → SageMaker Feature Store
- **Model Layer (Lab 3):** XGBoost training (SageMaker) + RAG pipeline (Bedrock) + Agent (Bedrock)
- **CI/CD Layer (Lab 4):** CodePipeline → Model Registry → approval gates
- **Deployment Layer (Lab 5):** SageMaker endpoints (real-time + batch) + canary strategy
- **Operations Layer (Lab 6):** CloudWatch dashboards + SageMaker Model Monitor + runbooks
- **Business Layer (Lab 7):** Metric Pyramid + FinOps reports + shared scorecard

**This is the complete platform. By Lab 7, you will have built it all.**

**Figure:** *Full NorthStar AWS architecture diagram.* Comprehensive, multi-tier AWS diagram showing all components from Lab 1 through Lab 7. Organized into horizontal layers (Foundation → Data → Models → CI/CD → Operations → Business Value). AWS service icons throughout. Color-coded by lab number (each lab adds a different color layer). Arrows show data flows and dependencies. This diagram should feel slightly overwhelming — but also exciting. It is what the semester builds toward.

**Notes:** "This is the system. Not a simplified version — the actual system you're going to build over 7 labs. It looks complex. It is complex. And by December, you will have built every layer of it." Print this diagram for students or post it on Canvas. It's a useful reference all semester. "Every time you wonder 'why does this lecture matter?' find the component this lecture maps to on this diagram. Every week connects to a specific layer."

---

## Slide 13 — Infrastructure as Code: Why Everything Is Terraform
**Layout:** Code comparison (console approach vs. IaC approach)

**Content:**
**The Console Approach (don't do this in production):**
- Click through the AWS console to create resources
- No version control, no repeatability, no team collaboration
- "Works on my account" — cannot reproduce in a new region or for a teammate
- Disaster recovery: rebuild from memory. Good luck.

**The IaC Approach (Terraform):**
- All resources defined in declarative `.tf` files
- Version-controlled in Git — every change is tracked, reviewable, revertable
- Fully reproducible: `terraform apply` creates the identical environment anywhere
- Team collaboration: infrastructure changes go through pull requests
- Disaster recovery: `terraform apply` from the last known-good commit

**Why Terraform specifically (vs. AWS CloudFormation)?**
- Multi-cloud capable (valuable if your team project isn't AWS-only)
- Larger ecosystem, more readable syntax, better state management tooling
- Industry standard at most large enterprises

**Figure:** *Side-by-side comparison.* Left panel: Console screenshot (clicking AWS UI buttons, manual steps numbered 1-8). Right panel: Terraform code snippet for the same resource (SageMaker domain), showing provider, resource type, and configuration in clean HCL syntax. Below both panels: two metrics: "Time to reproduce in new account" (Console: "Unknown / Days"; Terraform: "12 minutes") and "Recoverable from disaster?" (Console: "Maybe"; Terraform: "Yes, always"). The contrast is stark and immediate.

**Notes:** "Everything you provision for NorthStar will be in Terraform. That is non-negotiable. The grading TA will clone your repo and run `terraform apply` to verify your work. If it doesn't apply cleanly, you lose 20 points automatically." Introduce Terraform briefly for students who haven't used it. The HCL syntax is readable — you don't need prior Terraform experience. The Canvas Lab 1 starter kit includes the module directory structure; students fill in the resource definitions.

---

## Slide 14 — Platform Cost Governance
**Layout:** Cost breakdown + governance controls

**Content:**
**The Cost Problem with AI Platforms:**
- AI infrastructure costs can escalate unexpectedly: training jobs left running, endpoints not deprovisioned, large models with high token costs
- Without governance controls, teams discover their AWS bill at month-end — after the damage is done

**Cost Governance Controls (required in Lab 1):**
1. **AWS Budgets:** Set monthly spend threshold alerts at $50 and $100 (email + stop training jobs)
2. **SageMaker cost allocation tags:** Tag every resource with: Project, Environment, Team, CostCenter
3. **Lifecycle policies:** S3 `raw/` data deleted after 90 days; training snapshots deleted after 30 days
4. **Spot instance policy:** Use spot for all non-production training jobs (60-80% cost reduction)
5. **Endpoint auto-scaling:** Scale down to zero during off-hours for development endpoints

**Monthly Cost Estimate for NorthStar Platform Skeleton (Lab 1 deliverable):**
- Target: ~$25-40/month for the infrastructure skeleton (no training jobs running)

**Figure:** *AWS Cost Explorer mockup.* Shows a realistic cost breakdown chart for a NorthStar-like environment. Bar chart by service: SageMaker (largest), S3 (medium), Glue (small), CloudWatch (small), Other (small). Monthly total: ~$32. Below: a budget alert timeline showing: $0 → Month 1 $32 → Month 2 $38 → Budget alert triggered at $50 → Month 3 costs controlled at $41. Green and amber color coding. Shows cost governance working as intended.

**Notes:** "Your Lab 1 deliverable includes a monthly cost estimate. This is not a formality — it's an engineering exercise. What are the cost implications of the platform decisions you made? If your ADR says 'we'll use ml.p3.2xlarge instances for all training jobs,' your cost estimate should reflect that and justify it." This habit — building cost awareness into architectural decisions — is one of the most valuable skills the course develops. Most junior engineers have no intuition for cloud costs; this course fixes that.

---

## Slide 15 — Common Platform Architecture Mistakes
**Layout:** Five anti-patterns with brief description and remediation

**Content:**
1. **The Notebook Trap:** Shipping notebook code to production without an engineering pipeline. Notebooks are for exploration; production code is structured, tested, and version-controlled.

2. **The God Role:** Creating one IAM role with `AdministratorAccess` for all AI workloads. Violates least privilege; creates a massive blast radius in the event of compromise.

3. **Manual Model Promotion:** Promoting models to production by copying files between environments. No audit trail, no rollback, no governance. Use the Model Registry.

4. **No Data Versioning:** Training a model, then losing track of which data version it was trained on. When the model behaves unexpectedly, you can't investigate.

5. **The Cost Blindspot:** Building an AI platform without AWS Budgets or cost allocation tags. Discovering a $3,000 bill because a training job ran for 72 hours without anyone noticing.

**Figure:** *Five warning-sign visual.* Five rows, each with a red warning triangle icon on the left, an anti-pattern name in bold, a 1-sentence description, and a small "Fix:" label containing the remediation. Alternating row shading in very light pink/white. The visual design clearly communicates "these are mistakes" without clutter.

**Notes:** "Every one of these anti-patterns represents something I have personally seen cause a production incident. Not in student projects — in companies. The Notebook Trap alone is responsible for more undeployable AI work than almost any other single cause." Use these to preview what students need to avoid in their labs. "Your Lab 1 grader will check for the God Role anti-pattern specifically — one IAM role with AdministratorAccess is an automatic deduction."

---

## Slide 16 — Key Takeaways + What's Next
**Layout:** Five numbered takeaways + next session preview

**Content:**
**Key Takeaways:**
1. An AI platform is a shared, governed infrastructure for building, deploying, and operating AI systems — not a collection of isolated tools
2. Platform investment pays compound returns starting at your third AI system; NorthStar's three systems make it the right call
3. Every production AI platform has six core components: data foundation, compute, model registry, feature store, experiment tracking, and CI/CD
4. Infrastructure as Code (Terraform) is non-negotiable — if it's not in `terraform apply`, it doesn't exist
5. Cost governance is an architectural decision, not an afterthought — every resource gets a budget alert and cost allocation tag

**Next Session (Tue Sep 15):**
- Topic: AI Platform & Cloud Architecture II — AWS infrastructure deep dive, SageMaker ecosystem, NorthStar platform walkthrough
- Reading due: *AI Platform & Cloud Architecture* — "AWS Infrastructure" through "Key Takeaways"
- Lab 1 due in 9 days — your `terraform apply` should be working by now

**Figure:** *Five-point takeaway summary.* Same format as L01/L02 takeaways: numbered circles in navy on the left, takeaway text in large, readable type on the right. "Next Up" banner in teal below. Lab 1 deadline counter prominently displayed (e.g., "⏱ Lab 1 due in 9 days").

**Notes:** End with a practical check-in: "Where are you on Lab 1? Show of hands — who has their AWS Educate account set up?" If hands are low, emphasize urgency: "The account setup is the long pole in the tent. If you don't have it set up today, you're already in trouble. Office hours tomorrow — come." The practical urgency of Lab 1 should motivate students to act immediately.
