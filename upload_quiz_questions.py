#!/usr/bin/env python3
"""
Upload 5 quiz questions to each of the 12 CS 401R reading quiz shells.
    export CANVAS_API_TOKEN="your_token"
    python upload_quiz_questions.py
"""

import os, sys, requests

BASE_URL  = "https://byu.instructure.com"
COURSE_ID = "34609"
API_TOKEN = os.environ.get("CANVAS_API_TOKEN", "").strip()
if not API_TOKEN:
    sys.exit("Set CANVAS_API_TOKEN")

ROOT    = f"{BASE_URL}/api/v1/courses/{COURSE_ID}"
HEADERS = {"Authorization": f"Bearer {API_TOKEN}", "Content-Type": "application/json"}


# ─────────────────────────────────────────────────────────────────────────────
# Question bank — 5 questions per quiz, 10 pts each quiz (2 pts/question)
# mc  = multiple_choice_question  → answers list, first entry is correct
# tf  = true_false_question       → correct is "True" or "False"
# ─────────────────────────────────────────────────────────────────────────────

QUIZZES = {

    627962: {
        "title": "Week 02: AISDLC + AI Platform",
        "questions": [
            {
                "type": "mc",
                "text": "Which of the following best describes why the AI Systems Development Lifecycle (AISDLC) must differ from traditional software development?",
                "correct": "AI model quality degrades over time as real-world data distributions shift, requiring ongoing monitoring and retraining that software does not.",
                "wrong": [
                    "AI systems require more programmers than equivalent software systems.",
                    "AI development always requires more compute than traditional software development.",
                    "AI systems cannot be unit-tested before deployment.",
                ],
            },
            {
                "type": "tf",
                "text": "In the AISDLC, deployment is the final stage — once a model is live in production, the development lifecycle is complete.",
                "correct": "False",
            },
            {
                "type": "mc",
                "text": "What is the primary purpose of a stage gate in the AISDLC?",
                "correct": "To ensure each phase produces required artifacts and meets defined criteria before the project proceeds to the next phase.",
                "wrong": [
                    "To slow development velocity in order to reduce bugs.",
                    "To schedule mandatory team meetings between development sprints.",
                    "To produce documentation for future maintainers of the system.",
                ],
            },
            {
                "type": "mc",
                "text": "The 'compound returns' argument for investing in an AI platform refers to which of the following?",
                "correct": "Each capability added to the platform makes every subsequent AI system faster and cheaper to build, creating compounding productivity gains over time.",
                "wrong": [
                    "The financial returns from AI multiply as model accuracy improves.",
                    "Larger models trained on more data produce compounding accuracy improvements.",
                    "Platform infrastructure investments earn interest as cloud costs decline.",
                ],
            },
            {
                "type": "tf",
                "text": "A model that achieves strong performance on a held-out test set has met all requirements for production readiness.",
                "correct": "False",
            },
        ],
    },

    627963: {
        "title": "Week 03: AI Platform II + Data Engineering",
        "questions": [
            {
                "type": "mc",
                "text": "What is 'training-serving skew' in the context of feature engineering?",
                "correct": "A discrepancy between the features computed at training time and the features actually available at inference time in production.",
                "wrong": [
                    "A performance gap between a model's training accuracy and its validation accuracy.",
                    "The latency difference between training a model and serving predictions from it.",
                    "A mismatch between the compute used for training versus inference.",
                ],
            },
            {
                "type": "tf",
                "text": "Infrastructure as Code (IaC) means that cloud infrastructure is defined, versioned, and provisioned through machine-readable configuration files rather than through manual console interactions.",
                "correct": "True",
            },
            {
                "type": "mc",
                "text": "A SageMaker Feature Store's online store is optimized for which use case?",
                "correct": "Low-latency, real-time feature retrieval at model inference time.",
                "wrong": [
                    "Storing large historical datasets for batch model training jobs.",
                    "Archiving raw ingested data for long-term compliance storage.",
                    "Running parallel feature computation jobs across distributed clusters.",
                ],
            },
            {
                "type": "mc",
                "text": "What is the primary purpose of data lineage tracking in an AI system?",
                "correct": "Tracing each data artifact back to its source so that data quality issues can be diagnosed, reproduced, and audited.",
                "wrong": [
                    "Compressing datasets to reduce storage costs in the data lake.",
                    "Automatically encrypting data as it moves through the pipeline.",
                    "Scheduling data pipeline jobs based on upstream dependencies.",
                ],
            },
            {
                "type": "tf",
                "text": "The Zillow Offers case study demonstrates that a model can fail catastrophically in production even when its historical backtested performance appeared strong.",
                "correct": "True",
            },
        ],
    },

    627964: {
        "title": "Week 04: Data Engineering II + Model Development",
        "questions": [
            {
                "type": "mc",
                "text": "What is the primary risk of temporal leakage in feature engineering?",
                "correct": "Training features include information that would not be available at the time a prediction is made, causing the model to appear more accurate than it actually is in production.",
                "wrong": [
                    "Features take too long to compute to meet real-time inference latency requirements.",
                    "The feature store becomes unavailable during peak inference load.",
                    "Features computed on historical data expire before the model can use them.",
                ],
            },
            {
                "type": "mc",
                "text": "When is prompt engineering the most appropriate choice compared to fine-tuning a foundation model?",
                "correct": "When the task requirements can be met through careful instruction design without modifying model weights, avoiding the cost and complexity of fine-tuning.",
                "wrong": [
                    "When maximum model performance is required regardless of cost.",
                    "When the task requires processing documents larger than the model's context window.",
                    "When the model needs to run offline without API access.",
                ],
            },
            {
                "type": "tf",
                "text": "Fine-tuning a foundation model always produces better results than retrieval-augmented generation (RAG) for enterprise knowledge base question-answering tasks.",
                "correct": "False",
            },
            {
                "type": "mc",
                "text": "Model versioning in a production AI system primarily serves which purpose?",
                "correct": "Enabling reproducibility, rollback to prior versions, and auditing of which model version produced which predictions.",
                "wrong": [
                    "Reducing the storage footprint of model artifacts in the model registry.",
                    "Accelerating model inference by caching frequently used model weights.",
                    "Allowing multiple data scientists to modify the same model simultaneously.",
                ],
            },
            {
                "type": "tf",
                "text": "XGBoost was selected for the NorthStar churn prediction model because it is universally the highest-performing algorithm for any tabular binary classification problem.",
                "correct": "False",
            },
        ],
    },

    627965: {
        "title": "Week 05: RAG + Agent Development",
        "questions": [
            {
                "type": "mc",
                "text": "In a retrieval-augmented generation (RAG) pipeline, what is the purpose of the chunking step?",
                "correct": "Splitting source documents into segments of appropriate size for embedding and efficient retrieval from the vector store.",
                "wrong": [
                    "Compressing vector embeddings to reduce storage costs.",
                    "Encrypting document content before it is stored in the retrieval index.",
                    "Deduplicating overlapping documents in the knowledge corpus.",
                ],
            },
            {
                "type": "mc",
                "text": "The 'faithfulness' metric in RAG system evaluation measures which of the following?",
                "correct": "Whether the generated answer is grounded in the retrieved context rather than containing hallucinated information.",
                "wrong": [
                    "How quickly the system retrieves relevant documents from the vector store.",
                    "Whether the retrieved chunks contain the correct number of tokens.",
                    "How semantically similar the answer is to the user's original query.",
                ],
            },
            {
                "type": "tf",
                "text": "A ReAct agent selects which tool to call by executing a fixed, pre-programmed decision tree defined at development time.",
                "correct": "False",
            },
            {
                "type": "mc",
                "text": "Which failure mode is most distinctive to agentic AI systems compared to single-turn LLM completions?",
                "correct": "Error propagation and compounding across a multi-step action sequence, where an early mistake amplifies through subsequent steps.",
                "wrong": [
                    "Hallucination of factual information not present in training data.",
                    "Sensitivity to minor variations in prompt wording.",
                    "Performance degradation when input length exceeds the context window.",
                ],
            },
            {
                "type": "tf",
                "text": "For enterprise AI use cases, an agentic system always delivers better business outcomes than a simpler RAG pipeline covering the same task.",
                "correct": "False",
            },
        ],
    },

    627966: {
        "title": "Week 06: XOps Stack",
        "questions": [
            {
                "type": "mc",
                "text": "What distinguishes MLOps from traditional DevOps practices?",
                "correct": "MLOps must additionally manage data versioning, experiment tracking, model drift monitoring, and retraining triggers alongside application code deployment.",
                "wrong": [
                    "MLOps applies exclusively to cloud infrastructure while DevOps applies to on-premise systems.",
                    "MLOps eliminates the need for CI/CD pipelines by automating model selection.",
                    "MLOps is only relevant for organizations with more than 50 data scientists.",
                ],
            },
            {
                "type": "tf",
                "text": "In a DataOps framework, data pipelines should be treated as production software: versioned in source control, tested, and monitored in production.",
                "correct": "True",
            },
            {
                "type": "mc",
                "text": "LLMOps extends traditional MLOps primarily to address which challenge unique to foundation model systems?",
                "correct": "Managing prompt versioning, output quality evaluation, and the cost of token-based inference at enterprise scale.",
                "wrong": [
                    "Replacing human data labelers with automated data generation pipelines.",
                    "Retraining foundation models more frequently than traditional ML models requires.",
                    "Deploying large language models to edge devices with constrained compute resources.",
                ],
            },
            {
                "type": "mc",
                "text": "What is the primary concern that AgentOps addresses that MLOps does not?",
                "correct": "Providing operational governance, observability, and safety guardrails for AI systems that autonomously take actions with real-world consequences.",
                "wrong": [
                    "Managing the deployment of physical robotic automation systems in warehouses.",
                    "Tracking the performance of data engineering pipeline agents in Apache Airflow.",
                    "Automating human review of model outputs before they reach end users.",
                ],
            },
            {
                "type": "tf",
                "text": "A team that manually initiates model retraining on an ad-hoc basis whenever someone notices performance degradation is operating at a high XOps maturity level.",
                "correct": "False",
            },
        ],
    },

    627967: {
        "title": "Week 07: Testing & Evaluation",
        "questions": [
            {
                "type": "mc",
                "text": "What is the purpose of a model regression test in an AI CI/CD pipeline?",
                "correct": "Ensuring that a newly trained model version does not perform significantly worse than the current production champion on held-out evaluation data.",
                "wrong": [
                    "Testing whether the model can accurately solve regression (continuous prediction) tasks.",
                    "Detecting whether the training dataset contains statistically significant outliers.",
                    "Verifying that model predictions are monotonically ordered by confidence score.",
                ],
            },
            {
                "type": "tf",
                "text": "For a generative AI system, passing all automated unit tests and integration tests is sufficient to guarantee the system is safe to deploy to production users.",
                "correct": "False",
            },
            {
                "type": "mc",
                "text": "The Google Model Cards framework is primarily designed to accomplish which of the following?",
                "correct": "Document a model's intended uses, known limitations, and disaggregated performance across subgroups to enable accountability and informed deployment decisions.",
                "wrong": [
                    "Replace traditional unit testing with a structured documentation process.",
                    "Certify that a model has passed Google's internal safety review process.",
                    "Publish model weights publicly to enable reproducibility by the research community.",
                ],
            },
            {
                "type": "mc",
                "text": "When evaluating a churn prediction model on a dataset where 95% of customers do not churn, which metric is most likely to give a misleading picture of model quality?",
                "correct": "Accuracy",
                "wrong": [
                    "AUC-ROC",
                    "Precision at top 10%",
                    "Recall at top 10%",
                ],
            },
            {
                "type": "tf",
                "text": "A slice evaluation examines model performance broken down across meaningful subgroups of the population — such as customer loyalty tier or tenure band — to surface differential performance.",
                "correct": "True",
            },
        ],
    },

    627968: {
        "title": "Week 08: Continuous Delivery",
        "questions": [
            {
                "type": "mc",
                "text": "What is the key distinction between Continuous Integration (CI) and Continuous Delivery (CD) in an AI pipeline?",
                "correct": "CI validates code and model quality on every commit; CD automates the progression of a validated model through staging environments toward production readiness.",
                "wrong": [
                    "CI runs in the cloud while CD runs in on-premise data centers.",
                    "CI covers data pipelines exclusively while CD covers only model deployment.",
                    "CI is fully automated while CD always requires a manual approval step.",
                ],
            },
            {
                "type": "tf",
                "text": "For high-stakes enterprise AI systems, best practice is to automatically deploy any model that passes all automated tests directly to production without a human approval gate.",
                "correct": "False",
            },
            {
                "type": "mc",
                "text": "The Spotify Hendrix case study is cited in the Continuous Delivery chapter to illustrate which principle?",
                "correct": "How disciplined CI/CD practices enable teams to safely ship frequent model updates at scale while maintaining production reliability.",
                "wrong": [
                    "How streaming companies build and iterate on music recommendation systems.",
                    "The risks of deploying models without an A/B testing framework.",
                    "How to implement CI/CD pipelines specifically on AWS CodePipeline.",
                ],
            },
            {
                "type": "mc",
                "text": "In an AI CI/CD context, 'pipeline health' metrics typically track which of the following?",
                "correct": "Build success rate, test pass rate, deployment frequency, and lead time from code commit to production availability.",
                "wrong": [
                    "The CPU and memory utilization of the servers running the pipeline.",
                    "The quality and freshness of training data entering the pipeline.",
                    "The number of engineers actively committing code to the pipeline repository.",
                ],
            },
            {
                "type": "tf",
                "text": "Infrastructure automation in AI continuous delivery means the infrastructure required to serve a model is defined as code and provisioned automatically as part of the deployment process.",
                "correct": "True",
            },
        ],
    },

    627969: {
        "title": "Week 09: Deployment & Scaling",
        "questions": [
            {
                "type": "mc",
                "text": "In a canary deployment strategy, what occurs during the initial rollout phase?",
                "correct": "A small percentage of production traffic is routed to the new model version while the majority continues to be served by the current production version.",
                "wrong": [
                    "The new model replaces the old model entirely across all production traffic at once.",
                    "The new model runs alongside the old model but handles no real user traffic.",
                    "The new model is deployed only to internal employees before external release.",
                ],
            },
            {
                "type": "tf",
                "text": "In a shadow deployment, production users receive responses from the new model while the old model's outputs are logged as a comparison baseline.",
                "correct": "False",
            },
            {
                "type": "mc",
                "text": "What is the primary risk of deploying a new model to 100% of production traffic simultaneously without a gradual rollout strategy?",
                "correct": "There is no opportunity to catch performance regressions or unexpected behavior before they affect the entire user base.",
                "wrong": [
                    "Infrastructure costs increase due to running two models simultaneously during rollout.",
                    "Traffic routing overhead degrades inference latency for all users.",
                    "Compliance frameworks prohibit simultaneous multi-version model deployments.",
                ],
            },
            {
                "type": "mc",
                "text": "The Lyft ML Platform case study illustrates which deployment challenge at enterprise scale?",
                "correct": "Managing the operational complexity of deploying and maintaining hundreds of models across multiple teams with consistent practices and shared infrastructure.",
                "wrong": [
                    "The hardware cost of serving large language models for ride-sharing pricing.",
                    "The difficulty of building real-time routing optimization under traffic constraints.",
                    "Regulatory compliance requirements for ML systems in the transportation industry.",
                ],
            },
            {
                "type": "tf",
                "text": "SageMaker endpoint auto-scaling policies can be configured to scale out when the number of model invocations per instance per minute exceeds a defined threshold.",
                "correct": "True",
            },
        ],
    },

    627970: {
        "title": "Week 10: Security, Privacy & Compliance",
        "questions": [
            {
                "type": "mc",
                "text": "Prompt injection in an LLM-powered application refers to which type of attack?",
                "correct": "An adversarial input crafted to override the system's instructions, bypass safety controls, or extract information the system should not reveal.",
                "wrong": [
                    "Injecting poisoned examples into a model's fine-tuning dataset to influence its behavior.",
                    "Using a structured prompt template to standardize and validate model inputs.",
                    "Artificially inflating inference latency to simulate denial-of-service conditions.",
                ],
            },
            {
                "type": "tf",
                "text": "Under GDPR, a company may freely use customer purchase history for AI model training without restriction as long as the data has been anonymized by removing direct identifiers like names and email addresses.",
                "correct": "False",
            },
            {
                "type": "mc",
                "text": "In the STRIDE threat model applied to an AI inference endpoint, a model inversion attack — where an adversary queries the model to reconstruct training data — falls into which STRIDE category?",
                "correct": "Information Disclosure",
                "wrong": [
                    "Spoofing",
                    "Tampering",
                    "Denial of Service",
                ],
            },
            {
                "type": "mc",
                "text": "What makes 'right to erasure' compliance particularly challenging for trained machine learning models compared to raw databases?",
                "correct": "A trained model may have encoded information about an individual in its weights, making true erasure technically difficult even after the training record is deleted from the database.",
                "wrong": [
                    "Deleting a model from a model registry requires elevated cloud administrator access.",
                    "GDPR's right to erasure provisions do not apply to ML model artifacts, only raw data.",
                    "Model weights are typically stored in a format that cannot be modified after training.",
                ],
            },
            {
                "type": "tf",
                "text": "Committing a .env file containing AWS access keys to a public GitHub repository constitutes a critical security violation regardless of the scope of permissions attached to those credentials.",
                "correct": "True",
            },
        ],
    },

    627971: {
        "title": "Week 11: Metrics + Monitoring",
        "questions": [
            {
                "type": "mc",
                "text": "What is the key distinction between data drift and concept drift in a production ML model?",
                "correct": "Data drift is a change in the statistical distribution of input features; concept drift is a change in the underlying relationship between inputs and the correct output label.",
                "wrong": [
                    "Data drift affects classification models while concept drift affects regression models.",
                    "Data drift is measurable with statistical tests while concept drift cannot be detected.",
                    "Data drift occurs during training while concept drift only manifests at inference time.",
                ],
            },
            {
                "type": "tf",
                "text": "A Population Stability Index (PSI) value greater than 0.2 for an input feature is generally interpreted as indicating significant distribution shift that warrants investigation.",
                "correct": "True",
            },
            {
                "type": "mc",
                "text": "How does a guardrail metric differ from a primary success metric?",
                "correct": "A guardrail metric defines a minimum acceptable threshold that must not be violated, even if optimizing the primary metric would require crossing it.",
                "wrong": [
                    "Guardrail metrics are tracked at a weekly cadence while primary metrics are tracked daily.",
                    "Guardrail metrics are defined by engineering teams while primary metrics are set by product managers.",
                    "Guardrail metrics apply only to generative AI systems, not traditional ML models.",
                ],
            },
            {
                "type": "mc",
                "text": "Why is concept drift detection particularly challenging for the NorthStar churn prediction model?",
                "correct": "Churn ground truth labels are only observable 90 days after prediction, creating an unavoidable lag before the model can be evaluated against actual outcomes.",
                "wrong": [
                    "The churn model is retrained so frequently that drift cannot accumulate meaningfully.",
                    "CloudWatch does not natively support custom metric emission from SageMaker endpoints.",
                    "XGBoost models are architecturally resistant to concept drift by design.",
                ],
            },
            {
                "type": "tf",
                "text": "Comprehensive AI system observability requires monitoring at only the model performance layer, since cloud providers handle infrastructure-level metrics automatically.",
                "correct": "False",
            },
        ],
    },

    627972: {
        "title": "Week 12: Reliability Engineering + AI Economics",
        "questions": [
            {
                "type": "mc",
                "text": "In the context of Service Level Objectives (SLOs), what is an error budget?",
                "correct": "The allowable amount of unreliability derived from the gap between the SLO target and 100% availability — it defines how much downtime or degradation is permissible.",
                "wrong": [
                    "The financial budget allocated to the engineering team responsible for fixing production incidents.",
                    "The number of on-call engineers available to respond to production alerts.",
                    "The maximum acceptable response latency before a SLO alert fires.",
                ],
            },
            {
                "type": "tf",
                "text": "A blameless postmortem after an AI system incident focuses on identifying systemic process failures rather than assigning individual accountability for the outage.",
                "correct": "True",
            },
            {
                "type": "mc",
                "text": "'Graceful degradation' in an AI production system refers to which behavior?",
                "correct": "The system falls back to a simpler response, cached result, or rule-based alternative rather than returning an error or failing completely when a component is unavailable.",
                "wrong": [
                    "The system shuts down safely without data loss when it encounters a fatal error.",
                    "Model accuracy naturally decreases over time as expected due to concept drift.",
                    "The system sends stakeholder notifications before initiating a planned maintenance window.",
                ],
            },
            {
                "type": "mc",
                "text": "When calculating fully-loaded cost per AI prediction, which cost component is most commonly omitted from naive estimates?",
                "correct": "Amortized model training costs and ongoing human labor for model maintenance, monitoring, and retraining.",
                "wrong": [
                    "Real-time inference compute costs from the serving endpoint.",
                    "Third-party API costs for embedding or foundation model calls.",
                    "Data storage and transfer costs in the feature pipeline.",
                ],
            },
            {
                "type": "tf",
                "text": "In a build-vs-buy analysis for an AI capability, a lower total cost of ownership always favors the build option over purchasing a third-party solution.",
                "correct": "False",
            },
        ],
    },

    627973: {
        "title": "Week 13: Measuring Business Value",
        "questions": [
            {
                "type": "mc",
                "text": "The Metric Pyramid framework connects which two things in an AI system?",
                "correct": "Low-level technical model performance metrics up through business outcome metrics, making the causal chain from model behavior to business impact explicit.",
                "wrong": [
                    "Model training infrastructure metrics and model serving infrastructure metrics.",
                    "Engineering team KPIs and executive compensation targets.",
                    "Data pipeline performance metrics and model registry status.",
                ],
            },
            {
                "type": "tf",
                "text": "If an AI model is deployed and company revenue increases in the following quarter, that revenue increase can be fully attributed to the model without further analysis.",
                "correct": "False",
            },
            {
                "type": "mc",
                "text": "In AI business value measurement, a 'holdout group' refers to which of the following?",
                "correct": "A segment of users who do not receive the AI system's outputs, retained as a control group to measure the true causal impact of the system on business outcomes.",
                "wrong": [
                    "A subset of training data withheld from the model during training to evaluate generalization.",
                    "A team of business analysts who review model outputs before they reach customers.",
                    "An engineering team held in reserve to handle production incidents during deployment.",
                ],
            },
            {
                "type": "mc",
                "text": "Which of the following is the most appropriate way to communicate the value of the NorthStar churn model to a CFO?",
                "correct": "The model prevented an estimated $4.2M in annual revenue loss by enabling targeted retention campaigns, delivering a 3.1× ROI on platform investment.",
                "wrong": [
                    "The model achieves an AUC-ROC of 0.78 on the held-out validation dataset.",
                    "The model correctly identifies 72% of customers who will churn within 90 days.",
                    "The model serves predictions at p95 latency of 45ms with 99.9% endpoint availability.",
                ],
            },
            {
                "type": "tf",
                "text": "A Value Methodology Note documents the attribution method, counterfactual baseline, known confounders, and confidence level for an AI system's business impact measurement, making the approach auditable and repeatable.",
                "correct": "True",
            },
        ],
    },

}


# ─────────────────────────────────────────────────────────────────────────────
# Canvas API helpers
# ─────────────────────────────────────────────────────────────────────────────

def make_mc_answers(correct, wrong_list):
    answers = [{"answer_text": correct, "answer_weight": 100}]
    for w in wrong_list:
        answers.append({"answer_text": w, "answer_weight": 0})
    return answers

def make_tf_answers(correct_str):
    """correct_str is 'True' or 'False'"""
    return [
        {"answer_text": "True",  "answer_weight": 100 if correct_str == "True"  else 0},
        {"answer_text": "False", "answer_weight": 100 if correct_str == "False" else 0},
    ]

def post_question(quiz_id, q_num, q):
    if q["type"] == "mc":
        payload = {
            "question": {
                "question_name":  f"Question {q_num}",
                "question_text":  q["text"],
                "question_type":  "multiple_choice_question",
                "points_possible": 2,
                "answers": make_mc_answers(q["correct"], q["wrong"]),
            }
        }
    else:
        payload = {
            "question": {
                "question_name":  f"Question {q_num}",
                "question_text":  q["text"],
                "question_type":  "true_false_question",
                "points_possible": 2,
                "answers": make_tf_answers(q["correct"]),
            }
        }
    r = requests.post(f"{ROOT}/quizzes/{quiz_id}/questions",
                      headers=HEADERS, json=payload)
    return r.ok


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("Uploading quiz questions to Canvas\n")
    total_ok = 0

    for quiz_id, quiz_data in QUIZZES.items():
        title = quiz_data["title"]
        questions = quiz_data["questions"]
        print(f"  {title} (quiz_id={quiz_id})")
        ok_count = 0
        for i, q in enumerate(questions, 1):
            success = post_question(quiz_id, i, q)
            ok_count += success
            icon = "✓" if success else "✗"
            print(f"    {icon} Q{i} ({'MC' if q['type'] == 'mc' else 'T/F'})")
        total_ok += ok_count
        print()

    print(f"Done — {total_ok}/60 questions uploaded.")
    print(f"Review at: {BASE_URL}/courses/{COURSE_ID}/quizzes")

if __name__ == "__main__":
    main()
