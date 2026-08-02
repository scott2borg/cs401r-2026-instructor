---
created: 2026-07-30
tags: [CS401R, handoff, lab-5]
purpose: Warm-start context for a fresh session beginning Lab 5 work
---

# Session Handoff — Lab 4 → Lab 5

> **⚠ Superseded 2026-08-01 (defect 41).** The Lab 3 reference metrics quoted in this note (AUC 0.747 / baseline 0.642 / lift +0.105 / P@10% 0.611 / R@10% 0.293) do **not** reproduce. The canonical figures are now **AUC 0.7276 / baseline 0.6298 / lift +0.0978 / P@10% 0.6944 / R@10% 0.3333** — `train_reference.py`, Athena path, measured end to end 2026-08-01, registry v2. See [[Session Handoff — Labs 2-5 End-to-End Run]]. This note is retained as a historical record; do not quote its metrics.

> **How to use this:** Reference this note as the first message in a new session before starting Lab 5. It captures what Labs 1–4 landed, what Lab 5 inherits, and the open threads — including two live external dependencies.

---

## Source of Truth (read these first)

| What | Path |
|------|------|
| **Live reference implementation** (correct, authoritative) | `/Users/scott1/northstar-ai-platform` |
| Lab 5 spec | `CS 401R Labs.md` — Lab 5 section (**no standalone `Lab_5--*.md` yet**) |
| Lab 1–4 specs | `Lab_1--Platform Foundation.md` … `Lab_4--XOps & CICD.md` |
| Starter kits | `Starter Kits/Lab N/` (Labs 5–7 intentionally have none) |
| TA grading guides | `Sample Solutions/Lab Solution Notes/` |
| TA tooling | `TA Tools/` |

**Rules that have held:**
- The live repo is authoritative; Sample Solutions is a copy kept in sync.
- **Standalone `Lab_N--*.md` is authoritative over the master guide**, which gets synced to match. Labs 1–4 have standalone files; **Labs 5–7 live only in the master guide.**
- **Verify on AWS. "It should work" has been wrong ~14 times this project.**

---

## Where the Course Stands

| Lab | Spec | Starter kit | Verified on AWS | TA guide |
|---|---|---|---|---|
| 1 | ✅ | ✅ | ✅ | ✅ |
| 2 | ✅ | ✅ | ✅ (6 full runs) | ✅ |
| 3 | ✅ | ✅ | ✅ Track A end to end | ✅ |
| 4 | ✅ | ✅ | ✅ CodeBuild path | ✅ |
| **5** | ✅ audited | n/a | ❌ | ❌ **stale** |
| 6–7 | ✅ audited | n/a | ❌ | ❌ **stale** |

**AWS account `711457211658` is clean.** All 17 regions: 0 NAT, domains, endpoints, feature groups, Glue jobs, CodeBuild projects, CFN stacks, non-default VPCs, northstar IAM roles. Retained: `northstar-tfstate-711457211658` (S3) + `northstar-tfstate-lock` (DynamoDB). MTD spend ≈ $0. Budget alarm at $10/mo → scott@toborg.com.

---

## What Lab 5 Inherits

Lab 5 deploys the Lab 3 churn model to production with a controlled rollout, then documents security and privacy posture.

Tasks: Production Deployment (30) · Operational Deployment Plan (20) · Security Assessment (25: STRIDE 15 + Data Classification 10) · Privacy & Compliance (15) · Repository Quality (10) = **100**.

### Concrete artifacts available

| Artifact | Detail |
|---|---|
| Model Registry group | `northstar-churn-models`, version 1 `PendingManualApproval` (deleted after the reference run — recreate by running `models/churn/train_reference.py`) |
| Reference metrics | AUC 0.747 · baseline 0.642 · lift +0.105 · precision@10 0.611 · recall@10 0.293 |
| Model artifact | `artifacts/models/churn/<ts>/model.tar.gz`, XGBoost |
| Quality gate | `buildspec.yml` enforces AUC / precision / recall / **lift ≥ 0.03**; verified to fail a build |
| IAM roles | `MLEngineer` (SageMaker + Athena + features/artifacts), `DataEngineer` (Glue + data prefixes), `ModelMonitor` (CloudWatch + read-only artifacts) |

**`ModelMonitor` already exists from Lab 2** with monitoring-schedule and CloudWatch permissions. Lab 6 needs it; Lab 5's security assessment should reference it as an existing least-privilege boundary.

### Cost warning specific to Lab 5

**Lab 5 is the first lab that creates a persistent SageMaker endpoint.** Endpoints bill hourly until deleted — the Lab 3 equivalent of Lab 2's NAT Gateway.

`scripts/teardown-lab3.sh` already deletes endpoints, endpoint configs, and in-flight jobs, and verifies. Lab 5 should reuse it or ship its own. The spec already requires endpoint deletion with before/after screenshots and a **10-point deduction** for leaving one running — that discipline was written before this project's teardown work and is good as-is.

---

## What Lab 4 Landed (this session)

1. **`Lab_4--XOps & CICD.md`** extracted as a standalone spec; master guide synced and verified identical.
2. **`data/feature_engineering.py`** — pandas reference, verified *equivalent to the PySpark Glue job* on identical input (1,200 customers, tiers 417/456/216/111 exact match). `test_features.py` 18/18.
3. **CodeBuild integration verified on AWS** using an S3 source (no GitHub needed):
   ```
   INSTALL    SUCCEEDED  232s
   PRE_BUILD  SUCCEEDED   14s   test_data 26 passed · test_features 18 passed
   BUILD      SUCCEEDED    1s   gate 4/4 PASS
   ```
4. **Gate proven to block.** A model at AUC 0.800 — better than the reference — **failed the build** for only +0.005 lift over the recency baseline. This is Lab 4's central claim, now demonstrated.
5. **Lab 4 TA guide rewritten** against real output; 13 rubric items summing to 100.

### Two defects fixed that would have blocked every student

- **Colon-in-echo YAML trap.** `echo "=== BUILD PHASE: Package & Deploy ==="` parses as a *dict*, and CodeBuild rejects the entire file with `YAML_FILE_ERROR` before running anything. Two such commands shipped in `buildspec.yml`. Fixed; all 42 commands now parse as strings.
- **`terraform apply` fails on first attempt after teardown** — `aws_s3_object` refresh can't find an object the destroy removed. Re-running succeeds. Reproducible; documented; students hit it every cycle.

---

## Open Threads

### Live external dependency — Bedrock (blocks Lab 3 Track B/C only)

- Anthropic FTU form **submitted**; Claude Haiku agreement **AVAILABLE**; Titan entitlement **AVAILABLE**
- **Both quotas still 0.** Claude's cross-region quotas are adjustable (Scott filed a request); embedding quotas are **not adjustable** and need an AWS Support case.
- **The question that decides Lab 3 Track B/C:** do all 30 student accounts need manual quota grants? If yes, those tracks are undeliverable as scheduled.
- Monitor: `TA Tools/bedrock_canary.py --watch`. The Bedrock "Model access" console page was **retired 2025-10-08**; access is automatic now, and `Pre-Lab 3 — Bedrock Access Setup.md` reflects the current API-based process.

### Lab 4 residual

- **CodePipeline orchestration never run.** No GitHub repo or CodeStar connection exists, so the Source stage, stage sequencing, and the SageMaker Pipeline trigger are unproven. `pipeline.yaml` validates against CloudFormation but has never been deployed. The Lab 4 TA guide states this explicitly and tells TAs to reproduce before blaming students.
- To close it: push the repo to GitHub, create a CodeStar connection, then deploy `pipeline.yaml`.

### Course-structure backlog

- [ ] **Lab 5–7 TA guides** — all three still written against the retired architecture. Largest remaining block of stale material.
- [ ] **Standalone `Lab_5--*.md` / `Lab_6--*.md` / `Lab_7--*.md`** to match Labs 1–4
- [ ] Nothing in Labs 5–7 has been executed on AWS
- [ ] TA canary account for Bedrock timing — procedure in `TA Tools/TA Procedure — Bedrock Canary Test.md`
- [ ] `_retired/` folders in two places; decide keep or purge

---

## Traps Already Mapped — do not rediscover

Fourteen AWS/tooling defects found across this project, none caught by `terraform validate` or LocalStack. Full lists live in the Lab 2/3/4 TA guides. Most relevant to Lab 5:

1. **IAM propagation lag** — after a policy change wait ~30s; re-running immediately shows the *old* error and looks like the fix failed.
2. **Non-ASCII in AWS-facing `description` / `Description` fields** — EC2 rejects em dashes, IAM accepts them, so failures look arbitrary. Found in the SG, IAM policies, and `pipeline.yaml`.
3. **`terraform destroy` does not fully tear down** — six orphan classes, one of which (SageMaker EFS) **keeps billing**. Always use the teardown scripts.
4. **Console Resource Explorer lags hours** — it listed four already-deleted resources while being the only thing that surfaced orphaned lineage contexts. Verify against the live API.
5. **Colon-in-echo breaks buildspec YAML** (see above).
6. **Endpoints bill hourly until deleted** — the Lab 5 cost trap.

---

## Working Conventions (carry forward)

- Terraform vars use `var.project` / `var.environment`.
- No hardcoded `"northstar"` literals in module **values**; resource labels are fine.
- Guard variables (`enable_*`) for anything LocalStack cannot do, defaulting true.
  **Fast test path:** `-var-file=/tmp/pipeline-only.tfvars` (`enable_sagemaker_domain=false`, `enable_nat_gateway=false`, `enable_glue_vpc_connection=false`) gives a ~$0.05, 15-minute stack that avoids every known orphan.
- Every AWS-facing description is ASCII only.
- Verify against the live AWS API, never the console index.
- Tear down after every AWS session and confirm with an independent all-region sweep.
- Blunt, direct communication; challenge bad calls; one recommendation not ten options (per vault CLAUDE.md).

---

## Suggested First Moves for the Lab 5 Session

1. **Write `Lab_5--Deployment & Security.md`** from the master-guide section, then sync back — same structure as Labs 1–4. Audit it while extracting; every section audited so far has had drift.
2. **Rewrite the Lab 5 TA guide.** It predates the current architecture. Lab 5 is heavily written-deliverable (STRIDE, data classification, privacy) so much of it is gradable without an AWS run.
3. **Execute Lab 5's deployment path on AWS** — register a model via `train_reference.py`, deploy an endpoint with a canary/blue-green config, verify rollback triggers, then tear down. This is the first lab that creates hourly-billing resources, so verify the teardown story before students touch it.
4. Consider whether Lab 5 should reuse `scripts/teardown-lab3.sh` or ship `teardown-lab5.sh`.
