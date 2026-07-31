---
created: 2026-07-27
tags: [CS401R, handoff, lab-2]
purpose: Warm-start context for a fresh session beginning Lab 2 work
---

# Session Handoff — Lab 1 → Lab 2

> **How to use this:** Paste or reference this note as the first message in a new session before starting Lab 2. It captures what Lab 1 landed, the architecture Lab 2 inherits, and the open threads — so the new session starts warm instead of re-deriving everything.

---

## Source of Truth (read these first)

| What | Path |
|------|------|
| **Live reference implementation** (correct, authoritative) | `/Users/scott1/northstar-ai-platform` |
| Lab 2 spec | `Efforts/.../CS_401R_Labs/Lab_2--Data & Feature Engineering.md` |
| Master lab guide (all 7 labs) | `Efforts/.../CS_401R_Labs/CS 401R Labs.md` — Lab 2 section starts ~line 983 |
| Sample Solutions repo (TA answer key) | `Efforts/.../CS_401R_Labs/Sample Solutions/northstar-ai-platform/` |
| TA grading guides | `Efforts/.../CS_401R_Labs/Sample Solutions/Lab Solution Notes/` |

**Rule that held through Lab 1:** the live repo at `/Users/scott1/northstar-ai-platform` is authoritative. When Sample Solutions and live disagree, live wins. Sample Solutions is a *copy* maintained to match.

---

## What Lab 1 Landed (done, closed out)

1. **Reference implementation corrected** — Sample Solutions infrastructure was written for the *complex* (Lab 2+) architecture. Rewrote all 15 module/env files to match the *simplified* Lab 1 spec.
2. **TA answer key** — `Lab Solution Notes/Lab 1 - Platform Foundation (Solution).md` fully rewritten as a task-by-task grading guide matching the Lab_1--Platform Foundation.md rubric (A1–A4, B1–B5, S1–S2) with point breakdowns, common mistakes, and a deduction table.
3. **Starter Kit** — deleted `terraform/` (Option C: students build modules themselves per Task B1). Kept scenario + setup docs.
4. **AWS Educate → Free Tier migration** — course moved off AWS Educate ($150, rotating tokens) to **personal AWS Free Tier accounts ($200 credits, stable IAM keys, 6-month expiry)**. Rewrote `aws-account-setup.md` (replaces `aws-educate-setup.md`, deleted) + `Fix Credentials Problem.md`; scrubbed all $150/Educate refs across the lab guide, ADR, and solution notes.
5. **Account decision (settled):** Free Tier is the platform account. AWS Academy Learner Lab ($50, SageMaker-limited, rotating creds) is **not** used for labs — only for the required Academy prerequisite courses (Cloud Foundations, GenAI). A callout in `aws-account-setup.md` preempts the "why not Learner Lab?" question.
6. **Diagram** — `docs/northstar-lab1-platform-foundation.drawio` (validated, 7-step legend).

---

## Architecture Lab 2 Inherits and Extends

Lab 1 was deliberately simple. **Lab 2 adds the complexity that was stripped out.** This is the key delta to get right:

| Dimension | Lab 1 (built) | Lab 2 (adds) |
|-----------|---------------|--------------|
| Subnets | 1 public (`10.0.100.0/24`, us-east-1a) | **Private subnet(s) + NAT Gateway** for egress |
| SageMaker Studio | In public subnet | **Moves to private subnet** (`app_network_access_type = VpcOnly`) |
| IAM roles | 1 (`MLEngineer`) | **+ DataEngineer** (trust `glue.amazonaws.com`) **+ ModelMonitor** |
| S3 | 1 bucket, 4 prefixes (`raw/ processed/ features/ artifacts/`) | **Feature Store / Feature Groups**; possibly lifecycle rules on `raw/`, `processed/` |
| Services | VPC, S3, IAM, SageMaker Domain | **+ AWS Glue** (ETL), **Feature Store**, VPC endpoints (S3 gateway; maybe SageMaker interface) |
| Cost | ~$3–6 | ~$6–10 (NAT Gateway is the new cost driver — **destroy between labs**) |

**Important:** the *old* Sample Solutions code (pre-Lab-1-fix) already implemented much of this Lab 2 architecture — private subnets, NAT, 3 roles, Feature Store. When building Lab 2, the git history of `/Users/scott1/northstar-ai-platform` or the pre-fix patterns may be a useful starting reference — but verify against `Lab_2--Data & Feature Engineering.md`, don't assume.

---

## Data Engineering Context (Lab 2 core)

- Data schemas: `Starter Kits/Lab 1/northstar-data-schema.md` and `Lab_2--Data & Feature Engineering.md` starter kit section
- Feature Store event-time gotcha (flagged in old notes): event_time feature must be `Fractional` (Unix epoch), NOT `String` (ISO 8601) — `PutRecord` fails silently otherwise. Confirm this lands in Lab 2's common-mistakes.
- LocalStack: Community edition does **not** support SageMaker or Feature Store. Lab 1 used a separate `environments/local/` that skips SageMaker. Lab 2 must decide what's LocalStack-validatable (Glue partial, S3, IAM) vs. real-AWS-only.

---

## Open Threads / Watch Items

- [ ] Lab 2 Sample Solutions + TA grading guide don't exist yet — will need the same treatment Lab 1 got (build against live repo, then write answer key matching the Lab_2 rubric).
- [ ] Confirm Lab 2's rubric structure (task IDs + point values) before writing the grading guide — mirror it exactly, like Lab 1.
- [ ] NAT Gateway cost discipline: rubric should gate on `terraform destroy` after submission (raised as a general recommendation in Lab 1 discussion; verify it's enforced in Lab 2).
- [ ] `Notes About Lab Creation.md` exists in the labs folder — check it for any Lab 2 authoring intent before starting.

---

## Working Conventions (carry forward)

- Terraform vars use `var.project` / `var.environment` (NOT `var.project_name` — that was the stale pattern).
- No hardcoded `"northstar"` literals in modules; account-ID-suffixed bucket names.
- Sample Solutions is kept in sync with live; live is authoritative.
- Blunt, direct communication; challenge bad calls; one recommendation not ten options (per vault CLAUDE.md).
