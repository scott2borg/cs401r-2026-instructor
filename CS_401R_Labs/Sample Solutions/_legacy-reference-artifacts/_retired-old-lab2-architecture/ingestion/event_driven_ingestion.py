"""
NorthStar Retail AI Platform — CS 401R Lab 2 Sample Solution
event_driven_ingestion.py

S3-event-driven Lambda function for store_events ingestion.

Trigger: S3 ObjectCreated event on the raw/store_events/ prefix.

When a new CSV file lands in s3://{RAW_BUCKET}/raw/store_events/, this
Lambda automatically:
  1. Parses the S3 event to extract bucket + key.
  2. Reads the CSV into a pandas DataFrame.
  3. Validates required columns and non-null constraints.
  4. Normalises store_id whitespace and mixed date formats (ISO + MM/DD/YYYY).
  5. Writes valid records to processed/store_events/{year}/{month}/{day}/.
  6. Writes rejected records (missing required fields) to quarantine/store_events/.
  7. Logs metrics to CloudWatch and publishes an SNS alert on any unhandled error.

Environment variables:
  PROCESSED_BUCKET : S3 bucket for processed + quarantine output.
  SNS_TOPIC_ARN    : SNS topic for failure notifications.
  AWS_REGION       : Set automatically by Lambda runtime.

Author: CS 401R Sample Solution
"""

import os
import io
import re
import json
import logging
import traceback
from datetime import datetime, timezone
from typing import Any

import boto3
import pandas as pd

# ---------------------------------------------------------------------------
# Configuration & logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
logger = logging.getLogger("northstar.event_driven")

REGION           = os.environ.get("AWS_REGION", "us-east-1")
PROCESSED_BUCKET = os.environ.get("PROCESSED_BUCKET", "northstar-processed")
SNS_TOPIC_ARN    = os.environ.get("SNS_TOPIC_ARN", "")

REQUIRED_COLUMNS  = ["store_id", "event_date", "event_type"]
CW_NAMESPACE      = "NorthStar/DataPipeline"

# Regex patterns for date format detection
ISO_DATE_PATTERN  = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MDY_DATE_PATTERN  = re.compile(r"^\d{1,2}/\d{1,2}/\d{4}$")


# ---------------------------------------------------------------------------
# AWS clients (module-level for Lambda warm-start reuse)
# ---------------------------------------------------------------------------

s3         = boto3.client("s3",         region_name=REGION)
cloudwatch = boto3.client("cloudwatch", region_name=REGION)
sns        = boto3.client("sns",        region_name=REGION)


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _notify_failure(subject: str, message: str) -> None:
    """
    Publish a failure notification to the configured SNS topic.

    Called only on unhandled exceptions so the on-call team is paged
    when the pipeline fails unexpectedly.  If SNS_TOPIC_ARN is not set,
    logs a warning and continues so local testing doesn't require SNS.
    """
    if not SNS_TOPIC_ARN:
        logger.warning("SNS_TOPIC_ARN not set — skipping failure notification.")
        return
    try:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=subject[:100],   # SNS subject max = 100 chars
            Message=message,
        )
        logger.info("SNS failure notification published to %s.", SNS_TOPIC_ARN)
    except Exception as exc:
        logger.error("Failed to publish SNS notification: %s", exc)


def _publish_metrics(
    record_count: int,
    rejection_count: int,
    date_fixes: int,
    source_key: str,
) -> None:
    """
    Emit ingestion metrics to CloudWatch.

    Metrics:
      - StoreEventRecordCount   : Total records in the file.
      - StoreEventRejectedCount : Records missing required fields.
      - StoreEventDateFixCount  : Records with date format converted from MM/DD/YYYY.

    Dimension: SourceKey — the S3 object key that triggered this invocation.
    """
    now        = datetime.now(timezone.utc)
    dimensions = [{"Name": "SourceKey", "Value": source_key}]

    try:
        cloudwatch.put_metric_data(
            Namespace=CW_NAMESPACE,
            MetricData=[
                {
                    "MetricName": "StoreEventRecordCount",
                    "Dimensions": dimensions,
                    "Value": float(record_count),
                    "Unit": "Count",
                    "Timestamp": now,
                },
                {
                    "MetricName": "StoreEventRejectedCount",
                    "Dimensions": dimensions,
                    "Value": float(rejection_count),
                    "Unit": "Count",
                    "Timestamp": now,
                },
                {
                    "MetricName": "StoreEventDateFixCount",
                    "Dimensions": dimensions,
                    "Value": float(date_fixes),
                    "Unit": "Count",
                    "Timestamp": now,
                },
            ],
        )
        logger.info("CloudWatch metrics published.")
    except Exception as exc:
        logger.warning("Failed to publish CloudWatch metrics: %s", exc)


# ---------------------------------------------------------------------------
# Normalisation logic
# ---------------------------------------------------------------------------

def normalize_store_id_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    Strip leading/trailing whitespace from store_id values.

    Store events CSVs are manually maintained and frequently contain
    accidental whitespace.  This is a lightweight but high-value fix.
    """
    if "store_id" in df.columns:
        df["store_id"] = df["store_id"].astype(str).str.strip()
    return df


def normalize_event_date_column(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """
    Normalise the event_date column to ISO 8601 format (YYYY-MM-DD).

    Accepts two input formats:
      - ISO:       YYYY-MM-DD   (kept as-is)
      - US format: MM/DD/YYYY   (converted to YYYY-MM-DD)

    Values that match neither pattern are left as-is and flagged in the
    returned fix_count only for the MM/DD/YYYY conversions.

    Returns (df_with_normalized_dates, number_of_dates_converted).
    """
    if "event_date" not in df.columns:
        return df, 0

    fix_count = 0
    normalized_dates = []

    for raw_val in df["event_date"]:
        val = str(raw_val).strip() if pd.notna(raw_val) else ""

        if ISO_DATE_PATTERN.match(val):
            normalized_dates.append(val)

        elif MDY_DATE_PATTERN.match(val):
            # Convert MM/DD/YYYY -> YYYY-MM-DD
            try:
                dt = datetime.strptime(val, "%m/%d/%Y")
                normalized_dates.append(dt.strftime("%Y-%m-%d"))
                fix_count += 1
            except ValueError:
                logger.warning("Could not parse date: '%s' — keeping as-is.", val)
                normalized_dates.append(val)

        else:
            # Unknown format — keep original and log
            if val:
                logger.warning(
                    "Unrecognised date format: '%s' — keeping as-is.", val
                )
            normalized_dates.append(val)

    df = df.copy()
    df["event_date"] = normalized_dates
    return df, fix_count


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def split_valid_rejected(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split the DataFrame into valid and rejected records.

    A record is rejected if any REQUIRED_COLUMNS value is null or empty string.
    Rejected records are quarantined rather than dropped silently.

    Returns (valid_df, rejected_df).
    """
    # Treat empty strings as missing
    for col in REQUIRED_COLUMNS:
        if col in df.columns:
            df[col] = df[col].replace("", pd.NA)

    missing_mask = df[REQUIRED_COLUMNS].isnull().any(axis=1)
    valid_df     = df[~missing_mask].copy()
    rejected_df  = df[missing_mask].copy()
    return valid_df, rejected_df


# ---------------------------------------------------------------------------
# S3 write helpers
# ---------------------------------------------------------------------------

def _write_csv_to_s3(df: pd.DataFrame, bucket: str, key: str) -> None:
    """
    Serialise a DataFrame to CSV and upload to S3.

    Chosen over Parquet for store_events because the volume is low
    (typically a few hundred rows per file) and CSV is human-readable —
    useful for the quarantine path where humans need to inspect failures.
    """
    csv_body = df.to_csv(index=False).encode("utf-8")
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=csv_body,
        ContentType="text/csv",
    )
    logger.info("Wrote %d rows to s3://%s/%s", len(df), bucket, key)


def _write_processed(
    valid_df: pd.DataFrame,
    processed_bucket: str,
    source_key: str,
) -> None:
    """
    Write validated store_events records to the processed zone partitioned
    by today's UTC date (year/month/day).

    Output key pattern:
        processed/store_events/year=YYYY/month=MM/day=DD/{filename}
    """
    now      = datetime.now(timezone.utc)
    part     = f"year={now.year}/month={now.month:02d}/day={now.day:02d}"
    filename = source_key.split("/")[-1]   # Preserve original filename
    key      = f"processed/store_events/{part}/{filename}"

    _write_csv_to_s3(valid_df, processed_bucket, key)


def _write_quarantine(
    rejected_df: pd.DataFrame,
    processed_bucket: str,
    source_key: str,
) -> None:
    """
    Write rejected store_events records to the quarantine zone.

    A _rejection_ts column is added so operators can track when the record
    was quarantined vs. when it arrived.

    Output key pattern:
        quarantine/store_events/{filename}
    """
    if rejected_df.empty:
        return

    rejected_df = rejected_df.copy()
    rejected_df["_rejection_ts"] = datetime.now(timezone.utc).isoformat()
    filename = source_key.split("/")[-1]
    key      = f"quarantine/store_events/{filename}"

    _write_csv_to_s3(rejected_df, processed_bucket, key)


# ---------------------------------------------------------------------------
# Lambda handler
# ---------------------------------------------------------------------------

def handler(event: dict, context: Any) -> dict:
    """
    Lambda handler — fires on S3 ObjectCreated events under raw/store_events/.

    Full processing pipeline:
      1. Parse the S3 event to get bucket + object key.
      2. Read the CSV file from S3 into a pandas DataFrame.
      3. Validate required columns exist in the file schema.
      4. Normalize: strip whitespace from store_id; convert MM/DD/YYYY dates.
      5. Split valid / rejected records.
      6. Write valid records to processed/store_events/{year}/{month}/{day}/.
      7. Write rejected records to quarantine/store_events/.
      8. Publish CloudWatch metrics.

    On any unhandled exception, sends an SNS failure notification and
    re-raises so Lambda marks the invocation as failed (enabling retries
    or DLQ routing as configured on the event source mapping).

    Returns a summary dict for CloudWatch Logs.
    """
    logger.info("store_events event-driven ingestion invoked.")

    # ------------------------------------------------------------------ #
    # Step 1 — Parse S3 event
    # ------------------------------------------------------------------ #
    try:
        record     = event["Records"][0]
        src_bucket = record["s3"]["bucket"]["name"]
        src_key    = record["s3"]["object"]["key"]
        logger.info("Source: s3://%s/%s", src_bucket, src_key)
    except (KeyError, IndexError) as exc:
        msg = f"Malformed S3 event — cannot extract bucket/key: {exc}"
        logger.error(msg)
        _notify_failure("NorthStar store_events — malformed S3 event", msg)
        raise ValueError(msg) from exc

    try:
        # Step 2 — Read CSV from S3
        logger.info("Reading CSV from S3 …")
        response = s3.get_object(Bucket=src_bucket, Key=src_key)
        csv_body = response["Body"].read()
        df       = pd.read_csv(io.BytesIO(csv_body))
        logger.info("Read %d records, %d columns.", len(df), len(df.columns))

        # Step 3 — Schema validation: required columns present?
        missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        if missing_cols:
            raise ValueError(
                f"CSV is missing required columns: {missing_cols}. "
                f"Actual columns: {list(df.columns)}"
            )

        # Step 4a — Normalise store_id whitespace
        df = normalize_store_id_column(df)

        # Step 4b — Normalise event_date to ISO format
        df, date_fix_count = normalize_event_date_column(df)
        logger.info("%d date format conversions applied.", date_fix_count)

        # Step 5 — Split valid / rejected
        valid_df, rejected_df = split_valid_rejected(df)
        logger.info(
            "Valid: %d | Rejected: %d", len(valid_df), len(rejected_df)
        )

        # Step 6 — Write valid records to processed zone
        if not valid_df.empty:
            _write_processed(valid_df, PROCESSED_BUCKET, src_key)

        # Step 7 — Write rejected records to quarantine
        if not rejected_df.empty:
            _write_quarantine(rejected_df, PROCESSED_BUCKET, src_key)

        # Step 8 — CloudWatch metrics
        _publish_metrics(
            record_count=len(df),
            rejection_count=len(rejected_df),
            date_fixes=date_fix_count,
            source_key=src_key,
        )

        summary = {
            "source": f"s3://{src_bucket}/{src_key}",
            "total_records":    len(df),
            "valid_records":    len(valid_df),
            "rejected_records": len(rejected_df),
            "date_fixes":       date_fix_count,
            "status": "success",
        }
        logger.info("Pipeline complete: %s", summary)
        return summary

    except Exception as exc:
        tb  = traceback.format_exc()
        msg = (
            f"store_events ingestion FAILED for s3://{src_bucket}/{src_key}\n\n"
            f"Error: {exc}\n\nTraceback:\n{tb}"
        )
        logger.error(msg)
        _notify_failure(
            subject=f"NorthStar store_events ingestion FAILED — {src_key}",
            message=msg,
        )
        raise


# ---------------------------------------------------------------------------
# Local test entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    """
    Local testing shim: synthesises a minimal S3 event payload and invokes
    the handler so you can test normalisation logic without a live Lambda.

    Set PROCESSED_BUCKET and ensure AWS credentials are available before running.

    Usage:
        PROCESSED_BUCKET=my-bucket python event_driven_ingestion.py \
            --bucket raw-bucket --key raw/store_events/test.csv
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Local test runner for event_driven_ingestion.handler"
    )
    parser.add_argument("--bucket", required=True, help="S3 bucket containing the file.")
    parser.add_argument("--key",    required=True, help="S3 key of the store_events CSV.")
    cli_args = parser.parse_args()

    fake_event = {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": cli_args.bucket},
                    "object": {"key": cli_args.key},
                }
            }
        ]
    }

    result = handler(fake_event, context=None)
    print(json.dumps(result, indent=2))
