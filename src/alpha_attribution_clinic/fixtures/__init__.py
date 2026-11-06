"""
Synthetic fixtures for offline testing.
合成测试数据集，用于离线测试。

All data is synthetic - no real market data, no API keys required.
所有数据均为合成数据——无真实市场数据，无需API密钥。
"""

from .synthetic_data import (
    generate_aligned_bars,
    generate_universe_with_delistings,
    get_sample_fixture,
)

__all__ = [
    "generate_aligned_bars",
    "generate_universe_with_delistings",
    "get_sample_fixture",
]
