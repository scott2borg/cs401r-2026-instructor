"""
NorthStar Retail AI Platform — CS 401R Lab 2 Sample Solution
compute_features.py

Feature engineering for the customer churn prediction model.

All features are computed relative to FEATURE_SNAPSHOT_DATE to prevent
temporal data leakage.  Each function documents its leakage assessment
explicitly so reviewers can audit the feature set before training.

Leakage audit convention:
  SAFE         — Feature window closes at or before snapshot_date.
  REQUIRES CARE — Feature is safe to compute, but the underlying column also
                  appears elsewhere in the training set; document the
                  relationship so the modelling team can decide whether to
                  include both.
  UNSAFE       — Feature incorporates information from after snapshot_date.
                  (None in this set — all UNSAFE features should be removed.)

Reference date: FEATURE_SNAPSHOT_DATE = "2026-06-01"

Usage:
    python compute_features.py \
        --data-dir  northstar-data/ \
        --output-dir northstar-processed/

Author: CS 401R Sample Solution
"""

import os
import argparse
import logging
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
logger = logging.getLogger("northstar.compute_features")

FEATURE_SNAPSHOT_DATE = "2026-06-01"   # Reference point for ALL temporal features
_SNAPSHOT_DT          = pd.Timestamp(FEATURE_SNAPSHOT_DATE, tz="UTC")
NO_PURCHASE_SENTINEL  = 999            # Sentinel for customers with no transactions


# ---------------------------------------------------------------------------
# Helper — clip transactions to a look-back window
# ---------------------------------------------------------------------------

def _transactions_in_window(
    transactions_df: pd.DataFrame,
    days: int,
) -> pd.DataFrame:
    """
    Return only transactions within the trailing `days`-day window ending at
    FEATURE_SNAPSHOT_DATE (exclusive upper bound, i.e. < snapshot_date).

    Also excludes return transactions (return_flag = True).  Return
    transactions represent credits and would artificially suppress spend
    and frequency features.

    Args:
        transactions_df: Full transactions DataFrame with transaction_date (UTC).
        days           : Number of days to look back from snapshot_date.

    Returns:
        Filtered DataFrame of non-return transactions in the window.
    """
    cutoff = _SNAPSHOT_DT - pd.Timedelta(days=days)
    mask   = (
        (transactions_df["transaction_date"] >= cutoff)
        & (transactions_df["transaction_date"] <  _SNAPSHOT_DT)
        & (~transactions_df["return_flag"].astype(bool))
    )
    return transactions_df[mask].copy()


# ---------------------------------------------------------------------------
# Required Feature 1: days_since_last_purchase
# ---------------------------------------------------------------------------

def compute_days_since_last_purchase(
    transactions_df: pd.DataFrame,
    customers_df: pd.DataFrame,
) -> pd.Series:
    """
    Recency signal: days between each customer's last purchase and snapshot_date.

    Leakage assessment: SAFE — only uses transactions before snapshot_date.
    The window is deliberately left open (all historical transactions) rather
    than a fixed look-back because recency has diminishing importance at longer
    horizons and this open window captures "has this customer ever purchased?"

    Sentinel value: customers with NO transactions in the dataset receive
    NO_PURCHASE_SENTINEL (999).  This is preferable to NaN because tree-based
    models (XGBoost, LightGBM) handle sentinel ints cleanly.

    Args:
        transactions_df: Full transactions DataFrame.
        customers_df   : Customers DataFrame (provides the complete customer_id set).

    Returns:
        pd.Series indexed by customer_id, named 'days_since_last_purchase'.
    """
    # Filter to pre-snapshot, non-return transactions
    past_txns = transactions_df[
        (transactions_df["transaction_date"] < _SNAPSHOT_DT)
        & (~transactions_df["return_flag"].astype(bool))
    ].copy()

    last_purchase = (
        past_txns.groupby("customer_id")["transaction_date"]
        .max()
        .rename("last_purchase_date")
    )

    # Align to all customers in the customer table
    all_customers = customers_df[["customer_id"]].drop_duplicates().set_index("customer_id")
    result        = all_customers.join(last_purchase)

    days = (
        (_SNAPSHOT_DT - result["last_purchase_date"])
        .dt.days
        .fillna(NO_PURCHASE_SENTINEL)
        .astype(int)
        .rename("days_since_last_purchase")
    )

    logger.info(
        "days_since_last_purchase: min=%d, max=%d, n_no_purchase=%d",
        days[days < NO_PURCHASE_SENTINEL].min() if (days < NO_PURCHASE_SENTINEL).any() else 0,
        days[days < NO_PURCHASE_SENTINEL].max() if (days < NO_PURCHASE_SENTINEL).any() else 0,
        (days == NO_PURCHASE_SENTINEL).sum(),
    )
    return days


# ---------------------------------------------------------------------------
# Required Feature 2: purchase_frequency_90d
# ---------------------------------------------------------------------------

def compute_purchase_frequency_90d(transactions_df: pd.DataFrame) -> pd.Series:
    """
    Frequency signal: number of non-return purchases in the trailing 90 days.

    Leakage assessment: SAFE — the 90-day window ends at snapshot_date.
    Returns are excluded because they do not represent a purchase decision;
    including them would undercount true purchase frequency.

    Args:
        transactions_df: Full transactions DataFrame.

    Returns:
        pd.Series indexed by customer_id, named 'purchase_frequency_90d'.
        Customers with no qualifying transactions receive 0.
    """
    window_df = _transactions_in_window(transactions_df, days=90)

    freq = (
        window_df.groupby("customer_id")["transaction_id"]
        .count()
        .rename("purchase_frequency_90d")
    )

    logger.info(
        "purchase_frequency_90d: mean=%.2f, max=%d",
        freq.mean(),
        freq.max(),
    )
    return freq


# ---------------------------------------------------------------------------
# Required Feature 3: avg_basket_size_6m
# ---------------------------------------------------------------------------

def compute_avg_basket_size_6m(transactions_df: pd.DataFrame) -> pd.Series:
    """
    Value signal: mean gross transaction_amount over the past 6 months.

    Leakage assessment: SAFE — the 6-month window ends at snapshot_date.

    Excludes:
      - Return transactions (return_flag = True) — credits inflate the mean.
      - Zero-amount transactions (e.g. loyalty redemptions) — they represent
        a different behavioural signal and would pull down the basket average.

    Args:
        transactions_df: Full transactions DataFrame.

    Returns:
        pd.Series indexed by customer_id, named 'avg_basket_size_6m'.
        Customers with no qualifying transactions receive NaN.
    """
    window_df = _transactions_in_window(transactions_df, days=180)
    window_df = window_df[window_df["transaction_amount"] > 0]

    avg_basket = (
        window_df.groupby("customer_id")["transaction_amount"]
        .mean()
        .rename("avg_basket_size_6m")
    )

    logger.info(
        "avg_basket_size_6m: mean=$%.2f, median=$%.2f, n_null=%d",
        avg_basket.mean(),
        avg_basket.median(),
        avg_basket.isna().sum(),
    )
    return avg_basket


# ---------------------------------------------------------------------------
# Required Feature 4: category_diversity_score
# ---------------------------------------------------------------------------

def compute_category_diversity_score(transactions_df: pd.DataFrame) -> pd.Series:
    """
    Breadth signal: count of distinct product categories purchased in past 6 months,
    normalized to [0, 1] by dividing by the maximum possible (12 categories).

    A customer who has purchased across many categories is arguably more embedded
    in the NorthStar ecosystem and less likely to churn.

    Leakage assessment: SAFE — the 6-month window ends at snapshot_date.

    Implementation note:
        product_categories is a pipe-delimited string (e.g. "Apparel|Home|Beauty").
        We explode this to count unique categories per customer.

    Args:
        transactions_df: Full transactions DataFrame.

    Returns:
        pd.Series indexed by customer_id, named 'category_diversity_score'.
        Range: 0.0 (no purchases) to 1.0 (all 12 categories).
    """
    MAX_CATEGORIES = 12
    window_df      = _transactions_in_window(transactions_df, days=180)

    # Explode pipe-delimited categories into individual rows
    cats = (
        window_df[["customer_id", "product_categories"]]
        .dropna(subset=["product_categories"])
        .assign(
            category=lambda d: d["product_categories"].str.split("|")
        )
        .explode("category")
        .assign(category=lambda d: d["category"].str.strip())
    )

    diversity = (
        cats.groupby("customer_id")["category"]
        .nunique()
        .div(MAX_CATEGORIES)
        .clip(upper=1.0)
        .rename("category_diversity_score")
    )

    logger.info(
        "category_diversity_score: mean=%.3f, max=%.3f",
        diversity.mean(),
        diversity.max(),
    )
    return diversity


# ---------------------------------------------------------------------------
# Required Feature 5: online_to_store_ratio
# ---------------------------------------------------------------------------

def compute_online_to_store_ratio(transactions_df: pd.DataFrame) -> pd.Series:
    """
    Channel preference signal: proportion of transactions made online vs. in-store
    in the past 90 days.

    online_ratio = online_transactions / total_transactions

    Leakage assessment: SAFE — uses channel information from past transactions only.

    Edge cases:
      - Zero total transactions → 0.0 (not NaN) because absence of activity is
        a meaningful signal (customer hasn't purchased recently).
      - Ratio is bounded [0.0, 1.0] by construction.

    Args:
        transactions_df: Full transactions DataFrame.

    Returns:
        pd.Series indexed by customer_id, named 'online_to_store_ratio'.
    """
    window_df = _transactions_in_window(transactions_df, days=90)

    total_counts = (
        window_df.groupby("customer_id")["transaction_id"].count()
    )
    online_counts = (
        window_df[window_df["channel"] == "online"]
        .groupby("customer_id")["transaction_id"]
        .count()
    )

    ratio = (
        online_counts
        .reindex(total_counts.index, fill_value=0)
        .div(total_counts)
        .fillna(0.0)
        .rename("online_to_store_ratio")
    )

    logger.info(
        "online_to_store_ratio: mean=%.3f, pure_online=%.1f%%, pure_store=%.1f%%",
        ratio.mean(),
        (ratio == 1.0).mean() * 100,
        (ratio == 0.0).mean() * 100,
    )
    return ratio


# ---------------------------------------------------------------------------
# Required Feature 6: promo_response_rate
# ---------------------------------------------------------------------------

def compute_promo_response_rate(transactions_df: pd.DataFrame) -> pd.Series:
    """
    Promotion sensitivity signal: fraction of transactions in the past 12 months
    that used a promotion code.

    promo_response_rate = promo_transactions / total_transactions (12m window)

    A high promo_response_rate may indicate the customer is deal-driven and
    may churn when promotions are not offered.

    Leakage assessment: SAFE — uses promotion_code from past transactions only.
    promotion_discount is NOT used here (it is correlated with transaction_amount
    and would be redundant given avg_basket_size_6m).

    Args:
        transactions_df: Full transactions DataFrame.

    Returns:
        pd.Series indexed by customer_id, named 'promo_response_rate'.
        Customers with no transactions in the window receive NaN.
    """
    window_df = _transactions_in_window(transactions_df, days=365)

    window_df = window_df.copy()
    window_df["_promo_used"] = (
        window_df["promotion_code"].notna()
        & window_df["promotion_code"].astype(str).str.strip().ne("")
    )

    rate = (
        window_df.groupby("customer_id")["_promo_used"]
        .mean()
        .rename("promo_response_rate")
    )

    logger.info(
        "promo_response_rate: mean=%.3f, max=%.3f",
        rate.mean(),
        rate.max(),
    )
    return rate


# ---------------------------------------------------------------------------
# Required Feature 7: loyalty_tier_duration_days
# ---------------------------------------------------------------------------

def compute_loyalty_tier_duration_days(customers_df: pd.DataFrame) -> pd.Series:
    """
    Loyalty tenure signal: days at current loyalty tier.

    Implementation: approximated as days since account signup_date because
    a complete tier-change history is not available in the current data model.
    A full implementation would join against a tier_change_history table.

    Leakage assessment: REQUIRES CARE
      - loyalty_tier_duration_days is SAFE to compute (uses signup_date only).
      - However, loyalty_tier is also included in the feature set as a separate
        column.  The two features are correlated: longer tenure → higher tiers.
        Models may double-count this signal.  Include both, but document the
        relationship in the model card.
      - Do NOT use churn_date or churn_label when computing this feature.

    Args:
        customers_df: Customers DataFrame with signup_date column.

    Returns:
        pd.Series indexed by customer_id, named 'loyalty_tier_duration_days'.
    """
    df = customers_df[["customer_id", "signup_date"]].copy()
    df["signup_date"] = pd.to_datetime(df["signup_date"], utc=True, errors="coerce")

    duration = (
        (_SNAPSHOT_DT - df.set_index("customer_id")["signup_date"])
        .dt.days
        .rename("loyalty_tier_duration_days")
    )

    logger.info(
        "loyalty_tier_duration_days: min=%d, max=%d, n_null=%d",
        int(duration.min()) if duration.notna().any() else 0,
        int(duration.max()) if duration.notna().any() else 0,
        duration.isna().sum(),
    )
    return duration


# ---------------------------------------------------------------------------
# Additional Feature A: purchase_frequency_180d
# ---------------------------------------------------------------------------

def compute_purchase_frequency_180d(transactions_df: pd.DataFrame) -> pd.Series:
    """
    Frequency signal at 6-month horizon: number of non-return purchases in
    the trailing 180 days.

    Leakage assessment: SAFE — 180-day window ends at snapshot_date.

    Paired with purchase_frequency_90d, this allows the model to distinguish
    customers who have recently accelerated or decelerated their purchase rate
    (e.g. 90d=10, 180d=11 → recent acceleration; 90d=1, 180d=10 → recent drop-off).

    Args:
        transactions_df: Full transactions DataFrame.

    Returns:
        pd.Series indexed by customer_id, named 'purchase_frequency_180d'.
    """
    window_df = _transactions_in_window(transactions_df, days=180)

    freq = (
        window_df.groupby("customer_id")["transaction_id"]
        .count()
        .rename("purchase_frequency_180d")
    )

    logger.info(
        "purchase_frequency_180d: mean=%.2f, max=%d",
        freq.mean(),
        freq.max(),
    )
    return freq


# ---------------------------------------------------------------------------
# Additional Feature B: total_spend_90d
# ---------------------------------------------------------------------------

def compute_total_spend_90d(transactions_df: pd.DataFrame) -> pd.Series:
    """
    Monetary signal: total gross transaction_amount in the trailing 90 days.

    Leakage assessment: SAFE — 90-day window ends at snapshot_date.

    This is the M in RFM (Recency, Frequency, Monetary) framework.  Combined
    with avg_basket_size_6m and purchase_frequency_90d, it gives the model
    a comprehensive value signal without any future information.

    Args:
        transactions_df: Full transactions DataFrame.

    Returns:
        pd.Series indexed by customer_id, named 'total_spend_90d'.
        Customers with no qualifying transactions receive 0.0.
    """
    window_df = _transactions_in_window(transactions_df, days=90)
    window_df = window_df[window_df["transaction_amount"] > 0]

    spend = (
        window_df.groupby("customer_id")["transaction_amount"]
        .sum()
        .rename("total_spend_90d")
    )

    logger.info(
        "total_spend_90d: mean=$%.2f, max=$%.2f",
        spend.mean(),
        spend.max(),
    )
    return spend


# ---------------------------------------------------------------------------
# Additional Feature C: clickstream_sessions_30d
# ---------------------------------------------------------------------------

def compute_clickstream_sessions_30d(clickstream_df: pd.DataFrame) -> pd.Series:
    """
    Engagement signal: number of distinct web/app sessions in the past 30 days
    for authenticated (known) customers.

    Leakage assessment: SAFE — 30-day window ends at snapshot_date.

    Only authenticated sessions are included (customer_id is not null).
    Anonymous sessions (~35% of clickstream) cannot be attributed to a customer.

    Args:
        clickstream_df: Clickstream DataFrame with event_timestamp (ms UTC),
                        customer_id (nullable), and session_id.

    Returns:
        pd.Series indexed by customer_id, named 'clickstream_sessions_30d'.
        Customers with no authenticated sessions receive 0.
    """
    df = clickstream_df.dropna(subset=["customer_id"]).copy()
    df["event_timestamp"] = pd.to_datetime(
        df["event_timestamp"], unit="ms", utc=True, errors="coerce"
    )

    cutoff  = _SNAPSHOT_DT - pd.Timedelta(days=30)
    window  = df[
        (df["event_timestamp"] >= cutoff) & (df["event_timestamp"] < _SNAPSHOT_DT)
    ]

    sessions = (
        window.groupby("customer_id")["session_id"]
        .nunique()
        .rename("clickstream_sessions_30d")
    )

    logger.info(
        "clickstream_sessions_30d: mean=%.2f, max=%d",
        sessions.mean(),
        sessions.max(),
    )
    return sessions


# ---------------------------------------------------------------------------
# Additional Feature D: add_to_cart_rate_30d
# ---------------------------------------------------------------------------

def compute_add_to_cart_rate_30d(clickstream_df: pd.DataFrame) -> pd.Series:
    """
    Intent signal: ratio of add_to_cart events to product_view events in the
    past 30 days for authenticated customers.

    add_to_cart_rate = add_to_cart_events / product_view_events

    Leakage assessment: SAFE — 30-day window ends at snapshot_date.

    A declining add_to_cart_rate may signal reduced purchase intent and
    early churn signals even before transactions drop off.

    Edge cases:
      - Zero product_view events → NaN (customer did not browse products).
      - Customers with no clickstream records in the window → NaN.

    Args:
        clickstream_df: Clickstream DataFrame.

    Returns:
        pd.Series indexed by customer_id, named 'add_to_cart_rate_30d'.
    """
    df = clickstream_df.dropna(subset=["customer_id"]).copy()
    df["event_timestamp"] = pd.to_datetime(
        df["event_timestamp"], unit="ms", utc=True, errors="coerce"
    )

    cutoff = _SNAPSHOT_DT - pd.Timedelta(days=30)
    window = df[
        (df["event_timestamp"] >= cutoff) & (df["event_timestamp"] < _SNAPSHOT_DT)
    ]

    product_views = (
        window[window["event_type"] == "product_view"]
        .groupby("customer_id")["event_id"]
        .count()
        .rename("_pv_count")
    )
    add_to_carts = (
        window[window["event_type"] == "add_to_cart"]
        .groupby("customer_id")["event_id"]
        .count()
        .rename("_atc_count")
    )

    combined = pd.concat([product_views, add_to_carts], axis=1)
    rate     = (
        (combined["_atc_count"] / combined["_pv_count"])
        .rename("add_to_cart_rate_30d")
    )

    logger.info(
        "add_to_cart_rate_30d: mean=%.3f, n_null=%d",
        rate.mean(),
        rate.isna().sum(),
    )
    return rate


# ---------------------------------------------------------------------------
# Feature matrix assembly
# ---------------------------------------------------------------------------

def build_feature_matrix(
    customers_df: pd.DataFrame,
    transactions_df: pd.DataFrame,
    clickstream_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Join all individual feature series onto the customer_id index to produce
    the final feature matrix for model training.

    Also attaches churn_label from customers_df as the target variable.

    All join operations are left joins from the customer dimension: every
    customer appears in the output regardless of whether they have transactions
    or clickstream data.  Missing features receive NaN (or 0 for fill-value
    features like frequency counts).

    Args:
        customers_df   : Customers DataFrame.
        transactions_df: Transactions DataFrame.
        clickstream_df : Clickstream DataFrame.

    Returns:
        DataFrame with customer_id as index and all feature columns + churn_label.
        Shape: (n_customers, n_features + 2)   [+2 = churn_label + loyalty_tier]
    """
    logger.info("Building feature matrix for %d customers …", len(customers_df))

    # ---- Compute all features ------------------------------------------ #
    feat_recency       = compute_days_since_last_purchase(transactions_df, customers_df)
    feat_freq_90d      = compute_purchase_frequency_90d(transactions_df)
    feat_basket_6m     = compute_avg_basket_size_6m(transactions_df)
    feat_diversity     = compute_category_diversity_score(transactions_df)
    feat_online_ratio  = compute_online_to_store_ratio(transactions_df)
    feat_promo_rate    = compute_promo_response_rate(transactions_df)
    feat_tenure        = compute_loyalty_tier_duration_days(customers_df)
    feat_freq_180d     = compute_purchase_frequency_180d(transactions_df)
    feat_spend_90d     = compute_total_spend_90d(transactions_df)
    feat_sessions_30d  = compute_clickstream_sessions_30d(clickstream_df)
    feat_atc_rate      = compute_add_to_cart_rate_30d(clickstream_df)

    # ---- Assemble ------------------------------------------------------- #
    base = (
        customers_df[["customer_id", "loyalty_tier", "churn_label"]]
        .drop_duplicates(subset=["customer_id"])
        .set_index("customer_id")
    )

    feature_matrix = base.join(
        [
            feat_recency,
            feat_freq_90d.rename("purchase_frequency_90d"),
            feat_basket_6m,
            feat_diversity,
            feat_online_ratio,
            feat_promo_rate,
            feat_tenure,
            feat_freq_180d.rename("purchase_frequency_180d"),
            feat_spend_90d.rename("total_spend_90d"),
            feat_sessions_30d.rename("clickstream_sessions_30d"),
            feat_atc_rate,
        ],
        how="left",
    )

    # Fill frequency / count features to 0 for customers with no activity
    zero_fill_cols = [
        "purchase_frequency_90d",
        "purchase_frequency_180d",
        "total_spend_90d",
        "clickstream_sessions_30d",
    ]
    feature_matrix[zero_fill_cols] = feature_matrix[zero_fill_cols].fillna(0)

    logger.info(
        "Feature matrix shape: %s | Churn rate: %.2f%%",
        feature_matrix.shape,
        feature_matrix["churn_label"].mean() * 100,
    )
    return feature_matrix


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main(data_dir: str, output_dir: str) -> None:
    """
    Load NorthStar data files, compute all features, and write the feature
    matrix to a Parquet file.

    Input files expected:
      {data_dir}/customers.csv
      {data_dir}/transactions.parquet
      {data_dir}/clickstream.parquet

    Output:
      {output_dir}/features.parquet

    Args:
        data_dir  : Directory containing input data files.
        output_dir: Directory to write features.parquet.
    """
    data_path   = Path(data_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Load data
    logger.info("Loading customers from %s …", data_path / "customers.csv")
    customers_df = pd.read_csv(data_path / "customers.csv")
    customers_df["signup_date"] = pd.to_datetime(
        customers_df["signup_date"], utc=True, errors="coerce"
    )

    logger.info("Loading transactions from %s …", data_path / "transactions.parquet")
    transactions_df = pd.read_parquet(data_path / "transactions.parquet")
    transactions_df["transaction_date"] = pd.to_datetime(
        transactions_df["transaction_date"], utc=True, errors="coerce"
    )
    if "return_flag" not in transactions_df.columns:
        transactions_df["return_flag"] = False
    else:
        transactions_df["return_flag"] = transactions_df["return_flag"].astype(bool)

    logger.info("Loading clickstream from %s …", data_path / "clickstream.parquet")
    clickstream_df = pd.read_parquet(data_path / "clickstream.parquet")

    # Build feature matrix
    feature_matrix = build_feature_matrix(customers_df, transactions_df, clickstream_df)

    # Write output
    out_file = output_path / "features.parquet"
    feature_matrix.reset_index().to_parquet(out_file, index=False)
    logger.info("Feature matrix written to: %s  (shape: %s)", out_file, feature_matrix.shape)

    # Quick summary
    print("\n=== Feature Matrix Summary ===")
    print(f"Customers : {len(feature_matrix):,}")
    print(f"Features  : {feature_matrix.shape[1] - 1} (excl. churn_label)")
    print(f"Churn rate: {feature_matrix['churn_label'].mean():.2%}")
    print("\nNull rates per feature:")
    print(
        feature_matrix
        .drop(columns=["churn_label"])
        .isna()
        .mean()
        .sort_values(ascending=False)
        .apply(lambda x: f"{x:.2%}")
        .to_string()
    )


# ---------------------------------------------------------------------------
# Per-customer wrapper functions (used by test_features.py)
#
# The primary compute_* functions above operate over the full customer set
# (vectorized over the DataFrame index).  These wrappers accept a single
# customer_id and a snapshot date, making them easy to test in isolation.
# ---------------------------------------------------------------------------

def _cust_txns(customer_id: str, transactions_df: pd.DataFrame) -> pd.DataFrame:
    """Return all transactions for customer_id (with return_flag coerced to bool)."""
    df = transactions_df.copy()
    df["transaction_date"] = pd.to_datetime(df["transaction_date"], utc=True, errors="coerce")
    if "return_flag" not in df.columns:
        df["return_flag"] = False
    else:
        df["return_flag"] = df["return_flag"].astype(bool)
    return df[df["customer_id"] == customer_id].copy()


def _window(cust_df: pd.DataFrame, snapshot: pd.Timestamp, days: int,
            exclude_returns: bool = True) -> pd.DataFrame:
    """Filter cust_df to the trailing `days` window ending at snapshot."""
    snap_utc = snapshot.tz_localize("UTC") if snapshot.tzinfo is None else snapshot
    cutoff = snap_utc - pd.Timedelta(days=days)
    mask = (cust_df["transaction_date"] >= cutoff) & (cust_df["transaction_date"] <= snap_utc)
    if exclude_returns:
        mask &= ~cust_df["return_flag"]
    return cust_df[mask]


def compute_days_since_last_purchase(
    customer_id: str,
    transactions_df: pd.DataFrame,
    snapshot: pd.Timestamp,
) -> int:
    """
    Per-customer wrapper. Returns days since last purchase within the 90d window,
    or NO_PURCHASE_SENTINEL (999) if no qualifying transaction exists.
    """
    df = _cust_txns(customer_id, transactions_df)
    win = _window(df, snapshot, 90, exclude_returns=False)
    if win.empty:
        return NO_PURCHASE_SENTINEL
    latest = win["transaction_date"].max()
    snap_utc = snapshot.tz_localize("UTC") if snapshot.tzinfo is None else snapshot
    return int((snap_utc - latest).days)


def compute_purchase_frequency_90d(
    customer_id: str,
    transactions_df: pd.DataFrame,
    snapshot: pd.Timestamp,
) -> int:
    """Per-customer wrapper. Returns non-return purchase count in last 90 days."""
    df = _cust_txns(customer_id, transactions_df)
    return len(_window(df, snapshot, 90, exclude_returns=True))


def compute_purchase_frequency_180d(
    customer_id: str,
    transactions_df: pd.DataFrame,
    snapshot: pd.Timestamp,
) -> int:
    """Per-customer wrapper. Returns non-return purchase count in last 180 days."""
    df = _cust_txns(customer_id, transactions_df)
    return len(_window(df, snapshot, 180, exclude_returns=True))


def compute_avg_basket_size_6m(
    customer_id: str,
    transactions_df: pd.DataFrame,
    snapshot: pd.Timestamp,
) -> float:
    """Per-customer wrapper. Returns mean basket size over the past 180 days, excl. returns."""
    df = _cust_txns(customer_id, transactions_df)
    win = _window(df, snapshot, 180, exclude_returns=True)
    if win.empty:
        return 0.0
    col = "net_amount" if "net_amount" in win.columns else "transaction_amount"
    return float(win[col].mean())


def compute_total_spend_90d(
    customer_id: str,
    transactions_df: pd.DataFrame,
    snapshot: pd.Timestamp,
) -> float:
    """Per-customer wrapper. Returns total spend over the past 90 days, excl. returns."""
    df = _cust_txns(customer_id, transactions_df)
    win = _window(df, snapshot, 90, exclude_returns=True)
    if win.empty:
        return 0.0
    col = "net_amount" if "net_amount" in win.columns else "transaction_amount"
    return float(win[col].sum())


def compute_category_diversity_score(
    customer_id: str,
    transactions_df: pd.DataFrame,
    snapshot: pd.Timestamp,
) -> float:
    """
    Per-customer wrapper. Returns category diversity score in [0, 1].
    Normalized against the global category set in transactions_df.
    """
    df = _cust_txns(customer_id, transactions_df)
    win = _window(df, snapshot, 180, exclude_returns=True)
    if win.empty or "product_categories" not in win.columns:
        return 0.0

    cust_cats: set = set()
    for s in win["product_categories"].dropna():
        for c in str(s).split("|"):
            cust_cats.add(c.strip())

    global_cats: set = set()
    for s in transactions_df["product_categories"].dropna():
        for c in str(s).split("|"):
            global_cats.add(c.strip())

    max_cats = len(global_cats) if global_cats else 1
    return round(len(cust_cats) / max_cats, 4)


def compute_online_to_store_ratio(
    customer_id: str,
    transactions_df: pd.DataFrame,
    snapshot: pd.Timestamp,
) -> float:
    """Per-customer wrapper. Returns fraction of 90d purchases via online channel."""
    df = _cust_txns(customer_id, transactions_df)
    win = _window(df, snapshot, 90, exclude_returns=True)
    if win.empty or "channel" not in win.columns:
        return 0.0
    online = (win["channel"].str.lower() == "online").sum()
    return round(online / len(win), 4)


def compute_promo_response_rate(
    customer_id: str,
    transactions_df: pd.DataFrame,
    snapshot: pd.Timestamp,
) -> float:
    """Per-customer wrapper. Returns fraction of 90d purchases using a promo code."""
    df = _cust_txns(customer_id, transactions_df)
    win = _window(df, snapshot, 90, exclude_returns=True)
    if win.empty or "promotion_code" not in win.columns:
        return 0.0
    with_promo = win["promotion_code"].notna().sum()
    return round(with_promo / len(win), 4)


def build_feature_matrix(
    customers_df: pd.DataFrame,
    transactions_df: pd.DataFrame,
    snapshot: pd.Timestamp,
    clickstream_df: pd.DataFrame = None,
) -> pd.DataFrame:
    """
    Per-customer feature matrix builder (used by test_features.py).
    Delegates to the vectorized implementations above where possible,
    and applies the per-customer wrappers for the remaining features.

    Returns a DataFrame with one row per customer and all FEATURE_COLUMNS present.
    """
    customers_df = customers_df.copy()
    transactions_df = transactions_df.copy()
    transactions_df["transaction_date"] = pd.to_datetime(
        transactions_df["transaction_date"], utc=True, errors="coerce"
    )
    if "return_flag" not in transactions_df.columns:
        transactions_df["return_flag"] = False
    else:
        transactions_df["return_flag"] = transactions_df["return_flag"].astype(bool)

    rows = []
    for _, cust in customers_df.iterrows():
        cid = cust["customer_id"]
        row = {"customer_id": cid}

        row["days_since_last_purchase"]  = compute_days_since_last_purchase(cid, transactions_df, snapshot)
        row["purchase_frequency_90d"]    = compute_purchase_frequency_90d(cid, transactions_df, snapshot)
        row["purchase_frequency_180d"]   = compute_purchase_frequency_180d(cid, transactions_df, snapshot)
        row["avg_basket_size_6m"]        = compute_avg_basket_size_6m(cid, transactions_df, snapshot)
        row["total_spend_90d"]           = compute_total_spend_90d(cid, transactions_df, snapshot)
        row["category_diversity_score"]  = compute_category_diversity_score(cid, transactions_df, snapshot)
        row["online_to_store_ratio"]     = compute_online_to_store_ratio(cid, transactions_df, snapshot)
        row["promo_response_rate"]       = compute_promo_response_rate(cid, transactions_df, snapshot)

        # Customer-metadata features
        if "signup_date" in cust.index and pd.notna(cust.get("signup_date")):
            snap_naive = snapshot.tz_localize(None) if snapshot.tzinfo else snapshot
            su = pd.to_datetime(cust["signup_date"])
            su_naive = su.tz_localize(None) if hasattr(su, "tzinfo") and su.tzinfo else su
            row["customer_tenure_days"] = max(0, (snap_naive - su_naive).days)
        else:
            row["customer_tenure_days"] = 0

        row["loyalty_tier_duration_days"] = row["customer_tenure_days"]

        if clickstream_df is not None:
            cc = clickstream_df[clickstream_df["customer_id"] == cid]
            row["clickstream_sessions_30d"] = float(cc["sessions_30d"].iloc[0]) if not cc.empty else 0.0
            row["add_to_cart_rate_30d"]     = float(cc["add_to_cart_rate_30d"].iloc[0]) if not cc.empty else 0.0
        else:
            row["clickstream_sessions_30d"] = 0.0
            row["add_to_cart_rate_30d"]     = 0.0

        rows.append(row)

    result_df = pd.DataFrame(rows)
    col_order = ["customer_id"] + [c for c in [
        "days_since_last_purchase", "purchase_frequency_90d", "purchase_frequency_180d",
        "avg_basket_size_6m", "total_spend_90d", "category_diversity_score",
        "online_to_store_ratio", "promo_response_rate", "loyalty_tier_duration_days",
        "customer_tenure_days", "clickstream_sessions_30d", "add_to_cart_rate_30d",
    ] if c in result_df.columns]
    return result_df[col_order]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="NorthStar churn feature engineering"
    )
    parser.add_argument(
        "--data-dir",
        default="northstar-data",
        help="Directory containing input CSV/Parquet files.",
    )
    parser.add_argument(
        "--output-dir",
        default="northstar-processed",
        help="Directory to write features.parquet.",
    )
    args = parser.parse_args()
    main(data_dir=args.data_dir, output_dir=args.output_dir)
