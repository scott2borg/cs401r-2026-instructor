# Pre-Lab 4 — SageMaker Training Quota Setup

**Assigned:** Thu Sep 17 (with Lab 2, alongside Pre-Lab 3) | **Due:** Wed Sep 30
**Effort:** ~20 minutes of your time, then waiting on AWS
**Counts toward:** Lab 4 Task 2 (CI/CD Pipeline). The pipeline cannot run without it, so it is verified as part of that rubric item rather than scored separately.

Lab 4's pipeline runs a **SageMaker Training Job**. On a new AWS account, the on-demand training quota for every instance family is **zero**, so that job fails before it starts. This is not a billing limit you can spend your way past — there is no capacity allocated to your account at all until you ask for some.

Do this while you are working on Lab 2. Lab 4 is not assigned until **Oct 15**, and that is exactly the point: you are filing six weeks early because the approval time is not yours to control.

## Why this is a pre-lab and not a line in Lab 4

You have already seen this shape once, in Pre-Lab 3. Bedrock entitlement and compute quota are the same class of problem: **a dependency owned by someone else, with a lead time you cannot compress, discovered too late by teams who assumed availability.**

The lesson is not "AWS makes you fill in forms." It is that capacity is a procurement item. A platform team that discovers its training fleet is unallocated the week of a launch has made a planning error, not hit bad luck. Filing early, with a defensible number, is the job.

---

## What "no quota" actually looks like

Your pipeline will get as far as creating the training job and then stop:

```
ResourceLimitExceeded: The account-level service limit 'ml.m5.large for
training job usage' is 0 Instances, with current utilization of 0 Instances
and a request delta of 1 Instances. Please use AWS Service Quotas to request
an increase for this quota.
```

This is a clear error, which makes it one of the friendlier failures in this course. The trap is not the message — it is checking your quota *wrongly* and concluding you already have it.

---

## The trap: `get-service-quota` vs `get-aws-default-service-quota`

There are two different questions, and they have different answers:

| Command | Answers |
|---|---|
| `get-service-quota` | **What is applied to MY account right now** |
| `get-aws-default-service-quota` | **What a brand-new account starts with** |

An account that has been used for a while accrues elevated applied quotas quietly — from previous increase requests, sometimes from usage patterns. The course's reference account reports an applied quota of **15** for `ml.m5.large` training while the AWS default is **0**. An instructor checking `get-service-quota` on that account would conclude the lab works fine and ship you something that fails on every student machine. That is not hypothetical; it is why this pre-lab exists.

**Check both. If they differ, the smaller one is what a new account gets.**

> **A second trap, worth knowing generally.** `aws service-quotas list-service-quotas --query ...` applies `--query` **per page** and silently returns partial results — you can search for a quota, get nothing back, and wrongly conclude it does not exist. Use `get-service-quota` with an explicit quota code, or a boto3 paginator. This produced a false finding on this project on 2026-07-31.

---

## Step 1 — See what you actually have

```bash
# What a new account starts with (expect 0)
aws service-quotas get-aws-default-service-quota \
  --service-code sagemaker --quota-code L-611FA074 \
  --query 'Quota.{Name:QuotaName,Default:Value}' --output json

# What is applied to your account (probably also 0)
aws service-quotas get-service-quota \
  --service-code sagemaker --quota-code L-611FA074 \
  --query 'Quota.{Name:QuotaName,Applied:Value}' --output json
```

`L-611FA074` is **`ml.m5.large` for training job usage** — the instance type Lab 4's pipeline requests.

## Step 2 — Request the increase

```bash
aws service-quotas request-service-quota-increase \
  --service-code sagemaker --quota-code L-611FA074 \
  --desired-value 2
```

**Ask for 2, not 20.** One concurrent training job is all Lab 4 needs; 2 gives you room to leave a job running while you start another. A modest, justified request is also more likely to be approved quickly than a large unexplained one — and "what do you actually need?" is the question Step 4 asks you to answer.

Track it:

```bash
aws service-quotas list-requested-service-quota-change-history-by-quota \
  --service-code sagemaker --quota-code L-611FA074 \
  --query 'RequestedQuotas[].{Status:Status,Requested:DesiredValue,Case:CaseId}' \
  --output table
```

Status moves `PENDING` → `CASE_OPENED` → `APPROVED` (or `DENIED`). **AWS reviews on its own schedule.** This is why you are doing it in September.

## Step 3 — Know your fallback

If your increase is still pending when you need it, **spot training has non-zero defaults for 12 instance types**. `ml.m5.large` spot (`L-29688C85`) has an AWS default of **4** — verified 2026-08-04 — against **0** for on-demand. Spot instances can be interrupted, so a spot training job needs checkpointing and retry handling to be safe — but for a job that trains in under two minutes on 10,000 rows, interruption risk is low.

Check it:

```bash
aws service-quotas get-aws-default-service-quota \
  --service-code sagemaker --quota-code L-29688C85 \
  --query 'Quota.{Name:QuotaName,Default:Value}' --output json
```

If you take this path, say so in your Lab 4 submission and note what you changed.

## Step 4 — Verify, do not assume

Do not report "I clicked request increase." Report the state:

```bash
aws service-quotas get-service-quota \
  --service-code sagemaker --quota-code L-611FA074 \
  --query 'Quota.Value' --output text
```

A non-zero number here is the only evidence that matters.

---

## Cost

**Requesting a quota costs nothing.** A quota is permission to launch capacity, not capacity itself — an approved quota of 2 with no jobs running bills $0.00. You are billed only for training jobs you actually run, at roughly **$0.10–0.30 per run** on `ml.m5.large` for this course's dataset.

The relevant cost discipline for training jobs is that they **terminate on their own** when training finishes, which is what makes them safe compared to endpoints. An endpoint bills until you delete it; a training job does not.

---

## Deliverable

Submit `docs/training-quota-verification.txt` **by Wed Sep 30**, containing:

1. The Step 1 output showing the AWS **default** and your **applied** value, side by side
2. The Step 2 request status output, or the Step 4 output if it has already been approved
3. One short paragraph: what value you requested, why that number, and what your fallback is if it is not approved before Lab 4 opens

Point 3 is the real assignment, and it is the same skill Pre-Lab 3 asks for. A capacity request you cannot justify is a guess, and a plan with no fallback is not a plan.
