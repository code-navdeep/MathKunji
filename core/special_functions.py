"""
Special mathematical functions: gamma, zeta, Bessel, etc.
"""

from sympy import (
    gamma, zeta, factorial, binomial,
    besselj, bessely, besseli, besselk,
    hermite, legendre, laguerre, chebyshevt, chebyshevu,
    assoc_legendre, assoc_laguerre,
    erf, erfc
)
# Bare LaTeX (no $ delimiters). These evaluators build their own inline math
# contexts by hand -- "$\Gamma(...)$", "$H_{...}(...)$" -- so they need the
# unwrapped form. to_latex() is for standalone display math and wraps in $$.
from sympy import latex
from utils.parser import parse_expression
from utils.latex_formatter import to_latex, numeric_note


def evaluate_gamma(n_string, show_numeric=False):
    """
    Evaluate the Gamma function Γ(n).

    Args:
        n_string (str): Argument for gamma function

    Returns:
        str: Formatted result
    """
    success, n = parse_expression(n_string)
    if not success:
        return f"❌ {n}"

    try:
        result = gamma(n)

        output = "### Gamma Function\n\n"
        output += f"**Expression:** $\\Gamma({latex(n)})$\n\n"
        output += f"**Result:** {to_latex(result)}\n"
        output += numeric_note(result, show_numeric)

        return output

    except Exception as e:
        return f"❌ Error evaluating gamma: {str(e)}"


def evaluate_zeta(s_string, show_numeric=False):
    """
    Evaluate the Riemann Zeta function ζ(s).

    Args:
        s_string (str): Argument for zeta function

    Returns:
        str: Formatted result
    """
    success, s = parse_expression(s_string)
    if not success:
        return f"❌ {s}"

    try:
        result = zeta(s)

        output = "### Riemann Zeta Function\n\n"
        output += f"**Expression:** $\\zeta({latex(s)})$\n\n"
        output += f"**Result:** {to_latex(result)}\n"
        output += numeric_note(result, show_numeric)

        return output

    except Exception as e:
        return f"❌ Error evaluating zeta: {str(e)}"


def evaluate_factorial(n_string, show_numeric=False):
    """
    Evaluate n!

    Args:
        n_string (str): Number for factorial

    Returns:
        str: Formatted result
    """
    success, n = parse_expression(n_string)
    if not success:
        return f"❌ {n}"

    try:
        result = factorial(n)

        output = "### Factorial\n\n"
        output += f"**Expression:** ${latex(n)}!$\n\n"
        output += f"**Result:** {to_latex(result)}\n"
        output += numeric_note(result, show_numeric)

        return output

    except Exception as e:
        return f"❌ Error evaluating factorial: {str(e)}"


def evaluate_binomial(n_string, k_string, show_numeric=False):
    """
    Evaluate binomial coefficient C(n, k).

    Args:
        n_string (str): n value
        k_string (str): k value

    Returns:
        str: Formatted result
    """
    n_success, n = parse_expression(n_string)
    if not n_success:
        return f"❌ n: {n}"

    k_success, k = parse_expression(k_string)
    if not k_success:
        return f"❌ k: {k}"

    try:
        result = binomial(n, k)

        output = "### Binomial Coefficient\n\n"
        output += f"**Expression:** $C({latex(n)}, {latex(k)})$ or $\\binom{{{latex(n)}}}{{{latex(k)}}}$\n\n"
        output += f"**Result:** {to_latex(result)}\n"
        output += numeric_note(result, show_numeric)

        return output

    except Exception as e:
        return f"❌ Error evaluating binomial: {str(e)}"


def evaluate_hermite(n_string, x_string, show_numeric=False):
    """
    Evaluate Hermite polynomial H_n(x).

    Args:
        n_string (str): Polynomial order
        x_string (str): Variable value

    Returns:
        str: Formatted result
    """
    n_success, n = parse_expression(n_string)
    if not n_success:
        return f"❌ n: {n}"

    x_success, x = parse_expression(x_string)
    if not x_success:
        return f"❌ x: {x}"

    try:
        result = hermite(n, x)

        output = "### Hermite Polynomial\n\n"
        output += f"**Expression:** $H_{{{latex(n)}}}({latex(x)})$\n\n"
        output += f"**Result:** {to_latex(result)}\n"
        output += numeric_note(result, show_numeric)

        return output

    except Exception as e:
        return f"❌ Error evaluating Hermite: {str(e)}"


def evaluate_legendre(n_string, x_string, show_numeric=False):
    """
    Evaluate Legendre polynomial P_n(x).

    Args:
        n_string (str): Polynomial order
        x_string (str): Variable value

    Returns:
        str: Formatted result
    """
    n_success, n = parse_expression(n_string)
    if not n_success:
        return f"❌ n: {n}"

    x_success, x = parse_expression(x_string)
    if not x_success:
        return f"❌ x: {x}"

    try:
        result = legendre(n, x)

        output = "### Legendre Polynomial\n\n"
        output += f"**Expression:** $P_{{{latex(n)}}}({latex(x)})$\n\n"
        output += f"**Result:** {to_latex(result)}\n"
        output += numeric_note(result, show_numeric)

        return output

    except Exception as e:
        return f"❌ Error evaluating Legendre: {str(e)}"


def evaluate_laguerre(n_string, x_string, show_numeric=False):
    """
    Evaluate Laguerre polynomial L_n(x).

    Args:
        n_string (str): Polynomial order
        x_string (str): Variable value

    Returns:
        str: Formatted result
    """
    n_success, n = parse_expression(n_string)
    if not n_success:
        return f"❌ n: {n}"

    x_success, x = parse_expression(x_string)
    if not x_success:
        return f"❌ x: {x}"

    try:
        result = laguerre(n, x)

        output = "### Laguerre Polynomial\n\n"
        output += f"**Expression:** $L_{{{latex(n)}}}({latex(x)})$\n\n"
        output += f"**Result:** {to_latex(result)}\n"
        output += numeric_note(result, show_numeric)

        return output

    except Exception as e:
        return f"❌ Error evaluating Laguerre: {str(e)}"


def evaluate_erf(x_string, show_numeric=False):
    """
    Evaluate the error function erf(x).

    Args:
        x_string (str): Argument

    Returns:
        str: Formatted result
    """
    success, x = parse_expression(x_string)
    if not success:
        return f"❌ {x}"

    try:
        result = erf(x)

        output = "### Error Function\n\n"
        output += f"**Expression:** $\\text{{erf}}({latex(x)})$\n\n"
        output += f"**Result:** {to_latex(result)}\n"
        output += numeric_note(result, show_numeric)

        return output

    except Exception as e:
        return f"❌ Error evaluating erf: {str(e)}"


def evaluate_erfc(x_string, show_numeric=False):
    """
    Evaluate the complementary error function erfc(x) = 1 - erf(x).

    Args:
        x_string (str): Argument

    Returns:
        str: Formatted result
    """
    success, x = parse_expression(x_string)
    if not success:
        return f"❌ {x}"

    try:
        result = erfc(x)

        output = "### Complementary Error Function\n\n"
        output += f"**Expression:** $\\text{{erfc}}({latex(x)})$\n\n"
        output += f"**Result:** {to_latex(result)}\n"
        output += numeric_note(result, show_numeric)

        return output

    except Exception as e:
        return f"❌ Error evaluating erfc: {str(e)}"


def evaluate_besselj(n_string, x_string, show_numeric=False):
    """
    Evaluate Bessel function of the first kind J_n(x).

    Args:
        n_string (str): Order
        x_string (str): Argument

    Returns:
        str: Formatted result
    """
    n_success, n = parse_expression(n_string)
    if not n_success:
        return f"❌ n: {n}"

    x_success, x = parse_expression(x_string)
    if not x_success:
        return f"❌ x: {x}"

    try:
        result = besselj(n, x)

        output = "### Bessel Function (First Kind)\n\n"
        output += f"**Expression:** $J_{{{latex(n)}}}({latex(x)})$\n\n"
        output += f"**Result:** {to_latex(result)}\n"
        output += numeric_note(result, show_numeric)

        return output

    except Exception as e:
        return f"❌ Error evaluating Bessel J: {str(e)}"


def evaluate_bessely(n_string, x_string, show_numeric=False):
    """
    Evaluate Bessel function of the second kind Y_n(x).

    Args:
        n_string (str): Order
        x_string (str): Argument

    Returns:
        str: Formatted result
    """
    n_success, n = parse_expression(n_string)
    if not n_success:
        return f"❌ n: {n}"

    x_success, x = parse_expression(x_string)
    if not x_success:
        return f"❌ x: {x}"

    try:
        result = bessely(n, x)

        output = "### Bessel Function (Second Kind)\n\n"
        output += f"**Expression:** $Y_{{{latex(n)}}}({latex(x)})$\n\n"
        output += f"**Result:** {to_latex(result)}\n"
        output += numeric_note(result, show_numeric)

        return output

    except Exception as e:
        return f"❌ Error evaluating Bessel Y: {str(e)}"


def evaluate_besseli(n_string, x_string, show_numeric=False):
    """
    Evaluate modified Bessel function of the first kind I_n(x).

    Args:
        n_string (str): Order
        x_string (str): Argument

    Returns:
        str: Formatted result
    """
    n_success, n = parse_expression(n_string)
    if not n_success:
        return f"❌ n: {n}"

    x_success, x = parse_expression(x_string)
    if not x_success:
        return f"❌ x: {x}"

    try:
        result = besseli(n, x)

        output = "### Modified Bessel Function (First Kind)\n\n"
        output += f"**Expression:** $I_{{{latex(n)}}}({latex(x)})$\n\n"
        output += f"**Result:** {to_latex(result)}\n"
        output += numeric_note(result, show_numeric)

        return output

    except Exception as e:
        return f"❌ Error evaluating Bessel I: {str(e)}"


def evaluate_besselk(n_string, x_string, show_numeric=False):
    """
    Evaluate modified Bessel function of the second kind K_n(x).

    Args:
        n_string (str): Order
        x_string (str): Argument

    Returns:
        str: Formatted result
    """
    n_success, n = parse_expression(n_string)
    if not n_success:
        return f"❌ n: {n}"

    x_success, x = parse_expression(x_string)
    if not x_success:
        return f"❌ x: {x}"

    try:
        result = besselk(n, x)

        output = "### Modified Bessel Function (Second Kind)\n\n"
        output += f"**Expression:** $K_{{{latex(n)}}}({latex(x)})$\n\n"
        output += f"**Result:** {to_latex(result)}\n"
        output += numeric_note(result, show_numeric)

        return output

    except Exception as e:
        return f"❌ Error evaluating Bessel K: {str(e)}"


def evaluate_chebyshevt(n_string, x_string, show_numeric=False):
    """
    Evaluate Chebyshev polynomial of the first kind T_n(x).

    Args:
        n_string (str): Polynomial order
        x_string (str): Variable value

    Returns:
        str: Formatted result
    """
    n_success, n = parse_expression(n_string)
    if not n_success:
        return f"❌ n: {n}"

    x_success, x = parse_expression(x_string)
    if not x_success:
        return f"❌ x: {x}"

    try:
        result = chebyshevt(n, x)

        output = "### Chebyshev Polynomial (First Kind)\n\n"
        output += f"**Expression:** $T_{{{latex(n)}}}({latex(x)})$\n\n"
        output += f"**Result:** {to_latex(result)}\n"
        output += numeric_note(result, show_numeric)

        return output

    except Exception as e:
        return f"❌ Error evaluating Chebyshev T: {str(e)}"


def evaluate_chebyshevu(n_string, x_string, show_numeric=False):
    """
    Evaluate Chebyshev polynomial of the second kind U_n(x).

    Args:
        n_string (str): Polynomial order
        x_string (str): Variable value

    Returns:
        str: Formatted result
    """
    n_success, n = parse_expression(n_string)
    if not n_success:
        return f"❌ n: {n}"

    x_success, x = parse_expression(x_string)
    if not x_success:
        return f"❌ x: {x}"

    try:
        result = chebyshevu(n, x)

        output = "### Chebyshev Polynomial (Second Kind)\n\n"
        output += f"**Expression:** $U_{{{latex(n)}}}({latex(x)})$\n\n"
        output += f"**Result:** {to_latex(result)}\n"
        output += numeric_note(result, show_numeric)

        return output

    except Exception as e:
        return f"❌ Error evaluating Chebyshev U: {str(e)}"


def evaluate_assoc_legendre(n_string, m_string, x_string, show_numeric=False):
    """
    Evaluate associated Legendre polynomial P_n^m(x).

    Args:
        n_string (str): Degree
        m_string (str): Order
        x_string (str): Variable value

    Returns:
        str: Formatted result
    """
    n_success, n = parse_expression(n_string)
    if not n_success:
        return f"❌ n: {n}"

    m_success, m = parse_expression(m_string)
    if not m_success:
        return f"❌ m: {m}"

    x_success, x = parse_expression(x_string)
    if not x_success:
        return f"❌ x: {x}"

    try:
        result = assoc_legendre(n, m, x)

        output = "### Associated Legendre Polynomial\n\n"
        output += f"**Expression:** $P_{{{latex(n)}}}^{{{latex(m)}}}({latex(x)})$\n\n"
        output += f"**Result:** {to_latex(result)}\n"
        output += numeric_note(result, show_numeric)

        return output

    except Exception as e:
        return f"❌ Error evaluating associated Legendre: {str(e)}"


def evaluate_assoc_laguerre(n_string, alpha_string, x_string, show_numeric=False):
    """
    Evaluate associated Laguerre polynomial L_n^alpha(x).

    Args:
        n_string (str): Degree
        alpha_string (str): Parameter alpha
        x_string (str): Variable value

    Returns:
        str: Formatted result
    """
    n_success, n = parse_expression(n_string)
    if not n_success:
        return f"❌ n: {n}"

    alpha_success, alpha = parse_expression(alpha_string)
    if not alpha_success:
        return f"❌ alpha: {alpha}"

    x_success, x = parse_expression(x_string)
    if not x_success:
        return f"❌ x: {x}"

    try:
        result = assoc_laguerre(n, alpha, x)

        output = "### Associated Laguerre Polynomial\n\n"
        output += f"**Expression:** $L_{{{latex(n)}}}^{{{latex(alpha)}}}({latex(x)})$\n\n"
        output += f"**Result:** {to_latex(result)}\n"
        output += numeric_note(result, show_numeric)

        return output

    except Exception as e:
        return f"❌ Error evaluating associated Laguerre: {str(e)}"
