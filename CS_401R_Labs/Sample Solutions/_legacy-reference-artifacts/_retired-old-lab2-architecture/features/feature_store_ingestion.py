"""
NorthStar Retail AI Platform — CS 401R Lab 2 Sample Solution
feature_store_ingestion.py

Ingest the computed customer churn features into AWS SageMaker Feature Store.

This script:
  1. Creates the northstar-churn-features feature group (if it does not exist).
  2. Loads the feature matrix from northstar-processed/features.parquet.
  3. Ingests the DataFrame into Feature Store using the high-level SDK.
  4. Demonstrates how to retrieve a training dataset from the offline store
     via Athena for model training.

SageMaker Feature Store concepts used:
  - Online store  : Low-latency key-value lookup for real-time inference.
  - Offline store : S3-backed Parquet store for batch training dataset creation.
  - Record identifier feature : customer_id — unique key per record.
  - Event time feature        : feature_computation_timestamp — used for
                                point-in-time correct feature retrieval.

Usage:
    python feature_store_ingestion.py \
        --features-path northstar-processed/features.parquet \
        --features-bucket s3://northstar-features/ \
        --athena-bucket   s3://northstar-athena-results/

Environment variables:
    AWS_REGION        : AWS region (default: us-east-1)
    SAGEMAKER_ROLE    : ARN of the SageMaker execution role

Author: CS 401R Sample Solution
"""

import os
import time
import argparse
import logging
from datetime import datetime, timezone
from pathlib import Path

import boto3
import pandas as pd
import sagemaker
from sagemaker.feature_store.feature_group import FeatureGroup
from sagemaker.feature_store.inputs import FeatureDefinition, FeatureTypeEnum
from sagemaker.session import Session

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
logger = logging.getLogger("northstar.feature_store")

FEATURE_GROUP_NAME = "northstar-churn-features"
REGION             = os.environ.get("AWS_REGION", "us-east-1")
SAGEMAKER_ROLE     = os.environ.get(
    "SAGEMAKER_ROLE",
    "arn:aws:iam::ACCOUNT_ID:role/SageMakerExecutionRole",  # Override via env var
)

# Feature type mapping: column name → FeatureTypeEnum
FEATURE_TYPE_MAP = {
    "customer_id":                  FeatureTypeEnum.STRING,
    "loyalty_tier":                 FeatureTypeEnum.STRING,
    "churn_label":                  FeatureTypeEnum.INTEGRAL,
    "days_since_last_purchase":     FeatureTypeEnum.INTEGRAL,
    "purchase_frequency_90d":       FeatureTypeEnum.INTEGRAL,
    "avg_basket_size_6m":           FeatureTypeEnum.FRACTIONAL,
    "category_diversity_score":     FeatureTypeEnum.FRACTIONAL,
    "online_to_store_ratio":        FeatureTypeEnum.FRACTIONAL,
    "promo_response_rate":          FeatureTypeEnum.FRACTIONAL,
    "loyalty_tier_duration_days":   FeatureTypeEnum.INTEGRAL,
    "purchase_frequency_180d":      FeatureTypeEnum.INTEGRAL,
    "total_spend_90d":              FeatureTypeEnum.FRACTIONAL,
    "clickstream_sessions_30d":     FeatureTypeEnum.INTEGRAL,
    "add_to_cart_rate_30d":         FeatureTypeEnum.FRACTIONAL,
    "feature_computation_timestamp": FeatureTypeEnum.STRING,
}


# ---------------------------------------------------------------------------
# Session setup
# ---------------------------------------------------------------------------

def get_sagemaker_session(region: str = REGION) -> tuple[Session, sagemaker.Session]:
    """
    Create and return a SageMaker SDK Session and a boto3 SageMaker runtime client.

    The SageMaker Session wraps boto3 and handles S3 interactions required by
    the Feature Store SDK.

    Args:
        region: AWS region name.

    Returns:
        Tuple of (sagemaker.session.Session, sagemaker.Session).
    """
    boto_session    = boto3.Session(region_name=region)
    sm_client       = boto_session.client("sagemaker")
    sm_runtime      = boto_session.client("sagemaker-runtime")
    sm_fs_runtime   = boto_session.client(
        service_name="sagemaker-featurestore-runtime"
    )

    sm_session = sagemaker.Session(
        boto_session=boto_session,
        sagemaker_client=sm_client,
        sagemaker_runtime_client=sm_runtime,
        sagemaker_featurestore_runtime_client=sm_fs_runtime,
    )

    return Session(sagemaker_session=sm_session), sm_session


# ---------------------------------------------------------------------------
# Feature group creation
# ---------------------------------------------------------------------------

def create_feature_group_if_not_exists(
    feature_group_name: str,
    features_bucket: str,
    sagemaker_session: Session,
) -> FeatureGroup:
    """
    Create the NorthStar churn feature group in SageMaker Feature Store,
    or return the existing group if it already exists.

    Feature group configuration:
      - Online store enabled  : supports low-latency inference lookups.
      - Offline store enabled : writes Parquet files to S3 for batch training.
      - Record identifier     : customer_id
      - Event time feature    : feature_computation_timestamp
        Must be a string in ISO-8601 format (SageMaker requirement).

    Args:
        feature_group_name : Name of the feature group to create.
        features_bucket    : S3 bucket URI (s3://bucket-name) for the offline store.
        sagemaker_session  : SageMaker SDK session.

    Returns:
        FeatureGroup object (existing or newly created).

    Raises:
        RuntimeError: If feature group creation fails after the timeout.
    """
    sm_client = boto3.client("sagemaker", region_name=REGION)

    # Check if the feature group already exists
    try:
        sm_client.describe_feature_group(FeatureGroupName=feature_group_name)
        logger.info("Feature group '%s' already exists.", feature_group_name)
        feature_group = FeatureGroup(
            name=feature_group_name,
            sagemaker_session=sagemaker_session,
        )
        return feature_group
    except sm_client.exceptions.ResourceNotFoundException:
        logger.info(
            "Feature group '%s' not found — creating …", feature_group_name
        )

    # Build feature definitions from FEATURE_TYPE_MAP
    feature_definitions = [
        FeatureDefinition(feature_name=col, feature_type=ftype)
        for col, ftype in FEATURE_TYPE_MAP.items()
    ]

    feature_group = FeatureGroup(
        name=feature_group_name,
        feature_definitions=feature_definitions,
        sagemaker_session=sagemaker_session,
    )

    # S3 URI for offline store must not have trailing slash
    offline_store_bucket = features_bucket.rstrip("/")

    try:
        feature_group.create(
            s3_uri=offline_store_bucket,
            record_identifier_name="customer_id",
            event_time_feature_name="feature_computation_timestamp",
            role_arn=SAGEMAKER_ROLE,
            enable_online_store=True,
            description=(
                "NorthStar customer churn prediction features. "
                "Computed weekly at FEATURE_SNAPSHOT_DATE. "
                "Includes RFM signals, engagement metrics, and loyalty features."
            ),
        )
    except Exception as exc:
        logger.error("Feature group creation failed: %s", exc)
        raise

    # Poll until the feature group is active (creation is async)
    max_wait_s  = 300   # 5 minutes
    poll_s      = 10
    elapsed     = 0

    logger.info("Waiting for feature group to become active …")
    while elapsed < max_wait_s:
        status = sm_client.describe_feature_group(
            FeatureGroupName=feature_group_name
        )["FeatureGroupStatus"]

        if status == "Created":
            logger.info("Feature group '%s' is active.", feature_group_name)
            return feature_group
        elif status in ("CreateFailed", "DeleteFailed"):
            raise RuntimeError(
                f"Feature group entered terminal state: {status}. "
                "Check CloudWatch logs for the feature group for details."
            )
        else:
            logger.info(
                "Feature group status: %s — waiting %ds …", status, poll_s
            )
            time.sleep(poll_s)
            elapsed += poll_s

    raise RuntimeError(
        f"Feature group '{feature_group_name}' did not become active "
        f"within {max_wait_s}s. Check AWS console for current status."
    )


# ---------------------------------------------------------------------------
# Feature ingestion
# ---------------------------------------------------------------------------

def ingest_features(
    feature_group: FeatureGroup,
    features_df: pd.DataFrame,
    num_workers: int = 4,
) -> dict:
    """
    Ingest the feature matrix DataFrame into SageMaker Feature Store.

    Preparation steps:
      1. Add feature_computation_timestamp column (ISO-8601 UTC string).
         SageMaker Feature Store requires the event time as a string in
         yyyy-MM-dd'T'HH:mm:ssZ format or as fractional seconds since epoch.
         We use the ISO string format here.
      2. Ensure all column dtypes match the declared FeatureDefinition types:
         - Integral columns must be Python int (not numpy int64).
         - Fractional columns must be Python float.
         - String columns must be Python str.
      3. Replace NaN with 0 (int/float columns) or "" (string columns) —
         Feature Store does not accept NaN values.
      4. Call feature_group.ingest() with num_workers for parallel upload.

    Args:
        feature_group : FeatureGroup object pointing to the target group.
        features_df   : DataFrame produced by compute_features.build_feature_matrix.
        num_workers   : Parallel ingest workers (default: 4).

    Returns:
        Dict with ingestion summary: records_ingested, failed_rows.

    Raises:
        ValueError: If required columns are missing from features_df.
    """
    required = set(FEATURE_TYPE_MAP.keys()) - {"feature_computation_timestamp"}
    missing  = required - set(features_df.columns)
    if missing:
        raise ValueError(
            f"features_df is missing required columns: {missing}"
        )

    df = features_df.copy()

    # Step 1: Add event time column
    event_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    df["feature_computation_timestamp"] = event_time
    logger.info("feature_computation_timestamp set to: %s", event_time)

    # Step 2 & 3: Type coercion and NaN handling
    for col, ftype in FEATURE_TYPE_MAP.items():
        if col not in df.columns:
            continue
        if ftype == FeatureTypeEnum.INTEGRAL:
            df[col] = df[col].fillna(0).astype(int)
        elif ftype == FeatureTypeEnum.FRACTIONAL:
            df[col] = df[col].fillna(0.0).astype(float)
        elif ftype == FeatureTypeEnum.STRING:
            df[col] = df[col].fillna("").astype(str)

    # Reset index if customer_id is the index
    if df.index.name == "customer_id":
        df = df.reset_index()

    logger.info(
        "Ingesting %d records into feature group '%s' with %d workers …",
        len(df),
        feature_group.name,
        num_workers,
    )

    try:
        ingest_manager = feature_group.ingest(
            data_frame=df,
            max_workers=num_workers,
            wait=True,
        )
        failed_rows = ingest_manager.failed_rows
        logger.info(
            "Ingestion complete: %d records | %d failed rows.",
            len(df),
            len(failed_rows),
        )
        if failed_rows:
            logger.warning("Failed rows: %s", failed_rows[:5])  # Log first 5

        return {
            "records_ingested": len(df),
            "failed_rows":      len(failed_rows),
        }

    except Exception as exc:
        logger.error("Feature Store ingest failed: %s", exc)
        raise


# ---------------------------------------------------------------------------
# Training dataset retrieval via Athena
# ---------------------------------------------------------------------------

def retrieve_training_dataset(
    feature_group: FeatureGroup,
    start_date: str,
    end_date: str,
    athena_bucket: str,
) -> pd.DataFrame:
    """
    Retrieve a point-in-time correct training dataset from the offline store
    using Athena.

    The offline store in S3 stores all historical feature snapshots.  Athena
    is the standard query interface for the offline store.

    Date filtering:
        Filters on feature_computation_timestamp between start_date and end_date
        (inclusive) so that the training dataset only includes features computed
        within a specific date range.  This prevents training on features from
        outside the desired historical window.

    Args:
        feature_group : FeatureGroup to query.
        start_date    : ISO date string (YYYY-MM-DD) — inclusive lower bound.
        end_date      : ISO date string (YYYY-MM-DD) — inclusive upper bound.
        athena_bucket : S3 URI for Athena query results (s3://bucket-name/prefix/).

    Returns:
        pandas DataFrame with all feature columns for the requested date range.

    Raises:
        RuntimeError: If the Athena query fails or times out.
    """
    logger.info(
        "Retrieving training dataset: feature_group=%s, range=%s to %s",
        feature_group.name,
        start_date,
        end_date,
    )

    athena_query = feature_group.athena_query()
    table_name   = athena_query.table_name

    query_string = f"""
        SELECT *
        FROM "{table_name}"
        WHERE is_deleted = FALSE
          AND feature_computation_timestamp >= '{start_date}T00:00:00Z'
          AND feature_computation_timestamp <= '{end_date}T23:59:59Z'
    """

    logger.info("Running Athena query:\n%s", query_string)

    try:
        athena_query.run(
            query_string=query_string,
            output_location=athena_bucket,
        )
        athena_query.wait()

        if athena_query.get_query_execution()["QueryExecution"]["Status"]["State"] != "SUCCEEDED":
            state  = athena_query.get_query_execution()["QueryExecution"]["Status"]["State"]
            reason = athena_query.get_query_execution()["QueryExecution"]["Status"].get(
                "StateChangeReason", "unknown"
            )
            raise RuntimeError(
                f"Athena query did not succeed. State: {state}. Reason: {reason}"
            )

        df = athena_query.as_dataframe()
        logger.info(
            "Retrieved %d rows, %d columns from offline store.",
            len(df),
            len(df.columns),
        )
        return df

    except Exception as exc:
        logger.error("Athena query failed: %s", exc)
        raise


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(
    features_path: str,
    features_bucket: str,
    athena_bucket: str,
    retrieve_only: bool = False,
    start_date: str = "2026-05-01",
    end_date:   str = "2026-06-01",
) -> None:
    """
    Full feature store pipeline.

    Steps:
      1. Set up SageMaker session.
      2. Create feature group (or confirm it exists).
      3. Load features Parquet.
      4. Ingest features into Feature Store.
      5. Retrieve training dataset from offline store (demonstration).

    Args:
        features_path  : Path to features.parquet.
        features_bucket: S3 bucket URI for offline store.
        athena_bucket  : S3 URI for Athena query results.
        retrieve_only  : Skip ingestion; only retrieve training dataset.
        start_date     : Start of retrieval date range.
        end_date       : End of retrieval date range.
    """
    # Step 1: Session
    fs_session, sm_session = get_sagemaker_session(REGION)

    # Step 2: Feature group
    feature_group = create_feature_group_if_not_exists(
        feature_group_name=FEATURE_GROUP_NAME,
        features_bucket=features_bucket,
        sagemaker_session=fs_session,
    )

    if not retrieve_only:
        # Step 3: Load features
        features_path_obj = Path(features_path)
        if not features_path_obj.exists():
            raise FileNotFoundError(f"Features file not found: {features_path}")

        logger.info("Loading features from: %s", features_path)
        features_df = pd.read_parquet(features_path_obj)
        logger.info("Loaded %d customer feature records.", len(features_df))

        # Step 4: Ingest
        ingest_summary = ingest_features(feature_group, features_df)
        print(f"\nIngestion summary: {ingest_summary}")

    # Step 5: Retrieve training dataset (demonstration)
    logger.info("Retrieving training dataset from offline store …")
    training_df = retrieve_training_dataset(
        feature_group=feature_group,
        start_date=start_date,
        end_date=end_date,
        athena_bucket=athena_bucket,
    )
    print(f"\nTraining dataset shape: {training_df.shape}")
    print(training_df.head())


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="NorthStar Feature Store ingestion"
    )
    parser.add_argument(
        "--features-path",
        default="northstar-processed/features.parquet",
        help="Path to features.parquet produced by compute_features.py",
    )
    parser.add_argument(
        "--features-bucket",
        required=True,
        help="S3 bucket URI for SageMaker Feature Store offline store (s3://bucket-name).",
    )
    parser.add_argument(
        "--athena-bucket",
        required=True,
        help="S3 URI for Athena query result output (s3://bucket-name/prefix/).",
    )
    parser.add_argument(
        "--retrieve-only",
        action="store_true",
        help="Skip ingestion and only retrieve a training dataset.",
    )
    parser.add_argument(
        "--start-date",
        default="2026-05-01",
        help="Start date for training dataset retrieval (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--end-date",
        default="2026-06-01",
        help="End date for training dataset retrieval (YYYY-MM-DD).",
    )

    args = parser.parse_args()
    main(
        features_path=args.features_path,
        features_bucket=args.features_bucket,
        athena_bucket=args.athena_bucket,
        retrieve_only=args.retrieve_only,
        start_date=args.start_date,
        end_date=args.end_date,
    )
