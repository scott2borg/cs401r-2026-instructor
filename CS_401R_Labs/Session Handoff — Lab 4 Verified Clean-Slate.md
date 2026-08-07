---
created: 2026-08-04
tags: [CS401R, handoff, lab4, cicd, alarms, sns, verification, defects]
supersedes: "Session Handoff — Lab 4 Runs End to End"
purpose: Lab 4 verified green from a clean slate following the documented prerequisites verbatim, and the gate-failure alarm built, tested, found broken, and fixed.
---

# Session Handoff — Lab 4 Verified Clean-Slate

> **Read this before the next session.** It supersedes [[Session Handoff — Lab 4 Runs End to End]] and closes the two items that note left open: the unimplemented CloudWatch alarm, and the untested prerequisite sequence. Adds defects **73–74**.
>
> **The headline: the alarm I wrote yesterday was wrong in two independent ways, and only building it and firing it on purpose found either.** It watched a metric that a test failure skips, and it published to a topic that would not accept it. Both failed silently. Both are fixed and verified end to end.

---

## The one-line summary

Lab 4 now goes green on the first build from a clean slate with no fixes, and a
failing test provably halts the pipeline, blocks registration, and delivers a
notification to a real subscriber.

---

## The clean-slate run — the documented sequence works verbatim

Fresh `terraform apply`, fresh Glue chain, then the Lab 4 doc's four
prerequisites executed **exactly as written**, copy-paste, no edits:

| Prerequisite | Result |
|---|---|
| 1. Versioned artifacts bucket | Worked as written |
| 2. Connection `AVAILABLE` check | Worked as written — returned `AVAILABLE` |
| 3. SageMaker Pipeline via upsert | Worked — buildspec upserted it on the build |
| 4. `cloudformation deploy` with `CAPABILITY_NAMED_IAM` | Worked as written, including the `terraform output -raw` substitution |

**The first build after deploy went green with zero intervention** — Source →
Build → ManualApproval, all Succeeded. That is the thing yesterday's handoff
explicitly could not claim.

---

## Defects 73–74 — both mine, both silent

| # | Defect | Status |
|---|---|---|
| 73 | **The alarm watched a metric that the failure it targets skips.** It was built on a custom `NorthStar/CI BuildSucceeded` metric published from `buildspec.yml`'s `post_build`, on the belief that `post_build` always runs. **It does not.** When `PRE_BUILD` fails, CodeBuild goes straight to `FINALIZING` — `POST_BUILD` never appears in the phase list at all. So a **test** failure — precisely the case the rubric names — published nothing and the alarm sat in `OK` through a red build. (`post_build` *does* run when the `BUILD` phase fails, which is where the belief comes from.) | **Fixed.** Alarm now on `AWS/CodeBuild` `FailedBuilds`, which CodeBuild emits itself and no phase failure can skip. Confirmed emitted for the `pre_build` failure. `BuildSucceeded` stays, honestly commented, for the Lab 6 dashboard and to distinguish a gate rejection from an earlier failure |
| 74 | **The SNS topic policy omitted `cloudwatch.amazonaws.com`, so the alarm fired and could not notify.** The policy written 2026-08-03 allowed only `codepipeline.amazonaws.com`. The alarm evaluated correctly, transitioned to `ALARM` on cue, turned the console red — and delivered nothing. **The single trace anywhere was one line in `describe-alarm-history --history-item-type Action`:** `Failed to execute action arn:aws:sns:...`. Nothing surfaces on the alarm itself or on the topic | **Fixed.** Added the principal, with `Sid`s on both statements — SNS rejects a multi-statement topic policy without unique IDs (`Every policy statement must have a unique ID`) and the stack update rolls back |

**Defect 74 is the one worth remembering.** An alarm that fires and cannot
notify is worse than no alarm, because it looks like coverage on every
dashboard and in every review.

---

## The verification, in both directions

**Deliberate failing test pushed** (`assert False` in `tests/test_data.py`):

| Check | Result |
|---|---|
| Which phase halted | **`PRE_BUILD` FAILED**, `1 failed, 26 passed` |
| Did it reach BUILD | **No** — no upsert, no training, no registration |
| Model Registry versions | **stayed at 6** |
| Alarm | **`OK` → `ALARM`** |
| Notification | **`Successfully executed action`**, and the message arrived at a subscribed SQS endpoint with the full alarm description |

**Failure reverted:**

| Check | Result |
|---|---|
| Build | **Succeeded** |
| Model Registry versions | **6 → 7** — registration happens only on green |
| Alarm | **returned to `OK`** on its own |
| Pipeline | Source → Build → ManualApproval, all **Succeeded** |

The SQS subscriber was a temporary probe so delivery could be proven without
mailing anyone; it was unsubscribed and deleted at teardown.

---

## Docs updated

- **`Lab_4--XOps & CICD.md`** — gate-behavior section now carries the `sns subscribe` command and a blockquote covering **both** traps: `post_build` being skipped on a `pre_build` failure, and the topic-policy principal, including the `describe-alarm-history` command to check your own work. Also spells out the four-point demonstration and the reverse check.
- **Task 2 rubric rebalanced, still 30 points:** 10 / 8 / 6 and a **new 6-point item, "Failure notification demonstrably delivers"** — explicitly scoring 0 for an alarm that fires without delivering. That is the item that had no implementation behind it before this session.
- **Master `CS 401R Labs.md` synced** and verified: 0 unexpected differences across all seven standalones, code fences balanced. Only the two known-deliberate Lab 3 blockquote wraps differ, unchanged.
- Starter kit `pipeline.yaml` and `buildspec.yml` re-synced from the live repo.

---

## Measured on AWS 2026-08-04

| Stage | This run | Previous |
|---|---|---|
| `terraform apply` | 43 added | 43 added |
| Glue transform | **296 DPU-s** | 214 / 194 |
| Glue feature-engineer | **206 DPU-s** | 186 / 186 |
| Green CodeBuild run | ~5 min | 4 m 49 s |
| `terraform destroy` | 43 destroyed | 43 destroyed |

> **Glue DPU-s spread is much wider than documented.** Four measurements now:
> **430 / 400 / 380 / 502** total DPU-s for the same two jobs on identical data.
> That is a **32% spread**, not the ~7% recorded earlier. **Lab 7 Task 2's
> accept band must absorb this** — anything keyed near 430 as a point value will
> fail students for normal variance. This needs a real fix, not another note
> (thread 6).

---

## State of the account

**Clean.** 43 applied, 43 destroyed. Stack deleted, SageMaker Pipeline deleted,
CI/CD artifacts bucket purged of all versions and removed, SQS probe and its SNS
subscription removed. **8-region sweep returns zero** endpoints, feature groups,
NAT gateways, in-progress processing jobs and in-progress training jobs.
Stacks **0**, SageMaker pipelines **0**, alarms **0**, SNS topics **0**, SQS
queues **0**. Only `northstar-tfstate-711457211658` survives, which is correct.

**Model Registry: v1–v7.** v7 is the post-revert green run. **v7 is still
`Approved` and its `ModelDataUrl` died with the bucket — set it to `Rejected`
at the start of the next session** (or leave it, but do not treat it as
deployable).

**Cost:** one NAT-bearing session, no endpoint this time. Budget read
**$0.726 / $10** at session start; Cost Explorer still lags. The separate **$1**
budget remains at 73% and will breach.

---

## Git state

**Clean, `main` is the truth.** Four commits today, all merged and pushed.
`origin/main` moved `b1c3243 → e1b2c89`. The deliberate failing test was
committed and reverted in the immediately following commit; `tests/test_data.py`
is verified clean (0 occurrences). Nothing unmerged, no stale branches.

---

## Open threads

1. ~~Lab 4 end-to-end~~ — **CLOSED**, and now verified from a clean slate.
2. ~~Gate-failure alarm~~ — **CLOSED**, built and proven in both directions.
3. **Lab 5 canary/rollback + auto-scaling, and Lab 6 Model Monitor, still not re-run.** Unchanged. The deploy-and-predict path is verified at 10k; the canary weights, rollback alarm and Lab 6 analyzer-as-processing-job are not.
4. **`ArtifactsBucket` still has no owner (defect 65).** Documented in Lab 4 as a manual prerequisite and proven to work — but it is still a hand-run command, not infrastructure. Consider folding it into the Terraform storage module.
5. **Canvas — partially pushed 2026-08-04.** Course **34609**. `canvas_builder.py --sync` (new additive mode) uploaded both pre-lab guides as HTML to Files → `Pre-Lab Guides/` (ids 13374053, 13374054), updated Lab 3 and Lab 4 in place, and created **Pre-Lab 3** and **Pre-Lab 4** as 0-point assignments due Sep 30. `verify_canvas_sync.py` returned all-pass: no duplicates, real file links in all four descriptions, both pre-labs placed in a module.
    - **Still not pushed: quiz questions.** Run `python pipeline/stage4_quizzes.py` (the idempotent one — *not* `upload_quiz_questions.py`, which appends and duplicates).
    - **A stale gate shipped and was corrected minutes later.** Lab 3's Canvas points table still advertised `AUC-ROC ≥ 0.72`, retired 2026-08-02. `verify_canvas_sync.py` now carries a **retired-content sweep** over every assignment description; re-run `--sync` then verify.
    - **`canvas_builder.py` is a hand-maintained HTML duplicate of the labs.** Markdown edits do NOT propagate. This is a standing drift risk — the sweep catches known-retired content, not everything.
    - **Never run bare `canvas_builder.py` against this course again** — it is not idempotent and duplicates every assignment. Use `--sync`.
    - Token/course id are **not stored anywhere** and should stay that way; export per session.
6. **NEW — Lab 7 Task 2's Glue DPU-s accept band is too tight.** Four runs span 380–502 DPU-s (32%). Fix the band; do not just annotate it.
7. **Bedrock quotas still 0.** Unchanged.
8. **A7's anomaly alarm** still not demonstrable in a lab session. Unchanged.
9. Vault copy under `Sample Solutions/` still stale and gitignored. Unchanged.
10. **The quota decision is still outstanding and still the biggest deliverability risk.** Lab 4's TrainingStep needs on-demand training quota (default **0**; reference account has 15). Lab 3 Track B/C needs Bedrock. ~60 support cases across 30 independent accounts. **Three sessions have now proven the code works on an account that already has the quota. None of them reduced this risk.**
11. **The metric vocabulary is still forked** (`baseline_auc_roc` vs `baseline_auc`). `train_sagemaker.py` emits both as a deliberate shim. Unchanged.

---

## Notes for next session

- **The lesson, fourth refinement, and it is getting specific.** Previous sessions learned "re-run the sweep against the artifact," "never run ≠ ready to run," and "registering a model is not evidence it can be served." This one adds: **a monitoring control is not verified until you have made the bad thing happen on purpose and watched the notification arrive.** Both of this session's defects were in an alarm that looked correct in the console — right metric, right threshold, right state transition — and could not do its job.
- **`describe-alarm-history --history-item-type Action` is the only place a failed alarm action shows up.** Not on the alarm, not on the topic, not in the console's alarm view. Check it for every alarm this course ships. A7's anomaly alarm (thread 8) has never been checked this way and is a strong candidate for the same defect.
- CodeBuild phase semantics that cost time here: `post_build` runs after a failed **build** phase but is skipped entirely after a failed **pre_build**. Do not put anything load-bearing in `post_build` that must survive a test failure.
- SNS topic policies need a unique `Sid` per statement as soon as there are two.
- `sqs purge-queue` takes up to 60 seconds and deletes messages that arrive *during* that window — it briefly looked like a delivery failure when it was not. Prefer a fresh queue over a purge when timing matters.
- The deliberate-failure verification is cheap and repeatable and is now written into Lab 4 as the required demonstration. Re-run it any time the buildspec or the alarm changes.
