---
lecture: L25
title: Project Workshop I — Architecture Review
date: Tuesday, December 1, 2026
week: 14
arc: Project
reading_due: "None — project work"
lab_due: "Lab 7 due Sat Dec 5 (4 days); Final Project due Dec 10"
slides_target: 10
---

# L25: Project Workshop I — Architecture Review
**Tuesday, December 1, 2026 | CS 401R: Engineering Production AI Systems | Fall 2026**

> No new content today. This session is a working studio: bring your final project, get feedback, unblock problems, and hear what your classmates are building. The time you spend here is the highest-leverage time of the semester.

**Lab 7 Due:** Sat Dec 5 (4 days)
**Final Project Due:** Finals Week (Dec 8-10)

---

## Slide 1 — Workshop Introduction
**Layout:** Full slide with session structure

**Content:**
- Project Workshop I
- CS 401R · Lecture 25 · Tuesday, December 1, 2026
- Studio session: bring your project, get feedback, ship

**Session agenda (75 minutes):**
- 0:00-0:05 — Session context and Lab 7 reminder
- 0:05-0:35 — Architecture Review Rotation (students present 3 minutes each; feedback 2 minutes)
- 0:35-0:55 — Open lab time: work time, office hours-style help from instructor
- 0:55-1:10 — Common issues debrief (based on what came up during work time)
- 1:10-1:15 — Final project expectations and Dec 8-10 agenda

**What to bring:**
- Architecture diagram (drawn or Terraform-derived) of your final project
- One technical challenge you're stuck on
- A draft of your business case (or at least the value hypothesis)

**Figure:** *Workshop session flow visual.* Horizontal timeline: Architecture Review (30 min) → Open Lab Time (20 min) → Common Issues Debrief (15 min) → Final Expectations (5 min). Icons: architecture diagram (for Architecture Review), laptop (Open Lab Time), group discussion (Debrief), checklist (Expectations). The timeline is clear and communicated at the start of the session so students know what to expect.

**Notes:** "The Architecture Review Rotation is structured: 3 minutes to show your architecture, 2 minutes for peer and instructor feedback. No live demos — architecture diagrams and screenshots only. The goal is: before you leave today, someone else has seen your design and given you at least one concrete improvement suggestion. That feedback loop is the entire value of Workshop I."

---

## Slide 2 — Architecture Review: What Good Looks Like
**Layout:** Architecture review criteria and examples

**Content:**
**What Makes a Strong Final Project Architecture:**

**1. Completeness across the AISDLC:**
Does the architecture cover all stages? Platform → Data → Models → CI/CD → Deployment → Monitoring → Economics? Missing stages create gaps that are hard to fill in the final week.

**2. Appropriate scope:**
The best projects are focused, not sprawling. One well-engineered AI system with a full operational infrastructure beats three poorly engineered systems. Depth over breadth.

**3. Novel problem domain:**
Projects on churn prediction will be compared to NorthStar (they will look the same). Choose a problem domain that's yours: inventory, fraud, recommendation, healthcare scheduling, educational AI, supply chain.

**4. Clear business hypothesis:**
Every project should be able to answer: "If this AI system works perfectly, what business outcome does it improve and by how much?" If you can't answer this, the business case section of the final will be weak.

**5. Realistic scope:**
A complete system with core required features beats an ambitious system with half the features implemented. Be honest about what you can finish in 9 days.

**Architecture Review Template (3 minutes):**
1. Problem domain: what problem are you solving? (30 seconds)
2. Architecture overview: which components? (1 minute, show diagram)
3. AI approach: custom model, RAG, agent, or all three? (30 seconds)
4. Biggest risk: what could stop you from finishing? (1 minute)

**Figure:** *Architecture quality rubric.* Five-row rubric: AISDLC Completeness (0-4 points), Scope Appropriateness (0-4 points), Novel Domain (0-4 points), Business Hypothesis (0-4 points), Technical Depth (0-4 points). Maximum: 20 points. Example rating for a hypothetical project: "Healthcare appointment scheduling AI — 4+3+4+4+3 = 18/20 — strong project." The rubric communicates: what the instructor is looking for in the architecture review (and eventually in the final project).

**Notes:** "The biggest risk that consistently appears in Workshop I is scope. Students have built something ambitious; they're halfway through it and 9 days from the deadline. The honest conversation: what's the minimum viable version of this project that demonstrates the core principles? Can we implement that in 9 days? Often the answer is yes — but it requires scope reduction, not harder work."

---

## Slide 3 — Common Architecture Issues (Pre-Workshop Survey Results)
**Layout:** Issues surfaced from pre-class check-in

**Content:**
**Common Issues (from pre-class survey):**

*(Slide content will be populated based on actual pre-workshop survey results; template below)*

**Issue Category 1 — Lab 4 CI/CD dependency problems:**
Teams whose final project depends on a working CI/CD pipeline but whose Lab 4 has unresolved issues. The Lab 4 CI/CD is the critical path for the final project's deployment automation.
*Resolution:* Fix Lab 4 first; use a simplified manual deployment path as fallback for the final project.

**Issue Category 2 — Feature Store schema design:**
Teams designing their Feature Store who are uncertain about what to include.
*Resolution:* Design backward from the model input: what features does the model need? → design the Feature Group to produce those features → design the ETL to produce those Feature Group records.

**Issue Category 3 — Business case value hypothesis:**
Teams who have built something technically interesting but can't articulate the business value.
*Resolution:* Start with: who are the users? What decision do they make better with this AI? What's the consequence (in $) if they make a better decision? Work backward from that.

**Issue Category 4 — Scope overrun:**
Teams with 3+ AI systems planned but insufficient time to implement all three well.
*Resolution:* Pick the one AI system that best demonstrates the range of skills. Implement it completely. Describe what the other two would look like in your architecture documentation.

**Figure:** *Issue frequency bar chart.* Horizontal bar chart from the pre-class survey: "Lab 4 dependency" (35% of teams), "Business case unclear" (28%), "Scope overrun risk" (22%), "Feature Store design" (15%). Color-coded by urgency: Lab 4 dependency in red (must resolve), others in amber (important but manageable). The chart motivates the workshop's focus areas.

**Notes:** "The pre-survey results are the input that makes Workshop I useful. Without knowing what the class is stuck on, workshop time is unfocused. With the survey, the instructor can prioritize the most common issues and address them efficiently in the Common Issues Debrief. If you haven't submitted the pre-survey, do it before we start the Architecture Review Rotation."

---

## Slide 4 — Lab 7 Final Checklist
**Layout:** Lab 7 submission checklist — 4 days out

**Content:**
**Lab 7 Final Checklist (Due Saturday December 5):**

**Part 1 — Cost Analysis:**
- [ ] AWS Cost Explorer data pulled (actual or estimated)
- [ ] Cost taxonomy complete (all 7 categories)
- [ ] Cost per unit calculated (per prediction, per offer, per session)
- [ ] Monthly cost breakdown by system

**Part 2 — Value Analysis:**
- [ ] Metric chains built for all active AI systems
- [ ] Value per unit estimated with explicit assumptions
- [ ] Monthly value calculated per system
- [ ] ROI computed

**Part 3 — Optimization Recommendations:**
- [ ] Top 3 opportunities identified
- [ ] Effort and savings estimated for each
- [ ] Recommendation ranked by ROI

**Part 4 — FinOps Implementation:**
- [ ] Cost allocation tags added to remaining untagged resources
- [ ] AWS Budgets configured (3 budgets minimum)
- [ ] Cost dashboard created in CloudWatch

**Part 5 — Executive Briefing:**
- [ ] 1-page format (literally one page)
- [ ] Audience: CFO (no technical jargon without explanation)
- [ ] Includes: 3-year TCO, 3-year value, ROI, key risks, recommendation
- [ ] Reviewed by at least one non-technical person

**Figure:** *Lab 7 completion tracker.* Five-part checklist with completion percentages for a hypothetical typical student after the workshop session. Part 1: 80% complete (mostly done). Part 2: 40% complete (in progress). Part 3: 0% complete (not started). Part 4: 20% complete (started). Part 5: 0% complete (not started). "Priority for this week: finish Part 2 → start Part 3 → Executive Briefing (can be done last, takes 2-3 hours)."

**Notes:** "The Executive Briefing takes 2-3 hours to do well and should be the last thing you write — after your analysis is complete. Don't start with the briefing; start with the numbers. Once you have the cost analysis, value analysis, and optimization recommendations, the briefing writes itself from those inputs. The common mistake: writing the briefing before the analysis and then having to revise it when the numbers come in different from assumptions."

---

## Slide 5 — Final Project: What to Submit
**Layout:** Final project submission requirements

**Content:**
**Final Project Submission (Due Dec 10):**

**Deliverable 1: Architecture Documentation**
- Architecture diagram (Lucidchart, draw.io, Excalidraw, or Terraform-generated)
- Architecture Decision Records (minimum 3: platform, data, AI approach)
- README with: problem statement, system description, how to run

**Deliverable 2: Working Code**
- Terraform IaC for all infrastructure
- Python code for all Lambda functions, Glue jobs, SageMaker scripts
- Test suite (unit + integration + evaluation gate)
- CI/CD pipeline configuration (buildspec.yml, pipeline definition)

**Deliverable 3: Model Artifacts and Documentation**
- Model card (for custom models)
- Evaluation report (with gate criteria and results)
- MLflow experiment log (at least 3 tracked experiments)

**Deliverable 4: Business Case**
- 1-page executive briefing (from Lab 7 template)
- ROI calculation with explicit assumptions
- Sensitivity analysis

**Deliverable 5: Demo Presentation (Dec 8-10)**
- 10-minute presentation + 5-minute Q&A
- Show: working system end-to-end (prediction/offer/agent)
- Explain: architecture, key decisions, business value
- Q&A: be ready for technical and business questions

**Grading weights:**
- Working system (functional): 35%
- Architecture and documentation: 25%
- Business case and economic analysis: 20%
- Test suite and evaluation gate: 10%
- Presentation: 10%

**Figure:** *Final project grading rubric.* Five-row rubric with weight, criteria, and example of excellent vs. adequate performance for each. "Working system" row: excellent = all three AI approaches implemented, full operational stack; adequate = one AI approach, working CI/CD. "Business case" row: excellent = RCT design, sensitivity analysis, and a CFO-ready briefing; adequate = a rough ROI estimate without supporting analysis.

**Notes:** "The demo presentation is not a slideshow about what you built — it's a live demonstration of a working system. Boot your SageMaker Studio, show your endpoint running, invoke it with a real request, show the CloudWatch monitoring dashboard, show the Model Monitor report. Executives and technical evaluators both want to see a system that works, not slides that describe a system."

---

## Slide 6 — Project Workshop: Open Lab Time
**Layout:** Working session slide

**Content:**
**Open Lab Time — 20 Minutes**

Use this time for:
- Getting unstuck (raise your hand; instructor and TAs circulate)
- Sketching your architecture for peer review
- Finishing the Lab 7 components you haven't started
- Reviewing the final project rubric and identifying gaps

**Instructor office hours schedule this week:**
- Tuesday Dec 1 (today): after class until 5 PM
- Wednesday Dec 2: 2-5 PM
- Thursday Dec 3: 2-5 PM
- Friday Dec 4: 10 AM - 12 PM (final hours before Lab 7 due)
- Monday Dec 7: 2-5 PM (pre-final-project support)

**No office hours Dec 8-10 (final presentations)**

**Resources:**
- Lab 7 template notebook: `Labs/Lab_7/lab7_economics_template.ipynb`
- Final project spec: `Final Project/final_project_spec.md`
- Architecture diagram template: `Final Project/architecture_template.drawio`
- Executive briefing template: `Final Project/executive_briefing_template.md`

**Figure:** *Open lab time visual.* Minimal slide — just the office hours schedule as a clean calendar graphic (week of Dec 1-7 with hours highlighted). "Ask for help early — not the night before Lab 7 is due." Simple, clear, directly useful.

**Notes:** "The office hours this week are unusually dense for a reason: Labs 7 and the final project overlap. If you're working on Lab 7 Part 5 (Executive Briefing) and you're unsure whether your ROI calculation is credible, bring it to office hours Thursday. If you're stuck on the final project architecture, bring a draft diagram to Monday's session. The instructor can't help you if you wait until the night before."

---

## Slide 7 — Common Issues Debrief
**Layout:** Issues surfaced during open lab time

**Content:**
**Common Issues from Today's Workshop:**

*(Slide populated live based on what emerged during open lab time)*

**Template sections — populated in class based on actual issues observed:**

**Technical Issue 1:** *(populated live)*
Description of the issue and solution

**Technical Issue 2:** *(populated live)*
Description of the issue and solution

**Business Case Issue:** *(populated live)*
Common mistake and correction

**Scope Question:** *(populated live)*
Scope management advice based on what teams are attempting

**Figure:** *Issue board visual.* Blank whiteboard-style layout with four quadrant sections: Technical Issues, Business Case Issues, Scope Issues, Other. Sticky note placeholders in each section — filled in during the workshop. The whiteboard visual communicates: this slide is dynamic and will reflect what the class actually struggled with.

**Notes:** "The Common Issues Debrief is the most valuable 15 minutes of the workshop — it converts the specific struggles of individual students into shared learning for the whole class. If you struggled with something today that got resolved, it's likely 5 other students had the same struggle. Sharing the resolution is a gift to your classmates. Don't be shy about what you were stuck on."

---

## Slide 8 — What to Expect at the Final Presentations
**Layout:** Presentation day logistics and expectations

**Content:**
**Final Presentations — December 8, 10 (and 3 if needed)**

**Format:**
- 10-minute presentation + 5-minute Q&A per team/individual
- Live demo required (not a recorded video)
- Architecture diagram as the backbone (show on screen while explaining)

**What the Q&A looks like:**
Questions from instructor and TAs will fall into three categories:
1. **Technical deep dive:** "How does your canary deployment rollback work? Walk me through the Lambda logic."
2. **Design decision:** "Why did you choose XGBoost over a neural network for this problem?"
3. **Business value:** "What would it take for your ROI estimate to be negative? What's the most important assumption?"

**Presentation schedule:**
- Dec 8: Teams A-D (as assigned)
- Dec 10: Teams E-H + individual projects

**Physical setup:**
- Bring your own laptop; HDMI adapter available
- Connect 10 minutes before your slot
- Have AWS Console and SageMaker Studio open and logged in before you start

**What to demo specifically:**
1. A real prediction/offer/agent response (live, not cached)
2. CloudWatch monitoring dashboard (show at least 2 metrics with history)
3. Model Registry (show the registered model with metadata)
4. One piece of your test suite (run a test live or show the test output)

**Figure:** *Presentation day schedule visual.* Timeline for Dec 8 and Dec 10. Each slot: 15 minutes (10 presentation + 5 Q&A). Teams/individuals listed by slot. Setup note: "Arrive 10 minutes before your slot." "Technical check before presentations begin" label at the start of each day.

**Notes:** "The live demo requirement is non-negotiable. If your system doesn't work in real time, that's a significant deduction. Test your demo path end-to-end the night before, including logging into SageMaker Studio, invoking your endpoint, and opening your CloudWatch dashboard. Do it from the laptop you'll use for the presentation. If anything is broken the night before, you have one night to fix it."

---

## Slide 9 — Looking Back: What the Course Was Really About
**Layout:** Course retrospective

**Content:**
**What CS 401R Was Really About:**

The title says "Engineering Production AI Systems." The content was about something bigger.

**It was about systems thinking:**
Building AI that works in isolation (a model in a notebook) is easy. Building AI that works reliably within an organization — with data pipelines, CI/CD, monitoring, governance, and business accountability — is hard. Systems thinking is the skill that makes the hard version tractable.

**It was about professional responsibility:**
AI systems affect real people. The churn model affects which customers get retention offers. The agent affects how customer service issues are resolved. The offer system affects what customers buy. These are decisions with ethical, fairness, and privacy dimensions. The technical decisions you make have human consequences.

**It was about communication across boundaries:**
Technical excellence is necessary but not sufficient. The ability to explain AUC to a CFO, to design a model card for a governance officer, to write a business case for a VP — these are the skills that determine whether your technical work creates business value or sits on a server unread.

**It was about humility:**
The Zillow Offers failure ($569M loss), the Amazon recruiting bias, the Zestimate drift — every cautionary tale in this course is about smart engineers building technically sophisticated systems that failed because of assumptions that weren't questioned. The discipline of testing, monitoring, and governance is the operationalization of intellectual humility.

**Figure:** *Four-theme visual.* Four large text blocks: Systems Thinking, Professional Responsibility, Communication, Humility. Each with a 1-sentence expansion. Clean, minimal, reflective. This is not a technical slide — it's a values-in-practice slide.

**Notes:** "I'll say the quiet part out loud: the technical content of this course will be partially obsolete in 3-5 years. The tools will change. SageMaker will be replaced by something else. Bedrock will look different. Claude will be superseded. But systems thinking, professional responsibility, the ability to communicate across boundaries, and intellectual humility — those are the durable skills. Build those and the technical skills take care of themselves."

---

## Slide 10 — The Final Push: Dec 1-10 Plan
**Layout:** Week-by-week countdown

**Content:**
**Your Dec 1-10 Plan:**

**Dec 1-4 (this week — Lab 7 priority):**
- Finish Lab 7 Parts 1-3 (cost and value analysis, optimization recommendations)
- Implement Lab 7 Part 4 (FinOps — tags, budgets, dashboard)
- Write Lab 7 Part 5 (Executive Briefing — 2-3 hours, do it after analysis is done)
- Lab 7 submitted by Friday midnight

**Dec 5-7 (weekend + Monday — final project sprint):**
- Final project: close all open issues identified in today's workshop
- Complete any missing components (usually: test suite, runbook, business case)
- Run end-to-end demo path; fix anything broken
- Practice the 10-minute presentation

**Dec 8 or 10 — Presentation day:**
- Live demo; Q&A
- This is your portfolio moment; make it count

**The mindset for the final push:**
- Done is better than perfect. A complete, working, documented system beats an ambitious partially-implemented system.
- Ask for help now. Office hours are open. TA Slack channel is active. Don't suffer alone.
- Take care of yourself. Sleep. The work goes better when you're rested.

**Figure:** *Dec 1-10 countdown calendar.* Week view: Dec 1-4 (Lab 7 week, color: amber), Dec 5-7 (Final project sprint, color: teal), Dec 8-10 (Presentation week, color: gold). Key dates marked: Lab 7 due (Dec 5), Presentations (Dec 8, Dec 10). "Today" marker on Dec 1. The calendar communicates the schedule clearly and makes the timeline feel manageable.

**Notes:** "The most important advice for the final push: decide today what your final project scope is and commit to it. Scope creep in the last 9 days is the #1 cause of incomplete final projects. Whatever you have today — that's your scope. Make it complete, make it documented, make it work reliably for the demo. That's the goal. Not bigger — better."
