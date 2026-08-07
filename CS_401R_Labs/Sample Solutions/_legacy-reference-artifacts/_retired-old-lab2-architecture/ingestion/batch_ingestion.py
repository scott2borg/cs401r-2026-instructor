"""
NorthStar Retail AI Platform — CS 401R Lab 2 Sample Solution
batch_ingestion.py

Production AWS Glue PySpark ETL script for nightly POS transaction ingestion.
Reads raw transactions from S3, validates schema and data quality, cleans and
normalizes records, writes to the processed zone with partitioning, and emits
CloudWatch metrics.

Usage (Glue Job):
    Triggered nightly via EventBridge; arguments injected by the Glue job definition.

Author: CS 401R Sample Solution
"""

import sys
import re
import boto3
from datetime import datetime, timezone

from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrame

from pyspark.context import SparkContext
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField,
    StringType, DoubleType, IntegerType, BooleanType, TimestampType
)

# ---------------------------------------------------------------------------
# Job initialisation
# ---------------------------------------------------------------------------

args = getResolvedOptions(
    sys.argv,
    ["JOB_NAME", "raw_bucket", "processed_bucket", "run_date"],
)

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

RAW_BUCKET = args["raw_bucket"]
PROCESSED_BUCKET = args["processed_bucket"]
RUN_DATE = args["run_date"]          # YYYY-MM-DD  e.g. "2026-06-15"
REGION = "us-east-1"

cloudwatch = boto3.client("cloudwatch", region_name=REGION)

# ---------------------------------------------------------------------------
# Schema definition
# ---------------------------------------------------------------------------

REQUIRED_COLUMNS = [
    "transaction_id",
    "customer_id",
    "store_id",
    "transaction_date",
    "transaction_amount",
    "net_amount",
    "num_items",
    "num_units",
    "payment_method",
    "channel",
    "return_flag",
    "product_categories",
]

TRANSACTION_SCHEMA = StructType([
    StructField("transaction_id",    StringType(),    nullable=False),
    StructField("customer_id",       StringType(),    nullable=True),
    StructField("store_id",          StringType(),    nullable=True),
    StructField("transaction_date",  StringType(),    nullable=False),
    StructField("transaction_amount",DoubleType(),    nullable=False),
    StructField("net_amount",        DoubleType(),    nullable=True),
    StructField("num_items",         IntegerType(),   nullable=True),
    StructField("num_units",         IntegerType(),   nullable=True),
    StructField("payment_method",    StringType(),    nullable=True),
    StructField("promotion_code",    StringType(),    nullable=True),
    StructField("promotion_discount",DoubleType(),    nullable=True),
    StructField("channel",           StringType(),    nullable=False),
    StructField("device_type",       StringType(),    nullable=True),
    StructField("return_flag",       BooleanType(),   nullable=True),
    StructField("product_categories",StringType(),    nullable=True),
])


# ---------------------------------------------------------------------------
# Step 1: Read raw data from S3
# ---------------------------------------------------------------------------

def read_raw_transactions(raw_bucket: str, run_date: str):
    """
    Read raw transaction Parquet files for a given run date from S3.

    Parquet files are partitioned by date under:
        s3://{raw_bucket}/raw/transactions/date={run_date}/

    Returns a Spark DataFrame with the raw schema applied.
    """
    input_path = f"s3://{raw_bucket}/raw/transactions/date={run_date}/"
    print(f"[Step 1] Reading raw transactions from: {input_path}")

    try:
        raw_df = spark.read.schema(TRANSACTION_SCHEMA).parquet(input_path)
        record_count = raw_df.count()
        print(f"[Step 1] Loaded {record_count:,} raw records.")
        return raw_df
    except Exception as exc:
        print(f"[Step 1] ERROR reading raw transactions: {exc}")
        raise


# ---------------------------------------------------------------------------
# Step 2: Schema validation — null checks and required columns
# ---------------------------------------------------------------------------

def validate_schema(df):
    """
    Validate that all required columns are present and split into
    valid and rejected DataFrames.

    - Checks for required column presence (raises if missing).
    - Splits records: valid_df has non-null customer_id AND transaction_id;
      rejected_df captures any record with a null on either key field.

    Returns (valid_df, rejected_df).
    """
    print("[Step 2] Validating schema and checking nulls …")

    # Required column presence check (schema-level, not row-level)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            f"[Step 2] Schema validation failed — missing columns: {missing}"
        )

    # Row-level null check: both customer_id and transaction_id must be present
    # for a record to be actionable downstream.
    null_condition = F.col("customer_id").isNull() | F.col("transaction_id").isNull()

    valid_df    = df.filter(~null_condition)
    rejected_df = df.filter(null_condition)

    valid_count    = valid_df.count()
    rejected_count = rejected_df.count()

    print(f"[Step 2] Valid records   : {valid_count:,}")
    print(f"[Step 2] Rejected records: {rejected_count:,}")

    return valid_df, rejected_df


def write_rejected_records(rejected_df, processed_bucket: str, run_date: str):
    """
    Persist rejected (null key) records to the quarantine zone so they can
    be investigated and potentially reprocessed after upstream remediation.

    Output path: s3://{processed_bucket}/quarantine/transactions/date={run_date}/
    """
    quarantine_path = (
        f"s3://{processed_bucket}/quarantine/transactions/date={run_date}/"
    )
    print(f"[Step 2] Writing {rejected_df.count():,} rejected records to: {quarantine_path}")

    try:
        (
            rejected_df
            .write
            .mode("overwrite")
            .parquet(quarantine_path)
        )
        print(f"[Step 2] Quarantine write complete.")
    except Exception as exc:
        # Log but do not halt the job — quarantine failure should not block
        # the main pipeline. Alert separately.
        print(f"[Step 2] WARNING: Failed to write rejected records: {exc}")


# ---------------------------------------------------------------------------
# Step 3: Data cleaning
# ---------------------------------------------------------------------------

def normalize_store_id(df):
    """
    Normalise legacy store_id formats to the canonical STORE-{3 digits} form.

    Pre-March 2024 POS systems emitted store IDs as "S{3 digits}" (e.g. "S042").
    The canonical format is "STORE-{3 digits}" (e.g. "STORE-042").

    Regex: ^S(\d{3})$  →  STORE-\1
    Online transactions carry store_id = "ONLINE" and are left unchanged.
    """
    print("[Step 3] Normalising store_id …")
    normalised = F.when(
        F.col("store_id").rlike(r"^S\d{3}$"),
        F.regexp_replace(F.col("store_id"), r"^S(\d{3})$", "STORE-$1"),
    ).otherwise(F.col("store_id"))

    return df.withColumn("store_id", normalised)


def parse_transaction_date(df):
    """
    Cast the transaction_date string column to a proper TimestampType.

    The raw feed delivers ISO-8601 UTC strings ("2026-06-15T22:31:00Z").
    Spark's to_timestamp handles this format natively. Records that fail
    to parse are left as null and will be caught by the quality check step.
    """
    print("[Step 3] Parsing transaction_date …")
    return df.withColumn(
        "transaction_date",
        F.to_timestamp(F.col("transaction_date"), "yyyy-MM-dd'T'HH:mm:ss'Z'"),
    )


def cast_numeric_types(df):
    """
    Ensure numeric columns have the correct types after reading from
    raw Parquet (which may have loose schemas from upstream tools).
    """
    print("[Step 3] Casting numeric types …")
    return (
        df
        .withColumn("transaction_amount", F.col("transaction_amount").cast(DoubleType()))
        .withColumn("net_amount",          F.col("net_amount").cast(DoubleType()))
        .withColumn("num_items",           F.col("num_items").cast(IntegerType()))
        .withColumn("num_units",           F.col("num_units").cast(IntegerType()))
        .withColumn("promotion_discount",  F.col("promotion_discount").cast(DoubleType()))
    )


def add_job_metadata(df, run_date: str):
    """
    Stamp each record with pipeline metadata for lineage tracking.
    """
    return (
        df
        .withColumn("_job_run_date",      F.lit(run_date))
        .withColumn("_ingested_at",       F.lit(datetime.now(timezone.utc).isoformat()))
    )


def filter_to_run_date(df, run_date: str):
    """
    Retain only records whose transaction_date falls on run_date (UTC).

    This is a safety filter: the upstream S3 partition should already be
    date-scoped, but late-arriving records from adjacent partitions may
    slip through. We enforce the boundary here.
    """
    print(f"[Step 3] Filtering to run_date={run_date} …")
    filtered = df.filter(
        F.to_date(F.col("transaction_date")) == F.lit(run_date)
    )
    print(f"[Step 3] Records after date filter: {filtered.count():,}")
    return filtered


def clean_transactions(df, run_date: str):
    """
    Orchestrate all cleaning steps and return the cleaned DataFrame.
    """
    df = normalize_store_id(df)
    df = parse_transaction_date(df)
    df = cast_numeric_types(df)
    df = filter_to_run_date(df, run_date)
    df = add_job_metadata(df, run_date)
    return df


# ---------------------------------------------------------------------------
# Step 4: Quality checks
# ---------------------------------------------------------------------------

def run_quality_checks(df):
    """
    Run data quality assertions and return a dict of quality metrics.

    Checks performed:
      - Negative transaction_amount rate (informational; logged as CloudWatch metric)
      - customer_id null rate (must be < 5% of all records in the clean set)

    Raises RuntimeError if any hard threshold is breached so the Glue job
    fails visibly and triggers downstream alerting.
    """
    print("[Step 4] Running quality checks …")
    total = df.count()
    if total == 0:
        print("[Step 4] WARNING: Zero records after cleaning. Check upstream source.")
        return {"total": 0, "negative_amount_count": 0, "customer_id_null_rate": 0.0}

    # Negative amount check (returns will legitimately be negative)
    negative_count = df.filter(F.col("transaction_amount") < 0).count()
    negative_rate  = negative_count / total
    print(f"[Step 4] Negative transaction_amount: {negative_count:,} ({negative_rate:.2%})")

    # customer_id null rate check — must be < 5%
    # (Valid records should already have non-null customer_ids post-validation,
    # but GUEST checkouts may have been re-introduced here.)
    null_cust_count = df.filter(F.col("customer_id").isNull()).count()
    null_cust_rate  = null_cust_count / total
    print(f"[Step 4] customer_id null rate: {null_cust_rate:.2%} (threshold: <5%)")

    if null_cust_rate >= 0.05:
        raise RuntimeError(
            f"[Step 4] QUALITY GATE FAILED: customer_id null rate {null_cust_rate:.2%} "
            f"exceeds 5% threshold. Aborting job to prevent polluted downstream data."
        )

    return {
        "total": total,
        "negative_amount_count": negative_count,
        "customer_id_null_rate": null_cust_rate,
    }


# ---------------------------------------------------------------------------
# Step 5: Write to processed zone
# ---------------------------------------------------------------------------

def write_processed_transactions(df, processed_bucket: str):
    """
    Write cleaned transactions to the processed S3 zone in Parquet format,
    partitioned by _job_run_date and channel.

    Partition layout:
        s3://{processed_bucket}/processed/transactions/
            _job_run_date=2026-06-15/
                channel=store/
                channel=online/

    Partitioning on channel supports common analytical query patterns
    (e.g. "give me all online transactions this week") without full scans.
    """
    output_path = f"s3://{processed_bucket}/processed/transactions/"
    print(f"[Step 5] Writing processed transactions to: {output_path}")

    try:
        (
            df
            .write
            .mode("overwrite")
            .partitionBy("_job_run_date", "channel")
            .parquet(output_path)
        )
        print("[Step 5] Write complete.")
    except Exception as exc:
        print(f"[Step 5] ERROR writing processed transactions: {exc}")
        raise


# ---------------------------------------------------------------------------
# Step 6: CloudWatch metrics
# ---------------------------------------------------------------------------

def publish_cloudwatch_metrics(
    total_count: int,
    rejected_count: int,
    negative_amount_count: int,
    run_date: str,
):
    """
    Emit pipeline health metrics to CloudWatch under the
    NorthStar/DataPipeline namespace.

    Metrics published:
      - TransactionRecordCount   : total valid records written to processed zone
      - RejectedRecordCount      : records sent to quarantine (null key fields)
      - NegativeAmountCount      : records with transaction_amount < 0

    Dimensions: JobName, RunDate — allows filtering per-job and per-day
    in CloudWatch dashboards and alarms.
    """
    print("[Step 6] Publishing CloudWatch metrics …")
    namespace  = "NorthStar/DataPipeline"
    dimensions = [
        {"Name": "JobName", "Value": args["JOB_NAME"]},
        {"Name": "RunDate", "Value": run_date},
    ]

    metric_data = [
        {
            "MetricName": "TransactionRecordCount",
            "Dimensions": dimensions,
            "Value": float(total_count),
            "Unit": "Count",
            "Timestamp": datetime.now(timezone.utc),
        },
        {
            "MetricName": "RejectedRecordCount",
            "Dimensions": dimensions,
            "Value": float(rejected_count),
            "Unit": "Count",
            "Timestamp": datetime.now(timezone.utc),
        },
        {
            "MetricName": "NegativeAmountCount",
            "Dimensions": dimensions,
            "Value": float(negative_amount_count),
            "Unit": "Count",
            "Timestamp": datetime.now(timezone.utc),
        },
    ]

    try:
        # CloudWatch put_metric_data accepts at most 20 metrics per call
        cloudwatch.put_metric_data(
            Namespace=namespace,
            MetricData=metric_data,
        )
        print(f"[Step 6] Metrics published to {namespace}.")
    except Exception as exc:
        # Metric failure should not abort the job — log and continue.
        print(f"[Step 6] WARNING: Failed to publish CloudWatch metrics: {exc}")


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------

def main():
    """
    Orchestrate the full batch ingestion pipeline for one run_date.

    Pipeline steps:
        1. Read raw transactions from S3
        2. Validate schema; split valid / rejected; quarantine rejected
        3. Clean: normalize store_id, parse dates, cast types, filter to run_date
        4. Quality checks (null rate gates)
        5. Write to processed zone partitioned by date + channel
        6. Emit CloudWatch metrics
    """
    print(f"=== NorthStar Batch Ingestion — run_date={RUN_DATE} ===")

    # Step 1
    raw_df = read_raw_transactions(RAW_BUCKET, RUN_DATE)
    raw_total = raw_df.count()

    # Step 2
    valid_df, rejected_df = validate_schema(raw_df)
    rejected_count = rejected_df.count()
    write_rejected_records(rejected_df, PROCESSED_BUCKET, RUN_DATE)

    # Step 3
    cleaned_df = clean_transactions(valid_df, RUN_DATE)

    # Step 4
    quality_metrics = run_quality_checks(cleaned_df)

    # Step 5
    write_processed_transactions(cleaned_df, PROCESSED_BUCKET)

    # Step 6
    publish_cloudwatch_metrics(
        total_count=quality_metrics["total"],
        rejected_count=rejected_count,
        negative_amount_count=quality_metrics["negative_amount_count"],
        run_date=RUN_DATE,
    )

    print(f"=== Pipeline complete. Raw={raw_total:,} | Valid={quality_metrics['total']:,} | Rejected={rejected_count:,} ===")
    job.commit()


main()
