---
tags: [CS401R, handoff, course-close]
created: 2026-08-01
supersedes: "Session Handoff — Lab 6 to Lab 7"
purpose: Warm-start context for a fresh session. All seven labs are specified. What remains is integration, not authoring.
---

# Session Handoff — Lab 7 → Course Close

> **Read this before the next session.** It supersedes [[Session Handoff — Lab 6 to Lab 7]]. Lab 7 is closed; the largest remaining risk is no longer content, it is the **Labs 2→5 end-to-end run**, which has still never been executed.

---

## Source of Truth

| What | Where |
|------|-------|
| **Live reference implementation** | `/Users/scott1/northstar-ai-platform` — branch `lab5-deployment-verification`, pushed to `github.com/scott2borg/northstar-ai-platform` (**private**) |
| Course content, solutions, TA guides | `github.com/scott2borg/cs401r-2026-instructor` (**private**) — this vault folder |
| Student-facing labs + starter kits | `github.com/scott2borg/cs401r-2026-labs` (**public**) — published only via `scripts/publish_student_repo.sh` |
| Course constraints | [[Efforts/Projects/Active/CS_401R_2026/CLAUDE.md]] — **read this first** |
| Cost model + blocker history | [[Lab 6 — Cost Model & Pre-Flight Blockers]] |

**Rules that still hold:**
- Standalone `Lab_N--*.md` is authoritative; the master guide is synced to match and verified byte-identical.
- **Verify on AWS.** `terraform validate` has failed to catch a real defect roughly 20 times on this project.
- Tear down after every session and confirm with an independent all-region sweep.

---

## Where the course stands

| Lab | Spec | Verified on AWS | TA guide |
|---|---|---|---|
| 1 | ✅ | ✅ | ✅ |
| 2 | ✅ | ✅ | ✅ |
| 3 | ✅ | ✅ Track A | ✅ |
| 4 | ✅ | ✅ CodeBuild path only | ✅ |
| 5 | ✅ | ✅ full path, capture + rollback | ✅ |
| 6 | ✅ | ✅ Tasks 1–5 | ✅ |
| **7** | ✅ **written + audited 2026-08-01** | ✅ **read-only path verified; no infrastructure required** | ✅ **rewritten against measured numbers** |

**All seven labs are specified.** Account `711457211658` is clean — swept across 8 regions on 2026-08-01, zero endpoints, processing jobs, monitoring schedules, or anomaly detectors. AWS spend for the Lab 7 session: **$0.05** (five Cost Explorer requests at $0.01; every other call was free).

---

## What Lab 7 turned out to be

Lab 7 is the first lab in the course with **zero infrastructure risk**. It creates nothing, tears down nothing, and completes entirely inside AWS default quotas because every call it makes is read-only. That was confirmed early, as the previous handoff suggested, and it held.

It is also now the lab with the strongest evidence base, because it is built on the *measured* platform rather than on projections. Two AWS APIs did the work and both were verified this session:

- **`aws pricing get-products`** — free, no quota, authoritative for everything SageMaker, Glue, S3 and CloudWatch. This is the rate card the lab is built on.
- **`aws ce get-cost-and-usage --metrics UsageQuantity`** — $0.01/request, returns real consumption per usage type.

### The finding that reshaped the lab

**Cost Explorer reports $0.00 for July 2026 — a month in which the reference account ran all of Labs 1 through 6.**

Free tier absorbed the entire platform. Every usage type is present with a real quantity and a zero dollar amount:

| Usage type | Quantity | Billed |
|---|---|---|
| `Host:ml.m5.large` | 0.5889 hr | $0.00 |
| `Host:ml.t2.medium` | 0.4328 hr | $0.00 |
| `Host:ml.m6g.large` | 0.0192 hr | $0.00 |
| `Processing:ml.t3.large` | 0.0958 hr (5 min 45 s — the successful analyzer run) | $0.00 |
| `Processing:ml.t3.medium` | 0.2283 hr (13 min 42 s — the run that OOMed) | $0.00 |
| `ETL-DPU-Hour` | 1.0311 | $0.00 |
| `Crawler-DPU-Hour` | 0.4786 | $0.00 |
| `FeatureStore:WriteRequestUnits` | 7,967 | $0.00 |
| **Whole account, whole month** | | **$0.00** |

This invalidated the lab's original premise, which assumed students would read their own bill. The lab is now built on the opposite rule: **unit economics are computed from `usage × published rate`, never from the invoice.** The July usage table ships in the lab as evidence, and the failed-job row is called out — the OOM cost more instance time than the success did.

### The other finding: the CDO's target is unreachable

This is the Lab 7 analogue of the Lab 6 Recall@10% defect, one layer up.

The case sets the churn success metric at **18% → 14% annually**, with the retention program contacting only the **top 10%** of customers by risk. Working that against the measured model:

- 4pp of 2.1M customers = **84,000 retentions/year** required
- 378,000 churners/year; at the measured Recall@10% of 0.293, **110,754** reach the contactable decile
- Therefore the retention offer must save **75.8%** of everyone it touches
- At the theoretical recall ceiling of 0.48 it is still 46.3%
- Even contacting **100%** of customers at a plausible 12% save rate yields only **2.16pp**

**The target is not reachable by tuning anything.** It is structurally capped by the decile constraint. Meanwhile the platform costs $20,303/month and breaks even at a **0.647%** save rate — 717 customers a year. At 12% it returns **18.5x**.

So the honest answer is that the platform is an excellent investment *and* will miss its stated goal by roughly 6x. Both. That contradiction is now the highest-value graded item in the lab (Task 3, 10 points), and a scorecard reporting the target as "On Track" scores zero on it.

---

## Defects found and fixed on 2026-08-01

Continuing the project's running list, now at 38.

| # | Defect | Impact |
|---|---|---|
| 28 | Task 1 required the second metric pyramid to cover "your Track B/C choice from Lab 3" — Bedrock quotas are 0, so most students have no such system | Task 1 was uncompletable for the majority; now an explicit design exercise |
| 29 | Lab 7 used a **30-day** churn window; Lab 2 derives a **90-day** label and Lab 6 depends on it | Whole measurement framework was one label-definition off |
| 30 | Methodology template had **13** fields, rubric said "all 12" | Unresolvable rubric |
| 31 | Prior optimization example was `ml.c5.2xlarge` — non-burstable processing quota is 0 by AWS default | The model answer was an unexecutable instruction |
| 32 | Cost per 1,000 predictions of $0.011 was asserted, never derived | Now $0.012, from usage × rate, arithmetic published |
| 33 | Tasks 1 and 2 named no deliverable file; Tasks 3–5 did | Ungradeable submissions |
| 34 | Six-category cost taxonomy had no home for Glue pipeline compute | Students would have split it three ways or dropped it |
| 35 | **CDO success metric structurally unreachable** (see above) | Would have propagated into every student scorecard as "On Track" |
| 36 | Nothing anywhere noted that **Cost Explorer reports $0.00** | Every student would have concluded the platform is free |
| 37 | **Price List API returns a single pricing tier and does not say which.** `CW:MetricMonitorUsage` returns $0.02 (over-1M-metrics tier); the actual rate at this scale is $0.30 | Silent 15x error in any cost model built from the API |
| 38 | **Bedrock output-token prices are absent from the Price List API** in us-east-1, and Claude coverage is stale (2.0, 2.1, 3 Haiku, 3 Sonnet, Instant only) | An input-only LLM cost model understates by roughly half |

Defects 37 and 38 are the same family as the `--query`-per-page bug from 2026-07-31: **an AWS API that answers a question you did not ask, and returns HTTP 200 while doing it.** That is now three instances on this project. Assume it, check the `description` field, and never take a single row from a paginated or tiered API as the answer.

---

## Open threads, in priority order

1. **Labs 2→5 end-to-end run** — still never executed as one continuous pass through Feature Store → Athena → registry → deploy. **Not quota-blocked.** This is now the largest unclosed integration seam in the course, and with all seven labs written it is the top of the list. The Lab 5 reference trained locally via `models/churn/train_local.py`, which is the documented path.
2. **Lab 4 CodePipeline** — never run. Unblocked: a GitHub repo exists. Needs a CodeStar connection and `pipeline.yaml` deployed.
3. **Bedrock quotas still 0** — blocks Lab 3 Track B/C. Claude quotas are adjustable; embedding quotas are not and need a support case. **Unanswered: do all 30 student accounts need individual manual grants?** With no institutional lever, assume yes. Monitor: `TA Tools/bedrock_canary.py --watch`. Note that Lab 7 no longer depends on Track B/C being deployed, so this blocks Lab 3 only.
4. **Starter-kit / lab contradiction on the churn window.** `Starter Kits/Lab 1/northstar-scenario-overview.md` says "30-day churn probability"; every lab says 90 days. **It was deliberately not edited** — it is already published and changing it mid-semester has its own cost. Lab 7 states the correction explicitly and the labs are authoritative. **Instructor decision needed:** patch the starter kit, or let the Lab 7 correction carry it.
5. **The case's $140M churn figure does not reconcile with its own inputs.** 2.1M × 18% × $340 = $128.5M. Lab 7 turns this into a required reconciliation rather than papering over it, but the source document is still internally inconsistent.
6. **`alarms.tf` verified but SNS topics are empty strings** — alarms fire to nothing until real topic ARNs are supplied. Unchanged from the last handoff.
7. **A7's anomaly alarm cannot be demonstrated** inside a lab session (needs ~2 weeks of history; backfilled metrics are silently discarded). Defined and correct; just not showable.
8. `_retired/` folders in two places — decide keep or purge. Neither is published; this is housekeeping, not risk.
9. The vault copy of `northstar-ai-platform` under `Sample Solutions/` is **known-stale and gitignored**. Do not trust it; use the real repo.

---

## Suggested first moves for the next session

1. **Run Labs 2→5 end to end.** It is not quota-blocked, it is the only unclosed seam that can still surprise 30 students simultaneously, and every lab it touches is now frozen. Budget one session and tear down.
2. Decide thread 4 (starter-kit churn window). It is a one-line edit or a one-line decision; leaving it open guarantees a support burst in Lab 7 week.
3. Supply real SNS topic ARNs to `alarms.tf` (thread 6) — small, and it removes a "verified but inert" item from the list.
4. Lab 4 CodePipeline (thread 2) if there is session budget left.

---

## Working conventions

- Terraform vars use `var.project` / `var.environment`; no hardcoded `"northstar"` in module values.
- Every AWS-facing `description` is **ASCII only**.
- Prefer **observed** evidence over configuration screenshots.
- `AWS_PROFILE=terraform-user` on the reference account. There is no `[default]`.
- The `pricing` API endpoint exists only in `us-east-1` and `ap-south-1`; `--region` selects the endpoint, the `regionCode` filter selects what you are pricing.
- Commit to the instructor repo and push immediately; publish to the public repo **only** via `scripts/publish_student_repo.sh --dry-run` first, and read the file list. Lab 7 was added to the allowlist on 2026-08-01; dry-run stages 32 files with no leak or secret markers.
- Blunt, direct communication; challenge bad calls; one recommendation not ten.
