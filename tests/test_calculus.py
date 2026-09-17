from core.calculus import (
    calculate_derivative,
    calculate_integral,
    calculate_limit,
    taylor_series,
)


def assert_ok(result):
    assert not result.startswith("❌"), f"unexpected error: {result}"


def test_derivative_first_order():
    result = calculate_derivative("x^3", "x", 1)
    assert_ok(result)
    assert "3" in result


def test_indefinite_integral_includes_constant():
    result = calculate_integral("x^2", "x")
    assert_ok(result)
    assert "C" in result


def test_definite_integral():
    result = calculate_integral("x^2", "x", definite=True, lower="0", upper="1")
    assert_ok(result)
    assert "frac{1}{3}" in result


def test_limit_at_zero():
    result = calculate_limit("sin(x)/x", "x", "0", "+")
    assert_ok(result)


def test_limit_at_infinity():
    result = calculate_limit("1/x", "x", "oo", "+")
    assert_ok(result)


def test_taylor_series():
    result = taylor_series("exp(x)", "x", "0", 3)
    assert_ok(result)


def test_derivative_invalid_expression():
    result = calculate_derivative("((( invalid", "x", 1)
    assert result.startswith("❌")
