"""
Data leakage injector.
数据泄漏注入器。

Simulates using information that wouldn't be available at decision time
due to data timing issues (not future data, but same-day data that
arrives after market close).
模拟使用在决策时点不可用的信息（非未来数据，而是在收盘后才到达的当日数据）。
"""

import pandas as pd
import numpy as np
from typing import Any
from .base import BaseInjector


class LeakageInjector(BaseInjector):
    """
    Inject data leakage by using same-day information.

    Anti-pattern: Using data that technically exists at time t but
    wouldn't be available for trading decisions.

    Examples this simulates:
    - Using close price to make open-price decisions
    - Using end-of-day volume in pre-market
    - Using same-day announcement data before it's released
    """

    name = "leakage"
    description = "Uses same-day data that wouldn't be available at decision time"

    def __init__(self, leakage_type: str = "close_for_open"):
        """
        Parameters
        ----------
        leakage_type : str
            Type of leakage: "close_for_open", "volume_leak", "perfect_rank"
        """
        self.leakage_type = leakage_type
        self._injection_applied = False

    def inject(self, data: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """
        Add features with data leakage.
        """
        df = data.copy()
        df = df.reset_index()
        df = df.sort_values(["asset_id", "date"])

        if self.leakage_type == "close_for_open":
            intraday_return = (df["close"] - df["open"]) / df["open"]
            df["signal_leaked"] = intraday_return

        elif self.leakage_type == "volume_leak":
            df["volume_zscore"] = df.groupby("date")["volume"].transform(
                lambda x: (x - x.mean()) / (x.std() + 1e-8)
            )
            next_day_return = df.groupby("asset_id")["close"].pct_change().shift(-1)
            correlation = df.groupby("asset_id").apply(
                lambda g: g["volume_zscore"].corr(next_day_return.loc[g.index])
            )
            df["signal_leaked"] = df["volume_zscore"]

        elif self.leakage_type == "perfect_rank":
            df["future_return"] = df.groupby("asset_id")["close"].pct_change().shift(-1)
            df["signal_leaked"] = df.groupby("date")["future_return"].rank(pct=True)
            df = df.drop(columns=["future_return"])

        else:
            raise ValueError(f"Unknown leakage type: {self.leakage_type}")

        df = df.set_index(["date", "asset_id"])
        self._injection_applied = True
        return df

    def get_injection_metadata(self) -> dict[str, Any]:
        return {
            "injector": self.name,
            "leakage_type": self.leakage_type,
            "affected_columns": ["signal_leaked"],
            "description": f"Feature uses {self.leakage_type} leakage pattern",
        }


def compute_clean_volume_signal(data: pd.DataFrame, lookback: int = 5) -> pd.DataFrame:
    """
    Compute volume signal the CORRECT way: using lagged data.
    使用正确方式计算成交量信号：使用滞后数据。
    """
    df = data.copy()
    df = df.reset_index()
    df = df.sort_values(["asset_id", "date"])

    df["volume_ma"] = df.groupby("asset_id")["volume"].transform(
        lambda x: x.shift(1).rolling(lookback).mean()
    )
    df["signal_clean"] = df["volume"] / (df["volume_ma"] + 1)

    df = df.set_index(["date", "asset_id"])
    return df
