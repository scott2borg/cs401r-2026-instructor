---
tags: [CS401R, lab-solution, lab-4, sample-deliverable, xops, cicd, maturity]
course: CS 401R
lab: 4
status: sample-deliverable
source: rescued from the retired Sample Solutions/northstar-ai-platform tree, 2026-08-07
---

> **Worked sample deliverable — not a grading guide.** This is an example of what a
> strong Lab 4 submission looks like. The TA grading rubric lives in the companion
> file `Lab 4 - … (Solution).md`. For instructor use; not distributed to students.

# NorthStar Retail — XOps Maturity Assessment
**Lab 4 | CS 401R | Assessed against the five-level NorthStar XOps rubric**

---

## DataOps Maturity

**Current level: 2 (Repeatable)**

### Evidence

- Automated nightly Glue ETL job (`data/ingestion/batch_ingestion.py`) orchestrated by an EventBridge rule — no manual data prep steps.
- Schema validation and quality checks gate the pipeline before writing to `northstar-processed/`. Records that fail schema validation are written to the quarantine prefix with structured CloudWatch logging; they are not silently dropped.
- Data contract documented in `docs/lab2-data-contract.md` with numeric SLAs (e.g., null rate < 2% on `days_since_last_purchase`, store_id conformance to `STORE-NNN|ONLINE` pattern).
- All pipeline stages are committed to version control. No ad-hoc SQL or notebook-based transformations exist in the production path.
- Rejected-record counts are surfaced as CloudWatch custom metrics under `NorthStar/DataQuality`, making daily quality trends observable.

### Gap to Level 3 (Defined)

- **Missing:** Automated SLA breach alerting. Currently, a human must inspect CloudWatch dashboards to detect that a quality threshold has been crossed. The metrics exist; alarms do not.
- **Missing:** Formal data lineage tracking. The Mermaid diagram in `docs/lab2-data-contract.md` describes intended lineage, but no tool (e.g., AWS Glue Data Catalog lineage, OpenLineage) tracks actual lineage at runtime.
- **Missing:** Data quality scoring dashboard visible to business stakeholders. Engineers can see CloudWatch; non-engineers cannot.

### Top Priority Investment

Wire the existing CloudWatch quality metrics into SNS alarms with email notification to the on-call data engineer. Estimated effort: 2 days.

Concrete impact: breach detection time drops from "someone checks the dashboard on Monday" to "on-call is paged within 5 minutes of the nightly job completion." This single change closes the largest operational risk on the DataOps dimension without requiring new infrastructure.

---

## MLOps Maturity

**Current level: 2 (Repeatable)**

### Evidence

- SageMaker Pipeline (`pipeline/sagemaker_pipeline.py`) automates training end-to-end: feature extraction from Feature Store → XGBoost training → model evaluation → conditional registration.
- CI/CD pipeline (CodePipeline + CodeBuild, `pipeline/cicd/`) triggers on every push to `main`. Every model candidate must pass 4 test categories before promotion is possible.
- Model Registry (`northstar-churn-model-group`) captures every model version with AUC-ROC, Precision@10, Recall@10, training data URI, and commit SHA as metadata. Models start in `PendingManualApproval` and require both automated gate passage and a human approval step.
- Champion-challenger regression gate: a new model is promoted only if its AUC-ROC is >= (champion AUC − 0.02), enforced in `tests/test_model.py::TestRegressionGate`.
- Experiment tracking: a SageMaker **MLflow App** logs >= 3 hyperparameter runs per training cycle, making hyperparameter search reproducible and auditable. (Updated 2026-08-07: this was SageMaker Experiments, whose SDK tracking is Studio-Classic-only; the course moved to the serverless MLflow App.)
- Two retraining triggers are defined (see Retraining Triggers section below).

### Gap to Level 3 (Defined)

- **Missing:** Automated A/B test framework. Champion-challenger comparison currently happens offline (metrics comparison). No live traffic split between champion and challenger exists; a human decides based on offline metrics alone.
- **Missing:** Feature drift detection as a CI gate. PSI (Population Stability Index) is not computed before training, meaning the pipeline can train on drifted features without warning.

### Top Priority Investment

Add a PSI check on the top-3 features (`days_since_last_purchase`, `purchase_frequency_90d`, `avg_basket_size_6m`) as a CI gate in `tests/test_data.py`. If PSI > 0.2 on any of these features relative to the training baseline distribution, fail the build and require a data investigation before training proceeds. Estimated effort: 1 day.

Concrete impact: prevents training a new model on a feature distribution that has shifted significantly from the distribution the champion was trained on, which is the most common silent failure mode in production ML systems.

---

## Champion-Challenger Criterion

A new model is "better enough" to replace the champion when:

> **New model AUC-ROC >= Champion AUC-ROC + 0.005**

This requires a positive improvement of at least 0.5 percentage points, not merely "not regressing." The rationale: a pipeline that accepts lateral moves will silently plateau over time as teams optimize metrics that don't translate to real improvement. Requiring a positive delta ensures every promoted model is demonstrably better.

The criterion is evaluated automatically in the CI regression gate (`TestRegressionGate.test_new_model_doesnt_regress_from_champion`). The champion AUC is retrieved from SageMaker Model Registry metadata (`CustomerMetadataProperties.auc_roc`) at test time, so the gate always compares against the current production model.

---

## Retraining Triggers

**Trigger 1 — Scheduled:** An EventBridge rule fires every Sunday at 02:00 UTC, triggering a new CodePipeline execution. This ensures the model is retrained at least weekly regardless of code changes, incorporating the most recent customer behavior data.

**Trigger 2 — Performance-based:** A CloudWatch Alarm monitors the `NorthStar/Model/AUCProxy` metric published by the post-build phase of each CodeBuild run. When the metric drops below **0.68** for 2 consecutive evaluation periods (14 days), the alarm publishes to the `northstar-pipeline-notifications` SNS topic, which triggers a new CodePipeline execution. This catches cases where model performance degrades between scheduled retrains — for example, due to a sudden shift in customer behavior following a major promotion or a competitor event.
