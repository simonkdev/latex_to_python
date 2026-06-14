# Tech Stack

## Backend
- **Framework**: FastAPI (async, auto docs, production-ready)
- **Runtime**: Python 3.11+

## LaTeX Processing
- **Parsing**: `latex2sympy2` plus guarded custom normalization for selected LaTeX expressions
- **Symbolic Math**: SymPy (for expression manipulation and validation)
- **Code Generation**: Custom logic mapping SymPy/internal expressions → Python, NumPy, or symbolic SymPy output
- **Support Matrix**: See `SUPPORTED.md`; full LaTeX math semantics are not claimed.

## Frontend
- **UI**: Minimal HTML/CSS/JS (server-rendered or static)
- **Components**: Input textarea, output mode/backend selectors, output code block, copy button

## Deployment
- **Platform**: Vercel (Serverless Functions for FastAPI)
- **Adapter**: `vercel-python` or custom `vercel.json`
- **Dependency Mgmt**: devenv via devenv.nix (see https://devenv.sh for syntax and options. If packages are required, use https://search.nixos.org)
- **Production Server**: Vercel provides the ASGI runtime; `uvicorn[standard]` is kept in development dependencies only.
- **Smoke Checks**: See `docs/deployment-smoke.md`.

## DevOps
- **Formatting**: `black`
