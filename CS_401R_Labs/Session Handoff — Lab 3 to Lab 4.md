---
tags: [CS401R, handoff, lab-4]
created: 2026-07-29
purpose: Warm-start context for a fresh session beginning Lab 4 work
---

# Session Handoff — Lab 3 → Lab 4

> **⚠ Superseded 2026-08-01 (defect 41).** The Lab 3 reference metrics quoted in this note (AUC 0.747 / baseline 0.642 / lift +0.105 / P@10% 0.611 / R@10% 0.293) do **not** reproduce. The canonical figures are now **AUC 0.7276 / baseline 0.6298 / lift +0.0978 / P@10% 0.6944 / R@10% 0.3333** — `train_reference.py`, Athena path, measured end to end 2026-08-01, registry v2. See [[Session Handoff — Labs 2-5 End-to-End Run]]. This note is retained as a historical record; do not quote its metrics.

> **How to use this:** Reference this note as the first message in a new session before starting Lab 4. It captures what Labs 1–3 landed, what Lab 4 inherits, and the open threads — including one live external dependency.

---

## Source of Truth (read these first)

| What | Path |
|------|------|
| **Live reference implementation** (correct, authoritative) | `/Users/scott1/northstar-ai-platform` |
| Lab 4 spec | `CS 401R Labs.md` — Lab 4 section (**no standalone `Lab_4--*.md` exists yet**) |
| Lab 1–3 specs | `Lab_1--Platform Foundation.md`, `Lab_2--Data & Feature Engineering.md`, `Lab_3--Model Development.md` |
| Starter kits | `Starter Kits/Lab N/` |
| TA grading guides | `Sample Solutions/Lab Solution Notes/` |
| TA tooling | `TA Tools/` |

**Rules that have held:**
- The live repo is authoritative. Sample Solutions is a copy kept in sync with it.
- **Standalone `Lab_N--*.md` is authoritative over the master guide**, and the master guide gets synced to match. Labs 1–3 have standalone files; **Labs 4–7 live only in the master guide.**
- **Verify on AWS; do not trust "it should work."** This session found ~12 defects that `terraform validate` and LocalStack both missed.

---

## Where the Course Stands

| Lab | Spec | Starter kit | Verified on AWS | TA guide |
|---|---|---|---|---|
| 1 | ✅ | ✅ | ✅ | ✅ |
| 2 | ✅ | ✅ | ✅ (5 full runs) | ✅ |
| 3 | ✅ | ✅ all 4 files audited | ✅ Track A end to end | ✅ |
| **4** | ✅ audited | ✅ all 5 files audited | ❌ **never executed** | ❌ stale |
| 5–7 | ✅ audited | n/a (intentional) | ❌ | ❌ stale |

**AWS account `711457211658` is clean.** Verified across all 17 regions: 0 NAT, domains, endpoints, feature groups, Glue jobs, non-default VPCs. Only `northstar-tfstate-711457211658` (S3) and `northstar-tfstate-lock` (DynamoDB) retained — Lab 3+ needs them. MTD spend ≈ $0. A $10/month budget alarm notifies scott@toborg.com at 50/80/100%.

---

## What Lab 4 Inherits

### The data and model contract (verified end to end)

```
raw/customers/        19,548 dirty transaction rows, 1,200 customers
processed/customers/  transaction grain, cleaned Parquet
features/customers/   customer grain, 13 features + churn_label
features/offline-store/  Feature Store offline, queried via Athena
artifacts/            glue scripts, athena-results, model artifacts
```

**Temporal split** — the thing Lab 4's tests must not break:
```
|<---- observation window ---->|<--- 90d holdout --->|
2025-04-01              2026-04-01 (T)          2026-06-30
```
Features come from ≤ T; `churn_label` from the holdout. Roughly **21%** churn. About a third of churners are still buying right up to T, which is why the behavioural features exist.

### Reference Track A results (measured 2026-07-28)

| Metric | Value |
|---|---|
| AUC-ROC | 0.747 |
| Recency-only baseline AUC | 0.642 |
| **Lift** | **+0.105** |
| Precision@10% / Recall@10% | 0.611 / 0.293 |
| `scale_pos_weight` | 3.828 (derived, not hardcoded) |

Reference implementation: `models/churn/train_reference.py`. It writes `artifacts/evaluations/latest/evaluation_metrics.json` including **`baseline_auc_roc`** — the field Lab 4's CI quality gate reads.

### The Platinum finding (RETRACTED — see banner below)

> **⚠ Retracted 2026-08-06.** The banner at the top of this note covers the
> aggregate metrics only; this section was not covered and said the opposite of
> what is true. **The Platinum finding reversed.** At 1,200 customers Platinum
> was ~33 test rows with ~2 churners, and its AUC ranged 0.00–1.00 across 200
> splits — it read "worse than random" on only 34.9% of them. On the 10,000-
> customer dataset Platinum has n=307 and is the model's **best** slice at
> **0.8483**. The worst slice is **Silver** (n=1,139, **0.6935**), the largest
> tier. Canonical slice figures, reproduced independently three times, most
> recently on a full teardown-and-rebuild 2026-08-06:
>
> | Tier | n | AUC | Churn |
> |---|---|---|---|
> | Platinum | 307 | 0.8483 | 6.8% |
> | Gold | 483 | 0.7559 | 10.8% |
> | Bronze | 1,071 | 0.7442 | 33.7% |
> | **Silver** | 1,139 | **0.6935** | 19.8% |
>
> See [[Session Handoff — Labs Dataset Rebase & Gate Redesign]]. Lab 3 was
> rewritten around the spread across tiers plus the sample-size lesson; do not
> teach or grade the 0.430 claim.

Slice AUC: Bronze 0.809 · Gold 0.745 · Silver 0.688 · **Platinum 0.430** (worse than random, n=41, ~3 positives). Aggregate 0.747 hides it entirely. Lab 4's `test_fairness.py` requirement should surface this same class of problem.

---

## Lab 4 Status in Detail

### Spec — audited and corrected

Tasks: Test Suite (30) · CI/CD Pipeline (30) · MLOps Configuration (20) · XOps Maturity Assessment (20) = **100**.

Corrections made this session:
- Data-validation test list rewritten around the real three-dataset pipeline (raw/processed/features), including grain and leakage checks
- **Baseline gate added**: model must beat recency-only by ≥ 0.03 AUC, requiring `baseline_auc_roc` in the metrics file
- Starter-kit description corrected (it promised `tests/template/`; three populated suites actually ship)
- Added an explicit callout that a missing dataset must **fail, not skip**

### Starter kit — all 5 files audited and fixed

| File | State |
|---|---|
| `tests/test_data.py` | **Rewritten.** Was loading the retired 5-dataset corpus and calling `pytest.skip` on missing files — a green run that tested nothing. Now targets raw/processed/features, fails loudly, 26 tests. |
| `tests/test_features.py` | Phantom features and clickstream tests removed; cutoff aligned to 2026-04-01; fails rather than skips when the module is absent |
| `tests/test_model.py` | `FEATURE_COLUMNS` corrected to the real 11; synthetic fixtures rebuilt (fixed 2026-07-29 — they still carried phantom features after the first pass) |
| `buildspec.yml` | Three-bucket + SSM model replaced with the single derived bucket; thresholds corrected; **all four quality gates** now enforced including baseline lift; pre-build stages the datasets the tests need |
| `pipeline.yaml` | SSM parameter resolution removed (nothing creates those params); `PROJECT`/`ENVIRONMENT` passed to CodeBuild |

Also created `requirements.txt` / `requirements-dev.txt` in the live repo — the buildspec installed both and neither existed.

**Verified:** `test_data.py` scored 26/26 against real AWS pipeline output, and correctly produced 12 errors when the features directory was removed. Zero phantom features remain across all three suites.

### Not done

- **Nothing in Lab 4 has been executed on AWS.** No CodePipeline stack deployed, no CodeBuild run, no SageMaker Pipeline. The YAML is reviewed but unproven — and this session repeatedly showed the gap between "reviewed" and "works."
- **TA guide is stale** (`Lab 4 - XOps & CICD (Solution).md`, dated Jul 6, written against the old architecture). Needs the same treatment Labs 1–3 got.
- `test_features.py` assumes students extract Lab 2's PySpark logic into pandas-testable functions in `data/feature_engineering.py`. That refactor is the assignment, but **no reference implementation exists** — worth building alongside the TA guide.

---

## Open Threads

### Live external dependency — Bedrock (blocks Lab 3 Track B/C, not Lab 4)

- Anthropic FTU form: **submitted** via `PutUseCaseForModelAccess`
- Claude Haiku 4.5 agreement: **AVAILABLE** (created via API, took 60s)
- Titan entitlement: **AVAILABLE** (Amazon models need no agreement)
- **Blocker:** all on-demand inference quotas are **0**. Claude's cross-region quotas are adjustable (request filed by Scott); embedding quotas are **not adjustable** and need an AWS Support case.
- Key unknown for course design: **do all 30 student accounts need manual quota grants?** If yes, Track B/C are undeliverable as scheduled.
- Monitor with `TA Tools/bedrock_canary.py --watch`. It logs quota values every probe, so approval time is captured precisely.
- The Bedrock "Model access" console page was **retired 2025-10-08** — access is automatic now. `Pre-Lab 3 — Bedrock Access Setup.md` was rewritten against the current process.

### Course-structure items

- [ ] **Write `Lab_4--XOps & CICD.md`** as a standalone spec, then sync the master guide to it — matching how Labs 1–3 are structured
- [ ] **Lab 4 TA guide** rewrite (needs a real pipeline run first, ideally)
- [ ] **Execute Lab 4 on AWS** — deploy the CodePipeline stack, trigger a build, confirm the quality gates actually block a bad model
- [ ] **Lab 5–7 TA guides** — all still from the old architecture
- [ ] TA canary account — Scott's TA is setting one up; procedure in `TA Tools/TA Procedure — Bedrock Canary Test.md`
- [ ] `_retired/` folders exist in two places; decide keep or purge

---

## Traps Already Mapped — do not rediscover

Twelve AWS defects were found this session, none caught by `terraform validate` or LocalStack. Full lists live in the Lab 2 and Lab 3 TA guides. Most likely to recur in Lab 4:

1. **IAM propagation lag** — after a policy change, wait ~30s. Re-running immediately shows the *old* error and looks like the fix failed. This wasted the most time of anything.
2. **Non-ASCII in AWS-facing `description` fields** — EC2 rejects em dashes; IAM accepts them, so the failure looks arbitrary.
3. **`terraform destroy` does not fully tear down** — six orphan classes, one of which (SageMaker EFS) **keeps billing**. Always use `scripts/teardown-lab2.sh` / `teardown-lab3.sh`.
4. **Do not trust the console's Resource Explorer** to confirm teardown — its index lags hours. It listed four already-deleted resources while being the only thing that surfaced orphaned lineage contexts. Verify against the live API.
5. **Athena + offline store**: `event_time` is Fractional epoch (ISO strings raise `TYPE_MISMATCH`), and the store is append-only so you must dedup with `ROW_NUMBER() OVER (PARTITION BY customer_id ...)`. A global `MAX(write_time)` filter returned **29 of 1,200** customers.
6. **Test suites that skip on missing data are worse than none** — they go green having validated nothing.

---

## Working Conventions (carry forward)

- Terraform vars use `var.project` / `var.environment` (never `var.project_name`).
- No hardcoded `"northstar"` literals in module **values**; resource labels are fine.
- Guard variables (`enable_*`) for anything LocalStack cannot do, defaulting true. `enable_sagemaker_domain=false` + `enable_nat_gateway=false` + `enable_glue_vpc_connection=false` gives a ~$0.05, 15-minute pipeline-only test path that avoids every known orphan.
- Every AWS-facing `description` is ASCII only.
- Verify against the live AWS API, never the console index.
- Tear down after every AWS session and confirm with an independent sweep.
- Blunt, direct communication; challenge bad calls; one recommendation not ten options (per vault CLAUDE.md).

---

## Suggested First Moves for the Lab 4 Session

1. **Write `Lab_4--XOps & CICD.md`** from the master-guide section, then sync back — gives Lab 4 the same authoritative-standalone structure as Labs 1–3.
2. **Build the reference `data/feature_engineering.py`** — the pandas extraction `test_features.py` expects. Cheap, offline, and unblocks that suite.
3. **Execute Lab 4 on AWS**: deploy `pipeline.yaml`, run a build, and verify the quality gate *actually blocks* a model that fails the baseline lift. That last check is the whole point of the lab and has never been exercised.
4. **Then** write the Lab 4 TA guide against real results, the way Lab 3's was written.
