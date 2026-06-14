# Remediation To-Do List

Generated from `REPORT.md` on 2026-06-14.

## P0 - Must Fix Before Public Exposure

- [x] Remove unsafe `sympy.sympify` fallback from user input parsing.
  - Source: `REPORT.md` security finding “Unsafe sympy.sympify on user-controlled input”.
  - Target: `core/parser.py`.
  - Acceptance: no API-controlled string reaches raw `sp.sympify`; factorial handling uses controlled AST construction or a strict parser.

- [x] Add regression tests proving malicious parser payloads are rejected.
  - Source: `REPORT.md` test recommendation for malicious `sympify` payloads.
  - Target: `tests/`.
  - Acceptance: tests cover representative unsafe strings and assert stable rejection without execution.

- [x] Add maximum length validation for `ConvertRequest.latex`.
  - Source: `REPORT.md` security finding “No request size, complexity, or timeout limits”.
  - Target: `api/schemas.py`.
  - Acceptance: oversized LaTeX payloads return validation errors before parsing.

- [x] Add parser complexity limits.
  - Source: `REPORT.md` security finding “No request size, complexity, or timeout limits”.
  - Target: `core/parser.py`.
  - Acceptance: overly nested braces, repeated operators, or excessive command counts are rejected before `latex2sympy2`.

- [x] Restrict expensive symbolic evaluation.
  - Source: `REPORT.md` security/speed finding about unconditional `.doit()`.
  - Target: `core/generator.py`.
  - Acceptance: `.doit()` is applied only to whitelisted small expressions or guarded by a complexity budget.

- [x] Add structured parse and generation errors.
  - Source: `REPORT.md` reliability finding about failures collapsing into `None`.
  - Target: `core/parser.py`, `core/generator.py`, `api/routes.py`, `api/schemas.py`.
  - Acceptance: API can distinguish invalid syntax, unsupported notation, unsafe input, and generation failure.

- [x] Replace client-facing internal exception text with stable error codes.
  - Source: `REPORT.md` security finding “Detailed internal errors are returned to clients”.
  - Target: `api/routes.py`.
  - Acceptance: public responses expose stable messages/codes; internal exception details are logged only server-side.

## P1 - Production Hardening

- [x] Restrict production CORS.
  - Source: `REPORT.md` security finding “CORS allows every origin”.
  - Target: `api/main.py`.
  - Acceptance: allowed origins are configured by environment and no longer default to `["*"]` in production.

- [x] Gate FastAPI docs behind an environment setting.
  - Source: `REPORT.md` security finding “API docs exposed in production”.
  - Target: `api/main.py`.
  - Acceptance: `/docs` and `/redoc` can be disabled in production.

- [x] Resolve template and static paths relative to the project root.
  - Source: `REPORT.md` reliability finding “Server-relative paths can break”.
  - Target: `api/main.py`.
  - Acceptance: app can start correctly from a different working directory.

- [x] Split production and development dependencies.
  - Source: `REPORT.md` speed/cleanliness findings about dependency footprint and dev tools in production.
  - Target: `requirements.txt`, new `requirements-prod.txt`, new `requirements-dev.txt`, `devenv.nix`, `vercel.json` if needed.
  - Acceptance: production dependency file excludes `pytest`, `black`, and `ruff`.

- [x] Pin production dependency versions.
  - Source: `REPORT.md` cleanliness finding “Dependency pins are loose”.
  - Target: production requirements or deployment lockfile.
  - Acceptance: Vercel deploys from reproducible versions rather than lower-bound ranges.

- [x] Add Python/test/build artifacts to `.gitignore`.
  - Source: `REPORT.md` cleanliness finding “Generated caches are not ignored”.
  - Target: `.gitignore`.
  - Acceptance: ignores `__pycache__/`, `*.py[cod]`, `.pytest_cache/`, `.ruff_cache/`, `.coverage`, `htmlcov/`, and `.venv/`.

- [x] Add `symbol_map` to conversion responses.
  - Source: `REPORT.md` accuracy finding “Variable naming can alter meaning”.
  - Target: `api/schemas.py`, `api/routes.py`, `core/generator.py`.
  - Acceptance: API returns original symbol names mapped to sanitized Python identifiers.

- [x] Detect sanitized variable-name collisions.
  - Source: `REPORT.md` accuracy finding “Variable naming can alter meaning”.
  - Target: `core/generator.py`.
  - Acceptance: collisions are rejected or resolved deterministically and covered by tests.

- [x] Add a conversion support-level field.
  - Source: `REPORT.md` accuracy finding “Many real ML formulas are not semantically converted”.
  - Target: `api/schemas.py`, `api/routes.py`, parser/generator result model.
  - Acceptance: response indicates `computed`, `symbolic`, `unsupported`, or `ambiguous`.

- [x] Add production logging for parser/generator failures.
  - Source: `REPORT.md` security/reliability/deployment recommendations.
  - Target: `api/routes.py`, app config.
  - Acceptance: internal errors are logged with enough context while public responses remain stable.

## P2 - Accuracy And Feature Completeness

- [x] Add targeted detection for unsupported ML notation.
  - Source: `REPORT.md` accuracy finding “Unsupported notation currently returns generic parse failure”.
  - Target: `core/parser.py`.
  - Acceptance: detects norms, expectations, argmin/argmax, update arrows, probability notation, and reports feature-specific unsupported errors.

- [x] Implement norm notation support.
  - Source: `REPORT.md` accuracy finding examples such as `\left\|x\right\|_2^2`.
  - Target: parser/generator.
  - Acceptance: common `L1`, `L2`, squared `L2`, and absolute-value norms convert correctly for the selected backend.

- [x] Implement expectation notation support.
  - Source: `REPORT.md` completeness/accuracy findings for `\mathbb{E}`.
  - Target: parser/generator.
  - Acceptance: expectations are represented symbolically or converted for supported discrete cases.

- [x] Implement argmin/argmax notation support.
  - Source: `REPORT.md` completeness/accuracy findings for `\arg\min` and `\arg\max`.
  - Target: parser/generator.
  - Acceptance: output clearly represents optimization calls or structured symbolic objects rather than parse failure.

- [x] Implement update-arrow notation support.
  - Source: `REPORT.md` completeness findings for `\leftarrow`.
  - Target: parser/generator/API.
  - Acceptance: update equations produce assignment-style script output or structured unsupported responses.

- [x] Add optional NumPy backend.
  - Source: `REPORT.md` completeness finding “No NumPy backend”.
  - Target: `core/generator.py`, API schemas, frontend mode selector, tests.
  - Acceptance: output mode `numpy` supports matrices, vectors, dot products, norms, reductions, sigmoid, softmax, ReLU, and Gaussian likelihoods.

- [x] Add backend-specific output metadata.
  - Source: `REPORT.md` recommendation for plain Python, NumPy, and SymPy backends.
  - Target: API response model.
  - Acceptance: responses identify required imports and backend assumptions.

- [x] Replace string-based import detection with structured generation results.
  - Source: `REPORT.md` speed/efficiency finding “String-based import detection is brittle”.
  - Target: `core/generator.py`.
  - Acceptance: generator returns `code` plus explicit `imports`, and tests no longer depend on substring-driven import inference.

- [x] Document set and matrix output semantics.
  - Source: `REPORT.md` accuracy finding “Some conversions are mathematically approximate or scalarized”.
  - Target: docs and possibly frontend help text.
  - Acceptance: users can see that sets use Python set semantics and matrices currently emit nested lists unless another backend is selected.

- [x] Add a `SUPPORTED.md` capability matrix.
  - Source: `REPORT.md` cleanliness/completeness recommendation.
  - Target: new documentation file.
  - Acceptance: notation is grouped as supported, partially supported, symbolic-only, or unsupported.

- [x] Update `ARCH.md`, `STACK.md`, and `PROGRESS.md` to avoid overstating support.
  - Source: `REPORT.md` cleanliness finding “Documentation overstates planned support”.
  - Target: documentation files.
  - Acceptance: docs align with actual supported features and documented limitations.

## P3 - Testing, Performance, And Developer Experience

- [x] Add bounded fuzz tests for parser robustness.
  - Source: `REPORT.md` test recommendation.
  - Target: `tests/`.
  - Acceptance: randomized LaTeX-like inputs do not crash the API or poison later parses.

- [x] Add performance budget tests.
  - Source: `REPORT.md` test recommendation and speed findings.
  - Target: `tests/`.
  - Acceptance: large sums/products/nested fractions complete or reject within defined thresholds.

- [x] Add API error snapshot tests.
  - Source: `REPORT.md` test recommendation.
  - Target: `tests/`.
  - Acceptance: public error payloads remain stable.

- [x] Add a small LRU cache for deterministic conversions.
  - Source: `REPORT.md` speed/efficiency finding “Repeated parsing and generation with no caching”.
  - Target: API or core conversion layer.
  - Acceptance: identical safe inputs can be served from cache; cache is bounded and tested.

- [x] Rebalance tests away from private helpers where practical.
  - Source: `REPORT.md` cleanliness finding “Tests include private helper coverage”.
  - Target: `tests/test_converter.py`.
  - Acceptance: private-helper tests remain only for security-sensitive transformations; most behavior is tested through public APIs.

- [x] Add deployment smoke checklist or CI workflow.
  - Source: `REPORT.md` deployment recommendations.
  - Target: docs or CI config.
  - Acceptance: deployment validation steps cover `/`, `/health`, `/api/v1/convert`, static assets, and docs behavior.

- [x] Decide whether `uvicorn[standard]` is needed in production.
  - Source: `REPORT.md` speed/deployment recommendation.
  - Target: production requirements.
  - Acceptance: production dependencies include only runtime packages needed by Vercel.
