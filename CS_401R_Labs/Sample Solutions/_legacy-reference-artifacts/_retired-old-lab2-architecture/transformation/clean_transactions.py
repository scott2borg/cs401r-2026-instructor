"""
NorthStar Retail AI Platform — CS 401R Lab 2 Sample Solution
clean_transactions.py

Standalone pandas script for local testing of transaction transformation logic.

This module intentionally avoids any Glue or PySpark dependency so that
data scientists can run and validate transformation logic on a laptop without
a cluster.  The functions here mirror the logic in batch_ingestion.py; keeping
them in sync is part of the software contract between the platform and ML teams.

Functions:
  normalize_store_id       — Canonicalize legacy S{3} store IDs.
  parse_transaction_date   — Parse raw date strings to datetime objects.
  filter_returns           — Optionally exclude return transactions.
  compute_daily_summary    — Aggregate by date + channel.
  main                     — Full pipeline: read → transform → write.

Usage:
    python clean_transactions.py \
        --input-dir  northstar-data/ \
        --output-dir northstar-processed/

Author: CS 401R Sample Solution
"""

import re
import os
import argparse
import logging
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
logger = logging.getLogger("northstar.clean_transactions")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LEGACY_STORE_ID_RE = re.compile(r"^S(\d{3})$")


# ---------------------------------------------------------------------------
# Transformation functions
# ---------------------------------------------------------------------------

def normalize_store_id(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize legacy store_id formats to the canonical STORE-{3 digits} pattern.

    Background:
        Pre-March 2024, POS systems emitted store IDs as "S{3 digits}" (e.g. "S042").
        The canonical format adopted March 2024 onward is "STORE-{3 digits}".
        Online transactions carry store_id = "ONLINE" and are left unchanged.

    Transformation applied:
        S042  →  STORE-042
        S001  →  STORE-001
        ONLINE  →  ONLINE  (no change)
        STORE-042  →  STORE-042  (already canonical, no change)

    Args:
        df: DataFrame with a store_id column (string).

    Returns:
        DataFrame with store_id values in canonical format.

    Raises:
        KeyError: If store_id column is absent.
    """
    if "store_id" not in df.columns:
        raise KeyError("normalize_store_id: 'store_id' column not found in DataFrame.")

    def _normalize(val: str) -> str:
        if pd.isna(val):
            return val
        m = LEGACY_STORE_ID_RE.match(str(val).strip())
        if m:
            return f"STORE-{m.group(1)}"
        return val

    before_unique = df["store_id"].nunique()
    df = df.copy()
    df["store_id"] = df["store_id"].apply(_normalize)
    after_unique   = df["store_id"].nunique()

    logger.info(
        "normalize_store_id: unique store_id values %d → %d (after canonicalization)",
        before_unique,
        after_unique,
    )
    return df


def parse_transaction_date(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parse the transaction_date column from string to a timezone-aware datetime.

    The raw transaction feed delivers ISO-8601 UTC strings:
        "2026-06-15T22:31:00Z"

    pandas.to_datetime with utc=True handles this directly and converts any
    timezone-naive strings to UTC. Records that fail to parse are set to NaT
    and logged so they can be quarantined upstream.

    Args:
        df: DataFrame with a transaction_date column (string or object dtype).

    Returns:
        DataFrame with transaction_date as DatetimeTZDtype (UTC).

    Raises:
        KeyError: If transaction_date column is absent.
    """
    if "transaction_date" not in df.columns:
        raise KeyError(
            "parse_transaction_date: 'transaction_date' column not found."
        )

    df = df.copy()
    before_nulls = df["transaction_date"].isna().sum()

    df["transaction_date"] = pd.to_datetime(
        df["transaction_date"],
        utc=True,
        errors="coerce",   # Unparseable → NaT instead of ValueError
    )

    after_nulls = df["transaction_date"].isna().sum()
    new_nulls   = after_nulls - before_nulls
    if new_nulls > 0:
        logger.warning(
            "parse_transaction_date: %d records failed to parse → NaT.", new_nulls
        )

    logger.info(
        "parse_transaction_date: %d records have valid transaction_date.",
        df["transaction_date"].notna().sum(),
    )
    return df


def filter_returns(
    df: pd.DataFrame,
    include_returns: bool = False,
) -> pd.DataFrame:
    """
    Optionally filter out return / refund transactions.

    Return transactions (return_flag = True) represent credits to the customer
    and are typically excluded from revenue calculations and feature engineering
    windows.  They may be included when modelling return behaviour explicitly.

    Args:
        df             : DataFrame with a return_flag column (bool or 0/1 int).
        include_returns: If True, all records are returned unchanged.
                         If False (default), return_flag=True rows are dropped.

    Returns:
        Filtered DataFrame.

    Raises:
        KeyError: If return_flag column is absent.
    """
    if "return_flag" not in df.columns:
        raise KeyError("filter_returns: 'return_flag' column not found.")

    if include_returns:
        logger.info("filter_returns: include_returns=True — keeping all records.")
        return df

    before = len(df)
    df     = df[~df["return_flag"].astype(bool)].copy()
    after  = len(df)
    logger.info(
        "filter_returns: removed %d return records, kept %d.", before - after, after
    )
    return df


def compute_daily_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate transaction data by calendar date and channel.

    Groups by the date portion of transaction_date and the channel column,
    computing the following metrics per group:

      total_revenue      : Sum of transaction_amount (gross, includes tax).
      transaction_count  : Number of distinct transactions.
      avg_basket_size    : Mean transaction_amount per transaction.
      promo_usage_rate   : Fraction of transactions that used a promotion_code.

    Assumptions:
      - transaction_date is already a datetime column (run parse_transaction_date first).
      - return_flag=True records have been filtered out or intentionally included.
      - A non-null, non-empty promotion_code is treated as "used a promotion."

    Args:
        df: Cleaned transactions DataFrame.

    Returns:
        DataFrame indexed by (transaction_date_utc, channel) with the four
        aggregate columns described above.  Sorted by date descending.

    Raises:
        KeyError: If any required column is missing.
    """
    required = ["transaction_date", "channel", "transaction_amount", "promotion_code"]
    missing  = [c for c in required if c not in df.columns]
    if missing:
        raise KeyError(f"compute_daily_summary: missing columns: {missing}")

    df = df.copy()

    # Extract date component for grouping
    df["_txn_date"] = pd.to_datetime(df["transaction_date"]).dt.date

    # Boolean promo flag: True when promotion_code is non-null and non-empty
    df["_promo_used"] = (
        df["promotion_code"].notna()
        & df["promotion_code"].astype(str).str.strip().ne("")
    )

    summary = (
        df.groupby(["_txn_date", "channel"], sort=True)
        .agg(
            total_revenue=("transaction_amount", "sum"),
            transaction_count=("transaction_amount", "count"),
            avg_basket_size=("transaction_amount", "mean"),
            promo_usage_rate=("_promo_used", "mean"),
        )
        .reset_index()
        .rename(columns={"_txn_date": "transaction_date_utc"})
        .sort_values("transaction_date_utc", ascending=False)
    )

    logger.info(
        "compute_daily_summary: produced %d date-channel rows from %d transactions.",
        len(summary),
        len(df),
    )
    return summary


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def main(input_dir: str, output_dir: str, include_returns: bool = False) -> None:
    """
    Full local transformation pipeline.

    Steps:
      1. Read transactions.parquet from input_dir.
      2. Apply normalize_store_id.
      3. Apply parse_transaction_date.
      4. Apply filter_returns (controlled by include_returns flag).
      5. Compute daily summary.
      6. Write cleaned transactions + daily summary to output_dir.

    Output files:
      {output_dir}/transactions_cleaned.parquet   — row-level cleaned data
      {output_dir}/daily_summary.parquet          — aggregated daily metrics

    Args:
        input_dir      : Directory containing transactions.parquet.
        output_dir     : Directory to write output files.
        include_returns: Forwarded to filter_returns.

    Raises:
        FileNotFoundError: If transactions.parquet is not found.
    """
    input_path = Path(input_dir) / "transactions.parquet"
    if not input_path.exists():
        raise FileNotFoundError(f"transactions.parquet not found at: {input_path}")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    logger.info("Reading transactions from: %s", input_path)
    df = pd.read_parquet(input_path)
    logger.info("Loaded %d records.", len(df))

    # Apply transformations
    df = normalize_store_id(df)
    df = parse_transaction_date(df)
    df = filter_returns(df, include_returns=include_returns)

    # Write cleaned transactions
    cleaned_out = output_path / "transactions_cleaned.parquet"
    df.to_parquet(cleaned_out, index=False)
    logger.info("Wrote cleaned transactions to: %s", cleaned_out)

    # Compute and write daily summary
    summary_df  = compute_daily_summary(df)
    summary_out = output_path / "daily_summary.parquet"
    summary_df.to_parquet(summary_out, index=False)
    logger.info("Wrote daily summary to: %s", summary_out)

    # Print a quick preview for interactive use
    print("\n=== Daily Summary Preview (top 10) ===")
    print(summary_df.head(10).to_string(index=False))
    print(f"\nCleaned: {len(df):,} transactions → {len(summary_df)} date-channel rows")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="NorthStar local transaction cleaning pipeline"
    )
    parser.add_argument(
        "--input-dir",
        default="northstar-data",
        help="Directory containing transactions.parquet (default: northstar-data/)",
    )
    parser.add_argument(
        "--output-dir",
        default="northstar-processed",
        help="Directory to write output files (default: northstar-processed/)",
    )
    parser.add_argument(
        "--include-returns",
        action="store_true",
        help="Include return transactions (return_flag=True) in output.",
    )
    args = parser.parse_args()

    main(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        include_returns=args.include_returns,
    )
