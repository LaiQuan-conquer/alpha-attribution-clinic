"""
Anti-pattern injectors for teaching bad practices.
反模式注入器，用于教学目的。

Each injector takes clean data/strategy and introduces a specific bias.
每个注入器接收干净的数据/策略，并引入特定的偏差。

WARNING: These deliberately create WRONG results to demonstrate anti-patterns.
警告：这些注入器故意创建错误结果以展示反模式。
"""

from .lookahead import LookaheadInjector
from .leakage import LeakageInjector
from .survivorship import SurvivorshipInjector
from .cost_blind import CostBlindInjector

__all__ = [
    "LookaheadInjector",
    "LeakageInjector",
    "SurvivorshipInjector",
    "CostBlindInjector",
]
