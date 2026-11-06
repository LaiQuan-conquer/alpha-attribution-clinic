# 案例 01：前视偏差 / Case 01: Lookahead Bias

## 现象 / Phenomenon

回测显示动量策略 IC (信息系数) 高达 0.85，Sharpe Ratio 达到 4.5。
但任何经验丰富的量化研究员都知道，这个数字"好得不真实"。

**关键指标**：
- IC: 0.85 (正常范围: 0.02-0.10)
- Sharpe: 4.5 (正常范围: 0.5-2.0)
- 胜率: 78% (正常范围: 50-55%)

## 根因 / Root Cause

特征计算中不小心使用了"当日收益"来预测"当日收益"。
这等同于"用答案预测答案"。

### 错误代码片段 / Buggy Code

```python
# ❌ 错误：直接使用当日收益率作为特征
def compute_momentum_wrong(df):
    # 这个"特征"实际上包含了我们要预测的信息
    df["signal"] = df.groupby("asset_id")["close"].pct_change()
    return df

# 然后用来预测：
df["future_return"] = df.groupby("asset_id")["close"].pct_change().shift(-1)
# signal 和 future_return 高度相关！
```

### 问题分析 / Analysis

1. **时间线问题**：
   - t 日收盘价在 t 日收盘后才可知
   - 基于 t 日数据的信号只能在 t+1 日执行
   - 但代码将 t 日信号与 t 日收益对应

2. **为什么回测好看**：
   - 当日收益与"动量"自然相关
   - 实际是在测试"今天涨的股票今天涨"

3. **为什么实盘崩溃**：
   - 实盘中你无法"知道今天会涨然后买入"
   - 信号滞后一天后，相关性消失

## 修复 / Fix

### 正确代码 / Correct Code

```python
# ✅ 正确：使用 t-1 数据计算 t 日信号
def compute_momentum_correct(df):
    # shift(1) 确保使用昨日收盘价
    df["signal"] = df.groupby("asset_id")["close"].shift(1).pct_change(5)
    return df

# 时间线：
# t-6 到 t-1 的收益 → t 日信号 → t 日开盘执行 → t 日收盘结算
```

### 修复要点 / Key Points

1. **黄金法则**：特征计算时，任何价格都要 `shift(1)`
2. **验证方法**：计算 IC 时，信号与未来收益相关性应 < 0.1
3. **防御措施**：在代码审查中强制检查 shift

## 如何转化为考题 / How This Becomes an Exam Question

### 题干示例 / Sample Question

> **场景**：某量化研究员提交了以下动量因子代码，回测 Sharpe 为 3.8。
> 
> ```python
> def compute_momentum(prices):
>     returns = prices.pct_change(20)
>     signal = returns.rank(pct=True)
>     return signal
> ```
> 
> **问题**：
> 1. 该代码存在什么问题？(3分)
> 2. 如何修复？(3分)
> 3. 如何通过统计方法检测此问题？(2分)
> 4. 如何设计测试防止此问题再次发生？(2分)

### 标准答案 / Expected Answer

1. **问题识别** (3分)
   - 存在前视偏差（look-ahead bias）
   - `pct_change(20)` 使用了当日收盘价
   - 信号和目标变量有信息重叠

2. **修复方案** (3分)
   ```python
   def compute_momentum_fixed(prices):
       returns = prices.shift(1).pct_change(20)  # 添加 shift(1)
       signal = returns.rank(pct=True)
       return signal
   ```

3. **检测方法** (2分)
   - 计算信号与同期/未来收益的相关性
   - 相关性 > 0.3 说明可能存在泄漏
   - 使用本工具的 `LookaheadDetector`

4. **测试设计** (2分)
   - 单元测试：验证信号只使用历史数据
   - 集成测试：验证 IC < 0.1

### 采分点 / Scoring Rubric

| 要点 | 分值 | 说明 |
|------|------|------|
| 识别前视偏差 | 2分 | 必须明确指出是 look-ahead |
| 解释 pct_change 问题 | 1分 | 理解当日数据不可用 |
| 正确添加 shift(1) | 2分 | 代码正确 |
| 解释修复原理 | 1分 | 知其所以然 |
| 统计检测方法 | 2分 | IC/相关性分析 |
| 测试防护方案 | 2分 | 可操作的建议 |

## 检测器验证 / Detector Validation

```python
from alpha_attribution_clinic.fixtures import generate_aligned_bars
from alpha_attribution_clinic.injectors import LookaheadInjector
from alpha_attribution_clinic.detectors import LookaheadDetector

# 生成数据并注入前视偏差
data = generate_aligned_bars(n_assets=5, n_days=100, seed=42)
injector = LookaheadInjector(lookahead_days=1)
dirty_data = injector.inject(data)

# 检测
detector = LookaheadDetector(correlation_threshold=0.3)
result = detector.detect(dirty_data, signal_col="signal_lookahead")

# 验证检测器工作正常
assert result.detected == True, "Should detect lookahead bias"
assert result.confidence > 0.5, "Should have high confidence"
assert "correlation" in str(result.evidence)
```

## 延伸阅读 / Further Reading

1. Lopez de Prado, M. (2018). *Advances in Financial Machine Learning*. Chapter 7.
2. Bailey, D. et al. (2014). "The Probability of Backtest Overfitting"
3. Harvey, C. et al. (2016). "...and the Cross-Section of Expected Returns"
