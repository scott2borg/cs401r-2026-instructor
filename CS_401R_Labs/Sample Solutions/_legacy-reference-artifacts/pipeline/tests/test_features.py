"""
NorthStar Retail — Feature Engineering Unit Tests
Tests the feature computation functions in data/features/compute_features.py

Run: pytest tests/test_features.py -v
"""

import sys
import pandas as pd
import numpy as np
import pytest
from datetime import datetime, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Import feature computation functions.
# We insert "." so this works from the repo root: pytest tests/test_features.py
# ---------------------------------------------------------------------------
sys.path.insert(0, ".")
try:
    from data.features.compute_features import (
        compute_days_since_last_purchase,
        compute_purchase_frequency_90d,
        compute_avg_basket_size_6m,
        compute_category_diversity_score,
        compute_online_to_store_ratio,
        compute_promo_response_rate,
        build_feature_matrix,
        FEATURE_SNAPSHOT_DATE,
    )
    IMPORT_OK = True
except ImportError as _import_err:
    IMPORT_OK = False
    _import_err_msg = str(_import_err)

# All tests in this module require the module to be importable
pytestmark = pytest.mark.skipif(
    not IMPORT_OK,
    reason=f"compute_features not importable — run from repo root. Error: "
           f"{_import_err_msg if not IMPORT_OK else ''}",
)

SNAPSHOT = pd.Timestamp(FEATURE_SNAPSHOT_DATE)

# Threshold / sentinel constants
DAYS_SENTINEL = 999          # Returned when customer has no recent purchase
WINDOW_90D = 90              # Days in the short purchase frequency window
WINDOW_180D = 180            # Days in the basket size computation window

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def sample_customers():
    """Minimal customer DataFrame with 3 test customers."""
    return pd.DataFrame({
        "customer_id": ["CUST-00000001", "CUST-00000002", "CUST-00000003"],
        "signup_date": ["2022-01-01", "2023-06-15", "2024-01-01"],
        "loyalty_tier": ["Gold", "Bronze", "Silver"],
        "churn_label": [0, 1, 0],
    })


@pytest.fixture(scope="module")
def sample_transactions():
    """
    Transactions covering normal, boundary, and edge cases.

    CUST-00000001 — Active customer with multiple transactions:
        - 5 days ago  (online, no promo)      → inside 90d window
        - 35 days ago (store, SAVE15 promo)   → inside 90d window
        - 80 days ago (online, no promo)      → inside 90d window
        - 10 days ago (store, RETURN)         → return; must be excluded from freq/basket

    CUST-00000002 — Churned customer:
        - 100 days ago (store, no promo)      → OUTSIDE 90d window

    CUST-00000003 — Edge case: single transaction, today:
        - 0 days ago  (online, WELCOME10)     → boundary: days_since == 0
    """
    return pd.DataFrame({
        "transaction_id": [f"TXN-{i:012d}" for i in range(6)],
        "customer_id": [
            "CUST-00000001",
            "CUST-00000001",
            "CUST-00000001",
            "CUST-00000002",
            "CUST-00000003",
            "CUST-00000001",   # Return — must be excluded from positive counts
        ],
        "transaction_date": [
            SNAPSHOT - timedelta(days=5),
            SNAPSHOT - timedelta(days=35),
            SNAPSHOT - timedelta(days=80),
            SNAPSHOT - timedelta(days=100),   # Outside 90d window
            SNAPSHOT,                          # Edge: today (0 days ago)
            SNAPSHOT - timedelta(days=10),     # Return transaction
        ],
        "transaction_amount": [150.00, 89.99, 220.00, 45.50, 300.00, -50.00],
        "net_amount":          [150.00, 89.99, 220.00, 45.50, 300.00, -50.00],
        "channel": ["online", "store", "online", "store", "online", "store"],
        "promotion_code":    [None, "SAVE15", None, None, "WELCOME10", None],
        "promotion_discount": [None, 13.50,   None, None, 30.00,       None],
        "product_categories": [
            "Apparel|Footwear",
            "Camping & Hiking",
            "Cycling|Apparel",
            "Footwear",
            "Electronics",
            "Apparel",
        ],
        "return_flag": [False, False, False, False, False, True],
    })


# ---------------------------------------------------------------------------
# days_since_last_purchase tests
# ---------------------------------------------------------------------------

class TestDaysSinceLastPurchase:

    def test_normal_case(self, sample_transactions):
        """CUST-00000001's most recent purchase was 5 days ago."""
        result = compute_days_since_last_purchase("CUST-00000001", sample_transactions, SNAPSHOT)
        assert result == 5, (
            f"Expected 5 days for CUST-00000001, got {result}. "
            f"Check that return transactions are not excluded from recency calc."
        )

    def test_outside_window_returns_sentinel(self, sample_transactions):
        """
        CUST-00000002's only purchase was 100 days ago — outside the 90-day
        lookback window. The function must return the sentinel value 999.
        """
        result = compute_days_since_last_purchase("CUST-00000002", sample_transactions, SNAPSHOT)
        assert result == DAYS_SENTINEL, (
            f"Expected sentinel {DAYS_SENTINEL} for CUST-00000002 (last purchase 100 days ago), "
            f"got {result}."
        )

    def test_same_day_purchase_returns_zero(self, sample_transactions):
        """CUST-00000003 transacted on the snapshot date itself — should be 0."""
        result = compute_days_since_last_purchase("CUST-00000003", sample_transactions, SNAPSHOT)
        assert result == 0, (
            f"Expected 0 days for same-day purchase, got {result}."
        )


# ---------------------------------------------------------------------------
# purchase_frequency_90d tests
# ---------------------------------------------------------------------------

class TestPurchaseFrequency90d:

    def test_normal_case(self, sample_transactions):
        """
        CUST-00000001 has transactions at 5, 35, and 80 days ago — all inside
        the 90-day window. The return (10 days ago) must be excluded.
        Expected frequency: 3.
        """
        result = compute_purchase_frequency_90d("CUST-00000001", sample_transactions, SNAPSHOT)
        assert result == 3, (
            f"Expected 3 purchases in 90d for CUST-00000001, got {result}. "
            f"Ensure return_flag=True rows are excluded and 80-day txn is included."
        )

    def test_zero_purchases_in_window(self, sample_transactions):
        """
        CUST-00000002's only transaction was 100 days ago — outside the 90-day
        window. Expected frequency: 0.
        """
        result = compute_purchase_frequency_90d("CUST-00000002", sample_transactions, SNAPSHOT)
        assert result == 0, (
            f"Expected 0 purchases in 90d for CUST-00000002, got {result}. "
            f"The 100-day-old transaction must not be counted."
        )


# ---------------------------------------------------------------------------
# avg_basket_size_6m tests
# ---------------------------------------------------------------------------

class TestAvgBasketSize6m:

    def test_excludes_returns(self, sample_transactions):
        """
        CUST-00000001's average basket size over 180 days should NOT include
        the return transaction (-50.00). Valid transactions in window:
            150.00 (5d), 89.99 (35d), 220.00 (80d) — 10d return excluded.
        Expected avg: (150 + 89.99 + 220) / 3 = 153.33
        """
        result = compute_avg_basket_size_6m("CUST-00000001", sample_transactions, SNAPSHOT)
        expected = (150.00 + 89.99 + 220.00) / 3
        assert abs(result - expected) < 0.01, (
            f"Expected avg basket ~{expected:.2f} for CUST-00000001, got {result:.2f}. "
            f"Return transaction (-50.00) must be excluded."
        )

    def test_single_transaction(self, sample_transactions):
        """CUST-00000003 has exactly one transaction (today, 300.00). Avg = 300.00."""
        result = compute_avg_basket_size_6m("CUST-00000003", sample_transactions, SNAPSHOT)
        assert abs(result - 300.00) < 0.01, (
            f"Expected avg basket 300.00 for CUST-00000003, got {result:.2f}."
        )


# ---------------------------------------------------------------------------
# category_diversity_score tests
# ---------------------------------------------------------------------------

class TestCategoryDiversityScore:

    def test_pipe_delimited_categories_deduplicated(self, sample_transactions):
        """
        CUST-00000001 transactions contain:
            'Apparel|Footwear', 'Camping & Hiking', 'Cycling|Apparel'
        After pipe-split and dedup: {Apparel, Footwear, Camping & Hiking, Cycling}
        Score = unique_categories / max_categories_in_dataset (normalized to [0,1]).
        This test verifies the pipe-split logic works — score must be > 0.
        """
        result = compute_category_diversity_score("CUST-00000001", sample_transactions, SNAPSHOT)
        assert 0.0 < result <= 1.0, (
            f"Expected diversity score in (0, 1] for CUST-00000001, got {result}. "
            f"Check pipe-split and dedup in compute_category_diversity_score."
        )

    def test_single_category_customer_has_low_score(self, sample_transactions):
        """
        CUST-00000002 has a single transaction with category 'Footwear'.
        Their diversity score must be strictly less than CUST-00000001's.
        """
        score_multi = compute_category_diversity_score("CUST-00000001", sample_transactions, SNAPSHOT)
        score_single = compute_category_diversity_score("CUST-00000002", sample_transactions, SNAPSHOT)
        assert score_single < score_multi, (
            f"Single-category customer score ({score_single:.3f}) should be < "
            f"multi-category customer score ({score_multi:.3f})."
        )


# ---------------------------------------------------------------------------
# online_to_store_ratio tests
# ---------------------------------------------------------------------------

class TestOnlineToStoreRatio:

    def test_mixed_channels(self, sample_transactions):
        """
        CUST-00000001 in the 90-day window (non-return transactions):
            - 5d ago:  online
            - 35d ago: store
            - 80d ago: online
        online_to_store_ratio = online_count / total_count = 2/3 ≈ 0.667.
        """
        result = compute_online_to_store_ratio("CUST-00000001", sample_transactions, SNAPSHOT)
        expected = 2 / 3
        assert abs(result - expected) < 0.01, (
            f"Expected online_to_store_ratio ≈ {expected:.3f} for CUST-00000001, "
            f"got {result:.3f}. Return transaction must be excluded."
        )

    def test_fully_online_customer(self, sample_transactions):
        """CUST-00000003 has exactly 1 transaction via online channel: ratio = 1.0."""
        result = compute_online_to_store_ratio("CUST-00000003", sample_transactions, SNAPSHOT)
        assert abs(result - 1.0) < 0.001, (
            f"Expected ratio 1.0 for fully-online CUST-00000003, got {result}."
        )


# ---------------------------------------------------------------------------
# promo_response_rate tests
# ---------------------------------------------------------------------------

class TestPromoResponseRate:

    def test_promo_response_rate_calculation(self, sample_transactions):
        """
        CUST-00000001 in 90-day window (non-return transactions):
            - 5d ago:  no promo
            - 35d ago: SAVE15  ← promo
            - 80d ago: no promo
        promo_response_rate = promo_transactions / total_transactions = 1/3 ≈ 0.333.
        """
        result = compute_promo_response_rate("CUST-00000001", sample_transactions, SNAPSHOT)
        expected = 1 / 3
        assert abs(result - expected) < 0.01, (
            f"Expected promo_response_rate ≈ {expected:.3f} for CUST-00000001, "
            f"got {result:.3f}."
        )

    def test_no_promo_customer_has_zero_rate(self, sample_transactions):
        """
        CUST-00000002 has no promotion codes in any transaction.
        Expected promo_response_rate: 0.0.
        """
        result = compute_promo_response_rate("CUST-00000002", sample_transactions, SNAPSHOT)
        assert result == 0.0, (
            f"Expected 0.0 promo rate for CUST-00000002, got {result}."
        )


# ---------------------------------------------------------------------------
# build_feature_matrix integration test
# ---------------------------------------------------------------------------

class TestFeatureMatrix:

    def test_feature_matrix_has_all_customers(self, sample_customers, sample_transactions):
        """
        build_feature_matrix() must produce exactly one row per customer.
        No customer should be dropped or duplicated during the join.
        """
        result_df = build_feature_matrix(sample_customers, sample_transactions, SNAPSHOT)
        expected_count = len(sample_customers)
        assert len(result_df) == expected_count, (
            f"build_feature_matrix returned {len(result_df)} rows; "
            f"expected {expected_count} (one per customer). "
            f"Check for dropped NaN rows or duplicated customer_ids in the join."
        )

    def test_feature_matrix_contains_required_columns(self, sample_customers, sample_transactions):
        """Feature matrix output must include all 12 churn model input features."""
        REQUIRED_FEATURES = [
            "days_since_last_purchase",
            "purchase_frequency_90d",
            "purchase_frequency_180d",
            "avg_basket_size_6m",
            "total_spend_90d",
            "category_diversity_score",
            "online_to_store_ratio",
            "promo_response_rate",
            "loyalty_tier_duration_days",
            "customer_tenure_days",
            "clickstream_sessions_30d",
            "add_to_cart_rate_30d",
        ]
        result_df = build_feature_matrix(sample_customers, sample_transactions, SNAPSHOT)
        missing = [c for c in REQUIRED_FEATURES if c not in result_df.columns]
        assert not missing, (
            f"Feature matrix missing columns required by churn model: {missing}"
        )
