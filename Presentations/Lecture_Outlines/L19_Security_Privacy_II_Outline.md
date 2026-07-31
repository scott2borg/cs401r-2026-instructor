---
lecture: L19
title: Security, Privacy & Compliance II — Bridge Build→Operate
date: Thursday, November 5, 2026
week: 10
arc: Bridge (Build → Operate)
reading_due: "AI Governance — Responsible AI Frameworks through Key Takeaways"
lab_due: "Lab 5 due Sat Nov 14 (9 days)"
slides_target: 15
---

# L19: Security, Privacy & Compliance II — The Build→Operate Bridge
**Thursday, November 5, 2026 | CS 401R: Engineering Production AI Systems | Fall 2026**

> You've built a production AI platform. Now you need to prove it's trustworthy — to your users, your regulators, your executive team, and to yourself. Responsible AI in practice is not a checkbox. It's an ongoing operational discipline.

**Reading Due:** *AI Governance* — "Responsible AI Frameworks" through "Key Takeaways"
**Lab 5 Due:** Sat Nov 14 (9 days)

---

## Slide 1 — Title
**Layout:** Left dark panel + right "Build complete → Operate begins" arc visual

**Content:**
- Security, Privacy & Compliance II: Responsible AI in Practice
- CS 401R · Lecture 19 · Thursday, November 5, 2026
- The Build→Operate Bridge: You've Built It. Now Prove It's Trustworthy.

**Figure:** *Build→Operate arc bridge visual.* Left side: the NorthStar platform architecture (compressed) labeled "Built." Right side: four Operate arc questions floating above the platform: "Is it still working?" "Is it fair?" "Is it worth it?" "Who's accountable?" A bridge spanning the two sides, with this lecture labeled on the bridge. The visual communicates: the platform exists; now comes the harder question of whether it deserves to run.

**Notes:** "Today is the inflection point of the course. For nine weeks, the question was: can we build this? The answer — after Labs 1-5 — is yes. Starting next week, the question becomes: should this keep running, and at what cost, and how do we know it's still doing what we built it to do? That's a harder question, and it's the question that separates production engineers from notebook data scientists."

---

## Slide 2 — What "Trustworthy AI" Means in Practice
**Layout:** Trustworthy AI framework with NorthStar status

**Content:**
**The EU's Definition of Trustworthy AI (HLEG):**
The European Commission's High-Level Expert Group on AI identified seven requirements for Trustworthy AI:

1. **Human agency and oversight** — AI supports human decision-making; humans can override
2. **Technical robustness and safety** — AI is resilient to errors, attacks, and failures
3. **Privacy and data governance** — AI respects privacy; data is governed appropriately
4. **Transparency** — AI decisions can be understood and traced
5. **Diversity, non-discrimination and fairness** — AI treats people equitably
6. **Societal and environmental wellbeing** — AI's broader impacts are considered
7. **Accountability** — AI decisions can be audited; responsibility is assignable

**NorthStar status after Build arc:**

| Requirement | Status | Key Control |
|------------|--------|-------------|
| Human oversight | ⚠️ Partial | Escalation path; override not fully implemented |
| Technical robustness | ✅ | Evaluation gates; canary; auto-scaling |
| Privacy/data governance | ✅ | PII removal; encryption; Feature Store |
| Transparency | ✅ | CloudTrail; Model Registry; SHAP; model card |
| Fairness | ✅ | Clarify bias audit; segment evaluation |
| Societal wellbeing | ⚠️ | Not formally assessed |
| Accountability | ✅ | Governance approval workflow; audit trail |

**Figure:** *HLEG trustworthy AI checklist visual.* Seven requirement cards arranged in a grid. Each card: requirement name, NorthStar status (✅/⚠️), and key control. Two amber cards (Human oversight, Societal wellbeing) stand out from the five green cards. The visual communicates: NorthStar after Labs 1-5 is substantially trustworthy, with two areas for improvement.

**Notes:** "The 'Societal wellbeing' requirement is the one that's hardest to make concrete. For NorthStar: does the churn prediction system benefit society? It helps NorthStar retain customers and drive revenue. But does it systematically advantage certain customer populations over others? Does it drive consumption behavior in ways that harm customers? These are not hypothetical questions — they're the questions that AI ethics boards and regulators will ask. Have an answer."

---

## Slide 3 — Case Study: When AI Goes Wrong at Enterprise Scale
**Layout:** Real-world AI failure case study with lessons

**Content:**
**Case Study: Amazon's Recruiting AI (2018) — What Went Wrong**

Amazon built an ML model to screen job candidates. The model was trained on historical hiring decisions (predominantly male hires in technical roles). The model learned to penalize resumes that included the word "women's" (e.g., "Women's Chess Club"), and systematically downgraded graduates of all-women's colleges.

**Why it failed the trustworthiness requirements:**
- **Fairness:** Model encoded historical gender bias from training data
- **Transparency:** Failure was not detected for years because the model's behavior wasn't explainable
- **Human oversight:** Automated screening reduced human judgment; bias passed undetected
- **Data governance:** Training data audit would have detected gender imbalance and its implications

**What the control should have been:**
1. Training data audit (Clarify pre-training bias) → detected before training completed
2. Fairness evaluation at Stage 6 (segment performance by gender) → caught before deployment
3. SHAP analysis → revealed "women's" as a feature driver → flagged for review

**The lesson for NorthStar:**
- Churn model trained on historical customer data → what historical biases are in that data?
- If NorthStar historically offered lower-quality service to certain demographics → the model may perpetuate that underservice by predicting higher churn for those customers → business responds by investing less in their retention → the bias reinforces itself

**Figure:** *Bias feedback loop diagram.* Circular flow: Historical underservice of Group A → Group A has higher historical churn rate → Churn model predicts high churn for Group A → Business invests less in retaining Group A → Group A churns more → More historical data showing Group A churns → Model continues to predict high churn. The self-reinforcing loop communicates: without active fairness intervention, historical bias perpetuates into the future.

**Notes:** "The Amazon case is not an outlier. It's a canonical example of a pattern that repeats across AI systems in hiring, lending, criminal justice, and retail. The pattern is always the same: historical data reflects past human decisions, which reflect past human biases; the model learns from historical data; the model perpetuates the bias with the veneer of objectivity. Breaking the cycle requires active fairness intervention at training time and monitoring at inference time."

---

## Slide 4 — Responsible AI Governance: Organizational Structure
**Layout:** AI governance organizational design

**Content:**
**How Enterprise AI Governance Is Structured:**

At mature AI organizations, governance is not a single team — it's a distributed responsibility model:

**Individual Level (every AI practitioner):**
- Responsible for: following the ML engineering standards; completing required documentation (model card, evaluation report, ADR)
- Accountable for: knowing the intended use and limitations of systems they build
- Training required: responsible AI principles; data privacy requirements

**Team Level (ML team lead / platform team):**
- Responsible for: reviewing models before Model Registry submission; peer review of evaluation reports; enforcing technical standards
- Accountable for: team compliance with ML engineering standards; escalation to governance when edge cases arise

**Governance Function (ML governance officer / AI review board):**
- Responsible for: approving models for production; reviewing fairness reports; maintaining the AI system inventory
- Accountable for: organizational AI risk posture; regulatory compliance
- Composition: ML lead, Legal/compliance, Ethics officer, Business owner

**Executive Level (CAIO / CTO / Risk Committee):**
- Responsible for: setting AI strategy and risk tolerance; approving high-risk AI deployments
- Accountable for: organization's AI governance to board/regulators

**NorthStar governance structure:**
- Individual: each ML engineer owns the model card and ADR
- Team: ML lead reviews evaluation reports; enforces standards
- Governance: governance officer role (already in IAM) approves all production deployments
- Executive: CTO or VP Engineering approves any high-risk AI reclassification

**Figure:** *AI governance organizational chart.* Four-level pyramid: Individual (wide, bottom), Team (middle), Governance Function (narrow), Executive (top). Each level: role, responsibilities, escalation path. Arrows show: unresolved issues escalate from Individual → Team → Governance → Executive. The pyramid communicates: governance is not a tax on ML teams — it's a distributed accountability system.

**Notes:** "The most common governance failure mode is treating governance as a bottleneck: 'We built the model; now we have to send it to the compliance team and wait two weeks.' Governance works when it's embedded in the development process — model cards written during development, not after; evaluation reports completed during Stage 6, not at deployment time. The governance function reviews, doesn't create. That requires ML engineers to produce complete governance artifacts as part of their standard workflow."

---

## Slide 5 — AI System Inventory: Managing What You've Built
**Layout:** AI system inventory structure and NorthStar example

**Content:**
**The AI System Inventory: Knowing What You're Running**

An AI system inventory is a catalog of all AI systems in production. Required for:
- Regulatory compliance (EU AI Act requires registration of high-risk systems)
- Risk management (you can't manage risk from systems you don't know exist)
- Security (shadow AI — unauthorized AI systems built outside governance — is a real risk)
- Business continuity (which systems are critical path? What happens if they fail?)

**NorthStar AI System Inventory (after Labs 1-5):**

| System | Purpose | Risk Class | Status | Owner | Last Review |
|--------|---------|-----------|--------|-------|------------|
| Churn Prediction | Customer retention | Minimal | Production | ML Team | Oct 2026 |
| Offer Generation | Marketing personalization | Minimal | Production | ML Team | Oct 2026 |
| Customer Service Agent | Customer support | Limited (disclosure reqd) | Production | ML Team | Oct 2026 |
| NorthStar Hiring Screener | (Hypothetical, rejected) | High → Not built | Rejected | — | — |

**Shadow AI (the governance risk):**
At many enterprises, individual business teams build their own AI tools (ChatGPT for customer emails, Copilot for data analysis) without governance oversight. This creates:
- Unknown PII processing
- Unknown bias risks
- No audit trail
- Unknown regulatory exposure

**Shadow AI detection:** Regular audits of cost reports (Bedrock/OpenAI API spend by team); self-reporting programs with amnesty for existing tools that get properly reviewed.

**Figure:** *AI system inventory table.* The table above, formatted as a professional registry card. "Status" column uses traffic-light colors: Production (green), Development (amber), Rejected (red). "Risk Class" column uses the EU AI Act color scheme. Last-reviewed date with "Overdue" flag if >6 months. The inventory communicates: AI governance requires knowing what's running, not just governing what you're building today.

**Notes:** "Shadow AI is the governance challenge that keeps CISOs and CAIOs up at night. At enterprises I've worked with, AI system inventories routinely reveal AI deployments that the central governance function had no knowledge of. An individual salesperson building a GPT-4 tool that emails customers using the company's name is a GDPR liability, a reputation risk, and a security risk — none of which were reviewed. The shadow AI problem is real and growing."

---

## Slide 6 — Practical Responsible AI: What You Actually Do
**Layout:** Actionable responsible AI checklist for ML practitioners

**Content:**
**Responsible AI as Engineering Practice (Not Just Policy)**

What responsible AI looks like in your daily workflow:

**At problem definition (AISDLC Stage 1):**
- [ ] Define intended use explicitly (who benefits, how, from what decisions)
- [ ] Define NOT intended use explicitly (what decisions this system should NOT make)
- [ ] Identify affected populations and potential harms
- [ ] Define fairness criteria and metrics before training

**At data preparation (AISDLC Stages 2-3):**
- [ ] Audit training data for demographic representation (Clarify pre-training bias)
- [ ] Remove PII or replace with synthetic keys before training
- [ ] Document data provenance: source, collection date, known limitations

**At model development (AISDLC Stages 4-5):**
- [ ] Evaluate segment performance (not just overall accuracy)
- [ ] Run SHAP analysis: are the drivers of predictions reasonable?
- [ ] Test for proxy variables (features that encode protected attributes indirectly)

**At evaluation (AISDLC Stage 6):**
- [ ] Fairness report: Clarify bias metrics
- [ ] Model card: complete and accurate
- [ ] Human review: have a non-ML stakeholder read the model card and flag concerns

**At deployment and operation (Stages 7-8):**
- [ ] Model registered in AI system inventory with risk classification
- [ ] Ongoing bias monitoring (Clarify scheduled runs)
- [ ] Incident response plan documents responsible AI failures specifically

**Figure:** *Responsible AI checklist across AISDLC stages.* AISDLC pipeline (8 stages) at top. Below each stage: 2-3 responsible AI checklist items. Checkmarks and status indicators. The visual shows: responsible AI is woven through the full AISDLC, not added at the end. It's a thread through the lifecycle, not a stage.

**Notes:** "The 'proxy variable' check at model development is the one teams skip most often. A proxy variable is a feature that correlates with a protected attribute (race, gender, income) and can cause discrimination even when the protected attribute is not in the training data. For NorthStar: zip code correlates with income and race. If zip code is a strong predictor of churn, the model may discriminate by income/race without using income or race directly. The check: look at SHAP values for zip code features and interpret in context."

---

## Slide 7 — AI Ethics in Context: Christian Values and Enterprise AI
**Layout:** Values-based AI decision making

**Content:**
**Why Values Matter in AI Engineering**

Technical excellence is necessary but not sufficient for responsible AI. The systems you build reflect the values of the people and organizations that build them.

**The question engineers must ask:** Not just "does this work?" but "should this work?"

**Enterprise AI through a values lens:**

**Dignity:** Every AI prediction affects a person. That person has inherent worth. A churn prediction that determines whether a customer receives premium service treats that customer differently. Does our AI enhance or diminish human dignity?

**Honesty:** AI transparency requirements (model cards, explainability, disclosure of AI use) are technical implementations of an honesty value. Building an AI system that conceals its nature, limitations, or errors is a form of deception — even if it's legal.

**Service:** The most valuable AI systems are ones that genuinely serve the people they affect. NorthStar's Offer Generation system — if done well — helps customers find products they genuinely want at prices they value. Done poorly, it manipulates customers into purchases they'll regret. The difference is in how it's designed.

**Justice:** Fairness in AI is a technical implementation of justice. When an algorithm disadvantages people who are already disadvantaged by historical circumstances, it compounds injustice. Responsible AI engineers actively work against this.

**The ethical test for an AI decision:** If you fully disclosed to the affected person exactly how this AI system works, what data it uses, and what decision it's driving — would you be comfortable? If not, reconsider the system.

**Figure:** *Values-to-controls diagram.* Four values (Dignity, Honesty, Service, Justice) as circular nodes. From each node: arrows pointing to specific technical controls: Dignity → SHAP explainability; right to appeal. Honesty → Model card; disclosure in UI. Service → HITL review; customer feedback loop. Justice → Fairness audit; Clarify bias detection. The diagram shows that values translate into engineering decisions.

**Notes:** "This slide is the one that puts the whole course in context. Every technical decision we've covered — evaluation gates, fairness audits, model cards, guardrails, explainability — is an engineering implementation of a value. When you make a technical decision in your career, you're making an ethical decision. The question 'should we build this?' is always upstream of 'how do we build this?' Don't let technical expertise make you forget the first question."

---

## Slide 8 — The AISDLC Complete: Stage Gates and Return Loops
**Layout:** Full AISDLC review with all gates and return loops completed

**Content:**
**The Complete AISDLC: Everything We've Built**

Revisiting the AISDLC from Week 1 with everything the course has built:

**Stage 1 — Define Problem:** Success criteria defined; intended use documented; fairness criteria set; stakeholder alignment. *What NorthStar built:* Lab 1 ADR; model card Intended Use section; AUC ≥ 0.72 gate criteria from business requirement analysis.

**Stage 2 — Discover Data:** Data sources identified; quality assessed; ethical review. *What NorthStar built:* Lab 2 data quality gates; Clarify pre-training bias audit; training data lineage in Glue Data Catalog.

**Stage 3 — Prepare Data:** ETL pipelines; Feature Store; data contracts; PII removal. *What NorthStar built:* Lab 2 Glue ETL; SageMaker Feature Store with RFM features; PII removal at ETL boundary.

**Stage 4 — Design Solution:** Architecture decisions; build vs. buy; spectrum choice. *What NorthStar built:* Lab 3 model selection (XGBoost for churn; Bedrock for offers/agent); ADRs for each decision.

**Stage 5 — Develop:** Training; experiment tracking; hyperparameter tuning. *What NorthStar built:* Lab 3 SageMaker training, MLflow, and SHAP analysis.

**Stage 6 — Evaluate:** Gate criteria, evaluation report, model card, fairness report. *What NorthStar built:* Lab 4 evaluation gate; evaluation report; model card; Clarify bias report.

**Stage 7 — Deploy:** CI/CD, canary, rollback, governance approval. *What NorthStar built:* Lab 4 CodePipeline; Lab 5 canary; governance approval workflow.

**Stage 8 — Monitor:** Model Monitor; LLMOps dashboard; retraining triggers; compliance reports. *What Lab 6 will build.*

**Figure:** *Full AISDLC with lab artifacts.* 8-stage pipeline with artifact cards under each stage showing what the labs produced at that stage. Stage gates shown between stages. Return loops: Stage 6 failure → back to Stage 5 (retrain). Stage 2 quality gate failure → back to Stage 1 (re-scoping). Stage 8 drift detected → back to Stage 3 (new features) or Stage 5 (retrain). The diagram is the complete picture of what the course has built.

**Notes:** "From here, the course shifts from building the AISDLC pipeline to operating it. The platform you've built runs through this AISDLC for every model update, every prompt change, every new system. The pipeline doesn't stop when the platform launches — it cycles continuously. Stage 8 connects back to Stage 1: monitoring reveals new problems, which define new project requirements, which start the cycle again."

---

## Slide 9 — Threat Modeling Workshop: NorthStar Attack Surface
**Layout:** Interactive threat modeling exercise for NorthStar

**Content:**
**Exercise: NorthStar Threat Model (15 minutes in pairs)**

Using the STRIDE framework, identify threats to the NorthStar AI platform:

**The system to model:**
- Customer Service Agent (Bedrock) receives customer input via web chat
- Agent calls 4 tools: `get_order_status`, `get_product_info`, `process_return`, `escalate_to_human`
- Agent accesses customer history via RAG Knowledge Base
- Session logged to CloudWatch; tool calls logged to DynamoDB audit log

**STRIDE exercise:**

| STRIDE Category | Question | NorthStar Threat Example |
|----------------|---------|------------------------|
| **S**poofing | Can an attacker impersonate a legitimate user or system component? | Attacker spoofs customer ID to get another customer's order history |
| **T**ampering | Can an attacker modify data in transit or at rest? | Attacker modifies agent tool response in transit to return false order status |
| **R**epudiation | Can an actor deny having performed an action? | Agent denies having issued a refund; no audit trail of tool call |
| **I**nformation Disclosure | Can sensitive data be exposed to unauthorized parties? | Prompt injection causes agent to reveal another customer's PII |
| **D**enial of Service | Can the system be made unavailable? | Flooding agent with long sessions to exhaust token budget |
| **E**levation of Privilege | Can an attacker gain unauthorized permissions? | Prompt injection to invoke `process_return` without customer authorization |

**Pair exercise:** For each threat, identify the existing NorthStar control and rate its effectiveness (1-5).

**Figure:** *STRIDE matrix for NorthStar Agent.* 6-row table (one per STRIDE category). Columns: Threat, Existing Control, Control Effectiveness (1-5), Gap. Students fill in the last two columns during the exercise. "Spoofing" row pre-filled as example: Existing Control = "IAM authentication on API Gateway," Effectiveness = 4, Gap = "Session fixation attacks not addressed." The pre-filled row models the expected response quality.

**Notes:** "Pair exercise — take 10 minutes, complete the matrix for the six STRIDE categories. Then we'll discuss as a class. The goal is not to have the perfect answer — it's to practice thinking adversarially about your own system. The engineers who find the vulnerabilities in their own systems before attackers do are the ones whose systems survive. Engineers who only think about features and performance leave the security thinking to the attacker."

---

## Slide 10 — Debrief: NorthStar Threat Model
**Layout:** Completed threat model debrief with key findings

**Content:**
**Threat Model Debrief: Key Findings**

**Highest severity threats:**

1. **Information Disclosure via prompt injection (severity: HIGH)**
   - Attack: crafted customer message causes agent to output another customer's PII
   - Gap: Guardrails may not catch all PII disclosure scenarios
   - Mitigation: Add PII output detection to output filter; rate-limit information requests per session

2. **Elevation of Privilege via authority boundary bypass (severity: HIGH)**
   - Attack: prompt injection convinces agent that `process_return` has been authorized for a different customer's item
   - Gap: agent does not verify that the customer_id in the tool call matches the authenticated session customer_id
   - Mitigation: Tool function validates: `assert tool_input['customer_id'] == session['authenticated_customer_id']`

3. **Denial of Service via session length manipulation (severity: MEDIUM)**
   - Attack: attacker designs prompts that force agent into multi-turn loops
   - Gap: session token limit (5,000 tokens) limits this, but loop detection threshold of 15 tool calls may not fire fast enough
   - Mitigation: Lower loop detection threshold to 8 tool calls; add per-session-per-IP rate limiting

**The most important finding:** The `process_return` authority bypass is exploitable without prompt injection—simply by crafting a valid-looking request for a different customer's item. This is a business logic vulnerability, not an AI-specific attack.

**Figure:** *Threat matrix with severity heat map.* STRIDE category × Severity matrix. High-severity cells in red (Information Disclosure, Elevation of Privilege). Medium-severity cells in amber (DoS). Low-severity cells in green (Spoofing, Tampering, Repudiation — controls in place). The heat map communicates: focus remediation on the red cells.

**Notes:** "The business logic vulnerability in `process_return` is more dangerous than prompt injection because it doesn't require AI trickery. A sophisticated human attacker can exploit it with a carefully crafted API call. This is a reminder: AI security includes traditional software security. Don't let the novelty of AI security concerns distract from the fundamentals — authentication, authorization, and input validation."

---

## Slide 11 — Responsible AI Communication: Talking to Executives
**Layout:** How to communicate AI risks to non-technical stakeholders

**Content:**
**The Communication Challenge:**

You understand: AUC, SHAP, PSI, prompt injection, EU AI Act risk categories.
Your CEO understands: revenue, risk, customers, reputation.
Your compliance team understands: regulations, controls, audit trails, liability.
Your customers understand: fairness, privacy, whether the AI is working for them.

**Translating technical risk for each audience:**

**For executives:** Frame risk as business risk.
- "Our churn model has a gap in performance for new customers (< 90 days). This means we're likely misidentifying new customer churn risk, which could cost us $X in misdirected retention budget per year."

**For compliance teams:** Frame risk as regulatory exposure.
- "Without SHAP explainability, if a customer challenges a churn-driven marketing decision under GDPR Article 22, we cannot provide the required explanation within 30 days. Penalty exposure: up to 2% of global revenue."

**For customers:** Frame risk as benefit.
- "We use AI to personalize your offers. Our AI is trained only on your purchase history, never on your personal information such as your name or address. You can request an explanation of any offer you receive."

**For engineers:** Frame risk in terms of technical failure modes.
- "The Gini coefficient for the churn model drops from 0.54 to 0.41 for customers with tenure < 90 days. This is below our defined segment threshold. We need either additional features for new customers or a separate model for early-tenure customers."

**Figure:** *Stakeholder communication matrix.* Four-quadrant diagram: x-axis: Technical Detail (low to high); y-axis: Business Impact (low to high). Four audience labels placed in quadrants: Executives (high business, low technical), Compliance (medium both), Customers (low technical, medium business), Engineers (high both). Four speech bubbles showing the same risk framed for each audience. The matrix shows the same risk across four different framings, each appropriate to the audience.

**Notes:** "The ability to translate technical risk into business language is the skill that separates engineers who get promoted from engineers who stay technical individual contributors for their entire career. When you brief an executive on AI risk, you have 3-5 minutes. Those minutes must be spent entirely on business implications — not on PSI scores and model architecture. Practice this translation; it's a learnable skill."

---

## Slide 12 — Lab 5 Final Guidance: Common Issues and Solutions
**Layout:** Lab 5 support for final 9 days

**Content:**
**Lab 5 Status and Common Issues (9 days remaining):**

**Part 1 (Canary Deployment) — most common issue:**
Lambda can't update endpoint weights: check `sagemaker:UpdateEndpointWeightsAndCapacities` in Lambda execution role. This permission is different from `sagemaker:UpdateEndpoint` (which updates the endpoint configuration) — students frequently confuse these.

**Part 2 (Auto-Scaling) — most common issue:**
Scale-out not triggering during load test: check that auto-scaling is registered on the **variant**, not the endpoint. The resource ID must be: `endpoint/{endpoint-name}/variant/{variant-name}`. If you registered on the endpoint (wrong: `endpoint/{endpoint-name}`), auto-scaling silently does nothing.

**Part 3 (Batch Transform) — most common issue:**
Job output format incorrect: the Batch Transform job writes one prediction per line (with the input record). If your model returns JSON, the output will be one JSON object per line. Verify the output format matches what your reporting script expects before submitting.

**Part 4/5 (RAG/Agent deployment) — most common issue:**
Bedrock KB sync takes longer than expected: the Bedrock Knowledge Base sync job can take 30-90 minutes for large indexes. Don't start this 1 hour before the deadline. Start the sync job early; verify it completed successfully (check Bedrock console for sync status).

**Lab 5 submission checklist:**
- [ ] Canary endpoint active (two variants: Production + Canary)
- [ ] Lambda health gate deployed and scheduled (EventBridge every 15 min)
- [ ] Auto-scaling policy attached (verify in SageMaker console)
- [ ] Batch Transform job completed successfully (at least one successful run)
- [ ] Deployment runbook written (what to do for canary deploy, rollback)
- [ ] CloudWatch screenshot of scale-out event (load test evidence)

**Figure:** *Lab 5 checklist card.* Six-item checklist with common issue callouts next to the two most problematic items (canary weight vs. endpoint update; auto-scaling variant vs. endpoint). Time estimate: "With working Lab 4: 15-20 hours for Lab 5. Start today."

**Notes:** "The most important thing you can do today for Lab 5: verify that your Lab 4 SageMaker Pipeline is working (after any Lab 4 grade feedback you received). Lab 5 is built on Lab 4. If Lab 4 has issues that weren't caught, resolve them first. Lab 5 with a broken Lab 4 foundation is exponentially harder."

---

## Slide 13 — The AI Governance Maturity Model
**Layout:** AI governance maturity progression for organizations

**Content:**
**AI Governance Maturity: Where Organizations Are and Where They're Going**

**Level 0 — Reactive (most companies in 2022-2023):**
- No formal AI inventory
- AI deployed without systematic governance review
- Incident response is ad hoc
- Compliance discovered post-deployment

**Level 1 — Defined (emerging standard 2024-2025):**
- AI inventory exists; high-risk systems identified
- Governance review required before production deployment
- Model cards and evaluation reports as standard artifacts
- Basic monitoring in place

**Level 2 — Managed (leading organizations 2025-2026):**
- Governance integrated into SDLC/AISDLC; not a separate process
- Automated compliance checks in CI/CD pipeline
- Fairness monitoring continuous (not just at deployment)
- AI incident response process defined and practiced

**Level 3 — Optimized (frontier 2026+):**
- AI governance drives AI strategy (not just compliance)
- Governance tooling integrated at IDE level (engineers get real-time feedback)
- External audits and certifications
- Governance function contributes to competitive advantage (trust as a differentiator)

**NorthStar course target:** Level 1-2. By Lab 7, the platform has governance review workflows, automated compliance in CI/CD, model cards, and monitoring. Not Level 3 — that's years of institutional development.

**Your career:** The ML engineers who can build Level 2-3 AI governance infrastructure are rare and in high demand. This is a skill set, not just a compliance checkbox.

**Figure:** *AI governance maturity staircase.* Four steps (Level 0-3). Each step: maturity level name, organizational characteristics, example capabilities. NorthStar "course target" bracket spanning Level 1-2. "Industry average" marker at Level 0-1. "Leading enterprises" marker at Level 2. The staircase communicates: governance maturity is a journey; the course takes you materially up the staircase.

**Notes:** "The organizations that are investing in Level 2-3 AI governance right now are doing so because they see it as a competitive advantage, not just a compliance requirement. Enterprise customers increasingly ask AI vendors for evidence of governance maturity before signing large contracts. 'We have a model card, a bias audit, and a governance approval workflow' is a sales differentiator in B2B AI in 2026."

---

## Slide 14 — What's Coming: The Operate Arc
**Layout:** Operate arc preview

**Content:**
**The Operate Arc: Weeks 11-13**

You've built the platform. Now we measure whether it's earning its keep.

**L20 (Tue Nov 10): Metrics, Benchmarks & Guardrails**
- How do you define "good" for an AI system in production?
- Building the measurement framework: leading indicators vs. lagging indicators
- Guardrails as operational controls (not just security)
- **Lab 6 assigned**

**L21 (Thu Nov 12): Monitoring, Observability & Model Lifecycle**
- SageMaker Model Monitor deep dive
- LLMOps observability: what to watch for RAG and agent systems
- The model lifecycle: when to retrain vs. retire vs. redesign

**L22 (Tue Nov 17): Reliability Engineering**
- SLA design; error budgets; chaos engineering for AI
- The reliability difference between "99%" and "99.9%."
- Designing AI systems that degrade gracefully

**L23 (Thu Nov 19): AI Economics**
- The cost model for enterprise AI: training, inference, operations
- ROI framework: cost/prediction → cost/value created
- **Lab 7 assigned**

**L24 (Tue Nov 24): Measuring Business Value**
- Connecting AUC to churn reduction to revenue retained
- The business case for AI: how to build it, how to defend it

**Figure:** *Operate arc timeline.* Five sessions (L20-L24) on a horizontal timeline. Each session: topic, one-line description, and any lab assignments. Session bubbles color-coded by topic cluster: Metrics/Monitoring (teal), Reliability (blue), Economics/Value (gold). The timeline communicates: the Operate arc has its own internal structure — from measurement to operations to economics.

**Notes:** "The Economics session (L23) and Business Value session (L24) are the ones that will be most directly useful in your first job. The ability to build a business case for AI investment — and to defend it with concrete numbers — is what gets AI projects funded and continued. 'Our model has 0.74 AUC' means nothing to a CFO. 'Our churn model enabled $2.3M in retained revenue at a cost of $6,000/month' is a business case."

---

## Slide 15 — Key Takeaways + Lab 5 Countdown
**Layout:** Takeaways + lab count and motivation

**Content:**
**Key Takeaways:**
1. Trustworthy AI requires seven properties (HLEG framework): oversight, robustness, privacy, transparency, fairness, wellbeing, accountability — each translates to specific engineering controls
2. Responsible AI is a lifecycle discipline, not a deployment checklist — fairness, explainability, and governance controls must be woven through Stages 1-8 of the AISDLC
3. AI governance maturity is a business capability — Level 2-3 governance (automated compliance in CI/CD, continuous fairness monitoring) is becoming a competitive differentiator, not just compliance overhead
4. Threat modeling (STRIDE) applied to AI systems surfaces security vulnerabilities that AI-specific security thinking alone would miss — traditional software security (auth, authz, input validation) remains essential
5. Technical communication is a professional skill: the ability to translate AUC, drift, and prompt injection into executive risk, compliance liability, and customer value is what makes you effective at enterprise scale

**Lab 5 — 9 Days:**
- Due: Saturday, November 14
- Key milestone: get Part 1 (canary) working by Tuesday
- Office hours: Mon-Wed; extended Thursday
- Last-day submissions historically have infrastructure issues — don't wait

**Figure:** *Final takeaways card.* Lab 5 countdown (9 days, amber). "Operate Arc begins Tuesday" announcement in teal. Course arc progress bar: 69% complete (9 of 13 content weeks done). Key message: "You've built it. Now we prove it's worth it."

**Notes:** "Nine days to Lab 5. This is the last complex lab before the final project. After Lab 5, you have two shorter labs (6 and 7) and two project workshops. The hardest lab sequence (Labs 4 and 5) is almost over. For the Operate arc, shift your mental model: stop thinking like a builder and start thinking like an operator. The system exists; your job is to keep it running, prove it's working, and make the case that it's worth the investment."
