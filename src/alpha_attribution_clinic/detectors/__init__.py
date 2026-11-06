"""
Detectors for identifying anti-patterns in research code.
用于识别研究代码中反模式的检测器。

Each detector implements heuristics to flag potential issues.
每个检测器实现启发式方法来标记潜在问题。
"""

from .lookahead_detector import LookaheadDetector
from .leakage_detector import LeakageDetector
from .survivorship_detector import SurvivorshipDetector
from .cost_blind_detector import CostBlindDetector
from .report import DetectionReport, generate_report

__all__ = [
    "LookaheadDetector",
    "LeakageDetector",
    "SurvivorshipDetector",
    "CostBlindDetector",
    "DetectionReport",
    "generate_report",
]
