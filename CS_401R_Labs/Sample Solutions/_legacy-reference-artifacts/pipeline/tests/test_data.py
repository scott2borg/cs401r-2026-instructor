"""
NorthStar Retail — Data Quality Tests
Validates raw data, processed data, referential integrity, and Feature Store snapshots.

Run: pytest tests/test_data.py -v
"""

import os
import re
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import date

# ---------------------------------------------------------------------------
# Path resolution helpers
# ---------------------------------------------------------------------------
RAW_DIR = Path(os.environ.get("NORTHSTAR_RAW_PATH", "./northstar-raw"))
PROCESSED_DIR = Path(os.environ.get("NORTHSTAR_PROCESSED_PATH", "./northstar-processed"))

# Threshold constants
SEASONAL_UPLIFT_FACTOR = 1.15          # Nov/Dec volume must be 15% above annual average
LOYALTY_TIER_MIN_TRANSACTIONS = 100    # Each loyalty tier must have >= 100 transactions
EMAIL_AT_SIGN_COUNT = 0                # Hashed emails must contain no '@' characters
STORE_ID_PATTERN = re.compile(r"^(STORE-\d{3}|ONLINE)$")  # Normalized store ID format

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def customers_df():
    """Load the customers raw CSV."""
    path = RAW_DIR / "customers.csv"
    if not path.exists():
        pytest.skip(f"Raw customers file not found at {path}")
    return pd.read_csv(path, parse_dates=["signup_date", "snapshot_date", "churn_date"],
                       infer_datetime_format=True)


@pytest.fixture(scope="module")
def transactions_df():
    """Load the transactions raw CSV."""
    path = RAW_DIR / "transactions.csv"
    if not path.exists():
        pytest.skip(f"Raw transactions file not found at {path}")
    return pd.read_csv(path, parse_dates=["transaction_date"], infer_datetime_format=True)


@pytest.fixture(scope="module")
def store_events_df():
    """Load raw store events CSV."""
    path = RAW_DIR / "store_events.csv"
    if not path.exists():
        pytest.skip(f"Raw store_events file not found at {path}")
    return pd.read_csv(path)


@pytest.fixture(scope="module")
def processed_store_events_df():
    """Load the PROCESSED store events parquet (post-Glue pipeline)."""
    path = PROCESSED_DIR / "store_events.parquet"
    if not path.exists():
        pytest.skip(f"Processed store_events not found at {path} — run Glue ETL first")
    return pd.read_parquet(path)


@pytest.fixture(scope="module")
def processed_transactions_df():
    """Load the PROCESSED transactions parquet (post-Glue pipeline)."""
    path = PROCESSED_DIR / "transactions.parquet"
    if not path.exists():
        pytest.skip(f"Processed transactions not found at {path} — run Glue ETL first")
    return pd.read_parquet(path)


# ---------------------------------------------------------------------------
# Customer tests
# ---------------------------------------------------------------------------

class TestCustomers:

    def test_customer_id_format(self, customers_df):
        """All customer_ids must match CUST-XXXXXXXX (8-digit zero-padded)."""
        pattern = re.compile(r"^CUST-\d{8}$")
        bad = customers_df[~customers_df["customer_id"].str.match(pattern)]
        assert len(bad) == 0, (
            f"{len(bad)} customer_ids fail format check. "
            f"Examples: {bad['customer_id'].head(5).tolist()}"
        )

    def test_no_duplicate_customers(self, customers_df):
        """customer_id must be unique across the customer table."""
        dup_count = customers_df["customer_id"].duplicated().sum()
        assert dup_count == 0, f"{dup_count} duplicate customer_ids found"

    def test_loyalty_tier_values(self, customers_df):
        """loyalty_tier must be one of the four defined tiers."""
        valid_tiers = {"Bronze", "Silver", "Gold", "Platinum"}
        bad = customers_df[~customers_df["loyalty_tier"].isin(valid_tiers)]
        assert len(bad) == 0, (
            f"{len(bad)} rows have invalid loyalty_tier. "
            f"Unknown values: {set(bad['loyalty_tier'].unique())}"
        )

    def test_churn_label_is_binary(self, customers_df):
        """churn_label must be 0 or 1 only."""
        valid = {0, 1}
        bad_vals = set(customers_df["churn_label"].unique()) - valid
        assert not bad_vals, f"Non-binary churn_label values found: {bad_vals}"

    def test_email_is_hashed(self, customers_df):
        """
        Email column must contain hashed values — no raw '@' sign allowed.
        Hashed emails (SHA-256 hex) are 64-character hex strings with no '@'.
        """
        if "email" not in customers_df.columns:
            pytest.skip("No 'email' column in customers_df")
        has_at = customers_df["email"].str.contains("@", na=False).sum()
        assert has_at == EMAIL_AT_SIGN_COUNT, (
            f"{has_at} customer emails still contain '@' — PII not hashed. "
            f"Run the email hashing step before committing to Feature Store."
        )

    def test_churn_date_is_before_snapshot(self, customers_df):
        """
        For churned customers (churn_label == 1), churn_date must be <= snapshot_date.
        A churn date in the future indicates a data pipeline error.
        """
        churned = customers_df[customers_df["churn_label"] == 1].copy()
        if "churn_date" not in churned.columns or "snapshot_date" not in churned.columns:
            pytest.skip("churn_date or snapshot_date column not present")

        churned = churned.dropna(subset=["churn_date", "snapshot_date"])
        future_churn = churned[churned["churn_date"] > churned["snapshot_date"]]
        assert len(future_churn) == 0, (
            f"{len(future_churn)} churned customers have churn_date after snapshot_date. "
            f"Sample customer_ids: {future_churn['customer_id'].head(5).tolist()}"
        )


# ---------------------------------------------------------------------------
# Transaction tests
# ---------------------------------------------------------------------------

class TestTransactions:

    def test_transaction_id_format(self, transactions_df):
        """All transaction_ids must match TXN-XXXXXXXXXXXX (12-digit zero-padded)."""
        pattern = re.compile(r"^TXN-\d{12}$")
        bad = transactions_df[~transactions_df["transaction_id"].str.match(pattern)]
        assert len(bad) == 0, (
            f"{len(bad)} transaction_ids fail format check. "
            f"Examples: {bad['transaction_id'].head(5).tolist()}"
        )

    def test_no_negative_transaction_amounts_except_returns(self, transactions_df):
        """
        Negative transaction_amount is only permitted when return_flag == True.
        Unexplained negative amounts indicate a pipeline or source data error.
        """
        if "return_flag" not in transactions_df.columns:
            pytest.skip("return_flag column not present")
        bad = transactions_df[
            (transactions_df["transaction_amount"] < 0) &
            (~transactions_df["return_flag"].fillna(False))
        ]
        assert len(bad) == 0, (
            f"{len(bad)} transactions have negative amounts without return_flag=True. "
            f"Sample IDs: {bad['transaction_id'].head(5).tolist()}"
        )

    def test_transaction_date_not_in_future(self, transactions_df):
        """No transaction date should be in the future relative to today."""
        today = pd.Timestamp(date.today())
        future = transactions_df[transactions_df["transaction_date"] > today]
        assert len(future) == 0, (
            f"{len(future)} transactions have future dates. "
            f"Latest: {transactions_df['transaction_date'].max()}"
        )

    def test_seasonal_volume_pattern(self, transactions_df):
        """
        November and December should each have at least 15% more transactions
        than the monthly average across the full year.
        This validates that seasonal demand is captured correctly in the data.
        """
        df = transactions_df.copy()
        df["month"] = pd.to_datetime(df["transaction_date"]).dt.month

        monthly_counts = df.groupby("month").size()

        # Require at least 12 months of data for a meaningful seasonality check
        if len(monthly_counts) < 12:
            pytest.skip(
                f"Only {len(monthly_counts)} months of data; need 12 for seasonality check"
            )

        annual_avg = monthly_counts.mean()

        for holiday_month in [11, 12]:
            if holiday_month not in monthly_counts.index:
                pytest.skip(f"Month {holiday_month} not present in transaction data")
            month_vol = monthly_counts[holiday_month]
            threshold = annual_avg * SEASONAL_UPLIFT_FACTOR
            assert month_vol >= threshold, (
                f"Month {holiday_month} volume ({month_vol:.0f}) is not >= "
                f"{SEASONAL_UPLIFT_FACTOR:.0%} of annual average ({annual_avg:.0f}). "
                f"Expected >= {threshold:.0f}. Seasonal demand pattern not detected."
            )

    def test_store_id_format_after_normalization(self, processed_transactions_df):
        """
        After the Glue normalization pipeline, all store_ids must match
        STORE-NNN or ONLINE format. Legacy formats like S001 must be transformed.
        """
        if "store_id" not in processed_transactions_df.columns:
            pytest.skip("store_id column not in processed transactions")

        bad = processed_transactions_df[
            ~processed_transactions_df["store_id"].str.match(STORE_ID_PATTERN)
        ]
        assert len(bad) == 0, (
            f"{len(bad)} rows have non-normalized store_id after Glue pipeline. "
            f"Sample bad values: {bad['store_id'].unique()[:10].tolist()}. "
            f"Check the store_id normalization step in batch_ingestion.py."
        )


# ---------------------------------------------------------------------------
# Store events tests
# ---------------------------------------------------------------------------

class TestStoreEvents:

    def test_event_type_values(self, store_events_df):
        """event_type must be one of the defined promotion event types."""
        valid_event_types = {
            "SALE", "GRAND_OPENING", "LOYALTY_EVENT",
            "SEASONAL_PROMO", "CLEARANCE", "FLASH_SALE",
        }
        if "event_type" not in store_events_df.columns:
            pytest.skip("event_type column not present")
        bad = store_events_df[~store_events_df["event_type"].isin(valid_event_types)]
        assert len(bad) == 0, (
            f"{len(bad)} rows have invalid event_type. "
            f"Unknown values: {set(bad['event_type'].unique())}"
        )

    def test_date_format_consistency(self, processed_store_events_df):
        """
        In PROCESSED store events, all date columns must parse to a consistent
        ISO 8601 format. Mixed formats (MM/DD/YYYY vs YYYY-MM-DD) must be
        resolved by the Glue ETL pipeline before data reaches Feature Store.
        """
        date_cols = [c for c in processed_store_events_df.columns
                     if "date" in c.lower() or "time" in c.lower()]

        if not date_cols:
            pytest.skip("No date columns found in processed store events")

        # Regex for ISO 8601 date string (YYYY-MM-DD or YYYY-MM-DDThh:mm:ss...)
        iso_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}.*)?$")

        mixed_format_count = 0
        offending_cols = []

        for col in date_cols:
            str_col = processed_store_events_df[col].dropna().astype(str)
            bad_in_col = (~str_col.str.match(iso_pattern)).sum()
            if bad_in_col > 0:
                mixed_format_count += bad_in_col
                offending_cols.append(f"{col} ({bad_in_col} bad)")

        assert mixed_format_count == 0, (
            f"Non-ISO date formats found in processed store_events in columns: "
            f"{offending_cols}. Run the date normalization step in the Glue job."
        )


# ---------------------------------------------------------------------------
# Referential integrity tests
# ---------------------------------------------------------------------------

class TestReferentialIntegrity:

    def test_all_transactions_have_valid_customer(self, customers_df, transactions_df):
        """Every transaction must reference an existing customer_id."""
        valid_ids = set(customers_df["customer_id"])
        orphaned = transactions_df[~transactions_df["customer_id"].isin(valid_ids)]
        assert len(orphaned) == 0, (
            f"{len(orphaned)} transactions reference non-existent customer_ids. "
            f"Sample orphaned IDs: {orphaned['customer_id'].head(5).tolist()}"
        )

    def test_all_loyalty_tiers_have_transactions(self, customers_df, transactions_df):
        """
        All four loyalty tiers (Bronze, Silver, Gold, Platinum) must each have
        at least 100 associated transactions. Missing tiers indicate a join or
        data segmentation problem.
        """
        merged = customers_df[["customer_id", "loyalty_tier"]].merge(
            transactions_df[["transaction_id", "customer_id"]],
            on="customer_id",
            how="inner",
        )
        tier_counts = merged.groupby("loyalty_tier")["transaction_id"].count()
        required_tiers = {"Bronze", "Silver", "Gold", "Platinum"}

        for tier in required_tiers:
            count = tier_counts.get(tier, 0)
            assert count >= LOYALTY_TIER_MIN_TRANSACTIONS, (
                f"Loyalty tier '{tier}' has only {count} transactions "
                f"(minimum: {LOYALTY_TIER_MIN_TRANSACTIONS}). "
                f"Check data segmentation in the customer enrichment pipeline."
            )

    def test_churn_rate_within_expected_range(self, customers_df):
        """
        Churn rate must be between 8% and 35%.
        Outside this range likely indicates a labeling or sampling error.
        """
        churn_rate = customers_df["churn_label"].mean()
        assert 0.08 <= churn_rate <= 0.35, (
            f"Churn rate {churn_rate:.1%} is outside expected range [8%, 35%]. "
            f"Check label generation in the customer snapshot pipeline."
        )


# ---------------------------------------------------------------------------
# Feature Store tests
# ---------------------------------------------------------------------------

class TestFeatureStore:

    @pytest.fixture
    def feature_snapshot_df(self):
        """Load the features.parquet written by compute_features.py."""
        path = Path(os.environ.get("NORTHSTAR_FEATURES_PATH",
                                   "./northstar-processed/features.parquet"))
        if not path.exists():
            pytest.skip("features.parquet not found — run compute_features.py first")
        return pd.read_parquet(path)

    def test_days_since_last_purchase_null_rate(self, feature_snapshot_df):
        """days_since_last_purchase null rate must be < 2%."""
        null_rate = feature_snapshot_df["days_since_last_purchase"].isna().mean()
        assert null_rate < 0.02, (
            f"days_since_last_purchase null rate {null_rate:.1%} > 2%. "
            f"Check imputation logic in compute_features.py."
        )

    def test_purchase_frequency_90d_non_negative(self, feature_snapshot_df):
        """purchase_frequency_90d must be >= 0 for all customers."""
        negative = (feature_snapshot_df["purchase_frequency_90d"] < 0).sum()
        assert negative == 0, (
            f"{negative} customers have negative purchase_frequency_90d. "
            f"Return transactions may be incorrectly counted against frequency."
        )

    def test_feature_computation_freshness(self, feature_snapshot_df):
        """Feature computation must have happened within the last 48 hours."""
        if "feature_computation_timestamp" not in feature_snapshot_df.columns:
            pytest.skip("feature_computation_timestamp not in features")
        latest = pd.to_datetime(feature_snapshot_df["feature_computation_timestamp"]).max()
        age_hours = (
            pd.Timestamp.utcnow().tz_localize(None) - latest.tz_localize(None)
        ).total_seconds() / 3600
        assert age_hours < 48, (
            f"Features are {age_hours:.1f} hours old (max: 48). "
            f"Trigger a feature recompute via the nightly pipeline."
        )

    def test_all_required_features_present(self, feature_snapshot_df):
        """All feature columns required by the churn model must be present."""
        REQUIRED = [
            "days_since_last_purchase",
            "purchase_frequency_90d",
            "avg_basket_size_6m",
            "category_diversity_score",
            "online_to_store_ratio",
            "promo_response_rate",
        ]
        missing = [c for c in REQUIRED if c not in feature_snapshot_df.columns]
        assert not missing, (
            f"Missing required feature columns: {missing}. "
            f"These are expected by the XGBoost churn model input schema."
        )

    def test_category_diversity_score_bounded(self, feature_snapshot_df):
        """category_diversity_score must be between 0.0 and 1.0 inclusive."""
        if "category_diversity_score" not in feature_snapshot_df.columns:
            pytest.skip("category_diversity_score not in features")
        col = feature_snapshot_df["category_diversity_score"].dropna()
        below = (col < 0.0).sum()
        above = (col > 1.0).sum()
        assert below == 0 and above == 0, (
            f"category_diversity_score out of [0, 1]: "
            f"{below} below 0, {above} above 1."
        )
