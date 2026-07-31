---
tags: [CS401R, TA, bedrock, canary, course-ops]
course: CS 401R
audience: TA
status: ready
---

# TA Procedure — Bedrock Canary Test

**Goal:** find out how long a brand-new AWS account actually takes to get usable Bedrock access.

That single number decides whether the *Pre-Lab 3 — Bedrock Access Setup* exercise works as scheduled (assigned Sep 17, due Sep 30 — a 13-day window). Nobody knows it yet. Everything else in Lab 3 has been verified end to end; this is the last unknown, and it has a hard deadline attached.

**Please start this as early as possible.** If approval turns out to take three weeks, we need to know now, not in September.

---

## What we already know

Measured on the instructor's development account on 2026-07-29:

| Finding | Detail |
|---|---|
| Bedrock inference quotas | **400 of 411 were zero** |
| Anthropic models | `ResourceNotFoundException: Model use case details have not been submitted` |
| All other models | `ThrottlingException: Too many tokens per day` |

That second error is **misleading and worth internalising** — it does not mean the allowance was used up. It means the allowance is zero. Students will read it as "I need to wait" and wait forever.

The instructor's account is **not** representative: it has billing history and months of use. A genuinely new account may behave differently in either direction. That is exactly what you are measuring.

---

## Step 1 — Create the canary account

It must be indistinguishable from a student's day one:

- **Brand new** AWS account, never used for anything
- **Not** linked to an AWS Organization that might inherit quotas or entitlements
- Standard Free Tier signup, own payment method
- Region **us-east-1**
- Do **not** enable Bedrock, request quotas, or touch anything before Step 2

Create an IAM user with programmatic access and attach `AdministratorAccess` (this is a throwaway test account; least privilege is not the exercise here). Configure a named profile locally:

```bash
aws configure --profile canary
export AWS_PROFILE=canary
export AWS_DEFAULT_REGION=us-east-1
aws sts get-caller-identity      # CONFIRM this is the canary, not your own account
```

> Getting this wrong and probing your own account produces meaningless data. Check the account number every session.

---

## Step 2 — Baseline probe, before changing anything

```bash
cd "TA Tools"
pip install boto3
python3 bedrock_canary.py
```

Expected output on an untouched account — both blocked, all quotas zero:

```
  embeddings  QUOTA_ZERO           quota is zero (message says 'too many tokens' - misleading)
  generation  FORM_NOT_SUBMITTED   Anthropic use-case form outstanding
  quotas:
    titan_embed_tpm    0  <-- BLOCKED
    ...
  ==> still blocked
```

**Record the timestamp of this probe. Every later measurement is relative to it.**

If the baseline shows anything already passing, stop and tell the instructor — the account is not clean and the results will not represent a student.

---

## Step 3 — Work through the student exercise, timing each action

Open `Pre-Lab 3 — Bedrock Access Setup.md` and follow it **exactly as written**, as a student would. Do not use shortcuts or prior knowledge. If a step is unclear or wrong, that is a finding — write it down.

Record the wall-clock time you complete each action:

| Action | Time completed (UTC) | Notes |
|---|---|---|
| Anthropic use-case form submitted | | |
| Titan Text Embeddings V2 enabled | | |
| Claude Haiku 4.5 enabled | | |
| Quota request: Titan tokens/min | | value requested: |
| Quota request: Titan requests/min | | value requested: |
| Quota request: Haiku tokens/min | | value requested: |
| Quota request: Haiku requests/min | | value requested: |

For each quota request also note the **Service Quotas case ID** — you will need it if you have to chase them.

---

## Step 4 — Let the canary run

Start the watcher immediately after submitting the requests:

```bash
python3 bedrock_canary.py --watch --interval 30
```

It probes every 30 minutes, appends a timestamped row to `bedrock_canary_log.csv`, and stops when access works. Safe to ctrl-C and restart — the log persists and `--report` reads the whole history.

If you would rather not leave a terminal open, schedule it instead:

```bash
# hourly, via cron
0 * * * * cd /path/to/TA\ Tools && AWS_PROFILE=canary python3 bedrock_canary.py >> canary.out 2>&1
```

**Do not probe more often than every 15 minutes.** Rapid polling against a zero quota is itself throttled and will not speed anything up.

---

## Step 5 — Report

Once `ALL PASS` appears — or after two weeks, whichever comes first:

```bash
python3 bedrock_canary.py --report
```

This prints when each milestone was reached and how many hours it took, then gives a verdict against the Sep 30 deadline:

| Result | Meaning |
|---|---|
| ≤ 7 days | Comfortable. No schedule change. |
| 7–11 days | Works, little margin. Consider assigning earlier. |
| > 11 days | **Too slow.** The exercise must move earlier, or Track B/C must be decoupled from the Lab 3 deadline. |

---

## Step 6 — Cost check

A day or two after access works, run one Track B evaluation on the canary (embed the four policy documents, run the four RAGAS test cases), then:

```bash
python3 bedrock_canary.py --cost
```

Compare against the **~$2** estimate in the student doc. Cost Explorer lags 24–48 hours and must be enabled once in the console.

If real cost materially exceeds $2, the student doc needs correcting — students budget against it and have finite Free Tier credits.

---

## What to send back to the instructor

1. `bedrock_canary_log.csv` — the raw log
2. The `--report` output
3. The Step 3 timing table, filled in, with case IDs
4. The `--cost` output
5. **Any step in the student doc that was wrong, unclear, or out of date** — model IDs, console menu names, and quota names all drift, and you are the first person to walk the path end to end

Point 5 matters as much as the timing. The doc was written from the instructor's account and verified there; you are testing whether it survives contact with a real new account.

---

## Keep the canary after the test

Do not delete it. During the semester it is the fastest way to answer "is this a student mistake or did AWS change something?" When a student reports Bedrock failing, reproduce on the canary first.

Nothing in Bedrock bills when idle — there is no NAT Gateway or endpoint equivalent. The canary costs nothing to keep.

---

## Troubleshooting

**"No usable AWS credentials"** — `AWS_PROFILE` is unset or wrong. Run `aws sts get-caller-identity`.

**Quota values show `not found`** — AWS renamed the quota. Check manually and tell the instructor so `QUOTA_PATTERNS` in the script can be updated:

```bash
aws service-quotas list-service-quotas --service-code bedrock \
  --query "Quotas[?contains(QuotaName, 'Titan')].[QuotaName,Value]" --output table
```

**`NEEDS_PROFILE` on generation** — the script is using a bare model ID instead of an inference profile. Anthropic models on Bedrock are inference-profile only. Confirm what is available:

```bash
aws bedrock list-inference-profiles \
  --query 'inferenceProfileSummaries[?contains(inferenceProfileId, `haiku`)].[inferenceProfileId,status]' \
  --output text
```

**A quota request is denied** — reply to the case explaining it is for university coursework with a small fixed workload. Note the denial; it is a finding, because students will hit the same wall.
