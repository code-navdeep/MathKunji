"""
Tests for utils/latex_formatter.py.

extract_latex() in particular got its rule wrong three separate times while it
was being written, each against a real output shape from this app:

  1. Preferring the last display-math block returned the *input matrix* for
     eigenvalues, because that template puts the matrix in $$...$$ and the
     eigenvalues in inline $...$ after it.
  2. Taking a single inline block returned one root of two for solve, silently
     dropping the other.
  3. Once "Show steps" existed, the last maths-bearing line became an
     intermediate step rather than the answer.

Every one of those was caught by hand. These tests exist so the next one is not.
"""

from core.algebra import simplify_expression, solve_equation
from core.calculus import calculate_derivative, calculate_integral
from core.matrices import matrix_eigenvalues, matrix_determinant
from core.special_functions import evaluate_gamma, evaluate_zeta
from core.steps import derivative_steps
from utils.latex_formatter import extract_latex, numeric_note, to_latex, to_latex_inline
from utils.parser import parse_expression


def parse(text):
    success, value = parse_expression(text)
    assert success, f"fixture failed to parse: {text!r} -> {value!r}"
    return value


# --------------------------------------------------------------------------
# extract_latex
# --------------------------------------------------------------------------

def test_extract_latex_takes_the_result_not_the_input():
    latex_source = extract_latex(simplify_expression("sin(x)^2 + cos(x)^2"))
    assert latex_source == "1"


def test_extract_latex_returns_every_root_of_a_solve():
    """Regression: taking a single inline block dropped one of the two roots."""
    latex_source = extract_latex(solve_equation("x^2 - 4", "x"))
    assert "-2" in latex_source and "2" in latex_source


def test_extract_latex_prefers_eigenvalues_over_the_input_matrix():
    """
    Regression: this template puts the matrix in display maths and the
    eigenvalues in inline maths afterwards, so "last display block" returned
    the input the user had just typed in.
    """
    latex_source = extract_latex(matrix_eigenvalues("[[2, -1], [-1, 2]]"))
    assert "begin{matrix}" not in latex_source


def test_extract_latex_ignores_step_by_step_working():
    """
    Regression: steps are appended after the result, so the last maths-bearing
    line stopped being the answer and Copy LaTeX returned a sub-derivative.
    """
    result = calculate_derivative("x^2*sin(x)", "x", 1)
    with_steps = result + "\n\n" + derivative_steps("x^2*sin(x)", "x")
    assert extract_latex(with_steps) == extract_latex(result)


def test_extract_latex_handles_matrices_and_specials():
    assert extract_latex(matrix_determinant("[[1, 2], [3, 4]]")) == "-2"
    assert extract_latex(evaluate_gamma("5")) == "24"
    assert "frac" in extract_latex(calculate_integral("x^2", "x"))


def test_extract_latex_empty_when_there_is_no_maths():
    assert extract_latex("❌ Empty expression") == ""
    assert extract_latex("") == ""
    assert extract_latex(None) == ""


# --------------------------------------------------------------------------
# numeric_note
# --------------------------------------------------------------------------

def test_numeric_note_off_by_default_flag():
    assert numeric_note(parse("zeta(3)"), show=False) == ""


def test_numeric_note_renders_an_opaque_exact_value():
    note = numeric_note(parse("zeta(3)"))
    assert "Numeric" in note and "1.20205" in note


def test_numeric_note_silent_when_symbols_remain():
    """No single number exists, so there is nothing to show."""
    assert numeric_note(parse("erf(x)")) == ""


def test_numeric_note_silent_for_plain_integers_and_floats():
    """
    "120" followed by "120.0" is noise, and a result SymPy already returned as
    a decimal does not need restating.
    """
    assert numeric_note(parse("120")) == ""
    assert numeric_note(parse("1.5")) == ""


def test_numeric_note_kept_for_rationals():
    """1/3 -> 0.3333333333 genuinely adds information."""
    assert "0.333" in numeric_note(parse("1/3"))


# --------------------------------------------------------------------------
# delimiters
# --------------------------------------------------------------------------

def test_display_and_inline_delimiters_differ():
    expr = parse("x^2")
    assert to_latex(expr).startswith("$$") and to_latex(expr).endswith("$$")
    inline = to_latex_inline(expr)
    assert inline.startswith("$") and not inline.startswith("$$")
