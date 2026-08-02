---
created: 2026-07-31
tags: [CS401R, handoff, lab-7]
supersedes: "Session Handoff — Lab 5 to Lab 6"
purpose: Warm-start context for a fresh session. Labs 5 and 6 are closed; Lab 7 is next.
---

# Session Handoff — Lab 6 → Lab 7

> **⚠ Superseded 2026-08-01 (defect 41).** The Lab 3 reference metrics quoted in this note (AUC 0.747 / baseline 0.642 / lift +0.105 / P@10% 0.611 / R@10% 0.293) do **not** reproduce. The canonical figures are now **AUC 0.7276 / baseline 0.6298 / lift +0.0978 / P@10% 0.6944 / R@10% 0.3333** — `train_reference.py`, Athena path, measured end to end 2026-08-01, registry v2. See [[Session Handoff — Labs 2-5 End-to-End Run]]. This note is retained as a historical record; do not quote its metrics.

> **Read this before starting Lab 7.** It supersedes [[Session Handoff — Lab 5 to Lab 6]], which contains at least one claim now known to be false (see *Corrections* below).

---

## Source of Truth

| What | Where |
|------|-------|
| **Live reference implementation** | `/Users/scott1/northstar-ai-platform` — branch `lab5-deployment-verification`, pushed to `github.com/scott2borg/northstar-ai-platform` (**private**) |
| Course content, solutions, TA guides | `github.com/scott2borg/cs401r-2026-instructor` (**private**) — this vault folder |
| Student-facing labs + starter kits | `github.com/scott2borg/cs401r-2026-labs` (**public**) — published only via `scripts/publish_student_repo.sh` |
| Course constraints | [[Efforts/Projects/Active/CS_401R_2026/CLAUDE.md]] — **read this first**, it holds the hard constraints |
| Cost model + blocker history | [[Lab 6 — Cost Model & Pre-Flight Blockers]] |

**Rules that still hold:**
- Standalone `Lab_N--*.md` is authoritative; the master guide is synced to match and verified byte-identical.
- **Verify on AWS.** `terraform validate` has now failed to catch a real defect roughly **20 times** on this project — most recently three of five CloudWatch alarms that were schema-perfect and semantically wrong.
- Tear down after every session and confirm with an independent all-region sweep.

---

## Where the course stands

| Lab | Spec | Verified on AWS | TA guide |
|---|---|---|---|
| 1 | ✅ | ✅ | ✅ |
| 2 | ✅ | ✅ | ✅ |
| 3 | ✅ | ✅ Track A | ✅ |
| 4 | ✅ | ✅ CodeBuild path only | ✅ |
| 5 | ✅ **redesigned + re-verified 2026-07-31** | ✅ **full path, capture + rollback** | ✅ **rewritten** |
| 6 | ✅ **rewritten around closed API** | ✅ **Tasks 1–5, answer keys written** | ✅ **rewritten** |
| **7** | ⚠️ audited only, **no standalone file** | ❌ | ❌ **stale** |

**Labs 5 and 6 are done.** Account `711457211658` is clean — verified across 8 regions. Total AWS spend for the whole of 2026-07-31: **under $0.20**.

---

## THE THING THAT CHANGES EVERYTHING

**Student AWS accounts are completely independent of BYU.** No institutional relationship, no account team, no bulk quota grants, no Organizations. Students get **AWS default quotas, full stop.**

Consequences already absorbed into Labs 5 and 6, and which Lab 7 must respect:

1. **Every on-demand SageMaker quota defaults to 0** — endpoint, training, and processing are three separate numbers per instance type. Only `ml.t2.medium`/`ml.m6g.*` (endpoint) and `ml.t3.{medium,large,xlarge}` (processing) have non-zero defaults.
2. **SageMaker Model Monitor *schedules* are closed to new accounts.** `CreateMonitoringSchedule` and `CreateDataQualityJobDefinition` both return *"maintenance mode... not available to new customers"*. No quota or permission fixes it.
3. The reference account is **not representative** — it has accrued elevated limits through use. Always check `get-aws-default-service-quota`, never `get-service-quota`, when reasoning about students.

**Design rule for Lab 7: it must complete inside AWS default quotas.** Lab 7 is mostly analysis and writing, so this should be easy — but verify any AWS call it requires.

---

## Corrections to the previous handoff

- **"Every training-job quota is 0" was WRONG.** On-demand training on the reference account is **15**. The error came from `aws service-quotas list-service-quotas --query`, which applies `--query` **per pagination page** and silently returns partial results. Use `get-service-quota` with an explicit quota code, or a boto3 paginator.
- **"Endpoint quota is 4"** — it is 8.
- **The Labs 2→5 end-to-end run is NOT quota-blocked** and could be executed today. It remains the largest unclosed integration seam.

---

## Defects found on 2026-07-31 (all fixed and verified)

Numbered from the project's running list, now at ~20.

| # | Defect | Impact |
|---|---|---|
| 18 | `ModelMonitor` IAM role cannot run a monitoring job — no S3 write, no ECR pull, by design | Task 1 impossible; fixed with a separate `ModelMonitorExecution` role |
| 19 | Lab 5 deployed endpoints with **no `DataCaptureConfig`** | Lab 6 had nothing to analyse; endpoint configs are immutable so it could not be patched later |
| 20 | **Data capture fails completely silently** without an endpoint-role S3 write | 41 invocations produced zero objects, no error anywhere |
| 21 | Model Monitor **schedules closed to new accounts** | Lab 6 Task 1 rewritten around manual analyzer runs |
| 22 | `ml.t3.medium` OOMs the analyzer after **13 min 43 s**, blaming the *data* | Cheapest instance with quota is the one that does not work |
| 23 | `publish_cloudwatch_metrics=Enabled` fails without a schedule | Model layer must be self-published |
| 24 | **CloudWatch silently discards backfilled metrics** — past-timestamped puts return HTTP 200 and are never queryable | 7-day-average rules cannot be demonstrated in a lab session |
| 25 | `CustomerMetadataProperties` rejects **parentheses and commas** | Same family as the em-dash trap |
| 26 | **Anomaly detectors survive `terraform destroy`** — a new orphan class | `teardown-lab6.sh` now removes them and the sweep checks independently |
| 27 | Recall@10% SLO of 0.35 was **above the ceiling** (~0.48) and above Lab 4's own gate | Reference model would have breached its SLO on launch day; corrected to 0.25 |

**CLI traps worth carrying forward:** percentiles need `--extended-statistics`, not `--statistics`. And **zsh does not word-split unquoted variables** the way bash does, so `--dimensions $D` arrives as one malformed argument. Both produce *empty results rather than errors*.

---

## What Lab 7 inherits

Lab 7 is *Metrics + Economics & Business Value* — 5 tasks, 100 points, mostly written analysis. It should be the cheapest lab in the course.

**Real numbers now available to build unit economics on:**

| Quantity | Measured |
|---|---|
| Endpoint `ml.t2.medium` | $0.056/hr |
| Endpoint `ml.m5.large` | $0.115/hr |
| Model Monitor analyzer run (`ml.t3.large`) | 5 min 46 s, **$0.010** per run |
| Full Lab 5 canary + rollback session | ~$0.12 |
| Model AUC / recency baseline | 0.747 / 0.642 |
| Recall@10% (ceiling ~0.48 at 21% base rate) | 0.293 |
| Churn base rate | 21.2% |
| Inference latency p95 | ~4.1 ms |

That is enough to compute a genuine cost-per-thousand-predictions and a real ROI model rather than invented figures — which is exactly what Lab 7 Task 2 asks for.

---

## Open threads, in priority order

1. **Lab 7 has no standalone `Lab_7--*.md`** and its TA guide is stale. This is the largest remaining block of work.
2. **Labs 2→5 end-to-end run** — never executed as one continuous pass through Feature Store → Athena → registry → deploy. **Not quota-blocked.** The Lab 5 reference trained locally via `models/churn/train_local.py`, which is now the documented path.
3. **Lab 4 CodePipeline** — never run. Now **unblocked**: a GitHub repo exists. Needs a CodeStar connection and `pipeline.yaml` deployed.
4. **Bedrock quotas still 0** — blocks Lab 3 Track B/C. Claude quotas are adjustable; embedding quotas are not and need a support case. **The unanswered question: do all 30 student accounts need manual grants?** Given students are on independent accounts with no institutional lever, assume yes and plan accordingly. Monitor: `TA Tools/bedrock_canary.py --watch`.
5. **`alarms.tf` is verified but SNS topics are empty strings** — alarms fire to nothing until real topic ARNs are supplied.
6. **A7's anomaly alarm cannot be demonstrated** inside a lab session (needs ~2 weeks of history + backfill is discarded). Defined and correct; just not showable.
7. `_retired/` folders in two places — decide keep or purge.
8. The vault copy of `northstar-ai-platform` under `Sample Solutions/` is **known-stale and gitignored**. Do not trust it; use the real repo.

---

## Working conventions

- Terraform vars use `var.project` / `var.environment`; no hardcoded `"northstar"` in module values.
- Every AWS-facing `description` is **ASCII only**.
- Prefer **observed** evidence over configuration screenshots — a counted traffic split beats a console capture.
- `AWS_PROFILE=terraform-user` on the reference account. There is no `[default]`.
- Commit to the instructor repo and push immediately; publish to the public repo **only** via `scripts/publish_student_repo.sh --dry-run` first, and read the file list.
- Blunt, direct communication; challenge bad calls; one recommendation not ten.

---

## Suggested first moves for the Lab 7 session

1. **Extract `Lab_7--Metrics & Business Value.md`** from the master guide, auditing as you go. Every section audited so far has had drift.
2. **Rebuild Task 2's unit economics on the measured numbers above.** The current spec predates having any of them.
3. **Check Lab 7 for the same class of defect found in Lab 6** — thresholds that contradict earlier labs, or that the reference model cannot meet. The Recall@10% 0.35-vs-0.25 error was exactly that, and it survived multiple prior reviews.
4. Rewrite the Lab 7 TA guide last, against whatever the audit produces.
5. Lab 7 likely needs **no AWS run at all**. Confirm that early — if true, it is the first lab in the course with zero infrastructure risk.
