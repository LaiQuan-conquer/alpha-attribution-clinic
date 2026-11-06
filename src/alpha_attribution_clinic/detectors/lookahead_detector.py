"""
Lookahead bias detector.
前视偏差检测器。

Heuristics to detect if features are using future information.
检测特征是否使用了未来信息的启发式方法。
"""

import pandas as pd
import numpy as np
from .base import BaseDetector, DetectionResult


class LookaheadDetector(BaseDetector):
    """
    Detect lookahead bias through statistical analysis.

    Detection methods:
    1. Correlation with future returns (should be ~0 for valid features)
    2. Information coefficient timing analysis
    3. Perfect prediction detection (too-good-to-be-true signals)
    """

    name = "lookahead"
    description = "Detects features that correlate suspiciously with future returns"

    def __init__(self, correlation_threshold: float = 0.3):
        """
        Parameters
        ----------
        correlation_threshold : float
            Correlation above this triggers detection (default 0.3)
        """
        self.correlation_threshold = correlation_threshold

    def detect(
        self,
        data: pd.DataFrame,
        signal_col: str = "signal_lookahead",
        **kwargs
    ) -> DetectionResult:
        """
        Detect potential lookahead bias in signal column.

        Checks if the signal has suspicious correlation with future returns.
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

        if "close" not in df.columns:
            return DetectionResult(
                detected=False,
                confidence=0.0,
                evidence={"error": "close column not found"},
                description="Cannot analyze - close price missing",
                recommendation="Provide data with close prices",
            )

        df = df.sort_values(["asset_id", "date"])
        df["future_return_1d"] = df.groupby("asset_id")["close"].pct_change().shift(-1)
        df["future_return_5d"] = df.groupby("asset_id")["close"].pct_change(5).shift(-5)

        valid_data = df.dropna(subset=[signal_col, "future_return_1d"])

        if len(valid_data) < 10:
            return DetectionResult(
                detected=False,
                confidence=0.0,
                evidence={"error": "Insufficient data"},
                description="Not enough data points for analysis",
                recommendation="Provide more data",
            )

        corr_1d = valid_data[signal_col].corr(valid_data["future_return_1d"])
        corr_5d = valid_data.dropna(subset=["future_return_5d"])[signal_col].corr(
            valid_data.dropna(subset=["future_return_5d"])["future_return_5d"]
        )

        max_corr = max(abs(corr_1d), abs(corr_5d) if not np.isnan(corr_5d) else 0)

        ic_by_date = valid_data.groupby("date").apply(
            lambda g: g[signal_col].corr(g["future_return_1d"])
        )
        ic_stability = ic_by_date.std() if len(ic_by_date) > 1 else 0

        detected = max_corr > self.correlation_threshold

        if detected:
            confidence = min(1.0, max_corr / 0.5)
        else:
            confidence = max(0.0, 1.0 - max_corr / self.correlation_threshold)

        evidence = {
            "correlation_1d": float(corr_1d) if not np.isnan(corr_1d) else None,
            "correlation_5d": float(corr_5d) if not np.isnan(corr_5d) else None,
            "max_correlation": float(max_corr),
            "threshold": self.correlation_threshold,
            "ic_stability": float(ic_stability) if not np.isnan(ic_stability) else None,
            "n_observations": len(valid_data),
        }

        if detected:
            description = (
                f"DETECTED: Signal has {max_corr:.2%} correlation with future returns. "
                f"This is suspiciously high and suggests lookahead bias."
            )
            recommendation = (
                "Review feature computation. Ensure you use data from t-1 to predict "
                "returns at t. Check for any peeking at future prices or volumes."
            )
        else:
            description = (
                f"No obvious lookahead detected. Correlation with future: {max_corr:.2%}"
            )
            recommendation = "Signal appears clean, but always verify computation logic."

        return DetectionResult(
            detected=detected,
            confidence=confidence,
            evidence=evidence,
            description=description,
            recommendation=recommendation,
        )
