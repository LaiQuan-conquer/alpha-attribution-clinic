"""
Alpha Attribution Clinic - Bad Experiment Diagnosis Toolkit

⚠️ DISCLAIMER / 免责声明:
This project is for TEACHING and DIAGNOSIS purposes ONLY.
本项目仅用于教学和诊断目的。

- No proprietary factors / 无专有因子
- No live/sim trading claims / 无实盘/模拟盘声明
- No investment advice / 无投资建议
- Dirty experiments are EXPECTED to look better - that is the point
  脏实验预期会看起来更好——这正是本项目的意义所在

The purpose is to demonstrate anti-patterns and teach how to detect them,
NOT to produce profitable trading signals.
目的是展示反模式并教授如何检测它们，而非产出盈利交易信号。
"""

__version__ = "0.1.0"

from . import injectors
from . import detectors
from . import fixtures

__all__ = ["injectors", "detectors", "fixtures", "__version__"]
