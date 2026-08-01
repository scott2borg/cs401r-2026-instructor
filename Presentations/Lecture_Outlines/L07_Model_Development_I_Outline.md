---
lecture: L07
title: Model Development I
date: Thursday, September 24, 2026
week: 4
arc: Build
reading_due: "Model Development — Motivation through Fine-Tuning Foundation Models; Reproducibility and Model Versioning"
lab_due: "Lab 2 due Sat Oct 3"
slides_target: 16
---

# L07: Model Development I
**Thursday, September 24, 2026 | CS 401R: Engineering Production AI Systems | Fall 2026**

> The development spectrum from prompt engineering to custom training. How to choose your approach. Training custom models. Fine-tuning foundation models. Reproducibility and model versioning. This lecture sets the conceptual and technical foundation for Lab 3.

**Reading Due:** *Model Development* — "Motivation" through "Fine-Tuning Foundation Models"; "Reproducibility and Model Versioning"

---

## Slide 1 — Title
**Layout:** Left dark panel + right development spectrum visualization

**Content:**
- Model Development I
- CS 401R · Lecture 07 · Thursday, September 24, 2026
- Development Spectrum · Training · Fine-Tuning · Reproducibility

**Figure:** *AI development spectrum.* A horizontal spectrum from left (Simple, Fast, Cheap) to right (Complex, Slow, Expensive). Five labeled positions along the spectrum: "Prompt Engineering," "RAG," "Fine-Tuning," "Custom Training," "Full Architecture Design." Each position shows a complexity icon, a time-to-first-result estimate (hours, days, weeks, months), and a cost indicator ($). Color gradient from green (left) to red (right). A vertical arrow labeled "Start here" points to "Prompt Engineering" with caption: "Move right only when you can justify it."

**Notes:** "Today's lecture covers the left half of this spectrum — custom training and fine-tuning. Thursday covers RAG (Lecture 8) and Agents (Lecture 9). By the end of next week, you'll have a complete mental model of every AI development approach and how to choose between them." Open with: "What approach did NorthStar choose for each of its three AI systems? And why?" Let students answer before revealing.

---

## Slide 2 — The Development Spectrum: Five Approaches
**Layout:** Five-row table with approach, when to use, example

**Content:**
| Approach | What You Build | When to Use | NorthStar Example |
|----------|---------------|-------------|-------------------|
| **Prompt Engineering** | A carefully crafted prompt for an existing foundation model | Problem requires language understanding; behavior can be fully specified in a prompt; time to production is critical | Offer Generation first pass — test whether GPT-4 can generate adequate offers before building RAG |
| **RAG** | A retrieval pipeline + prompt that provides relevant context to a foundation model at inference time | Foundation model has no access to proprietary data; accuracy requires grounding in specific documents | Offer Generation final system — retrieves customer history + product catalog before generating offer text |
| **Fine-Tuning** | A foundation model with additional training on domain-specific data | Base model has the right architecture but wrong domain knowledge; enough labeled examples exist | NorthStar product description classifier — fine-tune for retail domain language |
| **Custom Training** | A model trained from scratch on your data | Problem is tabular/structured data; foundation models don't add value; full control of architecture | Churn Prediction — XGBoost on tabular customer transaction data |
| **Full Architecture** | Custom model architecture designed for specific problem | No existing architecture is adequate; massive scale; strong research capability needed | Reserved for companies with large research teams (not NorthStar, not most enterprises) |

**Figure:** *Development spectrum visual as a horizontal stacked bar.* Each approach is a colored segment. Width suggests approximate "coverage" in enterprise AI (RAG and Custom Training are widest; Full Architecture is very narrow). Below each segment: 2-3 word use case label. The bar makes it clear that most enterprise AI lives in the RAG + Custom Training segments.

**Notes:** "The most important judgment in AI development is: what level of the spectrum do I actually need? The failure mode is almost always going too far right — spending weeks fine-tuning when a well-crafted prompt would have been sufficient, or building a custom training pipeline when RAG would have worked better and faster."

---

## Slide 3 — Why NorthStar Uses XGBoost for Churn Prediction
**Layout:** Decision rationale with model comparison

**Content:**
**The Churn Prediction Problem:**
- Input: 8 engineered tabular features (recency, frequency, monetary, engagement metrics)
- Output: probability of churn in the next 90 days
- Data: 250K customer records, 18 months of history, ~12% historical churn rate
- Latency requirement: batch (nightly), not real-time

**Why XGBoost and not a neural network?**
| Factor | XGBoost | Neural Network |
|--------|---------|---------------|
| Data type | Tabular (structured) | Tabular (suboptimal) |
| Training data size | 250K examples | Needs millions for advantage |
| Interpretability | High (feature importance) | Low (black box) |
| Training time | Minutes | Hours-days |
| Hyperparameter tuning | Well-understood | More complex |
| Production serving | Lightweight, fast | Heavier, more latency |

**Why not a foundation model?** The problem is structured prediction, not language understanding. Foundation models add no value for tabular features — and add significant cost and latency.

**Figure:** *Decision tree flowchart for model selection.* Starting from "What type of data?" → branches: Tabular (→ Classical ML / XGBoost / LightGBM), Text/Documents (→ Foundation Model / RAG / Fine-Tuning), Images (→ CNN / Vision Foundation Model). Churn prediction follows the Tabular branch. At each decision node, the reasoning is shown. The "NorthStar Churn" path is highlighted in gold throughout the flowchart.

**Notes:** "The correct answer is almost always: start with the simplest model that meets the success criteria. For tabular prediction problems, XGBoost is still the state of the art in most enterprise settings. Adding complexity doesn't add accuracy for this problem type — it adds cost, latency, and debugging difficulty." Feature importance from XGBoost is also directly useful for the business: "Here are the top signals driving churn in our customer base."

---

## Slide 4 — XGBoost Training on SageMaker: The Architecture
**Layout:** Training job architecture with inputs, computation, outputs

**Content:**
**SageMaker Training Job for NorthStar Churn:**

**Inputs:**
- Training data: s3://northstar-features/churn-training-2026-09/*.parquet (from Feature Store offline read)
- Validation data: s3://northstar-features/churn-validation-2026-09/*.parquet
- Hyperparameters: n_estimators, max_depth, learning_rate, scale_pos_weight (class imbalance handling)
- Container: AWS XGBoost built-in container (no custom Docker required)

**Computation (ml.m5.xlarge, ~45 minutes):**
- Loads training data, trains XGBoost model
- Outputs: model.tar.gz (the trained model artifact), training metrics to CloudWatch
- MLflow logging: all parameters, metrics, and artifact URI recorded automatically

**Outputs:**
- Model artifact: s3://northstar-artifacts/churn/v{run_id}/model.tar.gz
- Training metrics: AUC, precision, recall, F1 at multiple thresholds
- Feature importance: SHAP values for all 8 features

**Figure:** *SageMaker Training Job diagram.* Three-column layout: Inputs (S3 parquet files, hyperparameters config) → Training Container (XGBoost container on ml.m5.xlarge, training loop, metric logging) → Outputs (model artifact in S3, CloudWatch metrics, MLflow experiment log). A side channel shows: "MLflow Auto-Logging" capturing all parameters and metrics. The NorthStar-specific values are filled in (45-minute runtime, ml.m5.xlarge cost: $0.30, feature importance SHAP output).

**Notes:** "The SageMaker Training Job abstracts away instance provisioning, monitoring, and cleanup. You provide: the container (built-in XGBoost), the training script, the data location, and the output location. SageMaker handles the rest." In Lab 3, students write a training script that reads from their Lab 2 Feature Store, trains an XGBoost model, and saves the artifact to S3. The training job architecture from this slide is what they're building.

---

## Slide 5 — Training the Churn Model: Key Engineering Decisions
**Layout:** Decision table with NorthStar choices and rationale

**Content:**
**Lab 3 Engineering Decisions:**

**1. Train/Validation/Test Split:**
- Standard random split is WRONG for time-series customer data (temporal leakage risk)
- Correct approach: time-based split — train on 2024-01 to 2026-06, validate on 2026-07 to 2026-08, test on 2026-09
- Rationale: simulates real production behavior (model always predicts into the future)

**2. Class Imbalance Handling:**
- NorthStar churn rate: ~12% (imbalanced)
- Options: oversample (SMOTE), undersample, or set `scale_pos_weight` in XGBoost
- Recommended: `scale_pos_weight = (1 - 0.12) / 0.12 ≈ 7.3` — adjusts XGBoost's cost function

**3. Hyperparameter Tuning:**
- Use SageMaker Automatic Model Tuning (AMT) for systematic search
- Search space: n_estimators (100-500), max_depth (3-8), learning_rate (0.01-0.3)
- Objective metric: validation:auc
- Budget: 10 training jobs (each ~45 min), automated search

**4. Success Criterion:**
- Gate criteria from Stage 6: AUC ≥ 0.72, Precision@threshold_0.4 ≥ 0.65
- These were set in the Stage 1 Project Charter — before any data was seen

**Figure:** *Engineering decision summary table.* Four rows (one per decision), three columns: Decision, Wrong Approach (red background), Correct Approach (green background). Compact, high-contrast. Caption: "Each of these decisions affects production model quality. The 'wrong approach' is what most teams default to without thinking."

**Notes:** "The time-based split is the most important engineering decision in Lab 3. Random splitting a time-series dataset causes temporal leakage — you're training on the future and testing on the past. The model will show excellent evaluation metrics and fail in production, exactly like the Zillow case." This connection between training methodology and the Zillow cautionary tale from L05 should click for students.

---

## Slide 6 — Evaluating the Churn Model: The Lab 3 Gate
**Layout:** Evaluation metrics dashboard with NorthStar thresholds

**Content:**
**The Stage 6 Gate Criteria for NorthStar Churn Model:**

**Primary Metrics:**
- **AUC (Area Under ROC Curve) ≥ 0.72** — measures overall discrimination ability
- **Precision@threshold=0.4 ≥ 0.65** — of customers flagged as at-risk, 65% must actually churn
- **Recall@threshold=0.4 ≥ 0.55** — must catch at least 55% of actual churners

**Secondary Metrics:**
- Feature importance: recency_days must be in top-3 features (sanity check)
- Calibration: predicted probabilities should match actual churn rates (use reliability diagram)

**Business-informed threshold selection:**
- The 0.4 threshold is chosen by the business: it controls the volume of retention offers sent
- Lower threshold = more offers = more cost = more churners caught
- Higher threshold = fewer offers = less cost = fewer churners caught
- Threshold is a business decision, not a model decision

**Figure:** *ROC Curve with calibration plot.* Left: ROC curve (AUC = 0.76 for a good run), with the chosen operating point (threshold = 0.4) marked with a gold dot. Shaded region above the diagonal. AUC value displayed prominently. Right: Calibration plot (reliability diagram) showing predicted probability on the x-axis vs. actual churn rate on the y-axis. Ideal calibration line (diagonal) vs. model's actual calibration curve. Good calibration = close to the diagonal.

**Notes:** "The gate criteria were set before the model was trained — in the Stage 1 Project Charter. This is what prevents post-hoc rationalization: 'we got AUC 0.68, but we think that's good enough.' It's not. The gate says 0.72. If the model doesn't pass, we return to Stage 5 (develop) or Stage 2 (discover more data). The gate owner decides, not the engineering team."

---

## Slide 7 — Foundation Model Fine-Tuning: When and How
**Layout:** Fine-tuning architecture diagram with use case criteria

**Content:**
**When to Fine-Tune (vs. prompt engineering or RAG):**
✅ Fine-tune when:
- The base model's behavior is correct, but its domain knowledge is wrong
- You have 1,000-100,000 labeled examples
- A consistent output format is required at scale (e.g., structured JSON every time)
- The task cannot be solved with retrieval (the knowledge isn't in documents)

❌ Don't fine-tune when:
- You have fewer than 500 examples (insufficient signal)
- The base model already does the task well with a good prompt
- The domain knowledge changes frequently (you'd need to re-fine-tune constantly)

**Fine-Tuning Approaches:**
1. **Full fine-tuning:** Update all model weights — most powerful, requires most compute and data
2. **LoRA / QLoRA:** Update small adapter matrices — practical for most enterprise use cases; 10-100× cheaper
3. **Instruction fine-tuning:** Train on instruction-following pairs — improves task adherence

**NorthStar Fine-Tuning Use Case (optional in Lab 3):**
Fine-tune a foundation model on NorthStar product descriptions to improve the quality of product categorization for the RAG system.

**Figure:** *Fine-tuning architecture diagram.* Base Foundation Model (large box, gray) with adapter layers (small gold layers on top) representing LoRA. Two training inputs shown: a pair of (instruction, expected output) examples. Below: comparison of base model output vs. fine-tuned output for a NorthStar product description (base model: generic; fine-tuned: retail-specific, structured correctly). The visual makes the "better at domain task" outcome concrete and visible.

**Notes:** "LoRA is the practical choice for most enterprise fine-tuning use cases. Full fine-tuning requires significant GPU compute and careful learning rate management. LoRA adds a small number of trainable parameters (the adapter matrices) while keeping the base model weights frozen — achieving most of the benefit at a fraction of the cost." AWS Bedrock now supports fine-tuning via their model customization API — students can use this for the optional Lab 3 fine-tuning task.

---

## Slide 8 — Reproducibility: The Non-Negotiable Standard
**Layout:** What reproducibility requires + what breaks it

**Content:**
**Why Reproducibility Matters:**
- You need to reproduce a specific model version to investigate a production incident
- A regulator asks you to prove exactly how a model was trained
- A team member needs to verify a result before approving the gate
- You discover a bug and need to retrain from a known-good state

**What Full Reproducibility Requires:**
1. **Fixed random seeds:** `xgb.train(..., seed=42)` — every element of stochasticity must be seeded
2. **Pinned library versions:** `requirements.txt` with exact versions (not `>=`; exact `==`)
3. **Versioned training data:** Point-in-time Feature Store read + data hash logged to MLflow
4. **Captured hyperparameters:** Every parameter, even defaults, logged to MLflow
5. **Environment specification:** Docker image tag, Python version, compute instance type
6. **Deterministic data ordering:** Sort or shuffle with fixed seed before splits

**The reproducibility test:** Can a colleague reproduce your exact model artifact from scratch, using only your MLflow experiment log?

**Figure:** *Reproducibility checklist.* Six-item checklist with pass/fail icons. Each item has: a checkbox, the requirement name, and a "What breaks without this" consequence in small text. Example: ☑ Fixed random seeds → "Without: training run 1 and training run 2 produce slightly different models; evaluation metrics drift." A "Reproducibility Score" gauge on the right: 0/6 = "Not Reproducible"; 6/6 = "Fully Reproducible." Clean, high-contrast.

**Notes:** "The reproducibility test is simple: hand your MLflow experiment log to a colleague and ask them to reproduce your model. If they can't without asking you questions, your experiment logging is incomplete." This is not academic — in enterprise settings, model audits require complete traceability. Regulators in financial services and healthcare now routinely require model development logs as evidence.

---

## Slide 9 — MLflow: The Experiment Tracking Standard
**Layout:** MLflow UI mockup with NorthStar churn experiments

**Content:**
**MLflow Tracking Components:**
- **Experiments:** Groups of related runs (e.g., "churn-prediction-v2-tuning")
- **Runs:** Individual training executions, each with parameters, metrics, and artifacts
- **Parameters:** All hyperparameters and configuration values (logged at run start)
- **Metrics:** All performance metrics (logged during and after training)
- **Artifacts:** Model files, plots, evaluation reports (logged after training)
- **Tags:** Metadata (run_name, git_commit, data_version)

**NorthStar MLflow experiment output example:**
```
Experiment: churn-v2-tuning (12 runs)
Best Run: churn-v2-run-009
  Params: n_estimators=350, max_depth=5, learning_rate=0.08
  Metrics: auc=0.763, precision_at_0.4=0.71, recall_at_0.4=0.57
  Artifacts: model.tar.gz, shap_feature_importance.png, roc_curve.png
  Tags: data_version=churn-features-2026-09-18, git_commit=a3f2b8c
```

**Figure:** *MLflow experiment UI mockup.* A realistic recreation of the MLflow Runs table for the churn model. Table shows 5 runs with columns: Run Name, AUC, Precision@0.4, Recall@0.4, n_estimators, max_depth, learning_rate. Best run highlighted in gold. The "Compare Runs" view below shows two selected runs side by side, with metric differences. The UI shows real NorthStar values, making it look like actual student work product.

**Notes:** "The MLflow UI for the NorthStar churn model should look exactly like this after Lab 3. You should have at least 5 experiment runs, each with all parameters and metrics logged, and the best run registered in the Model Registry." SageMaker integrates MLflow natively through SageMaker Experiments — students can use the SageMaker console to view their experiments without running a separate MLflow server.

---

## Slide 10 — Model Registry: From Experiment to Production Candidate
**Layout:** Model Registry workflow with NorthStar example

**Content:**
**The Path from Experiment to Registry:**

1. Training job completes → model artifact saved to S3
2. Evaluate: does the model pass the Stage 6 gate criteria?
   - AUC ≥ 0.72 ✓, Precision@0.4 ≥ 0.65 ✓, Recall@0.4 ≥ 0.55 ✓
3. Register: create a Model Package in the SageMaker Model Registry
   - Attach evaluation metrics, training data version, feature group version
   - Status: "Pending Review"
4. Review: the Governance role reviews the model package
   - Check: metrics pass thresholds, training methodology is sound, no bias issues
   - Status: "Approved" (or "Rejected" with reasoning)
5. Deploy: CI/CD pipeline (Lab 4) detects "Approved" status and triggers deployment

**Lab 3 deliverable:** At least one model package in the Model Registry with "Pending Review" status and all required metadata attached.

**Figure:** *Model Registry workflow diagram.* Vertical flow with 5 steps numbered and connected by arrows. Step 1-2 (Training side, blue): S3 artifact → evaluation script → gate check. Step 3 (Registry, center, navy): "Pending Review" badge on model package card. Step 4 (Governance, amber): reviewer icon, approved/rejected decision. Step 5 (Deployment, teal): CI/CD trigger. The "Approved" path goes right (to deployment); the "Rejected" path goes left (back to development with documented reason).

**Notes:** "The Model Registry is the handshake between the ML team and the operations team. The ML team says: 'Here is a model that passes our evaluation criteria.' The Governance team says: 'We have reviewed it and it is safe to deploy.' The CI/CD pipeline says: 'It's approved — deploy it.' Without the registry, these three functions are email threads and Slack messages, which is how models get deployed without proper review."

---

## Slide 11 — SHAP: Making the Churn Model Explainable
**Layout:** SHAP value plot with NorthStar feature importances

**Content:**
**Why Model Explainability Matters:**
- The business wants to know why this customer is being flagged as at risk.
- Regulators may ask: are protected attributes (age, gender) driving decisions?
- Engineers debugging: which features are contributing to anomalously high false positive rates?

**SHAP (SHapley Additive exPlanations):**
- Provides consistent, mathematically grounded feature importance scores
- Available natively in XGBoost (`xgb.get_booster().get_score(importance_type='gain')`)
- For individual predictions: shows which features pushed the prediction up or down

**Expected NorthStar Feature Importance (healthy model):**
1. recency_days (strongest churn signal)
2. frequency_90d (declining frequency → churn signal)
3. monetary_trend (declining spend trend)
4. tenure_days (long-tenure customers churn differently)
5. sessions_7d (declining engagement signal)
6. support_contacts_30d (high friction signal)
7. loyalty_tier (moderate importance)
8. category_breadth_90d (lowest importance)

**If your model doesn't show recency_days in the top-3, check your feature engineering.**

**Figure:** *SHAP summary plot.* Horizontal bar chart showing SHAP importance values for all 8 NorthStar features. Y-axis: feature names. X-axis: mean |SHAP value|. Bars colored by feature type (demographic features in teal, transaction features in navy, engagement features in gold). recency_days is clearly the longest bar. A second "SHAP Waterfall Plot" for a single customer (showing how each feature pushed the prediction toward/away from churn) sits below the summary plot. This is what the Lab 3 evaluation report should contain.

**Notes:** "If recency_days is not in your top-3 features, something is wrong. Either your recency calculation is off (check your feature engineering), your training data has a labeling problem, or there's a temporal leakage issue. The feature importance sanity check is a diagnostic tool, not just a reporting requirement."

---

## Slide 12 — Lab 3 Assigned: Model Development
**Layout:** Lab assignment slide with task list

**Content:**
**Lab 3: Model Development**
- **Assigned:** Thursday, October 1 (next Thursday — announced early today as preview)
- **Due:** Saturday, October 17, midnight
- **Builds on:** Lab 2 (Feature Store data feeds this lab)

**Key Tasks:**
1. Read from your Lab 2 Feature Store (offline store, point-in-time split)
2. Train an XGBoost churn prediction model on SageMaker
3. Run at least 5 experiments with different hyperparameter configurations in MLflow
4. Evaluate against Stage 6 gate criteria (AUC ≥ 0.72, Precision@0.4 ≥ 0.65)
5. Register the best model in SageMaker Model Registry with all required metadata
6. Produce: feature importance SHAP plot, ROC curve, calibration plot, evaluation report

**Optional (+5 points):** Fine-tune a small foundation model on NorthStar product descriptions using AWS Bedrock model customization

**Figure:** *Lab 3 architecture diagram.* Shows the complete pipeline: Feature Store (offline read) → training/validation split (time-based) → SageMaker Training Job → MLflow experiment log → model evaluation (gate criteria check) → Model Registry registration. All NorthStar-specific values labeled. Lab 2 components shown in gray (already built); Lab 3 components shown in blue (what they're building now).

**Notes:** "Lab 3 is assigned next Thursday — I'm previewing it today so you can start thinking about your feature engineering in Lab 2 in terms of what the churn model will need. The Feature Groups you design in Lab 2 directly determine the training data for Lab 3." Preview the optional bonus: "AWS Bedrock model customization lets you fine-tune models like Amazon Titan — it's a real production feature, and the experience of going through the fine-tuning workflow is valuable even at small scale."

---

## Slide 13 — Common Model Development Mistakes
**Layout:** Five anti-patterns with detection and fix

**Content:**
1. **Evaluating on the training set:** The model "achieves" AUC 0.99 — because it has memorized the training data. Fix: always evaluate on a held-out test set that was never used during training or hyperparameter tuning.

2. **Cherry-picking the evaluation threshold:** Setting the threshold to make precision and recall look good, rather than setting it based on business requirements. Fix: the threshold is set by the business before evaluation; don't tune it to hit the gate.

3. **No baseline comparison:** Claiming AUC 0.72 is good without establishing what a naive baseline achieves. Fix: always implement and evaluate a simple baseline (e.g., "flag the 15% of customers with the longest days since last purchase").

4. **Ignoring class imbalance:** With a 12% churn rate, a model that predicts "no churn" for everyone achieves 88% accuracy. Fix: use appropriate metrics (AUC, F1) and class-imbalance handling (scale_pos_weight).

5. **Overfitting to validation set:** Running too many experiments against the same validation set, inadvertently selecting hyperparameters that happen to work well on that specific sample. Fix: keep a held-out test set that is only evaluated once, at the very end.

**Figure:** *Five-row anti-pattern table.* Same format as previous anti-pattern slides. Each row: icon, anti-pattern name, consequence, fix. "Cherry-picking threshold" row has an additional annotation: "Symptom: precision and recall both look suspiciously good." "Overfitting to validation" row has annotation: "Your test AUC is always 3-5% lower than your validation AUC — this is normal. If it's 10%+ lower, you've overfit."

**Notes:** "The baseline comparison is the one that trips up students most often. If I have a dataset with 12% churners and I build a very simple model — 'flag all customers who haven't bought anything in 60 days' — that model might achieve AUC 0.68. If your XGBoost model achieves AUC 0.70, you've barely beaten the rule. AUC 0.76? Now you have something." Always establish the baseline before claiming the model is good.

---

## Slide 14 — From Model to System: What Lab 3 Produces
**Layout:** Model → System transformation diagram

**Content:**
**A trained model artifact is not a deployed system. Between the model file and the production endpoint are:**

1. **Inference script:** The code that loads the model and handles a prediction request (input validation, preprocessing, model call, output formatting)
2. **Container:** The Docker image that packages the inference script, model, and dependencies
3. **Endpoint configuration:** Instance type, auto-scaling policy, latency targets
4. **Monitoring configuration:** What metrics to track; what thresholds to alert on
5. **Runbook:** What to do when the endpoint fails, degrades, or times out

**Lab 3 produces:** the trained model artifact, the evaluation report, and Model Registry registration. Labs 4-6 build the remaining components.

**The Lab 3 deliverable IS the Stage 5 + Stage 6 output of the AISDLC.**

**Figure:** *"Model to System" transformation pipeline.* A horizontal flow starting from "model.tar.gz" (the Lab 3 output, shown as a gold hexagon) and flowing through each subsequent component (inference script → container → endpoint config → monitoring → runbook). Each component beyond "model.tar.gz" is shown in lighter gray with a lab number label (Lab 4, Lab 5, Lab 6). The visual makes clear that Lab 3 produces the foundation, and subsequent labs build the operational wrapper around it.

**Notes:** "Students often feel like Lab 3 is 'done' when the model is trained and evaluated. It's not done — it's not even deployed yet. The model file is Step 1 of 6 toward a production system. This is the core insight: a model is an ingredient, not a product. The product is the complete system that uses the model." This sets up Labs 4, 5, and 6 as the engineering work that transforms the model ingredient into the production product.

---

## Slide 15 — NorthStar: Model Development Decisions Summary
**Layout:** Summary table of all three NorthStar model development decisions

**Content:**
| System | Approach | Why | Lab |
|--------|----------|-----|-----|
| Churn Prediction | Custom training (XGBoost) | Tabular data; strong baseline; interpretability required; 250K examples | Lab 3 |
| Offer Generation | RAG on foundation model | Requires personalization from customer data + product catalog; no labeled training data | Lab 3 (optional) + L08 |
| Customer Service Agent | ReAct agent on foundation model | Multi-step reasoning; tool use; no training data for agent behavior | L09 |

**Decision rationale for Lab 3 focus (churn model):**
- Highest business priority (churn = lost revenue)
- Tabular data makes custom training appropriate
- Interpretability requirement (explain to the business which customers and why)
- Training data available (18 months of transaction history)
- Clear success criteria (AUC ≥ 0.72 from Stage 1 charter)

**Figure:** *Three-system comparison card layout.* Three side-by-side cards (one per NorthStar AI system). Each card: system name (header), approach badge (colored: Custom Training = navy, RAG = teal, Agent = gold), why chosen (3 bullet points), which lab. The Churn Prediction card is highlighted with a "Lab 3 Focus" badge. Clean card design, consistent format.

**Notes:** "Lab 3 focuses on the churn model because it illustrates the custom training workflow most clearly. The RAG and agent systems (Labs 5 and 9 lectures) have different development workflows. By the time we get to Labs 5-6, you'll have the custom training and CI/CD patterns well understood — which actually helps you design better RAG and agent systems."

---

## Slide 16 — Key Takeaways + What's Next
**Layout:** Takeaways + Lab 3 preview + next session

**Content:**
**Key Takeaways:**
1. The development spectrum runs from prompt engineering to full architecture — always start at the left and move right only when justified by data, use case, and time-to-production constraints
2. XGBoost is the right choice for NorthStar's tabular churn prediction problem — foundation models add no value for structured prediction with 250K examples
3. Time-based train/validation/test splits are required for time-series customer data — random splits cause temporal leakage
4. Reproducibility requires: fixed seeds, pinned library versions, versioned training data, captured hyperparameters, and environment specification
5. The Model Registry is the handshake between ML engineering, governance, and operations — nothing deploys without a registered, approved package

**Next Session (Tue Sep 29):**
- Topic: Model Development II — RAG: architecture, chunking, embedding, reranking, evaluation
- Reading due: *Model Development* — "Retrieval-Augmented Generation" section
- Lab 3 assigned next Thursday (Oct 1) — preview: you'll train the XGBoost churn model

**Figure:** *Five-takeaway summary.* Standard format. Preview banner for L08 (RAG architecture diagram). Lab 3 countdown: "Assigned in 7 days."

**Notes:** "Lab 2 due in 9 days. Lab 3 preview is what you just saw today. The connection is direct: the Feature Store you build in Lab 2 is the input to the XGBoost model you'll train in Lab 3. Design your feature groups in Lab 2 knowing what the model will need."
