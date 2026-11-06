"""
Synthetic data generator for reproducible offline testing.
用于可复现离线测试的合成数据生成器。

Design principles:
- Deterministic with seed for reproducibility
- Aligned timestamps (no look-ahead in clean data)
- Includes delisting events for survivorship bias testing
"""

import numpy as np
import pandas as pd
from typing import Optional


def generate_aligned_bars(
    n_assets: int = 5,
    n_days: int = 252,
    seed: int = 42,
    start_date: str = "2020-01-01",
) -> pd.DataFrame:
    """
    Generate synthetic OHLCV bars with aligned timestamps.

    The data is deliberately simple and synthetic - not meant to
    represent real market dynamics. Each asset follows a random walk.

    Parameters
    ----------
    n_assets : int
        Number of synthetic assets to generate
    n_days : int
        Number of trading days
    seed : int
        Random seed for reproducibility
    start_date : str
        Start date for the time series

    Returns
    -------
    pd.DataFrame
        MultiIndex DataFrame with (date, asset_id) index and OHLCV columns.
        All prices are available at market close of each date.
        Feature computation should use data up to t-1 to predict returns at t.
    """
    np.random.seed(seed)

    dates = pd.bdate_range(start=start_date, periods=n_days, freq="B")
    assets = [f"ASSET_{i:03d}" for i in range(n_assets)]

    records = []
    for asset in assets:
        base_price = 100.0
        prices = [base_price]
        for _ in range(n_days - 1):
            daily_return = np.random.normal(0.0005, 0.02)
            prices.append(prices[-1] * (1 + daily_return))

        for i, date in enumerate(dates):
            close = prices[i]
            high = close * (1 + abs(np.random.normal(0, 0.005)))
            low = close * (1 - abs(np.random.normal(0, 0.005)))
            open_ = (high + low) / 2 + np.random.normal(0, 0.001) * close
            volume = int(np.random.lognormal(15, 1))

            records.append({
                "date": date,
                "asset_id": asset,
                "open": round(open_, 2),
                "high": round(high, 2),
                "low": round(low, 2),
                "close": round(close, 2),
                "volume": volume,
            })

    df = pd.DataFrame(records)
    df = df.set_index(["date", "asset_id"]).sort_index()
    return df


def generate_universe_with_delistings(
    n_assets: int = 10,
    n_days: int = 252,
    delist_rate: float = 0.2,
    seed: int = 42,
    start_date: str = "2020-01-01",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generate synthetic data with some assets delisting mid-period.

    This is useful for testing survivorship bias:
    - Clean analysis should use point-in-time universe
    - Dirty analysis uses only currently-surviving assets

    Parameters
    ----------
    n_assets : int
        Total number of assets (some will delist)
    n_days : int
        Number of trading days
    delist_rate : float
        Fraction of assets that will delist before end
    seed : int
        Random seed
    start_date : str
        Start date

    Returns
    -------
    tuple[pd.DataFrame, pd.DataFrame]
        (price_data, delist_info)
        price_data: OHLCV data (assets stop appearing after delist)
        delist_info: DataFrame with asset_id, delist_date columns
    """
    np.random.seed(seed)

    n_delist = int(n_assets * delist_rate)
    dates = pd.bdate_range(start=start_date, periods=n_days, freq="B")
    assets = [f"ASSET_{i:03d}" for i in range(n_assets)]

    delist_assets = np.random.choice(assets, size=n_delist, replace=False)
    delist_dates = {
        asset: dates[np.random.randint(n_days // 4, 3 * n_days // 4)]
        for asset in delist_assets
    }

    delist_info = pd.DataFrame([
        {"asset_id": asset, "delist_date": delist_date}
        for asset, delist_date in delist_dates.items()
    ])

    records = []
    for asset in assets:
        base_price = 100.0
        prices = [base_price]
        for _ in range(n_days - 1):
            if asset in delist_assets:
                daily_return = np.random.normal(-0.002, 0.03)
            else:
                daily_return = np.random.normal(0.001, 0.02)
            prices.append(max(0.01, prices[-1] * (1 + daily_return)))

        for i, date in enumerate(dates):
            if asset in delist_dates and date >= delist_dates[asset]:
                continue

            close = prices[i]
            high = close * (1 + abs(np.random.normal(0, 0.005)))
            low = close * (1 - abs(np.random.normal(0, 0.005)))
            open_ = (high + low) / 2
            volume = int(np.random.lognormal(15, 1))

            records.append({
                "date": date,
                "asset_id": asset,
                "open": round(open_, 2),
                "high": round(high, 2),
                "low": round(low, 2),
                "close": round(close, 2),
                "volume": volume,
            })

    df = pd.DataFrame(records)
    df = df.set_index(["date", "asset_id"]).sort_index()
    return df, delist_info


def get_sample_fixture(name: str = "basic") -> pd.DataFrame:
    """
    Get a pre-defined sample fixture for testing.

    Parameters
    ----------
    name : str
        Fixture name: "basic", "with_delistings"

    Returns
    -------
    pd.DataFrame or tuple
        The fixture data
    """
    if name == "basic":
        return generate_aligned_bars(n_assets=5, n_days=100, seed=42)
    elif name == "with_delistings":
        return generate_universe_with_delistings(
            n_assets=10, n_days=100, delist_rate=0.3, seed=42
        )
    else:
        raise ValueError(f"Unknown fixture: {name}. Available: basic, with_delistings")
