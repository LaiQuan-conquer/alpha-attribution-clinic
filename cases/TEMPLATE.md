# 案例复盘模板 / Case Writeup Template

## 现象 / Phenomenon

> 描述观察到的异常现象

**示例**：回测 Sharpe Ratio 达到 5.0，远超正常策略水平。

## 根因 / Root Cause

> 分析导致该现象的技术原因

**示例**：特征计算使用了当日收盘价预测当日收益，存在前视偏差。

### 错误代码片段 / Buggy Code

```python
# ❌ 错误示例
df["signal"] = df["close"].pct_change()  # 使用当日数据
df["target"] = df["close"].shift(-1) / df["close"] - 1
```

### 问题分析 / Analysis

- 在实际交易中，t 时刻无法获得 t 时刻的收盘价
- 此计算等同于"用答案算答案"
- 回测结果虚高，无法复现于实盘

## 修复 / Fix

### 正确代码 / Correct Code

```python
# ✅ 正确示例
df["signal"] = df["close"].shift(1).pct_change()  # 使用 t-1 数据
df["target"] = df["close"].shift(-1) / df["close"] - 1
```

### 修复要点 / Key Points

1. 特征计算必须使用 t-1 及更早的数据
2. 信号在 t-1 收盘后计算，t 开盘时执行
3. 验证方法：检查特征与未来收益的相关性应接近 0

## 如何转化为考题 / How This Becomes an Exam Question

### 题干示例 / Sample Question

> 以下回测代码的 Sharpe Ratio 为 3.2，但实盘后 Sharpe 仅为 0.3。
> 请分析可能的原因并给出修复方案。

```python
def compute_signal(df):
    df["momentum"] = df["close"].pct_change(5)
    return df["momentum"]
```

### 追问 / Follow-up Questions

1. 如何通过数据分析检测此类问题？
2. 还有哪些常见的前视偏差场景？
3. 如何设计测试用例防止此类问题？

### 采分点 / Scoring Rubric

| 要点 | 分值 |
|------|------|
| 识别前视偏差 | 2分 |
| 解释时间对齐问题 | 2分 |
| 给出正确修复代码 | 3分 |
| 说明检测方法 | 2分 |
| 提出预防措施 | 1分 |

---

## 检测器验证 / Detector Validation

```python
from alpha_attribution_clinic.detectors import LookaheadDetector

detector = LookaheadDetector(correlation_threshold=0.3)
result = detector.detect(dirty_data, signal_col="signal")

assert result.detected == True
assert result.confidence > 0.5
```

## 参考资料 / References

- [Advances in Financial Machine Learning - Chapter 7](https://www.wiley.com/en-us/Advances+in+Financial+Machine+Learning-p-9781119482086)
- [Common pitfalls in backtesting](https://quantstrattrader.com/2016/03/09/common-pitfalls-in-quantitative-backtesting/)
