"""Automated tests for the LaTeX to Python translator."""

from __future__ import annotations

import math
import random
import string
import time

import numpy as np
import pytest
import sympy as sp
from fastapi.testclient import TestClient
from pydantic import ValidationError

import main as cli_main
import run_app
from api.main import app
from api.routes import _convert_cached, convert_latex
from api.schemas import ConvertRequest, ConvertResponse
from core import generator
from core.generator import generate_python
from core.parser import parse_latex_detailed, get_variables, parse_latex

client = TestClient(app)


def eval_expression_code(code: str, **values):
    """Evaluate generated expression-mode code with optional imports."""
    lines = [line for line in code.splitlines() if line.strip()]
    namespace = dict(values)
    exec("\n".join(lines[:-1] + [f"_result = {lines[-1]}"]), namespace)
    return namespace["_result"]


class TestParserModule:
    """Tests for every parser module function."""

    @pytest.mark.parametrize(
        ("latex", "expected"),
        [
            (r"x + y", sp.Symbol("x") + sp.Symbol("y")),
            (r"x - y", sp.Symbol("x") - sp.Symbol("y")),
            (r"x y", sp.Symbol("x") * sp.Symbol("y")),
            (r"\frac{x+1}{x-1}", (sp.Symbol("x") + 1) / (sp.Symbol("x") - 1)),
            (r"x^2 + y^3", sp.Symbol("x") ** 2 + sp.Symbol("y") ** 3),
            (r"\sqrt{x^2 + y^2}", sp.sqrt(sp.Symbol("x") ** 2 + sp.Symbol("y") ** 2)),
        ],
    )
    def test_parse_latex_arithmetic(self, latex, expected):
        result = parse_latex(latex)
        assert result is not None
        assert sp.simplify(result - expected) == 0

    @pytest.mark.parametrize(
        ("latex", "expected_functions"),
        [
            (r"\sin(x) + \cos(x) + \tan(x)", [sp.sin, sp.cos, sp.tan]),
            (r"\sinh(x) + \cosh(x) + \tanh(x)", [sp.sinh, sp.cosh, sp.tanh]),
            (r"\log(x) + \ln(x)", [sp.log]),
            (r"\left|x\right|", [sp.Abs]),
            (r"e^x", [sp.exp]),
        ],
    )
    def test_parse_latex_functions(self, latex, expected_functions):
        result = parse_latex(latex)
        assert result is not None
        for func in expected_functions:
            assert result.has(func)

    @pytest.mark.parametrize(
        "latex",
        [
            r"\alpha + \beta + \gamma",
            r"\delta + \epsilon + \zeta",
            r"\eta + \theta + \lambda",
            r"\mu + \nu + \xi",
            r"\pi + \rho + \sigma",
            r"\tau + \phi + \chi + \psi + \omega",
            r"\Gamma + \Delta + \Theta + \Lambda",
            r"\Xi + \Pi + \Sigma + \Phi + \Psi + \Omega",
        ],
    )
    def test_parse_latex_greek_symbols(self, latex):
        result = parse_latex(latex)
        assert result is not None
        assert result.free_symbols

    def test_parse_latex_sum(self):
        result = parse_latex(r"\sum_{i=1}^{n} i")
        i, n = sp.symbols("i n")
        assert result == sp.Sum(i, (i, 1, n))

    def test_parse_latex_product(self):
        result = parse_latex(r"\prod_{i=1}^{n} i")
        i, n = sp.symbols("i n")
        assert result == sp.Product(i, (i, 1, n))

    def test_parse_latex_integral(self):
        result = parse_latex(r"\int_{0}^{1} x^2 dx")
        x = sp.Symbol("x")
        assert result == sp.Integral(x**2, (x, 0, 1))

    def test_parse_latex_limit(self):
        result = parse_latex(r"\lim_{x\to 0} \frac{\sin(x)}{x}")
        assert isinstance(result, sp.Limit)
        assert result.doit() == 1

    def test_parse_latex_matrix(self):
        result = parse_latex(r"\begin{bmatrix}1 & 2 \\ 3 & 4\end{bmatrix}")
        assert result == sp.Matrix([[1, 2], [3, 4]])

    @pytest.mark.parametrize(
        "latex",
        [
            r"\begin{matrix}1 & x \\ y & 4\end{matrix}",
            r"\begin{pmatrix}1 & x \\ y & 4\end{pmatrix}",
            r"\begin{Bmatrix}1 & x \\ y & 4\end{Bmatrix}",
            r"\begin{smallmatrix}1 & x \\ y & 4\end{smallmatrix}",
            r"\begin{array}{cc}1 & x \\ y & 4\end{array}",
        ],
    )
    def test_parse_latex_begin_end_matrix_environments(self, latex):
        x, y = sp.symbols("x y")
        assert parse_latex(latex) == sp.Matrix([[1, x], [y, 4]])

    @pytest.mark.parametrize(
        "latex",
        [
            r"\begin{vmatrix}1 & 2 \\ 3 & 4\end{vmatrix}",
            r"\begin{Vmatrix}1 & 2 \\ 3 & 4\end{Vmatrix}",
            r"\det\begin{pmatrix}1 & 2 \\ 3 & 4\end{pmatrix}",
        ],
    )
    def test_parse_latex_begin_end_determinants(self, latex):
        assert parse_latex(latex) == -2

    def test_parse_latex_rejects_ragged_matrix_environment(self):
        result = parse_latex_detailed(r"\begin{bmatrix}1 & 2 \\ 3\end{bmatrix}")
        assert result.expression is None
        assert result.error_code == "UNSUPPORTED_EXPRESSION"

    def test_parse_latex_determinant(self):
        result = parse_latex(r"\det\begin{bmatrix}1 & 2 \\ 3 & 4\end{bmatrix}")
        assert result == -2

    def test_parse_latex_relation(self):
        result = parse_latex(r"x \le y")
        x, y = sp.symbols("x y")
        assert result == sp.Le(x, y)

    @pytest.mark.parametrize(
        ("latex", "expected"),
        [
            ("x < y", sp.Lt(sp.Symbol("x"), sp.Symbol("y"))),
            ("x > y", sp.Gt(sp.Symbol("x"), sp.Symbol("y"))),
            (r"x \leq y", sp.Le(sp.Symbol("x"), sp.Symbol("y"))),
            (r"x \geq y", sp.Ge(sp.Symbol("x"), sp.Symbol("y"))),
            (r"x \ne y", sp.Ne(sp.Symbol("x"), sp.Symbol("y"))),
        ],
    )
    def test_parse_latex_relation_aliases(self, latex, expected):
        assert parse_latex(latex) == expected

    def test_parse_latex_factorial_shorthand(self):
        n = sp.Symbol("n")
        assert parse_latex("n!") == sp.factorial(n)

    def test_parse_latex_plus_minus(self):
        x, y = sp.symbols("x y")
        assert parse_latex(r"x \pm y") == sp.Tuple(x + y, x - y)
        assert parse_latex(r"x \mp y") == sp.Tuple(x - y, x + y)
        assert parse_latex(r"\pm x") == sp.Tuple(x, -x)

    def test_parse_latex_derivatives(self):
        x, y = sp.symbols("x y")
        assert parse_latex(r"\frac{d}{dx} x^2").doit() == 2 * x
        assert parse_latex(r"\frac{\partial}{\partial x} x^2 y").doit() == 2 * x * y

    @pytest.mark.parametrize(
        ("latex", "function_name"),
        [
            (r"x \in A", "__latex_in"),
            (r"x \notin A", "__latex_notin"),
            (r"A \subset B", "__latex_subset"),
            (r"A \subseteq B", "__latex_subseteq"),
            (r"A \cup B", "__latex_union"),
            (r"A \cap B", "__latex_intersection"),
        ],
    )
    def test_parse_latex_set_operations(self, latex, function_name):
        result = parse_latex(latex)
        assert result is not None
        assert str(result.func) == function_name

    @pytest.mark.parametrize(
        ("latex", "function_name"),
        [
            (r"\left\|x\right\|_2^2", "__latex_norm"),
            (r"\mathbb{E}_{x}[x^2]", "__latex_expectation"),
            (r"\arg\min_{x} x^2", "__latex_argmin"),
            (r"\arg\max_{x} x^2", "__latex_argmax"),
        ],
    )
    def test_parse_latex_ml_special_notation(self, latex, function_name):
        result = parse_latex(latex)
        assert result is not None
        assert str(result.func) == function_name

    def test_parse_latex_update_arrow_reports_unsupported_feature(self):
        result = parse_latex_detailed(r"x \leftarrow x + 1")
        assert result.expression is None
        assert result.error_code == "UNSUPPORTED_FEATURE"
        assert "update arrow" in result.error_message

    def test_parse_latex_quadratic_formula_fragment(self):
        result = parse_latex(r"\frac{-b + \sqrt{b^2 - 4 a c}}{2 a}")
        a, b, c = sp.symbols("a b c")
        expected = (-b + sp.sqrt(b**2 - 4 * a * c)) / (2 * a)
        assert result is not None
        assert sp.simplify(result - expected) == 0

    @pytest.mark.parametrize("latex", ["", "   ", "invalid latex expression"])
    def test_parse_latex_rejects_empty_or_prose(self, latex):
        assert parse_latex(latex) is None

    @pytest.mark.parametrize(
        "latex",
        [
            "__import__('os').system('echo unsafe')",
            "open('/etc/passwd').read()",
            "x.__class__",
        ],
    )
    def test_parse_latex_rejects_malicious_fallback_payloads(self, latex):
        result = parse_latex_detailed(latex)
        assert result.expression is None
        assert result.error_code in {
            "INVALID_LATEX",
            "UNSAFE_INPUT",
            "UNSUPPORTED_EXPRESSION",
        }

    def test_parse_latex_rejects_overly_large_input(self):
        result = parse_latex_detailed("x" * 2001)
        assert result.expression is None
        assert result.error_code == "INPUT_TOO_LARGE"

    def test_parse_latex_rejects_overly_nested_input(self):
        result = parse_latex_detailed("{" * 65 + "x" + "}" * 65)
        assert result.expression is None
        assert result.error_code == "INPUT_TOO_COMPLEX"

    def test_parse_latex_invalid_input_does_not_poison_later_parse(self):
        assert parse_latex("invalid latex expression") is None
        assert parse_latex(r"\frac{x+1}{x-1}") is not None

    def test_bounded_fuzz_inputs_do_not_crash_or_poison_parser(self):
        alphabet = string.ascii_letters + string.digits + " +-*/^_=<>(){}[]\\"
        rng = random.Random(20260614)
        for _ in range(100):
            latex = "".join(rng.choice(alphabet) for _ in range(rng.randint(1, 80)))
            result = parse_latex_detailed(latex)
            assert result.expression is not None or result.error_code is not None
        assert sp.simplify(parse_latex(r"x + 1") - (sp.Symbol("x") + 1)) == 0

    def test_large_sum_completes_within_performance_budget(self):
        start = time.perf_counter()
        result = parse_latex_detailed(r"\sum_{i=1}^{100} i")
        elapsed = time.perf_counter() - start
        assert result.expression is not None
        assert elapsed < 1.0

    @pytest.mark.parametrize(
        "latex",
        [
            "{" * 65 + "x" + "}" * 65,
            "+".join(["x"] * 502),
            r"\sin" * 101 + "{x}",
        ],
    )
    def test_complex_inputs_reject_within_performance_budget(self, latex):
        start = time.perf_counter()
        result = parse_latex_detailed(latex)
        elapsed = time.perf_counter() - start
        assert result.expression is None
        assert result.error_code == "INPUT_TOO_COMPLEX"
        assert elapsed < 0.25

    @pytest.mark.parametrize(
        ("latex", "expected"),
        [
            ("x", True),
            ("x + 1", True),
            ("x < y", True),
            ("n!", True),
            (r"\alpha", True),
            ("plain words", False),
            ("", False),
        ],
    )
    def test_looks_like_math(self, latex, expected):
        assert generator is not None
        from core.parser import _looks_like_math

        assert _looks_like_math(latex) is expected

    def test_get_variables_simple(self):
        x, y = sp.symbols("x y")
        assert get_variables(x + y) == {x, y}

    def test_get_variables_constant(self):
        assert get_variables(sp.Integer(5)) == set()


class TestGeneratorModule:
    """Tests for every generator module function."""

    def test_generate_expression_mode_executes(self):
        x, y = sp.symbols("x y")
        code = generate_python(x + y, mode="expression")
        assert eval_expression_code(code, x=2, y=3) == 5

    def test_generate_function_mode_executes(self):
        x = sp.Symbol("x")
        code = generate_python(x**2 + 1, mode="function", func_name="square_plus_one")
        namespace = {}
        exec(code, namespace)
        assert namespace["square_plus_one"](4) == 17

    def test_generate_script_mode_shape(self):
        x = sp.Symbol("x")
        code = generate_python(x * 2, mode="script", func_name="double")
        assert "def double(x):" in code
        assert "argparse.ArgumentParser" in code
        assert 'if __name__ == "__main__":' in code

    @pytest.mark.parametrize(
        ("expr", "values", "expected"),
        [
            (sp.sin(sp.Symbol("x")) + sp.cos(sp.Symbol("x")), {"x": 0}, 1),
            (sp.sqrt(sp.Symbol("x")) + sp.Abs(sp.Symbol("y")), {"x": 9, "y": -2}, 5),
            (sp.pi * 2, {}, math.pi * 2),
            (sp.E ** sp.Symbol("x"), {"x": 1}, math.e),
        ],
    )
    def test_generate_math_imports_execute(self, expr, values, expected):
        code = generate_python(expr, mode="expression")
        assert "import math" in code
        assert eval_expression_code(code, **values) == pytest.approx(expected)

    def test_generate_sqrt_expression_imports_math(self):
        x, y = sp.symbols("x y")
        code = generate_python(sp.sqrt(x**2 + y**2), mode="function")
        assert "import math" in code
        namespace = {}
        exec(code, namespace)
        assert namespace["f"](3, 4) == 5

    def test_generate_numpy_sigmoid_executes(self):
        z = sp.Symbol("z")
        expr = 1 / (1 + sp.exp(-z))
        code = generate_python(expr, mode="expression", backend="numpy")
        assert "import numpy as np" in code
        assert eval_expression_code(code, z=0.7) == pytest.approx(
            1 / (1 + np.exp(-0.7))
        )

    def test_generate_numpy_relu_executes(self):
        x = sp.Symbol("x")
        code = generate_python(sp.Max(0, x), mode="expression", backend="numpy")
        assert eval_expression_code(code, x=-2.0) == 0
        assert eval_expression_code(code, x=3.0) == 3

    def test_generate_numpy_matrix_executes(self):
        code = generate_python(
            sp.Matrix([[1, 2], [3, 4]]), mode="expression", backend="numpy"
        )
        assert "np.array" in code
        result = eval_expression_code(code)
        assert np.array_equal(result, np.array([[1, 2], [3, 4]]))

    def test_generate_sympy_matrix_uses_sympy_backend(self):
        code = generate_python(
            sp.Matrix([[1, 2], [3, 4]]), mode="expression", backend="sympy"
        )
        assert code == "import sympy as sp\n\nsp.Matrix([[1, 2], [3, 4]])"
        result = eval_expression_code(code)
        assert result == sp.Matrix([[1, 2], [3, 4]])

    def test_generate_numpy_vector_add_uses_numpy_operation(self):
        x, y = sp.symbols("x y")
        code = generate_python(
            x + y,
            mode="expression",
            backend="numpy",
            var_types={"x": "vector", "y": "vector"},
        )
        assert "np.add(" in code
        result = eval_expression_code(code, x=np.array([1, 2]), y=np.array([3, 4]))
        assert np.array_equal(result, np.array([4, 6]))

    def test_generate_numpy_matrix_multiply_uses_matmul(self):
        a, x = sp.symbols("A x")
        code = generate_python(
            a * x,
            mode="expression",
            backend="numpy",
            var_types={"A": "matrix", "x": "vector"},
        )
        assert "np.matmul(" in code
        result = eval_expression_code(
            code,
            A=np.array([[1, 2], [3, 4]]),
            x=np.array([5, 6]),
        )
        assert np.array_equal(result, np.array([17, 39]))

    def test_generate_numpy_vector_product_uses_dot(self):
        x, y = sp.symbols("x y")
        code = generate_python(
            x * y,
            mode="expression",
            backend="numpy",
            var_types={"x": "vector", "y": "vector"},
        )
        assert "np.dot(" in code
        assert eval_expression_code(code, x=np.array([1, 2]), y=np.array([3, 4])) == 11

    def test_generate_numpy_norm_executes(self):
        expr = parse_latex(r"\left\|x\right\|_2^2")
        code = generate_python(expr, mode="expression", backend="numpy")
        assert eval_expression_code(code, x=np.array([3.0, 4.0])) == pytest.approx(25)

    def test_generate_sum_expression_executes(self):
        i, n = sp.symbols("i n")
        code = generate_python(sp.Sum(i, (i, 1, n)), mode="expression")
        assert eval_expression_code(code, n=4) == 10

    def test_generate_product_expression_executes(self):
        i, n = sp.symbols("i n")
        code = generate_python(sp.Product(i, (i, 1, n)), mode="expression")
        assert "math.factorial" in code
        assert eval_expression_code(code, n=5) == 120

    def test_generate_integral_expression_evaluates_when_possible(self):
        x = sp.Symbol("x")
        code = generate_python(sp.Integral(x**2, (x, 0, 1)), mode="expression")
        assert eval_expression_code(code) == pytest.approx(1 / 3)

    def test_generate_limit_expression_evaluates_when_possible(self):
        x = sp.Symbol("x")
        code = generate_python(
            sp.Limit(sp.sin(x) / x, x, 0, dir="+"), mode="expression"
        )
        assert eval_expression_code(code) == 1

    def test_generate_matrix_as_nested_lists(self):
        code = generate_python(sp.Matrix([[1, 2], [3, 4]]), mode="expression")
        assert eval_expression_code(code) == [[1, 2], [3, 4]]

    def test_generate_relation_executes(self):
        x, y = sp.symbols("x y")
        code = generate_python(sp.Le(x, y), mode="expression")
        assert eval_expression_code(code, x=1, y=2) is True
        assert eval_expression_code(code, x=3, y=2) is False

    def test_generate_plus_minus_tuple_executes(self):
        x, y = sp.symbols("x y")
        code = generate_python(sp.Tuple(x + y, x - y), mode="expression")
        assert eval_expression_code(code, x=5, y=2) == (7, 3)

    def test_generate_derivative_evaluates_when_possible(self):
        x = sp.Symbol("x")
        code = generate_python(sp.Derivative(x**2, x), mode="expression")
        assert eval_expression_code(code, x=3) == 6

    def test_generate_symbolic_fallback_uses_sympy(self):
        x = sp.Symbol("x")
        code = generate_python(sp.Derivative(sp.Function("f")(x), x), mode="expression")
        assert "import sympy as sp" in code
        result = eval_expression_code(code)
        assert isinstance(result, sp.Derivative)

    def test_generate_norm_executes(self):
        expr = parse_latex(r"\left\|x\right\|_2^2")
        code = generate_python(expr, mode="expression")
        assert eval_expression_code(code, x=-3) == 9

    @pytest.mark.parametrize(
        "latex",
        [r"\mathbb{E}_{x}[x^2]", r"\arg\min_{x} x^2", r"\arg\max_{x} x^2"],
    )
    def test_generate_ml_special_notation_symbolic(self, latex):
        expr = parse_latex(latex)
        code = generate_python(expr, mode="expression")
        assert "import sympy as sp" in code
        assert eval_expression_code(code) is not None

    @pytest.mark.parametrize(
        ("expr", "values", "expected"),
        [
            (parse_latex(r"x \in A"), {"x": 2, "A": {1, 2, 3}}, True),
            (parse_latex(r"x \notin A"), {"x": 4, "A": {1, 2, 3}}, True),
            (parse_latex(r"A \subset B"), {"A": {1}, "B": {1, 2}}, True),
            (parse_latex(r"A \subseteq B"), {"A": {1, 2}, "B": {1, 2}}, True),
            (parse_latex(r"A \cup B"), {"A": {1, 2}, "B": {2, 3}}, {1, 2, 3}),
            (parse_latex(r"A \cap B"), {"A": {1, 2}, "B": {2, 3}}, {2}),
        ],
    )
    def test_generate_set_operations_execute(self, expr, values, expected):
        code = generate_python(expr, mode="expression")
        assert eval_expression_code(code, **values) == expected

    def test_generate_with_custom_variable_names(self):
        alpha = sp.Symbol("alpha")
        code = generate_python(
            alpha + 1,
            mode="function",
            func_name="f",
            var_names={"alpha": "input-value"},
        )
        assert "def f(input_value):" in code

    def test_generate_function_with_variable_type_hints(self):
        x, y = sp.symbols("x y")
        code = generate_python(
            x + y,
            mode="function",
            backend="numpy",
            var_types={"x": "vector", "y": "matrix"},
        )
        assert "import numpy as np" in code
        assert "def f(x: np.ndarray, y: np.ndarray):" in code

    def test_generate_rejects_sanitized_name_collisions(self):
        expr = sp.Symbol("a-b") + sp.Symbol("a_b")
        with pytest.raises(generator.GenerationError) as exc_info:
            generate_python(expr, mode="expression")
        assert exc_info.value.code == "VARIABLE_NAME_COLLISION"

    @pytest.mark.parametrize("func_name", ["not valid", "class", "1starts_with_digit"])
    def test_generate_rejects_invalid_function_name(self, func_name):
        with pytest.raises(ValueError):
            generate_python(sp.Symbol("x"), mode="function", func_name=func_name)

    def test_generate_rejects_unknown_mode(self):
        with pytest.raises(ValueError, match="Unknown mode"):
            generate_python(sp.Symbol("x"), mode="unknown")  # type: ignore[arg-type]

    def test_generate_rejects_unknown_backend(self):
        with pytest.raises(generator.GenerationError) as exc_info:
            generate_python(sp.Symbol("x"), mode="expression", backend="bad")  # type: ignore[arg-type]
        assert exc_info.value.code == "INVALID_BACKEND"

    @pytest.mark.parametrize(
        ("name", "expected"),
        [
            ("x", "x"),
            ("input-value", "input_value"),
            ("1x", "v_1x"),
            ("class", "v_class"),
            ("", "v_"),
        ],
    )
    def test_safe_name_private(self, name, expected):
        assert generator._safe_name(name) == expected

    @pytest.mark.parametrize(
        ("name", "expected"),
        [("x", True), ("class", False), ("not valid", False), ("_x", True)],
    )
    def test_is_identifier_private(self, name, expected):
        assert generator._is_identifier(name) is expected


class TestSchemas:
    """Tests for schema defaults and validation."""

    def test_convert_request_defaults(self):
        request = ConvertRequest(latex="x + 1")
        assert request.mode == "function"
        assert request.func_name == "f"
        assert request.backend == "python"
        assert request.variable_types == {}

    def test_convert_request_rejects_invalid_mode(self):
        with pytest.raises(ValidationError):
            ConvertRequest(latex="x", mode="bad")  # type: ignore[arg-type]

        with pytest.raises(ValidationError):
            ConvertRequest(latex="x", mode="script")  # type: ignore[arg-type]

    def test_convert_request_rejects_invalid_backend(self):
        with pytest.raises(ValidationError):
            ConvertRequest(latex="x", backend="bad")  # type: ignore[arg-type]

    def test_convert_request_rejects_invalid_variable_type(self):
        with pytest.raises(ValidationError):
            ConvertRequest(latex="x", variable_types={"x": "tensor"})  # type: ignore[dict-item]

    def test_convert_request_rejects_oversized_latex(self):
        with pytest.raises(ValidationError):
            ConvertRequest(latex="x" * 2001)

    def test_convert_response_defaults(self):
        response = ConvertResponse(python="x + 1")
        assert response.variables == []
        assert response.error is None
        assert response.error_code is None
        assert response.symbol_map == {}
        assert response.support_level == "computed"
        assert response.backend == "python"
        assert response.required_imports == []
        assert response.variable_types == {}


class TestRoutesAndAPI:
    """Tests for route functions and mounted API behavior."""

    @pytest.mark.anyio
    async def test_convert_latex_direct_success(self):
        response = await convert_latex(
            ConvertRequest(latex=r"\frac{x+1}{x-1}", mode="function", func_name="f")
        )
        assert response.error is None
        assert response.variables == ["x"]
        assert response.symbol_map == {"x": "x"}
        assert response.support_level == "computed"
        assert response.backend == "python"
        assert "def f(x):" in response.python

    @pytest.mark.anyio
    async def test_convert_latex_direct_parse_error(self):
        response = await convert_latex(ConvertRequest(latex="invalid latex expression"))
        assert response.python == ""
        assert response.variables == []
        assert response.error_code == "INVALID_LATEX"

    @pytest.mark.anyio
    async def test_convert_latex_direct_generation_error(self):
        response = await convert_latex(ConvertRequest(latex="x", func_name="not valid"))
        assert response.python == ""
        assert response.error_code == "INVALID_FUNCTION_NAME"
        assert response.support_level == "unsupported"

    def test_root_serves_frontend(self):
        response = client.get("/")
        assert response.status_code == 200
        assert "LaTeX to Python Translator" in response.text
        assert 'id="latex-input"' in response.text
        assert 'id="variable-types"' in response.text
        assert 'value="script"' not in response.text
        assert "highlightPython" in response.text
        assert 'data-example="\\\\frac' not in response.text
        assert 'data-example="\\frac{x+1}{x-1}"' in response.text
        assert (
            'data-example="\\begin{bmatrix}1 &amp; 2 \\\\ 3 &amp; 4\\end{bmatrix}"'
            in response.text
        )
        assert "&#039;" not in response.text

    def test_static_css_uses_dark_color_scheme(self):
        response = client.get("/static/style.css")
        assert response.status_code == 200
        assert "color-scheme: dark" in response.text
        assert "--bg: #070b12" in response.text

    def test_static_css_served(self):
        response = client.get("/static/style.css")
        assert response.status_code == 200
        assert ".code-output" in response.text

    def test_health_endpoint(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    @pytest.mark.parametrize("mode", ["expression", "function"])
    def test_convert_endpoint_modes(self, mode):
        response = client.post(
            "/api/v1/convert",
            json={"latex": r"\sin(x)", "mode": mode, "func_name": "f"},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["error"] is None
        assert payload["variables"] == ["x"]
        assert payload["symbol_map"] == {"x": "x"}
        assert payload["support_level"] == "computed"
        assert payload["backend"] == "python"
        assert payload["python"]

    def test_convert_endpoint_numpy_backend(self):
        response = client.post(
            "/api/v1/convert",
            json={
                "latex": r"\frac{1}{1 + e^{-z}}",
                "mode": "expression",
                "backend": "numpy",
            },
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["error"] is None
        assert "import numpy as np" in payload["python"]
        assert "np.exp" in payload["python"]
        assert payload["backend"] == "numpy"
        assert payload["required_imports"] == ["import numpy as np"]

    def test_convert_endpoint_variable_types(self):
        response = client.post(
            "/api/v1/convert",
            json={
                "latex": "x + y",
                "mode": "function",
                "backend": "numpy",
                "variable_types": {"x": "vector", "y": "matrix"},
            },
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["error"] is None
        assert payload["variable_types"] == {"x": "vector", "y": "matrix"}
        assert "np.add(" in payload["python"]
        assert "def f(x: np.ndarray, y: np.ndarray):" in payload["python"]

    def test_convert_endpoint_matrix_backend_changes_output(self):
        response = client.post(
            "/api/v1/convert",
            json={
                "latex": r"\begin{bmatrix}1 & 2 \\ 3 & 4\end{bmatrix}",
                "mode": "expression",
                "backend": "numpy",
            },
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["error"] is None
        assert "np.array([[1, 2], [3, 4]])" in payload["python"]

    def test_convert_endpoint_examples_do_not_collapse_to_symbolic_hashes(self):
        examples = [
            r"\frac{x+1}{x-1}",
            r"\begin{bmatrix}1 & 2 \\ 3 & 4\end{bmatrix}",
            r"\sin(x)^2 + \cos(x)^2",
            r"\sum_{i=1}^{n} i^2",
            r"\sqrt{x^2 + y^2}",
        ]
        outputs = []
        for latex in examples:
            response = client.post(
                "/api/v1/convert",
                json={"latex": latex, "mode": "function", "backend": "python"},
            )
            assert response.status_code == 200
            payload = response.json()
            assert payload["error"] is None
            assert "__latex_symbolic" not in payload["python"]
            assert "latex_expr_" not in payload["python"]
            outputs.append(payload["python"])
        assert len(set(outputs)) == len(outputs)

    def test_convert_endpoint_parse_error(self):
        response = client.post(
            "/api/v1/convert",
            json={"latex": "invalid latex expression", "mode": "expression"},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["python"] == ""
        assert payload["error_code"] == "INVALID_LATEX"
        assert payload["support_level"] == "unsupported"

    @pytest.mark.parametrize(
        ("body", "snapshot"),
        [
            (
                {"latex": "invalid latex expression", "mode": "expression"},
                {
                    "python": "",
                    "variables": [],
                    "error": "Input does not look like a mathematical expression.",
                    "error_code": "INVALID_LATEX",
                    "symbol_map": {},
                    "support_level": "unsupported",
                    "backend": "python",
                    "required_imports": [],
                    "variable_types": {},
                },
            ),
            (
                {"latex": "x" * 2001, "mode": "expression"},
                {
                    "detail": [
                        {
                            "type": "string_too_long",
                            "loc": ["body", "latex"],
                            "msg": "String should have at most 2000 characters",
                            "ctx": {"max_length": 2000},
                        }
                    ]
                },
            ),
        ],
    )
    def test_api_error_payload_snapshots(self, body, snapshot):
        response = client.post("/api/v1/convert", json=body)
        payload = response.json()
        if "detail" in snapshot:
            assert response.status_code == 422
            assert payload["detail"][0]["type"] == snapshot["detail"][0]["type"]
            assert payload["detail"][0]["loc"] == snapshot["detail"][0]["loc"]
            assert payload["detail"][0]["msg"] == snapshot["detail"][0]["msg"]
            assert payload["detail"][0]["ctx"] == snapshot["detail"][0]["ctx"]
            return
        assert response.status_code == 200
        assert payload == snapshot

    def test_convert_cache_serves_repeated_safe_inputs(self):
        _convert_cached.cache_clear()
        first = client.post(
            "/api/v1/convert",
            json={"latex": r"\sin(x)", "mode": "expression"},
        )
        second = client.post(
            "/api/v1/convert",
            json={"latex": r"\sin(x)", "mode": "expression"},
        )
        assert first.status_code == 200
        assert second.status_code == 200
        assert first.json() == second.json()
        assert _convert_cached.cache_info().hits == 1
        assert _convert_cached.cache_info().maxsize == 256

    def test_convert_endpoint_validation_error(self):
        response = client.post(
            "/api/v1/convert",
            json={"latex": "x", "mode": "invalid"},
        )
        assert response.status_code == 422

    def test_openapi_available(self):
        response = client.get("/openapi.json")
        assert response.status_code == 200
        assert "/api/v1/convert" in response.json()["paths"]


class TestModuleImports:
    """Tests for simple module-level wiring."""

    def test_root_main_exports_fastapi_app(self):
        assert cli_main.app is app

    def test_run_app_module_importable(self):
        assert callable(run_app.main)

    def test_package_modules_importable(self):
        import api
        import core

        assert api is not None
        assert core is not None
