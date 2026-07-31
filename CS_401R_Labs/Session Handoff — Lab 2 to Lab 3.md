---
tags: [CS401R, handoff, lab-3]
created: 2026-07-27
purpose: Warm-start context for a fresh session beginning Lab 3 work
---

# Session Handoff — Lab 2 → Lab 3

> **How to use this:** Reference this note as the first message in a new session before starting Lab 3. It captures what Lab 2 landed, the architecture Lab 3 inherits, the traps already mapped, and the open threads.

---

## Source of Truth (read these first)

| What | Path |
|------|------|
| **Live reference implementation** (correct, authoritative) | `/Users/scott1/northstar-ai-platform` |
| Lab 3 spec | `Efforts/.../CS_401R_Labs/Lab_3--Model Development.md` (written 2026-07-28; master guide synced to it) |
| Sample Solutions repo (TA answer key) | `Efforts/.../CS_401R_Labs/Sample Solutions/northstar-ai-platform/` |
| TA grading guides | `Efforts/.../CS_401R_Labs/Sample Solutions/Lab Solution Notes/` |

**Rules that held through Labs 1 and 2:**
- The live repo is authoritative. When Sample Solutions and live disagree, live wins.
- **Standalone `Lab_N--*.md` is authoritative over the master guide**, and the master guide gets synced to match. This was established in Lab 2 after the master guide's Lab 1 *and* Lab 2 sections were found badly stale.
- **Lab 3 has no standalone spec yet.** Writing `Lab_3--Model Development.md` from the master guide section — and then re-syncing the guide to it — is the first task, mirroring how Lab 2 began.

---

## What Lab 2 Landed (done, verified on real AWS)

All 100 points build, run, and verify against account `711457211658`.

| Task | Pts | Evidence |
|---|---|---|
| 1 — Private subnet, NAT, 3 IAM roles, lifecycle, Domain → private/VpcOnly | 25 | Domain InService, 11/11 IAM boundary assertions |
| 2 — Glue catalog, crawler, transform ETL | 25 | Crawler + job SUCCEEDED; 10,150 → 9,800 rows, 0 nulls, 0 dups |
| 3 — Feature Store + feature engineering | 20 | Job SUCCEEDED; 1,967 customers; `GetRecord` 3/3 exact match |
| 4 — Data contract + lineage diagram | 15 | `docs/lab2-data-contract.md`, `docs/lab2-data-lineage.png` |
| 5 — Repo quality, README, verify script | 15 | `fmt`/`validate` clean |

Also delivered: `scripts/verify-lab2.sh`, `scripts/teardown-lab2.sh`, student starter kit (stubbed scripts + sample CSV + verify script), and a full TA grading guide.

**Infrastructure is destroyed.** Verified zero billable resources across all 17 regions. Retained deliberately: `northstar-tfstate-711457211658` (S3) and `northstar-tfstate-lock` (DynamoDB) — Lab 3 needs both. Month-to-date spend $0.

---

## Architecture Lab 3 Inherits

```
VPC 10.0.0.0/16
├── public  10.0.100.0/24  → IGW, NAT Gateway anchor
└── private 10.0.1.0/24    → SageMaker Domain (VpcOnly), Glue workers
S3 northstar-dev-data-{account}
├── raw/customers/          CSV, transaction grain
├── processed/customers/    Parquet, transaction grain (9,800 rows)
├── features/customers/     Parquet, customer grain (1,967 rows)
├── features/offline-store/ Feature Store offline
└── artifacts/glue/         job scripts (DataEngineer: read-only)
IAM: MLEngineer | DataEngineer | ModelMonitor
Glue: northstar_dev catalog, raw-crawler, transform, feature-engineer
Feature Store: northstar-dev-customer-features (8 features, event_time Fractional)
```

**Rebuild is one command:** `terraform apply` in `infrastructure/environments/dev` (~15 min, mostly the SageMaker Domain). Then re-run the pipeline per the README.

### What Lab 3 adds

Training on those features. Key interfaces Lab 3 will consume:

- **MLEngineer role** — already scoped to read `features/` and write `artifacts/`. Training jobs should assume it. It does **not** currently have Feature Store read permissions — check whether Lab 3 needs `sagemaker:GetRecord` / Athena access to the offline store and add it.
- **Offline store** at `features/offline-store/`, with a Glue table auto-registered in the `sagemaker_featurestore` database. That is the Athena query path for building training sets.
- **`churn_risk_score`** is a rule-based proxy, not a label. Lab 3 replaces it with a trained model. The starter `churn_training_skeleton.py` in `Starter Kits/Lab 3/` already assumes a Feature Store Athena query.

---

## Traps Already Mapped (do not rediscover these)

Ten AWS failures were found building Lab 2, none caught by `terraform validate` or LocalStack. Full table is in the Lab 2 TA guide appendix. The ones most likely to recur in Lab 3:

1. **IAM propagation lag** — after a policy change, wait ~30s. Re-running immediately shows the *old* error and looks like the fix failed. This wasted the most time of anything.
2. **Non-ASCII in AWS-facing `description` fields** — EC2 rejects em dashes; IAM accepts them. Use plain hyphens everywhere.
3. **`event_time` must be `Fractional`** — a `String` declaration makes `PutRecord` succeed while the record never lands. Silent.
4. **Misleading Feature Store errors** — "execution role ARN is invalid" means the trust policy is wrong; "Invalid S3Uri provided" means `s3:GetBucketAcl` is missing.
5. **`terraform destroy` does not fully tear down** — six orphan classes, one of which (SageMaker EFS) **keeps billing**. Always use `scripts/teardown-lab2.sh`, and expect Lab 3 to need its own equivalent.
6. **Do not trust the console's Resource Explorer** to confirm teardown. Its index lags by minutes to hours; it listed four already-deleted resources while being the only thing that surfaced orphaned lineage contexts. Verify against the live API.

---

## Open Threads / Watch Items

- [x] ~~Write `Lab_3--Model Development.md`~~ — done 2026-07-28, master guide synced, rubrics total 100.
- [ ] **Audit the master guide's Labs 4–7 sections** for the same drift. Both audited sections so far were badly stale (Lab 1's still described NAT Gateways and 3 IAM roles; Lab 2's was an entirely different 4-task lab).
- [ ] **MLEngineer still needs Feature Store / Athena read permissions** — Lab 3 Task 1 queries the offline store via Athena. The role currently has S3 read on `features/` but no `athena:*`, `glue:GetTable` on the `sagemaker_featurestore` database, or Athena results-bucket write. **This will fail on the first training run and is the top open item.**
- [x] ~~Lab 3 teardown script~~ — `scripts/teardown-lab3.sh` written and verified 2026-07-28: deletes endpoints and endpoint configs, stops in-flight training/processing/transform jobs, then verifies. Teardown gate is in `Lab_3--Model Development.md`.
- [x] ~~`northstar-policy-docs/` missing~~ — written 2026-07-28: return policy, loyalty terms, shipping policy, customer FAQ (~3,700 words). Contains deliberate hard limits (final sale, expired offers, the $500 affidavit) that Track C's adversarial scenario tests against.
- [x] ~~`Starter Kits/Lab 3/` assumes the old data model~~ — resolved 2026-07-28. `FEATURE_COLUMNS` now matches the feature group exactly (verified programmatically), `scale_pos_weight` corrected to 3.8 for the measured 20.8% churn rate, Athena query rewritten for Fractional `event_time` and per-customer dedup, thresholds aligned to the spec.
- [x] ~~Lab 2's synthetic data has no real churn label~~ — resolved 2026-07-28 via a temporal split. Generator simulates two churn populations (lapsed + imminent); `feature_engineer.py` computes 13 features from the observation window and derives `churn_label` from the holdout. Verified on AWS: full model AUC 0.730 vs recency-only 0.650, lift +0.080.
- [ ] `_retired/` folders now exist in two places (`CS_401R_Labs/_retired/`, `Sample Solutions/northstar-ai-platform/_retired-old-lab2-architecture/`). Decide whether to keep or purge.

---

## Working Conventions (carry forward)

- Terraform vars use `var.project` / `var.environment` (never `var.project_name`).
- No hardcoded `"northstar"` literals in module **values**; resource labels are fine.
- Guard variables (`enable_*`) for anything LocalStack cannot do, defaulting true.
- Every AWS-facing `description` is ASCII only.
- Sample Solutions is kept in sync with live; live is authoritative.
- Verify against the live AWS API, never the console index.
- Blunt, direct communication; challenge bad calls; one recommendation not ten options (per vault CLAUDE.md).
