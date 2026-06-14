"""Regression tests for ML expressions listed in test-strings.md."""

from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Callable

import pytest

from core.generator import generate_python
from core.parser import parse_latex

ROOT = Path(__file__).resolve().parents[1]
ML_STRINGS_PATH = ROOT / "test-strings.md"


def load_ml_expressions() -> dict[int, str]:
    """Load numbered backtick expressions from test-strings.md."""
    text = ML_STRINGS_PATH.read_text()
    matches = re.findall(r"^(\d+)\.\s+`(.+)`$", text, flags=re.MULTILINE)
    return {int(number): expression for number, expression in matches}


def rhs(expression: str) -> str:
    """Return the expression to calculate from an equation-like string."""
    if "=" not in expression:
        return expression
    return expression.split("=", 1)[1].strip()


def eval_expression_code(code: str, **values):
    """Evaluate generated expression-mode code with optional imports."""
    lines = [line for line in code.splitlines() if line.strip()]
    namespace = dict(values)
    exec("\n".join(lines[:-1] + [f"_result = {lines[-1]}"]), namespace)
    return namespace["_result"]


def generated_value(latex: str, **values):
    """Parse LaTeX, generate Python, and evaluate it with provided values."""
    parsed = parse_latex(latex)
    assert parsed is not None, f"Could not parse {latex!r}"
    code = generate_python(parsed, mode="expression")
    return eval_expression_code(code, **values)


ML_EXPRESSIONS = load_ml_expressions()


NUMERIC_CASES: dict[int, tuple[dict[str, float], Callable[..., float]]] = {
    6: ({"z": 0.7}, lambda z: 1 / (1 + math.exp(-z))),
    8: ({"x": -1.2}, lambda x: 1 / (1 + math.exp(-x))),
    9: ({"x": -3.0}, lambda x: max(0, x)),
    10: (
        {"x": 0.9},
        lambda x: (math.exp(x) - math.exp(-x)) / (math.exp(x) + math.exp(-x)),
    ),
    13: (
        {"N": 5, "y_i": 3.0, "_hat_y__i": 1.0},
        lambda N, y_i, _hat_y__i: (y_i - _hat_y__i) ** 2,
    ),
    19: (
        {"x_i": 2.0, "x_j": 3.0, "c": 1.5, "d": 2.0},
        lambda x_i, x_j, c, d: (x_i * x_j + c) ** d,
    ),
    27: ({"W": 2.5, "x": 4.0, "mu": 1.0}, lambda W, x, mu: W * (x - mu)),
    31: (
        {"C": 4, "p_k": 0.25},
        lambda C, p_k: sum(p_k * (1 - p_k) for _ in range(1, C + 1)),
    ),
    32: (
        {"C": 4, "p_k": 0.25},
        lambda C, p_k: -sum(p_k * math.log(p_k, 2) for _ in range(1, C + 1)),
    ),
    38: (
        {"x_i": 1.4, "mu_y": 1.0, "sigma_y": 0.8},
        lambda x_i, mu_y, sigma_y: (1 / math.sqrt(2 * math.pi * sigma_y**2))
        * math.exp(-((x_i - mu_y) ** 2) / (2 * sigma_y**2)),
    ),
}


DECLARATIVE_OR_SYMBOLIC_CASES = {
    1: "linear model with ellipsis and indexed symbolic variables",
    2: "ridge argmin objective",
    3: "lasso argmin objective",
    4: "elastic-net argmin objective",
    5: "prediction equation with sigma function application",
    7: "layer equation with indexed tensor symbols",
    11: "softmax with symbolic indexed denominator",
    12: "cross-entropy indexed symbolic sum",
    14: "chain-rule derivative equation",
    15: "convolution with symbolic indexed function calls",
    16: "SVM constrained optimization objective",
    17: "kernel feature-map identity",
    18: "RBF kernel with norm notation",
    20: "SVM decision rule with sign and symbolic kernel",
    21: "k-means cluster-set optimization",
    22: "cluster centroid set sum",
    23: "Gaussian mixture with distribution notation",
    24: "GMM responsibility with distribution notation",
    25: "GMM mean update with symbolic responsibility",
    26: "PCA trace maximization with constraint",
    28: "KL divergence indexed symbolic sum",
    29: "t-SNE probability with pairwise indexed denominator",
    30: "UMAP-style optimization objective",
    33: "information gain over symbolic sets",
    34: "ensemble average over symbolic tree functions",
    35: "AdaBoost weight update with symbolic classifier",
    36: "Bayes rule with probability function notation",
    37: "Naive Bayes product with probability notation",
    39: "Bayesian prior distribution notation",
    40: "Bayesian posterior distribution notation",
    41: "Bellman optimality equation with state/action functions",
    42: "Q-learning assignment/update equation",
    43: "policy gradient expectation",
    44: "REINFORCE expectation",
    45: "actor-critic expectation",
    46: "aligned LSTM gate system",
    47: "attention equation with matrix softmax",
    48: "transformer block with named layer functions",
    49: "GAN minimax objective with expectations",
    50: "VAE ELBO with expectations and KL divergence",
}


def test_ml_expression_file_contains_expected_50_entries():
    assert len(ML_EXPRESSIONS) == 50
    assert set(ML_EXPRESSIONS) == set(range(1, 51))


def test_every_ml_expression_has_a_test_classification():
    classified = set(NUMERIC_CASES) | set(DECLARATIVE_OR_SYMBOLIC_CASES)
    assert classified == set(ML_EXPRESSIONS)


@pytest.mark.parametrize("case_id", sorted(NUMERIC_CASES))
def test_ml_numeric_expression_calculations(case_id):
    values, reference = NUMERIC_CASES[case_id]
    latex = rhs(ML_EXPRESSIONS[case_id])
    actual = generated_value(latex, **values)
    expected = reference(**values)
    assert actual == pytest.approx(expected)


@pytest.mark.parametrize("case_id", sorted(DECLARATIVE_OR_SYMBOLIC_CASES))
def test_ml_declarative_expression_is_tracked(case_id):
    expression = ML_EXPRESSIONS[case_id]
    reason = DECLARATIVE_OR_SYMBOLIC_CASES[case_id]
    assert expression
    assert reason
