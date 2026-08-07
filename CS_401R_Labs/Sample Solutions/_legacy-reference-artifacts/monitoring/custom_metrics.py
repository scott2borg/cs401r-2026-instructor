"""
NorthStar Retail — Custom Business Metrics Publisher
=====================================================
Publishes the business layer (Layer 5) metrics to CloudWatch after each nightly
Batch Transform completes.

Metrics published to namespace NorthStar/Business:
  - DailyChurnAlertsGenerated:  Count of customers with churn_probability >= 0.60.
                                 Drives daily retention team capacity planning.
  - ChurnProbabilityMean:       Mean churn score across all scored customers.
                                 Drift in this metric is an early concept drift signal.
  - ChurnProbabilityStdDev:     Standard deviation of churn scores.
                                 A collapsing std dev indicates the model is "hedging"
                                 (all scores converging to the mean — a failure mode).
  - HighRiskCustomerCount:      Customers with churn_probability >= 0.80.
                                 Input to executive reporting and budget decisions.

All metrics include a RunDate dimension for time-series lookup and anomaly detection.
The NorthStar/Business CloudWatch alarm uses DailyChurnAlertsGenerated with
anomaly detection band to catch unexpected volume changes.

Called by:
  deployment/configs/canary_deploy.py — after each Batch Transform completes.
  Can also be run standalone:
    python custom_metrics.py --scores-s3-uri s3://bucket/predictions/churn/2026/07/06/output.csv.out

Dependencies:
  boto3, numpy, pandas
"""

import argparse
import io
import logging
import sys
from datetime import datetime, timezone
from typing import Optional

import boto3
import numpy as np
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

NAMESPACE = "NorthStar/Business"
CHURN_ALERT_THRESHOLD = 0.60   # Customers above this are flagged for retention outreach
HIGH_RISK_THRESHOLD = 0.80     # Customers above this receive priority retention offers
REGION = "us-east-1"


# ─────────────────────────────────────────────────────────────
# Core metric publisher
# ─────────────────────────────────────────────────────────────

def publish_churn_metrics(
    scores_df: pd.DataFrame,
    run_date: Optional[str] = None,
    region: str = REGION,
    dry_run: bool = False,
) -> dict:
    """
    Compute churn business metrics and publish them to CloudWatch.

    Args:
        scores_df: DataFrame with at minimum a 'churn_probability' column (float, [0,1]).
                   Optional: 'customer_id' column (used for logging, not published).
        run_date:  ISO 8601 date string (e.g., "2026-07-06"). Defaults to today UTC.
                   Used as the RunDate CloudWatch dimension — allows querying metrics
                   for a specific batch run.
        region:    AWS region for CloudWatch (default: us-east-1).
        dry_run:   If True, compute and log metrics but do not publish to CloudWatch.
                   Use in unit tests and CI validation.

    Returns:
        dict with computed metric values:
          - alerts_count (int): Customers with churn_prob >= CHURN_ALERT_THRESHOLD
          - high_risk_count (int): Customers with churn_prob >= HIGH_RISK_THRESHOLD
          - mean_probability (float): Mean churn probability
          - std_probability (float): Std dev of churn probabilities
          - total_customers (int): Total customers scored
          - run_date (str): ISO date string
          - published (bool): True if metrics were sent to CloudWatch

    Raises:
        ValueError: If scores_df is empty or missing 'churn_probability' column.
        boto3.ClientError: If CloudWatch PutMetricData call fails (propagated to caller).
    """
    if scores_df.empty:
        raise ValueError("scores_df is empty — no customers to compute metrics for.")
    if "churn_probability" not in scores_df.columns:
        raise ValueError(
            f"scores_df missing 'churn_probability' column. "
            f"Available columns: {list(scores_df.columns)}"
        )

    run_date = run_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    probs = scores_df["churn_probability"].values.astype(np.float64)

    # Validate score range — scores outside [0,1] indicate a model output format problem
    out_of_range = np.sum((probs < 0.0) | (probs > 1.0))
    if out_of_range > 0:
        logger.warning(
            "%d scores are outside [0, 1] range. This indicates a model output format "
            "issue — check the Batch Transform output file format. Clamping for metric "
            "computation but this should be investigated.",
            out_of_range,
        )
        probs = np.clip(probs, 0.0, 1.0)

    # Compute metrics
    alerts_count = int((probs >= CHURN_ALERT_THRESHOLD).sum())
    high_risk_count = int((probs >= HIGH_RISK_THRESHOLD).sum())
    mean_probability = float(np.mean(probs))
    std_probability = float(np.std(probs))
    total_customers = len(probs)

    result = {
        "alerts_count": alerts_count,
        "high_risk_count": high_risk_count,
        "mean_probability": round(mean_probability, 6),
        "std_probability": round(std_probability, 6),
        "total_customers": total_customers,
        "run_date": run_date,
        "published": False,
    }

    logger.info(
        "Computed business metrics | run_date=%s total=%d alerts=%d (%.1f%%) "
        "high_risk=%d (%.1f%%) mean=%.4f std=%.4f",
        run_date,
        total_customers,
        alerts_count,
        100.0 * alerts_count / total_customers if total_customers > 0 else 0,
        high_risk_count,
        100.0 * high_risk_count / total_customers if total_customers > 0 else 0,
        mean_probability,
        std_probability,
    )

    # Sanity check before publishing: implausible spike detection
    high_risk_fraction = high_risk_count / total_customers if total_customers > 0 else 0
    if high_risk_fraction > 0.15:
        logger.warning(
            "IMPLAUSIBLE SPIKE DETECTED: %.1f%% of customers scored > %.0f%%. "
            "Historical baseline is 2-5%%. Publishing metrics but also logging warning "
            "metric. Investigate model output before using these scores for offers.",
            100.0 * high_risk_fraction,
            100.0 * HIGH_RISK_THRESHOLD,
        )

    if dry_run:
        logger.info("[DRY RUN] Metrics computed but not published to CloudWatch.")
        return result

    # Build CloudWatch MetricData payload
    timestamp = datetime.now(timezone.utc)
    dimensions = [{"Name": "RunDate", "Value": run_date}]

    metric_data = [
        {
            "MetricName": "DailyChurnAlertsGenerated",
            "Value": float(alerts_count),
            "Unit": "Count",
            "Dimensions": dimensions,
            "Timestamp": timestamp,
        },
        {
            "MetricName": "ChurnProbabilityMean",
            "Value": mean_probability,
            "Unit": "None",
            "Dimensions": dimensions,
            "Timestamp": timestamp,
        },
        {
            "MetricName": "ChurnProbabilityStdDev",
            "Value": std_probability,
            "Unit": "None",
            "Dimensions": dimensions,
            "Timestamp": timestamp,
        },
        {
            "MetricName": "HighRiskCustomerCount",
            "Value": float(high_risk_count),
            "Unit": "Count",
            "Dimensions": dimensions,
            "Timestamp": timestamp,
        },
        {
            "MetricName": "TotalCustomersScored",
            "Value": float(total_customers),
            "Unit": "Count",
            "Dimensions": dimensions,
            "Timestamp": timestamp,
        },
    ]

    # Add implausible spike indicator metric
    metric_data.append({
        "MetricName": "ImplausibleSpikeDetected",
        "Value": 1.0 if high_risk_fraction > 0.15 else 0.0,
        "Unit": "Count",
        "Dimensions": dimensions,
        "Timestamp": timestamp,
    })

    cw = boto3.client("cloudwatch", region_name=region)
    # CloudWatch PutMetricData accepts up to 20 metrics per call
    for i in range(0, len(metric_data), 20):
        batch = metric_data[i:i + 20]
        cw.put_metric_data(Namespace=NAMESPACE, MetricData=batch)

    result["published"] = True
    logger.info("Published %d metrics to CloudWatch namespace '%s'", len(metric_data), NAMESPACE)
    return result


# ─────────────────────────────────────────────────────────────
# S3 loader
# ─────────────────────────────────────────────────────────────

def load_scores_from_s3(s3_uri: str, region: str = REGION) -> pd.DataFrame:
    """
    Load churn prediction scores from S3 (Batch Transform output).

    Supports two output formats from SageMaker Batch Transform:
      1. Plain float: one score per line (e.g., "0.7823")
      2. CSV with header: "customer_id,churn_probability" + data rows

    Args:
        s3_uri: S3 URI of the Batch Transform output file or prefix.
                Examples:
                  s3://northstar-artifacts/predictions/churn/2026/07/06/output.csv.out
                  s3://northstar-artifacts/predictions/churn/2026/07/06/
        region: AWS region (default: us-east-1).

    Returns:
        DataFrame with at least a 'churn_probability' column.
        If the input is plain floats, 'customer_id' column will not be present.

    Raises:
        ValueError: If no .out files found at the given S3 URI.
        RuntimeError: If the output format cannot be parsed.
    """
    s3 = boto3.client("s3", region_name=region)
    without_scheme = s3_uri.replace("s3://", "")
    bucket, _, prefix = without_scheme.partition("/")

    # Collect all .out files under the prefix
    paginator = s3.get_paginator("list_objects_v2")
    out_keys = []
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            if obj["Key"].endswith(".out") or obj["Key"].endswith(".csv"):
                out_keys.append(obj["Key"])

    if not out_keys:
        raise ValueError(
            f"No output files (.out or .csv) found at s3://{bucket}/{prefix}. "
            "Check that the Batch Transform job completed successfully."
        )

    frames = []
    for key in out_keys:
        body = s3.get_object(Bucket=bucket, Key=key)["Body"].read().decode("utf-8")
        lines = [line.strip() for line in body.strip().splitlines() if line.strip()]

        if not lines:
            logger.warning("Empty output file: s3://%s/%s", bucket, key)
            continue

        # Detect format: CSV with header vs. plain floats
        if "," in lines[0] and not _is_float(lines[0]):
            # CSV format: header row present
            df = pd.read_csv(io.StringIO(body))
            if "churn_probability" not in df.columns:
                # Try to find a float column
                float_cols = [c for c in df.columns if _is_float_series(df[c])]
                if not float_cols:
                    raise RuntimeError(
                        f"Cannot find churn_probability column in {key}. "
                        f"Columns: {list(df.columns)}"
                    )
                df = df.rename(columns={float_cols[-1]: "churn_probability"})
        else:
            # Plain float format: one score per line
            scores = []
            for line in lines:
                try:
                    scores.append(float(line.split(",")[-1]))
                except ValueError:
                    pass  # Skip unparseable lines (headers, empty lines)
            df = pd.DataFrame({"churn_probability": scores})

        frames.append(df)
        logger.info("Loaded %d scores from s3://%s/%s", len(df), bucket, key)

    if not frames:
        raise ValueError(f"No parseable score data found at {s3_uri}")

    combined = pd.concat(frames, ignore_index=True)
    logger.info("Total scores loaded: %d", len(combined))
    return combined


def _is_float(s: str) -> bool:
    """Return True if string can be parsed as a float."""
    try:
        float(s)
        return True
    except ValueError:
        return False


def _is_float_series(series: pd.Series) -> bool:
    """Return True if pandas Series contains numeric data."""
    return pd.api.types.is_numeric_dtype(series)


# ─────────────────────────────────────────────────────────────
# Entrypoint
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Publish NorthStar churn business metrics to CloudWatch after Batch Transform."
    )
    parser.add_argument(
        "--scores-s3-uri",
        required=True,
        help=(
            "S3 URI of the Batch Transform output (file or prefix). "
            "Example: s3://northstar-artifacts/predictions/churn/2026/07/06/"
        ),
    )
    parser.add_argument(
        "--run-date",
        default=None,
        help="ISO date for the batch run (default: today UTC, e.g., 2026-07-06).",
    )
    parser.add_argument(
        "--region",
        default=REGION,
        help=f"AWS region for CloudWatch (default: {REGION}).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Compute metrics but do not publish to CloudWatch. Use for testing.",
    )
    args = parser.parse_args()

    try:
        scores_df = load_scores_from_s3(args.scores_s3_uri, region=args.region)
        result = publish_churn_metrics(
            scores_df,
            run_date=args.run_date,
            region=args.region,
            dry_run=args.dry_run,
        )
        import json
        print(json.dumps(result, indent=2))
    except Exception as exc:
        logger.error("Failed to publish metrics: %s", exc, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
