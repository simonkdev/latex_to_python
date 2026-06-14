# Architecture

## Overview
```
LaTeX Input → Parser → AST → Python Generator → Python Output
```

## Components

### 1. API Layer (FastAPI)
- **Endpoint**: `POST /convert`
- **Input**: `{"latex": "\frac{x+1}{x-1}"}`
- **Output**: `{"python": "def f(x): return (x + 1) / (x - 1)"}`

### 2. Parser
- Converts supported LaTeX string → SymPy expression or internal symbolic node
- Applies input length/complexity guards before parsing
- Returns structured errors for invalid, unsafe, too-complex, or unsupported notation
- See `SUPPORTED.md` for current support boundaries

### 3. Python Generator
- Walks AST → generates Python code
- Output modes:
  - Expression (returns value)
  - Function (def f(...): ...)
  - Script (full runnable)
- Backends:
  - Plain Python
  - NumPy
  - SymPy symbolic fallback

### 4. Frontend
- Single page with:
  - LaTeX input (textarea)
  - Mode selector (expression/function/script)
  - Backend selector (Python/NumPy/SymPy)
  - Convert button
  - Python output (code block with copy)

## File Structure
```
project/
├── api/
│   ├── main.py          # FastAPI app
│   ├── routes.py        # Endpoints
│   └── schemas.py       # Pydantic models
├── core/
│   ├── parser.py        # LaTeX → AST
│   ├── generator.py     # AST → Python
│   └── utils.py         # Helpers
├── static/              # Frontend assets
├── templates/           # HTML templates
├── tests/
└── vercel.json          # Deployment config
```
