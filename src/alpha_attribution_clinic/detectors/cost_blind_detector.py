"""
Cost-blindness detector.
忽略成本检测器。

Heuristics to detect if strategy ignores transaction costs.
检测策略是否忽略了交易成本。
"""

import pandas as pd
import numpy as np
from .base import BaseDetector, DetectionResult


class CostBlindDetector(BaseDetector):
    """
    Detect cost-blindness through turnover and PnL analysis.

    Detection methods:
    1. High turnover with no cost deduction
    2. Compare zero-cost vs realistic-cost performance
    3. Check for cost column presence
    """

    name = "cost_blind"
    description = "Detects if transaction costs are ignored in backtesting"

    def __init__(
        self,
        high_turnover_threshold: float = 0.2,
        cost_sensitivity_threshold: float = 0.5,
    ):
        """
        Parameters
        ----------
        high_turnover_threshold : float
            Daily turnover above this is considered high
        cost_sensitivity_threshold : float
            If costs reduce Sharpe by more than this fraction, flag it
        """
        self.high_turnover_threshold = high_turnover_threshold
        self.cost_sensitivity_threshold = cost_sensitivity_threshold

    def detect(
        self,
        data: pd.DataFrame,
        assumed_cost_bps: float = 20.0,
        **kwargs
    ) -> DetectionResult:
        """
        Detect if strategy would be significantly impacted by costs.

        Parameters
        ----------
        data : pd.DataFrame
            Data with position changes or PnL
        assumed_cost_bps : float
            Assumed round-trip cost in basis points
        """
        df = data.copy()
        df = df.reset_index()

        has_cost_column = "cost" in df.columns or "pnl_with_cost" in df.columns
        has_no_cost_pnl = "pnl_no_cost" in df.columns

        if "position_change" in df.columns:
            avg_turnover = df["position_change"].mean()
            high_turnover = avg_turnover > self.high_turnover_threshold
        else:
            avg_turnover = None
            high_turnover = False

        if has_no_cost_pnl and "position_change" in df.columns:
            cost_per_trade = assumed_cost_bps / 10000
            implied_costs = df["position_change"].fillna(0) * cost_per_trade
            pnl_with_implied_cost = df["pnl_no_cost"] - implied_costs

            daily_pnl_no_cost = df.groupby("date")["pnl_no_cost"].mean()
            daily_pnl_with_cost = df.groupby("date").apply(
                lambda g: (g["pnl_no_cost"] - implied_costs.loc[g.index]).mean()
            )

            sharpe_no_cost = (
                daily_pnl_no_cost.mean() / (daily_pnl_no_cost.std() + 1e-8) * np.sqrt(252)
            )
            sharpe_with_cost = (
                daily_pnl_with_cost.mean() / (daily_pnl_with_cost.std() + 1e-8) * np.sqrt(252)
            )

            if sharpe_no_cost > 0:
                sharpe_degradation = (sharpe_no_cost - sharpe_with_cost) / sharpe_no_cost
            else:
                sharpe_degradation = 0

            cost_sensitive = sharpe_degradation > self.cost_sensitivity_threshold
        else:
            sharpe_no_cost = None
            sharpe_with_cost = None
            sharpe_degradation = None
            cost_sensitive = False

        detected = (not has_cost_column) and (high_turnover or cost_sensitive)

        evidence = {
            "has_cost_column": has_cost_column,
            "avg_turnover": float(avg_turnover) if avg_turnover is not None else None,
            "high_turnover": high_turnover,
            "turnover_threshold": self.high_turnover_threshold,
            "assumed_cost_bps": assumed_cost_bps,
            "sharpe_no_cost": float(sharpe_no_cost) if sharpe_no_cost is not None else None,
            "sharpe_with_cost": float(sharpe_with_cost) if sharpe_with_cost is not None else None,
            "sharpe_degradation": float(sharpe_degradation) if sharpe_degradation is not None else None,
        }

        if detected:
            if cost_sensitive:
                confidence = min(1.0, sharpe_degradation) if sharpe_degradation else 0.7
                description = (
                    f"DETECTED: Strategy shows {sharpe_degradation:.1%} Sharpe degradation "
                    f"with {assumed_cost_bps}bps costs. No cost column found."
                )
            else:
                confidence = 0.6
                description = (
                    f"DETECTED: High turnover ({avg_turnover:.2%} daily) but no cost accounting. "
                    "Performance may be unrealistic."
                )
            recommendation = (
                "Add transaction cost modeling. Include commission, spread, and impact. "
                "Run sensitivity analysis across different cost assumptions."
            )
        else:
            if has_cost_column:
                confidence = 1.0
                description = "Cost column present - costs appear to be modeled."
            else:
                confidence = 0.3
                description = "No obvious cost issue, but cost column not found."
            recommendation = "Verify cost assumptions are realistic for your strategy."

        return DetectionResult(
            detected=detected,
            confidence=confidence,
            evidence=evidence,
            description=description,
            recommendation=recommendation,
        )
