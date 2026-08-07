"""
CS 401R — Lab 3: Model Development
Track A: Churn Prediction Model
NorthStar Retail AI Platform

This script is the SageMaker training job entry point.
It loads features from the SageMaker Feature Store, trains an XGBoost model,
performs slice evaluation, logs to SageMaker Experiments, and registers
the model in the SageMaker Model Registry.

Usage (local test, no SageMaker):
    python train.py --feature-group-name northstar-churn-features \
                    --start-date 2025-01-01 --end-date 2025-12-31 \
                    --artifacts-bucket northstar-dev-artifacts

Usage (inside SageMaker Training Job):
    Launched via launch_training.py — see that file.
"""

import argparse
import json
import logging
import os
import pickle
import tarfile
from datetime import datetime
from pathlib import Path

import boto3
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xgboost as xgb
from sagemaker.feature_store.feature_group import FeatureGroup
from sagemaker.session import Session
from sklearn.metrics import (
    auc,
    confusion_matrix,
    ConfusionMatrixDisplay,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Feature schema — must match Lab 2 Feature Store definition exactly
# ---------------------------------------------------------------------------
FEATURE_COLUMNS = [
    "days_since_last_purchase",
    "purchase_frequency_90d",
    "purchase_frequency_180d",
    "avg_basket_size_6m",
    "total_spend_90d",
    "category_diversity_score",
    "online_to_store_ratio",
    "promo_response_rate",
    "loyalty_tier_duration_days",
    "customer_tenure_days",
    "clickstream_sessions_30d",
    "add_to_cart_rate_30d",
]
LABEL_COLUMN = "churn_label"

# Categorical columns used for slice evaluation
LOYALTY_TIER_COLUMN = "loyalty_tier"
TENURE_BAND_COLUMN = "tenure_band"


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_features_from_feature_store(feature_group_name: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Query the SageMaker Feature Store offline store via Athena.

    Uses DISTINCT ON (customer_id) with ORDER BY write_time DESC to ensure
    we get the most-recent record per customer within the date window.
    This prevents duplicates introduced by incremental ingestion.

    Args:
        feature_group_name: SageMaker Feature Group name (e.g. "northstar-churn-features")
        start_date: ISO date string, inclusive (e.g. "2025-01-01")
        end_date:   ISO date string, inclusive (e.g. "2025-12-31")

    Returns:
        DataFrame with FEATURE_COLUMNS + LABEL_COLUMN
    """
    session = Session()
    feature_group = FeatureGroup(name=feature_group_name, sagemaker_session=session)
    athena_query = feature_group.athena_query()

    table_name = athena_query.table_name
    query_string = f"""
        SELECT
            customer_id,
            {', '.join(FEATURE_COLUMNS)},
            {LABEL_COLUMN},
            loyalty_tier,
            customer_tenure_days
        FROM (
            SELECT *,
                   ROW_NUMBER() OVER (
                       PARTITION BY customer_id
                       ORDER BY write_time DESC
                   ) AS rn
            FROM "{table_name}"
            WHERE event_time BETWEEN '{start_date}' AND '{end_date}'
        )
        WHERE rn = 1
    """
    # NOTE: Standard Athena (Presto/Trino) does not support DISTINCT ON (PostgreSQL syntax).
    # The subquery + ROW_NUMBER() window function is the portable equivalent.

    artifacts_bucket = os.environ.get("ARTIFACTS_BUCKET", "northstar-dev-artifacts")
    output_loc = f"s3://{artifacts_bucket}/athena-results/"

    logger.info("Running Athena query against Feature Store table: %s", table_name)
    athena_query.run(query_string=query_string, output_location=output_loc)
    athena_query.wait()

    df = athena_query.as_dataframe()
    logger.info("Loaded %d rows from Feature Store", len(df))
    return df


def add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add derived columns used for slice evaluation only (not model features).
    Tenure bands allow us to check model fairness across customer lifecycle stage.
    """
    df = df.copy()
    df[TENURE_BAND_COLUMN] = pd.cut(
        df["customer_tenure_days"],
        bins=[0, 90, 365, 730, float("inf")],
        labels=["<90d", "90d-1yr", "1-2yr", "2yr+"],
    )
    return df


# ---------------------------------------------------------------------------
# Evaluation helpers
# ---------------------------------------------------------------------------

def precision_recall_at_top_k_pct(y_true: np.ndarray, y_score: np.ndarray, pct: float = 0.10):
    """
    Compute precision and recall for the top-pct% of scores.

    This is the primary business metric: NorthStar's retention campaign
    contacts the top 10% highest-risk customers. We want to maximise
    how many true churners are captured in that group.

    Args:
        y_true:  Binary ground-truth labels
        y_score: Predicted churn probabilities
        pct:     Top fraction to evaluate (default 0.10 = top 10%)

    Returns:
        (precision, recall, threshold)
    """
    n = len(y_score)
    k = max(1, int(np.ceil(n * pct)))
    threshold = np.sort(y_score)[::-1][k - 1]
    y_pred = (y_score >= threshold).astype(int)
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    return precision, recall, threshold


def evaluate_model(model: xgb.Booster, X: pd.DataFrame, y: pd.Series) -> dict:
    """
    Compute all Task 1 required metrics on a held-out split.

    Returns dict with: auc_roc, precision_top10, recall_top10, threshold_top10
    """
    dmatrix = xgb.DMatrix(X)
    y_score = model.predict(dmatrix)
    y_true = y.values

    auc_roc = roc_auc_score(y_true, y_score)
    precision, recall, threshold = precision_recall_at_top_k_pct(y_true, y_score, pct=0.10)

    metrics = {
        "auc_roc": float(auc_roc),
        "precision_top10": float(precision),
        "recall_top10": float(recall),
        "threshold_top10": float(threshold),
    }
    logger.info("Evaluation metrics: %s", json.dumps(metrics, indent=2))
    return metrics


def evaluate_slices(
    model: xgb.Booster,
    X: pd.DataFrame,
    y: pd.Series,
    slice_column: str,
    aggregate_metrics: dict,
) -> dict:
    """
    Evaluate model performance for each value of slice_column.

    Flags slices where recall@10% drops more than 10 percentage points
    below the aggregate recall — a signal of potential fairness issues.

    Args:
        model:             Trained XGBoost booster
        X:                 Feature DataFrame (aligned with y)
        y:                 Label series
        slice_column:      Column name to slice on (must be in X.index or passed separately)
        aggregate_metrics: Dict returned by evaluate_model() on the full validation set

    Returns:
        Dict keyed by slice value, each with keys:
          precision_top10, recall_top10, auc_roc, n_samples, flagged
    """
    # Global top-10% threshold from aggregate evaluation ensures comparability across slices.
    # Using a per-slice threshold would hide disparities — we want the same business cutoff.
    global_threshold = aggregate_metrics["threshold_top10"]
    aggregate_recall = aggregate_metrics["recall_top10"]

    slice_values = X[slice_column].unique() if slice_column in X.columns else []
    results = {}

    for val in sorted(slice_values):
        mask = X[slice_column] == val
        if mask.sum() < 30:
            logger.warning("Slice %s=%s has only %d samples — skipping", slice_column, val, mask.sum())
            continue

        X_slice = X[mask].drop(columns=[slice_column], errors="ignore")
        y_slice = y[mask].values

        dmatrix = xgb.DMatrix(X_slice)
        y_score = model.predict(dmatrix)

        y_pred = (y_score >= global_threshold).astype(int)
        precision = precision_score(y_slice, y_pred, zero_division=0)
        recall = recall_score(y_slice, y_pred, zero_division=0)

        # AUC requires at least one positive and one negative sample
        if len(np.unique(y_slice)) < 2:
            slice_auc = float("nan")
        else:
            slice_auc = float(roc_auc_score(y_slice, y_score))

        flagged = recall < (aggregate_recall - 0.10)
        results[str(val)] = {
            "n_samples": int(mask.sum()),
            "precision_top10": float(precision),
            "recall_top10": float(recall),
            "auc_roc": slice_auc,
            "flagged": flagged,
        }

        flag_str = " *** FLAGGED ***" if flagged else ""
        logger.info(
            "Slice %s=%s | n=%d | precision=%.3f | recall=%.3f | auc=%.3f%s",
            slice_column, val, mask.sum(), precision, recall, slice_auc, flag_str,
        )

    return results


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

def plot_feature_importance(model: xgb.Booster, output_dir: str) -> str:
    """
    Save a horizontal bar chart of XGBoost feature importance (gain).

    Gain is used rather than 'weight' (split count) because it measures
    the average improvement in loss brought by each feature — a better
    proxy for predictive value than raw split frequency.
    """
    importance = model.get_score(importance_type="gain")
    sorted_items = sorted(importance.items(), key=lambda x: x[1])
    features, scores = zip(*sorted_items)

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(features, scores, color="steelblue")
    ax.set_xlabel("Gain")
    ax.set_title("XGBoost Feature Importance (Gain)")
    plt.tight_layout()

    path = os.path.join(output_dir, "feature_importance.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    logger.info("Feature importance plot saved to %s", path)
    return path


def plot_confusion_matrix(model: xgb.Booster, X: pd.DataFrame, y: pd.Series,
                          threshold: float, output_dir: str) -> str:
    """Save confusion matrix at the top-10% threshold."""
    dmatrix = xgb.DMatrix(X)
    y_score = model.predict(dmatrix)
    y_pred = (y_score >= threshold).astype(int)

    cm = confusion_matrix(y.values, y_pred)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=["Retained", "Churned"])
    fig, ax = plt.subplots(figsize=(5, 4))
    disp.plot(ax=ax, colorbar=False, cmap="Blues")
    ax.set_title(f"Confusion Matrix (threshold = {threshold:.3f})")
    plt.tight_layout()

    path = os.path.join(output_dir, "confusion_matrix.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    logger.info("Confusion matrix saved to %s", path)
    return path


def plot_roc_curve(model: xgb.Booster, X: pd.DataFrame, y: pd.Series, output_dir: str) -> str:
    """Save ROC curve plot."""
    dmatrix = xgb.DMatrix(X)
    y_score = model.predict(dmatrix)
    fpr, tpr, _ = roc_curve(y.values, y_score)
    roc_auc = auc(fpr, tpr)

    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(fpr, tpr, label=f"AUC = {roc_auc:.3f}", color="steelblue")
    ax.plot([0, 1], [0, 1], "k--", linewidth=0.8)
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title("ROC Curve — NorthStar Churn Model")
    ax.legend(loc="lower right")
    plt.tight_layout()

    path = os.path.join(output_dir, "roc_curve.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    logger.info("ROC curve saved to %s", path)
    return path


# ---------------------------------------------------------------------------
# Model registration
# ---------------------------------------------------------------------------

def _tar_model(model_path: str, tar_path: str) -> str:
    """
    Package the XGBoost model file into model.tar.gz.
    SageMaker Model Registry expects a .tar.gz archive at the S3 model data URI.
    """
    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(model_path, arcname="xgboost-model")
    logger.info("Model archived to %s", tar_path)
    return tar_path


def save_and_register_model(
    model: xgb.Booster,
    metrics: dict,
    slice_results: dict,
    args: argparse.Namespace,
    output_dir: str,
) -> str:
    """
    Persist the trained model, upload to S3, and register in Model Registry.

    Registration flow:
      1. Save XGBoost model binary locally
      2. Package into model.tar.gz (SageMaker convention)
      3. Upload to S3 under artifacts_bucket/models/<timestamp>/
      4. Create a ModelPackage in a ModelPackageGroup with approval status
         "PendingManualApproval" — a human reviewer must approve before deployment

    Customer metadata stored in the registry entry:
      - All evaluation metrics (AUC, precision@10%, recall@10%)
      - Training data S3 URI and date range
      - Git commit SHA (for reproducibility)
      - Slice evaluation summary (flagged tiers)
    """
    sm_client = boto3.client("sagemaker", region_name="us-east-1")
    s3_client = boto3.client("s3", region_name="us-east-1")

    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")

    # 1. Save model locally
    local_model_path = os.path.join(output_dir, "xgboost-model")
    model.save_model(local_model_path)

    # 2. Package into tar.gz
    local_tar_path = os.path.join(output_dir, "model.tar.gz")
    _tar_model(local_model_path, local_tar_path)

    # 3. Upload to S3
    s3_model_key = f"models/{timestamp}/model.tar.gz"
    logger.info("Uploading model to s3://%s/%s", args.artifacts_bucket, s3_model_key)
    s3_client.upload_file(local_tar_path, args.artifacts_bucket, s3_model_key)
    model_data_url = f"s3://{args.artifacts_bucket}/{s3_model_key}"

    # 4. Retrieve XGBoost container image URI
    import sagemaker
    image_uri = sagemaker.image_uris.retrieve(
        framework="xgboost",
        region="us-east-1",
        version="1.7-1",
    )

    # Ensure the ModelPackageGroup exists (idempotent)
    model_package_group_name = "northstar-churn-models"
    try:
        sm_client.create_model_package_group(
            ModelPackageGroupName=model_package_group_name,
            ModelPackageGroupDescription="NorthStar churn prediction models",
        )
        logger.info("Created ModelPackageGroup: %s", model_package_group_name)
    except sm_client.exceptions.ResourceInUse:
        logger.info("ModelPackageGroup already exists: %s", model_package_group_name)

    # Collect flagged tiers for metadata
    flagged_tiers = [k for k, v in slice_results.get("loyalty_tier", {}).items() if v.get("flagged")]

    commit_sha = os.environ.get("GIT_COMMIT_SHA", "unknown")

    # 5. Register the model package
    response = sm_client.create_model_package(
        ModelPackageGroupName=model_package_group_name,
        ModelPackageDescription=f"XGBoost churn model trained on {args.start_date} to {args.end_date}",
        InferenceSpecification={
            "Containers": [
                {
                    "Image": image_uri,
                    "ModelDataUrl": model_data_url,
                    "Framework": "XGBOOST",
                    "FrameworkVersion": "1.7-1",
                }
            ],
            "SupportedContentTypes": ["text/csv"],
            "SupportedResponseMIMETypes": ["text/csv"],
            "SupportedTransformInstanceTypes": ["ml.m5.xlarge"],
            "SupportedRealtimeInferenceInstanceTypes": ["ml.m5.large"],
        },
        ModelApprovalStatus="PendingManualApproval",
        ModelMetrics={
            "ModelQuality": {
                "Statistics": {
                    "ContentType": "application/json",
                    "S3Uri": f"s3://{args.artifacts_bucket}/models/{timestamp}/metrics.json",
                }
            }
        },
        CustomerMetadataProperties={
            "auc_roc": str(round(metrics["auc_roc"], 4)),
            "precision_top10": str(round(metrics["precision_top10"], 4)),
            "recall_top10": str(round(metrics["recall_top10"], 4)),
            "training_data_uri": f"s3://{args.artifacts_bucket}/athena-results/",
            "training_start_date": args.start_date,
            "training_end_date": args.end_date,
            "commit_sha": commit_sha,
            "flagged_tiers": json.dumps(flagged_tiers),
            "feature_group": args.feature_group_name,
        },
    )

    model_package_arn = response["ModelPackageArn"]
    logger.info("Model registered. ARN: %s", model_package_arn)

    # Upload metrics JSON to S3 for ModelMetrics reference
    metrics_with_slices = {"aggregate": metrics, "slices": slice_results}
    metrics_json = json.dumps(metrics_with_slices, indent=2)
    s3_client.put_object(
        Bucket=args.artifacts_bucket,
        Key=f"models/{timestamp}/metrics.json",
        Body=metrics_json.encode("utf-8"),
        ContentType="application/json",
    )

    return model_package_arn


# ---------------------------------------------------------------------------
# Main training routine
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="NorthStar Churn Model Training")

    # Data
    parser.add_argument("--feature-group-name", default="northstar-churn-features",
                        help="SageMaker Feature Group name")
    parser.add_argument("--start-date", default="2025-01-01",
                        help="Training data start date (ISO format)")
    parser.add_argument("--end-date", default="2025-12-31",
                        help="Training data end date (ISO format)")
    parser.add_argument("--artifacts-bucket", default=os.environ.get("ARTIFACTS_BUCKET", "northstar-dev-artifacts"),
                        help="S3 bucket for model artifacts")
    parser.add_argument("--register-model", action="store_true",
                        help="Register model in SageMaker Model Registry after training")

    # SageMaker training job paths (set automatically when running as a training job)
    parser.add_argument("--model-dir", default=os.environ.get("SM_MODEL_DIR", "/opt/ml/model"),
                        help="Output directory for model artifacts")
    parser.add_argument("--output-data-dir", default=os.environ.get("SM_OUTPUT_DATA_DIR", "/opt/ml/output/data"),
                        help="Output directory for evaluation artifacts (plots, metrics)")

    # Hyperparameters
    parser.add_argument("--max-depth", type=int, default=6)
    parser.add_argument("--eta", type=float, default=0.1)
    parser.add_argument("--n-estimators", type=int, default=300)
    parser.add_argument("--subsample", type=float, default=0.8)
    parser.add_argument("--colsample-bytree", type=float, default=0.8)
    parser.add_argument("--min-child-weight", type=int, default=5)
    parser.add_argument("--scale-pos-weight", type=float, default=3.0,
                        help="Controls class imbalance. NorthStar churn rate ~25%%; default=3 approximates neg/pos ratio")
    parser.add_argument("--eval-fraction", type=float, default=0.20,
                        help="Fraction of data held out for validation (temporal split)")
    parser.add_argument("--random-seed", type=int, default=42)
    parser.add_argument("--early-stopping-rounds", type=int, default=20)

    return parser.parse_args()


def train(args: argparse.Namespace) -> None:
    """
    End-to-end training pipeline:
      1. Load from Feature Store
      2. Add derived columns for slicing
      3. Temporal train/val split (important: random split would leak future signal)
      4. Train XGBoost with early stopping
      5. Evaluate global metrics + loyalty_tier and tenure_band slices
      6. Save plots to output_data_dir
      7. Optionally register in Model Registry
    """
    from sagemaker.experiments.run import Run

    os.makedirs(args.model_dir, exist_ok=True)
    os.makedirs(args.output_data_dir, exist_ok=True)

    # ---- 1. Load data ----
    logger.info("Loading features from Feature Store: %s", args.feature_group_name)
    df = load_features_from_feature_store(args.feature_group_name, args.start_date, args.end_date)
    df = add_derived_columns(df)

    # ---- 2. Split ----
    # Sort by customer_tenure_days as a proxy for time — newer customers at the end.
    # This prevents the model from seeing future customers' behaviour during training.
    df = df.sort_values("customer_tenure_days")
    split_idx = int(len(df) * (1 - args.eval_fraction))
    train_df = df.iloc[:split_idx].copy()
    val_df = df.iloc[split_idx:].copy()
    logger.info("Train: %d rows | Val: %d rows", len(train_df), len(val_df))

    # Retain slice columns separately before dropping from feature matrices
    val_loyalty = val_df[LOYALTY_TIER_COLUMN].copy() if LOYALTY_TIER_COLUMN in val_df.columns else None
    val_tenure_band = val_df[TENURE_BAND_COLUMN].copy() if TENURE_BAND_COLUMN in val_df.columns else None

    drop_cols = [LABEL_COLUMN, "customer_id", LOYALTY_TIER_COLUMN, TENURE_BAND_COLUMN]
    X_train = train_df.drop(columns=drop_cols, errors="ignore")[FEATURE_COLUMNS]
    y_train = train_df[LABEL_COLUMN]
    X_val = val_df.drop(columns=drop_cols, errors="ignore")[FEATURE_COLUMNS]
    y_val = val_df[LABEL_COLUMN]

    dtrain = xgb.DMatrix(X_train, label=y_train, feature_names=FEATURE_COLUMNS)
    dval = xgb.DMatrix(X_val, label=y_val, feature_names=FEATURE_COLUMNS)

    params = {
        "max_depth": args.max_depth,
        "eta": args.eta,
        "subsample": args.subsample,
        "colsample_bytree": args.colsample_bytree,
        "min_child_weight": args.min_child_weight,
        "scale_pos_weight": args.scale_pos_weight,
        "objective": "binary:logistic",
        "eval_metric": ["logloss", "auc"],
        "seed": args.random_seed,
    }

    run_name = f"run-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"

    # ---- 3. Train with SageMaker Experiments tracking ----
    with Run(
        experiment_name="northstar-churn-experiment",
        run_name=run_name,
    ) as run:
        run.log_parameters({
            "max_depth": args.max_depth,
            "eta": args.eta,
            "n_estimators": args.n_estimators,
            "subsample": args.subsample,
            "colsample_bytree": args.colsample_bytree,
            "min_child_weight": args.min_child_weight,
            "scale_pos_weight": args.scale_pos_weight,
            "early_stopping_rounds": args.early_stopping_rounds,
            "eval_fraction": args.eval_fraction,
            "feature_group": args.feature_group_name,
            "start_date": args.start_date,
            "end_date": args.end_date,
        })

        logger.info("Training XGBoost model with params: %s", json.dumps(params, indent=2))
        evals_result = {}
        model = xgb.train(
            params=params,
            dtrain=dtrain,
            num_boost_round=args.n_estimators,
            evals=[(dtrain, "train"), (dval, "val")],
            early_stopping_rounds=args.early_stopping_rounds,
            evals_result=evals_result,
            verbose_eval=50,
        )
        logger.info("Best iteration: %d", model.best_iteration)

        # ---- 4. Evaluate global metrics ----
        metrics = evaluate_model(model, X_val, y_val)

        run.log_metrics({
            "auc_roc": metrics["auc_roc"],
            "precision_top10": metrics["precision_top10"],
            "recall_top10": metrics["recall_top10"],
            "best_iteration": model.best_iteration,
        })

        # ---- 5. Slice evaluation ----
        slice_results = {}

        if val_loyalty is not None:
            X_val_with_tier = X_val.copy()
            X_val_with_tier[LOYALTY_TIER_COLUMN] = val_loyalty.values
            logger.info("=== Slice evaluation: loyalty_tier ===")
            loyalty_slices = evaluate_slices(
                model, X_val_with_tier, y_val, LOYALTY_TIER_COLUMN, metrics
            )
            slice_results["loyalty_tier"] = loyalty_slices

        if val_tenure_band is not None:
            X_val_with_tenure = X_val.copy()
            X_val_with_tenure[TENURE_BAND_COLUMN] = val_tenure_band.values
            logger.info("=== Slice evaluation: tenure_band ===")
            tenure_slices = evaluate_slices(
                model, X_val_with_tenure, y_val, TENURE_BAND_COLUMN, metrics
            )
            slice_results["tenure_band"] = tenure_slices

        # ---- 6. Save plots ----
        plot_feature_importance(model, args.output_data_dir)
        plot_confusion_matrix(model, X_val, y_val, metrics["threshold_top10"], args.output_data_dir)
        plot_roc_curve(model, X_val, y_val, args.output_data_dir)

        # Save metrics JSON locally (also uploaded to S3 during registration)
        metrics_path = os.path.join(args.output_data_dir, "metrics.json")
        with open(metrics_path, "w") as f:
            json.dump({"aggregate": metrics, "slices": slice_results}, f, indent=2)

        run.log_file(metrics_path, name="metrics.json", is_output=True)

    # ---- 7. Register model ----
    if args.register_model:
        model_package_arn = save_and_register_model(model, metrics, slice_results, args, args.model_dir)
        logger.info("Model registered with ARN: %s", model_package_arn)
    else:
        # Still save the model binary for local use / SageMaker artifact collection
        model_path = os.path.join(args.model_dir, "xgboost-model")
        model.save_model(model_path)
        logger.info("Model saved to %s (not registered)", model_path)

    # Print summary for student readability
    print("\n" + "=" * 60)
    print("TRAINING COMPLETE")
    print("=" * 60)
    print(f"  AUC-ROC:              {metrics['auc_roc']:.4f}")
    print(f"  Precision @ top 10%:  {metrics['precision_top10']:.4f}")
    print(f"  Recall @ top 10%:     {metrics['recall_top10']:.4f}")
    print(f"  Best iteration:       {model.best_iteration}")
    if slice_results:
        for dim, slices in slice_results.items():
            flagged = [k for k, v in slices.items() if v.get("flagged")]
            if flagged:
                print(f"\n  *** FLAGGED slices ({dim}): {flagged} ***")
            else:
                print(f"\n  All {dim} slices within acceptable recall range.")
    print("=" * 60 + "\n")


# ---------------------------------------------------------------------------
# SageMaker Estimator launcher (called from launch_training.py)
# ---------------------------------------------------------------------------

def launch_training_job(
    feature_group_name: str,
    artifacts_bucket: str,
    role_arn: str,
    hyperparams: dict,
) -> "sagemaker.xgboost.XGBoost":
    """
    Launch a SageMaker managed Training Job using the XGBoost container.

    This function is called from launch_training.py (local terminal) or from
    a pipeline step. It does NOT run inside the training container — it submits
    the job to SageMaker and waits for completion.

    Args:
        feature_group_name: Feature Group to query
        artifacts_bucket:   S3 bucket for model artifacts and Athena results
        role_arn:           IAM role ARN with SageMaker + S3 + Feature Store permissions
        hyperparams:        Dict of hyperparameter name → value (strings)

    Returns:
        Fitted XGBoost Estimator object (use .model_data to get S3 model URI)
    """
    from sagemaker.xgboost import XGBoost

    # Resolve script directory so SageMaker can package the source
    source_dir = str(Path(__file__).parent)

    estimator = XGBoost(
        entry_point="train.py",
        source_dir=source_dir,
        role=role_arn,
        instance_count=1,
        instance_type="ml.m5.xlarge",
        framework_version="1.7-1",
        py_version="py3",
        output_path=f"s3://{artifacts_bucket}/models/",
        hyperparameters={
            "feature-group-name": feature_group_name,
            "artifacts-bucket": artifacts_bucket,
            "register-model": "true",
            **hyperparams,
        },
        enable_sagemaker_metrics=True,
        metric_definitions=[
            {"Name": "validation:auc", "Regex": r"val-auc:([\d\.]+)"},
            {"Name": "validation:logloss", "Regex": r"val-logloss:([\d\.]+)"},
        ],
        environment={
            "ARTIFACTS_BUCKET": artifacts_bucket,
        },
    )

    # No input channels — data is loaded from Feature Store inside the container
    estimator.fit(wait=True)
    logger.info("Training job complete. Model data: %s", estimator.model_data)
    return estimator


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    args = parse_args()
    train(args)
