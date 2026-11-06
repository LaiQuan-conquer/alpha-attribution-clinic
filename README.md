# Alpha Attribution Clinic

**回测异常诊断工作台 / Bad Experiment Clinic**

[![pytest](https://github.com/LaiQuan-conquer/alpha-attribution-clinic/actions/workflows/pytest.yml/badge.svg)](https://github.com/LaiQuan-conquer/alpha-attribution-clinic/actions/workflows/pytest.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## ⚠️ 重要声明 / Important Disclaimer

**本项目仅用于教学和诊断目的。**

- ❌ **无专有因子** - 仅使用公开已知的经典构造
- ❌ **无实盘/模拟盘声明** - 不声称任何策略可盈利
- ❌ **无投资建议** - 本项目不构成任何投资建议
- ✅ **脏实验预期更好看** - 这正是本项目的意义所在

**This project is for TEACHING and DIAGNOSIS purposes ONLY.**

- No proprietary factors
- No live/sim trading claims
- No investment advice
- Dirty experiments are EXPECTED to look better — that is the point

---

## 项目简介 / Overview

`alpha-attribution-clinic` 是一个"坏实验诊所"：

1. **注入 (Inject)** - 故意向实验数据注入常见反模式
2. **检测 (Detect)** - 使用启发式方法检测这些问题
3. **报告 (Report)** - 生成诊断报告和案例复盘

### 支持的反模式 / Supported Anti-patterns

| 类型 | 中文名 | 描述 |
|------|--------|------|
| `lookahead` | 前视偏差 | 特征计算使用了未来数据 |
| `leakage` | 数据泄漏 | 使用了决策时点不可用的当日数据 |
| `survivorship` | 幸存者偏差 | 仅分析当前存活资产，忽略已退市标的 |
| `cost_blind` | 忽略成本 | 回测未考虑交易成本、滑点等 |

---

## 快速开始 / Quick Start

### 安装 / Installation

```bash
# 克隆仓库
git clone https://github.com/LaiQuan-conquer/alpha-attribution-clinic.git
cd alpha-attribution-clinic

# 安装（开发模式）
pip install -e ".[dev]"
```

### 运行演示 / Run Demo

```bash
# 运行完整演示：注入 → 检测 → 报告
clinic demo

# 或分步执行
clinic inject --type all --output dirty_data.csv
clinic detect --input dirty_data.csv --format markdown
```

### 运行测试 / Run Tests

```bash
pytest -v
```

---

## 使用示例 / Usage Examples

### Python API

```python
from alpha_attribution_clinic.fixtures import generate_aligned_bars
from alpha_attribution_clinic.injectors import LookaheadInjector
from alpha_attribution_clinic.detectors import LookaheadDetector

# 生成干净的合成数据
clean_data = generate_aligned_bars(n_assets=5, n_days=100, seed=42)

# 注入前视偏差
injector = LookaheadInjector(lookahead_days=1)
dirty_data = injector.inject(clean_data)

# 检测问题
detector = LookaheadDetector(correlation_threshold=0.3)
result = detector.detect(dirty_data, signal_col="signal_lookahead")

print(f"检测到问题: {result.detected}")
print(f"置信度: {result.confidence:.1%}")
print(f"建议: {result.recommendation}")
```

### CLI 命令

```bash
# 注入特定类型的偏差
clinic inject --type lookahead --output lookahead_data.csv
clinic inject --type survivorship --output survivor_data.csv

# 检测并生成报告
clinic detect --input dirty_data.csv --format json --output report.json
clinic detect --input dirty_data.csv --format markdown > report.md
```

---

## 项目结构 / Project Structure

```
alpha-attribution-clinic/
├── src/alpha_attribution_clinic/
│   ├── __init__.py
│   ├── cli.py                 # 命令行接口
│   ├── fixtures/              # 合成数据生成
│   │   ├── __init__.py
│   │   └── synthetic_data.py
│   ├── injectors/             # 反模式注入器
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── lookahead.py       # 前视偏差
│   │   ├── leakage.py         # 数据泄漏
│   │   ├── survivorship.py    # 幸存者偏差
│   │   └── cost_blind.py      # 忽略成本
│   └── detectors/             # 检测启发式
│       ├── __init__.py
│       ├── base.py
│       ├── lookahead_detector.py
│       ├── leakage_detector.py
│       ├── survivorship_detector.py
│       ├── cost_blind_detector.py
│       └── report.py
├── cases/                     # 案例复盘（可转化为试题）
│   ├── TEMPLATE.md
│   └── 01_lookahead_bias.md
├── tests/                     # 测试套件
│   ├── test_fixtures.py
│   ├── test_injectors.py
│   ├── test_detectors.py
│   └── test_cli.py
├── pyproject.toml
├── LICENSE
└── README.md
```

---

## 核心设计 / Core Design

### 1. 合成数据 (Fixtures)

所有测试使用合成数据，确保：
- **离线运行** - 无需网络或API密钥
- **可复现** - 固定随机种子
- **对齐时间戳** - 干净数据无前视问题

```python
from alpha_attribution_clinic.fixtures import generate_aligned_bars

# 基础数据集
data = generate_aligned_bars(n_assets=5, n_days=100, seed=42)

# 包含退市的数据集
data, delist_info = generate_universe_with_delistings(
    n_assets=10, n_days=100, delist_rate=0.3
)
```

### 2. 注入器 (Injectors)

每个注入器实现一种反模式：

```python
# 前视偏差：使用未来收益作为特征
LookaheadInjector(lookahead_days=1)

# 数据泄漏：使用当日收盘价做开盘决策
LeakageInjector(leakage_type="close_for_open")

# 幸存者偏差：移除已退市资产
SurvivorshipInjector()

# 忽略成本：不计算交易费用
CostBlindInjector()
```

### 3. 检测器 (Detectors)

每个检测器使用启发式方法识别问题：

```python
# 检测前视：信号与未来收益相关性异常高
LookaheadDetector(correlation_threshold=0.3)

# 检测泄漏：信号与当日收益相关性异常高
LeakageDetector(correlation_threshold=0.5)

# 检测幸存者偏差：对比已知退市列表
SurvivorshipDetector()

# 检测成本忽略：高换手无成本扣除
CostBlindDetector()
```

---

## 如何将案例转化为试题 / Creating Exam Questions

每个案例复盘 (`cases/`) 包含：

1. **现象** - 异常的回测结果
2. **根因** - 技术问题分析
3. **错误代码** - 有问题的代码示例
4. **正确代码** - 修复后的代码
5. **题干示例** - 可直接用于考试
6. **采分点** - 评分标准

参见 [`cases/01_lookahead_bias.md`](cases/01_lookahead_bias.md) 了解完整示例。

---

## 测试验证 / Test Verification

测试套件验证两个核心断言：

1. **脏 vs 干净分叉** - 注入反模式后，实验结果应显著"更好"
2. **检测器捕获** - 检测器应能识别注入的问题

```bash
# 运行所有测试
pytest -v

# 运行特定测试
pytest tests/test_injectors.py -v
pytest tests/test_detectors.py -v
```

---

## 贡献 / Contributing

欢迎贡献新的反模式、检测器或案例复盘！

1. Fork 本仓库
2. 创建特性分支
3. 提交 Pull Request

---

## 许可证 / License

MIT License - 详见 [LICENSE](LICENSE)

---

## 致谢 / Acknowledgments

本项目受以下资源启发：

- Lopez de Prado, M. (2018). *Advances in Financial Machine Learning*
- Bailey, D. et al. (2014). "The Probability of Backtest Overfitting"
- [polakowo/vectorbt](https://github.com/polakowo/vectorbt)
- [stefan-jansen/alphalens-reloaded](https://github.com/stefan-jansen/alphalens-reloaded)

---

**记住：脏实验看起来更好 — 这就是为什么我们需要学会识别它们。**

**Remember: Dirty experiments look better — that's why we need to learn to detect them.**
