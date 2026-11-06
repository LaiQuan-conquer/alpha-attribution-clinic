"""
Cost-blind injector.
忽略成本注入器。

Simulates ignoring transaction costs in backtesting,
which leads to unrealistic performance estimates.
模拟在回测中忽略交易成本，导致不切实际的业绩估计。
"""

import pandas as pd
import numpy as np
from typing import Any
from .base import BaseInjector


class CostBlindInjector(BaseInjector):
    """
    Inject cost-blindness by ignoring transaction costs.

    Anti-pattern: Running backtests without considering:
    - Commission/fees
    - Bid-ask spread
    - Market impact
    - Slippage

    High-frequency strategies are especially sensitive to this.
    """

    name = "cost_blind"
    description = "Ignores transaction costs in backtest"

    def __init__(self):
        self._injection_applied = False

    def inject(
        self,
        data: pd.DataFrame,
        positions: pd.DataFrame | None = None,
        **kwargs
    ) -> pd.DataFrame:
        """
        Compute returns WITHOUT transaction costs.

        Parameters
        ----------
        data : pd.DataFrame
            Price data
        positions : pd.DataFrame, optional
            Position data to compute turnover

        Returns
        -------
        pd.DataFrame
            Data with naive (no-cost) strategy returns
        """
        df = data.copy()
        df = df.reset_index()
        df = df.sort_values(["asset_id", "date"])

        df["return"] = df.groupby("asset_id")["close"].pct_change()

        df["signal_naive"] = df.groupby("asset_id")["return"].transform(
            lambda x: x.shift(1).rolling(5).mean()
        )

        df["position_change"] = df.groupby("asset_id")["signal_naive"].diff().abs()
        df["turnover"] = df.groupby("date")["position_change"].transform("mean")

        df["pnl_no_cost"] = df["signal_naive"].shift(1) * df["return"]

        df = df.set_index(["date", "asset_id"])
        self._injection_applied = True
        return df

    def get_injection_metadata(self) -> dict[str, Any]:
        return {
            "injector": self.name,
            "affected_columns": ["pnl_no_cost"],
            "description": "PnL computed without transaction costs",
        }


def compute_returns_with_costs(
    data: pd.DataFrame,
    commission_bps: float = 10.0,
    spread_bps: float = 5.0,
    impact_bps: float = 5.0,
) -> pd.DataFrame:
    """
    Compute returns WITH transaction costs (CORRECT approach).

    Parameters
    ----------
    data : pd.DataFrame
        Price data with 'return', 'signal_naive', 'position_change'
    commission_bps : float
        Commission in basis points (default 10 = 0.1%)
    spread_bps : float
        Half bid-ask spread in basis points
    impact_bps : float
        Market impact in basis points

    Returns
    -------
    pd.DataFrame
        Data with cost-adjusted PnL
    """
    df = data.copy()
    df = df.reset_index()

    if "return" not in df.columns:
        df["return"] = df.groupby("asset_id")["close"].pct_change()

    if "signal_naive" not in df.columns:
        df["signal_naive"] = df.groupby("asset_id")["return"].transform(
            lambda x: x.shift(1).rolling(5).mean()
        )

    if "position_change" not in df.columns:
        df["position_change"] = df.groupby("asset_id")["signal_naive"].diff().abs()

    total_cost_bps = commission_bps + spread_bps + impact_bps
    cost_per_trade = total_cost_bps / 10000

    df["cost"] = df["position_change"].fillna(0) * cost_per_trade

    df["pnl_with_cost"] = (
        df["signal_naive"].shift(1) * df["return"] - df["cost"]
    )

    df = df.set_index(["date", "asset_id"])
    return df


def compute_cost_sensitivity(
    data: pd.DataFrame,
    cost_levels_bps: list[float] = [0, 5, 10, 20, 50, 100],
) -> pd.DataFrame:
    """
    Compute strategy performance across different cost assumptions.
    计算不同成本假设下的策略表现。
    """
    results = []

    for cost_bps in cost_levels_bps:
        df_with_cost = compute_returns_with_costs(
            data,
            commission_bps=cost_bps,
            spread_bps=0,
            impact_bps=0,
        )
        df_with_cost = df_with_cost.reset_index()

        total_pnl = df_with_cost.groupby("date")["pnl_with_cost"].mean().sum()
        results.append({
            "cost_bps": cost_bps,
            "total_pnl": total_pnl,
        })

    return pd.DataFrame(results)
