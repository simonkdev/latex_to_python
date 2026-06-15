"""Tests for matrix support in LaTeX to Python."""

import sympy as sp
from core.parser import parse_latex


def test_bmatrix():
    """Test basic bmatrix parsing."""
    result = parse_latex(r"\begin{bmatrix}1 & 2 \\ 3 & 4\end{bmatrix}")
    assert result == sp.Matrix([[1, 2], [3, 4]])


def test_pmatrix():
    """Test pmatrix parsing."""
    result = parse_latex(r"\begin{pmatrix}1 & 2 \\ 3 & 4\end{pmatrix}")
    assert result == sp.Matrix([[1, 2], [3, 4]])


def test_matrix_with_expressions():
    """Test matrix with symbolic expressions."""
    result = parse_latex(r"\begin{bmatrix}x & y \\ z & w\end{bmatrix}")
    x, y, z, w = sp.symbols("x y z w")
    expected = sp.Matrix([[x, y], [z, w]])
    assert result == expected


def test_matrix_with_fractions():
    """Test matrix with fractions."""
    result = parse_latex(r"\begin{bmatrix}\frac{1}{2} & 3 \\ 4 & 5\end{bmatrix}")
    expected = sp.Matrix([[sp.Rational(1, 2), 3], [4, 5]])
    assert result == expected


def test_matrix_3x3():
    """Test 3x3 matrix."""
    result = parse_latex(
        r"\begin{bmatrix}1 & 2 & 3 \\ 4 & 5 & 6 \\ 7 & 8 & 9\end{bmatrix}"
    )
    expected = sp.Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    assert result == expected


def test_matrix_single_row():
    """Test single-row matrix."""
    result = parse_latex(r"\begin{bmatrix}1 & 2 & 3\end{bmatrix}")
    expected = sp.Matrix([[1, 2, 3]])
    assert result == expected


def test_matrix_single_column():
    """Test single-column matrix."""
    result = parse_latex(r"\begin{bmatrix}1 \\ 2 \\ 3\end{bmatrix}")
    expected = sp.Matrix([[1], [2], [3]])
    assert result == expected


def test_matrix_single_element():
    """Test single-element matrix."""
    result = parse_latex(r"\begin{bmatrix}42\end{bmatrix}")
    expected = sp.Matrix([[42]])
    assert result == expected


if __name__ == "__main__":
    test_bmatrix()
    test_pmatrix()
    test_matrix_with_expressions()
    test_matrix_with_fractions()
    test_matrix_3x3()
    test_matrix_single_row()
    test_matrix_single_column()
    test_matrix_single_element()
    print("All matrix tests passed!")
