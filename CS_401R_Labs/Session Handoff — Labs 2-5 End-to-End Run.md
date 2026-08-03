---
created: 2026-08-01
tags: [CS401R, handoff, integration, e2e]
supersedes: "Session Handoff — Lab 7 to Course Close"
purpose: The Labs 2→5 end-to-end run finally executed. It passed. It also found that the course's published reference metrics do not reproduce.
---

# Session Handoff — Labs 2→5 End-to-End Run


> **⚠ Superseded 2026-08-03 by [[Session Handoff — Dataset Rebase & Gate Redesign]]** on metrics, gates, dataset size and defects 39–48. Every model figure in this note — including the 0.7276 set it introduced as canonical — came from the retired 1,200-customer dataset on a non-deterministic Athena pull and does not reproduce. The AWS-mechanics observations still stand. Retained as the record of how defect 45 was found.

> **Read this before the next session.** It supersedes [[Session Handoff — Lab 7 to Course Close]] on the items below and leaves the rest of that note standing.
>
> **Update 2026-08-01 (third session): threads 1 and 2 below are CLOSED.** Defects 39, 40 and 41 are fixed and pushed. See "Closed 2026-08-01 (third session)". One residual: the Lab 3 slice AUCs were never re-measured.
>
> **The largest unclosed integration seam is now closed.** Labs 2→5 ran as one continuous pass on 2026-08-01 and worked. The new top risk is not integration — it is that **every reference metric published in Labs 3, 6, and 7 is stale and does not reproduce from either reference script.**

---

## What ran

One continuous pass on account `711457211658`, us-east-1, in ~50 minutes wall clock. SageMaker Studio Domain deliberately disabled (`enable_sagemaker_domain=false`) — it is not part of the data seam, and it costs ~10 min each way.

| Stage | Result | Measured |
|---|---|---|
| `terraform apply` — VPC + NAT + storage + IAM + Glue + Feature Store | 20 added, 0 errors | NAT create 1 m 35 s |
| Raw CSV → S3 → Glue crawler | SUCCEEDED | 54 s |
| Glue transform → `processed/customers/` | SUCCEEDED | 139 s, 278 DPU-s, 19,013 rows / 1,200 customers |
| Glue feature-engineer → `features/customers/` + Feature Store | SUCCEEDED | 106 s, 212 DPU-s, 1,200 rows, 0 nulls, churn 20.75% |
| Feature Store online store | `GetRecord` returns 16 features | immediate |
| Feature Store **offline** store hydration | first Parquet landed | **~5 min**, not the ~15 min the lab warns about |
| **Athena → train → register** (`train_reference.py`) | **all gates PASS** | 1,200 rows deduped, model package **v2** |
| Approve v2 → deploy → serve | `InService` | **404 s** on `ml.t2.medium` |
| Invoke (120-row batch + 20 singles) | scores 0.0066–0.9969 | client p50 375 ms, p95 461 ms |
| Data capture | landed at documented layout | **~4 min** behind invocation |
| `terraform destroy` | 43 destroyed | — |
| All-region sweep, 8 regions | endpoints/proc/schedules/domains/NAT/Glue/FG all **0** | — |

**The seam works.** `verify-lab2.sh` scored 31/33 from the repo root; both failures are covered below.

---

## The finding that matters: the published numbers do not reproduce

This is the Lab 7 defect-35 pattern again, one layer down. Four different "reference metrics" for the same Lab 3 model are in circulation, and **no two agree**:

| Source | AUC | Baseline | Lift | P@10% | R@10% |
|---|---|---|---|---|---|
| Handoffs Lab 3→4 and Lab 4→5 | 0.747 | 0.642 | +0.105 | 0.611 | **0.293** |
| `Lab_3--Model Development.md` body text | 0.736 | 0.667 | +0.069 | — | — |
| `train_local.py` — **measured today**, registry v1 | 0.7145 | 0.6727 | +0.0418 | — | — |
| `train_reference.py` (Athena) — **measured today**, registry v2 | **0.7276** | **0.6298** | **+0.0978** | **0.6944** | **0.3333** |

Both scripts use `seed=42` and `test_size=0.30`, so this is not split noise — the two paths build features differently, and the published figures came from neither of them in their current form.

**Why this is not cosmetic.** `R@10% = 0.293` is load-bearing in two places:

1. **Lab 6 Task 4** justifies the prediction-quality SLO of 0.25 by "the Lab 3 reference model achieves 0.293" sitting just above Lab 4's ≥ 0.25 promotion gate. At the measured **0.3333** the argument still holds but the margin it describes is wrong.
2. **Lab 7 Task 3** — the highest-value graded item in the course — computes the CDO-target-is-unreachable finding from 0.293. Redoing it at 0.3333: 378,000 churners × 0.3333 = **125,987** reach the contactable decile, so the retention offer must save **66.7%** of everyone it touches, not 75.8%.

   **The conclusion survives.** 66.7% against a plausible 12% save rate is still unreachable by roughly 5.6x rather than 6x. But the model answer's arithmetic is wrong, and Task 3 grades students on arithmetic.

**Recommendation — do this first next session.** Pick `train_reference.py` (the Athena path) as the single source of truth, because it is the path Lab 3 Task 1 actually requires and the only one now verified end to end. Propagate its numbers to Lab 3, Lab 6 Task 4, Lab 7 Task 3 and the Lab 7 solution notes, and delete the competing figures. Do not average them or split the difference.

---

## Defects found 2026-08-01 (second session)

Continuing the running list, now at 48.

| # | Defect | Impact |
|---|---|---|
| 39 | **Lab 2 names the catalog table `raw_customers`; the crawler creates `customers`.** No `TablePrefix` is set and the S3 path is `raw/customers/`. The verification command at Task 2 and the rubric pass criterion both name `raw_customers` | `aws glue get-table --name raw_customers` returns `EntityNotFoundException` for every student who follows the lab. The TA rubric line fails against a correct submission. `modules/glue/main.tf` comments carry the same wrong name |
| 40 | **S3 lifecycle rule count is 5, not 4.** The reference storage module has `expire-datacapture`; Lab 2's Architecture Reference table, its rubric ("returns all 4 rules") and `verify-lab2.sh` all say 4 | The reference implementation **fails its own verifier**. Worse in the other direction: a student who follows the lab literally ships 4 rules and no `datacapture/` expiry, so Lab 5/6 capture data accumulates with nothing to age it out — on the one prefix the module's own comment calls out as unbounded |
| 41 | **Four mutually inconsistent sets of Lab 3 reference metrics** (see above) | Lab 6's SLO justification and Lab 7 Task 3's graded arithmetic both rest on a figure no current code path produces |
| 42 | **`generate_presentations.py` does not build the shipped decks.** It writes `Presentations/L01_Course_Introduction.pptx`; the decks in use are `Presentations/PowerPoint/CS-401R-4-F26-L01.pptx`. Nothing in the repo produces that name, and L01 is 41 MB against the generator's 358 KB | The previous handoff's suggested move #2 — "rebuild and re-upload the decks" — would have **overwritten heavily hand-edited decks with generator output**. Do not run that generator expecting to refresh what students see |
| 43 | **Terraform reports an SNS email subscription as confirmed when it is not.** `aws_sns_topic_subscription.arn` returned a well-formed ARN for all four topics; `aws sns list-subscriptions-by-topic` returned the literal `PendingConfirmation` for the same four | Anything that reads the Terraform attribute records the alert path as live when no mail can be delivered. **Fourth instance** of the project's recurring pattern: a call that answers a question you did not ask and reports success |
| 44 | **The only durable copy of the evaluation metrics lived inside the bucket teardown deletes.** `train_reference.py` wrote the full metrics blob — including `slices_by_tier` — to `s3://<data-bucket>/artifacts/evaluations/latest/`. That bucket is `force_destroy = true`. The Model Registry carried only four scalars and no slice data | This is why the 2026-08-01 slice AUCs are unrecoverable. Nothing on the account held a second copy, so a routine `terraform destroy` silently destroyed the evidence behind Lab 3's highest-value teaching point. **Fixed 2026-08-01** — see below |
| 45 | **The Lab 3 reference metrics were never reproducible by construction.** `load_from_offline_store()` had no `ORDER BY` on its outer `SELECT`. Athena parallelises the scan and returns rows in whatever order the splits finish; `train_test_split(random_state=42)` is deterministic only for a *given* row order. Same data, different partition, different metrics, every run | Four runs on identical data measured AUC **0.7276–0.7431** and Platinum slice AUC **0.430–0.700**. Fixed with `ORDER BY customer_id`, verified byte-identical across three runs. **But the fix pins the pipeline to one arbitrary draw — and that draw is AUC 0.6919, which fails the course's own ≥0.72 gate.** A 200-split sweep shows the reference model fails that gate on **58%** of splits and the ≥0.03 lift gate on **21%**. The Platinum finding is worse-than-random on only **34.9%** of splits. See `docs/lab3-metric-stability.md` |
| 46 | **`canary_deploy_realtime.py` failed for every student before its first AWS call.** `--sample-csv` defaulted to the bare string `sample.csv`, resolved against the caller's cwd; Lab 5 tells students to run from the repo root and nothing in the repo creates that file | Guaranteed `FileNotFoundError` on the first Lab 5 deployment attempt. Hit directly during the 10k run. Fixed: default resolves against the script directory and a `sample.csv` ships beside it |
| 47 | **Lab 4's starter test gates never matched Lab 3's.** `test_model.py` required precision@10 ≥ 0.40 and recall@10 ≥ 0.35; Lab 3 has always specified 0.50 and 0.25. The Lab 3 skeleton's "baseline" was `np.full_like(proba, y.mean())` — a constant predictor whose AUC is exactly 0.5 by construction | A model could pass Lab 3 and fail Lab 4 CI, or the reverse. Any student using the skeleton as shipped compared against a coin flip rather than the recency rule the lab specifies, producing a "lift" near +0.27 that means nothing. Both fixed |
| 48 | **Batched invocation silently breaks Model Monitor.** More than one CSV row per request is captured as a single `endpointInput.data` string; the analyzer parses it as **1 column** and fails `missing_column_check`. Verified against an identical baseline: 60 single-row records parsed correctly at 12 columns, 211 batched records (121 rows each) collapsed to 1 | Any student who scores in batches gets a schema error instead of drift results, and nothing in the message mentions batching. Documented in Lab 6, the master, the solution note and `docs/lab6-runbook.md` |

Defect 43 joins 37, 38 and the `--query`-per-page bug. The rule stands and now has a fourth data point: **never accept a success response as an answer to a question you did not literally ask.**

---

## Closed this session

**Thread 1 — Labs 2→5 end-to-end run. CLOSED.** Ran as one continuous pass, all stages green. This was the top of the previous list.

**Thread 4 — `alarms.tf` SNS topics. CLOSED.** `monitoring/alerts/alarms.tf` now takes `create_sns_topics` (bool, default `false`) and `alert_email`. When true it creates the four P0–P3 topics and subscribes the address to each; when false, behaviour is byte-for-byte what it was, including the bring-your-own-ARN path. A `validation` block fails at plan time if `create_sns_topics` is set without a valid email, rather than creating four topics nobody is subscribed to.

Applied and destroyed on AWS to verify — 8 resources up, 8 down, account clean. That apply is what produced defect 43, so the module deliberately does **not** output the Terraform subscription ARN; it outputs the CLI command that gives a truthful answer instead.

Note: creating those topics sent four confirmation emails to scott@toborg.com. They are unconfirmed and the topics are deleted, so they are dead links — ignore them.

**Move 2 — downstream artifacts. PARTIALLY CLOSED.** See below.

---

## Downstream artifacts: what was actually stale

The generator *sources* are clean — a full scan for churn-window text across the project found no stale 30-day references outside the legitimate ones (return policy, `purchase_frequency_30d` / `spend_30d` lookbacks, S3 lifecycle, GDPR Article 22, tenure examples, dashboard windows).

The **built decks** were stale in exactly three places, each a single PowerPoint text run:

| Deck | Slide | Was | Now |
|---|---|---|---|
| `CS-401R-4-F26-L01.pptx` | 20 | "flags at-risk customers **30 days** out." | 90 days |
| `CS-401R-4-F26-L02.pptx` | 7 | "Identify customers at risk of churning within **30 days**." | 90 days |
| `CS-401R-4-F26-L07.pptx` | 3 | "churn probability, next **30 days**" | 90 days |

Patched by direct XML replacement inside the `.pptx` zip — **not** by regenerating, because of defect 42. Originals backed up to `/tmp/deckbak/` (transient; re-copy somewhere durable if you want them). All three verified to reopen and to contain the corrected text. No other deck carries a stale churn window; L03, L05, L12, L18, L19 and L22 hits are all legitimate. No stale `$140M` or `~15%` figures survive in any deck.

**Still open:** Canvas quiz banks and pages. `upload_quiz_questions.py` and `Canvas LMS/canvas_builder.py` both require `CANVAS_API_TOKEN` and `CANVAS_COURSE_ID`, which are not in this environment. **Nothing was re-uploaded to Canvas.** If quizzes were pushed before 2026-08-01 they still carry the old text. Set both env vars and re-run to close this.

---

## One thing to know about the teardown

`terraform destroy` removed **43** resources against the 20 this session added. The difference is the storage and IAM modules, which were already in state before this session and which the destroy correctly took with everything else.

Consequence: the data bucket `northstar-dev-data-711457211658` is gone (`force_destroy = true`), so **model packages v1 and v2 in `northstar-churn-models` now have dangling `ModelDataUrl`s** pointing into a deleted bucket. Neither will deploy as-is. Re-running either training script after the next apply regenerates the artifact and registers a fresh version.

Left the registry entries in place rather than deleting them — they are the Lab 3/5 evidence trail, and purging registry history is your call, not mine. Only `northstar-tfstate-711457211658` survives, which is correct.

---

## Closed 2026-08-01 (third session)

**Defect 41 — reference metrics. CLOSED.** `train_reference.py` (Athena path, 2026-08-01, registry v2) is now the single source of truth everywhere: **AUC 0.7276 · baseline 0.6298 · lift +0.0978 · P@10% 0.6944 · R@10% 0.3333**, base rate 20.75%. Propagated to Lab 2/3/6/7 standalones, `CS 401R Labs.md`, the Lab 2/3/4/5/7 solution notes, `docs/lab6-runbook.md` and `monitoring/alerts/alert-architecture.md`. Every competing figure is gone from live guidance; the five superseded handoffs carry a banner instead of being rewritten, so the history stays readable.

Three consequences worth knowing before you grade anything:

- **The AUC gate margin collapsed from +0.027 to +0.0076.** 0.7276 against a 0.72 threshold is close. Expect real near-misses from students and grade the method, not the third decimal. This is called out in the Lab 3 solution note.
- **Lab 7 Task 3 re-derived.** 378,000 × 0.3333 = **125,987** in the contactable decile → required save rate **66.7%** (was 75.8%). Downstream: 15,118 saved/yr, $5.14M, ROI **21.1x**, churn moves 0.72 pp, break-even save rate **0.569%**. The finding survives — the CDO's 4 pp target is still unreachable, now by ~5.5x rather than 6x.
- **The slice AUCs were NOT re-measured.** Bronze 0.809 / Gold 0.745 / Silver 0.688 / Platinum 0.430 are from the 2026-07-28 run; the 2026-08-01 pass did not capture slice output before teardown. The Lab 3 solution note now says so explicitly. **The Platinum finding is structural and will survive a re-run; the numbers are pending.** Capture `slices` from `train_reference.py` on the next apply and close this — it is the last unreproducible figure in the course.

**Defect 39 — `raw_customers`. CLOSED, docs side.** The crawler creates `customers` and that path is verified end to end, so the docs moved rather than the infrastructure. Lab 2, `CS 401R Labs.md`, the Lab 2 solution note and the `modules/glue/main.tf` comments all say `customers` now, with a one-line note explaining why (no `TablePrefix`, prefix is `raw/customers/`). Old submissions using `raw_customers` are still accepted.

**Defect 40 — lifecycle rule count. CLOSED, lab gains the fifth rule.** Lab 2's Architecture Reference, its rubric, the Lab 2 solution note and `verify-lab2.sh` all say **5** now and name `expire-datacapture` explicitly. The reference module was always right; the docs were wrong. The solution note tells TAs not to deduct from submissions graded against the older "4 rules" text.

**Defect 44 — evaluation metrics did not survive teardown. FIXED.** `train_reference.py` now calls `persist_metrics()` **before** registration and regardless of `--skip-register`, writing the full blob to three places: `docs/lab3-evaluation-metrics.json` in the repo (git-tracked, required, survives everything), the `northstar-tfstate-<account>` bucket (the one bucket that is never force-destroyed), and the data bucket as before. The S3 copies are best-effort — verified that credential/bucket failures warn and the run still succeeds, because losing metrics to a failed upload after a clean training run is the same bug in a different coat.

`CustomerMetadataProperties` on the model package went from 4 scalars to 16, now including `precision_top10`, `recall_top10`, `churn_rate`, per-tier `slice_<Tier>` entries, and — the one that matters — `slice_worst_tier` / `slice_worst_auc` as scalars, so the Platinum finding is visible in `describe-model-package` without parsing anything. The registry entry outlives the artifact bucket, so it is the last line of defence.

Verified locally with a synthetic metrics blob: default path resolves into the repo, nested directories are created, `None` slice AUCs serialise, worst-tier selection ignores them, and the map stays inside SageMaker's 50-pair / 256-char limits. Not run against AWS — no infrastructure is standing.

**Not committable: the three patched decks.** `Presentations/PowerPoint/` is in `.gitignore`, so the L01/L02/L07 churn-window fixes exist only in the working tree. Back them up somewhere durable — `/tmp/deckbak/` will not survive a reboot.

---

## Open threads, re-prioritised

1. ~~Decide how Lab 3 reports metrics.~~ **DONE 2026-08-02/03.** Dataset grown to 10,000 customers, full Labs 2→5 chain re-verified on AWS, decisions implemented and propagated across Labs 2, 3, 4, 6, 7, the master, five solution notes, both starter kits and the schema doc. Canonical figures: **AUC 0.7696 · baseline 0.7233 · lift +0.0464 CI [0.0254, 0.0670] · P@10% 0.6833 · R@10% 0.3106 · churn 22.0%**, registry v4. The absolute AUC gate is gone; the promotion gate is now a bootstrap CI on the lift that must exclude zero. Full evidence in `docs/lab3-metric-stability.md`. The last figure in the course that no current run reproduces. **Bundle it with thread 2** — Lab 4 CodePipeline needs the same infrastructure standing, so one apply pays the NAT once instead of twice. `train_reference.py` now persists slices automatically (defect 44, fixed), so the run is: apply → CSV → crawler → both Glue jobs → ~5 min hydration → `python models/churn/train_reference.py` → destroy. The metrics land in `docs/lab3-evaluation-metrics.json` and survive the teardown. Then update the Lab 3 solution note's slice table and drop its "pending re-measurement" banner. Do it before anyone grades Lab 3 Task 1 (due Oct 17 — no urgency, but do not let it reach a TA).
2. **Lab 4 CodePipeline** — never run. Unblocked; needs a CodeStar connection and `pipeline.yaml` deployed. Now the largest genuinely unexecuted path in the course.
4. **Canvas re-upload** — needs `CANVAS_API_TOKEN` / `CANVAS_COURSE_ID`.
4. **Bedrock quotas still 0** — blocks Lab 3 Track B/C only. Unchanged. Still unanswered whether all 30 student accounts need individual grants; assume yes.
5. **A7's anomaly alarm cannot be demonstrated** in a lab session. Unchanged, defined and correct, just not showable.
6. `_retired/` folders in two places — housekeeping.
7. Vault copy of `northstar-ai-platform` under `Sample Solutions/` is known-stale and gitignored. Unchanged.

---

## Notes for next session

- Offline store hydration measured at **~5 minutes**, not 15. Lab 2's "~15 min lag" warning is safe but pessimistic; if you are iterating, poll rather than wait.
- `ml.t2.medium` endpoint create measured **404 s**, consistent with the 7 min in the Lab 5 reference.
- Data capture landed **~4 min** behind invocation.
- Setting `DataCaptureConfig.DestinationS3Uri` to `s3://bucket/datacapture/<endpoint>` double-nests the prefix — SageMaker appends the endpoint name itself. Point it at `s3://bucket/datacapture` to get the documented layout.
- AWS spend for this session is expected to be small but **non-zero** — the NAT Gateway is the one component here Free Tier does not absorb. Check Cost Explorer for 2026-08 before assuming $0.00 the way July's data invited.
- **Committed and pushed 2026-08-01** to both `northstar-ai-platform` and `cs401r-2026-instructor`, including the previously uncommitted `alarms.tf`. The three `.pptx` files could not be committed — `Presentations/PowerPoint/` is gitignored.

---

## The decision waiting on you (defect 45)

A 360-row holdout cannot support a point estimate. Three things need deciding, and they interact:

**1. How metrics are reported.** Single split (status quo, now deterministic but arbitrary) vs. repeated stratified CV reporting mean ± SD. CV shrinks the standard error by roughly √k and is what the data supports. It changes `train_reference.py`, the Lab 3 evaluation-report table, the Lab 4 CI gate, and what students are asked to submit.

**2. Where the gates go.** Measured: AUC mean 0.7120 (sd 0.0291), lift mean 0.0604 (sd 0.0328). The ≥0.72 AUC gate fails on 58% of splits and the ≥0.03 lift gate on 21% — the lift threshold is smaller than the metric's own standard deviation. P@10% (≥0.50) and R@10% (≥0.25) fail on 1% and 2.5% and are well calibrated; leave them alone.

**3. What happens to the Platinum item.** It is worse-than-random on 34.9% of splits and undefined on 5.5%. As written it is a coin flip. The honest replacement is arguably a better lesson than the original: *a slice of ~33 customers with ~2 positives cannot support any claim; report the interval and refuse to conclude.* That preserves the 5 points and teaches something truer, but it is a rewrite of Lab 3's centrepiece, not an edit.

**Downstream if any of this moves:** Lab 4's CI quality gate reuses the same thresholds; Lab 6 Task 4's SLO justification and Lab 7 Task 3's graded arithmetic both consume single-draw values.
