from core.algebra import (
    simplify_expression,
    expand_expression,
    factor_expression,
    solve_equation,
    evaluate_expression,
)


def assert_ok(result):
    assert not result.startswith("❌"), f"unexpected error: {result}"


def test_simplify():
    assert_ok(simplify_expression("sin(x)^2 + cos(x)^2"))


def test_expand():
    result = expand_expression("(x+1)*(x-1)")
    assert_ok(result)
    assert "x^{2}" in result or "x^2" in result


def test_factor():
    assert_ok(factor_expression("x^2 - 4"))


def test_solve_bare_expression_implicit_zero():
    result = solve_equation("x^2 - 4", "x")
    assert_ok(result)
    assert "-2" in result and "2" in result


def test_solve_accepts_equals_sign():
    """Regression for A2: Solve previously only accepted bare expr = 0."""
    result = solve_equation("x^2 - 1 = 2*x", "x")
    assert_ok(result)
    assert "sqrt" in result or "\\sqrt" in result


def test_solve_contradiction_uses_inline_latex():
    """Regression for A1: the empty-solution branch used to interpolate a raw
    sympy repr instead of LaTeX inside the markdown."""
    result = solve_equation("x - x + 1", "x")  # 1 = 0, never true
    assert_ok(result)
    assert "No solution" in result
    assert "never true" in result
    assert "$1$" in result


def test_solve_identity_is_not_reported_as_no_solution():
    """
    sympy.solve returns [] for an identity as well as for a genuinely
    unsolvable equation. "x = x" is true for every x -- the opposite of no
    solution -- so it must not be reported as one.
    """
    result = solve_equation("x = x", "x")
    assert_ok(result)
    assert "Identity" in result
    assert "every" in result


def test_solve_reports_missing_variable_distinctly():
    """
    Solving y^2-4 for x is not unsolvable; the variable just isn't there.
    The message should point at the Variable field rather than claim the
    equation has no solution.
    """
    result = solve_equation("y^2 - 4", "x")
    assert_ok(result)
    assert "does not appear" in result
    assert "$y$" in result


def test_evaluate_with_substitution():
    result = evaluate_expression("x^2 + 1", {"x": 2})
    assert_ok(result)
    assert "5" in result


def test_evaluate_simplify_result_false():
    """Regression for B8: simplify_result param controls post-sub simplification."""
    result = evaluate_expression("x^2 + 1", {"x": 2}, simplify_result=False)
    assert_ok(result)


def test_solve_invalid_expression_reports_error():
    result = solve_equation("((( invalid", "x")
    assert result.startswith("❌")
