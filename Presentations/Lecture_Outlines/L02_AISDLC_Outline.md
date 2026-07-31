---
lecture: L02
title: AI Systems Development Lifecycle (AISDLC)
date: Tuesday, September 8, 2026
week: 2
arc: Build
reading_due: "AI Systems Development Lifecycle — Why AI Development Is Different; The AISDLC at a Glance; Lifecycle Phases; Stage Gates and Artifacts"
lab_due: "Lab 1 due Sat Sep 19"
slides_target: 17
---

# L02: AI Systems Development Lifecycle (AISDLC)
**Tuesday, September 8, 2026 | CS 401R: Engineering Production AI Systems | Fall 2026**

> The AISDLC is the unifying intellectual framework for everything we do in this course. Every lecture, every lab, every architectural decision traces back to this lifecycle. Understand it deeply.

**Reading Due:** *AI Systems Development Lifecycle* — "Why AI Development Is Different" through "Stage Gates and Artifacts"  
**Lab 1 Due:** Sat Sep 19, midnight

---

## Slide 1 — Title
**Layout:** Left dark panel + right pipeline visualization

**Content:**
- AI Systems Development Lifecycle (AISDLC)
- CS 401R · Lecture 02 · Tuesday, September 8, 2026
- Dr. Scott T. Toborg · Brigham Young University

**Figure:** *8-stage pipeline visualization.* Eight colored rectangular boxes arranged left to right on a dark navy background, connected by forward-pointing arrows. Boxes labeled: 1-Define Problem, 2-Discover Data, 3-Prepare Data, 4-Design Solution, 5-Develop, 6-Evaluate, 7-Deploy, 8-Monitor. Each box is a slightly different shade from deep blue (left) to teal (right). Below the linear pipeline, a curved return arrow loops from stage 8 back to stage 1, labeled "Operational feedback." Additional smaller return arrows visible at key points (5→4, 6→2, 8→4). The image communicates: structured, iterative, not waterfall.

**Notes:** "What is the most common reason enterprise AI projects fail?" Most common answers: wrong process, no monitoring, bad data, etc. "All of those are symptoms of one root cause: applying a software development mindset to a problem that is fundamentally not a software problem."

---

## Slide 2 — Opening Provocation
**Layout:** Full-bleed dark slide, large pull quote

**Content:**
> "The failure is not a technology failure or a talent failure. It is a process failure — applying a software development mindset to a problem that requires a fundamentally different approach."
>
> — *Engineering the AI Enterprise*, Ch. 3

**Figure:** *Minimalist dark slide.* The quote in large, elegant type (Calibri Light, white) centered on a deep slate (#2A323E) background. Opening quotation mark in very large (100pt) gray. Attribution line in gold/amber at the bottom. No other elements. The visual restraint makes the words land harder.

**Notes:** "This is the premise of this entire lecture — and in many ways, the premise of this entire course. We are going to spend the next hour building the process that solves this problem." The quote frames everything that follows as practical rather than theoretical.

---

## Slide 3 — The Story of a Failed AI Project
**Layout:** Narrative flow with 6 stages, each on its own row with a status indicator

**Content:**
**Step 1:** Team receives AI project → assigns a sprint team → runs it like a software feature
**Step 2:** Demo works. Stakeholder impressed. Project greenlit for production.
**Step 3:** Team deploys to production.

**Then:**
**Step 4 →** Real data has different distributions than the training sample. Predictions degrade.
**Step 5 →** No monitoring. Nobody notices for 3 months. Business analyst flags "predictions seem wrong."
**Step 6 →** 6 months of forensics, model retraining, data archaeology, stakeholder remediation.

**Outcome:** Project quietly reclassified as a "learning initiative." Engineering lead moves to a different team.

*This is not an edge case. It is the modal outcome for first-time enterprise AI projects.*

**Figure:** *Narrative timeline.* A horizontal timeline with 6 stages. Steps 1-3 show a green upward arrow (indicating things are going well). Steps 4-6 show a red downward arrow (failure cascade). The transition point (Step 3, "Deploy") is marked with a vertical red line labeled "The Production Cliff." Each stage has a small icon (team → presentation → rocket → warning → no-monitoring icon → forensics). The visual reads like a case study story. Final box at right: gray, labeled "Lessons Learned (Too Late)."

**Notes:** "I have seen this story unfold in organizations ranging from 50 people to 50,000 people. The details change — sometimes it's churn prediction, sometimes it's demand forecasting, sometimes it's a recommendation system. The failure pattern is always the same." "Where in this story could a better process have changed the outcome?" Identify multiple intervention points. Each one maps to an AISDLC stage gate.

---

## Slide 4 — The Counter-Story: What Good Looks Like
**Layout:** Same format as Slide 3 but all green

**Content:**
**Week 1-2:** Team spends 2 weeks with business stakeholders BEFORE writing code. Defines: what decision does the model inform? What's the acceptable error rate? Who owns the output?
**Week 3:** Team documents a simple rule-based baseline. Ships it. Measures it.
**Week 4-8:** Team builds the model against those criteria. Gate: "Does this beat the baseline by ≥15%?"
**Week 9:** External evaluation. Privacy review. Production readiness checklist. Gate: "Ready to deploy?"
**Week 10:** Canary deployment (5% traffic). Monitoring dashboard built before launch. Runbook written.
**Month 3:** Model still within performance criteria. Automated retraining trigger fires. Self-heals.

**Outcome:** System has been running for 18 months. Still delivering value. Team is trusted by the business.

**Figure:** *Same timeline layout as Slide 3 but entirely green.* Each stage has a checkmark and green upward arrow. Milestones labeled: "Problem Definition Gate ✓", "Baseline Gate ✓", "Model Evaluation Gate ✓", "Production Readiness Gate ✓", "Deployment Gate ✓", "Operational Health ✓". The visual contrast with the previous slide is immediate and deliberate.

**Notes:** "This is the same organization. Same talent level. Different process." This is the most important conceptual flip of the lecture. The difference between the two stories is not better engineers, better data, or better models — it is a structured process with explicit decision points. Every gate that failed in Story 1 is present and working in Story 2. The AISDLC is the formalization of Story 2.

---

## Slide 5 — The Four Properties That Make AI Development Different
**Layout:** 2×2 quadrant, each cell a distinct color

**Content:**
**1. PROBABILISTIC, not deterministic**
- "It works" is not binary — only performance thresholds exist
- You cannot write a unit test that verifies correctness
- Every assertion about system behavior is probabilistic

**2. DATA is a first-class engineering dependency**
- Data quality problems ARE production bugs
- A label-encoding error in a pipeline is a production incident
- Data is not an analytics concern — it is an engineering responsibility

**3. Models DEGRADE over time**
- Deployment is the beginning, not the end
- Concept drift, data drift, distribution shift: real, frequent, expensive
- Monitoring is not optional — it is part of the system

**4. EXPERIMENTATION is inherent**
- You cannot commit to a delivery date for a model
- Traditional project management tools break here
- Gates replace deadlines: "proceed when criteria are met"

**Figure:** *2×2 color-blocked quadrant diagram.* Each quadrant has a large background color (navy, dark teal, amber, slate), a single large icon (dice, database, trend-down arrow, flask), and a 2-line label + 1-line sub-text. The quadrant lines are crisp white. Each property number is in large white type in the corner. No gradients, no drop shadows. Clean and high-contrast.

**Notes:** These four properties drive every AISDLC design decision. "When you ask 'why do we need a stage gate at this point?' the answer always traces to one of these four properties." Walk through each quadrant and ask: "How does this change what you do in practice?" For example, Property 1: "What does your QA strategy look like when correctness is a distribution, not a boolean?" Property 3: "What do you do when a model that was 90% accurate 6 months ago is now 72% accurate — and nobody noticed?"

---

## Slide 6 — The AISDLC: 8 Stages Overview
**Layout:** Full-width 8-stage pipeline with abbreviated description of each stage below

**Content:**
| Stage | Name | Core Question |
|-------|------|--------------|
| 1 | Define Problem | Is this the right problem, defined well enough to build? |
| 2 | Discover Data | Does the required data exist in sufficient quantity and quality? |
| 3 | Prepare Data | Is data in a form suitable for development? |
| 4 | Design Solution | Is the approach technically sound and aligned to constraints? |
| 5 | Develop | Does the candidate system meet the success criteria? |
| 6 | Evaluate | Is the system safe to deploy across all relevant dimensions? |
| 7 | Deploy | Is the system behaving as expected in production? |
| 8 | Monitor | Is the system still delivering value at acceptable cost? |

**Figure:** *8-box horizontal pipeline diagram.* Each box is clearly numbered and labeled, with the core question in smaller text below the stage name. Color progression from deep navy (left) to bright teal (right). Forward arrows between stages. Gate symbols (diamond shapes) between each pair of stages — small diamond with a checkmark. A large curved return arrow loops below the entire pipeline from stage 8 back to stage 1. The diagram fits on one slide and reads clearly at presentation size.

**Notes:** "This is the lifecycle you will use for every AI system you build in this course — and if you do this right, every AI system you build for the rest of your career." "We're going to go deep on each of these over the next few slides. But first, I want you to notice what's missing from this diagram that you'd see in a traditional software lifecycle." Answer: No fixed schedule. No sprint deadlines. No "done by this date." Instead: gates. Each stage ends with a decision, not a date.

---

## Slide 7 — Stage 1: Define Problem
**Layout:** Left content + right artifact example

**Content:**
**What happens in Stage 1:**
- Work with business stakeholders to define the decision the AI system will inform
- Establish success criteria before any data is touched
- Define what "acceptable" error looks like in business terms
- Document constraints: latency, cost, regulatory, organizational
- Produce the AI Project Charter

**AI Project Charter contains:**
- Problem statement (business language, not technical)
- Success criteria: specific, measurable, agreed by all parties
- Constraints: budget, timeline, risk tolerance
- Named gate owner: who has authority to approve Stage 1 completion

**Gate Decision: Invest / Pause / Reframe**

**Figure:** *AI Project Charter template mockup.* A clean document layout showing a realistic (but brief) filled-in example for the NorthStar churn prediction system. Sections: Problem Statement ("Identify customers at risk of churning within 30 days..."), Success Criteria ("AUC ≥ 0.75, precision ≥ 0.68 at threshold 0.4"), Constraints ("$15K/month inference budget, GDPR compliance, no PII in feature names"), Gate Owner ("CDO, Maria Chen"). Document is formatted like a professional one-pager. Header: "NorthStar Retail — AI Project Charter."

**Notes:** "Stage 1 is the stage most teams skip entirely. They receive a request like 'build us a churn model' and immediately start writing code. The Project Charter is how you slow down enough to find out what the business actually needs. Who defines success? At what point do we admit the approach is wrong and reframe?" The gate decision is three-way on purpose: Invest (proceed to Stage 2), Pause (something isn't clear yet, go back and clarify), or Reframe (the AI approach is wrong — the right solution may not be ML at all).

---

## Slide 8 — Stages 2 & 3: Discover + Prepare Data
**Layout:** Two-column side by side

**Content:**
**Stage 2 — Discover Data**
- Audit available data sources against the success criteria from Stage 1
- Core questions: Does the data exist? Is there enough of it? How clean is it?
- Produce: Data Readiness Assessment
- Gate: Proceed (data sufficient) / Defer (need more data) / Redesign (data-constrained problem)

**Stage 3 — Prepare Data**
- Transform raw data into development-ready format
- Feature engineering, cleaning, train/validation/test split
- Establish data lineage: where did each feature come from?
- Produce: Prepared data assets + Data Contract
- Gate: Proceed (data ready) / Remediate (quality issues require fixing)

**Why these are separate stages:**
- Stage 2 can reveal the project is impossible — before spending on Stage 3
- Stage 3 failures are expensive if the Stage 2 gate wasn't enforced

**Figure:** *Two-panel data flow diagram.* Left panel: "Discover" — shows raw data sources (S3 bucket icons: customers.csv, transactions.parquet, clickstream.parquet) flowing into a "Data Readiness Assessment" document. Quality score bars below each source (green = good, amber = marginal, red = problematic). Right panel: "Prepare" — shows the same data flowing through transformation steps (Glue icon) into prepared outputs (Feature Store icon). A "Data Contract" document sits between the two panels, connecting them.

**Notes:** "These two stages are frequently collapsed into one sprint. That's a mistake — and here's why." Tell the Zillow story briefly (preview of L05): Zillow's iBuying model collapsed in part because the data it was trained on didn't match the production data environment. A proper Stage 2 discovery would have surfaced this mismatch. "Data discovery is due diligence. Skipping it is like starting construction on a building without a soil test."

---

## Slide 9 — Stages 4 & 5: Design + Develop
**Layout:** Two-column side by side, with development spectrum diagram

**Content:**
**Stage 4 — Design Solution**
- Choose the technical approach: prompt engineering, RAG, fine-tuning, custom training, agent
- Define the system architecture: components, interfaces, data flows
- Produce: Solution Design Document (your Lab 1 ADR is Stage 4 output!)
- Gate: Approve / Revise / Escalate

**Stage 5 — Develop**
- Build and iterate on candidate models and system components
- The stage where experimentation lives — multiple approaches explored
- Produce: Trained artifacts + Experiment Log (tracked in MLflow or similar)
- Gate: Ship (to Stage 6) / Return to Design (if approach is wrong)

**The Experimentation Budget:**
- Stage 5 is the only stage where iteration without a gate is acceptable
- But the stage as a whole has entry and exit criteria — not open-ended
- "We'll iterate until it's good enough" is not a plan

**Figure:** *Development spectrum visualization.* A horizontal arrow from "Simple" (left) to "Complex" (right). Along the arrow, five labeled points: "Prompt Engineering" → "RAG" → "Fine-Tuning" → "Custom Training" → "Agentic System." Each point has: a complexity bar (height), a time estimate (weeks), and a cost indicator ($). A vertical dashed line labeled "Start here" sits at "Prompt Engineering" with an arrow pointing right, labeled "Move right only when justified." Color gradient from green (left) to red (right).

**Notes:** "Stage 4 is where most senior engineers live — designing the system before anyone writes code. Stage 5 is where junior engineers want to live — writing code and running experiments. Both matter, but the order matters more." "MLflow or similar tool tracking every experiment — hyperparameters, metrics, data versions, model artifacts. If you can't reproduce an experiment from the log, the experiment didn't happen." This directly maps to Lab 3.

---

## Slide 10 — Stages 6 & 7: Evaluate + Deploy
**Layout:** Two-column with evaluation dimensions and deployment strategy comparison

**Content:**
**Stage 6 — Evaluate**
- The gate before production — the most consequential gate in the lifecycle
- Evaluation dimensions: technical performance, fairness/bias, robustness, safety, regulatory compliance
- Output: Validation Report + Production Readiness Checklist (PRC)
- Gate: Deploy / Remediate (fixable issues) / Halt (fundamental problem)

**Stage 7 — Deploy**
- Deployment strategies: canary, blue/green, shadow, feature flags
- Monitoring infrastructure live before traffic arrives
- Runbook written and reviewed before the first request
- Output: Live dashboards + Operational Runbooks
- Gate: Full rollout / Hold at canary / Rollback

**The Rule:** Monitoring before deployment. Never deploy a model without a dashboard.

**Figure:** *Deployment strategy comparison table.* Four rows (Canary, Blue/Green, Shadow, Feature Flags), four columns (How it works, Risk level, Rollback speed, When to use). Color-coded cells: green = low risk, amber = medium risk, red = high risk. A small diagram for each strategy shows traffic flow with percentages. Clean table with header row in navy. This becomes a reference diagram students can return to.

**Notes:** "Stage 6 is where the hard conversations happen. The model meets the business criteria. But is it fair? Does it degrade for certain customer segments? Could it be manipulated? Stage 6 is not a technical review — it's a system review across all risk dimensions." Stage 7: "The runbook is written before the first request hits the system. Every failure mode has a documented response. Every escalation path is named. If you can't write the runbook, you're not ready to deploy." These concepts map directly to Labs 5 and 6.

---

## Slide 11 — Stage 8: Monitor (The Stage That Never Ends)
**Layout:** Monitoring loop diagram with key monitoring dimensions

**Content:**
**Stage 8 — Monitor**
- The only stage with no defined completion — it runs for the lifetime of the system
- What monitoring covers: model performance drift, data drift, system health, business metrics
- Produce: Operational Review Records, Drift Reports, Incident Response Log
- Gate: Continue / Retrain (performance declining) / Retire (no longer valuable)

**The three monitoring signals:**
1. **Data drift** — the input distribution is shifting (new customer behaviors, seasonality)
2. **Concept drift** — the relationship between inputs and correct outputs is changing
3. **System drift** — infrastructure degradation, latency creep, cost escalation

**The operational review cadence:** Weekly automated checks → Monthly team review → Quarterly executive scorecard

**Figure:** *Monitoring dashboard mockup.* Shows a CloudWatch-style dashboard with four panels: (1) Model AUC over time — line chart with green zone and amber/red alert zones; (2) Data drift score — time series with a threshold line; (3) Request latency P95 — time series; (4) Monthly inference cost — bar chart. One alert is visible in panel 2 (amber spike). Labels are realistic NorthStar values. The dashboard looks like something you'd actually build in Lab 6.

**Notes:** "Stage 8 is where the lifecycle closes the loop — and where most teams stop investing. The model is deployed, everyone moves on, and nobody watches it. Months later, a business analyst notices performance has degraded." Connect this to Lab 6: "Your Lab 6 will build exactly this kind of dashboard for the NorthStar churn model. By the time you submit it, you should be able to answer the question: Is the model still performing? Is the data drifting? Is the system healthy?" Stage 8 gates are operational, not technical: Continue (healthy), Retrain (performance is declining, but the approach is still valid), or Retire (the system is no longer fit for purpose).

---

## Slide 12 — Stage Gates: The Discipline That Makes It Work
**Layout:** Gate anatomy diagram + five-component table

**Content:**
**What is a stage gate?**
A formal decision point with explicit pass/fail criteria that determines whether a project proceeds, pauses, or changes direction.

**Five components of every gate:**
| Component | What it requires | Why it matters |
|-----------|-----------------|----------------|
| Pass criteria | Specific, measurable, agreed BEFORE work starts | Prevents moving goalposts |
| Gate owner | One person or committee with actual decision authority | Prevents decisions by committee paralysis |
| Required artifacts | What must exist before the gate can open | Ensures evidence-based decisions |
| Decision options | The full set of possible outcomes (not just yes/no) | Forces nuanced decision-making |
| Escalation path | Who resolves deadlocks | Prevents projects stalling at gates |

**Why gates fail:** Schedule pressure + vague criteria + wrong ownership = gate theater

**Figure:** *Gate anatomy diagram.* A horizontal flow showing: "Previous Stage Output" box → large diamond shape (the gate) → three exit arrows (Proceed, Remediate, Halt/Reframe). Inside the diamond: the five gate components listed. The diamond is outlined in gold, with the stage name at the top. Below the gate: a red box labeled "Gate Theater" crossed out, with the caption "Occurs when: criteria are vague / owner lacks authority / pressure overrides judgment." Clean, high-contrast.

**Notes:** "Gates without explicit criteria become theater — you go through the motions, but nothing actually changes. I've seen projects where the Stage 4 gate was 'does the team feel confident?' That is not a gate. That is a vibe check." The most important gate component is the pass criteria: they must be defined before the stage begins, not after. "If you're setting criteria after you see the results, you're rationalizing, not deciding." Connect to Lab 3: "Your model evaluation rubric IS the Stage 6 gate criteria. AUC ≥ 0.72 at threshold 0.4. That is a gate criterion."

---

## Slide 13 — Return Loops: Controlled Iteration, Not Waterfall
**Layout:** AISDLC pipeline with return arrows labeled and annotated

**Content:**
**The AISDLC is not waterfall — it has explicit return loops:**

| From | To | Trigger |
|------|----|---------|
| Stage 2 | Stage 1 | Data discovery reveals required data doesn't exist |
| Stage 3 | Stage 2 | Data preparation reveals quality issues not seen in discovery |
| Stage 5 | Stage 4 | Experimentation reveals the approach is fundamentally wrong |
| Stage 6 | Stage 5 | Evaluation failure in known dimension → back to development |
| Stage 6 | Stage 2 | Evaluation failure in data dimension → back to data |
| Stage 8 | Stage 4 | Monitoring reveals a design flaw, not just a performance issue |
| Stage 8 | Stage 1 | Business context has changed — problem requires reframing |

**The key distinction:** Every return loop passes through a gate with documented rationale.
You don't drift backward — you formally return with updated artifacts.

**Figure:** *Return loop diagram.* The 8-stage pipeline shown again, this time with prominent curved arrows below the pipeline showing the named return loops. Each arrow is labeled with the trigger condition in small text. A legend at bottom-right distinguishes "Forward flow" (blue arrows above) from "Return loops" (orange/amber arrows below). The visual makes clear this is a structured, deliberate iteration model, not chaotic back-and-forth.

**Notes:** "This is the question I always get: 'Isn't the AISDLC just waterfall with extra steps?' No — and here's why." Draw the distinction on the board: Waterfall assumes you get it right the first time. The AISDLC assumes you won't. "What the AISDLC gives you is controlled, gated iteration. When you return to Stage 2 from Stage 3, you don't just silently go back — you document why, you update the Data Readiness Assessment, and the Stage 2 gate owner re-approves. It is deliberate iteration, not sloppy backtracking."

---

## Slide 14 — Calibrating the AISDLC to Risk Level
**Layout:** Three-row risk matrix with gate weight guidance

**Content:**
| Risk Level | Definition | Gate Weight | Example |
|------------|-----------|-------------|---------|
| **LOW** | Internal analytics, experimental, no customer impact | Light gates, informal artifacts, fast iteration | A/B test on internal dashboard |
| **MEDIUM** | Customer-facing, revenue-impacting, limited regulatory exposure | Full gates, complete artifacts, documented decisions | NorthStar churn model (this course!) |
| **HIGH** | Regulated, safety-critical, autonomous action with real consequences | Extended evaluation, external audit, compliance gates, board visibility | AI in medical diagnosis, autonomous lending, LLM agents with financial authority |

**Rule of thumb:** Scale gate rigor to the blast radius of a failure.

**Skipping gates on a low-risk project:** Reasonable and often correct.
**Skipping gates on a high-risk project:** Professionally negligent.

**Figure:** *Three-tier risk pyramid.* A vertical pyramid divided into three color-coded sections: GREEN (low risk, large base) labeled "Move fast, document lightly"; AMBER (medium risk, middle section) labeled "Full process, full artifacts"; RED (high risk, narrow top) labeled "Maximum rigor, external review." Icons beside each tier illustrate the example use case. A blast-radius graphic sits beside each tier (small explosion at bottom, large at top). Proportions make clear that most enterprise AI projects live in the amber zone.

**Notes:** "For the NorthStar labs, we operate at medium-risk discipline — full gates, complete artifacts. That's intentional: it's where most enterprise AI systems live. If the course calibrated to low-risk, you'd be underprepared. If we calibrated to high-risk for a student course, we'd spend all semester on compliance documentation and never build anything." Students working in regulated industries after graduation will need to shift up. This framework gives them the mental model to know when and how.

---

## Slide 15 — The AISDLC at a Glance (Full Reference Table)
**Layout:** Full-width reference table, all 8 stages

**Content:**
| Stage | Core Question | Key Artifact | Gate Decision |
|-------|--------------|--------------|---------------|
| 1. Define Problem | Right problem, defined well enough to build? | AI Project Charter | Invest / Pause / Reframe |
| 2. Discover Data | Sufficient data exists to support this problem? | Data Readiness Assessment | Proceed / Defer / Redesign |
| 3. Prepare Data | Data in a format suitable for development? | Prepared data assets | Proceed / Remediate |
| 4. Design Solution | Approach technically sound, aligned to constraints? | Solution Design Document | Approve / Revise / Escalate |
| 5. Develop | Candidate system meets success criteria? | Trained artifacts + Experiment Log | Ship / Return to Design |
| 6. Evaluate | System safe to deploy across all risk dimensions? | Validation Report + PRC | Deploy / Remediate / Halt |
| 7. Deploy | System behaving as expected in production? | Dashboards + Runbooks | Full rollout / Canary / Rollback |
| 8. Monitor | System still delivering value at acceptable cost? | Operational Review Records | Continue / Retrain / Retire |

**Figure:** *The full table IS the figure.* Style it as a clean, high-contrast reference table with: Stage column in navy, Core Question column in dark gray, Key Artifact column in teal, Gate Decision column in amber/gold. Alternate row shading in very light blue/white. Large enough to read from the back of the room. This table will appear again throughout the course as a reference.

**Notes:** "This is the single most important reference table in the course." Walk through each row carefully, pointing out that every stage has a GATE (not a timeline), every artifact is a real document (not a checkbox), and every gate has options (not just yes/no). "When I ask you on a quiz to name the artifact from Stage 2, you should be able to answer without looking at your notes." This table will appear in modified form in Labs 1, 3, 4, and 5.

---

## Slide 16 — NorthStar: AISDLC in Practice
**Layout:** NorthStar connection — mapping labs to AISDLC stages

**Content:**
**NorthStar Retail already completed Stages 1 & 2:**
- Stage 1: CDO commissioned the churn prediction system; success criteria defined (churn reduction ≥ 8%)
- Stage 2: Data team confirmed: 18 months of transactions, 250K customers — data is sufficient

**Your labs complete Stages 3–8:**
| Stage | Lab | What You Build |
|-------|-----|----------------|
| Stage 3 — Prepare | Lab 2 | Glue ETL pipeline + SageMaker Feature Store |
| Stage 4 — Design | Lab 1 (ADR) | Architecture Decision Record = Solution Design Document |
| Stage 5 — Develop | Lab 3 | XGBoost training + RAG pipeline + evaluation |
| Stage 6 — Evaluate | Lab 3 | Model evaluation rubric → Stage 6 gate criteria |
| Stage 7 — Deploy | Labs 4 & 5 | CI/CD pipeline + canary deployment |
| Stage 8 — Monitor | Lab 6 | CloudWatch dashboards + drift detection + runbooks |

**Figure:** *AISDLC pipeline with lab labels.* Same 8-stage pipeline as on Slide 6, with lab assignment badges overlaid on the relevant stages. Stages 1-2 are labeled "NorthStar pre-work" and shown in gray (already done). Stages 3-8 are color-coded by lab: Lab 2 (stage 3), Lab 1/ADR (stage 4), Lab 3 (stages 5-6), Labs 4-5 (stage 7), Lab 6 (stage 8). Makes the entire semester's lab arc legible in one image.

**Notes:** "Every lab you submit is an AISDLC artifact. Your Lab 1 ADR is not homework — it IS the Stage 4 Solution Design Document. Your Lab 3 evaluation report is the Stage 6 Validation Report. When you write your Lab 6 runbook, you are completing Stage 8. The semester is a complete AISDLC cycle, run at medium-risk discipline, for a realistic enterprise AI system." This is the most important contextualizing statement of the lecture.

---

## Slide 17 — Key Takeaways + What's Next
**Layout:** Five numbered takeaways + next session preview

**Content:**
**Key Takeaways:**
1. AI projects fail because teams apply software process to a problem that requires a fundamentally different approach — not because of bad talent or bad technology
2. The AISDLC provides 8 stages with explicit stage gates: controlled, deliberate iteration, not waterfall and not chaos
3. Stage gates only work when they have specific criteria, named owners, and real decision authority — without these, they become theater
4. Every return loop in the AISDLC is documented and formal — no silent backward drift is acceptable
5. Your semester IS a complete AISDLC cycle: Labs 2-6 complete Stages 3-8 for the NorthStar churn system

**Next Session (Thu Sep 10):**
- Topic: AI Platform & Cloud Architecture I — what is a platform? Reference architectures. Core components.
- Reading due: *AI Platform & Cloud Architecture* — "Motivation" through "Core Platform Components"
- Lab 1 due: Saturday, September 19 — how's your AWS Educate setup going?

**Figure:** *Summary visual.* Five numbered circles (navy) with the key takeaway text beside each. Below: a "Next Up" banner (teal) showing the upcoming lecture topic and reading. The five takeaways are formatted for maximum readability — short, declarative sentences in large type.

**Notes:** "By the time you submit Lab 1, you will have produced an Architecture Decision Record — which is the Stage 4 Solution Design Document. So in two weeks, you will have completed AISDLC Stage 4 for NorthStar's churn prediction system. That's not hypothetical. That's real." Read the chapter on Platform & Cloud Architecture before Thursday."
