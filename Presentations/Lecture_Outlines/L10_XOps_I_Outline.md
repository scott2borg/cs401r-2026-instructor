---
lecture: L10
title: XOps I — DataOps & MLOps
date: Tuesday, October 6, 2026
week: 6
arc: Build
reading_due: "The XOps Stack — Motivation through MLOps"
lab_due: "Lab 3 due Sat Oct 17"
slides_target: 15
---

# L10: XOps I — DataOps & MLOps
**Tuesday, October 6, 2026 | CS 401R: Engineering Production AI Systems | Fall 2026**

> XOps as the operational foundation of enterprise AI. DataOps: building a reliable data foundation. MLOps: automating the model lifecycle. Where most teams fall short and why. NorthStar XOps assessment.

**Reading Due:** *The XOps Stack* — "Motivation" through "MLOps"

---

## Slide 1 — Title
**Layout:** Left dark panel + right XOps stack diagram

**Content:**
- XOps I: DataOps & MLOps
- CS 401R · Lecture 10 · Tuesday, October 6, 2026
- The Operational Foundation of Enterprise AI

**Figure:** *XOps stack diagram.* Vertical stack of four layers: DataOps (foundation, wide), MLOps (second layer), LLMOps (third layer), AgentOps (top, narrow). Each layer has: a name, a 2-word subtitle, and icons representing key tools/services. Color gradient from deep blue (bottom) to bright teal (top). The stack communicates: XOps is layered, each layer builds on the one below, and DataOps is the non-negotiable foundation.

**Notes:** "XOps is not a single thing. It's a family of operational disciplines, each addressing a different layer of the AI system stack. Today we cover DataOps and MLOps — the foundation. Thursday we cover LLMOps and AgentOps — the emerging layers."

---

## Slide 2 — What Is XOps and Why It Matters
**Layout:** Definition + the cost of XOps gaps

**Content:**
**XOps = the 'Ops' disciplines for AI systems:**
- **DataOps:** Operational discipline for data pipelines — reliability, quality, observability
- **MLOps:** Operational discipline for model lifecycle — training automation, deployment, monitoring
- **LLMOps:** Operational discipline for foundation model systems — prompt management, evaluation, guardrails
- **AgentOps:** Operational discipline for autonomous agents — trace monitoring, authority enforcement, incident response

**Why XOps gaps are expensive:**
- Without DataOps: pipeline failures discovered days after they occur; model retraining on corrupted data
- Without MLOps: manual model deployments take weeks; no rollback; no monitoring; model quality drifts silently
- Combined cost: Gartner estimates that XOps gaps cost enterprises 40-60% of potential AI ROI through unreliable systems and manual overhead

**The XOps maturity gap:** 70% of organizations have deployed AI models to production; fewer than 30% have automated the model lifecycle (source: Databricks State of Data + AI, 2024)

**Figure:** *XOps maturity gap visualization.* Horizontal bar chart with three pairs: "Have data pipelines" vs. "Have DataOps practices" (gap: 55%), "Have ML models in production" vs. "Have automated ML lifecycle" (gap: 40%), "Have LLM deployments" vs. "Have LLMOps in place" (gap: 65%). Bars color-coded: deployed (blue), with XOps (teal). The gaps are visually prominent and striking.

**Notes:** "The XOps maturity gap is the operational gap the course is designed to close. Your Lab 4 (CI/CD) and Lab 6 (monitoring) are XOps labs. They're the difference between an AI system that runs reliably for 18 months and one that silently degrades and has to be rebuilt from scratch after 6 months."

---

## Slide 3 — DataOps: Principles and Architecture
**Layout:** DataOps principles with NorthStar implementation

**Content:**
**DataOps Principles (adapted from DataKitchen):**

1. **Pipeline orchestration:** All data transformations are automated, scheduled, and monitored. No manual steps in the production path.

2. **Data quality gates:** Automated quality checks at every pipeline boundary. Violations halt the pipeline before bad data propagates downstream.

3. **Observability:** Pipeline health is visible in real time. Failures alert. Latency tracked. Volume trends monitored.

4. **Version control:** All pipeline code in Git. All data assets versioned (or at least lineage-tracked). Reproducible from commit.

5. **Testing:** Unit tests for transformation functions. Integration tests for end-to-end pipeline runs. Contract tests at every data boundary.

6. **Environment parity:** Dev, staging, and production pipelines use identical code. "Works in dev" means "works in production."

**NorthStar DataOps maturity (after Lab 2):**
- Orchestration: ✅ Glue scheduled jobs
- Quality gates: ✅ CloudWatch metrics + alerts
- Observability: ✅ CloudWatch dashboards
- Version control: ✅ All Glue job code in Git
- Testing: ⚠️ Unit tests required; integration tests partial
- Environment parity: ⚠️ Dev environment only in this course

**Figure:** *DataOps maturity scorecard.* Six principal rows with traffic-light status (green/amber/red) and NorthStar assessment. Two columns: "After Lab 2" and "Production standard." Makes clear where NorthStar labs bring students to vs. full production maturity. Motivates Labs 4 and 6 as the gaps to close.

**Notes:** "Environment parity is the DataOps principle most commonly violated in student labs. You test the Glue job in your dev account; it works. You submit, and the TA clones it into their account, where it fails because of a region-specific configuration. Use Terraform variables and parameterized Glue jobs to eliminate these environment differences."

---

## Slide 4 — DataOps in Practice: Pipeline Orchestration
**Layout:** Orchestration architecture with scheduling and dependency management

**Content:**
**The Pipeline Orchestration Problem:**
Glue jobs have dependencies. The feature engineering job can only run after the ETL job completes. The training job can only run after feature engineering. Manual triggering is error-prone and doesn't scale.

**NorthStar Pipeline Orchestration Stack:**
- **AWS Glue Workflows:** Chain Glue jobs with dependencies; trigger on schedule or on data arrival
- **Amazon EventBridge:** Event-driven triggers (S3 put event → trigger Glue workflow)
- **AWS Step Functions:** Complex orchestration with conditionals, parallel branches, error handling (used in Lab 4 CI/CD)

**Orchestration design for NorthStar:**
```
Daily at 2:00 AM UTC:
  1. Ingest: s3_sync_customer_data (15 min)
  2. Ingest: s3_sync_transaction_data (20 min)
  ↓ on both complete:
  3. ETL: customer_feature_extraction (30 min)
  4. ETL: transaction_aggregation (45 min)
  ↓ on both complete:
  5. Feature Store: ingest_features (20 min)
  ↓ on complete:
  6. Trigger: model training pipeline (if data quality gates pass)
```

**Figure:** *Glue Workflow DAG diagram.* Directed acyclic graph showing the 6-step NorthStar pipeline with dependencies. Steps 1-2 at the top (parallel); Steps 3-4 below (parallel, each depending on both Step 1 and Step 2); Step 5 below (depends on both 3 and 4); Step 6 at the bottom (depends on Step 5). Each node: step number, job name, estimated runtime. Edges: dependency arrows. Color: completed steps in green, running steps in gold, pending steps in gray. This is the Glue Workflow visualization.

**Notes:** "The 2:00 AM UTC schedule is deliberate — it runs while the US is asleep, so the features are ready for the morning's churn predictions without impacting daytime system performance. If the pipeline fails at 2:00 AM, the monitoring alert fires, the on-call engineer investigates, and the morning's predictions use yesterday's features (which is acceptable — churn doesn't change overnight)."

---

## Slide 5 — MLOps: The Model Lifecycle Automation Stack
**Layout:** MLOps component diagram with automation levels

**Content:**
**What MLOps Automates:**

**Level 1 — Manual MLOps (where most teams start):**
- Data preparation: manual scripts
- Training: notebook runs manually
- Evaluation: eyeball the metrics
- Deployment: copy model files to production
- Monitoring: hope it keeps working

**Level 2 — Automated Training Pipeline:**
- Automated: data prep → training → evaluation → registry registration
- Deployment: still manual (one-click, but manual)
- Monitoring: basic metrics dashboard
- NorthStar target: Lab 4 achieves this level

**Level 3 — Full CI/CD for ML:**
- Triggered: by new data, scheduled, or by code change
- Automated: train → evaluate → gate check → deploy → validate
- Monitoring: automated alerting + retraining triggers
- Production standard for mature ML organizations

**Level 4 — Self-Optimizing:**
- Continuous online learning or automated retraining with A/B testing
- Very few organizations have reached this level

**Figure:** *MLOps maturity staircase.* Four steps (Level 1-4), each labeled, with representative architecture diagram at each level. Level 1: simple notebook. Level 2: pipeline diagram with human deployment step. Level 3: full CI/CD pipeline without human steps. Level 4: feedback loop with online learning. NorthStar course target circled at Level 2→3 transition. "Industry standard" marker at Level 3.

**Notes:** "Lab 4 takes NorthStar from Level 1 (the Lab 3 state — you trained manually in a notebook/SageMaker job) to Level 2-3 (CI/CD pipeline that automatically trains, evaluates, and registers when triggered). That's a significant jump. Most enterprise organizations are in the Level 1-2 range."

---

## Slide 6 — SageMaker Pipelines: MLOps Automation Engine
**Layout:** Pipeline definition with step types and NorthStar configuration

**Content:**
**SageMaker Pipelines for NorthStar Churn Model:**
```python
pipeline = Pipeline(
    name="northstar-churn-training-pipeline",
    steps=[
        ProcessingStep(      # Step 1: Feature preparation
            name="PrepareFeatures",
            processor=SKLearnProcessor(...),
            inputs=[feature_store_input],
            outputs=[training_data_output, validation_data_output]
        ),
        TrainingStep(        # Step 2: XGBoost training
            name="TrainChurnModel",
            estimator=XGBoost(...),
            inputs={"train": training_data, "validation": validation_data}
        ),
        ProcessingStep(      # Step 3: Evaluate and check gate
            name="EvaluateModel",
            processor=ScriptProcessor(...),
            code="evaluate.py",  # checks AUC ≥ 0.72
            inputs=[training_step.properties.ModelArtifacts]
        ),
        ConditionStep(       # Step 4: Gate — proceed only if criteria met
            name="CheckGateCriteria",
            conditions=[ConditionGreaterThanOrEqualTo(
                left=auc_metric, right=0.72
            )],
            if_steps=[register_step],     # Gate passed → register
            else_steps=[fail_step]        # Gate failed → alert
        ),
        ModelStep(           # Step 5: Register in Model Registry
            name="RegisterModel",
            model=Model(image_uri=..., model_data=...)
        )
    ]
)
```

**Figure:** *SageMaker Pipeline DAG.* Visual representation of the pipeline above. Five step boxes connected by arrows. Condition step (Step 4) has a diamond shape showing the if/else branch. The "else" branch goes to a "Fail + Alert" box in red. The "if" branch goes to the "Register Model" box in green. Each step box shows the step name, step type, and runtime estimate. This pipeline is the Lab 4 deliverable.

**Notes:** "This is the pipeline you'll build in Lab 4. It's the ML equivalent of a CI/CD pipeline: triggered by new data or code changes, it automatically trains, evaluates, checks the gate, and registers the model. No human intervention required in the happy path. The gate check in Step 4 is the AISDLC Stage 6 gate — implemented as code."

---

## Slide 7 — MLOps Monitoring: The Feedback Loop
**Layout:** Monitoring-to-retraining feedback loop diagram

**Content:**
**The MLOps Monitoring Loop:**

1. Model deployed to SageMaker endpoint
2. SageMaker Model Monitor running: capturing prediction distributions, comparing to training baseline
3. Drift detected (data drift or model quality drift)
4. Alarm fires: CloudWatch → SNS → email/Slack
5. Decision: auto-retrain (if drift is within expected parameters) or alert for human review
6. Retraining triggered: SageMaker Pipeline runs automatically
7. New model evaluated against gate criteria
8. If passes: auto-deployed to endpoint (canary first, then full traffic)
9. Loop continues

**NorthStar retraining triggers:**
- Scheduled: monthly (baseline refresh)
- Drift-triggered: PSI score > 0.2 on any feature distribution
- Performance-triggered: AUC drops below 0.68 (10% below gate threshold)

**Figure:** *Feedback loop diagram.* Circular flow connecting: Production Endpoint → Model Monitor → Drift Detection → Alert → Retraining Decision → SageMaker Pipeline → New Model → Evaluation Gate → Endpoint (if passes). At the Alert node: two exit paths (auto-retrain vs. human review). At the Evaluation Gate: two paths (deploy if passes, investigate if fails). Arrows form a closed loop, communicating: this is an ongoing operational system, not a one-time deployment.

**Notes:** "The retraining trigger is where MLOps becomes genuinely operational. Without it, your model degradation is a manual discovery process. With it, the system detects drift, triggers retraining, and deploys the new model — all without human intervention. This is the automation that separates organizations at MLOps Level 3 from those at Level 2."

---

## Slide 8 — Experiment Tracking at Scale: MLflow Governance
**Layout:** MLflow governance patterns for teams

**Content:**
**The Experiment Tracking Problem at Team Scale:**
Single engineer: MLflow experiments in personal workspace; no structure needed.
Team of 10: 1,000+ experiments per month; experiments are duplicated; nobody knows which model is "the good one."

**MLflow Governance Practices:**

**Naming conventions:**
```
Experiment name: {system}-{version}-{date}-{team}
Example: churn-v3-2026-10-06-ml-team
```

**Tagging requirements (enforced at training job level):**
- `git_commit`: the exact code version that produced this run
- `data_version`: Feature Group version + ingest timestamp
- `run_purpose`: exploration | tuning | validation | production-candidate
- `owner`: who ran this experiment

**Promotion workflow:**
1. Exploration runs: any team member, free-form
2. Tuning runs: tagged `run_purpose=tuning`; parent experiment tracks hyperparameter sweep
3. Production candidate: single run tagged `run_purpose=production-candidate`; linked to Model Registry

**Figure:** *MLflow governance hierarchy diagram.* Three-level pyramid: Exploration (wide base, many runs, free-form), Tuning (middle, systematic, tagged), Production Candidate (narrow top, single run, registered). Each level has: access control (who can run), tagging requirements, and artifact requirements. A "Production Path" arrow shows which runs are eligible for Model Registry registration.

**Notes:** "Without MLflow governance, your experiment history is noise. With it, your experiment history is a decision log — you can trace every production model back to the experiments that informed the choice. This becomes important when a model fails in production and you need to understand whether the training process was sound."

---

## Slide 9 — The NorthStar XOps Assessment
**Layout:** Capability assessment across DataOps and MLOps dimensions

**Content:**
**NorthStar XOps Capability Assessment (after Labs 1-3, before Lab 4):**

| Capability | Status | Lab that Addresses |
|-----------|--------|-------------------|
| Data pipeline automation | ✅ Glue scheduled jobs | Lab 2 |
| Data quality gates | ✅ CloudWatch alerts | Lab 2 |
| Feature Store with versioning | ✅ SageMaker Feature Store | Lab 2 |
| Experiment tracking | ✅ MLflow | Lab 3 |
| Model registry | ✅ Model Registry (manual registration) | Lab 3 |
| Automated training pipeline | ❌ Manual SageMaker jobs | Lab 4 |
| CI/CD for model deployment | ❌ No automation | Lab 4 |
| Automated deployment | ❌ No canary/rollback | Lab 5 |
| Production monitoring | ❌ No drift detection | Lab 6 |
| Cost governance | ⚠️ Budget alerts only | Lab 7 |

**XOps Maturity Score: 5/10 (after Labs 1-3)**

**Figure:** *XOps assessment radar chart.* Radar/spider chart with 10 dimensions (one per capability in the table). Each dimension scored 0-4: 0=none, 1=manual, 2=partial, 3=automated, 4=optimized. After Labs 1-3: irregular polygon showing high scores on data capabilities (3-4), low on CI/CD and monitoring (0-1). After Labs 1-7: nearly full polygon, approaching Level 3 on all dimensions. Both states shown on the same chart: "before" in light blue, "after" in navy.

**Notes:** "This radar chart is the visual summary of what the lab sequence builds. After Labs 1-3, you have a capable data and model foundation but no operational automation. After Labs 4-7, you have a production-grade AI system with full CI/CD, monitoring, cost governance, and business value measurement. Each remaining lab closes a specific gap on this chart."

---

## Slide 10 — DataOps Anti-Patterns: What to Avoid
**Layout:** Five DataOps anti-patterns

**Content:**
1. **The Notebook Pipeline:** Data transformations written in Jupyter notebooks and run manually for production. When the notebook author leaves, the pipeline is orphaned. Fix: Glue jobs, parameterized, in version control.

2. **No Error Handling:** ETL jobs that fail silently when a source file is missing or malformed, producing partial output that gets treated as complete. Fix: explicit error handling with CloudWatch alerts on failure.

3. **Hardcoded Paths:** S3 paths, bucket names, and environment-specific values hardcoded in ETL scripts. Fix: environment variables and Terraform outputs passed as job parameters.

4. **No Testing:** Pipeline code without unit tests. "It worked once" is not a quality standard. Fix: pytest unit tests for all transformation functions before the job is promoted to production.

5. **Manual Quality Checks:** Data quality reviews done by a human running SQL queries periodically. Fix: automated quality gate with defined thresholds; human reviews the alerts, not the raw data.

**Figure:** *Anti-pattern checklist.* Five rows, same format as previous anti-pattern slides. Red X icon for each anti-pattern; green checkmark for the fix. "Notebook Pipeline" row has a specific note: "How to detect: your pipeline runs from a .ipynb file." Practical and direct.

**Notes:** "Hardcoded paths are the most common Lab 2 grading failure. Students write their ETL job with the path to their specific S3 bucket hardcoded. The TA clones the repo, runs `terraform apply`, gets a different bucket name, runs the Glue job — it fails because the path doesn't exist. Use environment variables."

---

## Slide 11 — MLOps Anti-Patterns
**Layout:** Five MLOps anti-patterns

**Content:**
1. **Model in a Notebook:** The production model is a .pkl file saved from a Jupyter notebook, deployed by copying it to an S3 bucket and hand-configuring an endpoint. No registry, no reproducibility, no rollback. Fix: SageMaker Pipelines → Model Registry → CI/CD deployment.

2. **No Gate in the Pipeline:** Training pipeline runs, but any model gets deployed regardless of evaluation results. Fix: ConditionStep in SageMaker Pipelines; fail the pipeline if AUC < threshold.

3. **Missing Baseline Model:** New model deployed without comparison to current production model performance. Fix: always include baseline model metrics in the evaluation; the new model must beat the current production model by a defined margin (e.g., +2% AUC).

4. **Ignoring Class Imbalance:** Pipeline trained on 88% majority class, model predicts majority class for everything, accuracy is 88%. "Looks good!" No: this is a useless model. Fix: balance metrics (AUC, F1); weight the minority class appropriately.

5. **No Deployment Testing:** Model deployed to production endpoint without any validation that the endpoint actually serves predictions correctly. Fix: smoke test: after deployment, send one test request and verify the response format matches the expected schema.

**Figure:** *Five-row MLOps anti-patterns table.* Same format. "Model in a Notebook" row has a production incident counter: "Causes ~35% of ML production incidents per industry survey."

**Notes:** "The missing baseline model is the one that leads to 'the new model is better' claims that aren't true. When you deploy a new churn model, you must answer: better than what? Better than yesterday's model? Better than a rule-based baseline? Better than random? The comparison must be explicit and documented in the evaluation report."

---

## Slide 12 — Cost of Technical Debt in AI Operations
**Layout:** Technical debt accumulation diagram with financial estimates

**Content:**
**AI Operations Technical Debt: What It Costs**

**Manual deployment overhead:** A team that manually deploys models spends ~4 hours per deployment cycle (prep, test, deploy, validate, rollback-test). At 2 deployments/month × 12 months: 96 hours/year. At $150/hour engineering cost: $14,400/year per model. With 10 models: $144,000/year.

**Incident cost from lack of monitoring:** Industry average: ML production incidents detected 2.3 weeks after onset without monitoring. Average incident recovery time: 4 weeks. At $10K/week lost revenue impact for a mid-size retailer: $23K per incident. With monitoring: detected in hours, recovery in days: $2.3K. Savings: $20K per incident avoided.

**Retraining without automation:** Manual retraining takes 2-3 days of engineering time per model per quarter. Automated: 0 engineering hours (just monitoring and gate review). At 5 models: 40 engineering days/year of manual retraining work eliminated.

**Total XOps automation ROI for NorthStar (estimated):** $ 180K–$250K/year in engineering efficiency and incident avoidance across a 3-system platform.

**Figure:** *ROI waterfall chart.* Starting from "$0" at left, three positive bars: Manual Deployment Savings ($144K), Incident Cost Reduction ($80K), Retraining Automation ($40K). Final bar: Total XOps ROI ($264K). Each bar labeled with the calculation basis. Clean, credible, business-oriented.

**Notes:** "The XOps ROI argument is important for your future career. When you propose building CI/CD for your AI systems at work, you'll be asked: 'How much does this cost to build? What's the payback period?' These numbers give you a framework for that conversation. The automation pays for itself within 6-12 months for a 3-system platform."

---

## Slide 13 — Lab 4 Preview: What CI/CD for AI Looks Like
**Layout:** Lab 4 pipeline architecture preview

**Content:**
**Lab 4: CI/CD Pipeline for NorthStar Churn Model**
(Assigned: Thu Oct 15 | Due: Sat Oct 31)

**What you'll build:**
1. **SageMaker Pipeline:** Automated training pipeline (Steps from Slide 6) triggered by new data
2. **AWS CodePipeline:** CI/CD orchestration connecting GitHub → CodeBuild → SageMaker Pipeline → Model Registry → Endpoint
3. **Automated tests:** Data validation, model quality gate (AUC ≥ 0.72), inference contract test
4. **Pipeline health dashboard:** CloudWatch dashboard showing pipeline run history, pass/fail rates, latency

**The trigger:**
- Code change merged to main → CodePipeline triggers → SageMaker Pipeline runs → if gate passes → model registered
- New data available (weekly Feature Store refresh) → same pipeline triggers automatically

**Figure:** *Lab 4 CI/CD architecture overview.* Full CI/CD pipeline diagram: GitHub (code commit) → CodePipeline (orchestrator) → CodeBuild (test runner) → SageMaker Pipeline trigger → Training/Evaluation → ConditionStep (gate) → Model Registry → Canary Endpoint (Lab 5). Arrows show automation flow with no human intervention required in the happy path. "Manual approval" optional gate shown as a toggle (off by default, on for high-risk deployments).

**Notes:** "Lab 4 is the most technically complex lab in the course. It connects the most components and requires getting the trigger logic exactly right. Start early — the CodePipeline + SageMaker Pipeline integration has specific configuration requirements. Office hours during Lab 4 week will be extended."

---

## Slide 14 — The XOps Maturity Journey
**Layout:** NorthStar labs mapped to XOps maturity progression

**Content:**
**From Labs to XOps Maturity:**

| Lab | XOps Capability Added | Maturity Level |
|-----|-----------------------|---------------|
| Lab 1 | IaC foundation (Terraform) | Pre-DataOps → Level 1 |
| Lab 2 | DataOps: pipelines, quality gates, lineage | DataOps Level 1 → 2 |
| Lab 3 | MLOps: experiment tracking, registry | MLOps Level 1 → 2 |
| Lab 4 | MLOps: CI/CD, automated training + deployment | MLOps Level 2 → 3 |
| Lab 5 | MLOps: canary deployment, scaling, rollback | MLOps Level 3 |
| Lab 6 | DataOps + MLOps: drift monitoring, reliability | Level 3 operational |
| Lab 7 | FinOps + XOps: cost governance, business value | Full XOps stack |

**By Lab 7:** NorthStar platform is at MLOps Level 3 — fully automated lifecycle with monitoring, rollback, cost governance, and business value measurement.

**Figure:** *XOps maturity progression bar.* Horizontal bar divided into 7 colored segments (one per lab). Under each segment: lab number and key capability added. Above the bar: maturity level markers (Level 0 at left, Level 3 at right). A "current position" marker moves from left to right across labs. The overall visual communicates: each lab is a concrete step toward operational maturity.

**Notes:** "The semester's lab structure is itself an XOps maturity journey. You start with a blank platform (Lab 1) and add operational capability with every lab. By Lab 7, you have a system that an operations team could actually run — with monitoring, automated retraining, cost controls, and business value reporting. That's the goal."

---

## Slide 15 — Key Takeaways + What's Next
**Layout:** Takeaways + L11 preview

**Content:**
**Key Takeaways:**
1. XOps is not a single discipline — it's a family (DataOps, MLOps, LLMOps, AgentOps), each addressing a different layer of the AI system stack
2. DataOps maturity requires six capabilities: orchestration, quality gates, observability, version control, testing, and environment parity
3. MLOps automation progresses through four levels: manual → automated training → full CI/CD → self-optimizing; most enterprises are at Level 1-2
4. SageMaker Pipelines is the automation engine for NorthStar: training → evaluation → gate → register, fully automated
5. The XOps ROI is measurable: automation eliminates $144K+/year in manual overhead and incident costs for a 3-system platform

**Next Session (Thu Oct 8):**
- Topic: XOps II — LLMOps & AgentOps; operational discipline for foundation model systems
- Reading due: *The XOps Stack* — "LLMOps" through "Key Takeaways"
- Lab 3 due in 11 days — where are you?

**Figure:** *Five-takeaway summary.* Standard format. Lab 3 countdown in amber (11 days). XOps radar chart thumbnail showing current vs. target state.

**Notes:** Quick Lab 3 check-in: "Where is everyone? Who has at least one successful training run in MLflow?" Address blockers. End with: "Thursday we cover LLMOps and AgentOps — the operational disciplines for your RAG and agent systems. If you're doing Lab 3 Option A or B, this lecture is especially relevant."
