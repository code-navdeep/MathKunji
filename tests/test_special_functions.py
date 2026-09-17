from core.special_functions import (
    evaluate_gamma,
    evaluate_zeta,
    evaluate_factorial,
    evaluate_binomial,
    evaluate_hermite,
    evaluate_legendre,
    evaluate_laguerre,
    evaluate_erf,
    evaluate_erfc,
    evaluate_besselj,
    evaluate_bessely,
    evaluate_besseli,
    evaluate_besselk,
    evaluate_chebyshevt,
    evaluate_chebyshevu,
    evaluate_assoc_legendre,
    evaluate_assoc_laguerre,
)


def assert_ok(result):
    assert not result.startswith("❌"), f"unexpected error: {result}"


def test_gamma():
    result = evaluate_gamma("5")
    assert_ok(result)
    assert "24" in result


def test_zeta():
    assert_ok(evaluate_zeta("2"))


def test_factorial():
    result = evaluate_factorial("5")
    assert_ok(result)
    assert "120" in result


def test_binomial():
    assert_ok(evaluate_binomial("5", "2"))


def test_erf():
    assert_ok(evaluate_erf("x"))


def test_erfc():
    assert_ok(evaluate_erfc("x"))


def test_besselj():
    assert_ok(evaluate_besselj("2", "x"))


def test_bessely():
    assert_ok(evaluate_bessely("2", "x"))


def test_besseli():
    assert_ok(evaluate_besseli("2", "x"))


def test_besselk():
    assert_ok(evaluate_besselk("2", "x"))


def test_hermite():
    assert_ok(evaluate_hermite("3", "x"))


def test_legendre():
    assert_ok(evaluate_legendre("2", "x"))


def test_laguerre():
    assert_ok(evaluate_laguerre("2", "x"))


def test_chebyshevt():
    assert_ok(evaluate_chebyshevt("2", "x"))


def test_chebyshevu():
    assert_ok(evaluate_chebyshevu("2", "x"))


def test_assoc_legendre():
    assert_ok(evaluate_assoc_legendre("2", "1", "x"))


def test_assoc_laguerre():
    assert_ok(evaluate_assoc_laguerre("2", "1", "x"))
