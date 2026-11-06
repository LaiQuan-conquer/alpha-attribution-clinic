"""
Data leakage detector.
数据泄漏检测器。

Heuristics to detect if features use same-day information
that wouldn't be available at decision time.
检测特征是否使用了决策时点不可用的当日信息。
"""

import pandas as pd
import numpy as np
from .base import BaseDetector, DetectionResult


class LeakageDetector(BaseDetector):
    """
    Detect data leakage through timing analysis.

    Detection methods:
    1. Same-day price relationship detection
    2. Volume-price same-day correlation
    3. Information availability timing checks
    """

    name = "leakage"
    description = "Detects features using same-day information inappropriately"

    def __init__(self, correlation_threshold: float = 0.5):
        self.correlation_threshold = correlation_threshold

    def detect(
        self,
        data: pd.DataFrame,
        signal_col: str = "signal_leaked",
        **kwargs
    ) -> DetectionResult:
        """
        Detect potential data leakage in signal column.
        """
        df = data.copy()
        df = df.reset_index()

        if signal_col not in df.columns:
            return DetectionResult(
                detected=False,
                confidence=0.0,
                evidence={"error": f"Column {signal_col} not found"},
                description="Cannot analyze - signal column missing",
                recommendation="Provide data with signal column",
            )

        required_cols = ["open", "close", "high", "low"]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            return DetectionResult(
                detected=False,
                confidence=0.0,
                evidence={"error": f"Missing columns: {missing}"},
                description="Cannot analyze - price columns missing",
                recommendation="Provide OHLC data",
            )

        df = df.sort_values(["asset_id", "date"])

        df["intraday_return"] = (df["close"] - df["open"]) / df["open"]
        df["intraday_range"] = (df["high"] - df["low"]) / df["open"]

        valid_data = df.dropna(subset=[signal_col, "intraday_return"])

        corr_intraday = valid_data[signal_col].corr(valid_data["intraday_return"])

        detected = abs(corr_intraday) > self.correlation_threshold

        corr_range = valid_data[signal_col].corr(valid_data["intraday_range"])

        if "volume" in df.columns:
            corr_volume = valid_data[signal_col].corr(valid_data["volume"])
        else:
            corr_volume = None

        evidence = {
            "correlation_intraday": float(corr_intraday) if not np.isnan(corr_intraday) else None,
            "correlation_range": float(corr_range) if not np.isnan(corr_range) else None,
            "correlation_volume": float(corr_volume) if corr_volume and not np.isnan(corr_volume) else None,
            "threshold": self.correlation_threshold,
            "n_observations": len(valid_data),
        }

        if detected:
            confidence = min(1.0, abs(corr_intraday) / 0.8)
            description = (
                f"DETECTED: Signal has {corr_intraday:.2%} correlation with intraday return. "
                "This suggests the feature uses same-day close price information."
            )
            recommendation = (
                "Check if the signal computation uses any same-day data. "
                "For open-based decisions, only use data available before market open."
            )
        else:
            confidence = max(0.0, 1.0 - abs(corr_intraday) / self.correlation_threshold)
            description = f"No obvious leakage detected. Intraday correlation: {corr_intraday:.2%}"
            recommendation = "Signal appears clean for same-day leakage."

        return DetectionResult(
            detected=detected,
            confidence=confidence,
            evidence=evidence,
            description=description,
            recommendation=recommendation,
        )
