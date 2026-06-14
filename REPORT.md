# Repository Evaluation Report

Date: 2026-06-14

Scope: Critical review of the current LaTeX-to-Python web app implementation, including backend, parser, generator, frontend, deployment config, tests, dependency setup, and repository hygiene.

## Executive Summary

The repository has a working FastAPI application with a browser UI, Vercel-oriented deployment config, and a substantial automated test suite. Current verification passes locally:

- `devenv shell pytest -q`: 165 passed, 2 third-party deprecation warnings
- `devenv shell -- python -m black --check .`: passed

The strongest parts are the test coverage around core parser/generator behavior, API smoke coverage, and the explicit ML-expression regression suite. The main weaknesses are security hardening, semantic accuracy boundaries, production readiness, and repository cleanliness.

The highest-priority issue is that user input can flow into `sympy.sympify` in `core/parser.py`. SymPy explicitly treats `sympify` as unsafe for unsanitized input because it can evaluate strings. The API currently exposes this path to unauthenticated users. The second most important issue is that the app can produce syntactically valid Python that is semantically wrong or too symbolic for many real ML formulas, especially optimization objectives, expectations, norms, vector/matrix notation, indexed tensors, and probability/distribution notation.

## Scores

| Area | Rating | Summary |
|---|---:|---|
| Security | 4/10 | Good function-name validation, but unsafe `sympify` exposure, permissive CORS, no input limits, and detailed error messages. |
| Reliability | 6/10 | Tests pass and many cases covered, but parser depends on a stateful third-party parser and broad exception swallowing hides failure modes. |
| Accuracy | 5/10 | Works for many scalar expressions; limited and sometimes misleading for ML notation and advanced LaTeX semantics. |
| Speed | 6/10 | Fine for small expressions; no protection against expensive symbolic parses/evaluations. |
| Efficiency | 6/10 | Small codebase and simple flow; dependency footprint and repeated symbolic processing could be costly in serverless cold starts. |
| Completeness | 5/10 | Functional MVP; not complete for “all LaTeX math” or many ML expressions in `test-strings.md`. |
| Cleanliness | 6/10 | Black-formatted and organized, but generated caches are present after tests, `.gitignore` is incomplete, and docs overstate support. |

## Security Findings

### High: Unsafe `sympy.sympify` on user-controlled input

Location: `core/parser.py:34-45`

`parse_latex` calls `sp.sympify(normalized)` when factorial shorthand is detected and again as a fallback after `latex2sympy` fails. The API passes user input directly into `parse_latex` from `api/routes.py:27`. This is risky because `sympify` is not designed as a safe parser for untrusted input.

Impact:

- Potential code execution or unsafe object construction if a malicious payload reaches `sympify`.
- The public `/api/v1/convert` endpoint can expose this path without authentication.

Recommendation:

- Remove raw `sympify` fallback for API input.
- Use `sympy.parsing.sympy_parser.parse_expr` with a strict local dictionary and disabled builtins if a fallback is needed.
- Keep factorial parsing as a controlled regex-to-AST transformation instead of `sympify("factorial(...)")`.

### High: No request size, complexity, or timeout limits

Location: `api/schemas.py:10`, `api/routes.py:25-45`, `core/parser.py:40-45`, `core/generator.py:67-73`

The input `latex` field has no maximum length, and symbolic parsing/evaluation has no complexity guard. `converted.doit()` in `core/generator.py:67-68` may trigger expensive symbolic evaluation for sums, products, integrals, limits, and derivatives.

Impact:

- Denial-of-service risk from large or adversarial expressions.
- Vercel serverless functions may time out or consume excessive memory.

Recommendation:

- Add `max_length` to `ConvertRequest.latex`.
- Reject overly nested or overly long expressions before parsing.
- Avoid unconditional `.doit()` or apply it only to small, whitelisted expression shapes.
- Add request timeout handling and rate limiting in deployment.

### Medium: CORS allows every origin

Location: `api/main.py:22-27`

`allow_origins=["*"]` allows any website to call the API from a browser.

Impact:

- Untrusted sites can use the public API as a compute endpoint.
- In combination with no rate limiting, this increases abuse risk.

Recommendation:

- Restrict CORS to the deployed frontend origin.
- If the API is intentionally public, add rate limiting and input limits.

### Medium: Detailed internal errors are returned to clients

Location: `api/routes.py:44-45`

Unhandled exceptions are converted into `HTTPException(status_code=400, detail=f"Conversion error: {str(e)}")`.

Impact:

- Internal parser/generator details can leak.
- Error message variability makes client behavior harder to stabilize.

Recommendation:

- Log internal exceptions server-side.
- Return stable public error codes/messages such as `INVALID_LATEX` or `UNSUPPORTED_EXPRESSION`.

### Low: API docs exposed in production

Location: `api/main.py:14-15`

FastAPI docs and ReDoc are enabled. This is acceptable for many public APIs, but should be intentional.

Recommendation:

- Disable docs in production or gate them behind an environment variable.

## Reliability Findings

### Positive: Strong local regression coverage

Locations: `tests/test_converter.py`, `tests/test_ml_expressions.py`

The suite covers parser helpers, generator helpers, API behavior, frontend smoke checks, and ML expression tracking. It currently passes with 165 tests.

### Medium: `latex2sympy2` statefulness and broad exception handling

Location: `core/parser.py:40-46`

Previous work added guards to avoid parser-state poisoning, but the code still catches all exceptions from `latex2sympy`. This prevents crashes but also hides distinct parser bugs, unsupported syntax, and state corruption.

Impact:

- Failures collapse into `None`, making support gaps harder to diagnose.
- New parser regressions may be masked unless tests catch specific cases.

Recommendation:

- Introduce a structured parse result with error type/reason.
- Log parser exceptions with enough context for debugging.
- Consider process isolation or parser reset strategy for hostile inputs.

### Medium: Generated `script` mode is not robust

Location: `core/generator.py:108-137`

`script` mode builds an argparse wrapper and treats all inputs as `float`. This cannot handle sets, matrices, complex values, booleans, symbolic parameters, or vectorized ML inputs.

Impact:

- Script output is only correct for simple scalar numeric functions.

Recommendation:

- Either document script mode as scalar-only or implement type-aware argument handling.
- Consider emitting a function plus example call rather than a CLI for complex expressions.

### Low: Server-relative paths can break under unusual working directories

Location: `api/main.py:18-19`

`Jinja2Templates(directory="templates")` and `StaticFiles(directory="static")` depend on the process working directory.

Recommendation:

- Resolve paths relative to `Path(__file__).parents[1]`.

## Accuracy Findings

### High: Many real ML formulas are not semantically converted

Location: `test-strings.md`, `tests/test_ml_expressions.py`

The ML regression tests explicitly classify many expressions as declarative or symbolic rather than numerically executable. Examples include `argmin`, expectations, KL divergence, distribution notation, matrix norms, indexed tensors, aligned LSTM systems, and update arrows.

Impact:

- The app may claim conversion while producing no output or symbolic fallback for important ML expressions.
- Users may assume generated code calculates the formula when it does not.

Recommendation:

- Add an explicit support level in the API response: `computed`, `symbolic`, `unsupported`, or `ambiguous`.
- Add domain-specific parsers for common ML notation before claiming ML completeness.
- Add examples in the UI showing what is supported and what is symbolic-only.

### High: Unsupported notation currently returns generic parse failure

Observed examples:

- `\arg\min_{x} x^2`
- `\mathbb{E}_{x}[x^2]`
- `\left\|x\right\|_2^2`

Impact:

- Common ML notation is not handled.
- The error message does not tell users whether syntax is invalid or merely unsupported.

Recommendation:

- Add targeted recognition for norms, expectations, argmin/argmax, and update arrows.
- Return `unsupported_feature` with feature names when detected.

### Medium: Some conversions are mathematically approximate or scalarized

Locations: `core/parser.py:105-127`, `core/generator.py:80-95`

Set operations are represented as synthetic SymPy functions and generated as Python set operations. This is useful but does not cover all mathematical set semantics. Matrix notation is emitted as nested lists, which loses linear algebra semantics unless users add their own operations.

Recommendation:

- Document Python semantics for generated set and matrix outputs.
- Consider optional output backends: plain Python, NumPy, SymPy.

### Medium: Variable naming can alter meaning

Location: `core/generator.py:153-159`

LaTeX symbols such as `\hat{y}_i` are sanitized into Python names like `_hat_y__i`. This is necessary for Python validity but can obscure meaning and cause collisions.

Recommendation:

- Return a `symbol_map` in API responses.
- Detect and reject/resolve collisions after sanitization.

## Speed And Efficiency Findings

### Medium: Cold-start and dependency footprint risk on Vercel

Locations: `requirements.txt`, `vercel.json`

FastAPI, SymPy, `latex2sympy2`, ANTLR runtime dependencies, and `uvicorn[standard]` can increase serverless cold-start time. `pytest`, `black`, and `ruff` are included in production requirements.

Impact:

- Larger deployment package and slower cold starts.
- Test/dev-only packages in production.

Recommendation:

- Split production and development requirements.
- Production requirements should exclude `pytest`, `black`, and `ruff`.
- Consider whether `uvicorn[standard]` is needed on Vercel.

### Medium: Repeated parsing and generation with no caching

Location: `api/routes.py:25-42`

Every request reparses and regenerates from scratch.

Recommendation:

- Add a small LRU cache for deterministic conversions if input sizes are bounded.
- Cache only after security limits are in place.

### Low: String-based import detection is brittle

Location: `core/generator.py:140-150`

Imports are added by searching for substrings like `"math."`, `"builtins."`, and `"sp."`.

Impact:

- Works for current outputs but is fragile.

Recommendation:

- Return a structured generation result with `code` and `imports`.

## Completeness Findings

### Positive: MVP scope is mostly implemented

The original task requested:

- LaTeX string input
- Equivalent Python code output
- Python implementation
- Vercel deployment config

All are present at a basic level.

### High: “All possible LaTeX math symbols” is not achievable with current design

LaTeX is a typesetting language, not a single semantic math language. Symbols such as `\mathbb{E}`, `\arg\min`, `\|x\|`, `\sim`, `\leftarrow`, `\odot`, and custom function names require domain interpretation.

Recommendation:

- Define supported grammar and output backend explicitly.
- Add feature-specific parsing incrementally.
- For unsupported symbols, return structured explanations.

### Medium: No NumPy backend

Many ML formulas naturally require vectors, matrices, tensor operations, reductions, and broadcasting. Plain Python output is insufficient for realistic ML calculations.

Recommendation:

- Add output mode `numpy`.
- Map matrix multiplication, dot products, norms, sums, products, sigmoid, softmax, ReLU, and Gaussian likelihoods to NumPy.

## Cleanliness Findings

### Medium: Generated caches are not ignored or cleaned consistently

Observed:

- `.pytest_cache/`
- `__pycache__/` directories appeared after test runs

Location: `.gitignore:1-10`

`.gitignore` currently ignores devenv and direnv files, but not Python caches, pytest caches, virtualenvs, or build artifacts.

Recommendation:

- Add:
  - `__pycache__/`
  - `*.py[cod]`
  - `.pytest_cache/`
  - `.ruff_cache/`
  - `.coverage`
  - `htmlcov/`
  - `.venv/`

### Medium: Dependency pins are loose

Location: `requirements.txt:1-9`

All dependencies use lower bounds only.

Impact:

- Future breaking changes can break builds.
- Reproducibility depends on `devenv.lock` but Vercel install may resolve newer packages.

Recommendation:

- Pin production dependencies or use a lockfile compatible with deployment.
- Separate dev dependencies.

### Medium: Tests include private helper coverage

Location: `tests/test_converter.py`

Testing private helpers increases coverage but can make refactors expensive.

Recommendation:

- Keep a few private-helper tests for security-sensitive transformations.
- Prefer public behavior tests for most generator/parser behavior.

### Low: Documentation overstates planned support

Location: `ARCH.md`, `STACK.md`, `PROGRESS.md`

The docs describe broad support for functions, Greek symbols, sums, products, and special notation. Actual support is partial and dependent on `latex2sympy2`.

Recommendation:

- Add a `SUPPORTED.md` matrix with supported, partial, and unsupported notation.

## Test Evaluation

Strengths:

- 165 tests currently pass.
- Tests cover core parser/generator functions, API endpoints, schema validation, frontend smoke checks, and ML expression tracking.
- ML expressions are explicitly classified, preventing silent omissions.

Limitations:

- Numeric ML tests cover only formulas that are simple scalar expressions after extracting the RHS.
- Many ML expressions are only tracked, not semantically executed.
- No property-based/fuzz tests for parser robustness.
- No load/performance tests.
- No security tests for malicious input payloads.

Recommended additions:

- Fuzz tests with bounded random LaTeX-like strings.
- Regression tests for rejected malicious `sympify` payloads after removing unsafe fallback.
- Performance budget tests for large sums/products/nested fractions.
- Snapshot tests for API error payloads.

## Deployment Evaluation

Strengths:

- `vercel.json` exists and routes requests to `main.py`.
- Static route caching is configured.

Risks:

- Production dependencies include dev tools.
- Serverless cold starts may be high due to SymPy and parser dependencies.
- Docs are exposed by default.
- No environment-specific settings.
- No deployment validation has been recorded.

Recommendations:

- Create `requirements-prod.txt` and `requirements-dev.txt`.
- Add a Vercel smoke checklist or CI workflow.
- Disable docs or make them configurable.
- Add production logging.

## Priority Roadmap

### P0

1. Remove unsafe `sympify` fallback for user input.
2. Add input length and complexity limits.
3. Add structured parse/generation errors.

### P1

1. Split production and development dependencies.
2. Restrict CORS for production.
3. Add `.gitignore` entries for Python caches and test artifacts.
4. Add `symbol_map` to conversion responses.

### P2

1. Add NumPy backend for ML formulas.
2. Add support for norms, expectations, argmin/argmax, update arrows, and common probability notation.
3. Add performance tests and fuzz tests.
4. Add a `SUPPORTED.md` capability matrix.

## Overall Assessment

This is a solid MVP with useful tests and a clear architecture. It is not yet production-hardened and should not be exposed publicly until unsafe parsing, input limits, and dependency separation are addressed. Accuracy is acceptable for basic scalar math and selected symbolic expressions, but incomplete for realistic ML notation. The next major engineering step should be to define a supported grammar and output backend strategy rather than continuing to patch individual LaTeX symbols one by one.
