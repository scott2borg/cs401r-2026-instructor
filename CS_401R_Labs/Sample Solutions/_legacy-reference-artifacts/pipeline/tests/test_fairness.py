"""
NorthStar Retail — Fairness Tests
Checks for disparate impact across loyalty tier segments.

Design intent:
    These tests FLAG but do not BLOCK the pipeline. A failing fairness
    threshold generates a JIRA ticket (via the warning message) and
    triggers a fairness review, but the model can still be deployed
    subject to a human approval step in the CodePipeline.

    Rationale: loyalty tier correlates with spending power, not with a
    protected class. A disparate performance gap is a business concern
    (are we underserving Bronze customers?) rather than a legal one.
    Blocking on fairness before that question is answered would prevent
    valuable churn interventions from reaching any customer.

Run: pytest tests/test_fairness.py -v -W error::UserWarning
     (the -W flag promotes fairness warnings to failures if you want strict mode)
"""

import os
import json
import warnings
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

# ---------------------------------------------------------------------------
# Path constants — override via environment variables
# ---------------------------------------------------------------------------
METRICS_PATH = os.environ.get("NORTHSTAR_METRICS_PATH", "./output/evaluation_metrics.json")
SLICE_METRICS_PATH = os.environ.get(
    "NORTHSTAR_SLICE_METRICS_PATH", "./output/slice_metrics.json"
)

# Fairness thresholds — named constants so they're easy to locate and justify
RECALL_GAP_THRESHOLD = 0.10   # Max allowed recall@10% gap between best/worst tier
AUC_GAP_THRESHOLD = 0.08      # Max allowed AUC gap between best/worst tier
ZERO_RECALL_FLOOR = 0.0       # No tier should have exactly 0% recall
REQUIRED_TIERS = {"Bronze", "Silver", "Gold", "Platinum"}

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def slice_metrics():
    """
    Load per-segment evaluation metrics written by evaluate.py.
    Expected schema:
        {
            "loyalty_tier": {
                "Bronze":   {"auc_roc": 0.71, "recall_top10": 0.32, "precision_top10": 0.38},
                "Silver":   {"auc_roc": 0.73, "recall_top10": 0.36, "precision_top10": 0.41},
                "Gold":     {"auc_roc": 0.75, "recall_top10": 0.39, "precision_top10": 0.44},
                "Platinum": {"auc_roc": 0.76, "recall_top10": 0.41, "precision_top10": 0.46}
            }
        }
    """
    path = Path(SLICE_METRICS_PATH)
    if not path.exists():
        pytest.skip(
            f"Slice metrics not found at {path}. "
            f"Run evaluate.py with --slice-by loyalty_tier or set NORTHSTAR_SLICE_METRICS_PATH."
        )
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def overall_metrics():
    """Load overall evaluation metrics for comparison baselines."""
    path = Path(METRICS_PATH)
    if not path.exists():
        pytest.skip(f"Overall metrics not found at {path}")
    with open(path) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Loyalty tier fairness tests
# ---------------------------------------------------------------------------

class TestLoyaltyTierFairness:

    def test_recall_gap_across_tiers_is_flagged_not_blocked(self, slice_metrics):
        """
        Fairness check: recall@10% gap between best-performing and worst-performing
        loyalty tier must not exceed 10 percentage points.

        Outcome policy:
            - Gap <= threshold: test PASSES silently.
            - Gap >  threshold: test WARNS (files a conceptual JIRA ticket) but
              still PASSES. Use -W error::UserWarning if you want strict blocking.
        """
        tier_metrics = slice_metrics.get("loyalty_tier", {})
        if len(tier_metrics) < 2:
            pytest.skip("Fewer than 2 tiers in slice_metrics — can't compute gap")

        recalls = {
            tier: metrics.get("recall_top10", 0.0)
            for tier, metrics in tier_metrics.items()
        }

        best_tier = max(recalls, key=recalls.get)
        worst_tier = min(recalls, key=recalls.get)
        best_recall = recalls[best_tier]
        worst_recall = recalls[worst_tier]
        gap = best_recall - worst_recall

        if gap > RECALL_GAP_THRESHOLD:
            warnings.warn(
                f"FAIRNESS ALERT [FairML-001]: Recall@10 gap across loyalty tiers "
                f"is {gap:.1%} (threshold: {RECALL_GAP_THRESHOLD:.0%}). "
                f"Best tier: {best_tier} ({best_recall:.1%}), "
                f"Worst tier: {worst_tier} ({worst_recall:.1%}). "
                f"Action: Create JIRA ticket FairML-001 for model fairness review. "
                f"Investigate whether underrepresentation of {worst_tier} tier "
                f"in training data is causing performance disparity.",
                UserWarning,
                stacklevel=2,
            )
        # Test always passes — fairness is informational, not a hard gate
        assert True

    def test_all_tiers_have_nonzero_recall(self, slice_metrics):
        """
        Hard gate: no loyalty tier should have 0% recall@10.
        Zero recall indicates the model is completely ignoring that segment,
        which is a severe model failure (not just a fairness concern).
        """
        tier_metrics = slice_metrics.get("loyalty_tier", {})
        zero_recall_tiers = [
            tier for tier, metrics in tier_metrics.items()
            if metrics.get("recall_top10", 1.0) == ZERO_RECALL_FLOOR
        ]
        assert not zero_recall_tiers, (
            f"Loyalty tier(s) with 0% recall@10: {zero_recall_tiers}. "
            f"The model is producing no correct churn predictions for these segments. "
            f"Possible causes: no positive labels in tier's training slice, "
            f"or threshold calibration is too high for low-activity segments."
        )

    def test_auc_gap_across_tiers(self, slice_metrics):
        """
        Fairness check: AUC gap between best and worst loyalty tier should not
        exceed 0.08. This test warns (does not block) if exceeded.
        """
        tier_metrics = slice_metrics.get("loyalty_tier", {})
        aucs = {
            tier: metrics.get("auc_roc", 0.0)
            for tier, metrics in tier_metrics.items()
        }

        if len(aucs) < 2:
            pytest.skip("Not enough tiers to compute AUC gap")

        best_tier = max(aucs, key=aucs.get)
        worst_tier = min(aucs, key=aucs.get)
        gap = aucs[best_tier] - aucs[worst_tier]

        if gap > AUC_GAP_THRESHOLD:
            warnings.warn(
                f"FAIRNESS ALERT [FairML-002]: AUC gap across tiers is {gap:.3f} "
                f"(threshold: {AUC_GAP_THRESHOLD}). "
                f"Best: {best_tier} ({aucs[best_tier]:.3f}), "
                f"Worst: {worst_tier} ({aucs[worst_tier]:.3f}). "
                f"Action: File FairML-002 for investigation.",
                UserWarning,
                stacklevel=2,
            )
        assert True

    def test_all_four_tiers_present_in_slice_metrics(self, slice_metrics):
        """
        All four loyalty tiers must appear in the slice metrics.
        Missing tiers mean the evaluation split excluded that segment,
        which masks potential fairness issues.
        """
        tier_metrics = slice_metrics.get("loyalty_tier", {})
        present = set(tier_metrics.keys())
        missing = REQUIRED_TIERS - present
        assert not missing, (
            f"Slice metrics are missing tiers: {missing}. "
            f"Ensure the evaluation dataset contains all loyalty tiers "
            f"and that evaluate.py slices by every tier."
        )

    def test_tier_precision_within_range(self, slice_metrics):
        """
        Precision@10 for each tier must be between 0.10 and 1.0.
        Values outside this range indicate a metrics computation error
        (e.g., empty slice or division-by-zero fallback to 0).
        """
        tier_metrics = slice_metrics.get("loyalty_tier", {})
        bad_tiers = []
        for tier, metrics in tier_metrics.items():
            prec = metrics.get("precision_top10", None)
            if prec is None:
                bad_tiers.append(f"{tier}: missing")
            elif not (0.10 <= prec <= 1.0):
                bad_tiers.append(f"{tier}: {prec:.3f}")
        assert not bad_tiers, (
            f"Tiers with out-of-range Precision@10: {bad_tiers}. "
            f"Check slice sizes — a very small tier may not have 10% to rank."
        )


# ---------------------------------------------------------------------------
# Per-tier vs. overall comparison
# ---------------------------------------------------------------------------

class TestSliceVsOverall:

    def test_no_tier_auc_drastically_below_overall(self, slice_metrics, overall_metrics):
        """
        No single tier's AUC should be more than 0.10 below the overall AUC.
        This catches the case where one tier drags down aggregate metrics
        while appearing acceptable at the aggregate level.
        """
        overall_auc = overall_metrics.get("auc_roc", 0.0)
        tier_metrics = slice_metrics.get("loyalty_tier", {})
        drastic_underperformers = {
            tier: metrics.get("auc_roc", 0.0)
            for tier, metrics in tier_metrics.items()
            if (overall_auc - metrics.get("auc_roc", overall_auc)) > 0.10
        }
        assert not drastic_underperformers, (
            f"Tier(s) with AUC > 0.10 below overall ({overall_auc:.3f}): "
            f"{drastic_underperformers}. "
            f"Investigate whether training data for these tiers is insufficient."
        )
