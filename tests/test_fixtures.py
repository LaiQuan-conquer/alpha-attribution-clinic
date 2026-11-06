"""
Tests for synthetic data fixtures.
合成数据测试。
"""

import pytest
import pandas as pd
import numpy as np

from alpha_attribution_clinic.fixtures import (
    generate_aligned_bars,
    generate_universe_with_delistings,
    get_sample_fixture,
)


class TestGenerateAlignedBars:
    """Tests for generate_aligned_bars."""

    def test_basic_generation(self):
        """Test basic data generation."""
        df = generate_aligned_bars(n_assets=3, n_days=50, seed=42)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3 * 50
        assert df.index.names == ["date", "asset_id"]

    def test_columns_present(self):
        """Test all required columns are present."""
        df = generate_aligned_bars()
        expected_cols = {"open", "high", "low", "close", "volume"}
        assert expected_cols.issubset(set(df.columns))

    def test_reproducibility(self):
        """Test same seed produces same data."""
        df1 = generate_aligned_bars(seed=123)
        df2 = generate_aligned_bars(seed=123)
        pd.testing.assert_frame_equal(df1, df2)

    def test_different_seeds_differ(self):
        """Test different seeds produce different data."""
        df1 = generate_aligned_bars(seed=1)
        df2 = generate_aligned_bars(seed=2)
        assert not df1["close"].equals(df2["close"])

    def test_price_validity(self):
        """Test price relationships are valid."""
        df = generate_aligned_bars()
        assert (df["high"] >= df["low"]).all()
        assert (df["high"] >= df["close"]).all()
        assert (df["low"] <= df["close"]).all()
        assert (df["close"] > 0).all()
        assert (df["volume"] > 0).all()


class TestGenerateUniverseWithDelistings:
    """Tests for generate_universe_with_delistings."""

    def test_basic_generation(self):
        """Test generation with delistings."""
        df, delist_info = generate_universe_with_delistings(
            n_assets=10, n_days=100, delist_rate=0.3, seed=42
        )

        assert isinstance(df, pd.DataFrame)
        assert isinstance(delist_info, pd.DataFrame)
        assert len(delist_info) == 3  # 30% of 10

    def test_delisted_assets_stop_appearing(self):
        """Test delisted assets don't appear after delist date."""
        df, delist_info = generate_universe_with_delistings(
            n_assets=10, n_days=100, delist_rate=0.3, seed=42
        )

        df_reset = df.reset_index()
        for _, row in delist_info.iterrows():
            asset = row["asset_id"]
            delist_date = row["delist_date"]

            asset_data = df_reset[df_reset["asset_id"] == asset]
            max_date = asset_data["date"].max()
            assert max_date < delist_date, f"{asset} appears after delist"

    def test_delist_info_format(self):
        """Test delist_info has correct columns."""
        _, delist_info = generate_universe_with_delistings()
        assert "asset_id" in delist_info.columns
        assert "delist_date" in delist_info.columns


class TestGetSampleFixture:
    """Tests for get_sample_fixture."""

    def test_basic_fixture(self):
        """Test basic fixture retrieval."""
        df = get_sample_fixture("basic")
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

    def test_delistings_fixture(self):
        """Test delistings fixture retrieval."""
        result = get_sample_fixture("with_delistings")
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_unknown_fixture_raises(self):
        """Test unknown fixture name raises error."""
        with pytest.raises(ValueError, match="Unknown fixture"):
            get_sample_fixture("nonexistent")
