"""
Tests for anti-pattern detectors.
反模式检测器测试。

Core assertion: detectors should catch injected biases.
核心断言：检测器应捕获注入的偏差。
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
from alpha_attribution_clinic.detectors import (
    LookaheadDetector,
    LeakageDetector,
    SurvivorshipDetector,
    CostBlindDetector,
    generate_report,
)


class TestLookaheadDetector:
    """Tests for LookaheadDetector."""

    @pytest.fixture
    def dirty_data(self):
        data = generate_aligned_bars(n_assets=5, n_days=100, seed=42)
        injector = LookaheadInjector(lookahead_days=1)
        return injector.inject(data)

    @pytest.fixture
    def clean_data(self):
        data = generate_aligned_bars(n_assets=5, n_days=100, seed=42)
        data = data.reset_index()
        data["signal_lookahead"] = (
            data.groupby("asset_id")["close"].shift(1).pct_change(5)
        )
        data = data.set_index(["date", "asset_id"])
        return data

    def test_detects_lookahead_bias(self, dirty_data):
        """CORE TEST: Detector catches lookahead injection."""
        detector = LookaheadDetector(correlation_threshold=0.3)
        result = detector.detect(dirty_data, signal_col="signal_lookahead")

        assert bool(result.detected) is True, "Should detect lookahead bias"
        assert result.confidence > 0.5, "Should have high confidence"

    def test_clean_data_passes(self, clean_data):
        """Clean data should not trigger detection."""
        detector = LookaheadDetector(correlation_threshold=0.3)
        result = detector.detect(clean_data, signal_col="signal_lookahead")

        assert bool(result.detected) is False, "Clean data should pass"

    def test_evidence_contains_correlation(self, dirty_data):
        """Evidence should include correlation metrics."""
        detector = LookaheadDetector()
        result = detector.detect(dirty_data, signal_col="signal_lookahead")

        assert "correlation_1d" in result.evidence
        assert "max_correlation" in result.evidence


class TestLeakageDetector:
    """Tests for LeakageDetector."""

    @pytest.fixture
    def dirty_data(self):
        data = generate_aligned_bars(n_assets=5, n_days=100, seed=42)
        injector = LeakageInjector(leakage_type="close_for_open")
        return injector.inject(data)

    def test_detects_leakage(self, dirty_data):
        """CORE TEST: Detector catches data leakage."""
        detector = LeakageDetector(correlation_threshold=0.5)
        result = detector.detect(dirty_data, signal_col="signal_leaked")

        assert bool(result.detected) is True, "Should detect leakage"
        assert result.confidence > 0.5


class TestSurvivorshipDetector:
    """Tests for SurvivorshipDetector."""

    @pytest.fixture
    def data_with_delistings(self):
        return generate_universe_with_delistings(
            n_assets=10, n_days=100, delist_rate=0.3, seed=42
        )

    def test_detects_missing_delistings(self, data_with_delistings):
        """CORE TEST: Detector catches survivorship bias."""
        clean_data, delist_info = data_with_delistings

        injector = SurvivorshipInjector()
        dirty_data = injector.inject(clean_data.copy(), delist_info=delist_info)

        detector = SurvivorshipDetector()
        result = detector.detect(dirty_data, delist_info=delist_info)

        assert bool(result.detected) is True, "Should detect survivorship bias"
        assert "missing_delisted_assets" in result.evidence

    def test_clean_data_passes(self, data_with_delistings):
        """Point-in-time data should not trigger detection."""
        clean_data, delist_info = data_with_delistings

        detector = SurvivorshipDetector()
        result = detector.detect(clean_data, delist_info=delist_info)

        assert bool(result.detected) is False, "Clean data should pass"


class TestCostBlindDetector:
    """Tests for CostBlindDetector."""

    @pytest.fixture
    def dirty_data(self):
        data = generate_aligned_bars(n_assets=5, n_days=100, seed=42)
        injector = CostBlindInjector()
        return injector.inject(data)

    def test_detects_cost_blindness(self, dirty_data):
        """CORE TEST: Detector catches cost-blind strategy."""
        detector = CostBlindDetector(high_turnover_threshold=0.001)
        result = detector.detect(dirty_data, assumed_cost_bps=20.0)

        assert bool(result.detected) is True, "Should detect cost blindness"
        assert "has_cost_column" in result.evidence
        assert result.evidence["has_cost_column"] is False

    def test_no_cost_column_flagged(self, dirty_data):
        """Should flag missing cost column with high turnover."""
        detector = CostBlindDetector(high_turnover_threshold=0.0001)
        result = detector.detect(dirty_data)

        assert result.evidence["has_cost_column"] is False


class TestReportGeneration:
    """Tests for report generation."""

    @pytest.fixture
    def fully_dirty_data(self):
        data = generate_aligned_bars(n_assets=5, n_days=100, seed=42)

        la = LookaheadInjector(lookahead_days=1)
        data = la.inject(data)

        le = LeakageInjector(leakage_type="close_for_open")
        data = le.inject(data)

        cb = CostBlindInjector()
        data = cb.inject(data)

        return data

    def test_report_captures_all_issues(self, fully_dirty_data):
        """Report should capture multiple issues."""
        report = generate_report(fully_dirty_data)

        assert report.summary["total_checks"] == 4
        assert report.summary["issues_detected"] >= 2

    def test_report_formats(self, fully_dirty_data):
        """Report should export to multiple formats."""
        report = generate_report(fully_dirty_data)

        json_out = report.to_json()
        assert "summary" in json_out

        md_out = report.to_markdown()
        assert "# Detection Report" in md_out

        dict_out = report.to_dict()
        assert isinstance(dict_out, dict)
