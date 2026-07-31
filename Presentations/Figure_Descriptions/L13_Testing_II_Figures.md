# L13: Testing & Evaluation II — Figures

## Slide 1 — Title

**Figure:** *Evaluation scorecard visual.* A scorecard card with three sections: Churn Model (AUC: 0.74 ✅ | Calibration: 0.91 ✅ | Segment Coverage: ✅), RAG Offer Generation (Faithfulness: 0.96 ✅ | Relevancy: 0.88 ✅ | Recall@5: 0.83 ✅), Agent (Resolution Rate: 91% ✅ | Escalation: 8.3% ✅ | Cost/session: $0.004 ✅). A "DEPLOY APPROVED" stamp in green. The scorecard communicates: evaluation produces concrete metrics against concrete thresholds, resulting in a clear deployment decision.

---

## Slide 2 — The Evaluation Framework: From Metrics to Decisions

**Figure:** *Threshold derivation diagram.* Two-panel figure. Left: ROC curve for NorthStar churn model at several AUC values (0.65, 0.70, 0.72, 0.75). At each AUC value, recall@0.4-precision is marked. Shows that AUC 0.72 → 78% recall@0.4-precision. Right: Decision tree for gate logic: "AUC ≥ 0.72? AND Recall ≥ 0.75? AND Beats production by ≥ 2%? → DEPLOY. Else → ALERT + retrain."

---

## Slide 3 — Multi-Dimensional Evaluation for AI Systems

**Figure:** *Three evaluation scorecards side by side.* Each scorecard formatted as a card with: system name, metric rows with status indicators (✅/❌/⚠️), and DEPLOY/HOLD/ALERT at the bottom. All three showing "DEPLOY" state in green. Advisory metrics shown in grey (not blocking). The design communicates: evaluation produces a clear, auditable deployment decision.

---

## Slide 4 — Segmented Evaluation: The Missing Practice

**Figure:** *Segment AUC bar chart.* Horizontal bar chart with six customer segments on the y-axis and AUC on the x-axis (0.0 to 1.0). Segments: High-Value (0.81, green), Premium (0.77, green), Medium-Value (0.73, green), Seasonal (0.63, amber/warning), Low-Value-New (0.57, red/fail), Irregular (0.61, amber). Overall AUC marked as a vertical line (0.74). Gate threshold (0.60) marked as a red vertical line. The chart reveals: two segments fail the gate threshold despite an acceptable overall AUC.

---

## Slide 5 — A/B Testing for AI Systems

**Figure:** *A/B test architecture diagram.* Customer request → traffic splitter (customer_id hash mod 5 → 0-3=Model A, 4=Model B) → Model A endpoint or Model B endpoint. Both endpoints → logging → evaluation system. Evaluation system: tracks actual churn outcomes, compares rates after a 4-week window. Statistical significance computed and displayed. Arrow from evaluation to "Promote B to production if significant improvement."

---

## Slide 6 — SageMaker Shadow Mode: Safe Production Evaluation

**Figure:** *Shadow mode architecture diagram.* Request comes in → Production model (v2.3) processes the request → Response is returned to the user. Simultaneously: same request → Shadow model (v3.0) processes request → Response captured to S3 (not returned to user). S3 capture → comparison analysis → CloudWatch metrics showing production vs. shadow prediction distributions. "Zero user exposure" label on the shadow path.

---

## Slide 7 — Human-in-the-Loop Evaluation

**Figure:** *HITL evaluation workflow diagram.* Sample production responses → annotation tool (Label Studio or custom UI) → human reviewer assigns scores on rubric → aggregated scores to CloudWatch → trend dashboard → weekly review meeting → prompt engineering or retraining action if trends decline. The workflow shows: HITL is not ad hoc — it's a systematic operational process with feedback loops.

---

## Slide 8 — Evaluation for RAG: RAGAS Deep Dive

**Figure:** *RAGAS metric visualization.* Three-panel figure. Each panel: bar chart showing score distribution for one metric across 200 sampled responses. Faithfulness: bimodal distribution (most responses near 1.0, a small tail near 0.5). Answer Relevancy: roughly normal, centered at 0.88. Context Recall: uniform-ish, centered at 0.82. Red dotted line showing gate threshold for each metric. The tails represent failure modes worth investigating.

---

## Slide 9 — Calibration: The Forgotten Evaluation Dimension

**Figure:** *Calibration curve diagram.* X-axis: mean predicted probability (0 to 1). Y-axis: fraction of positives (0 to 1). Diagonal line: perfect calibration. NorthStar churn model curve: mostly tracks the diagonal, with slight overconfidence in the 0.7-0.9 range (the curve bends below the diagonal). Shaded region: ECE = 0.034, shown graphically as the area between the curve and the diagonal. "Acceptable calibration" label.

---

## Slide 10 — Evaluation Report: The AISDLC Stage 6 Artifact

**Figure:** *Evaluation report cover page mockup.* Document cover page: NorthStar logo, "Churn Model v3.0 Evaluation Report," date, model ID, "DEPLOYMENT APPROVED — Gate Passed: 4/4 criteria" in green at the bottom. Professional, clean design communicating this is a formal artifact, not an ad hoc analysis.

---

## Slide 11 — Online Evaluation vs. Offline Evaluation

**Figure:** *Evaluation sequence timeline.* Horizontal timeline with four phases (Offline, Shadow, A/B, Full). Each phase: duration, what's measured, who can stop it, and what "success" looks like. Phases connected by gates: "Offline gate passed → enter Shadow," "Shadow comparison passed → enter A/B," "A/B results significant → Full rollout." The sequence shows: deployment is a process, not an event.

---

## Slide 12 — Lab 4 Walkthrough: Building the Evaluation Gate

**Figure:** *Lab 4 evaluation gate flowchart.* Three boxes: TrainingStep → EvaluateModel (your evaluate.py script) → ConditionStep (AUC ≥ 0.72?). Two branches: YES → RegisterModel (green box). NO → FailPipeline + CloudWatch Alert (red box). The code on this slide is what creates the flowchart.

---

## Slide 13 — Common Evaluation Mistakes

**Figure:** *Five-mistake checklist.* Same checklist format. Mistake 5 (no baseline) shows a mini comparison: NorthStar rule-based baseline AUC = 0.69; XGBoost v3.0 AUC = 0.74. "+5% over baseline" shown — this is the meaningful comparison. Without it, 0.74 AUC sounds good, but the context is missing.

---

## Slide 14 — Lab 4 Spec Review: What's Expected

**Figure:** *Lab 4 component dependency diagram.* Five components arranged in a flow. Each component: name, weight %, and 1-sentence description. Arrows showing dependencies: "Pipeline must work before CodePipeline can trigger it"; "Test suite must pass before pipeline runs"; "Evaluation report documents the gate result." Common failure modes highlighted in amber boxes next to the relevant component.

---

## Slide 15 — Evaluation in the AISDLC: Where It Fits

**Figure:** *AISDLC evaluation touchpoints diagram.* 8-stage AISDLC pipeline with evaluation icons overlaid on Stages 1, 2, 5, 6, 7, 8. Stage 6 highlighted as "primary evaluation gate." Stages 7 and 8 connected with a circular arrow showing "continuous evaluation loop." The visual communicates: evaluation is woven throughout the full lifecycle.

---

## Slide 16 — Key Takeaways + Lab 4 Launch

**Figure:** *Lab 4 launch card.* Bright teal box: "Lab 4: CI/CD Pipeline" with due date, spec location, and three starter steps: 1) Read the spec tonight, 2) Get the SageMaker Pipeline running first, 3) Attend office hours if blocked. Key takeaways numbered list alongside. Professional, clear, actionable.
