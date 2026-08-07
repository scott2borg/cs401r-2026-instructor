"""
NorthStar Retail — SageMaker Pipeline Definition
Defines the automated model training and evaluation pipeline.

Pipeline steps:
  1. TrainingStep  — XGBoost training (features pulled from Feature Store inside script)
  2. ProcessingStep — Model evaluation: writes evaluation_metrics.json + slice_metrics.json
  3. ConditionStep  — Promote to registry only if AUC-ROC >= MinAUCThreshold
  4. RegisterModel  — Create/update model package in northstar-churn-model-group

The pipeline is parameterized so the same definition can run for dev
(shorter date window) and prod (full window) without editing code.

Usage:
    # Create or update the pipeline definition in SageMaker:
    python pipeline/sagemaker_pipeline.py --create --role arn:aws:iam::... --bucket my-bucket

    # Trigger an execution with optional parameter overrides:
    python pipeline/sagemaker_pipeline.py --run --role arn:aws:iam::... --bucket my-bucket

    # Override a parameter at run time:
    python pipeline/sagemaker_pipeline.py --run ... --min-auc 0.74
"""

import argparse
import json
import logging
import os
import boto3
import sagemaker
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.steps import TrainingStep, ProcessingStep
from sagemaker.workflow.conditions import ConditionGreaterThanOrEqualTo
from sagemaker.workflow.condition_step import ConditionStep
from sagemaker.workflow.parameters import ParameterString, ParameterFloat
from sagemaker.workflow.properties import PropertyFile
from sagemaker.workflow.functions import JsonGet
from sagemaker.processing import ScriptProcessor, ProcessingInput, ProcessingOutput
from sagemaker.xgboost import XGBoost
from sagemaker.model import Model
from sagemaker.workflow.model_step import ModelStep
from sagemaker.model_metrics import ModelMetrics, MetricsSource

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
PIPELINE_NAME = "northstar-churn-pipeline"
MODEL_PACKAGE_GROUP = "northstar-churn-model-group"
XGBOOST_FRAMEWORK_VERSION = "1.7-1"
PYTHON_VERSION = "py3"

# Quality thresholds — duplicated here so the pipeline definition is self-contained.
# The canonical source is pipeline/tests/test_model.py.
AUC_ROC_THRESHOLD = 0.72


# ---------------------------------------------------------------------------
# Pipeline factory
# ---------------------------------------------------------------------------

def create_pipeline(
    role_arn: str,
    artifacts_bucket: str,
    region: str = "us-east-1",
    python_image_uri: str = None,
) -> Pipeline:
    """
    Build and return the SageMaker Pipeline object.
    Call pipeline.upsert(role_arn) to register it with SageMaker.

    Args:
        role_arn: IAM role ARN with SageMaker + S3 + Feature Store permissions.
        artifacts_bucket: S3 bucket name for model artifacts and evaluation output.
        region: AWS region.
        python_image_uri: ECR URI for the ScriptProcessor image. If None, uses the
                          SageMaker-managed sklearn image (available in all regions).
    Returns:
        sagemaker.workflow.pipeline.Pipeline
    """
    boto_session = boto3.Session(region_name=region)
    sm_session = sagemaker.Session(boto_session=boto_session)

    # ------------------------------------------------------------------
    # Pipeline parameters — overridable at execution time
    # ------------------------------------------------------------------
    training_start_date = ParameterString(
        name="TrainingStartDate",
        default_value="2025-02-01",
    )
    training_end_date = ParameterString(
        name="TrainingEndDate",
        default_value="2026-06-01",
    )
    commit_sha = ParameterString(
        name="CommitSha",
        default_value="local",
    )
    min_auc_threshold = ParameterFloat(
        name="MinAUCThreshold",
        default_value=AUC_ROC_THRESHOLD,
    )

    # ------------------------------------------------------------------
    # Step 1: Training
    # XGBoost estimator — features are pulled from Feature Store inside train.py
    # ------------------------------------------------------------------
    xgb_estimator = XGBoost(
        entry_point="train.py",
        source_dir="models/churn/",
        role=role_arn,
        instance_count=1,
        instance_type="ml.m5.xlarge",
        framework_version=XGBOOST_FRAMEWORK_VERSION,
        py_version=PYTHON_VERSION,
        output_path=f"s3://{artifacts_bucket}/models/",
        hyperparameters={
            # XGBoost tree parameters
            "max-depth": 6,
            "eta": 0.1,
            "num-round": 200,
            "min-child-weight": 5,
            "subsample": 0.8,
            "colsample-bytree": 0.8,
            # Imbalanced class handling: churn rate ~18% → scale_pos_weight ~ (1-0.18)/0.18 ≈ 4.6
            "scale-pos-weight": 5.5,
            # Passed through to train.py for Feature Store query
            "training-start-date": training_start_date,
            "training-end-date": training_end_date,
            "artifacts-bucket": artifacts_bucket,
        },
        enable_sagemaker_metrics=True,
        sagemaker_session=sm_session,
    )

    training_step = TrainingStep(
        name="TrainChurnModel",
        estimator=xgb_estimator,
        inputs={},  # Features pulled from Feature Store inside train.py
    )

    # ------------------------------------------------------------------
    # Step 2: Evaluation
    # Runs evaluate.py, which reads the model artifact and validation data,
    # then writes evaluation_metrics.json and slice_metrics.json to S3.
    # ------------------------------------------------------------------
    if python_image_uri is None:
        # Use the SageMaker-managed sklearn processor image
        from sagemaker.sklearn.processing import SKLearnProcessor
        eval_processor = SKLearnProcessor(
            framework_version="1.2-1",
            instance_type="ml.m5.large",
            instance_count=1,
            role=role_arn,
            sagemaker_session=sm_session,
        )
    else:
        eval_processor = ScriptProcessor(
            image_uri=python_image_uri,
            command=["python3"],
            instance_type="ml.m5.large",
            instance_count=1,
            role=role_arn,
            sagemaker_session=sm_session,
        )

    # PropertyFile lets the ConditionStep read values from the evaluation JSON
    eval_report = PropertyFile(
        name="EvaluationReport",
        output_name="evaluation",
        path="evaluation_metrics.json",
    )

    evaluation_step = ProcessingStep(
        name="EvaluateChurnModel",
        processor=eval_processor,
        inputs=[
            ProcessingInput(
                source=training_step.properties.ModelArtifacts.S3ModelArtifacts,
                destination="/opt/ml/processing/model",
            ),
        ],
        outputs=[
            ProcessingOutput(
                output_name="evaluation",
                source="/opt/ml/processing/evaluation",
                destination=f"s3://{artifacts_bucket}/evaluation/{commit_sha}/",
            ),
        ],
        code="models/churn/evaluate.py",
        property_files=[eval_report],
        job_arguments=[
            "--artifacts-bucket", artifacts_bucket,
            "--commit-sha", commit_sha,
        ],
    )

    # ------------------------------------------------------------------
    # Step 3: Condition — promote only if AUC >= MinAUCThreshold
    # ------------------------------------------------------------------
    auc_condition = ConditionGreaterThanOrEqualTo(
        left=JsonGet(
            step_name=evaluation_step.name,
            property_file=eval_report,
            json_path="auc_roc",
        ),
        right=min_auc_threshold,
    )

    # ------------------------------------------------------------------
    # Step 4a: Register model (runs when condition passes)
    # ------------------------------------------------------------------
    model = Model(
        image_uri=xgb_estimator.training_image_uri(),
        model_data=training_step.properties.ModelArtifacts.S3ModelArtifacts,
        role=role_arn,
        sagemaker_session=sm_session,
    )

    model_metrics = ModelMetrics(
        model_statistics=MetricsSource(
            s3_uri=f"s3://{artifacts_bucket}/evaluation/{commit_sha}/evaluation_metrics.json",
            content_type="application/json",
        )
    )

    register_step = ModelStep(
        name="RegisterChurnModel",
        step_args=model.register(
            content_types=["text/csv"],
            response_types=["application/json"],
            inference_instances=["ml.m5.large", "ml.m5.xlarge"],
            transform_instances=["ml.m5.xlarge"],
            model_package_group_name=MODEL_PACKAGE_GROUP,
            approval_status="PendingManualApproval",
            model_metrics=model_metrics,
            customer_metadata_properties={
                "auc_roc": JsonGet(
                    step_name=evaluation_step.name,
                    property_file=eval_report,
                    json_path="auc_roc",
                ),
                "precision_top10": JsonGet(
                    step_name=evaluation_step.name,
                    property_file=eval_report,
                    json_path="precision_top10",
                ),
                "recall_top10": JsonGet(
                    step_name=evaluation_step.name,
                    property_file=eval_report,
                    json_path="recall_top10",
                ),
                "commit_sha": commit_sha,
                "training_start_date": training_start_date,
                "training_end_date": training_end_date,
            },
        ),
    )

    # ------------------------------------------------------------------
    # Step 4b: If condition fails, log rejection (no-op ProcessingStep)
    # In a production system you'd trigger an SNS alert or JIRA ticket here.
    # ------------------------------------------------------------------
    rejection_processor = eval_processor  # Reuse the same image
    reject_step = ProcessingStep(
        name="RejectModel",
        processor=rejection_processor,
        code="pipeline/scripts/reject_model.py",
        job_arguments=[
            "--reason", "AUC below threshold",
            "--threshold", str(AUC_ROC_THRESHOLD),
            "--artifacts-bucket", artifacts_bucket,
            "--commit-sha", commit_sha,
        ],
    )

    # ------------------------------------------------------------------
    # Condition step wiring
    # ------------------------------------------------------------------
    condition_step = ConditionStep(
        name="CheckAUCThreshold",
        conditions=[auc_condition],
        if_steps=[register_step],
        else_steps=[reject_step],
    )

    # ------------------------------------------------------------------
    # Assemble pipeline
    # ------------------------------------------------------------------
    pipeline = Pipeline(
        name=PIPELINE_NAME,
        parameters=[
            training_start_date,
            training_end_date,
            commit_sha,
            min_auc_threshold,
        ],
        steps=[
            training_step,
            evaluation_step,
            condition_step,
        ],
        sagemaker_session=sm_session,
    )

    return pipeline


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="NorthStar churn SageMaker Pipeline management"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--create", action="store_true",
        help="Create or update the pipeline definition in SageMaker."
    )
    group.add_argument(
        "--run", action="store_true",
        help="Start a new pipeline execution."
    )
    parser.add_argument(
        "--role", required=True,
        help="IAM role ARN with SageMaker + S3 + Feature Store permissions."
    )
    parser.add_argument(
        "--bucket", required=True,
        help="S3 bucket name for artifacts and evaluation output."
    )
    parser.add_argument(
        "--region", default="us-east-1",
        help="AWS region (default: us-east-1)."
    )
    parser.add_argument(
        "--commit-sha", default="local",
        help="Git commit SHA to tag the pipeline execution."
    )
    parser.add_argument(
        "--min-auc", type=float, default=AUC_ROC_THRESHOLD,
        help=f"Minimum AUC threshold for model promotion (default: {AUC_ROC_THRESHOLD})."
    )
    parser.add_argument(
        "--start-date", default="2025-02-01",
        help="Training data start date (YYYY-MM-DD)."
    )
    parser.add_argument(
        "--end-date", default="2026-06-01",
        help="Training data end date (YYYY-MM-DD)."
    )
    return parser.parse_args()


def main():
    args = parse_args()
    pipeline = create_pipeline(
        role_arn=args.role,
        artifacts_bucket=args.bucket,
        region=args.region,
    )

    if args.create:
        logger.info(f"Upserting pipeline '{PIPELINE_NAME}' ...")
        response = pipeline.upsert(role_arn=args.role)
        pipeline_arn = response.get("PipelineArn", "")
        logger.info(f"Pipeline upserted: {pipeline_arn}")

    elif args.run:
        logger.info(f"Starting execution of pipeline '{PIPELINE_NAME}' ...")
        execution = pipeline.start(
            parameters={
                "CommitSha": args.commit_sha,
                "MinAUCThreshold": args.min_auc,
                "TrainingStartDate": args.start_date,
                "TrainingEndDate": args.end_date,
            }
        )
        logger.info(f"Execution ARN: {execution.arn}")
        logger.info(
            "Monitor progress in the SageMaker console under "
            f"Pipelines > {PIPELINE_NAME} > Executions."
        )


if __name__ == "__main__":
    main()
