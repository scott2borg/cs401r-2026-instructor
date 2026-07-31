---
lecture: L04
title: AI Platform & Cloud Architecture II
date: Tuesday, September 15, 2026
week: 3
arc: Build
reading_due: "AI Platform & Cloud Architecture — AWS Infrastructure through Key Takeaways"
lab_due: "Lab 1 due Sat Sep 19 · Lab 2 assigned Thu Sep 17"
slides_target: 16
---

# L04: AI Platform & Cloud Architecture II
**Tuesday, September 15, 2026 | CS 401R: Engineering Production AI Systems | Fall 2026**

> Deep dive on AWS infrastructure for AI: SageMaker ecosystem, VPC design, IAM scoping, cost governance, and the NorthStar platform walkthrough. Students leave with the knowledge to complete Lab 1 and understand why each architectural decision matters.

**Reading Due:** *AI Platform & Cloud Architecture* — "AWS Infrastructure" through "Key Takeaways"  
**Lab 1 Due:** Saturday, September 19 (4 days!)

---

## Slide 1 — Title
**Layout:** Left panel + NorthStar platform architecture diagram (full)

**Content:**
- AI Platform & Cloud Architecture II
- CS 401R · Lecture 04 · Tuesday, September 15, 2026
- AWS Deep Dive: SageMaker · VPC · IAM · Terraform · Cost Governance

**Figure:** *Complete NorthStar AWS architecture diagram, full color.* Professional-quality AWS architecture diagram identical to the "Lab 1 through Lab 7" vision diagram from L03. This time presented as the "what we're building together" visual — all seven lab layers visible, with Lab 1 components highlighted/circled in gold. The rest of the platform in lighter opacity, indicating "coming soon."

**Notes:** Open with a practical orientation: "Lab 1 is due Saturday. This lecture fills in everything you need to know to finish it correctly." Check in: "Who still doesn't have their AWS Educate account set up?" Address those students directly — offer office hours today if needed. Then proceed with urgency but without panic.

---

## Slide 2 — SageMaker Domain: The Hub of the NorthStar Platform
**Layout:** SageMaker Domain component diagram with user profiles and apps

**Content:**
**What is a SageMaker Domain?**
- The top-level resource that contains all SageMaker resources for a team or project
- Provides: shared network configuration, user profiles, execution roles, storage
- Single Domain for NorthStar (one per environment: dev and prod)

**Key Domain Components:**
- **Execution Role:** The IAM role that SageMaker Studio runs as — needs access to S3, ECR, CloudWatch
- **VPC Configuration:** Studio runs inside your private VPC (no public internet access)
- **User Profiles:** Named user profiles with individual execution roles (MLEngineer, DataEngineer)
- **Default S3 Location:** Where Studio saves notebooks, data, and model artifacts by default

**Terraform resource:** `aws_sagemaker_domain` with `auth_mode = "IAM"` (not SSO for this course)

**Figure:** *SageMaker Domain component diagram.* Central box labeled "SageMaker Domain" with sub-components shown as nested boxes: VPC (contains Private Subnet), EFS (shared storage), User Profiles (two: MLEngineer, DataEngineer), and Default S3. Arrows indicate that Studio App reads from EFS and Training Jobs write to S3 artifacts. IAM role shields beside each user profile. Terraform `resource` block shown in small text below the diagram. Clean AWS service icon style.

**Notes:** "The Domain is the first resource you create with Terraform. Everything else lives inside it or references it. If the Domain configuration is wrong — wrong VPC, wrong execution role — all subsequent resources will fail or be insecure." Common Lab 1 mistake: creating the Domain without the VPC configuration, which means Studio runs with public internet access. The private VPC configuration is required and is part of the grading rubric.

---

## Slide 3 — VPC Design for AI Workloads
**Layout:** VPC diagram with subnet tiers and traffic flows

**Content:**
**Why AI workloads need a private VPC:**
- SageMaker training jobs process sensitive customer data (NorthStar's 250K customer records)
- Data must not transit the public internet
- VPC endpoints keep traffic entirely within the AWS network
- Security compliance requirement for any system processing PII

**NorthStar VPC Design:**
```
VPC: 10.0.0.0/16
├── Private Subnets (×2, different AZs)
│   ├── SageMaker training instances
│   ├── SageMaker processing jobs
│   └── Glue ETL jobs
├── No Public Subnets (no internet gateway)
└── VPC Endpoints (PrivateLink):
    ├── S3 (Gateway endpoint)
    ├── SageMaker API
    ├── SageMaker Runtime
    ├── ECR
    └── CloudWatch Logs
```

**Figure:** *VPC architecture diagram.* Standard AWS VPC diagram showing the VPC boundary (blue rectangle), two private subnets inside (gray boxes with availability zone labels), VPC endpoints (green circles on the VPC boundary), and traffic flow arrows. No public subnet, no internet gateway. Customer data flow: S3 → VPC Endpoint → Private Subnet → SageMaker Training Job → back through VPC Endpoint → S3. The "No public internet" path is shown with a red X.

**Notes:** "The two-AZ private subnet design is the minimum for production. If one availability zone has an outage — which happens — your training jobs can continue in the second AZ." The VPC endpoint configuration is the most commonly missed element in Lab 1. "Without VPC endpoints for S3 and SageMaker, your training jobs will try to access those services over the public internet, which violates your security configuration. The jobs will fail."

---

## Slide 4 — IAM Design: Least Privilege for AI Workloads
**Layout:** Three-role structure with specific permission scopes

**Content:**
**The Principle of Least Privilege:** Every role has exactly the permissions it needs — no more.

**NorthStar IAM Roles (Lab 1 requirement: 3 roles):**

**Role 1: NorthStarMLEngineer**
- SageMaker: full access to training jobs, endpoints, Feature Store
- S3: read/write on `features/` and `artifacts/` buckets only
- Glue: read access (consume processed data; cannot modify pipelines)
- Bedrock: InvokeModel access (for RAG and agent inference)

**Role 2: NorthStarDataEngineer**
- Glue: full access (create/run ETL jobs)
- S3: read `raw/`, read/write `processed/` and `features/`
- SageMaker Feature Store: write access (ingest features)
- SageMaker: no training or endpoint access

**Role 3: NorthStarGovernance**
- S3: read-only across all buckets (for audit and lineage)
- SageMaker Model Registry: approve/reject model packages
- CloudWatch: read-only (review operational metrics)
- No compute access

**Figure:** *Permission matrix table.* Rows: three IAM roles. Columns: key AWS services (SageMaker, S3-raw, S3-processed, S3-features, S3-artifacts, Glue, Bedrock, Model Registry, CloudWatch). Cell values: Full Access (dark green), Read Only (light green), Write Only (blue), No Access (gray). The matrix makes permission boundaries immediately visible. Common mistake (God Role) shown in a fourth row at bottom in red: "AdministratorAccess — all cells dark green — NEVER do this."

**Notes:** "The Governance role often surprises students — why does it have read-only access to everything but no compute access? Because the governance function in a real organization is oversight, not operation. The person approving a model deployment should be able to review everything but not be able to train models or spin up endpoints." The role separation is also a security pattern: if the MLEngineer role is compromised, the attacker cannot modify pipelines (DataEngineer) or approve model deployments (Governance).

---

## Slide 5 — S3 Bucket Architecture: Design Decisions
**Layout:** S3 bucket diagram with data governance rules at each layer

**Content:**
**NorthStar S3 Bucket Architecture:**

| Bucket/Prefix | Purpose | Who Writes | Who Reads | Lifecycle |
|---------------|---------|-----------|----------|-----------|
| `northstar-raw/` | Source data landing zone | DataEngineer, automated ingestion | DataEngineer only | Delete after 90 days |
| `northstar-processed/` | Cleaned, schema-validated data | DataEngineer (Glue jobs) | DataEngineer, MLEngineer | Delete after 180 days |
| `northstar-features/` | Engineered feature datasets | Feature pipelines | MLEngineer, Feature Store | Retain indefinitely |
| `northstar-artifacts/` | Trained models, reports | SageMaker Training Jobs | MLEngineer, Model Registry | Versioned; retain indefinitely |

**Bucket-level settings (all buckets):**
- Block all public access: enabled
- Server-side encryption (SSE-S3): enabled
- Versioning: enabled on `artifacts/` bucket

**Figure:** *S3 architecture with data lineage arrows.* Four S3 bucket icons in a vertical flow, connected by transformation pipeline boxes between them: "Ingestion Scripts" between raw and processed; "Glue ETL + Feature Engineering" between processed and features; "Training Pipeline" between features and artifacts. Lifecycle policy icons with time labels beside each bucket. Permission lock icons showing who can write. Color coding matches the data zone colors from L03.

**Notes:** "The lifecycle rules are not optional — they're cost governance. Raw data without a lifecycle rule will accumulate indefinitely in your account. 250,000 customer records × 18 months of transactions stored in parquet is manageable. The same data in raw CSV format multiplied by 12 months of daily snapshots becomes a significant storage bill." Common mistake: enabling versioning on the raw bucket (unnecessary; versioning on the processed bucket; only artifacts need full versioning).

---

## Slide 6 — SageMaker Ecosystem: What You'll Actually Use
**Layout:** Ecosystem map with course-relevant services highlighted

**Content:**
**SageMaker services used in CS 401R:**

**Studio (Development):** Managed JupyterLab environment for notebook-based development. Runs in your VPC. Connected to your EFS volume for persistent storage.

**Training Jobs:** Managed training infrastructure. You provide: docker image (built-in or custom), training script, input data path (S3), output path (S3), instance type. SageMaker handles: instance provisioning, job monitoring, artifact upload.

**Processing Jobs:** Same managed infrastructure as Training Jobs, but for non-training workloads: data preprocessing, evaluation, batch feature computation.

**Pipelines:** Workflow orchestration for multi-step AI workflows (preprocess → train → evaluate → register). Used in Lab 4.

**Model Registry:** Versioned model catalog. Used in Labs 4 and 5.

**Feature Store:** Online + offline feature serving. Used in Labs 2 and 3.

**Endpoints (Real-Time):** Persistent inference endpoints for synchronous predictions. Used in Lab 5 for the Customer Service Agent.

**Batch Transform:** One-time batch inference jobs. Used for nightly churn scoring of all 250K customers.

**Figure:** *SageMaker ecosystem map.* SageMaker logo in center. Radiating outward: service circles (Studio, Training Jobs, Processing Jobs, Pipelines, Model Registry, Feature Store, Real-Time Endpoints, Batch Transform). Lines connecting services show data flows (e.g., Training Job reads from Feature Store, writes artifact to Model Registry). Course lab labels overlaid on relevant services (Lab 2 on Feature Store, Lab 3 on Training Jobs, Lab 4 on Pipelines + Registry, Lab 5 on Endpoints). Highlight circle around the 5-6 most-used services in the first three labs.

**Notes:** "SageMaker is a service ecosystem, not a single tool. You don't 'use SageMaker' — you use specific SageMaker services for specific tasks." Students sometimes try to use SageMaker Studio for everything, including tasks better suited to Processing Jobs or Batch Transform. The rule: Studio is for development; Training Jobs and Processing Jobs are for production workloads.

---

## Slide 7 — NorthStar Platform Walkthrough: Lab 1 Components
**Layout:** Terraform code walkthrough with architecture diagram beside it

**Content:**
**What Lab 1 provisions (in Terraform):**
```hcl
# Module 1: VPC
module "vpc" {
  source              = "./modules/vpc"
  cidr_block          = "10.0.0.0/16"
  private_subnet_cidrs = ["10.0.1.0/24", "10.0.2.0/24"]
  availability_zones   = ["us-east-1a", "us-east-1b"]
}

# Module 2: S3 Storage
module "storage" {
  source          = "./modules/storage"
  environment     = "dev"
  lifecycle_rules = { raw = 90, processed = 180 }
}

# Module 3: IAM
module "iam" {
  source       = "./modules/iam"
  s3_bucket_arns = module.storage.bucket_arns
}

# Module 4: SageMaker
module "sagemaker" {
  source              = "./modules/sagemaker"
  vpc_id              = module.vpc.vpc_id
  subnet_ids          = module.vpc.private_subnet_ids
  execution_role_arn  = module.iam.ml_engineer_role_arn
}
```

**Figure:** *Split-screen layout.* Left: clean Terraform HCL code with syntax highlighting (similar to above). Right: the NorthStar architecture diagram with each module mapped to the component it creates. Arrows connect code blocks to diagram elements. The split-screen connects the abstract (code) to the concrete (infrastructure). Color-coded by module (VPC=blue, Storage=teal, IAM=amber, SageMaker=navy).

**Notes:** "This is not pseudocode — this is the structure of what you should be building right now. The module structure is provided in the starter kit; the resource definitions inside each module are yours to write." Walk through the module dependency order: VPC must exist before SageMaker; Storage and IAM can be provisioned in parallel; SageMaker depends on VPC and IAM. "Run `terraform plan` before `terraform apply`. If the plan looks wrong, stop — don't apply."

---

## Slide 8 — Architecture Decision Record: How to Write One
**Layout:** ADR template with a completed example

**Content:**
**ADR Structure (Lab 1 requires 3 ADRs, 600-900 words total):**

**Decision 1 example: VPC Topology**

```markdown
## ADR 001: VPC Configuration for NorthStar AI Platform

### Context
NorthStar's AI platform processes customer PII (250K records, transaction 
history). Regulatory and organizational security policy requires all data 
processing to remain within a private network. SageMaker training jobs 
and Glue ETL jobs must not have internet access.

### Options Considered
**Option A: Public VPC with security groups**
- Simpler to configure; internet access enables easier package installation
- Risk: customer data could transit public internet; fails security audit

**Option B: Private VPC with VPC Endpoints**  
- More complex; requires VPC endpoint configuration for S3, SageMaker, ECR
- Data never leaves AWS network; satisfies security and compliance requirements

### Decision
Option B: Private VPC with VPC Endpoints.

### Consequences
Training instances cannot access public package repositories. Solution: 
build custom Docker images with required packages baked in (addresses 
this in the training job module). Security posture is significantly 
stronger — this design will pass a standard cloud security audit.
```

**Figure:** *ADR document visual.* The example ADR rendered as a clean document with section headers in distinct colors. Context section: dark gray background. Options: two-column comparison with green/red indicators. Decision: gold highlight. Consequences: teal section. Footer shows: "Status: Accepted | Author: [Name] | Date: Sep 19, 2026." Professional formatting that looks like a real engineering document, not a homework assignment.

**Notes:** "Three decisions, six sections (Context, Options, Decision, Consequences × 3), 600-900 words total. That is the Lab 1 ADR requirement." Common ADR mistakes: (1) Documenting a decision after the fact without genuinely considering alternatives. (2) Writing "Option A vs. Option B" but only describing one of them seriously. (3) Failing to describe consequences — what does this decision enable or foreclose? "The best ADRs read like engineering detective work. Show your reasoning. Show what you considered and rejected. Show what this choice costs you."

---

## Slide 9 — Platform Cost Estimate: How to Build One
**Layout:** Cost calculation methodology with NorthStar example

**Content:**
**Lab 1 Deliverable: Monthly cost estimate for the platform skeleton**

**Step 1: List all running resources**
- SageMaker Domain: $0 (pay-per-use; no charge when idle)
- SageMaker Studio storage (EFS): 2 GB × $0.30/GB-month = $0.60
- S3 buckets: ~5 GB × $0.023/GB-month = $0.12 (initially)
- VPC: NAT Gateway not needed (VPC Endpoints replace it) = $0
- VPC Endpoints: 5 endpoints × $0.01/hour × 720 hours = $36/month
- CloudWatch Logs: ~2 GB × $0.50/GB = $1.00
- **Total for skeleton (no jobs running): ~$38-45/month**

**Step 2: Estimate job costs (occasional)**
- SageMaker Training Job (ml.m5.xlarge, 2 hours): $0.269/hr × 2 = $0.54 per run
- Glue job (1 DPU, 30 min): $0.44/DPU-hour × 0.5 = $0.22 per run

**Step 3: Build a monthly budget scenario**
- Assume: 2 training jobs + 10 Glue runs per week = $5-8/month in jobs
- **Total estimated monthly spend: $43-53/month**

**Figure:** *Cost breakdown table.* Clean table with three columns: Service, Estimated Monthly Cost, Notes. Rows for each service listed above. Bottom row: Total with a range ($38-53). Beside the table: a small pie chart showing cost distribution by service (VPC Endpoints are the biggest cost driver, surprising students). Below: "Budget alert recommendation: set alerts at $50 and $100."

**Notes:** "Your cost estimate doesn't have to be exact — it has to be defensible. Show your math. If you just write '$40/month' with no calculation, you lose points." The most common surprise: VPC Endpoints cost $36/month just in interface endpoint fees, even when nothing is running. This is a real cost trade-off: you could avoid this cost by using public endpoints, but then you fail the security requirement. The ADR for VPC design should acknowledge this cost consequence.

---

## Slide 10 — Modularity: Building for the Future Labs
**Layout:** Terraform module dependency diagram with lab-by-lab additions

**Content:**
**Design principle:** Every Lab 1 Terraform module should be extendable by later labs without modification.

**Modularity requirements for Lab 1:**

**VPC module:** Designed to accommodate Glue connections (Lab 2), SageMaker Pipelines (Lab 4), and Bedrock VPC endpoints (Labs 5+). Use variables for subnet counts and CIDR ranges.

**IAM module:** Role boundaries should accommodate: Feature Store ingest (Lab 2), Bedrock InvokeModel (Labs 5+), CodePipeline execution (Lab 4). Use data sources to reference existing policies.

**Storage module:** S3 bucket outputs should expose ARNs for IAM policy attachment (Labs 2+) and bucket names for SageMaker configuration (Labs 3+). Use consistent naming convention: `northstar-{env}-{zone}`.

**SageMaker module:** Domain configuration should allow multiple user profiles to be added (Lab 2 adds DataEngineer profile). Use `for_each` for user profile creation.

**Figure:** *Module dependency tree with future lab callouts.* A tree diagram showing Lab 1 modules at the root (VPC, IAM, Storage, SageMaker). From each module, dashed arrows point to future labs that depend on it. Lab 2 arrow from Storage (adds Glue resources). Lab 3 arrow from IAM (adds Bedrock permissions). Lab 4 arrow from SageMaker (adds Pipelines). The diagram makes the architectural dependency clear and motivates good modular design now. Color: Lab 1 modules in solid blue; future labs in dashed teal.

**Notes:** "This is the architectural investment argument for good design in Lab 1. If your Terraform modules are tightly coupled and not parameterized, you'll rewrite them in Lab 2. If they're properly modular, Labs 2-7 add cleanly on top." The naming convention matters: `northstar-{env}-{zone}` is consistent, predictable, and greppable. Every resource you create this semester should follow it.

---

## Slide 11 — Vendor Strategy: AWS Lock-In and the Mitigation
**Layout:** Lock-in risk assessment with abstraction strategies

**Content:**
**The Lock-In Question:** "Are we too dependent on AWS?"

**Lock-in dimensions for NorthStar:**
- **Deep lock-in (accepted):** SageMaker Feature Store (proprietary schema), Bedrock (AWS-only models), CodePipeline (AWS-specific)
- **Moderate lock-in (managed):** SageMaker Training Jobs (alternatives: Kubeflow, Vertex AI)
- **No lock-in (by design):** Terraform IaC (runs against any cloud), Python training code, MLflow experiment tracking, model artifacts in ONNX or SavedModel format

**The mitigation strategy for this course:**
- Containerize training code (Docker) → portable to any container-capable compute
- Store model artifacts in standard formats (ONNX, joblib, SavedModel) → not SageMaker-specific
- Use MLflow (not SageMaker Experiments) for tracking → vendor-neutral
- Accept Bedrock lock-in for now → if the team project is for a company with multi-cloud requirements, discuss the trade-off

**Figure:** *Lock-in spectrum diagram.* A horizontal spectrum from "Vendor-Neutral" (left) to "Deep Lock-In" (right). AWS services plotted along the spectrum: S3 (slight lock-in, alternatives exist), SageMaker Training (moderate, containerized), MLflow (neutral), SageMaker Feature Store (high), Bedrock (very high), CodePipeline (high). Each service is shown as a labeled dot. Below: "NorthStar mitigation strategies" arrows pointing from high-lock-in services to their mitigations (containerization, standard model formats, etc.).

**Notes:** "Lock-in is a business decision, not just a technical one. For NorthStar — a single retailer on AWS — deep SageMaker lock-in is acceptable. For your team project, if you're designing for a company with existing Azure infrastructure, you'd make very different choices." The key skill: knowing which components you're willing to lock into (managed services that save engineering time) vs. which you need to keep portable (model code, data formats, orchestration logic).

---

## Slide 12 — Security Checklist for Lab 1
**Layout:** Checklist format with pass/fail criteria

**Content:**
**Lab 1 Security Requirements (graded):**

| ✅ | Requirement | Anti-pattern it prevents |
|----|-------------|------------------------|
| ☐ | No resource has `AdministratorAccess` IAM policy | God Role anti-pattern |
| ☐ | All S3 buckets have "Block Public Access" enabled | Public data exposure |
| ☐ | All S3 buckets have SSE-S3 encryption enabled | Data at rest unencrypted |
| ☐ | SageMaker Domain in private VPC (no public internet) | Data in transit exposure |
| ☐ | VPC Endpoints for S3 and SageMaker API configured | Traffic routing via public internet |
| ☐ | No AWS credentials or access keys in the repository | Credential exposure in GitHub |
| ☐ | IAM roles follow least-privilege scoping | Excessive permissions |
| ☐ | `.env` and credentials files in `.gitignore` | Secret committed to Git |

**Auto-fail:** Committed credentials in the repo = 0 on Lab 1, no exceptions.

**Figure:** *Checklist visual.* The table rendered as a clean checklist with checkbox icons. "Auto-fail" item at the bottom in a red box with a warning icon. Two column layout for space efficiency. Each requirement has a brief description. Can be used as a pre-submission self-check.

**Notes:** "Run this checklist before you submit. The TA runs an automated check for committed credentials — GitHub secret scanning is enabled on the course org. If a credential is committed, the grade is 0, no appeal. This is not punitive — it's a lesson about production consequences. In the real world, a committed AWS key that gets scraped by a bot can cost a company thousands of dollars in minutes."

---

## Slide 13 — Lab 1 Grading Rubric Overview
**Layout:** Rubric table with point distribution

**Content:**
**Lab 1 Grading (100 points):**

| Task | Points | Key Success Criteria |
|------|--------|---------------------|
| Task 1: AWS Environment Setup | 20 | SageMaker Domain, S3 buckets, IAM roles, VPC — all provisioned via Terraform |
| Task 2: Terraform Quality | 20 | Modular structure, clean `terraform plan` output, parameterized variables |
| Task 3: Security Configuration | 20 | Passes security checklist; no God Role; private VPC; no credentials committed |
| Task 4: Architecture Decision Record | 25 | 3 decisions, Context + Options + Decision + Consequences for each, 600-900 words |
| Task 5: Cost Estimate | 15 | Itemized estimate with math shown; monthly total with rationale |
| **Total** | **100** | |

**Bonus (up to 5 points):** Multi-environment design (dev and prod environments in separate Terraform workspaces)

**Figure:** *Rubric visualization.* The table above with a visual weight bar beside each task showing proportional weight. ADR (25 pts) has the longest bar. A pie chart sidebar shows the distribution visually. Key success criteria for the top 3 tasks shown in bold. Clear, readable at a glance.

**Notes:** "The ADR is the highest-weighted component because it tests judgment, not just technical execution. You can have a working Terraform deployment and still fail the ADR if it's just a list of facts with no decision reasoning." The bonus: multi-environment setup (dev and prod workspaces) demonstrates the kind of production-thinking the course rewards. Not required, but worth attempting if the student has time.

---

## Slide 14 — What Good Platform Architecture Feels Like
**Layout:** Characteristics of well-architected AI platforms

**Content:**
**The Well-Architected AI Platform (AWS Well-Architected Framework, AI edition):**

1. **Operational Excellence:** Everything is IaC. Every change is tracked. Every deployment is reproducible.

2. **Security:** Least-privilege IAM. Private network. Encryption at rest and in transit. Audit trail for all model approvals.

3. **Reliability:** Multi-AZ deployment. Automated drift detection. Runbooks for all failure scenarios. Rollback capability for every model version.

4. **Performance Efficiency:** Right-sized compute for each workload. Spot instances for training. Auto-scaling for inference. Feature Store eliminates training/serving skew.

5. **Cost Optimization:** Budget alerts. Cost allocation tags on every resource. Lifecycle policies on data. Regular cost reviews.

6. **Sustainability:** Spot instances reduce energy waste. Auto-scaling shuts down unused compute. Data lifecycle policies reduce storage.

**Figure:** *Six-pillar hexagon diagram.* Each pillar of the Well-Architected Framework as one segment of a hexagon, with a distinct color and icon. The hexagon rotates so "Security" is at the top (emphasizing its foundational importance). Each segment shows: pillar name + NorthStar-specific implementation example in small text. The overall visual communicates: "well-architected is multidimensional, not a single checkbox."

**Notes:** "The AWS Well-Architected Framework is a real tool that AWS solution architects use to evaluate production architectures. You can run a Well-Architected Review on your own platform after Lab 1 — it's a free online assessment that generates specific recommendations." For the team project, using the Well-Architected Framework to evaluate your design choices is excellent practice and good documentation for the final report.

---

## Slide 15 — NorthStar Architecture Decisions: The Complete ADR Set
**Layout:** Summary of all major platform decisions with brief rationale

**Content:**
**NorthStar Platform Decision Summary:**

| Decision | Choice Made | Key Rationale |
|----------|------------|---------------|
| VPC topology | Private VPC + endpoints | PII data cannot transit public internet |
| Compute | SageMaker managed | Build/buy: infrastructure not a differentiator |
| IaC tool | Terraform | Multi-cloud capable; industry standard; better state management than CloudFormation |
| IAM design | Three-role least-privilege | Blast radius minimization; audit requirements |
| S3 organization | Four-zone architecture | Clean lineage; appropriate governance per zone |
| Model registry | SageMaker Model Registry | Native integration; approval workflow built-in |
| Experiment tracking | MLflow (on SageMaker) | Vendor-neutral; full experiment reproducibility |
| Feature store | SageMaker Feature Store | Eliminates training/serving skew; online + offline paths |
| Authentication | IAM (not SSO) | Simpler for course; enterprise would use SSO |

**Figure:** *Decision table with rationale column.* Clean table as above. Color coding: decisions that are "buy/configure" choices in light green; "build" decisions in light blue. The rationale column uses concise engineering language — short phrases, not sentences. A bottom row: "Revisit at: Lab 5" indicating which decisions might need to be reconsidered later.

**Notes:** "This table is what your Lab 1 ADR should cover — these are the decisions. The depth your ADR needs to go into each decision is the Context/Options/Decision/Consequences structure from Slide 8." By the end of the semester, the NorthStar ADR set will be a complete architectural decision log for an enterprise AI platform — a genuine portfolio artifact.

---

## Slide 16 — Key Takeaways + What's Next
**Layout:** Takeaways + Lab 1 and Lab 2 prep

**Content:**
**Key Takeaways:**
1. SageMaker Domain is the hub of the NorthStar platform — VPC configuration inside the domain determines security posture for all downstream components
2. IAM least-privilege is an engineering discipline — three scoped roles, each with exactly the access it needs, nothing more
3. Four-zone S3 architecture provides clean data lineage and appropriate governance at each stage
4. Terraform modularity in Lab 1 pays off in Labs 2-7 — invest in good module design now
5. The Lab 1 ADR documents your reasoning, not just your decisions — show your alternatives considered

**Next Session (Thu Sep 17):**
- Topic: Data & Feature Engineering I — why data engineering for AI is different; ingestion patterns; the Zillow cautionary tale
- **Lab 2 is assigned Thursday** — start thinking about data pipeline design
- Reading due: *Data & Feature Engineering* — "Motivation" through "Feature Engineering"

**Lab 1 Reminder:**
- Due: Saturday, September 19, midnight
- Must submit: GitHub repo link on Canvas
- TA will clone and run `terraform apply` — test this yourself first

**Figure:** *Five-takeaway list + Lab 1 countdown.* Standard numbered takeaway format. Below: a prominent "Lab 1 Due: Saturday" callout in amber/orange with 4-day countdown. Lab 2 preview in teal: "Assigned Thursday."

**Notes:** "Four days. If your Terraform isn't applying cleanly yet, come to office hours today or tomorrow — not Friday night." The urgency of Lab 1 completion is real. Students who don't finish Lab 1 cleanly struggle with Lab 2, which builds directly on it. End with: "Who here has a clean `terraform plan` output?" Any hands that aren't up need to be in office hours tomorrow.
