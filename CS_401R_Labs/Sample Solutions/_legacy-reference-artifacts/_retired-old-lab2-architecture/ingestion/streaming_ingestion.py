"""
NorthStar Retail AI Platform — CS 401R Lab 2 Sample Solution
streaming_ingestion.py

Simulated streaming ingestion pipeline for clickstream events.

Architecture:
  Producer  : Reads clickstream Parquet, filters bot traffic, masks PII,
              batches records, and publishes to Kinesis Data Streams.
  Consumer  : AWS Lambda handler that consumes from the same Kinesis stream,
              validates each event record, and writes to S3 processed zone.

Key design decisions:
  - Kinesis put_records() in batches of 500 (API max = 500 records per call).
  - Bot filtering applied at producer side to reduce stream volume.
  - search_query PII masking: any query that looks like an email address is
    SHA-256 hashed before entering the stream.
  - Lambda consumer writes Parquet partitioned by event date for Athena
    compatibility.

Usage (producer):
    python streaming_ingestion.py --input-path northstar-data/clickstream.parquet
                                  --stream-name northstar-clickstream

Author: CS 401R Sample Solution
"""

import os
import re
import sys
import json
import time
import base64
import hashlib
import argparse
import logging
from datetime import datetime, timezone
from typing import Any

import boto3
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# ---------------------------------------------------------------------------
# Configuration & logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
logger = logging.getLogger("northstar.streaming")

KINESIS_STREAM_NAME = os.environ.get("KINESIS_STREAM_NAME", "northstar-clickstream")
PROCESSED_BUCKET    = os.environ.get("PROCESSED_BUCKET", "northstar-processed")
REGION              = os.environ.get("AWS_REGION", "us-east-1")
KINESIS_BATCH_SIZE  = 500           # Kinesis put_records hard limit
BOT_MIN_EVENTS      = 3             # Sessions with fewer events are discarded
BOT_MIN_DURATION_S  = 5            # Sessions shorter than 5 s are discarded

REQUIRED_EVENT_COLUMNS = {
    "event_id", "session_id", "event_timestamp", "event_type", "device_type"
}

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def sha256_hash(value: str) -> str:
    """Return the hex-encoded SHA-256 digest of value."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def mask_pii(record: dict) -> dict:
    """
    Mask PII in a single clickstream event record.

    Specifically: if search_query looks like an email address (matches the
    simple EMAIL_PATTERN regex), replace it with its SHA-256 hash.  All other
    fields are returned unchanged.

    Note: this is a heuristic. A production system would also run search_query
    through a more robust PII detection library (e.g. AWS Comprehend PII) for
    phone numbers, SSNs, etc.
    """
    query = record.get("search_query")
    if query and EMAIL_PATTERN.match(str(query).strip()):
        record = {**record, "search_query": sha256_hash(query)}
    return record


# ---------------------------------------------------------------------------
# Bot traffic filtering
# ---------------------------------------------------------------------------

def filter_bot_sessions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove sessions that exhibit bot-like behaviour.

    Heuristics applied:
      1. Sessions with fewer than BOT_MIN_EVENTS (3) events are dropped.
         Real users almost always view multiple pages.
      2. Sessions with a total duration under BOT_MIN_DURATION_S (5 seconds)
         are dropped. Bots process pages near-instantaneously.

    Duration is computed as (max_ts - min_ts) within each session_id,
    where event_timestamp is in milliseconds UTC.

    Returns a filtered DataFrame with bot sessions removed.
    """
    logger.info("Filtering bot traffic …")
    before = len(df)

    session_stats = (
        df.groupby("session_id")
        .agg(
            event_count=("event_id", "count"),
            min_ts=("event_timestamp", "min"),
            max_ts=("event_timestamp", "max"),
        )
        .reset_index()
    )
    session_stats["duration_s"] = (
        (session_stats["max_ts"] - session_stats["min_ts"]) / 1000.0
    )

    valid_sessions = session_stats[
        (session_stats["event_count"] >= BOT_MIN_EVENTS)
        & (session_stats["duration_s"] >= BOT_MIN_DURATION_S)
    ]["session_id"]

    filtered = df[df["session_id"].isin(valid_sessions)]
    after = len(filtered)
    logger.info(
        "Bot filter: removed %d records (%d sessions). Kept %d records.",
        before - after,
        len(session_stats) - len(valid_sessions),
        after,
    )
    return filtered


# ---------------------------------------------------------------------------
# Kinesis Producer
# ---------------------------------------------------------------------------

class ClickstreamProducer:
    """
    Reads clickstream Parquet from a local path (or S3 URI), applies bot
    filtering and PII masking, then publishes records to a Kinesis Data Stream
    in batches of KINESIS_BATCH_SIZE (500).

    Args:
        input_path   : Local file path or s3:// URI to the clickstream Parquet.
        stream_name  : Kinesis stream name.  Defaults to KINESIS_STREAM_NAME env var.
        region_name  : AWS region.
        dry_run      : If True, log what would be sent without calling Kinesis.
    """

    def __init__(
        self,
        input_path: str,
        stream_name: str = KINESIS_STREAM_NAME,
        region_name: str = REGION,
        dry_run: bool = False,
    ):
        self.input_path  = input_path
        self.stream_name = stream_name
        self.dry_run     = dry_run

        if not dry_run:
            self.kinesis = boto3.client("kinesis", region_name=region_name)
        else:
            self.kinesis = None

        logger.info(
            "ClickstreamProducer initialised. stream=%s dry_run=%s",
            stream_name,
            dry_run,
        )

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _load_clickstream(self) -> pd.DataFrame:
        """
        Load the clickstream Parquet file into a pandas DataFrame.

        Supports both local paths and s3:// URIs (via pyarrow S3FileSystem
        for S3, or plain filesystem for local).
        """
        logger.info("Loading clickstream from: %s", self.input_path)
        try:
            df = pd.read_parquet(self.input_path)
            logger.info("Loaded %d raw clickstream records.", len(df))
            return df
        except FileNotFoundError:
            logger.error("Input file not found: %s", self.input_path)
            raise
        except Exception as exc:
            logger.error("Failed to load clickstream: %s", exc)
            raise

    # ------------------------------------------------------------------
    # Record preparation
    # ------------------------------------------------------------------

    def _prepare_records(self, df: pd.DataFrame) -> list[dict]:
        """
        Convert DataFrame rows to JSON-serialisable dicts, apply PII masking,
        and add a pipeline metadata field (_producer_ts).
        """
        producer_ts = datetime.now(timezone.utc).isoformat()
        records = []
        for row in df.to_dict(orient="records"):
            # Convert numpy types to Python native for JSON serialisation
            clean = {
                k: (v.item() if hasattr(v, "item") else v)
                for k, v in row.items()
            }
            clean["_producer_ts"] = producer_ts
            clean = mask_pii(clean)
            records.append(clean)
        return records

    # ------------------------------------------------------------------
    # Kinesis publishing
    # ------------------------------------------------------------------

    def _put_batch(self, batch: list[dict]) -> int:
        """
        Send one batch of records to Kinesis using put_records().

        Uses session_id as the partition key so that all events from the same
        session land on the same shard (preserving order within a session).

        Returns the number of failed records in this batch (ideally 0).
        """
        kinesis_records = [
            {
                "Data": json.dumps(r, default=str).encode("utf-8"),
                "PartitionKey": str(r.get("session_id", "unknown")),
            }
            for r in batch
        ]

        if self.dry_run:
            logger.info("[DRY RUN] Would send %d records to Kinesis.", len(batch))
            return 0

        try:
            response = self.kinesis.put_records(
                StreamName=self.stream_name,
                Records=kinesis_records,
            )
            failed = response.get("FailedRecordCount", 0)
            if failed > 0:
                logger.warning(
                    "Kinesis put_records: %d/%d records failed.", failed, len(batch)
                )
            return failed
        except self.kinesis.exceptions.ResourceNotFoundException:
            logger.error(
                "Kinesis stream '%s' not found. Check stream name and region.",
                self.stream_name,
            )
            raise
        except Exception as exc:
            logger.error("Kinesis put_records error: %s", exc)
            raise

    # ------------------------------------------------------------------
    # Main produce loop
    # ------------------------------------------------------------------

    def produce(self):
        """
        Full producer pipeline:
          1. Load clickstream Parquet.
          2. Filter bot sessions.
          3. Prepare records (PII masking, type normalisation).
          4. Batch and publish to Kinesis in chunks of KINESIS_BATCH_SIZE.

        Returns a summary dict with total_records, batches_sent, total_failed.
        """
        df = self._load_clickstream()
        df = filter_bot_sessions(df)
        records = self._prepare_records(df)

        total    = len(records)
        batches  = 0
        failed   = 0

        logger.info(
            "Publishing %d records to Kinesis stream '%s' in batches of %d …",
            total,
            self.stream_name,
            KINESIS_BATCH_SIZE,
        )

        for start in range(0, total, KINESIS_BATCH_SIZE):
            batch = records[start : start + KINESIS_BATCH_SIZE]
            failed += self._put_batch(batch)
            batches += 1
            logger.info(
                "Batch %d sent (%d/%d records).", batches, start + len(batch), total
            )

        summary = {
            "total_records": total,
            "batches_sent":  batches,
            "total_failed":  failed,
        }
        logger.info("Producer complete: %s", summary)
        return summary


# ---------------------------------------------------------------------------
# Lambda Consumer (Kinesis trigger)
# ---------------------------------------------------------------------------

def _validate_event_record(record: dict) -> tuple[bool, list[str]]:
    """
    Validate that a decoded Kinesis record contains the required fields.

    Returns (is_valid, list_of_missing_fields).
    """
    missing = [f for f in REQUIRED_EVENT_COLUMNS if not record.get(f)]
    return len(missing) == 0, missing


def _partition_path(event_ts_ms: int | None) -> str:
    """
    Convert an event_timestamp (ms epoch UTC) to a S3 partition path fragment
    in the form year=YYYY/month=MM/day=DD.

    Falls back to today's UTC date if the timestamp is null or unparseable.
    """
    try:
        dt = datetime.fromtimestamp(event_ts_ms / 1000.0, tz=timezone.utc)
    except (TypeError, ValueError, OSError):
        dt = datetime.now(timezone.utc)
    return f"year={dt.year}/month={dt.month:02d}/day={dt.day:02d}"


def handler(event: dict, context: Any) -> dict:
    """
    AWS Lambda handler — triggered by the northstar-clickstream Kinesis stream.

    Processing steps for each batch of Kinesis records:
      1. Base64-decode and JSON-parse each record's Data field.
      2. Validate required schema fields; collect invalid records separately.
      3. Group valid records by partition date.
      4. Write each partition group to S3 as a Parquet file.

    The handler deliberately does NOT raise on partial failures — it logs
    invalid records and continues so a single bad record does not block the
    entire batch (Kinesis would re-deliver the whole shard segment on error).

    Environment variables expected:
      PROCESSED_BUCKET : S3 bucket for the processed clickstream zone.
      AWS_REGION       : AWS region (set automatically by Lambda runtime).

    Returns a summary dict for CloudWatch Logs visibility.
    """
    processed_bucket = os.environ.get("PROCESSED_BUCKET", PROCESSED_BUCKET)
    region           = os.environ.get("AWS_REGION", REGION)
    s3               = boto3.client("s3", region_name=region)

    kinesis_records  = event.get("Records", [])
    logger.info("Lambda invoked with %d Kinesis records.", len(kinesis_records))

    valid_records:   list[dict] = []
    invalid_records: list[dict] = []

    # Step 1 & 2: Decode and validate
    for kr in kinesis_records:
        try:
            raw_data = base64.b64decode(kr["kinesis"]["data"]).decode("utf-8")
            record   = json.loads(raw_data)
        except Exception as exc:
            logger.warning("Failed to decode Kinesis record: %s", exc)
            invalid_records.append({"raw": kr, "error": str(exc)})
            continue

        is_valid, missing = _validate_event_record(record)
        if is_valid:
            valid_records.append(record)
        else:
            logger.warning(
                "Invalid record (missing %s): event_id=%s",
                missing,
                record.get("event_id", "UNKNOWN"),
            )
            invalid_records.append({**record, "_validation_errors": missing})

    logger.info(
        "Validation complete: valid=%d, invalid=%d",
        len(valid_records),
        len(invalid_records),
    )

    if not valid_records:
        logger.info("No valid records to write. Exiting.")
        return {"valid": 0, "invalid": len(invalid_records)}

    # Step 3: Group by partition date
    partition_groups: dict[str, list[dict]] = {}
    for rec in valid_records:
        part = _partition_path(rec.get("event_timestamp"))
        partition_groups.setdefault(part, []).append(rec)

    # Step 4: Write each partition group to S3 as Parquet
    for part_path, part_records in partition_groups.items():
        part_df = pd.DataFrame(part_records)
        table   = pa.Table.from_pandas(part_df, preserve_index=False)
        buf     = pa.BufferOutputStream()
        pq.write_table(table, buf)

        ts_suffix = int(time.time() * 1000)
        s3_key    = (
            f"processed/clickstream/{part_path}/events_{ts_suffix}.parquet"
        )

        try:
            s3.put_object(
                Bucket=processed_bucket,
                Key=s3_key,
                Body=buf.getvalue().to_pybytes(),
                ContentType="application/octet-stream",
            )
            logger.info(
                "Wrote %d records to s3://%s/%s",
                len(part_records),
                processed_bucket,
                s3_key,
            )
        except Exception as exc:
            logger.error(
                "Failed to write partition %s to S3: %s", part_path, exc
            )
            # Continue with remaining partitions

    return {
        "valid":   len(valid_records),
        "invalid": len(invalid_records),
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="NorthStar Clickstream Kinesis Producer"
    )
    parser.add_argument(
        "--input-path",
        default="northstar-data/clickstream.parquet",
        help="Local or S3 path to clickstream Parquet file.",
    )
    parser.add_argument(
        "--stream-name",
        default=KINESIS_STREAM_NAME,
        help="Kinesis Data Stream name.",
    )
    parser.add_argument(
        "--region",
        default=REGION,
        help="AWS region.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and prepare records without sending to Kinesis.",
    )
    args = parser.parse_args()

    producer = ClickstreamProducer(
        input_path=args.input_path,
        stream_name=args.stream_name,
        region_name=args.region,
        dry_run=args.dry_run,
    )
    result = producer.produce()
    print(json.dumps(result, indent=2))
