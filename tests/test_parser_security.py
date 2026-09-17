"""
Regression tests for the AST-whitelist gate in utils/parser.py.

utils/parser.py previously fed user input straight into SymPy's eval-based
sympify()/parse_expr() with no sandboxing -- a confirmed remote-code-
execution vector reachable from every tab in the app (verified during the
2026-07-09 audit: a payload typed into the Algebra expression box, or the
Matrix box, executed real shell commands). These tests exist so that any
future change to utils/parser.py that reopens that hole fails CI
immediately, rather than being caught by a human re-reading the code.
"""

import pytest

from utils.parser import (
    parse_expression,
    parse_matrix,
    validate_variable,
    _ALLOWED_NAMES,
    _SAFE_GLOBAL_DICT,
)


ATTACK_PAYLOADS_EXPRESSION = [
    "().__class__.__base__.__subclasses__()",
    "(1).__class__.__mro__[0].__subclasses__()",
    "__import__('os').getcwd()",
    "eval('2+2')",
    "open('/etc/passwd').read()",
    "().__class__.__base__.__subclasses__()[0]('id', shell=True, stdout=-1)",
    # Re-parser bypass. These defeated the previous gate completely: the
    # allowlist was generated from every public name in `from sympy import *`,
    # which includes sympify/S/parse_expr -- all eval-based parsers. To an AST
    # walker `sympify("...")` is an ordinary call to an allowed name, so it
    # passed; the payload only executed once sympify re-parsed its string
    # argument with Python's builtins back in scope. Confirmed live: this
    # returned the real working directory before the fix.
    "sympify(\"__import__('os').getcwd()\")",
    "S(\"__import__('os').getcwd()\")",
    "parse_expr(\"__import__('os').getcwd()\")",
    "sympify(\"open('/etc/passwd').read()\")",
    "sympify(\"().__class__.__base__.__subclasses__()\")",
]

# Names that must never be reachable from user input, with the reason each is
# dangerous. Some of these no longer parse as calls at all (SymPy's tokenizer
# splits an unknown multi-letter name into a product of single-letter symbols,
# so "preview(1)" becomes the inert expression p*r*e*v*i*e*w*1). That inertness
# is a side effect, not the guarantee -- the guarantee is that the real
# callable is absent from the evaluation namespace, which is what this asserts.
FORBIDDEN_SYMPY_NAMES = [
    "sympify",       # eval-based re-parser
    "S",             # eval-based re-parser (sympify alias)
    "parse_expr",    # eval-based re-parser
    "preview",       # shells out to external LaTeX/dvipng tooling
    "lambdify",      # compiles generated source
    "var",           # injects names into caller globals
    "test",          # runs the SymPy test suite
    "doctest",       # runs doctests
    "init_session",  # starts an interactive session
    "init_printing",
    "source",        # reads and prints source files
]

ATTACK_PAYLOADS_MATRIX = [
    "().__class__.__base__.__subclasses__()",
    "().__class__.__base__.__subclasses__()[0](['id'])",
]


@pytest.mark.parametrize("payload", ATTACK_PAYLOADS_EXPRESSION)
def test_parse_expression_rejects_sandbox_escapes(payload):
    success, result = parse_expression(payload)
    assert success is False, f"payload should have been rejected: {payload!r} -> {result!r}"


@pytest.mark.parametrize("payload", ATTACK_PAYLOADS_MATRIX)
def test_parse_matrix_rejects_sandbox_escapes(payload):
    success, result = parse_matrix(payload)
    assert success is False, f"payload should have been rejected: {payload!r} -> {result!r}"


LEGITIMATE_EXPRESSIONS = [
    "x^2 + 3*x + 2",
    "3x",
    "2(x+1)",
    # Implicit multiplication where the left operand is a single-letter name.
    # SymPy's auto_symbol rewrites "x(" into a Function(...) call, so these
    # only survive because 'Function' is on the allowlist. Narrowing the list
    # without it silently broke all of these -- they are here to catch that.
    "x(x+1)",
    "y(y-1)",
    "t(t+1)",
    "a(b+c)",
    "sin(x)^2 + cos(x)^2",
    "5!",
    "exp(-x^2)",
    "sqrt(x)",
    "pi",
    "oo",
    "gamma(5)",
    "besselj(2, x)",
    "assoc_legendre(2, 1, x)",
    "a*b",
    "1e5",
    "-2.5",
    "2/3",
]


@pytest.mark.parametrize("expr", LEGITIMATE_EXPRESSIONS)
def test_parse_expression_accepts_legitimate_math(expr):
    success, result = parse_expression(expr)
    assert success is True, f"legitimate expression rejected: {expr!r} -> {result!r}"


LEGITIMATE_MATRICES = [
    "[[1, 2], [3, 4]]",
    "Matrix([[1, 2], [3, 4]])",
    "[[1, 2, 3], [4, 5, 6], [7, 8, 9]]",
    "[[x, y], [1, 2]]",
]


@pytest.mark.parametrize("matrix_str", LEGITIMATE_MATRICES)
def test_parse_matrix_accepts_legitimate_matrices(matrix_str):
    success, result = parse_matrix(matrix_str)
    assert success is True, f"legitimate matrix rejected: {matrix_str!r} -> {result!r}"


@pytest.mark.parametrize("name", FORBIDDEN_SYMPY_NAMES)
def test_forbidden_names_absent_from_evaluation_namespace(name):
    """
    The evaluation namespace must not contain any callable that can re-parse a
    string, compile code, touch the filesystem or spawn a process.

    This is the load-bearing assertion of the whole module. The AST allowlist
    is the first gate, but it only inspects syntax -- if a dangerous name were
    reachable, a call to it would look perfectly ordinary. Keeping the
    namespace itself curated means there is nothing to bind to even if a name
    slipped through.
    """
    assert name not in _SAFE_GLOBAL_DICT, (
        f"{name!r} is reachable from user input -- see FORBIDDEN_SYMPY_NAMES "
        f"for why that is unsafe"
    )
    assert name not in _ALLOWED_NAMES


def test_allowlist_is_curated_not_generated():
    """
    Guards the exact mistake that caused the vulnerability.

    The original allowlist was built with a comprehension over
    `from sympy import *`, which admits ~918 names including three eval-based
    parsers. Any future change that goes back to generating the list will blow
    past this bound and fail here.
    """
    full = {}
    exec("from sympy import *", full)
    assert _ALLOWED_NAMES <= set(full), "allowlist references names SymPy does not export"
    assert len(_ALLOWED_NAMES) < 100, (
        f"allowlist has grown to {len(_ALLOWED_NAMES)} names -- it is meant to be a "
        f"hand-curated set of what the UI needs, not a filtered view of SymPy"
    )


def test_parse_expression_empty_input():
    success, result = parse_expression("")
    assert success is False


def test_validate_variable_rejects_non_identifier():
    success, result = validate_variable("1x")
    assert success is False
