"""
Input parsing utilities for safe mathematical expression handling.
"""

import ast
import re

from sympy import Matrix
from sympy.parsing.sympy_parser import (
    stringify_expr,
    eval_expr,
    standard_transformations,
    implicit_multiplication_application,
    convert_xor,
)

_TRANSFORMATIONS = (
    standard_transformations +
    (implicit_multiplication_application, convert_xor)
)

# The UI, the readme and the sidebar syntax footer all advertise lowercase 'e'
# as Euler's number, but SymPy only recognises capital 'E' -- left alone, 'e'
# becomes an ordinary Symbol and "e^x" silently means "some unknown e, raised
# to x" rather than exp(x). Rewrite a standalone 'e' before parsing.
#
# The word boundaries are what make this safe. There is no \b between the
# characters of "1e5", "theta", "exp", "erf" or "besselj", so none of those are
# touched -- only an 'e' that stands alone as its own token.
_EULER_E = re.compile(r'\be\b')

# Nodes a cleaned-up arithmetic expression can legitimately contain once
# SymPy's tokenizer has already turned "3x" into "3*x", "x^2" into "x**2",
# and bare names into Symbol('name') calls. Notably absent: ast.Attribute
# and ast.Subscript -- those are exactly the syntax a Python `eval` sandbox
# escape needs (e.g. `x.__class__.__base__.__subclasses__()[i]`), and
# ordinary math input never needs them.
_ALLOWED_NODE_TYPES = (
    ast.Expression, ast.Constant, ast.Name, ast.Load,
    ast.BinOp, ast.UnaryOp,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod, ast.FloorDiv,
    ast.UAdd, ast.USub,
    ast.Call,
)


# The complete set of names user input may reference or call.
#
# This is a hand-curated allowlist, NOT a filtered view of SymPy's exports.
# That distinction is the whole security property of this module: a
# `from sympy import *` namespace publishes ~918 public names, and three of
# them -- `sympify`, `S` and `parse_expr` -- are themselves eval-based
# re-parsers. Allowing those re-opens arbitrary code execution through the
# front door, because `sympify("<payload>")` is, to an AST walker, just an
# ordinary call to an allowed name; the danger only materialises when it
# evaluates and re-parses its string argument with Python's builtins in
# scope. Others in that namespace are independently unsafe -- `preview`
# shells out to external LaTeX tooling, `lambdify` compiles generated
# source, `var` injects into caller globals, `test`/`doctest` run suites.
#
# So the rule is: a name gets in only because this app's UI actually needs
# it. Adding a name here is a security decision -- if it can re-parse a
# string, compile code, touch the filesystem, or spawn a process, it does
# not belong, no matter how mathematical it looks.
_ALLOWED_NAMES = frozenset("""
    Symbol Function Integer Float Rational
    pi E I oo zoo nan EulerGamma GoldenRatio
    sin cos tan cot sec csc
    asin acos atan acot asec acsc atan2
    sinh cosh tanh coth asinh acosh atanh
    exp log ln sqrt cbrt root Abs sign floor ceiling Min Max
    gamma zeta factorial binomial erf erfc
    besselj bessely besseli besselk
    hermite legendre laguerre chebyshevt chebyshevu
    assoc_legendre assoc_laguerre
""".split())


def _build_safe_global_dict():
    """
    Build the evaluation namespace: exactly ``_ALLOWED_NAMES``, nothing else.

    Two independent things are being defended against here.

    First, SymPy's own ``parse_expr`` -- when not given an explicit
    ``global_dict`` -- merges every Python builtin function (``eval``,
    ``exec``, ``open``, ``__import__``, ...) into the namespace it evaluates
    against, because those are all instances of ``types.BuiltinFunctionType``.
    We never let that happen: we build the namespace ourselves and neutralise
    the ``__builtins__`` key that ``exec`` leaves behind.

    Second -- and this is what a filtered ``import *`` got wrong -- the
    namespace is restricted to the curated allowlist rather than all of
    SymPy. That way the AST gate in ``_assert_safe_ast`` is not the only
    thing standing between user input and a dangerous callable: even if a
    name somehow reached evaluation, there is nothing here for it to bind to.
    """
    full = {}
    exec('from sympy import *', full)

    # Fail loudly at import time if a SymPy upgrade renames or drops
    # something we allow, rather than silently losing a function that users
    # rely on and only finding out via a confusing parse error at runtime.
    missing = sorted(name for name in _ALLOWED_NAMES if name not in full)
    if missing:
        raise ImportError(
            "utils.parser allowlist references names that this version of "
            f"SymPy does not export: {', '.join(missing)}"
        )

    namespace = {name: full[name] for name in _ALLOWED_NAMES}
    namespace['__builtins__'] = {}
    return namespace


_SAFE_GLOBAL_DICT = _build_safe_global_dict()

# Names and calls are gated against the same set. 'Symbol' is in it because
# SymPy's auto_symbol transform rewrites bare undefined names like "x" into
# `Symbol('x')` calls before we ever see the source, and 'Integer'/'Float'/
# 'Rational' are in it because auto_number does the same for numeric
# literals.
_ALLOWED_CALL_NAMES = _ALLOWED_NAMES


class UnsafeExpressionError(Exception):
    """Raised when an expression contains disallowed syntax."""


def _assert_safe_ast(source):
    try:
        tree = ast.parse(source, mode='eval')
    except SyntaxError as e:
        raise UnsafeExpressionError(str(e))

    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_NODE_TYPES):
            raise UnsafeExpressionError(f"disallowed syntax ({type(node).__name__})")

        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise UnsafeExpressionError("only direct function calls are allowed")
            if node.func.id not in _ALLOWED_CALL_NAMES:
                raise UnsafeExpressionError(f"function not allowed: {node.func.id}")
            if node.keywords:
                raise UnsafeExpressionError("keyword arguments are not allowed")

        if isinstance(node, ast.Name) and node.id not in _ALLOWED_CALL_NAMES:
            raise UnsafeExpressionError(f"unknown identifier: {node.id}")

    return tree


def _safe_eval(source):
    """Validate ``source`` against the AST whitelist, then evaluate it."""
    _assert_safe_ast(source)
    code = compile(source, '<string>', 'eval')
    return eval_expr(code, {}, _SAFE_GLOBAL_DICT)


def parse_expression(expr_string):
    """
    Safely parse a mathematical expression string into a SymPy expression.

    Args:
        expr_string (str): The expression string to parse

    Returns:
        tuple: (success: bool, result: sympy.Expr or error_message: str)

    Examples:
        >>> parse_expression("x^2 + 3*x + 2")
        (True, x**2 + 3*x + 2)

        >>> parse_expression("invalid{{}")
        (False, "Error parsing expression: ...")
    """
    if not expr_string or not expr_string.strip():
        return False, "Empty expression"

    try:
        # Clean up the input
        expr_clean = expr_string.strip()

        # Replace common notations
        expr_clean = expr_clean.replace('^', '**')  # x^2 -> x**2
        expr_clean = expr_clean.replace('×', '*')   # × -> *
        expr_clean = expr_clean.replace('÷', '/')   # ÷ -> /
        expr_clean = _EULER_E.sub('E', expr_clean)  # e -> E (Euler's number)

        # Apply SymPy's tokenizer transformations (implicit multiplication,
        # auto-symbol, etc.) to get plain, explicit Python source, then run
        # that source through our own AST whitelist before evaluating it.
        transformed = stringify_expr(expr_clean, {}, _SAFE_GLOBAL_DICT, _TRANSFORMATIONS)
        result = _safe_eval(transformed)
        return True, result

    except UnsafeExpressionError as e:
        return False, f"Error parsing expression: {e}"
    except (ValueError, TypeError, SyntaxError) as e:
        return False, f"Error parsing expression: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"


def parse_matrix(matrix_string):
    """
    Parse a matrix from string representation.

    Accepts formats like:
    - "[[1, 2], [3, 4]]"
    - "Matrix([[1, 2], [3, 4]])"

    Args:
        matrix_string (str): The matrix string to parse

    Returns:
        tuple: (success: bool, result: sympy.Matrix or error_message: str)
    """
    if not matrix_string or not matrix_string.strip():
        return False, "Empty matrix input"

    matrix_clean = matrix_string.strip()

    # Accept an optional Matrix(...) wrapper without ever handing the raw
    # string to sympify -- unwrap it and parse the inner list literal
    # ourselves instead.
    if matrix_clean.startswith('Matrix(') and matrix_clean.endswith(')'):
        matrix_clean = matrix_clean[len('Matrix('):-1].strip()

    try:
        tree = ast.parse(matrix_clean, mode='eval')
    except SyntaxError as e:
        return False, f"Error parsing matrix: {str(e)}"

    body = tree.body
    if not isinstance(body, ast.List) or not all(
        isinstance(row, ast.List) for row in body.elts
    ):
        return False, "Input is not a valid matrix: expected a list of lists, e.g. [[1, 2], [3, 4]]"

    rows = []
    for row_node in body.elts:
        row_values = []
        for cell_node in row_node.elts:
            cell_source = ast.unparse(cell_node)
            success, value = parse_expression(cell_source)
            if not success:
                return False, f"Error parsing matrix cell '{cell_source}': {value}"
            row_values.append(value)
        rows.append(row_values)

    try:
        result = Matrix(rows)
    except Exception as e:
        return False, f"Error parsing matrix: {str(e)}"

    return True, result


def validate_variable(var_string):
    """
    Validate that a string represents a valid variable name.

    Args:
        var_string (str): The variable string to validate

    Returns:
        tuple: (success: bool, result: sympy.Symbol or error_message: str)
    """
    from sympy import Symbol

    if not var_string or not var_string.strip():
        return False, "Empty variable name"

    var_clean = var_string.strip()

    # Check if it's a valid Python identifier
    if not var_clean.isidentifier():
        return False, f"Invalid variable name: {var_clean}"

    try:
        symbol = Symbol(var_clean)
        return True, symbol
    except Exception as e:
        return False, f"Error creating symbol: {str(e)}"
