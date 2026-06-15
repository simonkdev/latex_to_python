# LaTeX to Python

A web app that converts **LaTeX mathematical expressions** to **executable Python code**. Try it live at [https://dothefancymathforme.vercel.app/](https://dothefancymathforme.vercel.app/)

---

## 📌 About

This tool bridges the gap between mathematical notation and Python code. It parses LaTeX expressions and generates equivalent Python code with support for multiple backends (plain Python, NumPy, SymPy).

*This project was vibecoded. More information can be found in the repository description.*

---
## ✨ Features

Supports a wide range of mathematical notation including arithmetic, fractions, roots, trigonometry, calculus, matrices, sets, and norms. For a full list of supported notation, see [SUPPORTED.md](SUPPORTED.md).

---
## 🚀 Usage

### Web Interface
1. Go to [https://dothefancymathforme.vercel.app/](https://dothefancymathforme.vercel.app/)
2. Enter your LaTeX expression
3. Select output mode and backend
4. Click **Convert**
5. Copy the generated Python code

### API
**Endpoint**: `POST /api/v1/convert`

**Request**:
```json
{
  "latex": "\frac{x+1}{x-1}",
  "mode": "function",
  "backend": "python"
}
```

**Response**:
```json
{
  "python": "def f(x): return (x + 1) / (x - 1)",
  "support_level": "computed",
  "backend": "python",
  "required_imports": [],
  "symbol_map": {"x": "x"}
}
```

---
## 💻 Development

### Prerequisites
- Python 3.11+
- [Devenv](https://devenv.sh/) (recommended)

### Setup
```sh
git clone https://github.com/simonkdev/latex_to_python
cd latex_to_python
devenv shell
```

### Running Locally
```sh
python run_app.py
```
The app will be available at `http://localhost:8000`.

### Testing
```sh
pytest
```

---
## ✨ Contributing

We welcome contributions!

### How to Contribute
1. Fork the repository
2. Create a branch (`git checkout -b feature/your-feature`)
3. Make your changes
4. Add tests (if applicable)
5. Run tests (`pytest`)
6. Submit a Pull Request

---
## 📜 License

This project is licensed under the **MIT License**.

Copyright (c) 2026 Simon Korten
```
