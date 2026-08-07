---
lecture: L01
title: Course Introduction
date: Thursday, September 3, 2026
week: 1
arc: Build
reading_due: None
lab_assigned: "Lab 1 — Platform Foundation (Due: Sat Sep 19)"
slides_target: 16
---

# L01: Introduction
**Thursday, September 3, 2026 | CS 401R: Engineering Production AI Systems | Fall 2026**

> This course is about engineering production AI systems — not studying them, not demoing them, but building and operating them at enterprise scale.

**Lab Assigned:** Lab 1 — Platform Foundation (Due Sat Sep 19, midnight)

---

## Slide 1 — Title
**Layout:** Left dark panel (course/instructor info) + full right panel visual

**Content:**
- CS 401R-4: Engineering Production AI Systems
- Fall 2026 · Lecture 01 of 26
- Dr. Scott T. Toborg · Brigham Young University
- Thursday, September 3, 2026

**Figure:** *Enterprise AI system topology.* A dense network graph on a dark navy background showing 60+ interconnected nodes. Three prominent gold/amber hub nodes are labeled "Churn Model," "Offer Generator," and "Customer Agent." Smaller blue nodes represent data flows, microservices, feature stores, monitoring, and infrastructure. Lines between nodes vary in thickness (data volume) and color (data type). The image communicates complexity, scale, and the "living system" nature of production AI — not a model, not a demo, a running system.

**Notes:** "What you're looking at is what a production AI system looks like from the inside — not the model, but the whole system. Three AI systems, one shared platform, hundreds of moving parts, all running in real time. This course is about building that."

---

## Slide 2 — The State of Enterprise AI
**Layout:** Two large stat panels side by side + one headline stat above

**Content:**
- Headline: 85% of enterprise AI pilots never reach production (Gartner, 2024)
- Left panel: *The Deployment Gap* — organizations spend ~$500B/year on AI; only a fraction reaches customers
- Right panel: *The Operations Gap* — teams that deploy AI spend 80% of their time on maintenance, not improvement
- Bottom: "The engineers who close these gaps are the most valuable people in the room"

**Figure:** *Split bar chart.* Left bar: "AI Projects Started" (100%). Right bars, decreasing in height: "Reach Pilot" (60%), "Reach Staging" (35%), "Reach Production" (15%), "Still Running at 12 Months" (8%). Bars colored from light blue to deep navy. A red dashed line at 15% labeled "The Production Wall." Clean, white background, large readable labels.

**Notes:** The 85% failure rate is the opening argument for why this course needs to exist. Don't editorialize — let the numbers speak. Students should feel the weight of the problem before you tell them they're going to solve it. "How many of you have built something that worked in a demo but never made it to users?" "That's what this course fixes."

---

## Slide 3 — What This Course Is — and Isn't
**Layout:** Two-column contrast with clear section headers

**Content:**
**This course is NOT:**
- A machine learning theory course (no proofs, no gradient descent derivations)
- A data science course (no weeks spent on EDA or feature selection for its own sake)
- A tool tutorial (we use AWS, but this is not an AWS certification course)

**This course IS:**
- An engineering course: how do you BUILD production AI systems?
- An operations course: how do you RUN them reliably, cheaply, accountably?
- A judgment course: how do you make the right architectural and organizational decisions?
- The skill gap that separates AI engineers who ship from those who prototype

**Figure:** *Two-column visual contrast.* The left column, labeled "Demo / Prototype," shows a simple notebook → model path. The right column, labeled "Production System," shows a full system diagram: data ingestion → feature engineering → training pipeline → evaluation gates → deployment → monitoring → governance → feedback loop. The right column is 4× more complex. No numbers, just structural complexity visible at a glance.

**Notes:** Most CS students arrive expecting either a theory course or a tools tutorial. This course is neither. It is an engineering discipline course. The prototype→production gap is not a tools problem — it's a process, architecture, and judgment problem. "By the end of this course, you will have opinions about things that most engineers only encounter after their first production failure."

---

## Slide 4 — Why AI Engineering Is Different from Software Engineering
**Layout:** Four-quadrant grid, each quadrant a distinct color with title + one-sentence explanation

**Content:**
- **Quadrant 1 — Probabilistic, not deterministic:** "It works" is not binary. You cannot write a unit test that verifies correctness — only performance thresholds against which the system is measured.
- **Quadrant 2 — Data is a first-class dependency:** A label-encoding error in a pipeline is a production bug. Data quality is an engineering responsibility, not an analytics afterthought.
- **Quadrant 3 — Models degrade over time:** Deployment is the beginning, not the end. Concept drift, data drift, and distribution shift are real, frequent, and expensive to ignore.
- **Quadrant 4 — Experimentation is inherent:** You cannot commit to a model's delivery date. Gates replace deadlines: "proceed when criteria are met," not "ship on Friday."

**Figure:** *2×2 quadrant diagram.* Each quadrant has a distinct background (navy, teal, amber, slate), a large icon in the corner (dice for probabilistic, database for data, clock with a down-arrow for drift, flask for experimentation), and a 2-3-word label in large type. Sub-text in smaller type below each label. Clean grid lines, no gradients.

**Notes:** This is the intellectual foundation of the entire course. Every design decision in the AISDLC, every stage gate, every architectural choice we make this semester traces back to one of these four properties. Ask students: "What happens when your feature store goes down? When the model's training data no longer reflects production reality?" These questions don't exist in traditional software.

---

## Slide 5 — The Build → Operate Arc
**Layout:** Horizontal timeline with two major sections, labs marked as milestones

**Content:**
**BUILD (Weeks 1–10):**
- AISDLC · Platform & Cloud · Data Engineering · Model Development
- XOps · Testing & Evaluation · CI/CD · Deployment · Security/Privacy

**OPERATE (Weeks 11–13):**
- Metrics & Guardrails · Monitoring & Observability · Reliability Engineering
- AI Economics · Measuring Business Value

**Bridge (Week 10):** Security/Privacy II — where Build formally hands off to Operate

**Team Project (Weeks 14–15):** Apply both arcs to a system of your own design

**Figure:** *Horizontal arc timeline.* A sweeping arc from left (Week 1) to right (Week 15). The left ~65% of the arc is labeled "BUILD" in blue; the right ~35% is labeled "OPERATE" in teal. Seven gold diamond markers along the arc indicate lab assignments. A vertical dashed line at Week 10 labeled "Bridge: Build → Operate." Below the arc: a thin row of week numbers. Above the arc: lecture topics in small type at each position. The overall visual feels like a project roadmap.

**Notes:** This arc is the spine of the course. Every lecture and every lab fits into one of these two arcs. "The bridge between Build and Operate is the most commonly skipped step in enterprise AI. Teams build something, declare victory, and hand it off to someone else to operate — only for it to fail. You're going to learn to avoid that."

---

## Slide 6 — NorthStar Retail: The Case That Runs the Semester
**Layout:** Left panel (company profile) + right panel (three-system architecture diagram)

**Content:**
**Company Profile:**
- Fictional specialty retailer, 400 stores across North America
- Annual revenue ~$3.2B, growing e-commerce presence
- CDO has commissioned three AI systems to drive customer retention

**Three AI Systems:**
1. **Churn Prediction** — XGBoost batch model on SageMaker; identifies at-risk customers 90 days before churn
2. **Offer Generation** — LLM/RAG pipeline on Bedrock; personalizes retention offers using customer history + product catalog
3. **Customer Service Agent** — ReAct agent on Bedrock; handles order inquiries, returns, and escalations autonomously

**One Platform:** All three systems share a single AWS data and compute platform

**Figure:** *Three-tier architecture diagram.* Top tier: "AWS Data Platform" — S3 buckets (raw/processed/features/artifacts), Glue ETL, SageMaker Feature Store. Middle tier: three side-by-side boxes for each AI system with their key components. Bottom tier: "Business Impact" — churn rate ↓, offer conversion ↑, support cost ↓. Arrows flow from top to middle (data feeds models) and from middle to bottom (models drive outcomes). Color-coded: blue for infrastructure, teal for models, gold for business metrics.

**Notes:** "This isn't a textbook exercise. NorthStar is architecturally identical to what you'd encounter at a retail company of this size. The data volumes, the system complexity, the business pressure — all realistic." Students should understand: they're not building three separate things; they're building one platform that runs three systems. That distinction matters deeply.

---

## Slide 7 — What You'll Build: Seven Labs, One Platform
**Layout:** Visual layer cake showing each lab adding a layer to the platform

**Content:**
| Lab | Layer | Core Technology |
|-----|-------|----------------|
| Lab 1 | Platform Foundation | Terraform, SageMaker, IAM, VPC |
| Lab 2 | Data & Feature Pipeline | Glue, Feature Store, data lineage |
| Lab 3 | Model Development | XGBoost training, RAG, evaluation |
| Lab 4 | CI/CD Automation | CodePipeline, Model Registry, tests |
| Lab 5 | Deployment & Scaling | Canary deploy, auto-scaling, rollback |
| Lab 6 | Monitoring & Reliability | CloudWatch, drift detection, runbooks |
| Lab 7 | Metrics & Economics | FinOps, Metric Pyramid, value scorecard |

**Figure:** *Layer cake / stacked architecture diagram.* Seven horizontal layers stacked from bottom (Lab 1 - Infrastructure) to top (Lab 7 - Business Value). Each layer is a distinct color band. Small icons inside each layer (Terraform logo, S3 logo, XGBoost icon, etc.). The left side shows the lab number; the right side shows a brief description. Top of stack: "Complete NorthStar AI Platform." The visual makes clear that each lab builds on all previous labs.

**Notes:** Students need to understand the cumulative nature of the labs before they start Lab 1. "If you skip corners in Lab 1, you pay for it in Labs 2-7. The Terraform IaC you write today is what all subsequent labs deploy into. This is not isolated homework — it's an engineering project that grows every two weeks." "The standard for each lab is: would a senior engineer at a retail company trust this in production?"

---

## Slide 8 — How This Course Works
**Layout:** Clean table with grading breakdown + policy callout boxes below

**Content:**
**Grading:**
| Component | Weight | Notes |
|-----------|--------|-------|
| 7 Labs | 49% | 7% each — cumulative NorthStar platform |
| Final Team Project | 30% | Teams of 3-4; presentations during finals week |
| AWS Academy | 10% | Cloud Foundations + GenAI Foundations |
| Quizzes | 11% | Short in-class assessments on readings |

**Key Policies:**
- **Late work:** 10% per day. Contact me BEFORE the deadline — not after — if you have an emergency.
- **AI tools:** Use of AI tools is highly encouraged. But you must be ready to explain what you submit.
- **Collaboration:** Individual submissions on labs; working with classmates is fine, copying is not.
- **Office hours:** Tues & Thurs after class, or by appointment (email first).

**Figure:** *Simple pie chart* showing grade component weights. Sections: Labs (49%, navy), Team Project (30%, teal), AWS Academy (10%, amber), Quizzes (11%, gray). Clean, large text labels. No 3D effects.

**Notes:** The AI tools policy is the one that surprises students most: you are expected to use AI, not avoid it. But you need to understand everything you submit, because you may be asked about it.

---

## Slide 9 — Lab 1 Assigned: Platform Foundation
**Layout:** Orange header (lab assignment style) + task list + important notes

**Content:**
**Lab 1: Platform Foundation**
- **Due:** Saturday, September 19, midnight
- **Goal:** Stand up the NorthStar AWS platform skeleton using Terraform IaC

**Key Tasks:**
1. Provision SageMaker domain with Studio (MLEngineer user profile)
2. Create S3 bucket structure: `raw/`, `processed/`, `features/`, `artifacts/`
3. Configure 3 IAM roles with scoped permissions (MLEngineer, DataEngineer, Governance)
4. Set up VPC with private subnets for SageMaker training jobs
5. Write Architecture Decision Record (ADR) — 600-900 words, 3 major decisions
6. Produce monthly cost estimate for the skeleton

**⚠️ Start Today:** AWS Educate account setup takes 24-48 hours to process.

**Figure:** *Terraform architecture diagram.* Shows the four Terraform modules (vpc/, iam/, sagemaker/, storage/) in boxes connected to the AWS services they provision. Light gray background with AWS service icons (S3 bucket, SageMaker domain, IAM role shield, VPC network). Module names in bold; AWS resources in standard type below each module name. Arrows show dependency order (vpc → iam → storage → sagemaker).

**Notes:** Assign this explicitly — make it an event. "Lab 1 is now assigned. You have two weeks. That sounds like a lot. It is not. AWS Educate account approval takes 24-48 hours. Set up your account today — before you leave the building. The starter kit is on Canvas. The Terraform module structure is provided; you fill in the resource definitions." Walk through the Canvas page briefly if time allows.

---

## Slide 10 — The NorthStar Starter Kit
**Layout:** Repository structure diagram + key files callout

**Content:**
**GitHub Repository Structure (maintain all semester):**
```
northstar-ai-platform/
├── README.md                  ← Platform overview, updated each lab
├── infrastructure/            ← Lab 1: Terraform IaC
│   ├── modules/vpc/
│   ├── modules/iam/
│   ├── modules/sagemaker/
│   └── modules/storage/
├── data/                      ← Lab 2+
├── models/                    ← Lab 3+
├── pipeline/                  ← Lab 4+
├── deployment/                ← Lab 5+
├── monitoring/                ← Lab 6+
└── docs/                      ← ADRs and reports
```

**Key Files Due for Lab 1:**
- `infrastructure/` — all four Terraform modules, working `terraform apply`
- `docs/lab1-architecture-decision-record.md` — your ADR

**Figure:** *File tree diagram* styled like a terminal `tree` command output on a dark background. Folders are highlighted in blue, key deliverable files in gold/amber. The `docs/` folder and `infrastructure/` folder are visually emphasized with a subtle glow border. Clean monospace font.

**Notes:** The repository is the artifact that grows all semester. Emphasize this: "You're not submitting lab homework — you're building an engineering portfolio. By December, your GitHub repo will be a complete enterprise AI platform. That's something you can show to an employer." Also note the critical security rule: "Never commit AWS credentials, access keys, or `.env` files. Committed secrets = automatic 0 on the lab, no exceptions."

---

## Slide 11 — The Architecture Decision Record (ADR)
**Layout:** Template preview with explanation on the left

**Content:**
**What is an ADR?**
- A structured decision log documenting: what decision was made, what alternatives were considered, and why this choice was made
- Standard engineering practice at Amazon, Google, Netflix, and most mature tech organizations
- Not an essay — it is a decision engineering document

**ADR Structure (Lab 1 requires 3 decisions):**
1. **Context:** What forced this decision? What are the constraints?
2. **Options Considered:** At least two viable alternatives with tradeoffs
3. **Decision:** What was chosen, and the specific rationale
4. **Consequences:** What this choice enables, what it forecloses

**Example Decision Topic for Lab 1:** "Why VPC with private subnets instead of public endpoints for SageMaker training?"

**Figure:** *ADR template visual.* Shows a filled-out ADR for the VPC decision as an example. Formatted as a clean document with colored section headers (Context in blue, Options in gray, Decision in navy, Consequences in teal). The document shows realistic content, not lorem ipsum. Demonstrates the professional quality standard expected.

**Notes:** Many students have never written an ADR before. Frame it as a skill worth learning: "In your first engineering job, you will write ADRs. Engineers who can explain their architectural decisions concisely and confidently get promoted faster than those who can't. This is that skill, practiced in a controlled setting where the stakes are lab grades, not production systems." The ADR for Lab 1 should document three major architectural choices: VPC topology, IAM permission scoping approach, and S3 bucket organization strategy.

---

## Slide 12 — Who Succeeds in This Course
**Layout:** Two-column contrast: behaviors that predict success vs. struggle

**Content:**
**Students who do well:**
- Start labs the same week they're assigned (not the weekend they're due)
- Read the chapter before class — the lectures assume you've read
- Ask questions early when they're stuck — not at 11 pm Saturday
- Treat labs as engineering projects, not homework assignments
- Use AI tools aggressively and learn from what they generate
- Come to office hours (they are lightly used and extremely valuable)

**Students who struggle:**
- Wait until the week the lab is due to open AWS for the first time
- Skip the readings and try to learn everything from slides
- Work in isolation when they could get unstuck in 10 minutes
- Optimize for completing tasks instead of understanding systems
- Submit AI-generated code they can't explain

**Figure:** *Side-by-side timeline visualization.* Two timelines (16 weeks) shown horizontally. Top timeline ("Successful student"): evenly distributed work marks across all weeks, green color. Bottom timeline ("Struggling student"): work spikes at weeks 2, 4, 6... (lab due dates), in red. The visual makes clear the pace problem before students experience it.

**Notes:** This slide is a gift to students. Be direct without being preachy: "I've taught this course multiple times. The predictor of struggle isn't ability — it's timing. The students who fail do so in exactly the same way: they fall behind in Week 3, never recover, and spend the last month in crisis." Also set the tone about AI: "Using AI tools is not cheating. Not understanding what you submitted is." The distinction matters and should be clear from day one.

---

## Slide 13 — Reading the Book: How to Use EAIE
**Layout:** Book chapter map + reading strategy tips

**Content:**
**Primary Text:** *Engineering the AI Enterprise: Orchestrating Strategy, Product, and Execution* (Toborg, 2026) — Parts 3 (Build) and 4 (Operate)

**Reading Strategy:**
- Chapters are 5,000-8,000 words — read them actively, not passively
- Each chapter has: Motivation → Challenge → Framework → Case Study → Apply It
- Focus especially on: the framework sections (the "how"), the case studies (the "why it matters"), and the "Apply It" exercises
- The Apply It sections preview what you'll do in labs

**Pre-class reading is non-negotiable:**
- Lectures build on the reading — they don't repeat it
- Quizzes are on the reading, not the lecture slides
- "I didn't have time to read" is not a viable strategy

**This Week:** No reading due for Thu Sep 3. Read *AI Systems Development Lifecycle* before Tue Sep 8.

**Figure:** *Chapter structure visualization.* A vertical flowchart showing the anatomy of a chapter: "Motivation" box → "Challenge" box → "Key Framework" box (highlighted in gold, labeled "This is the core") → "Case Study" box → "Apply It" box. Arrows connect each section. The "Key Framework" section has a bracket pointing to: "This is what the lecture digs into." Clean, minimal, helps students know where to focus their reading attention.

**Notes:** Students often don't know how to read technical books actively. Give them specific guidance: "When you read the case studies, ask yourself: could I have made the same mistake? When you read the frameworks, ask: how does this apply to NorthStar? When you read the Apply It section, notice — that's often what your lab will ask you to do." Set the expectation: quizzes are short (10-15 minutes), happen at the start of class, and test whether you read the chapter. They're designed so that students who read carefully get full credit without studying.

---

## Slide 14 — The Semester Ahead: A Preview
**Layout:** Visual calendar / roadmap showing all 15 weeks with key milestones

**Content:**
**Major Milestones:**
- Weeks 1-10: Build the NorthStar platform (Labs 1-5 + foundation lectures)
- Week 10: Security/Privacy II — the Build→Operate bridge
- Weeks 11-13: Operate the platform (Labs 6-7 + operations lectures)
- Week 13: Team project introduced — teams finalized
- Weeks 14-15: Team project work sessions
- Finals Week: Team project presentations (Dec 17)

**What you'll have built by the end:**
- A complete, IaC-defined AWS AI platform (Terraform)
- Three production-ready AI systems (churn, RAG, agent)
- Monitoring, cost attribution, and governance artifacts
- A team project: a production AI system of your own design
- A GitHub portfolio demonstrating all of it

**Figure:** *Visual semester calendar.* A 15-column grid (one column per week). Each column has the week number at the top, lecture topics in small text in the middle, and color-coded bars at the bottom: blue for Build arc, teal for Operate arc, gold for Team Project. Lab assignments and due dates are shown as diamond markers above the grid. A vertical red line labeled "Bridge" at Week 10. The overall visual looks like a Gantt chart but more polished — a project roadmap.

**Notes:** End the semester overview on a high note. "By December you will have done something that most CS programs spend four years getting you ready to do — you will have built and operated a production AI system end-to-end. The team project is where that becomes yours: not NorthStar's system, but a system you designed for a problem you care about." Pause here. Let that land. Then move to questions.

---

## Slide 15 — NorthStar Tech Stack Preview
**Layout:** AWS architecture diagram, full platform view

**Content:**
**Platform Services Used This Semester:**
- **Compute:** SageMaker (training, endpoints, Studio), EC2 (if needed)
- **Storage:** S3 (data lake), SageMaker Feature Store, DynamoDB (agent state)
- **Pipeline:** Glue (ETL), SageMaker Pipelines, CodePipeline (CI/CD)
- **Models:** SageMaker (custom models), Bedrock (foundation models, RAG, agents)
- **Monitoring:** CloudWatch (metrics, logs, alarms), Evidently (open-source drift detection, run in SageMaker Processing)
- **Security:** IAM, Secrets Manager, KMS, VPC, GuardDuty
- **IaC:** Terraform (all infrastructure defined as code)

**Note:** AWS Educate provides access to most services. Some Bedrock features require the free-tier account.

**Figure:** *AWS architecture reference diagram.* Full AWS architecture showing all services used in the course, organized in three tiers: Data Tier (S3, Glue, Feature Store), Model Tier (SageMaker, Bedrock), and Operational Tier (CloudWatch, CodePipeline, IAM). AWS official service icons. Color-coded by course arc: blue = Build, teal = Operate. Light gray background with subtle grid. Professional engineering diagram quality.

**Notes:** Students often worry they don't know enough AWS to survive this course. Reassure them: "You don't need AWS experience coming in. You need the willingness to learn it as you go, which is exactly how it works in the real world. We'll cover each service in the context of why you need it — not as a feature list, but as a design decision." Point out the progression: "Each lab adds another tier to this diagram. By Lab 7, you'll have touched every service shown here."

---

## Slide 16 — Key Takeaways + What's Next
**Layout:** Five numbered takeaways + next session preview

**Content:**
**Key Takeaways from Today:**
1. This course is about engineering production AI systems — building and operating at enterprise scale, not demoing or theorizing
2. AI development differs from software in four fundamental ways: probabilistic outputs, data dependency, model drift, and inherent experimentation
3. The Build → Operate arc is the spine of the semester — every lecture and every lab fits into one of the two arcs
4. NorthStar Retail is your laboratory for 15 weeks — treat it like a real engineering project from day one
5. Lab 1 is assigned: start your AWS account setup today — it takes 24-48 hours to process

**Next Session (Tue Sep 8):**
- Topic: AI Systems Development Lifecycle (AISDLC) — the unifying framework for the course
- Reading due: *AI Systems Development Lifecycle* — "Why AI Development Is Different" through "Stage Gates and Artifacts"
- Come ready to discuss: why do most AI projects fail?

**Figure:** *Simple 5-point numbered list visual.* Each takeaway on its own row with a large numbered circle (navy background, white number) on the left and the takeaway text to the right. Below the list: a "Next Up" banner in teal showing the upcoming lecture topic and reading. Clean, high-contrast, readable from the back of the room.

**Notes:** End strong. Don't just read the takeaways — synthesize them in one sentence: "This course exists because the gap between building AI demos and running AI systems that matter is enormous, and someone has to bridge it. By December, that someone will be you." Then: "Questions? I'll be here after class. See you Tuesday — do the reading."
