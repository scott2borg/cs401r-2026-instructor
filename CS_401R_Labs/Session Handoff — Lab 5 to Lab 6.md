---
created: 2026-07-30
tags: [CS401R, handoff, lab-6]
purpose: Warm-start context for a fresh session beginning Lab 6 work
---

# Session Handoff — Lab 5 → Lab 6

> **⚠ Superseded 2026-08-01 (defect 41).** The Lab 3 reference metrics quoted in this note (AUC 0.747 / baseline 0.642 / lift +0.105 / P@10% 0.611 / R@10% 0.293) do **not** reproduce. The canonical figures are now **AUC 0.7276 / baseline 0.6298 / lift +0.0978 / P@10% 0.6944 / R@10% 0.3333** — `train_reference.py`, Athena path, measured end to end 2026-08-01, registry v2. See [[Session Handoff — Labs 2-5 End-to-End Run]]. This note is retained as a historical record; do not quote its metrics.

> **How to use this:** Reference this note as the first message in a new session before starting Lab 6. It captures what Lab 5 landed, what Lab 6 inherits, and the open threads.

---

## Source of Truth (read these first)

| What | Path |
|------|------|
| **Live reference implementation** (correct, authoritative) | `/Users/scott1/northstar-ai-platform` — branch `lab5-deployment-verification`, commit `36b8e50` |
| Lab 6 spec | `CS 401R Labs.md` — Lab 6 section (**no standalone `Lab_6--*.md` yet**) |
| Lab 1–5 specs | `Lab_1--Platform Foundation.md` … `Lab_5--Deployment & Security.md` |
| Starter kits | `Starter Kits/Lab N/` (Labs 5–7 intentionally have none) |
| TA grading guides | `Sample Solutions/Lab Solution Notes/` |
| TA tooling | `TA Tools/` |

**Rules that have held:**
- The live repo is authoritative; Sample Solutions is a copy kept in sync.
- **Standalone `Lab_N--*.md` is authoritative over the master guide**, which gets synced to match. Labs 1–5 have standalone files; **Labs 6–7 live only in the master guide.**
- **Verify on AWS. "It should work" has been wrong ~17 times this project** — and once this session it was *my own* claim that was wrong, not AWS's behaviour. Test the thing you are about to assert.

---

## Where the Course Stands

| Lab | Spec | Starter kit | Verified on AWS | TA guide |
|---|---|---|---|---|
| 1 | ✅ | ✅ | ✅ | ✅ |
| 2 | ✅ | ✅ | ✅ (6 full runs) | ✅ |
| 3 | ✅ | ✅ | ✅ Track A end to end | ✅ |
| 4 | ✅ | ✅ | ✅ CodeBuild path | ✅ |
| 5 | ✅ standalone | n/a | ✅ **full path, 2026-07-30** | ✅ **rewritten** |
| **6** | ✅ audited, units fixed | n/a | ❌ | ❌ **stale** |
| 7 | ✅ audited | n/a | ❌ | ❌ **stale** |

**AWS account `711457211658` is clean.** Verified after the Lab 5 run across all 17 regions: 0 endpoints, endpoint configs, models, model package groups, scaling targets, CloudWatch alarms. Retained: `northstar-tfstate-711457211658` (S3) + `northstar-tfstate-lock` (DynamoDB). Lab 5 verification cost **under $0.20**. Budget alarm at $10/mo → scott@toborg.com.

**AWS credentials:** there is no `[default]` profile. Use `AWS_PROFILE=terraform-user` (IAM user `CS401RAdmin`, region `us-east-1`). Note that `Fix Credentials Problem.md` tells students to configure `[default]` — the reference environment does not match that instruction. Minor, but it will confuse a TA.

---

## What Lab 6 Inherits

Lab 6 instruments the production system Lab 5 deployed: five monitoring layers, alert architecture, SLOs with error budgets, and runbooks.

Tasks: Five-Layer Monitoring (35) · Drift Detection Plan (15) · Alert Architecture (15) · SLO Design (15) · Runbooks (20) = **100**.

### Concrete artifacts available

| Artifact | Detail |
|---|---|
| Verified deployment reference | `deployment/configs/canary_deploy_realtime.py` — real-time canary, every timing measured |
| Batch deployment reference | `deployment/configs/canary_deploy.py` — **explicitly marked NOT verified on AWS** |
| Auto-scaling reference | `deployment/configs/auto_scaling.py` — includes a burstable-instance guard |
| Rollback alarm as code | `deployment/configs/rollback-alarm.json` — correct microsecond threshold |
| Teardown | `scripts/teardown-lab5.sh` — verified, writes `docs/lab5-teardown-output.txt` |
| Live-run evidence | `docs/lab5-deployment-output.txt` |
| Model answer keys | `docs/lab5-deployment-plan.md`, `docs/lab5-security-assessment.md` |
| `ModelMonitor` IAM role | Exists since Lab 2 — monitoring-schedule + CloudWatch permissions. **Lab 6 Task 1 needs it.** |

**`monitoring/` is empty.** Lab 6 Task 1 requires `monitoring/dashboards/northstar-dashboard.json` and Task 3 requires `monitoring/alerts/`. Neither directory exists yet.

### Measured numbers Lab 6 should build on

These came from the Lab 5 reference run and are the real baseline for every SLO and alert threshold in Lab 6:

```
ModelLatency steady state      ~4,150 us average  (4.15 ms), 7,821 us max
ModelLatency cold start        ~24,000 us         (~6x, first call after deploy)
create-endpoint -> InService   6 min 47 s
update-endpoint                3 min 47 s, zero downtime
weight-shift rollback          ~85 s, no dropped requests
alarm OK -> ALARM              < 60 s
```

**Lab 6's SLO table targets p95 < 200 ms. The measured p95 is ~4 ms — a 48x margin.** Nobody has stress-tested whether that margin holds under load, because the Lab 5 run never exceeded ~200 invocations/minute. A student could hit the SLO trivially and learn nothing. Worth deciding whether Lab 6 should tighten the target or add a load requirement.

### Cost warning specific to Lab 6

**Lab 6 needs a live endpoint to monitor, so it re-creates Lab 5's hourly-billing resource** — and then asks students to leave it running long enough to generate baseline statistics and a Model Monitor schedule. That is a longer live window than Lab 5's 60 minutes.

SageMaker Model Monitor also runs **processing jobs on their own instances** on a schedule, which bill separately from the endpoint. This has never been costed. Do that before writing the spec.

`scripts/teardown-lab5.sh` does not delete monitoring schedules. Lab 6 will need its own teardown, or an extension to that one.

---

## What Lab 5 Landed (this session)

1. **`Lab_5--Deployment & Security.md`** extracted as a standalone spec; master guide synced and verified byte-identical.
2. **Full Lab 5 path executed on AWS** — model registered and approved, two-variant canary deployed at 9:1, traffic split observed, auto-scaling registered, rollback alarm fired, rollback executed, everything torn down and verified across 17 regions.
3. **Lab 5 TA guide rewritten** against the real run; 16 rubric items summing to 100.
4. **`scripts/teardown-lab5.sh`** written and verified.
5. **Stale batch-era answer keys repaired** rather than purged — the batch material was better than expected and the spec permits the batch path.

### Three defects found that would have blocked students

- **`ml.t2.medium` cannot be an auto-scaling target.** `RegisterScalableTarget` rejects burstable types. The endpoint deploys fine and fails *only* at the scaling step — after it is already billing. Task 1 requires auto-scaling, so the cheapest instance is the one that makes the requirement impossible. Costs 5 points and a 4-minute rebuild.
- **`ModelLatency` is emitted in microseconds.** The spec, the chapter and Lab 6's SLO table all say "p95 < 200ms". A threshold of `200` alarms at 0.2 ms against a healthy endpoint, sits in `ALARM` permanently, and fires a rollback on every deploy. Verified both ways: `200000` stayed `OK`; `1000` alarmed in under a minute. **Lab 6's three latency references are now unit-corrected**, with a note explaining why.
- **Model weights were classified Internal/SSE-S3** in the answer key while the same document's threat model rated their exfiltration High impact. Corrected to Confidential/SSE-KMS.

### One claim I made and had to retract

I asserted in the Lab 4→5 handoff that Application Auto Scaling **orphans scalable targets on endpoint deletion**, and used it as the whole justification for a separate Lab 5 teardown script. **Tested it: false.** Registered a target, deleted only the endpoint, and the target, its scaling policies and the auto-created `TargetTracking-*` alarms were all gone within 90 seconds.

`teardown-lab5.sh` still earns its place — Lab 3's script does not delete SageMaker Models or rollback alarms, does not assert on scaling targets, and writes to the wrong evidence file — but on real grounds. The TA guide tells graders **not** to deduct for students who delete the endpoint without deregistering the target.

---

## Open Threads

### The Labs 2→5 end-to-end run (decided, not yet done)

**Decision made this session:** close the integration seam with a **single dedicated Labs 2→5 run**, not per-lab.

The Lab 5 verification deliberately skipped the Feature Store hop — it trained locally from `data/northstar-raw-sample.csv` through the verified pandas `feature_engineering.py` and registered that artifact. Deployment mechanics are model-agnostic so this was sound for Lab 5, but it means **`train_reference.py` → Athena → registry → deploy has never run as one continuous pass.**

Watch out: that shortcut model scored **AUC 0.7444, lift +0.0268** — *below* Lab 4's ≥0.03 gate. It would have failed the Lab 4 build. The canonical Lab 3 Track A metrics remain **AUC 0.747 / baseline 0.642 / lift +0.105 / precision@10 0.611 / recall@10 0.293**. Do not confuse the two.

### Live external dependency — Bedrock (blocks Lab 3 Track B/C only)

- Anthropic FTU form **submitted**; Claude Haiku agreement **AVAILABLE**; Titan entitlement **AVAILABLE**
- **Both quotas still 0.** Claude's cross-region quotas are adjustable (request filed); embedding quotas are **not adjustable** and need an AWS Support case.
- **The question that decides Lab 3 Track B/C:** do all 30 student accounts need manual quota grants? If yes, those tracks are undeliverable as scheduled.
- Monitor: `TA Tools/bedrock_canary.py --watch`.

### Lab 4 residual

- **CodePipeline orchestration never run.** No GitHub repo or CodeStar connection exists, so the Source stage, stage sequencing and the SageMaker Pipeline trigger are unproven. `pipeline.yaml` validates against CloudFormation but has never been deployed. Lab 5's Task 5 was written to accept the CodeBuild path so this does not block students.
- To close it: push the repo to GitHub, create a CodeStar connection, deploy `pipeline.yaml`.

### Course-structure backlog

- [ ] **Lab 6–7 TA guides** — both still written against the retired architecture. Lab 6's is now unit-correct but otherwise stale. Largest remaining block.
- [ ] **Standalone `Lab_6--*.md` / `Lab_7--*.md`** to match Labs 1–5
- [ ] Nothing in Labs 6–7 has been executed on AWS
- [ ] Cost Model Monitor processing jobs before writing the Lab 6 spec
- [ ] Decide whether Lab 6's p95 < 200 ms SLO is meaningful at a measured 4 ms
- [ ] `Fix Credentials Problem.md` says `[default]`; reference env uses profile `terraform-user`
- [ ] Branch `lab5-deployment-verification` is unpushed and unmerged
- [ ] TA canary account for Bedrock timing — `TA Tools/TA Procedure — Bedrock Canary Test.md`
- [ ] `_retired/` folders in two places; decide keep or purge

---

## Traps Already Mapped — do not rediscover

Seventeen AWS/tooling defects across this project, none caught by `terraform validate` or LocalStack. Full lists live in the Lab 2/3/4/5 TA guides. Most relevant to Lab 6:

1. **`ModelLatency` is in microseconds.** 200 ms is `200000`. Every Lab 6 latency threshold depends on this.
2. **Cold start is ~6x steady-state latency.** An alarm with `EvaluationPeriods: 1` trips on your own deployment.
3. **Endpoints bill hourly until deleted.** Rolling back to weight 0 does not stop the charge.
4. **Burstable instances cannot be auto-scaling targets.**
5. **IAM propagation lag ~30s** — re-running immediately shows the *old* error and looks like the fix failed.
6. **Non-ASCII in AWS-facing `description` / `Description` fields** — EC2 rejects em dashes, IAM accepts them, so failures look arbitrary.
7. **`terraform destroy` does not fully tear down** — six orphan classes, one (SageMaker EFS) **keeps billing**. Always use the teardown scripts.
8. **Console Resource Explorer lags hours.** Verify against the live API.
9. **Colon-in-echo breaks buildspec YAML.**
10. **`delete-model-package` takes an ARN but the flag is `--model-package-name`.** A package group cannot be deleted until every package inside it is gone.
11. **Auto-scaling does NOT orphan** (see retraction above) — do not "fix" this non-problem.

---

## Working Conventions (carry forward)

- Terraform vars use `var.project` / `var.environment`.
- No hardcoded `"northstar"` literals in module **values**; resource labels are fine.
- Guard variables (`enable_*`) for anything LocalStack cannot do, defaulting true.
  **Fast test path:** `-var-file=/tmp/pipeline-only.tfvars` (`enable_sagemaker_domain=false`, `enable_nat_gateway=false`, `enable_glue_vpc_connection=false`) gives a ~$0.05, 15-minute stack that avoids every known orphan.
- Every AWS-facing description is ASCII only.
- Verify against the live AWS API, never the console index.
- Tear down after every AWS session and confirm with an independent all-region sweep.
- Prefer **observed** evidence over configuration screenshots. Lab 5's strongest artifact is a counted traffic split, not a console capture — carry that standard into Lab 6's dashboard and alert grading.
- Blunt, direct communication; challenge bad calls; one recommendation not ten options (per vault CLAUDE.md).

---

## Suggested First Moves for the Lab 6 Session

1. **Cost Model Monitor first.** It is the one Lab 6 component with no cost data, it runs processing jobs on their own instances, and it drives 10 of Task 1's 35 points. Everything else in the lab is cheap by comparison.
2. **Write `Lab_6--Monitoring & Reliability.md`** from the master-guide section, then sync back — same structure as Labs 1–5. Audit while extracting; every section audited so far has had drift.
3. **Execute Lab 6's monitoring path on AWS** — redeploy the Lab 5 endpoint, configure a Model Monitor schedule, push a custom business metric, build the dashboard, export the JSON, then tear down. Decide teardown coverage for monitoring schedules before starting.
4. **Rewrite the Lab 6 TA guide** against the real run. Much of Lab 6 (drift plan, SLOs, runbooks) is written deliverable and gradable without an AWS run.
5. Resolve the p95 SLO question — a 48x margin makes the latency SLO free.
