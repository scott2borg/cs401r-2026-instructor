---
created: 2026-06-26
tags: [course, aws-academy, CS401R, educator-guide]
title: "AWS Academy Educator Tutorial — CS 401R"
course: CS 401R
semester: Fall 2026
status: reference
---

# AWS Academy Educator Tutorial — CS 401R

An educator's operational guide for using AWS Academy Learner Labs in CS 401R: Engineering Production AI Systems. Covers setup, student management, cost monitoring, troubleshooting, and CS 401R-specific guidance.

---

## What You Are Actually Running

Before anything else: understand the two distinct AWS Academy programs in this course and what each one does.

### Program 1 — AWS Academy Learner Lab (the sandbox)

This is the hands-on lab environment. Each enrolled student gets:
- A **sandboxed AWS account** pre-configured by AWS Academy
- A **$50 USD budget** for the duration of the class (not per lab — total)
- Access to a restricted subset of AWS services
- Sessions that run **4 hours by default** (extendable by clicking "Start Lab" again)

Students launch their lab environment from within your Canvas course via the Vocareum LMS integration. They click **Start Lab** → an AWS account spins up → they click **AWS** to open the Management Console → they work.

**The budget is the most important operational constraint in this course.** $50 sounds like a lot. For CS 401R with SageMaker, it is not. See the [Budget Reality Check](#budget-reality-check) section before Week 1.

### Program 2 — AWS Academy Curriculum Courses (the graded coursework)

These are self-paced structured courses students complete for the 10% AWS Academy grade component:
- **AWS Academy Cloud Foundations** — AWS fundamentals (required before Lab 1)
- **AWS Academy Generative AI Foundations** — LLM/generative AI on AWS

These are separate from the Learner Lab. Students complete them independently in the AWS Academy LMS. You assign them; AWS Academy grades them automatically.

**The Learner Lab and the curriculum courses are managed through the same AWS Academy LMS but are different class enrollments.**

---

## Educator Prerequisites

You must complete the following before you can create a Learner Lab class:

1. **Your institution must be an AWS Academy member.** BYU should already have this. Verify at [aws.amazon.com/training/awsacademy](https://aws.amazon.com/training/awsacademy).
2. **You must complete the "Educator Getting Started with AWS Academy" course** in the AWS Academy LMS. This is a gate — you cannot create a class without it. It takes roughly 2–3 hours.
3. **AWS recommends** completing the AWS Academy Cloud Foundations course and passing the AWS Certified Cloud Practitioner exam before facilitating a Learner Lab. Not a hard requirement, but the gap between what you know and what students will do in CS 401R is significant if you skip this.

---

## Setting Up Before the Semester

### Step 1 — Create the Learner Lab Class

1. Log in to the **AWS Academy Portal** at [awsacademy.instructure.com](https://awsacademy.instructure.com)
2. Navigate to the LMS (Canvas-based)
3. Go to **Account → Create a class**
4. For **Course**, select **AWS Academy Learner Lab**
5. Fill in:
   - **Class name**: `CS 401R Fall 2026 — Engineering Production AI Systems`
   - **Start date**: September 3, 2026
   - **End date**: December 17, 2026 (finals end date, not last day of class)
   - **Time zone**: Mountain Time
6. Submit. You will receive an email confirmation when the course is active (can take up to 24 hours).

**Set the end date to the last day of finals, not the last day of class.** Students need access through their final submission deadline (Dec 17). If the class ends early, students lose access to their lab environments and all their work.

### Step 2 — Create Classes for the Curriculum Courses

Repeat Step 1 twice, selecting:
- **AWS Academy Cloud Foundations** (assign in Week 1, due before Lab 2)
- **AWS Academy Generative AI Foundations** (assign in Week 5, due before Lab 3)

These are separate class enrollments with their own Canvas sites. Students complete them independently.

### Step 3 — Add Students to All Three Classes

Once your class is active, add students by email address.

**For each class (Learner Lab + both curriculum courses):**

1. From the Dashboard, open the class
2. In the left navigation, choose **People**
3. Click **+ People** (upper right)
4. Paste student email addresses (comma-separated or one per line)
5. Set Role: **Student**, Section: **AWS Academy Learner**
6. Click **Next** → confirm names → click **Add Users**

Students receive an invitation email to activate their account. If they do not receive it within 24 hours, check spam or re-add them.

**When to add students:** Add to the Learner Lab by September 1 (before the first class). Add to Cloud Foundations at the same time. Add to GenAI Foundations in late September when you assign it.

**Bulk add tip:** Export your Canvas enrollment roster, extract the email column, and paste the full list. You do not need to add students one by one.

### Step 4 — Require the Compliance and Security Module

Before students touch the Learner Lab, require them to complete the **"AWS Academy Learner Lab Compliance and Security"** module. This is built into the Learner Lab class and takes about 20 minutes. It covers:
- What the Learner Lab environment is and is not
- The AWS Shared Responsibility Model
- Security best practices (VPCs, IAM, storage)
- How to preserve their budget

**Make this a prerequisite for Lab 1 credit.** Students who skip it make expensive mistakes. The module is in the Learner Lab Canvas course under Modules → AWS Academy Learner Lab Compliance and Security.

---

## The Student Experience (What They See)

Understanding the student view prevents 80% of the confusion and help desk tickets you will receive.

### Launching a Session

1. Student logs into the AWS Academy LMS (separate from BYU Canvas)
2. Opens the Learner Lab course
3. Navigates to **Modules → AWS Academy Learner Lab → Launch AWS Academy Learner Lab**
4. Clicks **Start Lab** — a timer starts counting down from 4:00:00
5. Clicks **AWS** (the button turns green when the environment is ready, ~30 seconds)
6. The AWS Management Console opens — they are transparently logged into their sandboxed account

### Session Timer Mechanics

- **Default session length: 4 hours**
- The timer shows remaining time in the lab UI (top bar)
- Students can click **Start Lab** again at any time to reset the timer to 4 hours
- **The timer does not pause if they close their browser.** Resources keep running. Budget keeps depleting.
- At session end: EC2 instances are **automatically stopped**. Other resources (RDS, SageMaker endpoints, NAT Gateways, load balancers) **continue running and keep costing money.**

### Ending a Session

- **End Lab**: Stops EC2 instances. Preserves all other resources. Students return next time and their setup is still there.
- **Reset**: Deletes everything in the account. **Irreversible. All work is lost.** Students should never click Reset unless they intend to start completely over.

Tell students explicitly in Week 1: **always click "End Lab" when done. Never click "Reset" unless you mean it.**

### Spending Display

The budget gauge is visible in the Learner Lab interface (top of the instructions pane). Note: **spending data is delayed up to 8 hours.** Students may not see recent charges reflected in the display. This is a known limitation of how AWS Budgets reports.

---

## Monitoring Costs and Activity as the Educator

This is your most important ongoing operational task. Check spending weekly at minimum — weekly is not enough if you have students doing SageMaker training runs.

### Accessing the Analytics Dashboard

1. In the AWS Academy LMS, go to **Courses → Modules**
2. Click the link for the Learner Lab
3. Click the **Analytics** tab in the Vocareum interface
4. Choose the report you want:

| Report | What It Shows | When to Use |
|--------|--------------|-------------|
| **Accounts** | Spending by student per month in a grid | Weekly budget health check |
| **Lab Cost** | Detailed spending per student | When a student is burning budget fast |
| **Lab Time** | Time each student spent in the environment | Engagement tracking; debugging |
| **Learners** | Student list with status | Roster verification |

### Viewing an Individual Student's Spending

1. In the Vocareum interface, select the student from the dropdown
2. Click **Cost** — see a line-item breakdown by AWS service
3. Look for: SageMaker instances (training + endpoints), NAT Gateways, data transfer

Students burning budget fastest will typically have:
- SageMaker endpoints left running between sessions
- NAT Gateways that persist across sessions (EC2 auto-stops; NAT does not)
- Large model training jobs on ml.m5.xlarge or larger

### Accessing a Student's AWS Console

If a student needs troubleshooting help, you can log into their AWS environment directly:

1. In Vocareum, select the student
2. Click **Workarea**
3. Click **AWS** — you open the AWS Management Console as that student
4. You see exactly what they have built
5. To return to educator view: go back to the LMS → Modules

This is powerful for office hours. Instead of asking students to share screenshots, look at their actual environment.

---

## Budget Reality Check for CS 401R

**The $50 budget is tight for this course.** This is not a web app course. Students are running SageMaker.

### Estimated Costs by Lab

| Lab | Primary AWS Services                             | Estimated Cost (disciplined student) | Risk Factor |
|-----|---------------------|--------------------------------------|-------------|
| Lab 1 | VPC, S3, IAM, SageMaker Domain                   | $1–3 | Low — mostly storage |
| Lab 2 | Glue ETL, S3, SageMaker Feature Store            | $3–6 | Medium — Glue jobs bill per DPU-hour |
| Lab 3 | SageMaker Training (XGBoost), Bedrock            | $5–10 | High — training jobs on ml.m5.xlarge |
| Lab 4 | CodePipeline, SageMaker Training, Model Registry | $4–8 | High — CI/CD triggers repeat training runs |
| Lab 5 | SageMaker Endpoint (real-time)                   | $5–12 | **Very High** — endpoints left running burn $0.05+/hr |
| Lab 6 | SageMaker Endpoint, CloudWatch, Evidently drift job | $2–5 | Medium — the endpoint is the cost; the drift job is ~$0.002/run |
| Lab 7 | S3, CloudWatch, compute for analysis             | $1–3 | Low |

**Conservative total estimate: $21–47.** A disciplined student can stay within $50. A student who leaves a SageMaker real-time endpoint running for a week will exceed it well before Lab 7.

### What Kills Budgets

1. **SageMaker real-time endpoints left running.** Lab 5 deploys an endpoint. `ml.t3.medium` costs $0.05/hour. Over a week = $8.40. Over two weeks = $16.80. Students forget to delete them.
2. **NAT Gateways.** Lab 1 creates a VPC with private subnets. A NAT Gateway costs $0.045/hour + data processing = ~$32/month if left running. Students must delete it between extended breaks.
3. **Large training instance choices.** Students who choose `ml.m5.2xlarge` instead of `ml.m5.xlarge` pay 2× for training. Teach them to match instance size to task.
4. **SageMaker Studio apps not stopped.** Studio kernel apps continue billing when open. Students must explicitly shut down the kernel, not just close the browser tab.

### Mitigation Strategies

**In class on Day 1 — establish these as non-negotiable habits:**

```
After every lab session:
  1. Delete all SageMaker endpoints (they bill 24/7)
  2. Stop all SageMaker Studio kernel apps
  3. Delete NAT Gateways if not working again within 48 hours
  4. Check the budget gauge before clicking "End Lab"
  5. Verify your spend in the Learner Lab cost display
```

**Teach the pre-session checklist too:**
```
Before starting work:
  1. Check remaining budget (top of Learner Lab instructions)
  2. Use ml.t3.medium for dev/testing, ml.m5.xlarge only for final training runs
  3. Plan your session — know what you will build and approximately what it costs
```

**Your role:** Check the Accounts analytics report weekly. Flag any student over $30 by Lab 4 — they are on track to run out before Lab 7. Contact them directly. Early intervention is much easier than explaining to a student that their Lab 6 environment is gone.

### Service Restrictions in the Learner Lab

Not all AWS services are available. The Learner Lab provides a restricted environment. **Verify these before the semester:**

- ✓ S3, IAM, VPC, CloudWatch — available
- ✓ SageMaker Training Jobs, SageMaker Endpoints — available (verify instance types)
- ✓ AWS Glue — available
- ✓ AWS CodePipeline, CodeBuild — verify
- ✓ Amazon Bedrock — **verify availability and model access** (critical for Lab 3 Track B/C)
- ✓ SageMaker Feature Store — available
- ⚠ SageMaker Studio — available but has startup delays; verify domain creation works
- ✗ Some SageMaker instance types may be restricted (e.g., GPU instances)
- ✗ Some regions may be locked (environment defaults to us-east-1)

**Run Lab 1 yourself in a student-view Learner Lab session before September 3.** This is the only reliable way to discover service restrictions. Do not assume what worked in your personal AWS account will work in the sandboxed environment.

---

## Pre-Semester Checklist

Complete these before the first day of class.

### Administrative
- [x] Confirm BYU is an active AWS Academy member institution ✅ 2026-06-26
- [x] Complete "Educator Getting Started with AWS Academy" course ✅ 2026-06-26
- [x] Create Learner Lab class (Sep 3 – Dec 17) ✅ 2026-06-26
- [x] Create AWS Academy Cloud Foundations class ✅ 2026-06-26
- [x] Create AWS Academy Generative AI Foundations class ✅ 2026-06-26
- [ ] Add all students to Learner Lab class by Sep 1
- [ ] Add all students to Cloud Foundations class by Sep 1

### Technical Validation (do these in Student View)
- [ ] Launch a Learner Lab session yourself using Student View
- [ ] Run `terraform init` and `terraform plan` for a simple VPC config — verify Terraform works
- [ ] Create a SageMaker Domain via the console — confirm domain creation is not blocked
- [ ] Create an S3 bucket with the expected naming pattern
- [ ] Run a small SageMaker Training Job (XGBoost, ml.m5.xlarge, 1 minute) — confirm it works
- [ ] Create a SageMaker real-time endpoint (ml.t3.medium) — confirm it works
- [ ] Delete the endpoint — confirm deletion clears cleanly
- [ ] Check budget gauge after all the above — understand what $5–10 of work looks like
- [ ] Open the Bedrock console — verify model access (Claude Haiku or Mistral for Track B/C)

### Canvas Integration
- [ ] Link the AWS Academy Learner Lab into BYU Canvas (via LTI or direct link to Vocareum)
- [ ] Add the AWS Educate Setup Guide page to the Start Here module (already in course pipeline)
- [ ] Post the pre-semester cost hygiene habits in Week 1 module

---

## Week 1 Student Onboarding Sequence

This is the exact sequence to walk students through on the first day.

### Before Class (assign as Canvas reading)
- Complete the AWS Educate Setup Guide page in Canvas
- Accept the AWS Academy invitation email and activate their account
- Complete the Cloud Foundations Week 1 content (optional but beneficial)

### In Class — Day 1 (Sep 3, ~20 minutes)
Walk through this live with students:

1. **Log in to the AWS Academy LMS** — different from BYU Canvas. Show the URL.
2. **Locate the Learner Lab** — it is a separate course from Cloud Foundations
3. **Complete the Compliance and Security module** — require it before they leave today
4. **Launch a session** — click Start Lab, wait for green, click AWS
5. **Observe the budget gauge** — show where the $50 display is
6. **Click End Lab** — explicitly, not just closing the browser
7. **Critical rule: never click Reset** — say it twice

### Assign Lab 1 (Sep 3 — due Sep 19)
Lab 1 is specifically designed for the first two weeks because students need time to get their AWS environment configured before they can do any real work. The Lab 1 starter kit is pre-loaded in Canvas.

---

## Grading the AWS Academy Component (10%)

The 10% AWS Academy grade is for the curriculum courses, not lab work.

### Cloud Foundations (5%)
- Students complete this self-paced in the AWS Academy LMS
- AWS Academy tracks completion and module scores automatically
- View grades: AWS Academy LMS → your Cloud Foundations class → Grades
- Assign: complete by October 1 (before Lab 3)

### Generative AI Foundations (5%)
- Same structure, more advanced
- Covers LLM fundamentals, Bedrock, prompt engineering, RAG concepts
- Relevant to Lab 3 Track B and Track C
- Assign: complete by October 15

### Syncing Grades to BYU Canvas
AWS Academy does not automatically push grades to BYU Canvas. You have two options:
1. **Manual**: Export grades from AWS Academy LMS → enter in BYU Canvas gradebook
2. **LTI integration**: If BYU has configured Canvas LTI with AWS Academy, grades may sync automatically — confirm with BYU's Canvas admin

---

## Common Problems and Solutions

**Student cannot access the Learner Lab (no invitation received)**
→ Re-add them in People → check for typos in the email address
→ Have them check spam for email from `noreply@instructure.com`

**Student hit $50 budget limit before Lab 7**
→ Budget exhaustion ends their lab access — all work is inaccessible
→ Contact AWS Academy support to request a budget extension (not guaranteed)
→ Prevention: intervene when any student exceeds $30 by Lab 4

**Student accidentally clicked Reset**
→ Cannot be recovered. All resources are gone.
→ They restart from scratch; apply the same late policy as any other late lab
→ Prevention: stress the distinction between "End Lab" and "Reset" repeatedly

**SageMaker Studio takes 10+ minutes to launch**
→ Normal for cold starts — the first Studio open per session takes longer
→ Tell students: start the Studio launch first, then read the lab guide while it loads

**Bedrock model access denied**
→ Not all Bedrock models are enabled in the Learner Lab by default
→ Test before Lab 3 — if blocked, either: (a) enable them via the Bedrock console if you have admin access, or (b) adjust Lab 3 to use an available model

**Terraform cannot create resources (permissions error)**
→ The Learner Lab IAM role is scoped — not all IAM actions are permitted
→ The student is creating resources their lab role cannot create
→ Review the IAM restrictions in the Learner Lab environment; adjust the Terraform config to use only permitted actions

**Student's SageMaker domain in error state**
→ Use Workarea to log into their console directly
→ Check CloudWatch Logs for the domain creation failure reason
→ Common cause: trying to create a domain in a region or VPC configuration not supported by the Learner Lab

**Budget data not showing recent spend**
→ Normal — spending data is delayed up to 8 hours in the Learner Lab display
→ If a student says "my budget shows $5 but I've been running a training job for 3 hours," believe the training job, not the display

---

## Quick Reference

| Action | Where |
|--------|-------|
| Create a class | AWS Academy LMS → Account → Create a class |
| Add students | AWS Academy class → People → + People |
| View all student spending | AWS Academy LMS → Modules → Learner Lab → Analytics → Lab Cost |
| View one student's spending | Analytics → select student → Cost |
| Access student's AWS console | Analytics → select student → Workarea → AWS |
| Switch to Student View | Canvas course → Student View (upper right) |
| Extend class end date | Contact AWS Academy support |
| Request budget extension | Contact AWS Academy support (not guaranteed) |
| Export grades | AWS Academy LMS → Grades → Export |

**AWS Academy Support**: Available through the Help menu in the AWS Academy LMS. Response time varies — open tickets for account and budget issues at least 5 business days before they become critical.

---

## Notes Specific to CS 401R

**SageMaker Endpoints are the budget killer.** Lab 5 deploys a real-time endpoint. Make deletion explicit in the lab rubric — include a rubric item: "Endpoint deleted after testing (verified via SageMaker console screenshot)." This gives students a reason to clean up and gives TAs a grading touchpoint.

**The Learner Lab environment ≠ a real AWS account.** Students will discover documentation that describes features or console layouts that do not match what they see. This is because the Learner Lab restricts both services and IAM permissions. When students hit a wall, the first question is always: "Is this a service restriction or a misconfiguration?"

**Teach cost as a first-class engineering skill.** Lab 7 already includes a unit economics analysis. Frame cost hygiene from Week 1 as engineering discipline, not just policy compliance. Engineers who understand what their infrastructure costs make better architectural decisions. The Learner Lab budget forces that reality in a low-stakes environment.

**Run the labs before you assign them.** The NorthStar architecture was designed for a real AWS account. Some components may need adjustment for the Learner Lab environment. Completing each lab yourself before releasing it is the only way to find these issues before 40 students hit them simultaneously at 11 PM the night before the deadline.
