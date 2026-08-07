"""
NorthStar Retail — Model Evaluation Tests
Tests the churn prediction model against quality thresholds.

Run: pytest tests/test_model.py -v
"""

import os
import json
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

# ---------------------------------------------------------------------------
# Path / registry constants — override via environment variables in CI
# ---------------------------------------------------------------------------
MODEL_PATH = os.environ.get("NORTHSTAR_MODEL_PATH", "./model/model.xgb")
METRICS_PATH = os.environ.get("NORTHSTAR_METRICS_PATH", "./output/evaluation_metrics.json")
CHAMPION_MODEL_REGISTRY_GROUP = "northstar-churn-model-group"

# Quality gate thresholds (mirrors values in sagemaker_pipeline.py)
AUC_ROC_THRESHOLD = 0.72
PRECISION_TOP10_THRESHOLD = 0.40
RECALL_TOP10_THRESHOLD = 0.35
BASELINE_IMPROVEMENT_MIN = 0.05    # Must beat predict-mean baseline by >= 5 AUC points
REGRESSION_TOLERANCE = 0.02        # New model AUC may not drop > 2 points below champion

# Synthetic validation set dimensions (used when no real data is available)
SYNTHETIC_N_SAMPLES = 100
SYNTHETIC_N_FEATURES = 12          # Matches the 12-feature churn model input schema

# ---------------------------------------------------------------------------
# Module-scoped fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def trained_model():
    """Load the trained XGBoost model from MODEL_PATH."""
    try:
        import xgboost as xgb
    except ImportError:
        pytest.skip("xgboost not installed — pip install xgboost")

    path = Path(MODEL_PATH)
    if not path.exists():
        pytest.skip(f"Model not found at {path} — train first or set NORTHSTAR_MODEL_PATH")

    model = xgb.Booster()
    model.load_model(str(path))
    return model


@pytest.fixture(scope="module")
def evaluation_metrics():
    """
    Load saved evaluation metrics JSON written by the evaluate.py script.
    Expected schema:
        {
            "auc_roc": 0.7531,
            "precision_top10": 0.4280,
            "recall_top10": 0.3710,
            "auc_vs_baseline": 0.0931
        }
    """
    path = Path(METRICS_PATH)
    if not path.exists():
        pytest.skip(
            f"Metrics not found at {path}. "
            f"Run evaluate.py or set NORTHSTAR_METRICS_PATH."
        )
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def validation_data():
    """
    Provide a small validation dataset for shape tests.
    In CI: reads from the actual held-out validation split.
    Locally: generates a synthetic dataset so shape tests can run without real data.
    """
    validation_path = os.environ.get("NORTHSTAR_VALIDATION_PATH", "")
    if validation_path and Path(validation_path).exists():
        df = pd.read_parquet(validation_path)
        label_col = "churn_label"
        feature_cols = [c for c in df.columns if c != label_col]
        return df[feature_cols].values, df[label_col].values

    # Fallback: synthetic data that mirrors the 12-feature input schema
    rng = np.random.default_rng(seed=42)
    X = rng.standard_normal((SYNTHETIC_N_SAMPLES, SYNTHETIC_N_FEATURES))
    y = (X[:, 0] > 0).astype(int)
    return X, y


# ---------------------------------------------------------------------------
# Threshold tests
# ---------------------------------------------------------------------------

class TestModelThresholds:
    """Verify the trained model meets the NorthStar quality gates."""

    def test_auc_roc_meets_threshold(self, evaluation_metrics):
        """AUC-ROC must be >= 0.72 (defined in project SLA)."""
        auc = evaluation_metrics.get("auc_roc", 0.0)
        assert auc >= AUC_ROC_THRESHOLD, (
            f"AUC-ROC {auc:.4f} < {AUC_ROC_THRESHOLD} threshold. "
            f"Review hyperparameters or check for label leakage."
        )

    def test_precision_top10_meets_threshold(self, evaluation_metrics):
        """Precision@Top10% must be >= 0.40."""
        prec = evaluation_metrics.get("precision_top10", 0.0)
        assert prec >= PRECISION_TOP10_THRESHOLD, (
            f"Precision@Top10 {prec:.4f} < {PRECISION_TOP10_THRESHOLD} threshold. "
            f"Model is over-predicting churn — check class_weight/scale_pos_weight."
        )

    def test_recall_top10_meets_threshold(self, evaluation_metrics):
        """Recall@Top10% must be >= 0.35."""
        recall = evaluation_metrics.get("recall_top10", 0.0)
        assert recall >= RECALL_TOP10_THRESHOLD, (
            f"Recall@Top10 {recall:.4f} < {RECALL_TOP10_THRESHOLD} threshold. "
            f"Model is missing too many churners in the top decile."
        )

    def test_beats_baseline_by_5_points(self, evaluation_metrics):
        """
        Model must beat the predict-mean (majority class) baseline by >= 0.05 AUC points.
        A model that barely improves on predict-all-zeros is not deployable.
        """
        diff = evaluation_metrics.get("auc_vs_baseline", 0.0)
        assert diff >= BASELINE_IMPROVEMENT_MIN, (
            f"AUC vs baseline {diff:.4f} < {BASELINE_IMPROVEMENT_MIN} minimum improvement. "
            f"The model may be collapsing to majority-class predictions."
        )

    def test_metrics_keys_are_present(self, evaluation_metrics):
        """
        Sanity check: all expected keys must exist in the metrics JSON.
        Missing keys indicate the evaluation script did not run to completion.
        """
        required_keys = {"auc_roc", "precision_top10", "recall_top10", "auc_vs_baseline"}
        missing = required_keys - set(evaluation_metrics.keys())
        assert not missing, (
            f"evaluation_metrics.json is missing keys: {missing}. "
            f"Check that evaluate.py ran successfully."
        )


# ---------------------------------------------------------------------------
# Shape / type tests
# ---------------------------------------------------------------------------

class TestModelShapes:
    """Verify the model's output format is correct regardless of threshold pass/fail."""

    def test_predictions_are_probabilities(self, trained_model, validation_data):
        """
        All predictions must be probabilities in [0.0, 1.0].
        Values outside this range indicate a misconfigured objective function.
        """
        import xgboost as xgb
        X, y = validation_data
        dmat = xgb.DMatrix(X)
        preds = trained_model.predict(dmat)
        assert preds.min() >= 0.0, (
            f"Negative prediction probability found: min={preds.min():.6f}. "
            f"Ensure objective='binary:logistic' or apply sigmoid post-processing."
        )
        assert preds.max() <= 1.0, (
            f"Prediction probability > 1.0 found: max={preds.max():.6f}."
        )

    def test_output_shape_matches_input(self, trained_model, validation_data):
        """
        The model must return exactly one score per input row.
        Shape mismatch indicates a batch-level inference bug.
        """
        import xgboost as xgb
        X, y = validation_data
        dmat = xgb.DMatrix(X)
        preds = trained_model.predict(dmat)
        assert len(preds) == len(X), (
            f"Output length {len(preds)} != input length {len(X)}. "
            f"Output shape mismatch in model.predict()."
        )

    def test_predictions_are_not_all_identical(self, trained_model, validation_data):
        """
        The model must produce differentiated scores (not all the same probability).
        All-identical predictions indicate model collapse or incorrect feature input.
        """
        import xgboost as xgb
        X, y = validation_data
        dmat = xgb.DMatrix(X)
        preds = trained_model.predict(dmat)
        unique_preds = np.unique(np.round(preds, 4))
        assert len(unique_preds) > 1, (
            f"Model produced {len(unique_preds)} unique probability value(s). "
            f"All predictions are identical — model has collapsed."
        )

    def test_model_accepts_12_features(self, trained_model):
        """
        The trained model must accept exactly 12 input features
        matching the churn model schema. Feature count mismatch
        would cause silent errors at inference time.
        """
        import xgboost as xgb
        rng = np.random.default_rng(seed=0)
        X = rng.standard_normal((5, SYNTHETIC_N_FEATURES))
        dmat = xgb.DMatrix(X)
        # Should not raise; if feature count is wrong, XGBoost logs a warning
        preds = trained_model.predict(dmat)
        assert len(preds) == 5


# ---------------------------------------------------------------------------
# Regression gate
# ---------------------------------------------------------------------------

class TestRegressionGate:
    """
    Compare the new model against the current champion in SageMaker Model Registry.
    Skips gracefully when AWS credentials are not available (local dev).
    """

    def test_new_model_doesnt_regress_from_champion(self, evaluation_metrics):
        """
        Regression gate: new model AUC must be >= (champion AUC - 0.02).

        The champion AUC is retrieved from SageMaker Model Registry metadata.
        If no approved champion exists, the test skips (bootstrapping case).
        If AWS is unreachable, the test skips (local dev case).

        Failing this test means the new model is materially worse than the
        current production model — it must not be promoted.
        """
        import boto3

        new_auc = evaluation_metrics.get("auc_roc", 0.0)

        try:
            sm = boto3.client("sagemaker", region_name="us-east-1")
            packages = sm.list_model_packages(
                ModelPackageGroupName=CHAMPION_MODEL_REGISTRY_GROUP,
                ModelApprovalStatus="Approved",
                SortBy="CreationTime",
                SortOrder="Descending",
                MaxResults=1,
            )

            if not packages["ModelPackageSummaryList"]:
                pytest.skip(
                    "No approved champion model in registry — skipping regression gate "
                    "(this is expected on first deploy)."
                )

            champion_arn = packages["ModelPackageSummaryList"][0]["ModelPackageArn"]
            champion_desc = sm.describe_model_package(ModelPackageName=champion_arn)
            champion_auc = float(
                champion_desc
                .get("CustomerMetadataProperties", {})
                .get("auc_roc", "0.0")
            )

            min_acceptable = champion_auc - REGRESSION_TOLERANCE
            assert new_auc >= min_acceptable, (
                f"REGRESSION DETECTED: New model AUC {new_auc:.4f} regresses from "
                f"champion AUC {champion_auc:.4f} by more than {REGRESSION_TOLERANCE}. "
                f"Minimum acceptable AUC: {min_acceptable:.4f}. "
                f"Do NOT promote this model without a root-cause analysis."
            )

        except Exception as e:
            err_type = type(e).__name__
            skip_signals = (
                "NoCredentialsError",
                "EndpointConnectionError",
                "ClientError",
                "BotoCoreError",
            )
            if any(sig in err_type for sig in skip_signals):
                pytest.skip(f"AWS not available ({err_type}): {e}")
            raise
