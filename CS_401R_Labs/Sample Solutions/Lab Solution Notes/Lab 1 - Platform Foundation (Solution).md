---
tags: [CS401R, lab-solution, lab-1, terraform, AWS, TA-guide]
course: CS 401R
lab: 1
status: answer-key
total_points: 100
---

# Lab 1 — Platform Foundation: TA Grading Guide

> **For TA use only.** Do not distribute to students.
> Total points: 100. Run `bash scripts/verify-lab1.sh` in the student's repo root before manual review — it automates most Part A and Part B checks.

---

## Quick Reference: What Lab 1 Actually Builds

Lab 1 is intentionally simple. The correct architecture has:

| Component | Lab 1 Spec | Common Student Error |
|-----------|-----------|---------------------|
| Subnets | 1 public subnet only (`10.0.100.0/24`, `us-east-1a`) | Adds private subnets, NAT Gateway (Lab 2 scope) |
| S3 | 1 bucket with 4 prefixes (`raw/`, `processed/`, `features/`, `artifacts/`) | Creates 4 separate buckets (Lab 2+ scope) |
| IAM roles | 1 role: `MLEngineer` | Creates `DataEngineer` and `ModelMonitor` (Lab 2 scope) |
| SageMaker | Domain in public subnet, 1 user profile (`MLEngineer`) | Domain in private subnet with VPC endpoints (Lab 2 scope) |
| Remote state | S3 backend + DynamoDB lock, bootstrapped via script | Committed `terraform.tfstate` to git |
| Variable naming | `var.project`, `var.environment` | `var.project_name` (old pattern — does not match module interfaces) |

The live reference implementation is at `/Users/scott1/northstar-ai-platform`. When in doubt, that codebase is the answer.

---

## Part A: AWS Environment (35 pts)

### Task A1 — Architecture Diagram (10 pts)

**Deliverable:** A diagram file in `docs/` (draw.io, PDF, PNG, or similar) showing the Lab 1 architecture.

**Pass criteria (all required for full credit):**

- [ ] VPC boundary labeled with CIDR `10.0.0.0/16`
- [ ] Public subnet labeled with CIDR `10.0.100.0/24` and AZ `us-east-1a`
- [ ] Internet Gateway shown and attached to VPC
- [ ] Route Table shown with `0.0.0.0/0 → IGW` route
- [ ] Security Group shown attached to SageMaker Domain; inbound rule annotated (`VPC CIDR only`)
- [ ] S3 bucket shown outside VPC (regional service); 4 prefixes visible or referenced
- [ ] MLEngineer IAM role shown; arrows to `artifacts/` and `features/` prefixes only
- [ ] SageMaker Studio / Domain inside the public subnet
- [ ] Uses official AWS service icons (not generic shapes or hand-sketched)
- [ ] Includes a legend or data-flow numbered steps

**Grading notes:**

Award 8/10 if the diagram has all required components but missing one annotation (e.g., no CIDR on subnet). Award 6/10 if the diagram is architecturally correct but does not use AWS icons. Award 4/10 or less if the diagram shows incorrect architecture (e.g., NAT Gateway, private subnets, 4 separate S3 buckets) — the diagram is graded on correctness, not just completeness.

Do not deduct for aesthetic choices (color, layout, font). Do deduct if IAM arrows show MLEngineer accessing `raw/` or `processed/` — that is a correctness error, not a style choice.

---

### Task A2 — Network Layer (10 pts)

**Verified by:** `bash scripts/verify-lab1.sh` (Part A checks)

**Pass criteria:**

- [ ] VPC created (`aws ec2 describe-vpcs` returns the VPC ID from Terraform output)
- [ ] DNS hostnames and DNS resolution enabled on the VPC
- [ ] Public subnet `10.0.100.0/24` in `us-east-1a` exists
- [ ] Internet Gateway attached to VPC
- [ ] Route table has `0.0.0.0/0 → igw-*` route associated with the public subnet
- [ ] Security group: inbound `0.0.0.0/0` is NOT present; inbound rule is VPC CIDR only (`10.0.0.0/16`)
- [ ] No private subnets exist (verify script confirms count = 0)

**Point breakdown:**

| Check | Points |
|-------|--------|
| VPC with correct CIDR and DNS settings | 3 |
| Public subnet correct CIDR/AZ | 2 |
| IGW attached + route table configured | 3 |
| Security group correct inbound rule | 2 |

**Common mistakes:**

- **Public subnet has `map_public_ip_on_launch = false`:** Studio needs a public IP to reach the internet. Symptom: domain applies successfully but Studio fails to launch with a network connectivity error.
- **Security group inbound rule is `0.0.0.0/0`:** Allows all public internet inbound traffic to Studio. This is a security error. Award 0 for the SG check.
- **Route table not associated with the public subnet:** Subnet exists but has no route to IGW. Studio domain will apply but Studio won't launch. Full points for route table only if association is present.
- **Student adds NAT Gateway and private subnets:** This is Lab 2 scope. If the rest of Lab 1 still works, deduct 2 points for out-of-scope implementation and note it. Do not award partial credit for NAT — it adds $32/month charge.

---

### Task A3 — Storage and IAM (10 pts)

**Verified by:** `bash scripts/verify-lab1.sh` (A3 checks and IAM simulation)

**Pass criteria — S3 (5 pts):**

- [ ] Bucket name: `northstar-dev-data-{account_id}` (contains account ID)
- [ ] Versioning: Enabled
- [ ] Encryption: SSE-S3 (AES256)
- [ ] Public access: fully blocked (all four `block_public_*` settings = true)
- [ ] All four prefixes present: `raw/.keep`, `processed/.keep`, `features/.keep`, `artifacts/.keep`

**Pass criteria — IAM (5 pts):**

- [ ] Role name: `northstar-dev-MLEngineer`
- [ ] Trust policy: `sagemaker.amazonaws.com` only
- [ ] S3 permissions scoped to `artifacts/*` and `features/*` only (NOT `raw/*` or `processed/*`)
- [ ] SageMaker training/inference permissions present (`CreateTrainingJob`, etc.)
- [ ] ECR read permissions present (needed for training container pulls)
- [ ] CloudWatch Logs write present
- [ ] IAM sim: `sagemaker:CreateTrainingJob` → `allowed`
- [ ] IAM sim: `s3:PutObject` on `raw/` → `implicitDeny` or `explicitDeny`

**Point breakdown:**

| Check | Points |
|-------|--------|
| Bucket name correct (includes account ID) | 1 |
| Versioning + encryption + public access block | 2 |
| All 4 prefixes present | 2 |
| MLEngineer role trust correct | 1 |
| S3 permissions scoped to artifacts/ and features/ only | 2 |
| SageMaker + ECR + CloudWatch permissions | 2 |

**Common mistakes:**

- **Bucket missing account ID:** Name is `northstar-dev-data` without the account suffix. Will work within one account but fails if multiple students use shared environments. Deduct 1 point.
- **`AmazonSageMakerFullAccess` managed policy attached:** This is a 200+ permission policy that includes S3 full access, EC2 full access, IAM PassRole unrestricted. It violates least-privilege and will pass the IAM simulation trivially. Deduct all 4 IAM points — the student did not engage with the access design at all.
- **MLEngineer can write to `raw/`:** The IAM simulation will return `allowed` instead of `implicitDeny`. This is a correctness failure — the data ownership boundary is wrong. Deduct 2 points.
- **S3 resource ARN uses wildcard `northstar-*`:** Grants access to any bucket with that prefix. If the account has other NorthStar-prefixed buckets, this is overpermissioned. Deduct 1 point.
- **Trust policy missing (or wrong service):** If trust is `lambda.amazonaws.com` or `ec2.amazonaws.com`, SageMaker cannot assume the role. The domain apply will fail. Full deduct on IAM points.

---

### Task A4 — SageMaker Domain (5 pts)

**Verified by:** `bash scripts/verify-lab1.sh` (A4 check)

**Pass criteria:**

- [ ] Domain status: `InService` (not `Pending` or `Failed`)
- [ ] Domain uses correct VPC and public subnet IDs (from Terraform outputs)
- [ ] Studio URL accessible — student can click "Launch Studio" from the console
- [ ] Studio shutdown screenshot submitted as `docs/lab1-studio-shutdown.png`
- [ ] Screenshot shows no running Kernel Gateway or JupyterServer apps

**Point breakdown:**

| Check | Points |
|-------|--------|
| Domain InService | 2 |
| Studio launches successfully | 1 |
| Shutdown screenshot present and correct | 2 |

**Common mistakes:**

- **Domain stuck in `Pending`:** Usually a service-linked role issue. New AWS accounts sometimes require a manual one-time creation: IAM → Create Role → SageMaker Studio. Once created, the domain usually recovers. If the student hit this and documented it, award full points.
- **Screenshot shows apps still running:** Award 1/2 for the screenshot — they took it but didn't shut down properly.
- **Domain in private subnet:** Will apply but Studio won't be able to pull container images without NAT or VPC endpoints. If domain is `InService` and Studio launches, award full points even if the subnet is wrong — but note the architecture deviation.
- **`app_network_access_type = "VpcOnly"`:** Lab 1 should not set this. It blocks public access to the Studio UI, making the interface unreachable. Deduct 1 point.

---

## Part B: Infrastructure as Code (45 pts)

### Task B1 — Module Structure (15 pts)

**Verified by:** `bash scripts/verify-lab1.sh` (B1 checks), plus manual code review

**Pass criteria:**

- [ ] 4 modules present: `infrastructure/modules/vpc/`, `iam/`, `storage/`, `sagemaker/`
- [ ] Each module has `main.tf`, `variables.tf`, `outputs.tf`
- [ ] VPC module: creates VPC, public subnet, IGW, route table + association, security group — nothing else
- [ ] IAM module: creates MLEngineer role + policy + attachment — nothing else
- [ ] Storage module: creates one S3 bucket + public access block + versioning + SSE + 4 prefix objects — nothing else
- [ ] SageMaker module: creates domain + user profile — nothing else
- [ ] No hardcoded literal `"northstar"` in resource name attributes (all use `var.project`)
- [ ] `terraform fmt` passes (no formatting errors)
- [ ] `terraform validate` passes in `environments/dev/` (no schema errors)

**Point breakdown:**

| Check | Points |
|-------|--------|
| All 4 modules present with correct file structure | 3 |
| VPC module correct resources (no extras) | 3 |
| IAM module correct resources (one role) | 3 |
| Storage module correct (one bucket, 4 prefix objects) | 3 |
| SageMaker module correct (domain + user profile) | 2 |
| No hardcoded literals; fmt and validate pass | 1 |

**Common mistakes:**

- **Student added private subnets, NAT, EIPs, or VPC endpoints to the VPC module:** This is the single most common error. If the module has more than: `aws_vpc`, `aws_subnet` (one, public), `aws_internet_gateway`, `aws_route_table`, `aws_route_table_association`, `aws_security_group` — there are extra resources. Deduct 2 points per out-of-scope resource category (NAT=2, VPC endpoints=2).
- **Storage module creates 4 separate buckets:** Deduct 3 points — this is a fundamental architectural deviation, not a style issue.
- **SageMaker module includes `aws_sagemaker_feature_group`:** Lab 2 scope. Deduct 2 points.
- **Variable naming uses `var.project_name` instead of `var.project`:** The module interface is wrong. It won't connect to the environment root module without modification. Treat this as a configuration error. Award 0 for the affected module's wiring check (B1) but do not cascade to B2 if the student fixed it in the root module.
- **Module accepts only `project` but no `environment` variable:** All resources must distinguish dev from other environments. Without `var.environment`, naming collisions occur. Deduct 1 point.
- **`terraform validate` fails:** Zero points for B1 — code that doesn't parse is not a working module.

---

### Task B2 — Apply and Destroy (15 pts)

**Verified by:** Manual — student submits `docs/lab1b-apply-output.txt`

**Pass criteria:**

- [ ] `terraform apply` completes with 0 errors (student submits apply output)
- [ ] Apply output shows correct resource count: approximately 18–22 resources for Lab 1 spec
  - VPC: aws_vpc, aws_subnet, aws_internet_gateway, aws_route_table, aws_route_table_association, aws_security_group = 6
  - IAM: aws_iam_role, aws_iam_policy, aws_iam_role_policy_attachment = 3
  - Storage: aws_s3_bucket, aws_s3_bucket_public_access_block, aws_s3_bucket_versioning, aws_s3_bucket_server_side_encryption_configuration, aws_s3_object (×4) = 8
  - SageMaker: aws_sagemaker_domain, aws_sagemaker_user_profile = 2
  - **Total: ~19 resources**
- [ ] Resources visible in AWS Console (verified against Terraform outputs)
- [ ] `terraform destroy` completes cleanly (no orphaned resources)

**Point breakdown:**

| Check | Points |
|-------|--------|
| Apply completes 0 errors | 7 |
| Resource count within Lab 1 range (15-25) | 3 |
| Resources visible in console (spot check S3, IAM role, Domain) | 3 |
| Destroy completes cleanly | 2 |

**Common mistakes:**

- **Apply output shows 35–50 resources:** Student built Lab 2+ architecture. Review the resource list carefully. If the extra resources are all Lab 2-scope (NAT Gateway, private subnets, VPC endpoints, multiple IAM roles), deduct 3 points and note the scope creep.
- **Apply fails on SageMaker Domain with service-linked role error:** This is a new-account bootstrap issue, not a student error. If the student documents the workaround (IAM → Create Role → SageMaker Studio) and gets the domain to `InService`, award full points.
- **Destroy leaves orphaned SageMaker apps:** Students sometimes launch Studio before destroying. Active Studio apps block domain deletion. This is a process error, not a code error — award full points if the student eventually destroys cleanly.
- **Apply output not submitted:** Deduct 5 points. No output = no evidence the student ran apply.

---

### Task B3 — Remote State (8 pts)

**Verified by:** `bash scripts/verify-lab1.sh` (B3 check), plus manual review of `backend.tf`

**Pass criteria:**

- [ ] `infrastructure/environments/dev/backend.tf` exists
- [ ] Backend type: `s3`
- [ ] `bucket` value is `northstar-tfstate-{account_id}` (contains real account ID, not placeholder)
- [ ] `dynamodb_table` is `northstar-tfstate-lock`
- [ ] `encrypt = true`
- [ ] `scripts/bootstrap-state.sh` (or equivalent) is committed
- [ ] Bootstrap script is idempotent (running twice does not error)
- [ ] S3 state bucket has versioning and encryption enabled (verify in console)

**Point breakdown:**

| Check | Points |
|-------|--------|
| backend.tf correct structure (s3 + dynamodb + encrypt) | 3 |
| State bucket created with versioning + encryption | 2 |
| DynamoDB lock table created | 1 |
| Bootstrap script committed and idempotent | 2 |

**Common mistakes:**

- **`terraform.tfstate` committed to git:** Zero points for B3. The entire purpose of remote state is to keep state out of the repository. Also a security issue if state contains account IDs. Ask student to remove from git history.
- **Backend uses `YOUR_ACCOUNT_ID` placeholder (not patched):** `terraform init` will fail. Bootstrap script either wasn't run or wasn't written to patch the file. Deduct 2 points.
- **No DynamoDB lock table:** State locking is not configured. Multiple concurrent applies could corrupt state. Deduct 1 point.
- **Trying to use `${var.aws_account_id}` in backend block:** Terraform parses backend blocks before evaluating variables — this is a syntax error. Common mistake when students try to parameterize the backend. Full deduct on the backend configuration points; award partial credit if student worked around it manually.

---

### Task B4 — Parameterization (4 pts)

**Verified by:** `bash scripts/verify-lab1.sh` (B4 check), plus manual review

**Pass criteria:**

- [ ] 7 required variables with descriptions: `project`, `environment`, `aws_region`, `aws_account_id`, `vpc_cidr`, `public_subnet_cidr`, `availability_zone`
- [ ] All variables have `description` fields (not empty)
- [ ] `terraform.tfvars.example` committed to git
- [ ] `terraform.tfvars` is absent from git (covered by `.gitignore`)
- [ ] No hardcoded AWS account ID in any `.tf` file

**Point breakdown:**

| Check | Points |
|-------|--------|
| All 7 required variables with descriptions | 2 |
| tfvars.example committed; tfvars absent from git | 1 |
| No hardcoded account ID in .tf files | 1 |

**Common mistakes:**

- **`aws_account_id` has a default value:** The account ID should never have a default — it forces the student to set it explicitly in `terraform.tfvars`. A default of `""` is acceptable (forces explicit set), but a default of a real account ID is not.
- **`terraform.tfvars` committed to git:** Deduct 1 point. Run `git log -- '*.tfvars'` to confirm.

---

### Task B5 — LocalStack Validation (3 pts)

**Verified by:** `bash scripts/verify-lab1.sh` (B5 check)

**Pass criteria:**

- [ ] `make local-validate` exits 0 (or equivalent LocalStack deploy command)
- [ ] `docs/lab1-localstack-output.txt` committed and shows:
  - S3 bucket created with `northstar-local-data-*` name
  - IAM role `northstar-local-MLEngineer` present
  - VPC created
  - Public subnet created
- [ ] Student's `environments/local/main.tf` skips the SageMaker module (LocalStack Community does not support SageMaker)

**Point breakdown:**

| Check | Points |
|-------|--------|
| Local environment configuration present and skips SageMaker | 1 |
| LocalStack output file committed with correct content | 2 |

**Common mistakes:**

- **Student used `tflocal` instead of plain Terraform with explicit endpoints:** `tflocal` works but `tflocal init -backend=false` still attempts to create an S3 state bucket in LocalStack. This is fine if the output is correct. Award full points.
- **Student tries to deploy SageMaker to LocalStack:** LocalStack Community does not support the SageMaker API. `apply` will fail. The correct solution is a separate `environments/local/` that omits the SageMaker module. Deduct 1 point if the student includes SageMaker in local config (even if they describe why it fails).
- **Output file missing:** Deduct 2 points.

---

## Shared Deliverables (20 pts)

### Task S1 — Architecture Decision Record (12 pts)

**Deliverable:** `docs/lab1-architecture-decision-record.md`

**Pass criteria (evaluate holistically):**

- [ ] **Context section:** Describes the NorthStar-specific problem — not generic ("we need a VPC") but specific ("NorthStar's AWS Free Tier account has a $200 credit limit expiring in 6 months, making NAT Gateway cost significant")
- [ ] **Decision section:** States the actual decision made, not just restates what was built
- [ ] **Alternatives rejected:** At least one meaningful alternative per major decision (network, storage, IAM), with a concrete reason for rejection
- [ ] **Consequences:** Both positive and negative consequences named; at least one forward-looking note about what changes in Lab 2
- [ ] **Service rationale:** Explains why each service was chosen — not just "SageMaker is a managed service" but what specific property of SageMaker addresses a specific NorthStar constraint

**Point breakdown:**

| Section | Points |
|---------|--------|
| Context: NorthStar-specific, not generic | 2 |
| Decision: clear, stated (not just described) | 2 |
| Alternatives: at least one per major decision, concrete reason | 3 |
| Consequences: positive + negative + Lab 2 transition noted | 3 |
| Service rationale: specific, not generic | 2 |

**What separates A-range from C-range:**

An A-range ADR names specific costs (`$32–45/month for NAT Gateway against $150 credit`) and specific trade-offs (`public subnet for Lab 1, private + NAT in Lab 2`). A C-range ADR says "we chose a public subnet because it's simpler" without explaining what simpler means in this context or what the consequence is.

**Common mistakes:**

- **ADR is a description of what was built, not a decision record:** The document describes the infrastructure but never states a decision or rejects an alternative. Award 4/12 maximum.
- **Generic ADR not tied to NorthStar:** "S3 is cheap and scalable" applies to every AWS user. The ADR should reflect NorthStar's specific constraints. Award 6/12 maximum if content is correct but not contextualized.
- **No consequences section:** ADR without consequences is incomplete. Deduct 3 points.

---

### Task S2 — Cost Estimate (8 pts)

**Deliverable:** `docs/lab1-cost-estimate.md`

**Pass criteria:**

- [ ] **At least 5 cost components** estimated: VPC (free/minimal), S3 storage, S3 requests, SageMaker Studio (kernel instance time), SageMaker Domain (free tier or minimal)
- [ ] **Explicit assumptions:** Compute hours per week, GB of data stored, number of training job runs — not assumed silently
- [ ] **Pricing source:** References AWS pricing page, AWS calculator, or states "as of [date]"
- [ ] **Monthly estimate per lab vs. semester total**
- [ ] **At least one quantified optimization:** e.g., "Shutting down kernels when not in use saves approximately $X/month based on Y hours of idle time"

**Point breakdown:**

| Check | Points |
|-------|--------|
| 5+ components with per-unit cost | 3 |
| Explicit assumptions stated | 2 |
| Optimization identified and quantified | 2 |
| Totals and semester projection | 1 |

**Common mistakes:**

- **Cost estimate lists only SageMaker and S3:** Missing VPC (data transfer, though minimal), NAT Gateway (should explicitly note this is $0 in Lab 1), and the cost difference between leaving Studio kernels running vs. shutting down. Deduct 1 point per missing component category.
- **No assumptions stated:** "S3 costs $X/month" without specifying GB stored is meaningless. Deduct 2 points.
- **Optimization is generic:** "Stop resources when not in use" without a quantification. The student should calculate the difference: `ml.t3.medium` runs at $0.05/hour → 8 hours/day × 5 days = $2/week if never shut down vs. $0.40/week if shut down after each session. Deduct 1 point for unquantified optimization.

---

## Automated Grading Workflow

```bash
# 1. Clone student repo
git clone <student_repo_url> student-lab1
cd student-lab1

# 2. Run the verify script (does not require AWS credentials for static checks)
bash scripts/verify-lab1.sh 2>&1 | tee grading-output.txt

# 3. Check git history for secrets
git log --all -S "AKIA" --oneline

# 4. Manual checks
# - Review infrastructure/modules/*/main.tf for out-of-scope resources
# - Read docs/lab1-architecture-decision-record.md
# - Read docs/lab1-cost-estimate.md
# - Inspect docs/lab1-studio-shutdown.png

# 5. If you have AWS credentials, run the full AWS checks:
# (requires student's account to still have resources deployed)
# AWS_DEFAULT_REGION=us-east-1 bash scripts/verify-lab1.sh
```

---

## Grading Summary Sheet

| Task | Max Pts | Automated? | Notes |
|------|---------|-----------|-------|
| A1 — Architecture Diagram | 10 | No | Manual review of diagram file |
| A2 — Network Layer | 10 | Yes (verify script) | Check SG inbound rule manually |
| A3 — Storage + IAM | 10 | Yes (verify script + IAM sim) | Check for AmazonSageMakerFullAccess |
| A4 — SageMaker Domain | 5 | Yes (verify script) | Check screenshot manually |
| B1 — Module Structure | 15 | Partial | Verify no out-of-scope resources in modules |
| B2 — Apply + Destroy | 15 | No | Review apply output file |
| B3 — Remote State | 8 | Partial | Check backend.tf + git history for tfstate |
| B4 — Parameterization | 4 | Partial | Check tfvars absent from git |
| B5 — LocalStack | 3 | Yes (verify script) | Check output file |
| S1 — ADR | 12 | No | Holistic review against rubric |
| S2 — Cost Estimate | 8 | No | Check 5 components + assumptions |
| **Total** | **100** | | |

---

## Score Deduction Reference

| Issue | Deduction |
|-------|-----------|
| NAT Gateway in Lab 1 | -2 (scope creep) + note |
| Private subnets in Lab 1 | -2 (scope creep) |
| 4 separate S3 buckets instead of 1 | -3 (architectural error) |
| 3 IAM roles instead of 1 | -2 (scope creep) |
| `AmazonSageMakerFullAccess` used | -4 (all IAM points) |
| MLEngineer can write to `raw/` | -2 |
| `terraform.tfstate` in git | -5 (B3 total) + security flag |
| `terraform.tfvars` in git | -1 |
| AWS access key (`AKIA*`) in git history | -5 + security flag; notify Scott |
| `terraform validate` fails | -15 (B1 total; code doesn't work) |
| Apply output not submitted | -5 |
| ADR is description not decision record | cap at 4/12 |

---

## Security Escalation Protocol

If `git log --all -S "AKIA" --oneline` returns any results:
1. Note the commit hash
2. Award 0 for Task B4 (parameterization) and flag security violation in Canvas comments
3. Email Scott immediately: scott@toborg.com — do not wait until grade review
