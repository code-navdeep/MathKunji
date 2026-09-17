"""
Tests for core/steps.py.

These check that the right RULE is named for each shape of expression, not just
that some output came back -- the whole value of the feature is telling a
student which rule applies where, so "it returned a string" is not evidence
that it works.
"""

from core.steps import (
    MAX_DEPTH,
    MAX_STEPS,
    derivative_steps,
    integral_steps_markdown,
)


def assert_ok(result):
    assert not result.startswith("❌"), f"unexpected error: {result}"


# --------------------------------------------------------------------------
# Derivatives
# --------------------------------------------------------------------------

def test_derivative_names_the_power_rule():
    result = derivative_steps("x^3", "x")
    assert_ok(result)
    assert "Power rule" in result


def test_derivative_names_the_product_rule_and_recurses():
    result = derivative_steps("x^2*sin(x)", "x")
    assert_ok(result)
    assert "Product rule" in result
    # The sub-derivatives of both factors should appear underneath.
    assert "Power rule" in result
    assert "sin" in result


def test_derivative_names_the_chain_rule():
    result = derivative_steps("sin(x^2)", "x")
    assert_ok(result)
    assert "Chain rule" in result


def test_derivative_names_the_sum_rule():
    result = derivative_steps("3*x^2 + 2*x", "x")
    assert_ok(result)
    assert "Sum rule" in result


def test_derivative_names_the_constant_multiple_rule():
    result = derivative_steps("3*x^2", "x")
    assert_ok(result)
    assert "Constant multiple rule" in result


def test_derivative_of_a_constant_says_so():
    result = derivative_steps("5", "x")
    assert_ok(result)
    assert "does not contain" in result


def test_derivative_steps_reject_invalid_input():
    assert derivative_steps("((( invalid", "x").startswith("❌")
    assert derivative_steps("x^2", "1x").startswith("❌")


def test_derivative_steps_are_bounded():
    """
    A deeply nested expression must not produce unbounded output -- this runs
    inside the same timeout budget as every other operation.
    """
    nested = "sin(cos(sin(cos(sin(cos(x))))))"
    result = derivative_steps(nested, "x")
    assert_ok(result)
    assert result.count("- **") <= MAX_STEPS


# --------------------------------------------------------------------------
# Integrals
# --------------------------------------------------------------------------

def test_integral_names_the_power_rule():
    result = integral_steps_markdown("x^2", "x")
    assert_ok(result)
    assert "Power rule" in result


def test_integral_names_integration_by_parts():
    result = integral_steps_markdown("x*sin(x)", "x")
    assert_ok(result)
    assert "Integration by parts" in result


def test_integral_names_the_sum_rule_and_recurses():
    result = integral_steps_markdown("x^2 + 3*x + 1", "x")
    assert_ok(result)
    assert "Sum rule" in result
    assert "Power rule" in result
    assert "Constant multiple rule" in result


def test_integral_shows_the_running_result():
    """Each step should show what that rule produces, not just its name."""
    result = integral_steps_markdown("x^2", "x")
    assert "\\frac{x^{3}}{3}" in result


def test_integral_steps_reject_invalid_input():
    assert integral_steps_markdown("((( invalid", "x").startswith("❌")


def test_unknown_rule_names_degrade_readably():
    """
    The rule-name table is a convenience, not a whitelist -- a SymPy upgrade
    that introduces a new rule class should still render a readable label
    rather than raising.
    """
    from core.steps import _humanise_rule

    class SomeNewFancyRule:
        pass

    assert _humanise_rule(SomeNewFancyRule()) == "Some new fancy"
