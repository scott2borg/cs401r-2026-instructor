---
lecture: L13
title: Testing & Evaluation II
date: Thursday, October 15, 2026
week: 7
arc: Build
reading_due: "Testing AI Systems — System Testing through Key Takeaways"
lab_assigned: "Lab 4 — CI/CD Pipeline (due Sat Oct 31)"
lab_due: "Lab 3 due Sat Oct 17"
slides_target: 16
---

# L13: Testing & Evaluation II
**Thursday, October 15, 2026 | CS 401R: Engineering Production AI Systems | Fall 2026**

Evaluation is the discipline of measuring whether an AI system is good enough to deploy — and to keep running. Learn to design evaluation frameworks, run A/B tests, and know when to call in humans.

**Reading Due:** *Testing AI Systems* — "System Testing" through "Key Takeaways"
**Lab 4 Assigned Today:** CI/CD Pipeline — due Sat Oct 31

---

## Slide 1 — Title
**Layout:** Left dark panel + right split evaluation scorecard visual

**Content:**
- Testing & Evaluation II: Evaluation Frameworks & A/B Testing
- CS 401R · Lecture 13 · Thursday, October 15, 2026
- ⚠️ Lab 4 Assigned Today — Due October 31

**Figure:** *Evaluation scorecard visual.* A scorecard card with three sections: Churn Model (AUC: 0.74 ✅ | Calibration: 0.91 ✅ | Segment Coverage: ✅), RAG Offer Generation (Faithfulness: 0.96 ✅ | Relevancy: 0.88 ✅ | Recall@5: 0.83 ✅), Agent (Resolution Rate: 91% ✅ | Escalation: 8.3% ✅ | Cost/session: $0.004 ✅). A "DEPLOY APPROVED" stamp in green. The scorecard communicates: evaluation produces concrete metrics against concrete thresholds, resulting in a clear deployment decision.

**Notes:** "Today is Lab 4 day. The spec is posted. Lab 4 is due in 16 days. Today we cover the evaluation frameworks and A/B testing principles that are directly relevant to your Lab 4 gate check implementation — so pay attention to the ConditionStep discussion in slides 5 and 6."

---

## Slide 2 — The Evaluation Framework: From Metrics to Decisions
**Layout:** Evaluation framework design with NorthStar criteria

**Content:**
**How to Build an Evaluation Framework:**

An evaluation framework has three components:
1. **Metrics:** What you measure (AUC, faithfulness, resolution rate)
2. **Thresholds:** What value is "good enough" for deployment
3. **Decision logic:** How multiple metrics combine into a go/no-go decision

**Common threshold design mistakes:**
- Setting thresholds arbitrarily ("0.70 AUC sounds good")
- Using a single metric when multiple dimensions matter
- Not establishing a baseline (new model vs. what?)

**How NorthStar set its thresholds:**
- **Step 1:** Establish the business requirement. For churn: "We need to identify 70%+ of churners before they leave (recall). Precision must be high enough that we're not offering discounts to people who wouldn't churn anyway."
- **Step 2:** Translate to model metrics. Required recall → required AUC. Ran a historical analysis: AUC ≥ 0.72 achieves 78% recall at a precision threshold of 0.4 on historical data.
- **Step 3:** Add a safety margin. Gate set at 0.72, which gives margin above the 0.70 minimum business requirement.
- **Step 4:** Define the baseline. The new model must beat the current production model by ≥ 2% in AUC.

**Figure:** *Threshold derivation diagram.* Two-panel figure. Left: ROC curve for NorthStar churn model at several AUC values (0.65, 0.70, 0.72, 0.75). At each AUC value, recall@0.4-precision is marked. Shows that AUC 0.72 → 78% recall@0.4-precision. Right: Decision tree for gate logic: "AUC ≥ 0.72? AND Recall ≥ 0.75? AND Beats production by ≥ 2%? → DEPLOY. Else → ALERT + retrain."

**Notes:** "The threshold derivation process is what separates professional ML engineering from toy projects. When an executive asks why the deployment gate is 0.72 AUC, you should be able to show the analysis that connects that number to business outcomes — not just say 'it seemed like a good threshold.' This is the documentation that belongs in your evaluation report (Lab 4 deliverable)."

---

## Slide 3 — Multi-Dimensional Evaluation for AI Systems
**Layout:** Evaluation scorecard design across all three NorthStar systems

**Content:**
**NorthStar Evaluation Scorecards:**

**Churn Model Scorecard:**
| Metric | Threshold | Weight | Source |
|--------|-----------|--------|--------|
| AUC | ≥ 0.72 | Gate (must pass) | Holdout test set |
| Recall@0.4-precision | ≥ 0.75 | Gate (must pass) | Holdout test set |
| Beat production model | ≥ +2% AUC | Gate (must pass) | A/B comparison |
| Calibration (Brier) | ≤ 0.20 | Advisory | Calibration curve |
| Segment fairness | No segment AUC < 0.60 | Gate (must pass) | Segment analysis |

**RAG Offer Generation Scorecard:**
| Metric | Threshold | Weight |
|--------|-----------|--------|
| RAGAS Faithfulness | ≥ 0.95 | Gate |
| RAGAS Answer Relevancy | ≥ 0.85 | Gate |
| RAGAS Context Recall | ≥ 0.80 | Gate |
| Format compliance | = 1.00 | Gate |
| P90 latency | ≤ 3.0s | Gate |

**Agent Scorecard:**
| Metric | Threshold | Weight |
|--------|-----------|--------|
| Resolution rate | ≥ 85% | Gate |
| Escalation rate | 5-20% | Gate (range) |
| Tool failure rate | ≤ 2% | Gate |
| P90 session cost | ≤ $0.015 | Advisory |
| CSAT (sampled) | ≥ 4.0/5.0 | Advisory |

**Figure:** *Three evaluation scorecards side by side.* Each scorecard formatted as a card with: system name, metric rows with status indicators (✅/❌/⚠️), and DEPLOY/HOLD/ALERT at the bottom. All three showing "DEPLOY" state in green. Advisory metrics shown in grey (not blocking). The design communicates: evaluation produces a clear, auditable deployment decision.

**Notes:** "Advisory metrics (Brier score, session cost, CSAT) don't block deployment — but they're in the scorecard because they inform future action. If CSAT drops below 3.5, that's a signal to investigate even if the automated metrics look fine. Advisory metrics are early warning signals; gate metrics are hard stops."

---

## Slide 4 — Segmented Evaluation: The Missing Practice
**Layout:** Segment performance analysis for NorthStar churn model

**Content:**
**Why Average Performance Lies:**

Example: Overall AUC = 0.74. Gates pass. Deploy.
But:
- High-value customers (top 20% by revenue): AUC = 0.81 ✅
- Medium-value customers: AUC = 0.73 ✅
- Low-value new customers (< 90 days tenure): AUC = 0.57 ❌
- Seasonal/irregular shoppers: AUC = 0.63 ❌

The model performs well on the majority but poorly on exactly the customers you most need to retain.

**Segment evaluation implementation:**
```python
def evaluate_by_segment(model, X_test, y_test, segment_column):
    """Evaluate model AUC for each segment."""
    results = {}
    for segment in X_test[segment_column].unique():
        mask = X_test[segment_column] == segment
        X_seg = X_test[mask].drop(columns=[segment_column])
        y_seg = y_test[mask]
        
        if len(y_seg) < 100:  # Skip segments too small to evaluate
            results[segment] = {'auc': None, 'n': len(y_seg), 'status': 'INSUFFICIENT_DATA'}
            continue
        
        y_pred = model.predict_proba(X_seg)[:, 1]
        auc = roc_auc_score(y_seg, y_pred)
        results[segment] = {
            'auc': auc,
            'n': len(y_seg),
            'status': 'PASS' if auc >= 0.60 else 'FAIL'
        }
    
    return results

# Gate: no segment below 0.60 AUC with n >= 100
segment_results = evaluate_by_segment(model, X_test, y_test, 'customer_segment')
assert all(r['status'] in ['PASS', 'INSUFFICIENT_DATA'] 
           for r in segment_results.values())
```

**Figure:** *Segment AUC bar chart.* Horizontal bar chart with six customer segments on the y-axis and AUC on the x-axis (0.0 to 1.0). Segments: High-Value (0.81, green), Premium (0.77, green), Medium-Value (0.73, green), Seasonal (0.63, amber/warning), Low-Value-New (0.57, red/fail), Irregular (0.61, amber). Overall AUC marked as a vertical line (0.74). Gate threshold (0.60) marked as a red vertical line. The chart reveals: two segments fail the gate threshold despite an acceptable overall AUC.

**Notes:** "This chart is why segment evaluation is a gate requirement in NorthStar's evaluation framework. The Low-Value-New segment (customers in their first 90 days) is the hardest to predict — they don't have enough purchase history — but this is exactly the segment where early intervention is most effective. If the model can't predict churn in this segment, we need to flag it and potentially add features specific to new customers."

---

## Slide 5 — A/B Testing for AI Systems
**Layout:** A/B testing framework with statistical rigor

**Content:**
**A/B Testing in ML: The Right Way**

A/B testing for ML systems differs from web A/B testing:
- Traffic split must account for session correlation (same customer shouldn't see both models)
- Evaluation window must be long enough to capture the outcome of interest (churn happens over weeks, not hours)
- Business metrics (actual churn rate) lag behind model metrics (predicted churn probability)

**NorthStar Churn Model A/B Test Design:**

**Setup:**
- Model A (control): current production model (e.g., v2.3)
- Model B (challenger): new candidate model (v3.0)
- Traffic split: 80% control / 20% challenger (asymmetric to limit exposure to untested model)
- Split method: customer_id hash → consistent assignment (same customer always sees same model)

**Evaluation window:**
- 4 weeks minimum (to capture churn events that take 2-3 weeks to manifest)
- Success metric: observed churn rate in control vs. challenger populations

**Statistical criteria:**
- Minimum detectable effect: 5% relative improvement in churn prediction accuracy
- Power: 80% (probability of detecting the effect if it exists)
- Significance: p < 0.05, two-tailed
- Sample size required: ~12,000 customers per variant (calculated from power analysis)

**Figure:** *A/B test architecture diagram.* Customer request → traffic splitter (customer_id hash mod 5 → 0-3=Model A, 4=Model B) → Model A endpoint or Model B endpoint. Both endpoints → logging → evaluation system. Evaluation system: tracks actual churn outcomes, compares rates after a 4-week window. Statistical significance computed and displayed. Arrow from evaluation to "Promote B to production if significant improvement."

**Notes:** "The asymmetric 80/20 split is a risk management decision. You're not running this A/B test to maximize statistical power — you're running it to validate the new model with minimal exposure if it turns out to be worse. Once you're confident the new model is better, you shift to 50/50, then to 100% if the results hold. Never go straight to 100% without validation."

---

## Slide 6 — SageMaker Shadow Mode: Safe Production Evaluation
**Layout:** Shadow mode testing for zero-risk production evaluation

**Content:**
**Shadow Mode: The Risk-Free A/B Alternative**

Shadow mode sends every production request to both models simultaneously but returns only the production model's response to the user. The challenger model's responses are captured for evaluation but never shown.

**NorthStar Shadow Mode Setup:**
```python
# SageMaker Production Variant + Shadow Variant configuration
endpoint_config = {
    "EndpointConfigName": "northstar-churn-shadow-config",
    "ProductionVariants": [
        {
            "VariantName": "production-v2-3",
            "ModelName": "northstar-churn-v2-3",
            "InstanceType": "ml.m5.large",
            "InitialVariantWeight": 1.0  # gets 100% of traffic responses
        }
    ],
    "ShadowProductionVariants": [
        {
            "VariantName": "challenger-v3-0",
            "ModelName": "northstar-churn-v3-0",
            "InstanceType": "ml.m5.large",
            "SamplingPercentage": 100  # shadow evaluates 100% of traffic
        }
    ]
}
```

**What shadow mode gives you:**
- Zero risk: users always see production model responses
- Realistic load testing: challenger processes real production request distribution
- Offline comparison: compare production vs. challenger predictions on identical inputs
- Latency profiling: measure challenger latency under real load before promoting

**When to use shadow mode vs. A/B test:**
- Shadow mode: when you want to validate the challenger before exposing any users
- A/B test: when you want to measure downstream business metrics (actual churn rate requires real traffic to challenger)

**Figure:** *Shadow mode architecture diagram.* Request comes in → Production model (v2.3) processes the request → Response is returned to the user. Simultaneously: same request → Shadow model (v3.0) processes request → Response captured to S3 (not returned to user). S3 capture → comparison analysis → CloudWatch metrics showing production vs. shadow prediction distributions. "Zero user exposure" label on the shadow path.

**Notes:** "Shadow mode is underused in the industry. Teams often go straight to A/B testing because it's more familiar, but shadow mode is a safer first step. You can run the challenger model in shadow mode for a week, compare its predictions against production on real data, and proceed to A/B testing only if the shadow results look promising. It's a free validation step that costs only the compute for the shadow endpoint."

---

## Slide 7 — Human-in-the-Loop Evaluation
**Layout:** HITL evaluation design for LLM and agent systems

**Content:**
**When Automated Evaluation Isn't Enough:**

Automated evaluation (RAGAS, AUC, resolution rate) captures quantifiable dimensions. But some quality dimensions require human judgment:
- Is the offer tone appropriate for this customer segment?
- Does the agent's response feel natural and helpful?
- Is the reasoning trace logically consistent?

**NorthStar HITL Evaluation Program:**

**Frequency and scope:**
- Weekly: 100 randomly sampled RAG offer responses reviewed by the marketing team
- Monthly: 50 agent conversation traces reviewed by the customer service team
- On model update: 200 churn predictions reviewed by business analyst (spot-check)

**HITL evaluation rubric for RAG offers:**
1. Factual accuracy (1-5): Does the offer reference information that's actually true about this customer?
2. Relevance (1-5): Is the offer relevant to this customer's purchase history and segment?
3. Tone (1-5): Is the offer tone appropriate (not pushy, not generic)?
4. Format (pass/fail): Does it follow the required format?
5. Would you send this? (yes/no): Overall quality judgment

**HITL result reporting:**
- Aggregated scores by week: trend tracking
- Examples of low-scoring responses flagged for investigation
- Specific improvement patterns fed back to prompt engineering team

**Figure:** *HITL evaluation workflow diagram.* Sample production responses → annotation tool (Label Studio or custom UI) → human reviewer assigns scores on rubric → aggregated scores to CloudWatch → trend dashboard → weekly review meeting → prompt engineering or retraining action if trends decline. The workflow shows: HITL is not ad hoc — it's a systematic operational process with feedback loops.

**Notes:** "The 'Would you send this?' question is the most valuable one on the rubric. It's a holistic judgment that captures dimensions the other scores miss. If a response scores 4/5 on all dimensions but gets consistent 'no' answers on the overall judgment, that's a signal that something is wrong and you haven't yet quantified it. Use those 'no' examples to design better automated evaluation criteria."

---

## Slide 8 — Evaluation for RAG: RAGAS Deep Dive
**Layout:** RAGAS metric deep dive with NorthStar examples

**Content:**
**RAGAS Metrics: What They Actually Measure**

**Faithfulness (0-1):** What fraction of claims in the answer are supported by the retrieved context?
- Measured by: decompose answer into atomic claims → verify each claim against contexts → faithfulness = claims_supported / total_claims
- NorthStar example: Offer says "you purchased Nike shoes last month" → check if that claim appears in retrieved customer history
- High faithfulness: offer content is grounded in real customer data
- Pitfall: high faithfulness doesn't mean the response is *correct* — just that it's grounded in what was retrieved (garbage in, garbage out)

**Answer Relevancy (0-1):** Is the generated answer actually responsive to the question asked?
- Measured by: generate synthetic questions from the answer → compare to original question using embedding similarity
- NorthStar example: Customer asked for shoe recommendations; offer is about kitchen appliances → low relevancy
- High relevancy: the offer addresses what the customer is actually interested in

**Context Recall (0-1):** Was the relevant information actually retrieved from the index?
- Measured by: compare retrieved contexts against ground-truth relevant documents
- NorthStar example: Customer recently bought running shoes, but the running shoe category offers weren't retrieved → low recall
- High recall: retrieval is capturing the right documents

**The RAGAS pipeline for NorthStar (weekly evaluation):**
```python
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_recall
from ragas.llms import LangchainLLMWrapper
from langchain_aws import BedrockChat

# Use Claude as the RAGAS evaluator
evaluator_llm = LangchainLLMWrapper(BedrockChat(model_id='anthropic.claude-3-5-sonnet'))

results = evaluate(
    dataset=sampled_production_responses,  # 5% of weekly responses
    metrics=[faithfulness, answer_relevancy, context_recall],
    llm=evaluator_llm
)
```

**Figure:** *RAGAS metric visualization.* Three-panel figure. Each panel: bar chart showing score distribution for one metric across 200 sampled responses. Faithfulness: bimodal distribution (most responses near 1.0, a small tail near 0.5). Answer Relevancy: roughly normal, centered at 0.88. Context Recall: uniform-ish, centered at 0.82. Red dotted line showing gate threshold for each metric. The tails represent failure modes worth investigating.

**Notes:** "The faithfulness bimodal distribution is interesting. Most responses are highly faithful (grounded in retrieved context), but there's a tail at 0.5. When you investigate those low-faithfulness responses, you typically find that the customer had a very thin purchase history, so the model had little to ground itself in and started embellishing. The fix: add the INSUFFICIENT_DATA response path and detect when context is too thin to generate a reliable offer."

---

## Slide 9 — Calibration: The Forgotten Evaluation Dimension
**Layout:** Model calibration explanation with NorthStar churn example

**Content:**
**Calibration: Does "70% probability" Actually Mean 70%?**

A well-calibrated model's predicted probabilities match observed frequencies. If you predict 0.70 churn probability for 1,000 customers, approximately 700 of them should actually churn.

**Why calibration matters for NorthStar:**
The churn model output (probability score) is used to set retention intervention thresholds:
- Score ≥ 0.80: High-priority outreach (10% discount offer, personal call)
- Score 0.60-0.79: Medium-priority (email with 5% offer)
- Score < 0.60: Low-priority (newsletter only)

If the model is poorly calibrated:
- Systematic overconfidence: predicts 0.80 but 50% churn rate → wasting high-priority budget on medium-risk customers
- Systematic underconfidence: predicts 0.40 but 80% churn rate → missing the most at-risk customers with low-priority intervention

**Calibration evaluation:**
```python
from sklearn.calibration import calibration_curve
import matplotlib.pyplot as plt

# Compute calibration on held-out test set
fraction_of_positives, mean_predicted_value = calibration_curve(
    y_true=y_test, 
    y_prob=y_pred_proba, 
    n_bins=10
)

# Brier score: lower is better; 0.25 = random; 0 = perfect
brier_score = brier_score_loss(y_test, y_pred_proba)
print(f"Brier Score: {brier_score:.4f}")  # NorthStar target: < 0.20

# Calibration error (Expected Calibration Error)
ece = np.mean(np.abs(fraction_of_positives - mean_predicted_value))
print(f"ECE: {ece:.4f}")  # NorthStar target: < 0.05
```

**Fix for poor calibration:** Platt scaling or isotonic regression applied as a post-processing step after XGBoost training.

**Figure:** *Calibration curve diagram.* X-axis: mean predicted probability (0 to 1). Y-axis: fraction of positives (0 to 1). Diagonal line: perfect calibration. NorthStar churn model curve: mostly tracks the diagonal, with slight overconfidence in the 0.7-0.9 range (the curve bends below the diagonal). Shaded region: ECE = 0.034, shown graphically as the area between the curve and the diagonal. "Acceptable calibration" label.

**Notes:** "Calibration is commonly ignored in competition ML (Kaggle leaderboards don't show Brier scores) but essential in business ML. If your business stakeholders are making intervention decisions based on your probability scores, those scores must be calibrated. A 0.70 churn probability score that actually corresponds to a 40% churn rate will cause your intervention strategy to fail — and it will be attributed to bad AI, not to poor calibration."

---

## Slide 10 — Evaluation Report: The AISDLC Stage 6 Artifact
**Layout:** Evaluation report template and requirements

**Content:**
**The Evaluation Report: Stage 6 Gate Artifact**

The evaluation report documents the evidence for a deployment decision. It answers the question: "Why does this model deserve to go to production?"

**NorthStar Churn Model Evaluation Report Structure:**
```markdown
# NorthStar Churn Model v3.0 — Evaluation Report
Date: 2026-10-15
Model: northstar-churn-v3-0
Training run: mlflow://northstar/churn-experiments/run_abc123
Dataset: features-2026-10-01 (n=180,000 customers)

## 1. Executive Summary
[2-3 sentence summary: model performance, whether gate passed, deployment recommendation]

## 2. Performance vs. Gate Criteria
| Metric | Threshold | Actual | Status |
|--------|-----------|--------|--------|
| AUC | ≥ 0.72 | 0.741 | ✅ PASS |
| Recall@0.4-precision | ≥ 0.75 | 0.783 | ✅ PASS |
| Beat v2.3 by ≥ 2% | +2% | +3.1% | ✅ PASS |
| No segment AUC < 0.60 | All ≥ 0.60 | Min: 0.63 | ✅ PASS |

## 3. Segment Performance
[Segment AUC bar chart + table]

## 4. Calibration Analysis
[Calibration curve + Brier score]

## 5. Feature Importance
[Top 10 SHAP values + direction]

## 6. Failure Mode Analysis
[Examples of high-confidence incorrect predictions with analysis]

## 7. Deployment Recommendation
[APPROVED / HOLD / REJECT with reasoning]
```

**Figure:** *Evaluation report cover page mockup.* Document cover page: NorthStar logo, "Churn Model v3.0 Evaluation Report," date, model ID, "DEPLOYMENT APPROVED — Gate Passed: 4/4 criteria" in green at the bottom. Professional, clean design communicating this is a formal artifact, not an ad hoc analysis.

**Notes:** "The evaluation report is a required Lab 4 deliverable. It's also the artifact that you'd present to a risk committee or AI governance board before a major production deployment. Get into the habit of writing evaluation reports that stand alone — a person who didn't see the model training should be able to read this report and understand why the model is or isn't ready for production."

---

## Slide 11 — Online Evaluation vs. Offline Evaluation
**Layout:** Online vs. offline evaluation comparison with NorthStar examples

**Content:**
**Two Evaluation Modes:**

**Offline Evaluation (pre-deployment):**
- Uses held-out historical data
- Fast to compute (no live traffic required)
- Measures: how would this model have performed on past data?
- Limitation: doesn't capture distribution shift from current production data; can't measure downstream business outcomes
- NorthStar examples: AUC on holdout set; RAGAS on curated test set; agent simulation tests

**Online Evaluation (post-deployment):**
- Uses real production traffic
- Delayed: business outcomes (actual churn) take weeks to manifest
- Measures: how is this model actually performing on real users today?
- Advantage: captures the true distribution; captures downstream business impact
- NorthStar examples: actual churn rate in intervention cohort vs. control; CSAT on offer responses; agent resolution rate

**The Evaluation Sequence for NorthStar Deployments:**
1. **Offline eval:** Must pass gate criteria (AUC ≥ 0.72, RAGAS ≥ 0.95, etc.)
2. **Shadow mode (7 days):** Challenger runs alongside production; compare prediction distributions
3. **A/B test (4 weeks):** 20% traffic to challenger; compare online metrics
4. **Full rollout:** Promote challenger to 100% if A/B results confirm offline performance

**Figure:** *Evaluation sequence timeline.* Horizontal timeline with four phases (Offline, Shadow, A/B, Full). Each phase: duration, what's measured, who can stop it, and what "success" looks like. Phases connected by gates: "Offline gate passed → enter Shadow," "Shadow comparison passed → enter A/B," "A/B results significant → Full rollout." The sequence shows: deployment is a process, not an event.

**Notes:** "The 4-week A/B test for churn is a real constraint. Churn is defined as 'no purchase in 90 days' — so you can't measure actual churn rate in a week. You need the A/B test window to be long enough to see behavioral differences between the control and challenger populations. This is why the NorthStar churn model rollout takes 5+ weeks from training completion to full deployment."

---

## Slide 12 — Lab 4 Walkthrough: Building the Evaluation Gate
**Layout:** Step-by-step Lab 4 evaluation gate implementation

**Content:**
**Lab 4: Implementing the Evaluation Gate**

The evaluation gate in Lab 4 is a SageMaker ConditionStep that:
1. Runs the evaluation script after training
2. Reads AUC metric from evaluation output
3. Compares to threshold (0.72)
4. Proceeds to Model Registry registration if the gate passes
5. Fails the pipeline with an alert if the gate fails

**Key files in Lab 4 starter code:**

**`training/evaluate.py`** — Your evaluation script (you write this):
```python
import argparse, json, joblib, numpy as np
from sklearn.metrics import roc_auc_score

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model-dir', type=str)
    parser.add_argument('--test-data-dir', type=str)
    parser.add_argument('--output-dir', type=str)
    args = parser.parse_args()
    
    # Load model and test data
    model = joblib.load(f"{args.model_dir}/model.joblib")
    X_test = np.load(f"{args.test_data_dir}/X_test.npy")
    y_test = np.load(f"{args.test_data_dir}/y_test.npy")
    
    # Evaluate
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, y_pred_proba)
    
    # Write evaluation output (read by ConditionStep)
    metrics = {"auc": auc, "threshold": 0.72, "gate_passed": auc >= 0.72}
    with open(f"{args.output_dir}/evaluation.json", "w") as f:
        json.dump(metrics, f)
    
    print(f"AUC: {auc:.4f} | Gate: {'PASS ✅' if auc >= 0.72 else 'FAIL ❌'}")

if __name__ == '__main__':
    main()
```

**`pipeline.py`** — The ConditionStep (starter code provided, you configure it):
```python
from sagemaker.workflow.conditions import ConditionGreaterThanOrEqualTo
from sagemaker.workflow.condition_step import ConditionStep
from sagemaker.workflow.functions import JsonGet

auc_score = JsonGet(step_name="EvaluateModel", 
                    property_file=evaluation_report,
                    json_path="auc")

gate_step = ConditionStep(
    name="CheckGateCriteria",
    conditions=[ConditionGreaterThanOrEqualTo(left=auc_score, right=0.72)],
    if_steps=[register_step],
    else_steps=[fail_step]
)
```

**Figure:** *Lab 4 evaluation gate flowchart.* Three boxes: TrainingStep → EvaluateModel (your evaluate.py script) → ConditionStep (AUC ≥ 0.72?). Two branches: YES → RegisterModel (green box). NO → FailPipeline + CloudWatch Alert (red box). The code on this slide is what creates the flowchart.

**Notes:** "The `JsonGet` function is the key connector — it reads the AUC value from the `evaluation.json` file written by your `evaluate.py` script and passes it to the ConditionStep comparison. Make sure your `evaluate.py` writes the metric key exactly as `'auc'` — the ConditionStep JSON path must match."

---

## Slide 13 — Common Evaluation Mistakes
**Layout:** Five evaluation mistakes with NorthStar-specific examples

**Content:**
**Evaluation Mistakes That Lead to Failed Deployments:**

1. **Test set contamination (data leakage):**
   Splitting data after feature engineering (especially time-series features) can leak future information into the training set. Always split by time first, then engineer features within each split.

2. **Wrong evaluation metric for the business problem:**
   Using accuracy for an imbalanced churn dataset (88% majority class) gives misleading results. The right metric for churn is AUC-ROC (rank-ordering quality), plus precision/recall at the intervention threshold.

3. **Single-split evaluation:**
   Evaluating on a single holdout set can give high-variance results. For NorthStar, use 3-fold time-series cross-validation (each fold uses an earlier time period for training and the next period for validation).

4. **Ignoring the deployment distribution:**
   Evaluating on historical data from 2 years ago when the deployment will score customers from today. Customer behavior changes; evaluate using recent data (at most the last 6 months for NorthStar).

5. **No baseline comparison:**
   Evaluating in isolation — "AUC is 0.74" — without comparing to: a) the current production model, b) a simple rule-based baseline (e.g., "predict churn if no purchase in 60 days"). A model that beats the gate but doesn't beat a simple rule isn't worth deploying.

**Figure:** *Five-mistake checklist.* Same checklist format. Mistake 5 (no baseline) shows a mini comparison: NorthStar rule-based baseline AUC = 0.69; XGBoost v3.0 AUC = 0.74. "+5% over baseline" shown — this is the meaningful comparison. Without it, 0.74 AUC sounds good, but the context is missing.

**Notes:** "Mistake 1 — test set contamination — is the silent killer of student ML projects. You engineer RFM features on the full dataset, then split into train/test. But the recency feature for the test set was computed using the test set's purchase dates — which includes purchases that occurred after the split date. The model learned from the future. Fix: always split first, then engineer."

---

## Slide 14 — Lab 4 Spec Review: What's Expected
**Layout:** Lab 4 deliverables and grading breakdown

**Content:**
**Lab 4: CI/CD Pipeline — Due Saturday, October 31**

**What you're building:**
1. SageMaker Pipeline with 5 steps: PrepareFeatures → Train → Evaluate → Gate → Register
2. CI/CD via CodePipeline: GitHub push → CodeBuild (test runner) → SageMaker Pipeline trigger → conditional deployment
3. Test suite (from L12/L13 template): unit tests + integration tests + evaluation gate
4. Evaluation report: structured documentation of model performance and deployment decision
5. Architecture Decision Record (ADR): why this CI/CD architecture; alternatives considered

**Grading breakdown:**
| Component | Weight | Key Criteria |
|-----------|--------|-------------|
| SageMaker Pipeline (functional) | 30% | All 5 steps run; ConditionStep correctly gates |
| CodePipeline integration | 30% | GitHub push triggers full pipeline automatically |
| Test suite | 20% | Required tests present, passing, run in CodeBuild |
| Evaluation report | 10% | Complete template, correct metrics, clear recommendation |
| ADR | 10% | Clear rationale, alternatives considered |

**Common Lab 4 failure modes (historical):**
- IAM permissions: CodePipeline role needs permission to trigger SageMaker Pipeline
- ConditionStep JSON path mismatch: `evaluate.py` writes key A, ConditionStep reads key B
- CodeBuild environment: test imports fail because package not in requirements.txt
- Missing evaluation report: submitted code but not the documentation

**Figure:** *Lab 4 component dependency diagram.* Five components arranged in a flow. Each component: name, weight %, and 1-sentence description. Arrows showing dependencies: "Pipeline must work before CodePipeline can trigger it"; "Test suite must pass before pipeline runs"; "Evaluation report documents the gate result." Common failure modes highlighted in amber boxes next to the relevant component.

**Notes:** "The IAM permissions issue is the most common source of Lab 4 debugging time. CodePipeline needs a role that allows it to call `sagemaker:StartPipelineExecution`. The Lab 4 Terraform template includes this role definition — use it. If you've manually created your roles without Terraform, check that `sagemaker:StartPipelineExecution` is in your CodePipeline execution role."

---

## Slide 15 — Evaluation in the AISDLC: Where It Fits
**Layout:** AISDLC evaluation stages recap with deployment connection

**Content:**
**Evaluation Appears at Multiple AISDLC Stages:**

**Stage 1 — Define Problem:** Define success criteria (which metrics and thresholds). This is where gate criteria originate. Skip this, and you'll argue about metrics at Stage 6.

**Stage 2 — Discover Data:** Evaluate data quality (completeness, distribution, relevance). This is the first evaluation gate — before any model development.

**Stage 5 — Develop:** Continuous evaluation during development (MLflow experiment comparison). Not a gate — just tracking learning progress.

**Stage 6 — Evaluate:** Formal evaluation against Stage 1 success criteria. The deployment gate. The evaluation report. This is today's lecture applied.

**Stage 7 — Deploy:** Evaluation continues: shadow mode, A/B test, endpoint smoke test.

**Stage 8 — Monitor:** Evaluation never stops: drift monitoring, continuous quality evaluation, HITL review, CSAT.

**Key insight:** Evaluation is not a single event before deployment — it's a discipline that runs continuously from problem definition through the system's full operational lifetime.

**Figure:** *AISDLC evaluation touchpoints diagram.* 8-stage AISDLC pipeline with evaluation icons overlaid on Stages 1, 2, 5, 6, 7, 8. Stage 6 highlighted as "primary evaluation gate." Stages 7 and 8 connected with a circular arrow showing "continuous evaluation loop." The visual communicates: evaluation is woven throughout the full lifecycle.

**Notes:** "The Stage 1 connection is the most important and most commonly violated. Teams often define their evaluation criteria after the model is built — 'let's see what AUC we got and call that the threshold.' That's backward. The threshold must come from the business requirement, defined at Stage 1, before you know what your model can achieve. Otherwise, you're just validating what you already built, not whether it's good enough."

---

## Slide 16 — Key Takeaways + Lab 4 Launch
**Layout:** Takeaways + Lab 4 kickoff

**Content:**
**Key Takeaways:**
1. Evaluation frameworks have three components: metrics, thresholds (derived from business requirements), and decision logic — design all three before training begins
2. Segmented evaluation is non-optional: average performance hides failure modes in specific customer populations that may be the most business-critical
3. A/B testing for ML requires: consistent customer-level split, long enough evaluation window to observe outcomes, and sufficient sample size from power analysis
4. The evaluation report is a formal artifact: it documents the evidence for deployment; it must be reproducible and stand alone
5. Evaluation never stops: offline evaluation gates deployment; online evaluation runs continuously in production; HITL catches what automated metrics miss

**Lab 4 — Assigned Today:**
- **What:** CI/CD pipeline for NorthStar Churn Model
- **Due:** Saturday, October 31 (16 days)
- **Support:** Office hours Mon/Tue/Wed this week and next; extended on Oct 28-30
- **Start with:** SageMaker Pipeline (the core artifact); get the pipeline running before building CodePipeline around it

**Next Session (Tue Oct 20):**
- Topic: Continuous Delivery I — deployment patterns; canary releases; rollback strategies
- Reading due: *Continuous Delivery for AI* — "Introduction" through "Deployment Patterns"

**Figure:** *Lab 4 launch card.* Bright teal box: "Lab 4: CI/CD Pipeline" with due date, spec location, and three starter steps: 1) Read the spec tonight, 2) Get the SageMaker Pipeline running first, 3) Attend office hours if blocked. Key takeaways numbered list alongside. Professional, clear, actionable.

**Notes:** "Lab 4 kickoff advice: don't try to build everything at once. The dependency chain is: SageMaker Pipeline → CodePipeline → test suite. Get the SageMaker Pipeline running independently first (you can trigger it manually via the console or CLI). Only then connect CodePipeline to trigger it automatically. Trying to debug both layers simultaneously is exponentially harder than debugging each layer separately."
