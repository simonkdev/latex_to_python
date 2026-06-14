"""Generate executable Python code from SymPy expressions."""

from __future__ import annotations

from dataclasses import dataclass
import keyword
import re
from typing import Literal

import sympy as sp
from sympy.printing.codeprinter import PrintMethodNotImplementedError
from sympy.matrices import MatrixBase
from sympy.printing.pycode import pycode

OutputMode = Literal["expression", "function", "script"]
OutputBackend = Literal["python", "numpy", "sympy"]
MAX_EVALUATION_OPS = 100


@dataclass(frozen=True)
class GeneratedExpression:
    """Generated expression body plus required imports."""

    code: str
    imports: tuple[str, ...] = ()


class GenerationError(ValueError):
    """Structured error raised when Python generation cannot proceed safely."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def generate_python(
    expr: sp.Expr,
    mode: OutputMode = "function",
    backend: OutputBackend = "python",
    func_name: str = "f",
    var_names: dict[str, str] | None = None,
) -> str:
    """Generate Python code for a SymPy expression."""
    if not _is_identifier(func_name):
        raise GenerationError(
            "INVALID_FUNCTION_NAME",
            "Function name must be a valid Python identifier.",
        )

    variables = _ordered_variables(expr)
    python_names = build_symbol_map(expr, var_names)
    expression = _expression_to_fragment(expr, python_names, backend)

    if mode == "expression":
        return _with_imports(expression.code, expression.imports)

    if mode == "function":
        function_code = _function_code(
            func_name, variables, python_names, expression.code
        )
        return _with_imports(function_code, expression.imports)

    if mode == "script":
        script_code = _script_code(func_name, variables, python_names, expression.code)
        return _with_imports(script_code, expression.imports)

    raise ValueError(f"Unknown mode: {mode}")


def _expression_to_fragment(
    expr: sp.Expr, python_names: dict[str, str], backend: OutputBackend
) -> GeneratedExpression:
    if backend == "python":
        return _sympy_to_python_fragment(expr, python_names)
    if backend == "numpy":
        return _sympy_to_numpy_fragment(expr, python_names)
    if backend == "sympy":
        renamed = expr.xreplace(
            {
                symbol: sp.Symbol(python_names[str(symbol)])
                for symbol in expr.free_symbols
            }
        )
        return GeneratedExpression(
            code=f"sp.sympify({str(renamed)!r})",
            imports=("import sympy as sp",),
        )
    raise GenerationError("INVALID_BACKEND", "Unknown output backend.")


def _sympy_to_python(expr: sp.Expr, python_names: dict[str, str]) -> str:
    return _sympy_to_python_fragment(expr, python_names).code


def _sympy_to_python_fragment(
    expr: sp.Expr, python_names: dict[str, str]
) -> GeneratedExpression:
    replacements = {
        symbol: sp.Symbol(python_names[str(symbol)]) for symbol in expr.free_symbols
    }
    converted = expr.xreplace(replacements)

    if isinstance(converted, MatrixBase):
        row_codes = []
        imports = set()
        for row in converted.tolist():
            cells = [_sympy_to_python_fragment(cell, python_names) for cell in row]
            imports.update(import_ for cell in cells for import_ in cell.imports)
            row_codes.append("[" + ", ".join(cell.code for cell in cells) + "]")
        return GeneratedExpression(
            "[" + ", ".join(row_codes) + "]", tuple(sorted(imports))
        )

    special_operation = _special_operation_to_python(converted, python_names)
    if special_operation is not None:
        imports = ("import sympy as sp",) if special_operation.startswith("sp.") else ()
        return GeneratedExpression(special_operation, imports)

    if converted.has(sp.Product, sp.Integral, sp.Limit, sp.Derivative):
        converted = _safe_doit(converted)

    try:
        return GeneratedExpression(pycode(converted), _imports_for_pycode(converted))
    except (PrintMethodNotImplementedError, ValueError):
        return GeneratedExpression(
            f"sp.sympify({str(converted)!r})",
            ("import sympy as sp",),
        )


def _sympy_to_numpy(expr: sp.Expr, python_names: dict[str, str]) -> str:
    return _sympy_to_numpy_fragment(expr, python_names).code


def _sympy_to_numpy_fragment(
    expr: sp.Expr, python_names: dict[str, str]
) -> GeneratedExpression:
    replacements = {
        symbol: sp.Symbol(python_names[str(symbol)]) for symbol in expr.free_symbols
    }
    converted = expr.xreplace(replacements)

    if isinstance(converted, MatrixBase):
        rows = [
            "["
            + ", ".join(
                _sympy_to_numpy_fragment(cell, python_names).code for cell in row
            )
            + "]"
            for row in converted.tolist()
        ]
        return GeneratedExpression(
            "np.array([" + ", ".join(rows) + "])",
            ("import numpy as np",),
        )

    special_operation = _special_operation_to_numpy(converted, python_names)
    if special_operation is not None:
        imports = []
        if "np." in special_operation:
            imports.append("import numpy as np")
        if "sp." in special_operation:
            imports.append("import sympy as sp")
        return GeneratedExpression(special_operation, tuple(imports))

    python_fragment = _sympy_to_python_fragment(expr, python_names)
    body = (
        python_fragment.code.replace("math.", "np.")
        .replace("builtins.sum", "sum")
        .replace("max(", "np.maximum(")
        .replace("min(", "np.minimum(")
    )
    imports = {"import numpy as np"}
    imports.update(
        import_
        for import_ in python_fragment.imports
        if import_ == "import sympy as sp"
    )
    return GeneratedExpression(body, tuple(sorted(imports)))


def _imports_for_pycode(expr: sp.Expr) -> tuple[str, ...]:
    imports = set()
    if expr.has(sp.Sum):
        imports.add("import builtins")
    math_objects = (
        sp.Abs,
        sp.acos,
        sp.asin,
        sp.atan,
        sp.ceiling,
        sp.cos,
        sp.cosh,
        sp.cot,
        sp.csc,
        sp.E,
        sp.erf,
        sp.exp,
        sp.factorial,
        sp.floor,
        sp.gamma,
        sp.log,
        sp.pi,
        sp.sec,
        sp.sin,
        sp.sinh,
        sp.sqrt,
        sp.tan,
        sp.tanh,
    )
    if any(expr.has(item) for item in math_objects) or expr in {sp.E, sp.pi}:
        imports.add("import math")
    return tuple(sorted(imports))


def _ordered_variables(expr: sp.Expr) -> list[sp.Symbol]:
    return sorted(expr.free_symbols, key=lambda symbol: str(symbol))


def build_symbol_map(
    expr: sp.Expr, var_names: dict[str, str] | None = None
) -> dict[str, str]:
    """Map source symbol names to safe Python identifiers."""
    variables = _ordered_variables(expr)
    python_names = {
        str(symbol): _safe_name(
            var_names.get(str(symbol), str(symbol)) if var_names else str(symbol)
        )
        for symbol in variables
    }
    if len(set(python_names.values())) != len(python_names):
        raise GenerationError(
            "VARIABLE_NAME_COLLISION",
            "Multiple symbols resolve to the same Python identifier.",
        )
    return python_names


def _safe_doit(expr: sp.Expr) -> sp.Expr:
    """Evaluate symbolic constructs only when expression complexity is bounded."""
    if sp.count_ops(expr) > MAX_EVALUATION_OPS:
        raise GenerationError(
            "EXPRESSION_TOO_COMPLEX",
            f"Expression exceeds the symbolic evaluation budget of {MAX_EVALUATION_OPS} operations.",
        )
    return expr.doit()


def _special_operation_to_python(
    expr: sp.Expr, python_names: dict[str, str]
) -> str | None:
    if not expr.is_Function or len(expr.args) != 2:
        if (
            expr.is_Function
            and str(expr.func) == "__latex_norm"
            and len(expr.args) == 3
        ):
            inner = _sympy_to_python(expr.args[0], python_names)
            order = expr.args[1]
            power = expr.args[2]
            if order == 2 and power == 2:
                return f"({inner})**2"
            if order in {1, 2} and power == 1:
                return f"abs({inner})"
        return None

    operation = str(expr.func)
    left = _sympy_to_python(expr.args[0], python_names)
    right = _sympy_to_python(expr.args[1], python_names)
    operation_map = {
        "__latex_in": f"{left} in {right}",
        "__latex_notin": f"{left} not in {right}",
        "__latex_subset": f"{left} < {right}",
        "__latex_subseteq": f"{left} <= {right}",
        "__latex_union": f"{left} | {right}",
        "__latex_intersection": f"{left} & {right}",
        "__latex_expectation": f"sp.sympify({str(expr)!r})",
        "__latex_argmin": f"sp.sympify({str(expr)!r})",
        "__latex_argmax": f"sp.sympify({str(expr)!r})",
    }
    return operation_map.get(operation)


def _special_operation_to_numpy(
    expr: sp.Expr, python_names: dict[str, str]
) -> str | None:
    if expr.is_Function and str(expr.func) == "__latex_norm" and len(expr.args) == 3:
        inner = _sympy_to_numpy(expr.args[0], python_names)
        order = expr.args[1]
        power = expr.args[2]
        code = f"np.linalg.norm({inner}, ord={int(order)})"
        if power != 1:
            code = f"({code})**{int(power)}"
        return code
    return _special_operation_to_python(expr, python_names)


def _function_code(
    func_name: str,
    variables: list[sp.Symbol],
    python_names: dict[str, str],
    python_expr: str,
) -> str:
    params = ", ".join(python_names[str(symbol)] for symbol in variables)
    return f"def {func_name}({params}):\n    return {python_expr}"


def _script_code(
    func_name: str,
    variables: list[sp.Symbol],
    python_names: dict[str, str],
    python_expr: str,
) -> str:
    function_code = _function_code(func_name, variables, python_names, python_expr)
    lines = [
        function_code,
        "",
        "",
        'if __name__ == "__main__":',
        "    import argparse",
        "",
        "    parser = argparse.ArgumentParser()",
    ]

    for symbol in variables:
        name = python_names[str(symbol)]
        lines.append(f'    parser.add_argument("{name}", type=float)')

    lines.extend(
        [
            "    args = parser.parse_args()",
            f"    print({func_name}("
            + ", ".join(f"args.{python_names[str(symbol)]}" for symbol in variables)
            + "))",
        ]
    )
    return "\n".join(lines)


def _with_imports(code: str, imports: tuple[str, ...] | None = None) -> str:
    if imports is None:
        imports = tuple(
            import_
            for token, import_ in (
                ("builtins.", "import builtins"),
                ("math.", "import math"),
                ("np.", "import numpy as np"),
                ("sp.", "import sympy as sp"),
            )
            if token in code
        )
    if imports:
        return "\n".join(imports) + f"\n\n{code}"
    return code


def _safe_name(name: str) -> str:
    safe = re.sub(r"\W", "_", name)
    if not safe or safe[0].isdigit():
        safe = f"v_{safe}"
    if not _is_identifier(safe):
        safe = f"v_{safe}"
    return safe


def _is_identifier(name: str) -> bool:
    return name.isidentifier() and not keyword.iskeyword(name)
