# Alpha Equation Generation Policy

This document defines the rules and constraints for generating alpha equations. An **alpha** is a real-valued expression that produces one scalar signal per stock per day. Higher values indicate stronger long preference; lower (more negative) values indicate stronger short preference.

---

## 1. Allowed Data Fields

These are the only raw inputs permitted in any alpha expression:

| Field     | Description                                      |
|-----------|--------------------------------------------------|
| `open`    | Daily opening price                              |
| `high`    | Daily high price                                 |
| `low`     | Daily low price                                  |
| `close`   | Daily closing price                              |
| `volume`  | Daily traded volume (shares)                     |
| `vwap`    | Volume-weighted average price                    |
| `returns` | Daily log return: `log(close / close[-1])`       |
| `adv20`   | 20-day average daily dollar volume               |

---

## 2. Allowed Operators

### 2.1 Arithmetic Operators
Standard element-wise operations on vectors (one value per stock per day):

- `add(a, b)` — addition
- `sub(a, b)` — subtraction
- `mul(a, b)` — multiplication
- `div(a, b)` — division (denominator must not be identically zero)
- `neg(a)` — negation
- `abs(a)` — absolute value
- `sign(a)` — sign: returns -1, 0, or 1
- `log(a)` — natural logarithm (argument must be strictly positive)
- `pow(a, n)` — raise `a` to constant integer power `n` (2 or 3 only)

### 2.2 Cross-Sectional Operators
Applied across all stocks on a given day (output is cross-sectionally standardized):

- `rank(a)` — cross-sectional rank, scaled to [0, 1]
- `zscore(a)` — cross-sectional z-score: `(a - mean(a)) / std(a)`
- `neutralize(a, group)` — demean `a` within each `group` (e.g. sector, industry)
- `scale(a)` — rescale so that `sum(abs(a)) = 1`

### 2.3 Time-Series Operators
Applied along the time axis for each stock. The lookback window `d` must be a positive integer between **2 and 60** (inclusive):

- `ts_mean(a, d)` — rolling mean over past `d` days
- `ts_std(a, d)` — rolling standard deviation over past `d` days
- `ts_sum(a, d)` — rolling sum over past `d` days
- `ts_delta(a, d)` — difference: `a - a[d]` (change over `d` days)
- `ts_rank(a, d)` — rank of today's value within the past `d` days, scaled to [0, 1]
- `ts_corr(a, b, d)` — rolling Pearson correlation between `a` and `b` over `d` days
- `ts_cov(a, b, d)` — rolling covariance between `a` and `b` over `d` days
- `ts_decay(a, d)` — linearly-weighted decay sum over `d` days (recent = higher weight)
- `ts_max(a, d)` — rolling maximum over `d` days
- `ts_min(a, d)` — rolling minimum over `d` days
- `ts_argmax(a, d)` — day index (0-based from oldest) of maximum within window
- `ts_argmin(a, d)` — day index (0-based from oldest) of minimum within window

---

## 3. Structural Rules

1. **Output type**: The top-level expression must produce a real-valued scalar for every stock on every day (a cross-sectional vector).
2. **Nesting depth**: Maximum nesting depth is **5 levels**. Deeply nested expressions are harder to interpret and prone to overfitting.
3. **Window sizes**: All time-series lookback windows `d` must be integers in `[2, 60]`. Do not use windows of 1 (no-op) or greater than 60 (too sparse for daily data).
4. **No raw constants as top-level output**: The alpha cannot be a constant value (every stock would get the same signal).
5. **Division safety**: Whenever a division is used, the denominator must be a quantity that is non-zero by construction (e.g. use `ts_std` only when variance is expected to be non-zero; add a small epsilon comment if needed).
6. **Logarithm safety**: `log(a)` is only valid when `a` is guaranteed positive (e.g. `close`, `volume`, `adv20`). Do not apply `log` to `returns` or price differences without an `abs`.
7. **No lookahead bias**: Every operator uses only current and past data. Future prices or future returns are strictly forbidden.

---

## 4. Style Guidelines

1. **Economic interpretability**: Prefer alphas with a clear economic or behavioral rationale (e.g. momentum, mean-reversion, liquidity, volatility). State the rationale in one sentence.
2. **Avoid redundancy**: Do not apply `rank` twice on the same sub-expression without a meaningful transformation in between.
3. **Cross-sectional normalization**: The final output should ideally be cross-sectionally normalized (e.g. wrapped in `rank(...)` or `zscore(...)`) so that it is comparable across different market regimes.
4. **Complexity balance**: Prefer concise expressions. Aim for 2–4 operator levels. More complexity must be justified by the alpha hypothesis.
5. **Diversity**: Each generated alpha should represent a distinct signal type. Do not generate near-duplicate formulations of the same idea.

---

## 5. Output Format

When generating an alpha equation, produce:

1. **Equation** (required): A single-line expression using only the operators and fields defined above. Example:
   ```
   rank(ts_delta(close, 5))
   ```

2. **Rationale** (required): One to three sentences explaining the economic intuition behind the alpha.

3. **Signal type** (required): One of — `momentum`, `mean-reversion`, `liquidity`, `volatility`, `value`, `quality`, `other`.

4. **Lookback horizon** (required): Approximate horizon in days that the alpha captures (e.g. `5`, `20`, `60`).

---

## 6. Prohibited Patterns

- Do not use any operator or field not listed in sections 1–2.
- Do not embed raw numeric literals other than window sizes and the exponent in `pow`.
- Do not produce an alpha that is constant across all stocks on any given day.
- Do not use future data (no forward-looking constructs).
- Do not reference external datasets beyond the eight fields in section 1.
