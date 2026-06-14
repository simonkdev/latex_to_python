# Supported Notation Matrix

This project converts a practical subset of LaTeX math to Python code. LaTeX is a typesetting language, so some notation requires domain interpretation and is intentionally marked as symbolic or unsupported.

## Supported - Computed Python

| Category | Examples | Notes |
|---|---|---|
| Arithmetic | `x + y`, `x - y`, `x y`, `x / y`, `x^2` | Implicit multiplication is supported for common cases. |
| Fractions | `\frac{x+1}{x-1}` | Emits normal Python division. |
| Roots and powers | `\sqrt{x}`, `x^2` | Uses `math` or backend-specific functions where needed. |
| Trig and elementary functions | `\sin(x)`, `\cos(x)`, `\tan(x)`, `\log(x)`, `e^x` | Python backend uses `math`; NumPy backend uses `np`. |
| Min/max | `\max(0, x)`, `\min(x, y)` | NumPy backend maps to `np.maximum` / `np.minimum`. |
| Sums | `\sum_{i=1}^{n} i^2` | Emits bounded Python generator sums. |
| Products | `\prod_{i=1}^{n} i` | Evaluates when within complexity budget. |
| Definite integrals and limits | `\int_0^1 x^2 dx`, `\lim_{x\to0} ...` | Evaluates only within the symbolic complexity budget. |
| Derivatives | `\frac{d}{dx} x^2` | Evaluates only within the symbolic complexity budget. |
| Relations | `<`, `>`, `\le`, `\leq`, `\ge`, `\geq`, `\ne`, `\neq` | Emits Python comparisons. |
| Matrices | `\begin{bmatrix}...\end{bmatrix}` | Python backend emits nested lists; NumPy backend emits `np.array(...)`. |
| Sets | `\in`, `\notin`, `\subset`, `\subseteq`, `\cup`, `\cap` | Uses Python set/member semantics. |
| Scalar norms | `\left\|x\right\|_2^2` | Python backend handles scalar cases; NumPy backend uses `np.linalg.norm`. |
| Plus/minus | `x \pm y`, `x \mp y` | Emits tuple alternatives. |

## Supported - Symbolic Output

| Category | Examples | Notes |
|---|---|---|
| Expectations | `\mathbb{E}_{x}[x^2]` | Represented as symbolic SymPy fallback. |
| Argmin/argmax | `\arg\min_{x} x^2` | Represented as symbolic SymPy fallback. |
| Unprintable SymPy expressions | unevaluated function derivatives | Emitted as SymPy fallback code. |

## Unsupported With Specific Errors

| Category | Examples | Notes |
|---|---|---|
| Update arrows | `x \leftarrow x + 1` | Reported as `UNSUPPORTED_FEATURE`. |
| Embedded vector norms inside larger formulas | `\exp(-\gamma \|x_i-x_j\|^2)` | Requires deeper LaTeX normalization. |
| Distribution notation | `\mathcal{N}(x|\mu,\Sigma)` | Requires domain-specific probability semantics. |
| Sampling notation | `x \sim p(x)` | Requires statistical interpretation. |
| Hadamard products | `a \odot b` | Not yet mapped to NumPy or symbolic backend. |

## Backends

| Backend | API value | Description |
|---|---|---|
| Plain Python | `python` | Default. Emits standard-library Python where possible. |
| NumPy | `numpy` | Emits `numpy` imports and array/math operations for supported vector/matrix cases. |
| SymPy | `sympy` | Emits symbolic SymPy fallback code. |

The API response includes `support_level`, `backend`, `required_imports`, and `symbol_map` metadata so callers can inspect the assumptions behind generated code.
