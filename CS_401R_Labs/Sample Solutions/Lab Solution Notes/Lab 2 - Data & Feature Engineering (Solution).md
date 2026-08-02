---
tags: [CS401R, lab-solution, lab-2, terraform, glue, feature-store, TA-guide]
course: CS 401R
lab: 2
status: answer-key
total_points: 100
---

# Lab 2 — Data & Feature Engineering: TA Grading Guide

> **For TA use only.** Do not distribute to students.
> Total points: 100. Run `bash scripts/verify-lab2.sh` in the student's repo root before manual review — it automates the large majority of Tasks 1–3 and the file-presence checks for Tasks 4–5.

---

## Quick Reference: What Lab 2 Actually Builds

Lab 2 adds the complexity Lab 1 deliberately stripped out, then builds the data pipeline on top of it.

| Component | Lab 2 Spec | Common Student Error |
|-----------|-----------|---------------------|
| Subnets | Public (`10.0.100.0/24`) **+ private (`10.0.1.0/24`)**, both `us-east-1a` | Adds a second AZ (Lab 1's old stale guide showed 4 subnets) |
| NAT Gateway | One, in the public subnet, with an Elastic IP | Places NAT in the private subnet — it must be public to reach the IGW |
| SageMaker Domain | Private subnet, `app_network_access_type = VpcOnly` | Leaves it in the public subnet, or forgets `VpcOnly` |
| IAM roles | 3: `MLEngineer`, `DataEngineer`, `ModelMonitor` | DataEngineer scoped to `raw/`+`processed/` only — breaks Task 3 |
| S3 lifecycle | 5 rules on `raw/`, `processed/`, `features/`, `datacapture/` | Applies one blanket rule to the whole bucket; or omits `expire-datacapture`, leaving Lab 5/6 capture data unbounded |
| Glue | Catalog DB, crawler, 2 ETL jobs, NETWORK connection | Jobs run outside the VPC (works, but violates the architecture) |
| Feature Store | 8 features, `event_time` **Fractional**, online + offline | Declares `event_time` as `String` — records silently never land |
| **Grain** | `processed/` is transaction level; `features/` is customer level | **Deduplicates on `customer_id`** — the single most damaging error |

The live reference implementation is at `/Users/scott1/northstar-ai-platform`. When in doubt, that codebase is the answer. Verified end-to-end on 2026-07-27 against account `711457211658`.

**Reference run numbers** (seeded generator, so these should reproduce almost exactly):

| Stage | Rows | Notes |
|---|---|---|
| `raw/customers/` | 10,150 | 1,967 distinct customers; 6 injected defect classes |
| `processed/customers/` | 9,800 | 201 null `customer_id` dropped, 150 duplicate transactions removed |
| `features/customers/` | 1,967 | one row per customer |
| Tier distribution | 995 / 554 / 299 / 119 | Bronze / Silver / Gold / Platinum |
| `churn_risk_score` | 179 distinct values, 0.0–1.0 | non-degenerate by design |

A student whose processed row count is close to 1,967 rather than ~9,800 has deduplicated on the wrong key. See Task 2.

---

## Task 1 — Extend Platform Infrastructure (25 pts)

### Private subnet + NAT Gateway + Domain relocation (10 pts)

**Pass criteria:**

- [ ] `aws_subnet` private, `10.0.1.0/24`, `us-east-1a`, `map_public_ip_on_launch = false`
- [ ] `aws_eip` allocated and associated with the NAT Gateway
- [ ] `aws_nat_gateway` placed in the **public** subnet
- [ ] `aws_route_table` for private with `0.0.0.0/0 → nat_gateway_id`
- [ ] `aws_route_table_association` for the private subnet
- [ ] Variable `enable_nat_gateway` (bool, default true), used via `count`
- [ ] Module output exposes `private_subnet_id`
- [ ] SageMaker Domain `subnet_ids` points at the private subnet
- [ ] `app_network_access_type = "VpcOnly"`

**Verification:** `aws sagemaker describe-domain` returns `Status: InService`, the private subnet ID, and `AppNetworkAccessType: VpcOnly`. `aws ec2 describe-nat-gateways` returns `State: available`.

**Grading notes:**

Award full credit if the domain is InService in the private subnet. If the student put the NAT Gateway in the private subnet, the apply usually still succeeds but the private subnet has no working egress — deduct 4 and note it; this is a real architectural misunderstanding, not a typo.

A student who declared the private route's default route *inline* in `aws_route_table` rather than as a separate `aws_route` will find `enable_nat_gateway = false` breaks their LocalStack path. That is a design weakness, not a spec violation — no deduction if LocalStack still passes, but mention it in feedback.

Accept a domain that was **created** rather than **replaced**. Students who correctly destroyed Lab 1 after submission will see a create; students who left Lab 1 running will see a forced replacement. Both are correct.

### All 3 IAM roles with correct trust and policies (8 pts)

**Pass criteria:**

- [ ] `MLEngineer` — trust `sagemaker.amazonaws.com` (unchanged from Lab 1)
- [ ] `DataEngineer` — trust `glue.amazonaws.com`, `lambda.amazonaws.com`, **and `sagemaker.amazonaws.com`**
- [ ] `ModelMonitor` — trust `sagemaker.amazonaws.com`
- [ ] DataEngineer can read/write `raw/`, `processed/`, `features/`
- [ ] DataEngineer can **read** `artifacts/glue/` but **cannot write** `artifacts/`
- [ ] ModelMonitor can read `artifacts/` and write CloudWatch, but cannot write S3 at all

**Verification:** `verify-lab2.sh` runs `iam:SimulatePrincipalPolicy` for the boundary cases. Expected results:

| Principal | Action | Resource | Expect |
|---|---|---|---|
| DataEngineer | `s3:PutObject` | `artifacts/models/*` | `implicitDeny` |
| DataEngineer | `s3:GetObject` | `artifacts/glue/*` | `allowed` |
| DataEngineer | `s3:PutObject` | `features/*` | `allowed` |
| DataEngineer | `sagemaker:CreateTrainingJob` | `*` | `implicitDeny` |
| ModelMonitor | `s3:PutObject` | any | `implicitDeny` |
| ModelMonitor | `sagemaker:InvokeEndpoint` | `*` | `implicitDeny` |

**Grading notes:**

The `artifacts/` boundary is the interesting one and students get it wrong in both directions. A blanket deny on `artifacts/` means every Glue job fails at script fetch — if their jobs ran successfully, they did not do this. Granting full write on `artifacts/` breaks the least-privilege boundary — deduct 3.

Missing `sagemaker.amazonaws.com` in DataEngineer's trust means Task 3 could not have completed; if Task 3 works, this is present.

Do **not** deduct for the extra permissions Glue genuinely requires (`glue:GetConnection`, `ec2:CreateTags` on network interfaces, `s3:GetBucketAcl`). Those are necessary, not scope creep — see the troubleshooting appendix.

### S3 lifecycle rules (4 pts)

**Pass criteria:** `aws s3api get-bucket-lifecycle-configuration` returns exactly **5** rules:

| Rule ID | Prefix | Action |
|---|---|---|
| `expire-raw-data` | `raw/` | expire current after 90 days |
| `expire-raw-versions` | `raw/` | expire noncurrent after 30 days |
| `expire-processed-versions` | `processed/` | expire noncurrent after 30 days |
| `expire-feature-versions` | `features/` | expire noncurrent after 60 days |
| `expire-datacapture` | `datacapture/` | expire current after 7 days |

**Grading notes:** The 4 pts are for the rule set, not one point per rule. `expire-datacapture` is the one students most often miss — the lab text said "4 rules" before 2026-08-01, so **do not deduct from submissions graded against the older text**; note it in feedback instead. It matters: `datacapture/` is the only prefix in the platform that grows without bound, and Lab 5/6 fill it. A single blanket rule with no prefix filter earns 1/4 — it would expire `artifacts/` too, deleting trained models.

### LocalStack validation (3 pts)

**Pass criteria:** `docs/lab2-localstack-output.txt` shows 3 IAM roles, both subnets, and **no** NAT Gateway (guard variables set false in `environments/local/`).

**Grading notes:** Reference run applied 26 resources locally. If their output shows a NAT Gateway, they did not set `enable_nat_gateway = false` — deduct 1. If the file is missing entirely, 0/3.

---

## Task 2 — Data Ingestion Pipeline (25 pts)

### Catalog database and crawler-registered table (6 pts)

**Pass criteria:**

- [ ] `aws_glue_catalog_database` named `northstar_dev` (underscores — Glue rejects hyphens in database names)
- [ ] `aws_glue_crawler` targeting `s3://<bucket>/raw/customers/`, role = DataEngineer ARN
- [ ] Crawler run completed with `LastCrawl.Status: SUCCEEDED`
- [ ] `aws glue get-table` returns a table with all 9 columns

**Grading notes:** The crawler names the table after the S3 prefix, so it is **`customers`**. As of 2026-08-01 the lab text says `customers` throughout and `var.raw_table_name` defaults to `customers`, so this is now the expected answer rather than a tolerated deviation. Older submissions that used `raw_customers` (via a `TablePrefix` override) are still correct — accept either and do not deduct for the name.

### Transform script correctness (12 pts)

This is the largest single block of points in the task. Grade against the actual Parquet output, not the source code.

**Pass criteria** (`verify-lab2.sh` asserts all of these):

- [ ] 0 null `customer_id` in `processed/customers/`
- [ ] 0 duplicate `transaction_id`
- [ ] 0 null `purchase_date` — both date formats parsed
- [ ] 0 null `order_value` (median imputed)
- [ ] No leading/trailing whitespace in `customer_id`
- [ ] **Transaction-level grain preserved**: row count substantially exceeds distinct customer count

**Point allocation:**

| Behaviour | Pts |
|---|---|
| `cast_types` — types correct, both date formats parsed, null `customer_id` dropped | 4 |
| `impute_nulls` — median for numerics, `'unknown'` for strings | 4 |
| `deduplicate` — on `transaction_id`, deterministic tie-break | 4 |

**Grading notes — read this one carefully:**

**Deduplicating on `customer_id` is the defining failure of this lab.** The output will have ~1,967 rows instead of ~9,800. It looks clean, it passes a casual eyeball check, and it makes Task 3 mathematically impossible — `total_lifetime_value` and `purchase_frequency_30d` cannot be computed from one row per customer. If you see this, award **0/4** for `deduplicate` and check whether they then faked Task 3's aggregates. Leave explicit feedback: the grain is the contract.

Mean instead of median imputation: deduct 1 of the 4 impute points. It is defensible but wrong for right-skewed monetary data, and the lab says median.

Parsing only ISO 8601 dates: `to_date` returns null rather than raising, so ~3% of rows silently become null and are then dropped or carried as nulls. If `purchase_date` has nulls, deduct 2.

Forgetting to trim whitespace: ~1% of `customer_id` values keep padding and become distinct customers in Task 3. Their customer count will be ~1,990 instead of 1,967. Deduct 1 and point at the specific cause.

### `modules/glue/` applied cleanly (4 pts)

**Pass criteria:** module exists with catalog DB, crawler, job, and the `aws_s3_object` script upload; `terraform apply` reports 0 errors.

**Grading notes:** Award full credit if the script is uploaded by Terraform rather than by hand. A student who manually `aws s3 cp`'d the script and hardcoded the S3 path has broken reproducibility — deduct 2.

### Transform job SUCCEEDED (3 pts)

`aws glue get-job-run` returns `JobRunState: SUCCEEDED`. Reference execution time: ~111 seconds on 2× G.1X.

All-or-nothing. A `FAILED` final run is 0/3 even if an earlier run succeeded — check `JobRuns[0]`, the most recent.

---

## Task 3 — Feature Engineering (20 pts)

### Four feature functions (12 pts)

| Function | Pts | Check |
|---|---|---|
| `compute_rfm_features` | 4 | recency, 30-day frequency, average order value all non-null and plausible |
| `compute_ltv` | 2 | `total_lifetime_value` equals sum of that customer's `order_value` |
| `assign_loyalty_tier` | 3 | all four tiers present; boundaries at 500 / 2000 / 5000 |
| `compute_churn_proxy` | 3 | all values within [0, 1]; more than 3 distinct values |

**Grading notes:**

A degenerate tier distribution (one or two tiers only) means either the thresholds are wrong or the LTV aggregation is. Reference distribution is 995 / 554 / 299 / 119.

`churn_risk_score` with exactly three distinct values (0.85, 0.55, 0.2 or similar) means the student emitted band constants instead of scaling within the band. The lab explicitly asks for a spread. Deduct 1 of 3 — the logic is right, the modelling instinct is not.

Any `churn_risk_score` outside [0, 1] is an automatic 0 for that function; the lab states the range and the reference implementation clamps defensively.

**Time-anchoring:** the reference computes all windows relative to `max(purchase_date)`, not `today()`. A student using `current_date()` will produce different values on every run and their numbers will not match the reference. This is worth flagging in feedback but only deduct 1 — it is a reproducibility issue, and the lab text now warns about it explicitly.

### Feature Group via Terraform with 8 definitions (5 pts)

**Pass criteria:**

- [ ] `aws_sagemaker_feature_group` in a `modules/feature_store/` module
- [ ] All 8 feature definitions present
- [ ] `event_time` type is **`Fractional`**
- [ ] Online store enabled
- [ ] Offline store S3 URI under the data bucket, on a prefix separate from `features/customers/`

**Grading notes:** `event_time` declared as `String` is the trap this lab is built around. `PutRecord` returns success and the record never appears. If their `GetRecord` returns empty, this is almost always why. Deduct 2 of 5 and explain the failure mode — it is the single most valuable thing they will learn here.

Pointing the offline store at `features/` directly (rather than `features/offline-store/`) works but interleaves Feature Store's managed directory tree with the job's own Parquet. Deduct 1, note it.

### Feature engineering job SUCCEEDED (3 pts)

`aws glue get-job-run` returns `SUCCEEDED`. Reference: ~112 seconds.

**Additional check worth running manually:** a `GetRecord` round trip proves records actually landed.

```bash
aws sagemaker-featurestore-runtime get-record \
  --feature-group-name northstar-dev-customer-features \
  --record-identifier-value-as-string CUST-10000776
```

An empty `Record` with a SUCCEEDED job means the `event_time` type is wrong. The job cannot detect this — `PutRecord` reports success either way.

---

## Task 4 — Data Contract and Lineage (15 pts)

### Data contract (8 pts)

**Required sections:** schema, quality guarantees, SLA, versioning/breaking-change policy. At least 3 specific, measurable quality guarantees.

| Element | Pts |
|---|---|
| Complete schema with types and nullability | 2 |
| ≥3 measurable quality guarantees | 3 |
| SLAs stated as numbers, not adjectives | 2 |
| Versioning / breaking-change protocol | 1 |

**Grading notes:**

"Data should be fresh" is not an SLA. "Available within 2 hours of landing in `raw/`" is. Guarantees must be checkable: "`customer_id` is never null" passes; "data is high quality" does not.

**Award a bonus-quality note (not points) if the contract states the grain explicitly.** The reference contract leads with it, because a consumer assuming one row per customer produces silently wrong aggregates rather than an error. Students who identify this have understood the lab.

Cap at 4/8 if the document is a schema dump with no guarantees or SLAs — that is documentation, not a contract.

### Lineage diagram (7 pts)

**Pass criteria:**

- [ ] All nodes: source → `raw/` → crawler → catalog → transform job → `processed/` → feature job → `features/` + Feature Store
- [ ] Data format labelled on every edge (CSV, Parquet, `PutRecord`)
- [ ] IAM role labelled on every **write** edge

**Grading notes:** The IAM-role-on-write-edges requirement is what makes this a lineage diagram rather than a flowchart. Missing roles entirely: cap at 4/7. Missing formats: deduct 2. A diagram that omits the Feature Store offline store is incomplete but minor — deduct 1.

Accept any tool. The reference generates it from a committed Python script so it can be regenerated as the pipeline changes; hand-drawn is equally acceptable if accurate.

---

## Task 5 — Repository Quality (15 pts)

| Item | Pts | Check |
|---|---|---|
| `modules/glue/` and `modules/feature_store/` present, resources in the right modules | 4 | No cross-module duplication; Feature Store not defined inside the glue module |
| New resources parameterized | 3 | No hardcoded `"northstar"` or account IDs in `.tf` **values** |
| `terraform fmt` and `validate` pass | 3 | Clean output from both |
| `docs/lab2-extend-output.txt` ends with `Apply complete!` and mentions `aws_sagemaker_domain` | 3 | Either creation or replacement is acceptable |
| README describes Lab 2 additions and how to run the pipeline | 2 | Must include the end-to-end run sequence |

**Grading notes:** Terraform *resource labels* like `resource "aws_s3_bucket" "northstar"` are local identifiers, not hardcoded names — do not deduct for those. Deduct only when a hardcoded literal appears in a `name`, `bucket`, or ARN value.

---

## Teardown Gate (not points — a hold on Task 1)

**Required evidence:** `docs/lab2-destroy-output.txt` ending with `Destroy complete!`, plus the teardown script's verification output showing no billable resources.

If this evidence is missing, **cap Task 1 at 12/25 until the student produces it.** The NAT Gateway bills ~$32/month idle and students are on finite Free Tier credits.

**Be lenient about *how* they tore down.** `terraform destroy` alone does not fully clean up this lab — see the appendix. A student who destroyed successfully but left lineage contexts behind has done everything the lab asked. What matters is that NAT, the Domain, and EFS are gone.

**Check specifically for the EFS filesystem.** It is the one orphan that keeps billing, and `terraform destroy` never removes it. If a student's account still has one, tell them immediately — this is a real cost issue, not a grading one.

---

## Appendix: The Ten Failures Students Will Hit

Every one of these was encountered building the reference implementation. None are caught by `terraform validate` or LocalStack. Expect support questions on all of them; the error messages are mostly misleading.

| # | Error | Actual cause |
|---|---|---|
| 1 | `InvalidParameterValue: Character sets beyond ASCII are not supported` | An em dash or curly quote in a security group `description`. EC2 rejects non-ASCII; IAM accepts it, so the failure looks arbitrary |
| 2 | `DataCatalog Connection issue ... glue:GetConnection` | Role missing `glue:GetConnection`. Glue resolves the VPC connection before the script runs — not a script bug |
| 3 | `At least one security group must open all ingress ports` | Glue requires a **self-referencing** all-ports ingress rule. An identical rule written as the VPC CIDR does not satisfy the check |
| 4 | `The specified role doesn't have a permission to create a tag for your elastic network interface` | Missing `ec2:CreateTags`/`DeleteTags` on `network-interface/*` |
| 5 | `ValidationException: The execution role ARN is invalid` | The ARN is fine. DataEngineer's trust policy is missing `sagemaker.amazonaws.com` |
| 6 | `ValidationException: Invalid S3Uri provided` | The URI is fine. Role is missing `s3:GetBucketAcl` (and `s3:PutObjectAcl` on `features/*`) |
| 7 | Job SUCCEEDED but `GetRecord` returns empty | `event_time` declared `String` instead of `Fractional`. Silent — `PutRecord` reports success |
| 8 | `terraform destroy` hangs 10+ minutes then fails | Orphaned Glue ENIs, the SageMaker EFS mount target, and two auto-created NFS security groups |
| 9 | `BucketNotEmpty` on destroy | Versioned bucket; needs `force_destroy` or manual version purge |
| 10 | Old error persists after fixing a policy | IAM propagation lag. Wait ~30 seconds before concluding the fix failed |

**A note on #1 and IAM propagation:** students will re-run immediately after a fix, see the same error, and assume their fix was wrong. Tell them to wait 30 seconds. This wastes more student time than any other item on this list.

---

## Automated Grading Workflow

```bash
# 1. Clone student repo
git clone <student-repo> && cd <student-repo>

# 2. Static checks (no AWS credentials needed)
terraform -chdir=infrastructure/environments/dev fmt -check -recursive
terraform -chdir=infrastructure/environments/dev validate
ls docs/lab2-data-contract.md docs/lab2-data-lineage.png docs/lab2-extend-output.txt

# 3. Check git history for secrets
git log --all -S "AKIA" --oneline
git log --all --name-only | grep -E "terraform\.tfvars$|\.tfstate$"

# 4. Grain check without AWS - read their deduplicate()
grep -A6 "def deduplicate" data/glue-scripts/transform.py   # must partition by transaction_id

# 5. Full verification (requires the student's stack to still be deployed)
AWS_DEFAULT_REGION=us-east-1 bash scripts/verify-lab2.sh

# 6. Manual review
# - docs/lab2-data-contract.md      : guarantees measurable? SLAs numeric? grain stated?
# - docs/lab2-data-lineage.png      : IAM roles on write edges?
# - docs/lab2-destroy-output.txt    : ends with "Destroy complete!"?
```

**If the student has already torn down** (which the lab requires), `verify-lab2.sh` will fail most AWS checks. That is expected and correct. Grade Tasks 1–3 from their submitted `docs/lab2-extend-output.txt`, the Glue job run evidence, and their code. Do not penalise a student for having followed the teardown instruction.

---

## Grading Summary Sheet

| Task | Max Pts | Automated? | Notes |
|------|---------|-----------|-------|
| 1 — Private subnet, NAT, Domain move | 10 | Yes | `verify-lab2.sh` |
| 1 — 3 IAM roles + boundaries | 8 | Yes | `SimulatePrincipalPolicy` |
| 1 — S3 lifecycle rules | 4 | Yes | 1 pt per rule |
| 1 — LocalStack validation | 3 | Partial | Read the output file |
| 2 — Catalog + crawled table | 6 | Yes | |
| 2 — Transform correctness | 12 | Yes | Parquet assertions; **check the grain** |
| 2 — `modules/glue/` clean | 4 | Partial | Manual module review |
| 2 — Transform job SUCCEEDED | 3 | Yes | All or nothing |
| 3 — Four feature functions | 12 | Yes | Tier spread + score range |
| 3 — Feature Group, 8 defs | 5 | Yes | **Check `event_time` type** |
| 3 — Feature job SUCCEEDED | 3 | Yes | All or nothing |
| 4 — Data contract | 8 | No | Manual read |
| 4 — Lineage diagram | 7 | No | Manual review |
| 5 — Repo quality | 15 | Partial | fmt/validate automated |
| **Total** | **100** | | Teardown gate can cap Task 1 |

---

## Score Deduction Reference

| Issue | Deduction |
|-------|-----------|
| **Deduplicates on `customer_id` instead of `transaction_id`** | **-4 (all dedup pts) + flag; check Task 3 for fabricated aggregates** |
| `event_time` declared `String` | -2 and explain the silent-failure mode |
| NAT Gateway placed in the private subnet | -4 (architecture error) |
| Domain left in the public subnet | -6 (core Task 1 deliverable) |
| Missing `VpcOnly` | -2 |
| DataEngineer granted write on `artifacts/` | -3 (breaks least privilege) |
| Blanket `artifacts/` deny (jobs could not have run) | -3 |
| Single blanket lifecycle rule | -3 |
| Mean instead of median imputation | -1 |
| Only ISO date format parsed | -2 |
| Whitespace not trimmed | -1 |
| `churn_risk_score` outside [0, 1] | -3 (that function's full value) |
| Band constants instead of a scaled score | -1 |
| Degenerate tier distribution | -3 |
| Glue script uploaded manually, path hardcoded | -2 |
| Contract with no measurable guarantees | cap at 4/8 |
| Lineage diagram missing IAM roles on writes | cap at 4/7 |
| `terraform validate` fails | -3 and grade code by reading |
| `terraform.tfstate` or `.tfvars` in git | -5 + security flag |
| AWS access key (`AKIA*`) in git history | -5 + security flag; notify Scott |
| No teardown evidence | Task 1 capped at 12/25 until produced |

---

## Security Escalation Protocol

If `git log --all -S "AKIA" --oneline` returns any results:

1. Note the commit hash
2. Award 0 for Task 5 parameterization and flag the security violation in Canvas comments
3. Email Scott immediately: scott@toborg.com — do not wait until grade review

If a student's AWS account still shows a running NAT Gateway or an orphaned EFS filesystem after the due date, notify them directly regardless of grading status. Those bill continuously against finite credits they need for Labs 3–7.
