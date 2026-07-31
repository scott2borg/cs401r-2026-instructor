# L19: Security, Privacy & Compliance II — The Build→Operate Bridge — Figures

## Slide 1 — Title

**Figure:** *Build→Operate arc bridge visual.* Left side: the NorthStar platform architecture (compressed) labeled "Built." Right side: four Operate arc questions floating above the platform: "Is it still working?" "Is it fair?" "Is it worth it?" "Who's accountable?" A bridge spanning the two sides, with this lecture labeled on the bridge. The visual communicates: the platform exists; now comes the harder question of whether it deserves to run.

---

## Slide 2 — What "Trustworthy AI" Means in Practice

**Figure:** *HLEG trustworthy AI checklist visual.* Seven requirement cards arranged in a grid. Each card: requirement name, NorthStar status (✅/⚠️), and key control. Two amber cards (Human oversight, Societal wellbeing) stand out from the five green cards. The visual communicates: NorthStar after Labs 1-5 is substantially trustworthy, with two areas for improvement.

---

## Slide 3 — Case Study: When AI Goes Wrong at Enterprise Scale

**Figure:** *Bias feedback loop diagram.* Circular flow: Historical underservice of Group A → Group A has higher historical churn rate → Churn model predicts high churn for Group A → Business invests less in retaining Group A → Group A churns more → More historical data showing Group A churns → Model continues to predict high churn. The self-reinforcing loop communicates: without active fairness intervention, historical bias perpetuates into the future.

---

## Slide 4 — Responsible AI Governance: Organizational Structure

**Figure:** *AI governance organizational chart.* Four-level pyramid: Individual (wide, bottom), Team (middle), Governance Function (narrow), Executive (top). Each level: role, responsibilities, escalation path. Arrows show: unresolved issues escalate from Individual → Team → Governance → Executive. The pyramid communicates: governance is not a tax on ML teams — it's a distributed accountability system.

---

## Slide 5 — AI System Inventory: Managing What You've Built

**Figure:** *AI system inventory table.* The table above, formatted as a professional registry card. "Status" column uses traffic-light colors: Production (green), Development (amber), Rejected (red). "Risk Class" column uses the EU AI Act color scheme. Last-reviewed date with "Overdue" flag if >6 months. The inventory communicates: AI governance requires knowing what's running, not just governing what you're building today.

---

## Slide 6 — Practical Responsible AI: What You Actually Do

**Figure:** *Responsible AI checklist across AISDLC stages.* AISDLC pipeline (8 stages) at top. Below each stage: 2-3 responsible AI checklist items. Checkmarks and status indicators. The visual shows: responsible AI is woven through the full AISDLC, not added at the end. It's a thread through the lifecycle, not a stage.

---

## Slide 7 — AI Ethics in Context: Christian Values and Enterprise AI

**Figure:** *Values-to-controls diagram.* Four values (Dignity, Honesty, Service, Justice) as circular nodes. From each node: arrows pointing to specific technical controls: Dignity → SHAP explainability; right to appeal. Honesty → Model card; disclosure in UI. Service → HITL review; customer feedback loop. Justice → Fairness audit; Clarify bias detection. The diagram shows that values translate into engineering decisions.

---

## Slide 8 — The AISDLC Complete: Stage Gates and Return Loops

**Figure:** *Full AISDLC with lab artifacts.* 8-stage pipeline with artifact cards under each stage showing what the labs produced at that stage. Stage gates shown between stages. Return loops: Stage 6 failure → back to Stage 5 (retrain). Stage 2 quality gate failure → back to Stage 1 (re-scoping). Stage 8 drift detected → back to Stage 3 (new features) or Stage 5 (retrain). The diagram is the complete picture of what the course has built.

---

## Slide 9 — Threat Modeling Workshop: NorthStar Attack Surface

**Figure:** *STRIDE matrix for NorthStar Agent.* 6-row table (one per STRIDE category). Columns: Threat, Existing Control, Control Effectiveness (1-5), Gap. Students fill in the last two columns during the exercise. "Spoofing" row pre-filled as example: Existing Control = "IAM authentication on API Gateway," Effectiveness = 4, Gap = "Session fixation attacks not addressed." The pre-filled row models the expected response quality.

---

## Slide 10 — Debrief: NorthStar Threat Model

**Figure:** *Threat matrix with severity heat map.* STRIDE category × Severity matrix. High-severity cells in red (Information Disclosure, Elevation of Privilege). Medium-severity cells in amber (DoS). Low-severity cells in green (Spoofing, Tampering, Repudiation — controls in place). The heat map communicates: focus remediation on the red cells.

---

## Slide 11 — Responsible AI Communication: Talking to Executives

**Figure:** *Stakeholder communication matrix.* Four-quadrant diagram: x-axis: Technical Detail (low to high); y-axis: Business Impact (low to high). Four audience labels placed in quadrants: Executives (high business, low technical), Compliance (medium both), Customers (low technical, medium business), Engineers (high both). Four speech bubbles showing the same risk framed for each audience. The matrix shows the same risk across four different framings, each appropriate to the audience.

---

## Slide 12 — Lab 5 Final Guidance: Common Issues and Solutions

**Figure:** *Lab 5 checklist card.* Six-item checklist with common issue callouts next to the two most problematic items (canary weight vs. endpoint update; auto-scaling variant vs. endpoint). Time estimate: "With working Lab 4: 15-20 hours for Lab 5. Start today."

---

## Slide 13 — The AI Governance Maturity Model

**Figure:** *AI governance maturity staircase.* Four steps (Level 0-3). Each step: maturity level name, organizational characteristics, example capabilities. NorthStar "course target" bracket spanning Level 1-2. "Industry average" marker at Level 0-1. "Leading enterprises" marker at Level 2. The staircase communicates: governance maturity is a journey; the course takes you materially up the staircase.

---

## Slide 14 — What's Coming: The Operate Arc

**Figure:** *Operate arc timeline.* Five sessions (L20-L24) on a horizontal timeline. Each session: topic, one-line description, and any lab assignments. Session bubbles color-coded by topic cluster: Metrics/Monitoring (teal), Reliability (blue), Economics/Value (gold). The timeline communicates: the Operate arc has its own internal structure — from measurement to operations to economics.

---

## Slide 15 — Key Takeaways + Lab 5 Countdown

**Figure:** *Final takeaways card.* Lab 5 countdown (9 days, amber). "Operate Arc begins Tuesday" announcement in teal. Course arc progress bar: 69% complete (9 of 13 content weeks done). Key message: "You've built it. Now we prove it's worth it."
