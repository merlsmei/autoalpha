# Alpha Code Generation Policy

This document defines the rules and conventions for implementing alpha equations in Java. Each alpha equation (from an `alphaEqN.md` file) must be implemented as a standalone, compilable Java class.

---

## 1. File and Class Structure

- **One class per file.** The file is named `alphaCodeN.java` (lowercase `a`) where `N` matches the equation number.
- **Class name:** `AlphaCodeN` (capital `A`) where `N` matches the equation number.
- **Package:** `package alpha;` — declared at the top of every file.
- **No external libraries.** Only `java.util.*` may be imported. Do not use Apache Commons, Guava, or any other third-party dependency.

---

## 2. Data Model

All data is passed in via an `AlphaDataFrame` object. Assume this interface is available on the classpath:

```java
package alpha;

public interface AlphaDataFrame {
    /** Returns a 2-D array [stockIndex][dayIndex] for the named field. */
    double[][] col(String field);

    /** Total number of stocks in the universe. */
    int numStocks();

    /** Total number of days in the data. */
    int numDays();

    /** Optional: group label per stock for neutralization (e.g. sector id). */
    int[] groups();
}
```

Available field names (matching eqGenPolicy.md): `"open"`, `"high"`, `"low"`, `"close"`, `"volume"`, `"vwap"`, `"returns"`, `"adv20"`.

---

## 3. AlphaStrategy Interface

Every generated class must implement the following interface (assumed available on the classpath):

```java
package alpha;

public interface AlphaStrategy {
    /**
     * Compute the alpha signal for all stocks on the given day.
     *
     * @param df    the data frame providing price/volume series
     * @param today the day index (0-based) for which to compute the signal
     * @return      array of length df.numStocks(); entry i is the signal for stock i.
     *              Use Double.NaN for stocks where the signal cannot be computed.
     */
    double[] compute(AlphaDataFrame df, int today);
}
```

The `compute` method is the **single public entry point**. All operator logic must be implemented as `private static` helper methods inside the class.

---

## 4. Operator Implementation Rules

### 4.1 Arithmetic Operators (element-wise on `double[]`)

| Operator | Java signature |
|----------|---------------|
| `add(a, b)` | `private static double[] add(double[] a, double[] b)` |
| `sub(a, b)` | `private static double[] sub(double[] a, double[] b)` |
| `mul(a, b)` | `private static double[] mul(double[] a, double[] b)` |
| `div(a, b)` | `private static double[] div(double[] a, double[] b)` |
| `neg(a)` | `private static double[] neg(double[] a)` |
| `abs(a)` | `private static double[] abs(double[] a)` |
| `sign(a)` | `private static double[] sign(double[] a)` |
| `log(a)` | `private static double[] log(double[] a)` |
| `pow(a, n)` | `private static double[] pow(double[] a, int n)` |

- Operate element-wise; propagate `Double.NaN` if either operand is `NaN`.
- For `div`: if `|b[i]| < 1e-9`, set result to `Double.NaN`.
- For `log`: if `a[i] <= 0`, set result to `Double.NaN`.

### 4.2 Cross-Sectional Operators (across stocks, for a fixed day)

Input is a `double[]` of length `numStocks` (already extracted for day `today`). Output is also `double[]` of the same length.

| Operator | Java signature |
|----------|---------------|
| `rank(a)` | `private static double[] rank(double[] x)` |
| `zscore(a)` | `private static double[] zscore(double[] x)` |
| `scale(a)` | `private static double[] scale(double[] x)` |
| `neutralize(a, groups)` | `private static double[] neutralize(double[] x, int[] groups)` |

Implementation notes:
- **`rank`**: Assign fractional ranks in [0, 1]. Ties receive the average rank. Skip `NaN` values (they stay `NaN`).
- **`zscore`**: `(x[i] - mean) / (std + 1e-9)`. Compute mean and std over non-NaN values only.
- **`scale`**: `x[i] / sum(|x[j]|)`. If sum is zero, return all zeros.
- **`neutralize`**: For each distinct group label, subtract the group mean from each member. Non-NaN values only.

### 4.3 Time-Series Operators (along the day axis, for a fixed stock)

Input is `double[][] data` (the full `[stockIndex][dayIndex]` array for a field), the current day index `today`, and a window `d`. Output is `double[]` of length `numStocks`.

| Operator | Java signature |
|----------|---------------|
| `ts_mean(a, d)` | `private static double[] tsMean(double[][] data, int today, int d)` |
| `ts_std(a, d)` | `private static double[] tsStd(double[][] data, int today, int d)` |
| `ts_sum(a, d)` | `private static double[] tsSum(double[][] data, int today, int d)` |
| `ts_delta(a, d)` | `private static double[] tsDelta(double[][] data, int today, int d)` |
| `ts_rank(a, d)` | `private static double[] tsRank(double[][] data, int today, int d)` |
| `ts_corr(a, b, d)` | `private static double[] tsCorr(double[][] a, double[][] b, int today, int d)` |
| `ts_cov(a, b, d)` | `private static double[] tsCov(double[][] a, double[][] b, int today, int d)` |
| `ts_decay(a, d)` | `private static double[] tsDecay(double[][] data, int today, int d)` |
| `ts_max(a, d)` | `private static double[] tsMax(double[][] data, int today, int d)` |
| `ts_min(a, d)` | `private static double[] tsMin(double[][] data, int today, int d)` |
| `ts_argmax(a, d)` | `private static double[] tsArgmax(double[][] data, int today, int d)` |
| `ts_argmin(a, d)` | `private static double[] tsArgmin(double[][] data, int today, int d)` |

Implementation notes:
- The window spans days `[today - d + 1, today]` (inclusive). If `today - d + 1 < 0`, return `Double.NaN` for that stock.
- `ts_decay`: weight for day `today - k` (k = 0 is most recent) is `(d - k)`. Normalize by `sum of weights = d*(d+1)/2`.
- `ts_rank`: fraction of the `d-1` prior values (excluding today) that are strictly less than today's value, in `[0, 1]`.
- `ts_corr` / `ts_cov`: standard Pearson formula over the window; return `Double.NaN` if std is zero.

---

## 5. NaN Handling

- **Propagate NaN** through all arithmetic and time-series operations: if any input is `NaN`, the output is `NaN`.
- **Skip NaN** in cross-sectional aggregations (mean, std, rank): compute statistics over non-NaN values; stocks with `NaN` input remain `NaN` in output.
- **Insufficient window**: if `today < d - 1`, the stock has fewer than `d` data points — return `Double.NaN`.

---

## 6. Code Style

1. **Only implement operators that appear in the equation.** Do not add unused helper methods.
2. **Inline field extraction** at the top of `compute`:
   ```java
   double[][] close = df.col("close");
   double[][] volume = df.col("volume");
   // etc.
   ```
3. **No mutation of input arrays.** Always allocate a fresh `double[]` for output.
4. **No magic numbers** other than the window sizes from the equation and the epsilon `1e-9`.
5. **No comments** explaining what Java constructs do. Only add a comment when implementing a non-obvious algorithm step (e.g. the decay weight formula).
6. **Javadoc on `compute` only:** copy the equation string from the `.md` file into the Javadoc `@return` tag.

---

## 7. Output Format

Produce a **complete, compilable `.java` file** with no placeholders, no `// TODO`, and no `// ...`. The file must:
- Start with `package alpha;`
- Import only `java.util.*` (only if actually needed)
- Declare the class as `public class AlphaCodeN implements AlphaStrategy`
- Implement `public double[] compute(AlphaDataFrame df, int today)`
- Declare all helper methods as `private static`

Do not wrap the output in markdown code fences. Output only the raw Java source code.
