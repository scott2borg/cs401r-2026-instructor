---
lecture: L26
title: Project Workshop II — Final Demos & Course Conclusion
date: "Thursday December 3 / Tuesday December 8 / Thursday December 10, 2026"
week: 15
arc: Project
reading_due: "None"
lab_due: "Final Project Demos — Dec 8 & Dec 10"
slides_target: 15
---

# L26: Project Workshop II — Final Demos & Course Conclusion
**Finals Week | CS 401R: Engineering Production AI Systems | Fall 2026**

> The last session. The course ends with student work — not a lecture. This slide deck is split: the first half runs Dec 3 (pre-finals prep); the second half frames the demo days (Dec 8 & 10) and delivers the course conclusion.

**Lab 7 Due:** Sat Dec 5 (if not already submitted)
**Final Project Due:** Dec 10 (end of presentations)
**Course Complete:** Dec 10, 2026

---

## Slide 1 — Week 15: Final Push
**Layout:** Session overview

**Content:**
- Project Workshop II & Course Conclusion
- CS 401R · Lecture 26 · Finals Week 2026

**Three sessions this week:**
| Session | Date | Purpose |
|---------|------|---------|
| Workshop II | Thu Dec 3 | Pre-demo prep, final Q&A |
| Demo Day 1 | Tue Dec 8 | Presentations: Teams A-D |
| Demo Day 2 | Thu Dec 10 | Presentations: Teams E-H + Conclusion |

**What's done:**
- 25 lectures of content
- 7 labs covering the full AISDLC
- NorthStar case study: churn, RAG offers, agent
- Platform, data, models, XOps, testing, deployment, monitoring, reliability, governance, economics

**What's left:**
- Your final project demo
- The conversation about what happens next

**Figure:** *Course arc visual — final form.* The full course arc as a ribbon: Build arc (L01-L17) → Operate arc (L18-L24) → Project arc (L25-L26). The 26 lectures shown as dots along the ribbon. The ribbon ends at "Demo Day" with a flag icon. The current position (L26) is highlighted. The visual creates a sense of completion — you can see the whole journey.

**Notes:** "Two things happen in the last week of a course: students are exhausted, and students have a clear sense of how much they've built. The job of this final session is to honor both. Acknowledge the difficulty. Name what was accomplished. And open the door to what comes next — because this course is not the end of the journey, it's a launching pad."

---

## Slide 2 — Pre-Demo Checklist: Dec 3 Workshop
**Layout:** Working checklist for pre-demo preparation

**Content:**
**48-Hour Pre-Demo Checklist (Complete by Monday Dec 7):**

**System reliability:**
- [ ] End-to-end demo path works from cold start (logout, login, navigate to endpoint, invoke)
- [ ] Endpoint is in `InService` state (not in deployment or update)
- [ ] SageMaker Studio: notebook opens, cells run without errors
- [ ] CloudWatch dashboard: metrics visible, no "No data" panels
- [ ] If using Bedrock: Knowledge Base sync complete, agent is enabled

**Presentation:**
- [ ] 10-minute path timed (10 minutes exactly — hard cutoff)
- [ ] Architecture diagram clean, readable on projector (large fonts, high contrast)
- [ ] Transitions are smooth: know which AWS Console pages you're navigating to
- [ ] Laptop charged, HDMI adapter packed

**Q&A preparation:**
- [ ] Know your key architectural decisions and why you made them
- [ ] Know your ROI number and the 2-3 most important assumptions behind it
- [ ] Know one thing you would do differently and why

**Documentation:**
- [ ] README complete (problem, system description, how to run)
- [ ] Model card written (if custom model)
- [ ] Business case document final

**Backup plan:**
- [ ] Screenshots of working system taken (in case live demo fails)
- [ ] Lab 7 notebook PDF exported (shows your economics work even if notebook won't open)

**Figure:** *Demo day reliability matrix.* Two-column table: Demo Component | Risk Level. Endpoint InService: Low (check morning of). SageMaker Studio: Medium (can be slow to start). CloudWatch Dashboard: Low (always available). Bedrock Agent: Medium (verify enabled). Live prediction: Medium (have screenshot backup). Architecture diagram: Low (it's a PDF). The matrix helps students prioritize their pre-demo testing effort.

**Notes:** "The demo path is: 1) show architecture diagram (2 minutes), 2) explain the business problem (1 minute), 3) live prediction/offer/agent invoke (3 minutes), 4) monitoring dashboard (2 minutes), 5) business case ROI number (2 minutes). That's 10 minutes. Know this path cold. The Q&A is when you get to go deeper — but the 10-minute path should be automatic by demo day."

---

## Slide 3 — Presentation Structure: The 10-Minute Demo
**Layout:** Demo format guide

**Content:**
**The 10-Minute Final Presentation:**

**Minute 0:00-2:00 — Architecture Overview**
Show the architecture diagram. Walk through the major components: data pipeline → model → endpoint → monitoring. Don't describe every service — explain the key design choices. "I chose a canary deployment pattern because…" "I used a Bedrock Knowledge Base instead of a custom model because…"

**Minute 2:00-3:00 — Business Problem**
One slide or verbal explanation: what is the business problem, who the user is, what the AI system does for them, and what the expected business outcome is?

**Minute 3:00-6:00 — Live System Demo**
Go to AWS Console or invoke via SageMaker Studio. Show:
- A real prediction (or offer, or agent response)
- Show the output — not just "it ran," but "here is what it returned and here is what it means"
- Show one monitoring metric with history

**Minute 6:00-8:00 — Architecture Deep Dive**
Pick one architectural component to explain in depth: your Feature Store schema, your canary-deployment Lambda, your RAGAS evaluation gate, or your FinOps cost allocation. Choose the one that represents your most interesting technical decision.

**Minute 8:00-10:00 — Business Value**
ROI number, key assumptions, and: "Here is the metric chain — from model accuracy, to business outcome, to dollar value." Close with: "Here's what I would do next if this were a real system."

**Q&A: 5 minutes**
Instructor and TA questions. Focus: technical depth and business judgment.

**Figure:** *10-minute demo timeline.* Horizontal bar divided into 5 segments with exact times. Color coding: Architecture (blue, 2 min), Business Problem (green, 1 min), Live Demo (gold, 3 min — marked as "most important"), Deep Dive (teal, 2 min), Business Value (purple, 2 min). Plus Q&A bar (gray, 5 min) after the 10-minute mark. The timeline is visual and helps students structure their preparation.

**Notes:** "The 3 minutes of live demo are the most important 3 minutes of the presentation. Evaluators — including future employers who will hear about this course — remember whether the system worked and whether the student could explain what it was doing. Practice the live demo path more than anything else. The architecture slides and the business case can be recovered in Q&A; the live demo cannot."

---

## Slide 4 — What Makes an Excellent Final Project
**Layout:** Rubric deep dive

**Content:**
**Rubric: What Excellent Looks Like**

**Working System (35 points):**
- Excellent: All core features working; endpoint in production; CI/CD pipeline deployed; monitoring active; graceful degradation implemented
- Good: Core features working; endpoint deployed; some automation
- Adequate: System works but is not production-configured (no CI/CD, no monitoring)
- Below standard: System doesn't function end-to-end

**Architecture and Documentation (25 points):**
- Excellent: Comprehensive architecture diagram; 3+ ADRs with clear rationale; README that lets an engineer reproduce the environment; model card
- Good: Architecture diagram; brief documentation
- Adequate: Code without documentation; architecture diagram only
- Below standard: No documentation

**Business Case (20 points):**
- Excellent: Metric chain built; ROI calculated with explicit assumptions; sensitivity analysis; executive-quality briefing
- Good: ROI calculated; some assumptions stated
- Adequate: Cost estimated; value vague
- Below standard: No economic analysis

**Test Suite and Evaluation (10 points):**
- Excellent: Unit + integration + evaluation gate in CI/CD; gate actually rejects a bad model in tests
- Good: Unit and integration tests; manual evaluation
- Adequate: Some unit tests; no evaluation gate
- Below standard: No tests

**Presentation (10 points):**
- Excellent: Clear, confident; live demo works; Q&A answered with technical depth
- Good: Clear; demo works; Q&A answered
- Adequate: Disorganized but content is present; demo works
- Below standard: Demo fails; can't answer Q&A

**Figure:** *Rubric scorecard visual.* Five rows (one per rubric category) with four columns (Excellent/Good/Adequate/Below Standard). Each cell has a brief description and point range. A "Total: 100 points" row at the bottom. The visual clearly shows the weight of each category: Working System (35) is the largest, reflecting the course's emphasis on production-ready systems.

**Notes:** "The highest-weight rubric item is 'Working System' at 35 points — by design. This is an engineering course, and engineering means things that work. A beautifully documented system that doesn't run is not production-ready. A working system with rough documentation can still earn a B. A non-working system with excellent documentation cannot."

---

## Slide 5 — Demo Day I: Team Presentations
**Layout:** Presentation day logistics

**Content:**
**Demo Day I — Tuesday, December 8, 2026**

**Schedule:** (Adjust based on actual enrollment)
- 9:00-9:10 — Setup and sound check
- 9:10-9:25 — Team A: [Project Title]
- 9:25-9:40 — Team B: [Project Title]
- 9:40-9:55 — Team C: [Project Title]
- 9:55-10:10 — Team D: [Project Title]
- 10:10-10:25 — Break (15 minutes)
- 10:25-10:40 — Team E: [Project Title]
- 10:40-10:55 — Team F: [Project Title]
- 10:55-11:05 — Wrap-up and preview of Dec 10

**Hard rules:**
1. 10-minute presentation + 5-minute Q&A. Hard cutoff at 15 minutes.
2. Live demo required. Screenshots are backup, not primary.
3. Questions from instructor and TAs; peer questions welcome if time permits.
4. Audience: stay engaged. What your classmates built matters, and you'll be asked what you learned from each other.

**Audience engagement:**
Each observer should note:
- One architectural decision they found interesting
- One question they would ask about the business case
- One thing they would do differently

This becomes the basis for peer feedback given after all presentations are complete.

**Figure:** *Session timeline visual.* Horizontal timeline for Dec 8. Slots shown as color-coded blocks. Setup block (light gray). Presentation slots alternating two colors (for visual rhythm). Break block (white with coffee cup icon). The timeline ends with "Wrap-up." Total running time: ~115 minutes (including break). The visual helps students see where their slot falls.

**Notes:** "The audience engagement note-taking is deliberate. Watching a presentation passively is low-value. Watching a presentation with the mandate to identify one interesting decision, one business case question, and one thing you'd do differently turns you into an active evaluator. That's the skill you'll use in every architecture review meeting for the rest of your career."

---

## Slide 6 — Demo Day II: Final Presentations
**Layout:** Second presentation day

**Content:**
**Demo Day II — Thursday, December 10, 2026**

**Schedule:**
- 9:00-9:10 — Setup
- 9:10-9:25 — Team G: [Project Title]
- 9:25-9:40 — Team H: [Project Title]
- 9:40-9:55 — Individual Project 1: [Project Title]
- 9:55-10:10 — Individual Project 2: [Project Title]
- 10:10-10:25 — Break (15 minutes)
- 10:25-10:40 — Individual Project 3: [Project Title]
- 10:40-10:55 — Individual Project 4: [Project Title]
- 10:55-11:15 — Course Conclusion (20 minutes)

**Grades:**
- Grades posted within 72 hours of final presentation
- Rubric feedback sent via email for each category
- Office hours for grade questions: following week

**Lab 7 reminder:**
If you submitted Lab 7 and haven't received a grade, grades will be posted alongside final project grades on Dec 13.

**Figure:** *Dec 10 schedule mirror of Dec 8.* Same visual format as Dec 8 slide. Presentation slots through 10:55, then a "Course Conclusion" block highlighted in gold (different from the other slots). The gold block signals: this is the end of the course; it's deliberate; it's not administrative filler.

**Notes:** "The Course Conclusion happens at the end of Dec 10 for a reason: it should feel earned. By the 20-minute mark, every project has been shown. Every student has demonstrated the ability to build, deploy, and explain a production AI system. The conclusion is not a summary of the course — it's a reflection on what building these systems means."

---

## Slide 7 — Course Retrospective: What We Built Together
**Layout:** Course retrospective — visual inventory

**Content:**
**What You Built in 15 Weeks:**

**Lab 1 — Platform Foundation:**
Provisioned an AI platform from scratch: VPC, S3 zones, SageMaker Studio, IAM roles, Terraform IaC. You built the environment in which everything else runs.

**Lab 2 — Data Engineering:**
Built the NorthStar data pipeline: raw → curated → features → training datasets. Glue ETL jobs, Feature Store feature groups, data quality gates. The fuel that powers the models.

**Lab 3 — Model Development:**
Trained, tuned, and evaluated all three AI approaches: XGBoost churn prediction, RAG offer generation, ReAct customer service agent. MLflow experiment tracking. RAGAS evaluation.

**Lab 4 — Automated CI/CD:**
Built a CI/CD pipeline that automatically tests, evaluates, registers, and deploys. SageMaker Pipelines with ConditionStep evaluation gates. CodePipeline integration. DORA metrics before/after.

**Lab 5 — Production Deployment:**
Deployed to production with canary rollout: 10% → 30% → 50% → 100%. CloudWatch health gate Lambda. Automated rollback. Blue/Green for the RAG index.

**Lab 6 — Monitoring & Observability:**
Configured SageMaker Model Monitor, CloudWatch dashboards, alerting, RAGAS sampling pipeline, agent observability. Built a runbook.

**Lab 7 — Economics & Business Value:**
Cost taxonomy, unit economics, ROI calculation, FinOps implementation, executive briefing. Closed the loop from technical metrics to business value.

**Figure:** *Lab inventory visual.* Seven lab boxes arranged in the AISDLC arc: Platform → Data → Models → CI/CD → Deploy → Monitor → Economics. Each box has the lab number, a 1-line description, and the key artifact produced. Arrows connect them in sequence. The visual makes visible what was implicit: the labs were not isolated assignments — they were a sequential build of a production AI platform.

**Notes:** "Here's what's remarkable: you built a system that most organizations of 500 people don't have. A fully automated AI development lifecycle — from raw data to deployed model to monitored production system — with economic accountability. You did it in 15 weeks. In a graduate course. That's not a trivial achievement, and I want to name it explicitly."

---

## Slide 8 — The Durable Skills
**Layout:** Skills that outlast the technology

**Content:**
**What Stays When the Technology Changes:**

The AWS services you learned will change. SageMaker will be replaced by something else (or transformed beyond recognition). Bedrock's APIs will evolve. Claude 3.5 Sonnet will be succeeded by Claude 5, 6, beyond. The specific tools you learned have a half-life of 3-5 years.

**What doesn't change:**

**1. The discipline of rigor:**
The habit of: define the problem clearly → measure the baseline → test systematically → deploy carefully → monitor continuously → improve iteratively. This is not an AI pattern. It is an engineering pattern. It will be valid regardless of what AI systems look like in 2030.

**2. The skill of translation:**
The ability to explain a technical system to a non-technical executive. To write a business case that a CFO can act on. To design a governance process that a legal team can trust. These translation skills are increasingly rare and increasingly valuable as AI penetrates every industry.

**3. The instinct for failure modes:**
When you look at an AI system architecture, you now think: where does this fail? What's the fallback? How do we detect degradation? How do we roll back? This instinct is not default — you had to develop it. Keep it.

**4. The ethics reflex:**
Before we build something, we ask: who does this affect? What are the failure modes for fairness? What's the right human oversight design? What does this mean for privacy? This is not a compliance checkbox — it's how good engineers think.

**Figure:** *Four durable skills visual.* Four large circular icons: a gear (Discipline of Rigor), speech bubbles (Translation Skill), a lightning bolt (Failure Instinct), and a scale of justice (Ethics Reflex). Each with a 1-line description. Below: "The technology is the vehicle. These skills are the engine." Clean, memorable, suitable for a final slide.

**Notes:** "I want to push back on something you might be tempted to think: that what you learned in this course is AWS-specific and will be obsolete. That's not right. The technical vocabulary is AWS-specific. The engineering judgment underneath it is not. When Azure, Google Cloud, and whatever comes next look different from what you learned, your job is not to forget what you learned — it's to map the new thing to the pattern you already understand. That transfer is fast if the underlying pattern is solid. Make the pattern solid."

---

## Slide 9 — The State of Enterprise AI: What You're Walking Into
**Layout:** Industry landscape — 2026

**Content:**
**The Enterprise AI Landscape — Where You're Going:**

**What's changed in the last 2 years:**
- LLM capabilities have crossed the threshold for many enterprise tasks; the question is no longer "can it?" but "how do we operate it?"
- The profession of AI engineering is maturing — MLOps, LLMOps, and AgentOps are recognized job functions
- Enterprise AI governance frameworks (EU AI Act, NIST AI RMF, ISO 42001) are becoming compliance requirements, not optional
- The cost of AI development is falling rapidly; the cost of AI failures is rising

**Where the skill gaps are (and where you fit in 2027):**
The biggest gaps in the enterprise AI market are not in model research. They are in:
1. **Production engineering:** Building systems that actually work reliably in production
2. **Economic accountability:** Connecting AI investments to business outcomes with credible evidence
3. **Governance and compliance:** Making AI systems that satisfy regulators and governance boards
4. **Translation:** Helping organizations make good AI decisions, not just technical decisions

**The "valley of death" for enterprise AI:**
Organizations invest heavily in AI exploration (proofs of concept, pilots) and fail to operationalize it. The POC-to-production ratio remains very low. The engineers who can close that gap are extraordinarily valuable.

**Figure:** *Enterprise AI maturity distribution.* Bell curve showing the distribution of enterprise AI programs by maturity: Level 0-1 (ad hoc, 35%), Level 2-3 (managed, 45%), Level 4-5 (optimized, 20%). Arrow pointing to Level 4-5: "Where this course prepares you to work." The distribution communicates both the opportunity (most organizations are still maturing) and the differentiation (engineers who can operate at L4-5 are rare).

**Notes:** "The enterprise AI market in 2026 looks like the DevOps market in 2015: technically sophisticated, rapidly evolving, and massively under-staffed with engineers who understand both the technology and the operational discipline to run it in production. You are entering a market where your skills are scarce and increasingly valued. That's a good position to be in — as long as you keep learning."

---

## Slide 10 — Career Paths from Here
**Layout:** Career trajectory options

**Content:**
**What Comes Next — Career Paths:**

**Path 1: ML/AI Engineer → Senior ML Engineer → Staff ML Engineer**
Build AI systems at scale. Focus: production engineering, MLOps/LLMOps, platform development. Companies: hyperscalers, AI-native startups, large enterprises with mature AI programs.
*Next steps: Contribute to an open-source MLOps project; get AWS Machine Learning Specialty certification; build a public portfolio with one complete production system.*

**Path 2: AI Architect → Principal Architect → AI Platform Lead**
Design the systems that engineering teams build. Focus: architecture patterns, platform decisions, technical strategy. Companies: consulting firms, large enterprises, system integrators.
*Next steps: Deep-dive into the AWS Well-Architected Framework (ML lens); study 2-3 real enterprise AI architectures; get the Solutions Architect Professional certification.*

**Path 3: AI Product Manager / Technical PM**
Bridge AI capabilities and business requirements. Focus: product strategy, stakeholder management, economic analysis. Companies: any company building AI-powered products.
*Next steps: Study AI product frameworks (build vs. buy, make vs. partner); practice the business case format from Lab 7; develop a PM portfolio.*

**Path 4: AI Governance / Responsible AI**
Ensure AI systems are trustworthy, compliant, and ethical. Focus: governance frameworks, EU AI Act, fairness, explainability. Companies: large enterprises, regulators, consultancies.
*Next steps: Read EU AI Act in full; study NIST AI RMF; contribute to an AI policy working group.*

**Path 5: Research → Applied AI**
Push the frontier and bring it to production. Focus: research plus systems thinking.
*Next steps: Graduate school; paper-reading habit; contribute to reproduction studies.*

**Figure:** *Career path branching diagram.* A decision tree: "CS 401R graduate" branches into five paths, each with an icon, a 2-word description (Engineer, Architect, PM, Governance, Research), and 1-3 company logos or industry segments as examples. The diagram makes visible that the course prepares for multiple roles, not just "ML Engineer."

**Notes:** "The career path question I get most often is: 'Should I specialize in LLMs or in classical ML?' Wrong question. Specialize in production AI systems — which means you need to know both. The engineers who will be most valuable in 2027-2030 are those who can work across the full stack: data, classical models, LLMs, agents, and the infrastructure that runs them all. That's what this course is built for. Don't voluntarily narrow yourself before the market forces you to."

---

## Slide 11 — Recommended Continuing Education
**Layout:** What to read, build, and follow

**Content:**
**Keep Learning: Recommended Resources**

**Books (read these within the next 12 months):**
- *Designing Machine Learning Systems* — Chip Huyen (production ML; very aligned with this course)
- *Machine Learning Engineering* — Andriy Burkov (practical, implementation-focused)
- *Building LLM Applications for Production* — Chip Huyen (LLMOps focused)
- *Fundamentals of Data Engineering* — Joe Reis & Matt Housley (deep data engineering foundation)

**Papers (bookmark these):**
- "Hidden Technical Debt in Machine Learning Systems" — Sculley et al., NIPS 2015 (still the canonical paper on ML technical debt)
- "Challenges in Deploying Machine Learning" — Paleyes et al., 2022 (production deployment survey)
- "RAGAS: Automated Evaluation of Retrieval Augmented Generation" — Es et al., 2023

**Podcasts/newsletters:**
- *The TWIML AI Podcast* (This Week in Machine Learning)
- *Practical AI* podcast
- *The Batch* (Andrew Ng's newsletter)
- AWS Machine Learning Blog

**Communities:**
- MLOps Community (mlops.community) — Slack, meetups, papers
- Hugging Face community — open-source model ecosystem
- LangChain Discord — agentic systems community

**What to build next:**
- Take your final project to a real production environment (or contribute it to a real organization's AI program)
- Contribute to an open-source MLOps tool (MLflow, Prefect, Ray, Feast)
- Write a technical blog post about what you built in this course

**Figure:** *Recommended resources visual.* A curated bookshelf graphic featuring four book spines labeled with their titles and authors. Below the bookshelf: icons for papers (scroll), podcasts (headphones), communities (network), and building (hammer). Clean, inspiring, actionable. This is a slide students can photograph.

**Notes:** "The half-life of the specific tools is 3-5 years. The half-life of the fundamentals in Chip Huyen's books is 10-15 years. Read the fundamentals first. They'll give you the conceptual anchor that makes learning new tools fast. Chip Huyen in particular writes at exactly the level of rigor this course targets — if you liked this course, you'll like her books."

---

## Slide 12 — Acknowledging the Difficulty
**Layout:** Honest reflection

**Content:**
**This Course Was Hard. That Was Intentional.**

Seven labs. Seven different AWS services deeply understood. Three AI paradigms implemented. A full CI/CD pipeline. A monitoring system. An economic analysis. A governance framework.

That's a lot. More than most undergraduate courses. Comparable to the first year of production AI work at many companies.

**Why so much?**

Because the problems you'll encounter in production are not toy problems. They don't come with clean datasets and working environments. They come with:
- Data pipelines that break at 3 AM on a Friday
- Models that drift during the Q4 holiday season
- Executive stakeholders who need a business case, not a confusion matrix
- Regulators who want a model card and an audit log
- Engineers who are stuck on a ConditionStep that won't evaluate correctly

The course was calibrated to give you a taste of that difficulty — safely, with a safety net, with office hours and TAs. Real production systems don't have that safety net.

**What you built despite the difficulty:**

You built it anyway. That's the point.

**Figure:** *A simple, powerful visual.* White slide. Large text: "You built it anyway." Below in smaller text: the seven lab titles, numbered 1-7. No other decoration. The simplicity is deliberate — it creates a moment of silence and reflection in the final session.

**Notes:** "I'll be direct with you: I designed this course to be harder than you expected, and I tracked the rate of completion carefully. The students who make it through are not necessarily the ones who found it easy — they're the ones who kept going when it was hard. That persistence is the skill that compounds in a career. The technical knowledge doubles every few years. The persistence to work through hard problems compounds for decades."

---

## Slide 13 — The NorthStar Story: What We Built
**Layout:** NorthStar case study conclusion

**Content:**
**NorthStar Retail: The Final Picture**

We started with a 400-store, $3.2B retailer with a manual, fragmented approach to customer intelligence.

**Where we ended up:**

| System | Status | Business Impact |
|--------|--------|-----------------|
| Churn Prediction (XGBoost) | Production, monitored, versioned | 18% reduction in churn rate; $639K/month value |
| RAG Offer Generation (Bedrock) | Production with guardrails | 23% offer conversion rate vs. 11% baseline |
| ReAct Customer Service Agent (Bedrock Agents) | Production with HITL oversight | 67% self-service resolution rate; 34% cost reduction |

**Platform maturity: Level 3 → approaching Level 4**
- Full CI/CD automation
- Automated monitoring with alerting
- Economic accountability with FinOps
- Governance framework deployed
- Error budget management operational

**What NorthStar doesn't have yet (Level 4-5):**
- Fully autonomous retraining triggers
- Cross-system feature sharing (the data flywheel at full scale)
- Federated learning for privacy-preserving model improvement
- Advanced causal inference for business value attribution

**Figure:** *NorthStar before/after comparison.* Split view: "Before" (Week 1 state) and "After" (Week 15 state). Before: three disconnected systems, no monitoring, no CI/CD, manual deployment, no economic accountability. After: unified platform, full automation, monitoring stack, FinOps, governance framework. The visual makes visible the journey that the course guided students through using NorthStar as the through-line.

**Notes:** "NorthStar was always a stand-in for your actual work. The specific numbers were illustrative, not real. But the architecture is real. The patterns are real. The failure modes are real. If you take a job next year at a company that has a churn prediction model in production — and there is a very good chance you will — the XOps discipline, monitoring patterns, and economic accountability you learned via NorthStar will transfer directly. That was the point of the case study."

---

## Slide 14 — The Larger Context: Why This Matters
**Layout:** Mission and purpose

**Content:**
**Why Building Good AI Systems Matters:**

AI is not a technology trend. It is a structural shift in how organizations process information and make decisions. In the next 5-10 years, every significant organization — in healthcare, finance, logistics, education, government, non-profit — will have AI systems embedded in their core operations.

**The stakes:**

Those systems will make decisions that affect people's access to healthcare, financial options, employment, and education. They will be built by engineers like you.

**The responsibility:**

The principles you learned — fairness testing, privacy by design, explainability, human oversight, governance frameworks, error budgets, graceful degradation — are not bureaucratic overhead. They are the difference between AI systems that help people and AI systems that harm them.

**The opportunity:**

The engineers who understand both the technical depth and the ethical-operational discipline will shape what enterprise AI looks like for the next decade. That's not hyperbole. The frameworks being built now — the MLOps standards, the governance patterns, the monitoring norms — are being established by engineers at the beginning of their careers. You are at the beginning.

**Build things that help people. Hold to that.**

**Figure:** *Mission visual.* Large background: a subtle world map or organizational network graphic. Foreground text: "AI systems that help people." Below: three columns — Healthcare, Finance, Education — each with one example of AI having a positive impact and one example of AI causing harm (both preventable with the practices from this course). The visual grounds the technical course in human consequence.

**Notes:** "I want to end on this note because I believe it. After 40 years in technology, I've seen waves of change that were supposed to transform everything — and most of them transformed some things and left others untouched. AI is different. The speed, breadth, and depth of penetration into decision-making — it's different in kind, not just in degree. The engineers who build these systems carry real responsibility. Build things that hold up under scrutiny. Build things you'd be comfortable having your children use. That's the bar."

---

## Slide 15 — Thank You & See You in the Future
**Layout:** Course conclusion — final slide

**Content:**
**Thank You.**

To the students who showed up when the ConditionStep wouldn't evaluate.

To the students who figured out the Feature Store schema at midnight.

To the students who wrote the Executive Briefing and then rewrote it because the ROI wasn't credible.

To the students who stayed for office hours not because they were behind, but because they were curious.

**You are prepared. Go build things that matter.**

---

**CS 401R: Engineering Production AI Systems**
**Fall 2026 | Brigham Young University**

---

**Contact:**
Office hours continue through the grade posting period.
For research and mentoring conversations: email or LinkedIn.

**One last thought:**

> *"The best time to plant a tree was 20 years ago. The second best time is now."*

The best time to build production-ready AI engineering discipline was at the beginning of your career. You just did it. The compounding starts now.

**Figure:** *Simple, final visual.* Clean white slide with the course title in large text at the top. At the center: the AISDLC wheel from Lecture 2 — all 8 stages filled in, completed, cycling. At the bottom: "CS 401R · Fall 2026 · Brigham Young University." The AISDLC wheel, appearing one final time, serves as a bookend to Lecture 2's introduction of the framework — the course began with an empty framework and ends with one fully understood and implemented.

**Notes:** "The final slide is the final word. I want the last thing students see to be the AISDLC wheel — complete, cycling, running. Because that's what they built. They didn't just learn a framework. They implemented it. End of class."
