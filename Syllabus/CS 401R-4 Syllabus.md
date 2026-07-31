---
created: 2026-06-23
tags: [course, syllabus, CS401R, AI-engineering]
title: "CS 401R: Engineering Production AI Systems"
course: CS 401R
semester: Fall 2026
status: draft
updated: 2026-06-23
---

# CS 401R: Engineering Production AI Systems
## Brigham Young University — Fall 2026

**Instructor:** Scott Toborg
**Email:** scott@toborg.com
**Meeting Times:** Tuesday & Thursday, 2:00-3:15 pm
**First Day of Class:** Thursday, September 3, 2026
**Last Day of Class:** Thursday, December 10, 2026
**Final Exam:** Wednesday, December 16, 2026, 3:00--6:00 pm
**Credits:** 3
**Format:** In-person lecture

## Course Description

This course teaches engineers how to build, ship, and operate AI systems at production scale inside real enterprises. We move from theory to working systems: you will design platform architectures, build data and model pipelines, rigorously evaluate AI outputs, deploy with confidence, and then operate those systems with the economic, governance, and reliability discipline that enterprise stakeholders demand.

The course is organized around a single running case study — **NorthStar Retail** — a fictional but architecturally realistic enterprise AI deployment. Every lab builds one layer of that system. By the end of the semester, you will have designed and prototyped a complete, end-to-end enterprise AI platform on AWS.

The highlight of the course is the team project. You will organize into teams of 3-4 students and build an end-to-end AI System of your choice. This is where you can think big and create something you'd be proud of showing off to potential employers, investors, graduate search committees, etc. Some past student projects have led to full commercial deployments and inspired follow-on startups. 

Primary text: *Engineering the AI Enterprise: Orchestrating Strategy, Product, and Execution* (Toborg, 2026) — Parts 3 (Build) and 4 (Operate). Draft chapters will be distributed via Canvas. Please do not share outside the course — this is pre-publication copyrighted material.


## Prerequisites

- CS 240 or equivalent (Advanced Software Construction)
- CS 270 or equivalent (Introduction to Machine Learning)
- Recommended courses: CS 301R (Agentic Systems), CS 329 (QA & DevOps), CS 452 (Data Engineering), CS 574 (Transformers)
- Strong experience in Python and working knowledge of SQL
- Familiarity with cloud computing concepts (AWS experience helpful but not required)


## Learning Objectives

By the end of this course, students will be able to:

1. Design a production-grade AI platform on AWS, including infrastructure as code, feature stores, and model registries.
2. Build end-to-end data and feature engineering pipelines that can handle real-world distribution shifts.
3. Train, fine-tune, and deploy models across the full development spectrum — from prompt engineering to RAG to custom training to agent orchestration.
4. Apply XOps discipline (DataOps, MLOps, LLMOps, AgentOps) to automate the model lifecycle.
5. Implement CI/CD pipelines for AI systems with appropriate deployment strategies (e.g., A/B, canary, blue/green, shadow).
6. Evaluate AI system quality rigorously across predictive models, generative systems, and autonomous agents.
7. Operate AI systems in production: monitoring, drift detection, reliability engineering, and incident response.
8. Measure and communicate AI business value to both engineering and executive audiences.
9. Manage AI costs using FinOps discipline.
10. Design governance frameworks that scale to agentic AI systems.


## Required Materials and Costs

**Primary Text:** *Engineering the AI Enterprise* draft chapters (Parts 3 & 4), distributed as PDFs on Canvas. No charge. 

**AWS Environment:** Students work in AWS for all labs. Students will be enrolled in AWS Academy to get access to some free services. There are also other free training through Educate and Skillsbuilder. Students should also sign up for a free-tier account—see Canvas for setup instructions.

**No other textbook required.** Supplementary references are embedded in each chapter and linked on Canvas. These will be publicly available or accessible through the BYU Library. 

**Total Costs:** While we will do everything we can to minimize costs, there will be some unavoidable AWS charges estimated at $50-$100. You will be responsible for all charges. If you rack up unintended charges, AWS is usually very forgiving (this has happened to me). You will need a credit card to sign up for an AWS account. 


## Grading

| Component      | Weight   | Notes                        |
| -------------- | -------- | ---------------------------- |
| Labs (7 total) | 49%      | 7% each (evenly weighted)    |
| Final Project  | 30%      | Team-based                   |
| AWS Academy    | 10%      | Foundation and GenAI courses |
| Quizzes        | 11%      | In-class                     |
| **Total**      | **100%** |                              |

**Late Policy:** Labs lose 10% per day late. Contact me *before* the deadline if you have a documented emergency — not after.

**Extra Credit:** TBD up to 5% of grade.

**Grade Scale:** A 93+, A- 90–92, B+ 87–89, B 83–86, B- 80–82, C+ 77–79, C 73–76, below 73 see instructor.

## Lab Overview — NorthStar Retail Arc

All 7 labs use the **NorthStar Retail** case study. Each lab is self-contained but contributes to a complete AI platform. Labs are assigned in class (Thursdays) and due **Saturday at midnight**, approximately two weeks after assignment.

| Lab | Topic | Assigned | Due |
|-----|-------|----------|-----|
| **Lab 1** | Platform Foundation | Thu Sep 3 | Sat Sep 19 |
| **Lab 2** | Data & Feature Engineering | Thu Sep 17 | Sat Oct 3 |
| **Lab 3** | Model Development | Thu Oct 1 | Sat Oct 17 |
| **Lab 4** | CI/CD Pipeline | Thu Oct 15 | Sat Oct 31 |
| **Lab 5** | Deployment & Scaling | Thu Oct 29 | Sat Nov 14 |
| **Lab 6** | Monitoring & Reliability | Thu Nov 12 | Sat Nov 28 |
| **Lab 7** | Metrics, Economics & Business Value | Thu Nov 19 | Tue Dec 1 ⚠️ |

> ⚠️ Lab 7 is due **Tuesday Dec 1 at midnight** — This is the only exception to the Saturday convention given the Dec 10 end-of-semester constraint. All remaining class sessions after Dec 1 are devoted to the team project.

### Lab Descriptions

**Lab 1 — Platform Foundation**
Stand up the NorthStar AWS platform skeleton: SageMaker domain, S3 bucket structure, IAM roles, VPC configuration. Starter code is included. Deliverable: a reproducible platform deployment with a written architecture decision record (ADR).

**Lab 2 — Data & Feature Engineering**
Build NorthStar's customer data pipeline: raw ingestion from simulated sources, Glue transformation jobs, and a SageMaker Feature Store with at least three engineered features. Deliverable: TerraForm script, working pipeline + data lineage diagram.

**Lab 3 — Model Development**
Implement a RAG system for NorthStar's customer support assistant. Requires a prompt evaluation harness. Deliverable: deployed model + evaluation report.

**Lab 4 — CI/CD Pipeline**
Implement a CI/CD pipeline using GitHub Actions or AWS CodePipeline that runs automated tests, promotes a model through staging, and registers it in the SageMaker Model Registry with appropriate stage gates. Deliverable: working pipeline + pipeline health dashboard.

**Lab 5 — Deployment & Scaling**
Deploy the NorthStar recommendation model to a SageMaker endpoint using canary deployment. Configure auto-scaling policies and a rollback trigger. Deliverable: deployed endpoint + load test results + rollback runbook.

**Lab 6 — Monitoring & Reliability**
Implement CloudWatch, MLflow or Weights and Biases dashboards for NorthStar covering data drift, model performance degradation, and latency. Write an incident response runbook for three failure scenarios. Deliverable: dashboards + runbook + one simulated incident walkthrough.

**Lab 7 — Metrics, Economics & Business Value**
Instrument the NorthStar system end-to-end: build the Metric Pyramid linking model outputs to business KPIs, produce a FinOps cost attribution report (cost per recommendation, total platform spend, build-vs-buy comparison), and draft a shared scorecard bridging engineering and executive views. Deliverable: written report + supporting dashboard or spreadsheet artifacts.


## Week-by-Week Schedule

> **Reading** = chapter sections due *before* the listed class session.
> All chapter titles refer to *Engineering the AI Enterprise*, Parts 3 & 4.


#### Week 1
**Thu Sep 3** *(single session — first day)*

| Date | Topic | Reading Due |
|------|-------|------------|
| Thu Sep 3 | Course introduction. What it means to engineer an AI enterprise. The Build → Operate arc. NorthStar Retail introduced — the case that runs the entire semester. | None |

> 📋 **Lab 1 Assigned — Thu Sep 3** → **Due Sat Sep 19, midnight**
> *(Lab 1 is a platform setup lab — students can begin AWS environment configuration immediately. The Week 2 platform lectures support completion of the lab.)*


#### Week 2 — AI Systems Development Lifecycle + AI Platform I
**Tue Sep 8 | Thu Sep 10**

| Date | Topic | Reading Due |
|------|-------|------------|
| Tue Sep 8 | **AI Systems Development Lifecycle (AISDLC)** — the unifying framework for the course. Why AI development is different. Lifecycle phases, stage gates, and artifacts. How the AISDLC maps to real enterprise practice. | *AI Systems Development Lifecycle* — Why AI Development Is Different; The AISDLC at a Glance; Lifecycle Phases; Stage Gates and Artifacts |
| Thu Sep 10 | **AI Platform & Cloud Architecture I** — What is an AI platform? Reference architectures for enterprise AI. Core platform components. The compound-returns argument for platform investment. | *AI Platform & Cloud Architecture* — Motivation through Core Platform Components |


#### Week 3 — AI Platform II + Data & Feature Engineering I
**Tue Sep 15 | Thu Sep 17**

| Date | Topic | Reading Due |
|------|-------|------------|
| Tue Sep 15 | **AI Platform & Cloud Architecture II** — AWS infrastructure for AI. SageMaker domain and ecosystem. Infrastructure as Code with Terraform. Modularity, vendor strategy, and cost governance during build. NorthStar platform architecture walkthrough. | *AI Platform & Cloud Architecture* — AWS Infrastructure through Key Takeaways |
| Thu Sep 17 | **Data & Feature Engineering I** — Why data engineering for AI is different. Three ingestion patterns. Data transformation and operational quality. The Zillow Offers cautionary tale. AWS reference architecture. | *Data & Feature Engineering* — Motivation through Feature Engineering |

> 📋 **Lab 2 Assigned — Thu Sep 17** → **Due Sat Oct 3, midnight**


#### Week 4 — Data & Feature Engineering II + Model Development I
**Tue Sep 22 | Thu Sep 24**

| Date | Topic | Reading Due |
|------|-------|------------|
| Tue Sep 22 | **Data & Feature Engineering II** — Feature stores and training/serving skew. Data lineage and provenance. Governance, privacy, and security. Airbnb Zipline case study. | *Data & Feature Engineering* — Feature Stores through Key Takeaways |
| Thu Sep 24 | **Model Development I** — The development spectrum: choosing your approach. Prompt engineering as an engineering discipline. Training custom models. Fine-tuning foundation models. Reproducibility and model versioning. | *Model Development* — Motivation through Fine-Tuning Foundation Models; Reproducibility and Model Versioning |


#### Week 5 — Model Development II & III
**Tue Sep 29 | Thu Oct 1**

| Date | Topic | Reading Due |
|------|-------|------------|
| Tue Sep 29 | **Model Development II — RAG** — Retrieval-Augmented Generation architecture. Chunking strategies, embedding, reranking. Evaluation of RAG pipelines. When RAG beats fine-tuning and when it doesn't. | *Model Development* — Retrieval-Augmented Generation section |
| Thu Oct 1 | **Model Development III — Agents** — Agent design and orchestration. Tool use, memory, planning loops. Failure modes unique to agentic systems. When to use agents vs. simpler approaches. Morgan Stanley AI at Scale case study. | *Model Development* — Agent Design and Orchestration; AWS Architecture; Key Takeaways |

> 📋 **Lab 3 Assigned — Thu Oct 1** → **Due Sat Oct 17, midnight**


#### Week 6 — XOps I & II
**Tue Oct 6 | Thu Oct 8**

| Date | Topic | Reading Due |
|------|-------|------------|
| Tue Oct 6 | **XOps I — DataOps & MLOps** — XOps as the operational foundation of enterprise AI. DataOps: building the data foundation. MLOps: automating the model lifecycle. Where most teams fall short. | *The XOps Stack* — Motivation through MLOps |
| Thu Oct 8 | **XOps II — LLMOps & AgentOps** — Operational discipline for foundation model systems. Governance for systems that act. AWS reference XOps architecture. Building XOps capability in your organization. | *The XOps Stack* — LLMOps through Key Takeaways |


#### Week 7 — Testing & Evaluation
**Tue Oct 13 | Thu Oct 15**

| Date | Topic | Reading Due |
|------|-------|------------|
| Tue Oct 13 | **Testing & Evaluation I** — The testing hierarchy for AI systems. Evaluating predictive models: metrics, baselines, holdout strategy. Production readiness criteria. Google Model Cards case study. | *Testing and Evaluation* — Motivation through Evaluating Predictive Models; Production Readiness Criteria |
| Thu Oct 15 | **Testing & Evaluation II** — Evaluating generative AI systems. Evaluating agent systems. Fairness, robustness, and safety evaluation. What "passing" a test actually means at enterprise scale. | *Testing and Evaluation* — Evaluating Generative AI through Key Takeaways |

> 📋 **Lab 4 Assigned — Thu Oct 15** → **Due Sat Oct 31, midnight**


#### Week 8 — Continuous Delivery
**Tue Oct 20 | Thu Oct 22**

| Date | Topic | Reading Due |
|------|-------|------------|
| Tue Oct 20 | **Continuous Delivery I** — CI/CD for AI: what is genuinely different. Continuous integration for AI: testing data, models, and infrastructure in the pipeline. Spotify Hendrix case study. | *Continuous Delivery* — Motivation through Continuous Integration |
| Thu Oct 22 | **Continuous Delivery II** — Continuous delivery for AI. Deployment strategies. Infrastructure automation. Pipeline health and measurement. | *Continuous Delivery* — Continuous Delivery through Key Takeaways |


#### Week 9 — Deployment & Scaling
**Tue Oct 27 | Thu Oct 29**

| Date | Topic | Reading Due |
|------|-------|------------|
| Tue Oct 27 | **Deployment & Scaling I** — Deployment strategies: canary, blue/green, shadow, feature flags. Serving infrastructure at scale. Lyft ML Platform case study. | *Deployment and Scaling* — Motivation through Serving Infrastructure |
| Thu Oct 29 | **Deployment & Scaling II** — Scaling AI workloads from pilot to full production. Resilience and reliability at scale. Organizational readiness and the operational handoff. | *Deployment and Scaling* — Scaling AI Workloads through Key Takeaways |

> 📋 **Lab 5 Assigned — Thu Oct 29** → **Due Sat Nov 14, midnight**


#### Week 10 — Security, Privacy & Compliance
**Tue Nov 3 | Thu Nov 5**

| Date | Topic | Reading Due |
|------|-------|------------|
| Tue Nov 3 | **Security, Privacy & Compliance I** — The AI security surface. Data security. AI-specific threats: prompt injection, model inversion, adversarial inputs. Security gates in the development lifecycle. AWS infrastructure security. | *Security, Privacy & Compliance* — Motivation through AI-Specific Threats; Infrastructure Security |
| Thu Nov 5 | **Security, Privacy & Compliance II** — Privacy engineering. Regulatory compliance frameworks (GDPR, CCPA, EU AI Act). **Bridge: what Build hands to Operate.** The mindset shift from construction to stewardship. | *Security, Privacy & Compliance* — Privacy Engineering through Key Takeaways |


#### Week 11 — Metrics, Benchmarks & Guardrails + Monitoring & Observability
**Tue Nov 10 | Thu Nov 12**

| Date | Topic | Reading Due |
|------|-------|------------|
| Tue Nov 10 | **Metrics, Benchmarks & Guardrails** — The four performance dimensions. Leading vs. lagging indicators. Guardrail metrics: encoding risk tolerance as numbers. Experimentation and online validation. Stakeholder views. | *Metrics, Benchmarks & Guardrails* — full chapter |
| Thu Nov 12 | **Monitoring, Observability & Model Lifecycle Management** — What monitoring covers in an AI system. Drift detection: the core monitoring problem. Alerting architecture and escalation paths. Observability for generative AI and agent systems. Model lifecycle management. | *Monitoring, Observability & Model Lifecycle Management* — full chapter |

> 📋 **Lab 6 Assigned — Thu Nov 12** → **Due Sat Nov 28, midnight**


#### Week 12 — Reliability Engineering + AI Economics
**Tue Nov 17 | Thu Nov 19**

| Date | Topic | Reading Due |
|------|-------|------------|
| Tue Nov 17 | **Reliability Engineering** — SRE principles applied to AI systems. AI-specific failure modes. AWS reliability architecture. Incident response process. Runbook design and rollback procedures. | *Reliability Engineering* — full chapter |
| Thu Nov 19 | **AI Economics** — The full cost structure of enterprise AI. Cost estimation as a design discipline. FinOps for AI. Build vs. buy vs. subscribe. Cost-performance tradeoffs and governance. | *AI Economics* — full chapter |

> 📋 **Lab 7 Assigned — Thu Nov 19** → **Due Tue Dec 1, midnight** *(exception to Saturday convention)*


#### Week 13 — Measuring Business Value + Team Project Launch
**Tue Nov 24 | ~~Thu Nov 26 — NO CLASS (Thanksgiving)~~**

| Date | Topic | Reading Due |
|------|-------|------------|
| Tue Nov 24 | **Measuring Business Value** — The Metric Pyramid: the central discipline of value translation. The four value dimensions. Attribution: the hard problem. Measuring value for LLM and agentic systems. Shared scorecards. Communicating AI value to non-technical stakeholders. **Team project introduced — teams finalized this week.** | *Measuring Business Value* — full chapter |
| ~~Thu Nov 26~~ | *No class — Thanksgiving* | — |


### TEAM PROJECT SESSIONS

*Lab 7 is due Tue Dec 1. All remaining class sessions (Weeks 14–15) are devoted to team project work. Chapters on AI Governance and Closing the Loop are assigned as readings; content is discussed in workshop format as it connects to project work.*



#### Week 14 — Team Project Workshop I
**Tue Dec 1 | Thu Dec 3**

| Date | Topic | Reading Due |
|------|-------|------------|
| Tue Dec 1 | **Project Workshop** — Team check-ins. Architecture and design review. Q&A on AI Governance content. | *AI Governance* — full chapter (read before class) |
| Thu Dec 3 | **Project Workshop** — Team working session. Instructor and TA available for consults. Q&A on Closing the Loop content. | *Closing the Loop* — full chapter (read before class) |

---

#### Week 15 — Team Project Workshop II + Final Thoughts
**Tue Dec 8 | Thu Dec 10** *(last week of class)*

| Date | Topic | Reading Due |
|------|-------|------------|
| Tue Dec 8 | **Project Workshop** — Final working session. Team presentations dry run (optional). Open Q&A. | None |
| Thu Dec 10 | **Final Thoughts** — Where AI engineering goes next. What separates the engineers who shape this from those who follow it. How to keep learning after this course ends. | None |


## Final Project

**Team size:** 3-4 students
**Due:** Thu Dec 17 (last day of finals), 11:59 PM
**Teams finalized:** TBD, by mid-term. 

**Prompt:** Design a production AI system for a company and use case of your choosing. Your deliverable is a technical design document covering all course layers: platform architecture, data and feature pipeline, model development approach, XOps plan, deployment strategy, operating model (monitoring + reliability), economic justification, and governance framework.

**Presentations:** During finals week. Each team presents for 15 minutes + 5 minutes Q&A. Schedule posted on Canvas by Dec 1.

**Project Grading Rubric:**

| Dimension                                   | Weight |
| ------------------------------------------- | ------ |
| Innovation and technical depth              | 40%    |
| Integration and coherence across all layers | 30%    |
| Business/executive communication quality    | 20%    |
| Presentation                                | 10%    |

## Course Policies

**Attendance:** Not graded, but this course moves fast. We will need to make some changes on the fly. There will be a 5-point quiz at the beginning of each class. No make-ups if you miss class. But, I will have extra credit available, if needed. 

**AI Tools:** You are encouraged to master the use of AI coding assistants (Codex, Claude, etc.) for all work. You must understand and be able to explain everything you submit. If you cannot explain it, you may not get credit for it.

**Academic Honesty:** BYU Honor Code applies. Working together on Labs is highly encouraged. Just copying lab solutions from other students before the Saturday midnight due date is academic dishonesty. 

**Office Hours:** Tues and Thur after class.  Email me ahead of time for appointments, if possible. 

*Syllabus subject to change. All updates announced on Canvas.*
