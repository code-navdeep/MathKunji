"""
LaTeX formatting utilities for mathematical expressions.
"""

import re

from sympy import latex

# Display math ($$...$$) and inline math ($...$). The inline pattern excludes
# '$' from the body so it cannot swallow a neighbouring delimiter and match
# across two separate expressions.
_DISPLAY_MATH = re.compile(r'\$\$(.+?)\$\$', re.DOTALL)
_INLINE_MATH = re.compile(r'(?<!\$)\$([^$]+?)\$(?!\$)')

# Heading that core/steps.py puts in front of step-by-step working. Everything
# from here on is intermediate working rather than the result -- see
# extract_latex().
STEPS_MARKER = "**Steps:**"


def to_latex(expr):
    """
    Convert a SymPy expression to LaTeX format for beautiful rendering.

    Args:
        expr: A SymPy expression

    Returns:
        str: LaTeX-formatted string wrapped in $$ for display
    """
    try:
        latex_str = latex(expr)
        # Wrap in display math mode for Gradio
        return f"$${latex_str}$$"
    except Exception as e:
        return f"Error formatting LaTeX: {str(e)}"


def to_latex_inline(expr):
    """
    Convert a SymPy expression to LaTeX wrapped for inline math ($...$).

    Unlike to_latex(), which always wraps in display-mode ($$...$$), this
    is for embedding a sub-expression inside a larger line of text/markdown.

    Args:
        expr: A SymPy expression

    Returns:
        str: LaTeX-formatted string wrapped in single $ for inline display
    """
    try:
        return f"${latex(expr)}$"
    except Exception as e:
        return f"Error formatting LaTeX: {str(e)}"


def numeric_note(expr, show=True, digits=10):
    """
    Render a decimal value alongside an exact symbolic result.

    An exact answer like $\\zeta(3)$ or $\\Gamma(5/2)$ is correct but unreadable
    -- someone checking a value against a textbook or a calculator cannot use
    it. This adds the decimal underneath.

    Returns "" whenever there is nothing worth adding: the toggle is off, the
    expression still has free symbols (so no single number exists), evalf
    cannot produce a finite number, or the decimal is just a restatement of
    what is already displayed.

    Args:
        expr: A SymPy expression (the result being displayed)
        show (bool): Whether the caller asked for the numeric value
        digits (int): Significant digits to show

    Returns:
        str: A "**Numeric:** ..." markdown line, or "".
    """
    if not show:
        return ""

    try:
        if getattr(expr, "free_symbols", None):
            return ""
        # An exact result that is already a plain integer or decimal needs no
        # translation -- factorial(5) would otherwise print "120" and then
        # "120.0", and gamma(2.5) would restate the decimal it already gave.
        # Rationals are kept: 1/3 -> 0.3333333333 does add something.
        if getattr(expr, "is_Integer", False) or getattr(expr, "is_Float", False):
            return ""
        value = expr.evalf(digits)
        if not value.is_number or not value.is_finite:
            return ""
        rendered = latex(value)
        # Nothing gained if the exact form was already this decimal.
        if rendered == latex(expr):
            return ""
        return f"\n**Numeric:** ${rendered}$\n"
    except Exception:
        # A numeric value is a convenience; never let it break the result.
        return ""


def extract_latex(markdown):
    """
    Pull the result's raw LaTeX back out of a rendered markdown block.

    The "Copy LaTeX" button needs the bare LaTeX, but core/* functions return
    a finished markdown block with the maths already wrapped in delimiters --
    and changing all ~40 of them to return the two separately would break the
    contract every function in core/ keeps: strings in, finished markdown out.
    So this recovers it from the output instead.

    Scans for the LAST line that contains any maths and returns everything on
    it, because every template here puts the answer on the final maths-bearing
    line ("**Result:**", "**Solutions:**", the last eigenvalue bullet, ...).

    Simply preferring the last display-math block does not work, and both
    counter-examples are real output from this app:

      * matrix_eigenvalues puts the input matrix in $$...$$ and the actual
        eigenvalues in inline $...$ *after* it, so "last display block"
        returned the input rather than the answer.
      * solve_equation writes "**Solutions:** $-2$, $2$" -- several inline
        blocks on one line -- so taking a single block silently dropped a root.

    Args:
        markdown (str): A rendered result block from core/*.

    Returns:
        str: The LaTeX source without delimiters, or "" if there is none.
    """
    if not markdown:
        return ""

    # Step-by-step working is appended after the result, so with it enabled the
    # last maths-bearing line is an intermediate step rather than the answer --
    # Copy LaTeX was returning a sub-derivative from the middle of the working.
    # Steps are supplementary, so they are not part of "the result".
    steps_marker = markdown.find(STEPS_MARKER)
    if steps_marker != -1:
        markdown = markdown[:steps_marker]

    for line in reversed(markdown.splitlines()):
        blocks = [b.strip() for b in _DISPLAY_MATH.findall(line)]
        if not blocks:
            blocks = [b.strip() for b in _INLINE_MATH.findall(line)]
        blocks = [b for b in blocks if b]
        if blocks:
            return ", ".join(blocks)

    return ""


def format_step_by_step(original, result, operation):
    """
    Format a step-by-step solution display.

    Args:
        original: Original expression
        result: Result expression
        operation (str): Description of the operation

    Returns:
        str: Formatted step-by-step solution
    """
    try:
        output = f"### {operation}\n\n"
        output += f"**Input:**  {to_latex(original)}\n\n"
        output += f"**Result:**  {to_latex(result)}\n"
        return output
    except Exception as e:
        return f"Error formatting steps: {str(e)}"
