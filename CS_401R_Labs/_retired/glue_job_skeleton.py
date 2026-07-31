"""
NorthStar Retail — AWS Glue ETL Job Skeleton
CS 401R Lab 2 Starter Kit

This skeleton provides the Glue job structure for the batch ingestion pipeline.
Students complete the TODO sections to build a production-quality ETL job.

Job: northstar-transaction-etl
Trigger: Daily at 03:00 UTC
Source: s3://{raw_bucket}/raw/transactions/
Target: s3://{processed_bucket}/processed/transactions/YYYY/MM/DD/

Usage (local testing with glue-local or aws-glue-libs):
    python glue_job_skeleton.py --JOB_NAME test --raw_bucket my-raw --processed_bucket my-processed
"""

import sys
from datetime import datetime, timezone

from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from pyspark.sql import functions as F
from pyspark.sql.types import (DoubleType, IntegerType, StringType,
                                TimestampType)

# ── Job Initialization ─────────────────────────────────────────────────────────

args = getResolvedOptions(sys.argv, [
    "JOB_NAME",
    "raw_bucket",
    "processed_bucket",
    "run_date",           # YYYY-MM-DD — process data for this date
])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

logger = glueContext.get_logger()
logger.info(f"Starting NorthStar transaction ETL for {args['run_date']}")

RUN_DATE = datetime.strptime(args["run_date"], "%Y-%m-%d")
RAW_PATH = f"s3://{args['raw_bucket']}/raw/transactions/"
PROCESSED_PATH = (
    f"s3://{args['processed_bucket']}/processed/transactions/"
    f"{RUN_DATE.year}/{RUN_DATE.month:02d}/{RUN_DATE.day:02d}/"
)

# ── Step 1: Read Raw Data ──────────────────────────────────────────────────────

logger.info(f"Reading from {RAW_PATH}")

raw_df = glueContext.create_dynamic_frame.from_options(
    connection_type="s3",
    connection_options={"paths": [RAW_PATH], "recurse": True},
    format="parquet",
).toDF()

logger.info(f"Raw record count: {raw_df.count()}")

# ── Step 2: Schema Validation ──────────────────────────────────────────────────
# Reject records that fail validation. Log rejections — do NOT silently drop.

REQUIRED_COLUMNS = [
    "transaction_id", "customer_id", "store_id", "transaction_date",
    "transaction_amount", "channel",
]

# Check all required columns are present
missing_cols = [c for c in REQUIRED_COLUMNS if c not in raw_df.columns]
if missing_cols:
    raise ValueError(f"Schema validation failed — missing columns: {missing_cols}")

# TODO: Add a null check for customer_id and transaction_id
# Hint: Use F.col().isNull() and filter into valid/invalid DataFrames
valid_df = raw_df  # Replace this with your null-check filter
rejected_df = raw_df.filter(F.lit(False))  # Replace with rejected records

# TODO: Write rejected records to a quarantine path for investigation
# rejected_df.write.mode("append").parquet(f"s3://{args['processed_bucket']}/quarantine/transactions/")
logger.info(f"Rejected record count: {rejected_df.count()}")

# ── Step 3: Data Cleaning ──────────────────────────────────────────────────────

def clean_transactions(df):
    """
    Apply NorthStar-specific cleaning rules to the transaction dataset.
    See northstar-data-schema.md for documented quality issues.
    """

    # 3a. Normalize store_id format
    # Pre-March 2024 records use 'S{3 digits}' format — normalize to 'STORE-{3 digits}'
    # TODO: Use F.regexp_replace() to convert "S001" → "STORE-001"
    df = df.withColumn(
        "store_id",
        F.when(
            F.col("store_id").rlike("^S\\d{3}$"),
            F.concat(F.lit("STORE-"), F.substring("store_id", 2, 3))
        ).otherwise(F.trim(F.col("store_id")))
    )

    # 3b. Parse transaction_date to timestamp
    # TODO: Handle both ISO format and any other formats in your data
    df = df.withColumn(
        "transaction_date",
        F.to_timestamp(F.col("transaction_date"))
    )

    # 3c. Cast numeric fields
    df = df.withColumn("transaction_amount", F.col("transaction_amount").cast(DoubleType()))
    df = df.withColumn("net_amount", F.col("net_amount").cast(DoubleType()))
    df = df.withColumn("num_items", F.col("num_items").cast(IntegerType()))
    df = df.withColumn("num_units", F.col("num_units").cast(IntegerType()))

    # 3d. Filter to the run date (process only today's transactions)
    # TODO: Filter rows where DATE(transaction_date) == run_date
    # df = df.filter(F.to_date("transaction_date") == F.lit(args["run_date"]))

    # 3e. Add processing metadata
    df = df.withColumn("_processed_at", F.lit(datetime.now(timezone.utc).isoformat()))
    df = df.withColumn("_job_run_date", F.lit(args["run_date"]))
    df = df.withColumn("_source_path", F.lit(RAW_PATH))

    return df


cleaned_df = clean_transactions(valid_df)

# ── Step 4: Data Quality Checks ────────────────────────────────────────────────
# These checks gate whether the job proceeds. Fail loudly.

def run_quality_checks(df):
    """
    Run quality checks on the cleaned transaction dataset.
    Raise an exception if any check fails — do not produce bad output.
    """

    total = df.count()
    if total == 0:
        raise ValueError("Quality check FAILED: No records after cleaning. Possible pipeline issue.")

    # Check: transaction_amount must be positive
    negative_amounts = df.filter(F.col("transaction_amount") <= 0).count()
    if negative_amounts / total > 0.01:
        raise ValueError(
            f"Quality check FAILED: {negative_amounts / total:.1%} of records have negative amounts "
            f"(threshold: 1%). Investigate data source."
        )

    # Check: customer_id null rate must be below 5%
    # TODO: Implement this check
    # Hint: F.col("customer_id").isNull()

    # Check: valid channel values
    invalid_channels = df.filter(~F.col("channel").isin(["store", "online"])).count()
    if invalid_channels > 0:
        logger.warn(f"WARNING: {invalid_channels} records with invalid channel value")

    logger.info(f"✓ Quality checks passed — {total:,} clean records")
    return df


checked_df = run_quality_checks(cleaned_df)

# ── Step 5: Write to Processed Zone ───────────────────────────────────────────

logger.info(f"Writing {checked_df.count():,} records to {PROCESSED_PATH}")

# TODO: Consider partitioning strategy for Athena query performance
# Options: partition by year/month/day, or by channel
checked_df.write \
    .mode("overwrite") \
    .parquet(PROCESSED_PATH)

# ── Step 6: Write Data Quality Metrics to CloudWatch ──────────────────────────
# TODO: Publish custom metrics so the monitoring dashboard (Lab 6) can track ETL health.
#
# import boto3
# cloudwatch = boto3.client("cloudwatch", region_name="us-east-1")
# cloudwatch.put_metric_data(
#     Namespace="NorthStar/DataPipeline",
#     MetricData=[
#         {
#             "MetricName": "TransactionRecordCount",
#             "Value": checked_df.count(),
#             "Unit": "Count",
#             "Dimensions": [{"Name": "JobName", "Value": args["JOB_NAME"]}],
#         },
#     ],
# )

logger.info("✅ NorthStar transaction ETL completed successfully")
job.commit()
