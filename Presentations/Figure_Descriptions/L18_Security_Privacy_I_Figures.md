# L18: Security, Privacy & Compliance I — Figures

## Slide 1 — Title

**Figure:** *Global AI regulatory landscape map.* World map with color-coded regions: EU (dark blue, "EU AI Act — in force"), US (medium blue, "State-level patchwork + federal proposals"), China (red, "Generative AI Regulations — in force"), UK (teal, "Pro-innovation, principles-based"), Canada (blue, "AIDA — proposed"). Inset legend: compliance maturity by region. The map communicates: AI regulation is a global, fragmented, and rapidly evolving landscape — not a problem to be outsourced to compliance teams.

---

## Slide 2 — Why AI Compliance Is Different from Software Compliance

**Figure:** *Compliance challenge matrix.* Five rows (the challenges above) × two columns (Traditional software: met/not met, AI system: met/not met). Traditional software: all five "Met" (with caveats). AI system: Explainability (not met by default), Fairness (not met by default), Provenance (partially met), Autonomy oversight (not met by default), Output reproducibility (not met by default). The matrix makes the compliance gap visible and specific.

---

## Slide 3 — The EU AI Act: A Technical Overview

**Figure:** *EU AI Act risk pyramid.* Inverted pyramid (wide at top, narrow at bottom): Minimal Risk (wide, 95% of AI applications), Limited Risk (medium), High Risk (narrow, strict requirements), Unacceptable Risk (bottom, banned). NorthStar systems mapped: Churn → Minimal, Offer Gen → Minimal, Agent → Limited (disclosure required). Arrow showing: if churn score is used in credit decisions → reclassified to High Risk. The pyramid communicates the regulation's risk-based approach.

---

## Slide 4 — Technical Requirements for High-Risk AI

**Figure:** *EU AI Act Article-to-control mapping table.* Six rows (Articles 9, 10, 12, 13, 14, 15). Each row: Article number, requirement summary, NorthStar technical control, AWS service implementing the control. The table makes the abstract regulatory text concrete and actionable. "Already implemented in Labs 1-5" checkmarks on Articles 10, 12, 15.

---

## Slide 5 — GDPR and AI: The Privacy Engineering Challenge

**Figure:** *GDPR Article-to-implementation diagram.* Four GDPR articles as cards, each with: article number, right/requirement, NorthStar implementation, code snippet or architecture reference. Linked to NorthStar architecture components: Right to Erasure → federated deletion workflow diagram. Privacy by Design → ETL PII removal from L05. The diagram shows that GDPR compliance is an architectural decision, not a form to fill out.

---

## Slide 6 — Fairness and Bias in Production AI

**Figure:** *Bias measurement report visualization.* SageMaker Clarify output format: two-panel figure. Left: Pre-training bias metrics (class imbalance by zip income quartile — is one group underrepresented in training data?). Right: Post-training bias metrics (disparate impact — are churn score distributions different across groups?). Ideal: all metrics near 1.0 (no bias). Alert thresholds shown: DI < 0.8 → investigate. The figure shows what bias detection output looks like in practice.

---

## Slide 7 — SHAP Explainability as a Compliance Control

**Figure:** *SHAP waterfall plot for individual customer.* SHAP waterfall plot for Customer C123456: base value (0.35, population average churn rate) → feature contributions (recency_days: +0.21, monetary_30d: +0.15, frequency_30d: -0.18, category_diversity: -0.07, ...) → final prediction (0.73). Red bars: features pushing toward churn. Blue bars: features pushing against churn. The waterfall shows exactly how each feature contributed to this specific prediction — this is what "right to explanation" looks like in technical form.

---

## Slide 8 — Model Cards: The Documentation Compliance Artifact

**Figure:** *Model card document layout.* Multi-section card formatted as a structured document: header (model name, version, date); performance section (AUC gauge chart); segment table; limitations (amber warning boxes); ethical considerations (checklist); contact information. Clean, professional format. The model card communicates: this model is documented, its limitations are known, and there's a human accountable for it.

---

## Slide 9 — Security Monitoring: AWS Security Services for AI

**Figure:** *AWS security service architecture.* NorthStar AI platform at center. Five security service boxes surrounding it: GuardDuty (threat detection, wrapping the account), Config (compliance monitoring, checking resource configs), Security Hub (aggregating all findings), Inspector (scanning containers/code), CloudTrail Lake (audit queries). Arrows: each service feeds findings to Security Hub. Security Hub → SNS → on-call security team. The diagram shows the security monitoring architecture as an interconnected system.

---

## Slide 10 — AI-Specific Security: Prompt Injection Defense

**Figure:** *Defense-in-depth diagram for prompt injection.* User input → Layer 1 (regex pattern detection: BLOCK or PASS) → Layer 2 (Bedrock Guardrails: BLOCK or PASS) → Layer 3 (LLM call in sandbox) → Layer 4 (output filtering: BLOCK or PASS) → User response. Below: audit log capturing every BLOCK event. Attack success requires defeating all four layers. "Defense depth" labeled between each layer.

---

## Slide 11 — Data Minimization and Access Control in Production

**Figure:** *Data minimization table visual.* The table from the content, formatted with traffic-light colors: green rows (data not used, correctly excluded), amber rows (data used but aggregated), red rows (would be red if data were incorrectly used). The "Credit card number — Never" row at the bottom in bright green with "✅ Correctly excluded." The table is a data inventory for compliance review.

---

## Slide 12 — Responsible AI Frameworks: Principles to Controls

**Figure:** *Responsible AI radar chart.* Seven dimensions (one per principle) as a radar/spider chart. NorthStar current state: 5/7 fully covered (green), 1 partially covered (amber: Human oversight), 0 gaps (red). Target state: all seven fully covered. Small gap between current and target in the Human oversight dimension. The radar communicates: NorthStar's responsible AI posture after the lab sequence, and where improvement is needed.

---

## Slide 13 — Lab 6 Preview: Monitoring and Observability

**Figure:** *Lab 6 architecture diagram.* NorthStar AI platform with Lab 6 additions highlighted: Model Monitor (attached to churn endpoint), Unified Dashboard (CloudWatch), Retraining Trigger (Lambda → SageMaker Pipeline), Compliance Report (Lambda → S3 → stakeholder email). Bedrock LLMOps monitoring sidecar. The diagram shows Lab 6 as an operational layer added on top of the Labs 1-5 platform.

---

## Slide 14 — The Build → Operate Transition

**Figure:** *Arc transition visual.* Build arc (9 weeks) on left: technical components stacked (Platform → Data → Models → CI/CD → Deployment). Transition arrow in center (this week: Security + Compliance). Operate arc (4 weeks) on right: business lens over the same stack. Same platform, different questions. Build: "Does it work?" Operate: "Is it worth it?" "Is it still working?" "What's it costing?" "What's it earning?" The visual shows the same system from a different perspective.

---

## Slide 15 — AI Incident Response: When AI Systems Cause Harm

**Figure:** *AI incident response timeline.* Horizontal timeline showing Detect → Assess → Stop → Investigate → Remediate → Document → Prevent. Time estimates for each phase: Detect: < 1 hour (with monitoring); Assess: 1-2 hours; Stop: 15 minutes (automated rollback); Investigate: 4-24 hours; Remediate: days to weeks; Document: 2-4 hours; Prevent: 1-2 weeks. GDPR notification clock: starts at Detect; 72-hour deadline marked.

---

## Slide 16 — Key Takeaways + What's Next

**Figure:** *Five-takeaway summary card.* Responsible AI radar chart thumbnail. Lab 5 countdown (11 days, amber). "Operate Arc begins Week 10" preview banner.
