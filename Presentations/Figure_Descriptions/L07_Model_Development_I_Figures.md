# L07: Model Development I — Figures

## Slide 1 — Title

**Figure:** *AI development spectrum.* A horizontal spectrum from left (Simple, Fast, Cheap) to right (Complex, Slow, Expensive). Five labeled positions along the spectrum: "Prompt Engineering," "RAG," "Fine-Tuning," "Custom Training," "Full Architecture Design." Each position shows a complexity icon, a time-to-first-result estimate (hours, days, weeks, months), and a cost indicator ($). Color gradient from green (left) to red (right). A vertical arrow labeled "Start here" points to "Prompt Engineering" with caption: "Move right only when you can justify it."

---

## Slide 2 — The Development Spectrum: Five Approaches

**Figure:** *Development spectrum visual as a horizontal stacked bar.* Each approach is a colored segment. Width suggests approximate "coverage" in enterprise AI (RAG and Custom Training are widest; Full Architecture is very narrow). Below each segment: 2-3 word use case label. The bar makes it clear that most enterprise AI lives in the RAG + Custom Training segments.

---

## Slide 3 — Why NorthStar Uses XGBoost for Churn Prediction

**Figure:** *Decision tree flowchart for model selection.* Starting from "What type of data?" → branches: Tabular (→ Classical ML / XGBoost / LightGBM), Text/Documents (→ Foundation Model / RAG / Fine-Tuning), Images (→ CNN / Vision Foundation Model). Churn prediction follows the Tabular branch. At each decision node, the reasoning is shown. The "NorthStar Churn" path is highlighted in gold throughout the flowchart.

---

## Slide 4 — XGBoost Training on SageMaker: The Architecture

**Figure:** *SageMaker Training Job diagram.* Three-column layout: Inputs (S3 parquet files, hyperparameters config) → Training Container (XGBoost container on ml.m5.xlarge, training loop, metric logging) → Outputs (model artifact in S3, CloudWatch metrics, MLflow experiment log). A side channel shows: "MLflow Auto-Logging" capturing all parameters and metrics. The NorthStar-specific values are filled in (45-minute runtime, ml.m5.xlarge cost: $0.30, feature importance SHAP output).

---

## Slide 5 — Training the Churn Model: Key Engineering Decisions

**Figure:** *Engineering decision summary table.* Four rows (one per decision), three columns: Decision, Wrong Approach (red background), Correct Approach (green background). Compact, high-contrast. Caption: "Each of these decisions affects production model quality. The 'wrong approach' is what most teams default to without thinking."

---

## Slide 6 — Evaluating the Churn Model: The Lab 3 Gate

**Figure:** *ROC Curve with calibration plot.* Left: ROC curve (AUC = 0.76 for a good run), with the chosen operating point (threshold = 0.4) marked with a gold dot. Shaded region above the diagonal. AUC value displayed prominently. Right: Calibration plot (reliability diagram) showing predicted probability on the x-axis vs. actual churn rate on the y-axis. Ideal calibration line (diagonal) vs. model's actual calibration curve. Good calibration = close to the diagonal.

---

## Slide 7 — Foundation Model Fine-Tuning: When and How

**Figure:** *Fine-tuning architecture diagram.* Base Foundation Model (large box, gray) with adapter layers (small gold layers on top) representing LoRA. Two training inputs shown: a pair of (instruction, expected output) examples. Below: comparison of base model output vs. fine-tuned output for a NorthStar product description (base model: generic; fine-tuned: retail-specific, structured correctly). The visual makes the "better at domain task" outcome concrete and visible.

---

## Slide 8 — Reproducibility: The Non-Negotiable Standard

**Figure:** *Reproducibility checklist.* Six-item checklist with pass/fail icons. Each item has: a checkbox, the requirement name, and a "What breaks without this" consequence in small text. Example: ☑ Fixed random seeds → "Without: training run 1 and training run 2 produce slightly different models; evaluation metrics drift." A "Reproducibility Score" gauge on the right: 0/6 = "Not Reproducible"; 6/6 = "Fully Reproducible." Clean, high-contrast.

---

## Slide 9 — MLflow: The Experiment Tracking Standard

**Figure:** *MLflow experiment UI mockup.* A realistic recreation of the MLflow Runs table for the churn model. Table shows 5 runs with columns: Run Name, AUC, Precision@0.4, Recall@0.4, n_estimators, max_depth, learning_rate. Best run highlighted in gold. The "Compare Runs" view below shows two selected runs side by side, with metric differences. The UI shows real NorthStar values, making it look like actual student work product.

---

## Slide 10 — Model Registry: From Experiment to Production Candidate

**Figure:** *Model Registry workflow diagram.* Vertical flow with 5 steps numbered and connected by arrows. Step 1-2 (Training side, blue): S3 artifact → evaluation script → gate check. Step 3 (Registry, center, navy): "Pending Review" badge on model package card. Step 4 (Governance, amber): reviewer icon, approved/rejected decision. Step 5 (Deployment, teal): CI/CD trigger. The "Approved" path goes right (to deployment); the "Rejected" path goes left (back to development with documented reason).

---

## Slide 11 — SHAP: Making the Churn Model Explainable

**Figure:** *SHAP summary plot.* Horizontal bar chart showing SHAP importance values for all 8 NorthStar features. Y-axis: feature names. X-axis: mean |SHAP value|. Bars colored by feature type (demographic features in teal, transaction features in navy, engagement features in gold). recency_days is clearly the longest bar. A second "SHAP Waterfall Plot" for a single customer (showing how each feature pushed the prediction toward/away from churn) sits below the summary plot. This is what the Lab 3 evaluation report should contain.

---

## Slide 12 — Lab 3 Assigned: Model Development

**Figure:** *Lab 3 architecture diagram.* Shows the complete pipeline: Feature Store (offline read) → training/validation split (time-based) → SageMaker Training Job → MLflow experiment log → model evaluation (gate criteria check) → Model Registry registration. All NorthStar-specific values labeled. Lab 2 components shown in gray (already built); Lab 3 components shown in blue (what they're building now).

---

## Slide 13 — Common Model Development Mistakes

**Figure:** *Five-row anti-pattern table.* Same format as previous anti-pattern slides. Each row: icon, anti-pattern name, consequence, fix. "Cherry-picking threshold" row has an additional annotation: "Symptom: precision and recall both look suspiciously good." "Overfitting to validation" row has annotation: "Your test AUC is always 3-5% lower than your validation AUC — this is normal. If it's 10%+ lower, you've overfit."

---

## Slide 14 — From Model to System: What Lab 3 Produces

**Figure:** *"Model to System" transformation pipeline.* A horizontal flow starting from "model.tar.gz" (the Lab 3 output, shown as a gold hexagon) and flowing through each subsequent component (inference script → container → endpoint config → monitoring → runbook). Each component beyond "model.tar.gz" is shown in lighter gray with a lab number label (Lab 4, Lab 5, Lab 6). The visual makes clear that Lab 3 produces the foundation, and subsequent labs build the operational wrapper around it.

---

## Slide 15 — NorthStar: Model Development Decisions Summary

**Figure:** *Three-system comparison card layout.* Three side-by-side cards (one per NorthStar AI system). Each card: system name (header), approach badge (colored: Custom Training = navy, RAG = teal, Agent = gold), why chosen (3 bullet points), which lab. The Churn Prediction card is highlighted with a "Lab 3 Focus" badge. Clean card design, consistent format.

---

## Slide 16 — Key Takeaways + What's Next

**Figure:** *Five-takeaway summary.* Standard format. Preview banner for L08 (RAG architecture diagram). Lab 3 countdown: "Assigned in 7 days."
