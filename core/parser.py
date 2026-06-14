"""Parse LaTeX expressions into SymPy expressions or custom AST."""

from dataclasses import dataclass
import re
from typing import Optional, Union

import sympy as sp
from latex2sympy2 import latex2sympy
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

MAX_LATEX_LENGTH = 2000
MAX_NESTING_DEPTH = 64
MAX_LATEX_COMMANDS = 100
MAX_OPERATOR_COUNT = 500
SAFE_FALLBACK_PATTERN = re.compile(r"^[A-Za-z0-9_\s+\-*/^<>=!,().]+$")


@dataclass(frozen=True)
class ParseResult:
    """Structured result for LaTeX parsing."""

    expression: sp.Expr | None
    error_code: str | None = None
    error_message: str | None = None


def parse_latex(latex_str: str) -> Optional[Union[sp.Expr, str]]:
    """
    Parse a LaTeX string into a SymPy expression.

    Args:
        latex_str: LaTeX string (e.g., r'\frac{x+1}{x-1}')

    Returns:
        SymPy expression or None if parsing fails
    """
    return parse_latex_detailed(latex_str).expression


def parse_latex_detailed(latex_str: str) -> ParseResult:
    """Parse a LaTeX string and return structured error metadata."""
    latex_str = latex_str.strip()
    complexity_error = _validate_latex_complexity(latex_str)
    if complexity_error is not None:
        return complexity_error

    if not _looks_like_math(latex_str):
        return ParseResult(
            expression=None,
            error_code="INVALID_LATEX",
            error_message="Input does not look like a mathematical expression.",
        )

    special_expression = _parse_special_ml_notation(latex_str)
    if special_expression is not None:
        return ParseResult(expression=special_expression)

    unsupported_feature = _detect_unsupported_feature(latex_str)
    if unsupported_feature is not None:
        return ParseResult(
            expression=None,
            error_code="UNSUPPORTED_FEATURE",
            error_message=f"Unsupported notation: {unsupported_feature}.",
        )

    set_operation = _parse_set_operation(latex_str)
    if set_operation is not None:
        return ParseResult(expression=set_operation)

    plus_minus = _parse_plus_minus(latex_str)
    if plus_minus is not None:
        return ParseResult(expression=plus_minus)

    normalized = _normalize_latex(latex_str)

    if "factorial(" in normalized:
        return _safe_parse_expr(normalized)

    try:
        return ParseResult(expression=latex2sympy(normalized))
    except Exception:
        return _safe_parse_expr(normalized)


def get_variables(expr: sp.Expr) -> set:
    """Extract free variables from a SymPy expression."""
    return expr.free_symbols


def _looks_like_math(latex_str: str) -> bool:
    """Reject prose-like input before it reaches latex2sympy2's global parser."""
    if not latex_str:
        return False
    if "\\" in latex_str or re.search(r"[\d+\-*/^_=<>!(){}\[\]]", latex_str):
        return True
    if all(re.fullmatch(r"[A-Za-z]", token) for token in latex_str.split()):
        return True
    return bool(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", latex_str))


def _validate_latex_complexity(latex_str: str) -> ParseResult | None:
    """Reject inputs that are too large or structurally expensive to parse."""
    if not latex_str:
        return ParseResult(
            expression=None,
            error_code="INVALID_LATEX",
            error_message="Input is empty.",
        )
    if len(latex_str) > MAX_LATEX_LENGTH:
        return ParseResult(
            expression=None,
            error_code="INPUT_TOO_LARGE",
            error_message=f"Input exceeds {MAX_LATEX_LENGTH} characters.",
        )
    if _contains_unsafe_tokens(latex_str):
        return ParseResult(
            expression=None,
            error_code="UNSAFE_INPUT",
            error_message="Input contains unsafe tokens.",
        )
    if _max_nesting_depth(latex_str) > MAX_NESTING_DEPTH:
        return ParseResult(
            expression=None,
            error_code="INPUT_TOO_COMPLEX",
            error_message=f"Input nesting exceeds {MAX_NESTING_DEPTH} levels.",
        )
    if not _has_balanced_delimiters(latex_str):
        return ParseResult(
            expression=None,
            error_code="INVALID_LATEX",
            error_message="Input contains unbalanced delimiters.",
        )
    if len(re.findall(r"\\[A-Za-z]+", latex_str)) > MAX_LATEX_COMMANDS:
        return ParseResult(
            expression=None,
            error_code="INPUT_TOO_COMPLEX",
            error_message=f"Input contains more than {MAX_LATEX_COMMANDS} commands.",
        )
    if len(re.findall(r"[+\-*/^_=<>!]", latex_str)) > MAX_OPERATOR_COUNT:
        return ParseResult(
            expression=None,
            error_code="INPUT_TOO_COMPLEX",
            error_message=f"Input contains more than {MAX_OPERATOR_COUNT} operators.",
        )
    return None


def _contains_unsafe_tokens(text: str) -> bool:
    """Reject tokens that should never be needed for supported LaTeX math."""
    return any(token in text for token in ("__", "'", '"', "`", ";")) or bool(
        re.search(r"\.[A-Za-z_]", text)
    )


def _max_nesting_depth(text: str) -> int:
    max_depth = 0
    depth = 0
    pairs = {"{": "}", "(": ")", "[": "]"}
    closing = set(pairs.values())
    for char in text:
        if char in pairs:
            depth += 1
            max_depth = max(max_depth, depth)
        elif char in closing and depth > 0:
            depth -= 1
    return max_depth


def _has_balanced_delimiters(text: str) -> bool:
    stack = []
    pairs = {"{": "}", "(": ")", "[": "]"}
    closing = {value: key for key, value in pairs.items()}
    for char in text:
        if char in pairs:
            stack.append(char)
        elif char in closing:
            if not stack or stack[-1] != closing[char]:
                return False
            stack.pop()
    return not stack


def _safe_parse_expr(expr_str: str) -> ParseResult:
    """Parse a restricted non-LaTeX expression without raw sympify."""
    if "\\" in expr_str or not SAFE_FALLBACK_PATTERN.fullmatch(expr_str):
        return ParseResult(
            expression=None,
            error_code="UNSUPPORTED_EXPRESSION",
            error_message="Expression is not supported by the safe fallback parser.",
        )

    names = set(re.findall(r"[A-Za-z_]\w*", expr_str))
    allowed_functions = {"factorial": sp.factorial}
    local_dict = {name: allowed_functions.get(name, sp.Symbol(name)) for name in names}
    local_dict.update(allowed_functions)
    transformations = standard_transformations + (
        implicit_multiplication_application,
        convert_xor,
    )

    try:
        expression = parse_expr(
            expr_str,
            local_dict=local_dict,
            global_dict={"__builtins__": {}},
            transformations=transformations,
            evaluate=True,
        )
    except Exception:
        return ParseResult(
            expression=None,
            error_code="INVALID_LATEX",
            error_message="Expression could not be parsed.",
        )
    return ParseResult(expression=expression)


def _normalize_latex(latex_str: str) -> str:
    """Normalize common LaTeX variants before parsing."""
    normalized = latex_str.strip()
    normalized = normalized.replace(r"\leq", r"\le")
    normalized = normalized.replace(r"\geq", r"\ge")
    normalized = normalized.replace(r"\ne", r"\neq")
    normalized = _normalize_factorials(normalized)
    return normalized


def _normalize_factorials(latex_str: str) -> str:
    """Convert simple postfix factorial notation to SymPy-friendly calls."""
    pattern = re.compile(r"(?<!\\)([A-Za-z][A-Za-z0-9_]*|\d+)!")
    return pattern.sub(r"factorial(\1)", latex_str)


def _parse_special_ml_notation(latex_str: str) -> sp.Expr | None:
    """Parse selected ML notation into symbolic internal functions."""
    norm = _parse_norm(latex_str)
    if norm is not None:
        return norm

    expectation = _parse_expectation(latex_str)
    if expectation is not None:
        return expectation

    optimizer = _parse_arg_optimizer(latex_str)
    if optimizer is not None:
        return optimizer

    return None


def _parse_norm(latex_str: str) -> sp.Expr | None:
    patterns = [
        r"^\\left\\\|(?P<inner>.+?)\\right\\\|(?:_(?P<order>\d+))?(?:\^(?P<power>\d+))?$",
        r"^\\\|(?P<inner>.+?)\\\|(?:_(?P<order>\d+))?(?:\^(?P<power>\d+))?$",
    ]
    for pattern in patterns:
        match = re.match(pattern, latex_str)
        if match is None:
            continue
        inner = parse_latex(match.group("inner").strip())
        if inner is None:
            return None
        order = sp.Integer(match.group("order") or 2)
        power = sp.Integer(match.group("power") or 1)
        return sp.Function("__latex_norm")(inner, order, power)
    return None


def _parse_expectation(latex_str: str) -> sp.Expr | None:
    match = re.match(
        r"^\\mathbb\{E\}(?:_\{(?P<var>[^}]+)\})?\[(?P<body>.+)\]$",
        latex_str,
    )
    if match is None:
        return None
    body = parse_latex(match.group("body").strip())
    if body is None:
        return None
    variable_latex = match.group("var")
    variable = parse_latex(variable_latex.strip()) if variable_latex else sp.Symbol("_")
    if variable is None:
        return None
    return sp.Function("__latex_expectation")(body, variable)


def _parse_arg_optimizer(latex_str: str) -> sp.Expr | None:
    match = re.match(
        r"^\\arg\\(?P<kind>min|max)_\{(?P<var>[^}]+)\}\s*(?P<body>.+)$",
        latex_str,
    )
    if match is None:
        return None
    variable = parse_latex(match.group("var").strip())
    body = parse_latex(match.group("body").strip())
    if variable is None or body is None:
        return None
    function_name = f"__latex_arg{match.group('kind')}"
    return sp.Function(function_name)(body, variable)


def _detect_unsupported_feature(latex_str: str) -> str | None:
    features = [
        (r"\\leftarrow", "update arrow"),
        (r"\\odot", "Hadamard product"),
        (r"\\mathcal\{N\}", "distribution notation"),
        (r"\\sim", "distribution sampling"),
        (r"\\\|", "embedded norm"),
        (r"\\left\\\|", "embedded norm"),
    ]
    for pattern, label in features:
        if re.search(pattern, latex_str):
            return label
    return None


def _parse_plus_minus(latex_str: str) -> Optional[sp.Tuple]:
    """Parse plus-minus/minus-plus expressions as two Python alternatives."""
    operator = (
        r"\pm" if r"\pm" in latex_str else r"\mp" if r"\mp" in latex_str else None
    )
    if operator is None:
        return None

    left_latex, right_latex = latex_str.split(operator, 1)
    left_latex = left_latex.strip()
    right_latex = right_latex.strip()
    if not right_latex:
        return None

    left = parse_latex(left_latex) if left_latex else sp.Integer(0)
    right = parse_latex(right_latex)
    if left is None or right is None:
        return None

    if operator == r"\pm":
        return sp.Tuple(left + right, left - right)
    return sp.Tuple(left - right, left + right)


def _parse_set_operation(latex_str: str) -> Optional[sp.Expr]:
    """Parse common set and membership operators."""
    operations = [
        (r"\\notin(?![A-Za-z])", "__latex_notin"),
        (r"\\not\\in(?![A-Za-z])", "__latex_notin"),
        (r"\\subseteq(?![A-Za-z])", "__latex_subseteq"),
        (r"\\subset(?![A-Za-z])", "__latex_subset"),
        (r"\\in(?![A-Za-z])", "__latex_in"),
        (r"\\cup(?![A-Za-z])", "__latex_union"),
        (r"\\cap(?![A-Za-z])", "__latex_intersection"),
    ]
    for pattern, function_name in operations:
        match = re.search(pattern, latex_str)
        if match is None:
            continue
        left_latex = latex_str[: match.start()]
        right_latex = latex_str[match.end() :]
        left = parse_latex(left_latex.strip())
        right = parse_latex(right_latex.strip())
        if left is None or right is None:
            return None
        return sp.Function(function_name)(left, right)
    return None
