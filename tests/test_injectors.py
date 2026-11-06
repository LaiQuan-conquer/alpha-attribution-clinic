"""
Tests for anti-pattern injectors.
反模式注入器测试。

Core assertion: dirty experiments should produce different (better) results than clean.
核心断言：脏实验应产生与干净实验不同（更好）的结果。
"""

import pytest
import pandas as pd
import numpy as np

from alpha_attribution_clinic.fixtures import (
    generate_aligned_bars,
    generate_universe_with_delistings,
)
from alpha_attribution_clinic.injectors import (
    LookaheadInjector,
    LeakageInjector,
    SurvivorshipInjector,
    CostBlindInjector,
)
from alpha_attribution_clinic.injectors.lookahead import compute_clean_momentum
from alpha_attribution_clinic.injectors.cost_blind import compute_returns_with_costs


class TestLookaheadInjector:
    """Tests for LookaheadInjector."""

    @pytest.fixture
    def sample_data(self):
        return generate_aligned_bars(n_assets=5, n_days=100, seed=42)

    def test_injection_adds_column(self, sample_data):
        """Test injection adds signal column."""
        injector = LookaheadInjector(lookahead_days=1)
        result = injector.inject(sample_data)

        assert "signal_lookahead" in result.columns

    def test_injection_metadata(self, sample_data):
        """Test injection metadata is correct."""
        injector = LookaheadInjector(lookahead_days=3)
        injector.inject(sample_data)

        meta = injector.get_injection_metadata()
        assert meta["injector"] == "lookahead"
        assert meta["lookahead_days"] == 3

    def test_dirty_vs_clean_diverge(self, sample_data):
        """
        CORE TEST: Dirty signal should have much higher correlation
        with future returns than clean signal.
        """
        injector = LookaheadInjector(lookahead_days=1)
        dirty_data = injector.inject(sample_data)
        clean_data = compute_clean_momentum(sample_data, lookback=5)

        dirty_data = dirty_data.reset_index()
        clean_data = clean_data.reset_index()

        dirty_data = dirty_data.sort_values(["asset_id", "date"])
        clean_data = clean_data.sort_values(["asset_id", "date"])

        dirty_data["future_ret"] = (
            dirty_data.groupby("asset_id")["close"].pct_change().shift(-1)
        )
        clean_data["future_ret"] = (
            clean_data.groupby("asset_id")["close"].pct_change().shift(-1)
        )

        dirty_corr = dirty_data["signal_lookahead"].corr(dirty_data["future_ret"])
        clean_corr = clean_data["signal_clean"].corr(clean_data["future_ret"])

        assert abs(dirty_corr) > abs(clean_corr) + 0.2, (
            f"Dirty correlation ({dirty_corr:.3f}) should be much higher "
            f"than clean ({clean_corr:.3f})"
        )


class TestLeakageInjector:
    """Tests for LeakageInjector."""

    @pytest.fixture
    def sample_data(self):
        return generate_aligned_bars(n_assets=5, n_days=100, seed=42)

    def test_injection_adds_column(self, sample_data):
        """Test injection adds signal column."""
        injector = LeakageInjector(leakage_type="close_for_open")
        result = injector.inject(sample_data)

        assert "signal_leaked" in result.columns

    def test_close_for_open_leakage(self, sample_data):
        """Test close_for_open creates intraday correlation."""
        injector = LeakageInjector(leakage_type="close_for_open")
        result = injector.inject(sample_data)
        result = result.reset_index()

        intraday_ret = (result["close"] - result["open"]) / result["open"]
        corr = result["signal_leaked"].corr(intraday_ret)

        assert corr > 0.99, f"Signal should be perfectly correlated: {corr}"

    def test_leakage_types(self, sample_data):
        """Test different leakage types work."""
        for lt in ["close_for_open", "volume_leak", "perfect_rank"]:
            injector = LeakageInjector(leakage_type=lt)
            result = injector.inject(sample_data)
            assert "signal_leaked" in result.columns


class TestSurvivorshipInjector:
    """Tests for SurvivorshipInjector."""

    @pytest.fixture
    def sample_data_with_delistings(self):
        return generate_universe_with_delistings(
            n_assets=10, n_days=100, delist_rate=0.3, seed=42
        )

    def test_injection_removes_assets(self, sample_data_with_delistings):
        """Test injection removes delisted assets."""
        data, delist_info = sample_data_with_delistings
        original_assets = data.reset_index()["asset_id"].nunique()

        injector = SurvivorshipInjector()
        result = injector.inject(data, delist_info=delist_info)

        new_assets = result.reset_index()["asset_id"].nunique()
        assert new_assets < original_assets

    def test_removed_assets_tracked(self, sample_data_with_delistings):
        """Test that removed assets are properly tracked in metadata."""
        data, delist_info = sample_data_with_delistings

        injector = SurvivorshipInjector()
        injector.inject(data, delist_info=delist_info)

        meta = injector.get_injection_metadata()
        assert meta["n_removed"] > 0
        assert len(meta["removed_assets"]) == meta["n_removed"]


class TestCostBlindInjector:
    """Tests for CostBlindInjector."""

    @pytest.fixture
    def sample_data(self):
        return generate_aligned_bars(n_assets=5, n_days=100, seed=42)

    def test_injection_adds_columns(self, sample_data):
        """Test injection adds PnL columns."""
        injector = CostBlindInjector()
        result = injector.inject(sample_data)

        assert "pnl_no_cost" in result.columns
        assert "position_change" in result.columns

    def test_dirty_vs_clean_diverge(self, sample_data):
        """
        CORE TEST: Zero-cost PnL should be higher than
        PnL with realistic costs.
        """
        injector = CostBlindInjector()
        dirty_data = injector.inject(sample_data)

        result_with_cost = compute_returns_with_costs(
            dirty_data,
            commission_bps=10,
            spread_bps=5,
            impact_bps=5,
        )

        dirty_reset = dirty_data.reset_index()
        cost_reset = result_with_cost.reset_index()

        pnl_no_cost = dirty_reset["pnl_no_cost"].sum()
        pnl_with_cost = cost_reset["pnl_with_cost"].sum()

        assert pnl_no_cost > pnl_with_cost, (
            f"Zero-cost PnL ({pnl_no_cost:.4f}) should exceed "
            f"cost-adjusted PnL ({pnl_with_cost:.4f})"
        )
