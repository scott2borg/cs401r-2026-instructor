"""
CS 401R — Lab 3: Model Development
Track A: Launch SageMaker Training Job (local terminal script)

Run this from your local machine to kick off a managed SageMaker Training Job.
The job runs train.py inside an XGBoost container on ml.m5.xlarge, pulling data
from the SageMaker Feature Store and writing artifacts to S3.

Usage:
    python launch_training.py \
        --role-arn arn:aws:iam::123456789012:role/NorthStarSageMakerRole \
        --artifacts-bucket northstar-dev-artifacts

Optional overrides (hyperparameters, dates, etc.):
    python launch_training.py \
        --role-arn arn:aws:iam::123456789012:role/NorthStarSageMakerRole \
        --artifacts-bucket northstar-dev-artifacts \
        --feature-group-name northstar-churn-features \
        --start-date 2025-01-01 \
        --end-date 2025-12-31 \
        --max-depth 8 \
        --eta 0.05 \
        --n-estimators 500

After training completes, this script queries SageMaker Experiments to print
the run summary, then shows the Model Registry entry if --register-model was set.
"""

import argparse
import json
import logging
import sys
from datetime import datetime

import boto3

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Launch NorthStar churn model training job on SageMaker"
    )

    # Required
    parser.add_argument(
        "--role-arn",
        required=True,
        help="IAM role ARN with SageMaker + S3 + Feature Store permissions",
    )
    parser.add_argument(
        "--artifacts-bucket",
        required=True,
        help="S3 bucket for model artifacts and Athena query results",
    )

    # Data
    parser.add_argument(
        "--feature-group-name",
        default="northstar-churn-features",
        help="SageMaker Feature Group name (default: northstar-churn-features)",
    )
    parser.add_argument(
        "--start-date",
        default="2025-01-01",
        help="Training data start date, ISO format (default: 2025-01-01)",
    )
    parser.add_argument(
        "--end-date",
        default="2025-12-31",
        help="Training data end date, ISO format (default: 2025-12-31)",
    )

    # Hyperparameters
    parser.add_argument("--max-depth", type=int, default=6,
                        help="XGBoost max_depth (default: 6)")
    parser.add_argument("--eta", type=float, default=0.1,
                        help="XGBoost learning rate (default: 0.1)")
    parser.add_argument("--n-estimators", type=int, default=300,
                        help="Max boosting rounds (default: 300; early stopping applies)")
    parser.add_argument("--subsample", type=float, default=0.8,
                        help="XGBoost subsample ratio (default: 0.8)")
    parser.add_argument("--colsample-bytree", type=float, default=0.8,
                        help="XGBoost colsample_bytree (default: 0.8)")
    parser.add_argument("--min-child-weight", type=int, default=5,
                        help="XGBoost min_child_weight (default: 5)")
    parser.add_argument("--scale-pos-weight", type=float, default=3.0,
                        help="Class imbalance correction (default: 3.0 for ~25%% churn rate)")
    parser.add_argument("--early-stopping-rounds", type=int, default=20,
                        help="Early stopping patience (default: 20)")
    parser.add_argument("--eval-fraction", type=float, default=0.20,
                        help="Validation split fraction (default: 0.20)")

    # Options
    parser.add_argument("--register-model", action="store_true",
                        help="Register model in SageMaker Model Registry after training")
    parser.add_argument("--instance-type", default="ml.m5.xlarge",
                        help="SageMaker training instance type (default: ml.m5.xlarge)")
    parser.add_argument("--region", default="us-east-1",
                        help="AWS region (default: us-east-1)")
    parser.add_argument("--experiment-name", default="northstar-churn-experiment",
                        help="SageMaker Experiments name to query after training")

    return parser.parse_args()


def retrieve_experiment_results(experiment_name: str, region: str) -> None:
    """
    Query SageMaker Experiments to print the most recent run's metrics.

    SageMaker Experiments stores every run's parameters and metrics automatically
    when Run() is used in train.py. This is the audit trail for model governance.
    """
    sm_client = boto3.client("sagemaker", region_name=region)

    try:
        # List runs for this experiment, sorted by creation time descending
        response = sm_client.list_experiment_trials(
            ExperimentName=experiment_name,
            SortBy="CreationTime",
            SortOrder="Descending",
            MaxResults=1,
        )
        trial_summaries = response.get("TrialSummaries", [])
        if not trial_summaries:
            logger.warning("No trials found for experiment: %s", experiment_name)
            return

        trial_name = trial_summaries[0]["TrialName"]
        logger.info("Most recent trial: %s", trial_name)

        # Describe the trial components (runs)
        components = sm_client.list_trial_components(TrialName=trial_name)
        for component in components.get("TrialComponentSummaries", []):
            comp_name = component["TrialComponentName"]
            detail = sm_client.describe_trial_component(TrialComponentName=comp_name)

            print("\n" + "=" * 60)
            print(f"Experiment Run: {comp_name}")
            print("=" * 60)

            params = detail.get("Parameters", {})
            if params:
                print("\nHyperparameters:")
                for k, v in sorted(params.items()):
                    val = v.get("NumberValue", v.get("StringValue", "?"))
                    print(f"  {k}: {val}")

            metrics = detail.get("Metrics", {})
            if metrics:
                print("\nMetrics:")
                for k, v in sorted(metrics.items()):
                    print(f"  {k}: {v.get('Last', '?'):.4f}")

            print("=" * 60)

    except sm_client.exceptions.ResourceNotFound:
        logger.warning("Experiment '%s' not found. Was it created during training?", experiment_name)
    except Exception as e:
        logger.error("Could not retrieve experiment results: %s", e)


def retrieve_model_registry_entry(region: str) -> None:
    """
    Print the most recently registered model package from the northstar-churn-models group.
    Shows approval status, metrics, and ARN for the student to review.
    """
    sm_client = boto3.client("sagemaker", region_name=region)
    model_package_group = "northstar-churn-models"

    try:
        response = sm_client.list_model_packages(
            ModelPackageGroupName=model_package_group,
            SortBy="CreationTime",
            SortOrder="Descending",
            MaxResults=1,
        )
        packages = response.get("ModelPackageSummaryList", [])
        if not packages:
            logger.warning("No model packages found in group: %s", model_package_group)
            return

        latest = packages[0]
        arn = latest["ModelPackageArn"]
        detail = sm_client.describe_model_package(ModelPackageName=arn)

        print("\n" + "=" * 60)
        print("Model Registry Entry")
        print("=" * 60)
        print(f"  ARN:             {arn}")
        print(f"  Approval Status: {detail.get('ModelApprovalStatus', 'Unknown')}")
        print(f"  Creation Time:   {detail.get('CreationTime', 'Unknown')}")

        metadata = detail.get("CustomerMetadataProperties", {})
        if metadata:
            print("\n  Metadata:")
            for k, v in sorted(metadata.items()):
                print(f"    {k}: {v}")

        print("=" * 60)
        print("\nTo approve for deployment:")
        print(f"  aws sagemaker update-model-package \\")
        print(f"    --model-package-arn {arn} \\")
        print(f"    --model-approval-status Approved")

    except sm_client.exceptions.ValidationException as e:
        logger.warning("Could not retrieve model registry entry: %s", e)
    except Exception as e:
        logger.error("Unexpected error querying Model Registry: %s", e)


def main() -> None:
    args = parse_args()

    # Import here so the script can be imported without SageMaker installed (unit tests)
    try:
        from models.churn.train import launch_training_job
    except ImportError:
        # If running from the northstar-ai-platform root, adjust sys.path
        sys.path.insert(0, str(__import__("pathlib").Path(__file__).parents[2]))
        from models.churn.train import launch_training_job

    hyperparams = {
        "max-depth": str(args.max_depth),
        "eta": str(args.eta),
        "n-estimators": str(args.n_estimators),
        "subsample": str(args.subsample),
        "colsample-bytree": str(args.colsample_bytree),
        "min-child-weight": str(args.min_child_weight),
        "scale-pos-weight": str(args.scale_pos_weight),
        "early-stopping-rounds": str(args.early_stopping_rounds),
        "eval-fraction": str(args.eval_fraction),
        "start-date": args.start_date,
        "end-date": args.end_date,
        "register-model": str(args.register_model).lower(),
    }

    logger.info("Launching SageMaker Training Job...")
    logger.info("  Role ARN:       %s", args.role_arn)
    logger.info("  Artifacts:      s3://%s/", args.artifacts_bucket)
    logger.info("  Feature Group:  %s", args.feature_group_name)
    logger.info("  Date range:     %s → %s", args.start_date, args.end_date)
    logger.info("  Instance type:  %s", args.instance_type)

    estimator = launch_training_job(
        feature_group_name=args.feature_group_name,
        artifacts_bucket=args.artifacts_bucket,
        role_arn=args.role_arn,
        hyperparams=hyperparams,
    )

    print("\n" + "=" * 60)
    print("Training Job Complete")
    print("=" * 60)
    print(f"  Model data URI: {estimator.model_data}")
    print("=" * 60)

    # Query Experiments for the run metrics
    logger.info("Retrieving Experiment results...")
    retrieve_experiment_results(args.experiment_name, args.region)

    # Show Model Registry entry if registration was requested
    if args.register_model:
        logger.info("Retrieving Model Registry entry...")
        retrieve_model_registry_entry(args.region)


if __name__ == "__main__":
    main()
