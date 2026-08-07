# ADR-001: NorthStar Platform Foundation — Lab 1 Architecture

## Status

Accepted — CS 401R Lab 1 reference implementation

---

## Context

NorthStar Financial Services is migrating its credit risk and churn prediction workloads to AWS. Lab 1 establishes the platform foundation: the networking, storage, identity, and ML environment that every subsequent lab builds on.

Three decisions drive the Lab 1 design:

1. **How should the network be structured?** Public subnet only vs. private subnet with NAT Gateway vs. VPC endpoints.
2. **How should data be organized in S3?** Single bucket with prefixes vs. multiple buckets per tier.
3. **Which IAM roles are needed now vs. later?** MLEngineer only vs. all three roles up front.

The guiding constraint is the AWS Free Tier account: up to $200 in credits that expire in 6 months. Every architectural choice must be justifiable against that budget and timeline.

---

## Decisions

### Network: Single Public Subnet, No NAT Gateway

**Decision:** One public subnet (`10.0.100.0/24`) in `us-east-1a`, attached to an Internet Gateway. No private subnets. No NAT Gateway. SageMaker Studio runs directly in the public subnet.

**Rationale:**

A NAT Gateway costs $32–45/month ($0.045/hour + $0.045/GB processed). Over seven labs, a NAT Gateway alone would consume 20–30% of the $150 credit before any ML work runs. For Lab 1, whose purpose is deploying the Studio control plane and validating the module structure, that cost is not justified.

SageMaker Studio in a public subnet has no meaningful security gap for a lab environment: the security group restricts inbound traffic to the VPC CIDR (`10.0.0.0/16`), blocking all public internet inbound. Studio needs outbound internet access to pull container images from ECR and reach the SageMaker API — the Internet Gateway provides this without NAT overhead.

**Lab 2 transition:** When real training workloads begin in Lab 2, Studio moves to a private subnet with a NAT Gateway. The Terraform module accepts `public_subnet_id` as an explicit variable so that swap requires only a variable change at the environment level — no module refactoring.

**Alternatives rejected:**

| Option | Reason Rejected |
|--------|----------------|
| Private subnet + NAT Gateway from day one | $32–45/month cost not justified for a control-plane-only lab |
| VPC Gateway Endpoint for S3 (free) | Worth adding in Lab 2 once real data volumes make the cost difference measurable |
| VPC Interface Endpoints for SageMaker API/Runtime | $15/month each; justified in Lab 2 when training jobs make frequent API calls |

---

### Storage: Single S3 Bucket, Four Prefixes

**Decision:** One bucket (`northstar-dev-data-{account_id}`) with four logical prefixes: `raw/`, `processed/`, `features/`, `artifacts/`.

**Rationale:**

Separate buckets per data tier (raw, processed, features, artifacts) add operational complexity without benefit at Lab 1 scale. A single bucket with IAM-scoped prefix permissions achieves the same access isolation at lower cost and simpler Terraform. The prefix structure also mirrors the data lake zones that students will see in enterprise implementations — teaching the pattern without the operational overhead.

The bucket name includes the AWS account ID to guarantee global S3 namespace uniqueness. S3 bucket names are global; `northstar-dev-data` would collide if multiple students deploy to separate accounts within the same organization.

**Lab 2 transition:** Lifecycle rules (Intelligent-Tiering on `raw/`, Glacier transition on `processed/`) are added in Lab 2 when real data begins flowing. Adding lifecycle rules to an existing bucket requires no resource replacement.

**Alternatives rejected:**

| Option | Reason Rejected |
|--------|----------------|
| Four separate buckets (one per tier) | More Terraform resources, more IAM ARNs, more student confusion — no benefit at lab scale |
| One flat bucket (no prefix structure) | Doesn't teach data lake zone separation; IAM scoping becomes impossible |

---

### IAM: One Role (MLEngineer Only)

**Decision:** One IAM role in Lab 1: `northstar-dev-MLEngineer`. This role trusts `sagemaker.amazonaws.com` and has scoped permissions to read/write `artifacts/` and `features/` prefixes, run SageMaker training/inference operations, write CloudWatch logs, and pull ECR images.

**Rationale:**

The `DataEngineer` and `ModelMonitor` roles govern services that don't exist in Lab 1 — AWS Glue (Lab 2), Lambda (Lab 3), and CloudWatch Evidently Monitor (Lab 6). Creating roles for services that aren't deployed is dead weight: it generates IAM overhead, creates a false impression that those services are active, and adds 30+ resources to the Terraform plan that students can't validate.

The MLEngineer role deliberately excludes write access to `raw/` and `processed/` prefixes. This enforces the data ownership principle: raw data is the DataEngineer's responsibility. Students should be able to articulate _why_ the MLEngineer is denied `s3:PutObject` on `raw/` — the verify script confirms this with an IAM policy simulation.

**Lab 2 transition:** The IAM module is additive. Lab 2 adds `DataEngineer` (trusting `glue.amazonaws.com`) and `ModelMonitor` (trusting `sagemaker.amazonaws.com` with Monitor-specific permissions) as new resources in the same module. No existing resources change.

**Alternatives rejected:**

| Option | Reason Rejected |
|--------|----------------|
| All three roles in Lab 1 | Roles without corresponding services are dead weight and mislead students |
| `AmazonSageMakerFullAccess` managed policy | 200+ permissions; violates least-privilege; rubric explicitly penalizes this |
| Separate policies per S3 prefix as standalone resources | Over-engineering for one role; inline policy is cleaner at this scope |

---

## Consequences

**Positive:**
- Lab 1 infrastructure costs approximately $5–8 for a typical deploy-and-destroy cycle, well within the per-lab budget target.
- Module structure is additive: each subsequent lab adds resources without refactoring existing modules.
- IAM policy simulation in `verify-lab1.sh` gives students immediate feedback on whether their scoping is correct.

**Negative / Watch for in Labs 2–7:**
- The transition from public to private subnet in Lab 2 requires students to understand _why_ the change is happening — not just apply a new variable value. Build that explanation into Lab 2's setup section.
- Single-bucket prefix scoping works for two roles. If Lab 5 or 6 introduces cross-account access, separate buckets become necessary. Document this inflection point explicitly.
- Students who read ahead may implement features from later labs (Feature Store, lifecycle rules, multiple roles) in Lab 1. The verify script will pass — but grading should confirm the Lab 1 architecture matches the spec, not just that it works.

---

## Services Selected and Why

| Service | Role in Lab 1 | Alternative Considered |
|---------|--------------|----------------------|
| Amazon VPC | Network isolation; security group controls inbound access to Studio | Default VPC — rejected because default VPCs have no tag-based cost allocation and expose all resources to internet by default |
| Amazon S3 | Data lake storage; versioning for artifact recovery | EFS — rejected; per-GB cost is 10x S3, and SageMaker doesn't require POSIX semantics for batch workloads |
| AWS IAM | Least-privilege access control; scoped to specific S3 prefixes | AWS Lake Formation — rejected; adds significant complexity with no benefit at one-role, one-bucket scale |
| Amazon SageMaker Domain | Managed Studio IDE; shared domain allows multiple user profiles without separate infrastructure | Self-managed JupyterHub on EC2 — rejected; operational overhead defeats the purpose of a managed platform course |
| Amazon ECR | Container image registry for training job containers | Docker Hub — rejected; AWS data transfer charges apply to Docker Hub pulls ($0.09/GB); ECR pulls within-region are free |
