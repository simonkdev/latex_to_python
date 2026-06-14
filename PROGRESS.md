# Progress Tracker

## Phase 1: Planning (2026-06-14)
- [x] Create STACK.md
- [x] Create ARCH.md
- [x] Create AGENTS.md
- [x] Create PROGRESS.md

## Phase 2: Implementation (Complete Locally)
- [x] Setup Python project structure
- [x] Implement LaTeX parser
- [x] Implement Python generator
- [x] Create FastAPI endpoints
- [x] Build frontend
- [x] Configure Vercel deployment
- [x] Test end-to-end locally

## Phase 3: Deployment (Pending)
- [ ] Deploy to Vercel
- [ ] Validate production behavior

## Latest Update (2026-06-14)
- Fixed devenv setup by using a Python virtualenv backed by `requirements.txt` for pip-only dependencies.
- Replaced fragile custom Python generation with SymPy `pycode` output plus expression/function/script wrappers.
- Served the frontend from FastAPI at `/` and fixed browser JavaScript syntax.
- Added API and frontend smoke tests.
- Verified locally with `devenv shell pytest -q` and `devenv shell -- python -m black --check .`.

## Automated Testing Update (2026-06-14)
- Expanded automated tests to cover every local Python module and function, including private parser/generator helpers.
- Added representative LaTeX coverage for arithmetic, powers, fractions, roots, functions, Greek symbols, sums, products, integrals, limits, relations, matrices, determinants, and a quadratic-formula fragment.
- Added API route, schema validation, OpenAPI, static asset, and frontend smoke coverage.
- Improved generator support for matrices, products, integrals, limits, and generated `builtins` imports uncovered by the tests.
- Verified locally with `devenv shell pytest -q`: 87 passed.

## Broad Symbol Support Update (2026-06-14)
- Added parser normalization for relation aliases (`\leq`, `\geq`, `\ne`) and simple factorial shorthand (`n!`).
- Added plus/minus and minus/plus alternatives (`\pm`, `\mp`) as tuple outputs.
- Added common set and membership operators: `\in`, `\notin`, `\subset`, `\subseteq`, `\cup`, and `\cap`.
- Added generator support for evaluated derivatives and symbolic SymPy fallbacks for expressions that cannot be emitted as plain numeric Python.
- Expanded regression tests to 113 passing tests.

## ML Expression Regression Update (2026-06-14)
- Added `tests/test_ml_expressions.py` to load all 50 expressions from `test-strings.md`.
- Added numeric calculation checks for directly executable ML formulas, including sigmoid, ReLU, tanh, MSE, polynomial kernel, PCA projection, Gini impurity, entropy, and Gaussian likelihood.
- Classified every non-scalar/declarative ML expression with a tracked reason so future parser support can promote them into numeric cases intentionally.
- Verified locally with `devenv shell pytest -q`: 165 passed.

## Remediation Update (2026-06-14)
- Completed P0 security hardening from `TODO.md`: removed raw parser `sympify`, added malicious-input regression tests, request length validation, complexity guards, bounded symbolic evaluation, structured parse/generation errors, and stable public error codes.
- Completed P1 production hardening from `TODO.md`: configurable CORS/docs, project-root asset paths, split and pinned production/dev dependencies, Python cache ignores, symbol maps, collision detection, support-level metadata, and logging.
- Completed several P2 accuracy tasks: targeted unsupported ML notation detection, scalar/vector norm handling, symbolic expectation and argmin/argmax handling, update-arrow unsupported responses, NumPy backend, backend metadata, set/matrix semantics documentation, `SUPPORTED.md`, and aligned planning docs.

## Remediation Completion Update (2026-06-14)
- Completed the remaining P2 generator cleanup by moving import requirements into structured generation fragments instead of relying on generated-code substring scans.
- Added bounded fuzz tests, parser performance budget tests, API error payload snapshot tests, and an LRU cache for deterministic conversion responses.
- Fixed a parser reliability issue where malformed unbalanced delimiters could poison later `latex2sympy2` parses.
- Rebalanced tests away from nonessential private generator helpers while keeping safety-boundary helper coverage.
- Added `docs/deployment-smoke.md` and documented the production decision to keep `uvicorn[standard]` out of Vercel dependencies.
