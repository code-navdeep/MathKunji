import pytest

from core.graphing import plot_2d, plot_3d, plot_parametric


def test_plot_2d_normal():
    fig, status = plot_2d(["sin(x)", "cos(x)"], -10, 10)
    assert fig is not None
    assert status.startswith("✓")


def test_plot_2d_constant_expression():
    """Regression for A4: a constant expression used to crash ax.plot()
    because lambdify returned a bare scalar instead of an array."""
    fig, status = plot_2d(["5"], -10, 10)
    assert fig is not None
    assert status.startswith("✓")


def test_plot_2d_mixed_valid_invalid_reports_both():
    """Regression for A5/D4: per-expression failures used to be print()ed
    to stdout only, invisible in the UI."""
    fig, status = plot_2d(["sin(x)", "((( invalid"], -10, 10)
    assert fig is not None
    assert "invalid" in status


def test_plot_2d_no_expressions():
    fig, status = plot_2d([], -10, 10)
    assert fig is None
    assert status.startswith("❌")


def test_plot_3d_normal():
    fig, status = plot_3d("x^2 + y^2", -5, 5, -5, 5, "x", "y")
    assert fig is not None
    assert status.startswith("✓")


def test_plot_3d_constant_expression():
    """Regression for A6: a constant expression used to crash plot_surface()."""
    fig, status = plot_3d("5", -5, 5, -5, 5, "x", "y")
    assert fig is not None
    assert status.startswith("✓")


def test_plot_parametric_normal():
    fig, status = plot_parametric("cos(t)", "sin(t)", 0, 6.28)
    assert fig is not None
    assert status.startswith("✓")


def test_plot_parametric_infers_non_t_variable():
    """Regression for D5: the parameter symbol used to be hardcoded to 't'."""
    fig, status = plot_parametric("cos(s)", "sin(s)", 0, 6.28)
    assert fig is not None
    assert status.startswith("✓")


def test_plot_parametric_mismatched_variables_reports_error():
    fig, status = plot_parametric("cos(s)", "sin(u)", 0, 6.28)
    assert fig is None
    assert status.startswith("❌")


def test_plot_3d_title_with_dollar_sign_does_not_crash():
    """Regression for D12: unescaped '$' in user input could break the
    matplotlib mathtext title parser."""
    fig, status = plot_3d("x^2", -5, 5, -5, 5, "x", "y")
    assert fig is not None


def test_plot_2d_accepts_expressions_mathtext_would_reject():
    """
    Regression: the legend label was built from the raw user string and handed
    to matplotlib's mathtext parser. Mathtext is not LaTeX, so "x^2^3" -- which
    SymPy parses happily -- raised "Double superscript" and killed the entire
    plot rather than just the label. Labels now render via sympy.latex().
    """
    fig, status = plot_2d(["x^2^3"], -2, 2)
    assert fig is not None, status
    assert status.startswith("✓")


@pytest.mark.parametrize("bounds", [
    (None, 10), (-10, None), ("", 10), ("abc", 10),
])
def test_plot_2d_reports_missing_or_bad_bounds(bounds):
    """
    Regression: a cleared gr.Number arrives as None, and the range check
    compared it with >=. The resulting TypeError escaped guarded() -- which
    only catches timeouts -- and surfaced as a raw Gradio error instead of the
    app's "❌ ..." convention.
    """
    fig, status = plot_2d(["sin(x)"], *bounds)
    assert fig is None
    assert status.startswith("❌")


def test_plot_3d_and_parametric_also_validate_bounds():
    assert plot_3d("x^2+y^2", -5, 5, None, 5, "x", "y")[1].startswith("❌")
    assert plot_parametric("cos(t)", "sin(t)", 0, None)[1].startswith("❌")


def test_plots_do_not_leak_figures():
    """
    Regression: figures were created through pyplot, which retains every one
    in a process-global registry that only plt.close() clears -- and nothing
    in the Gradio request path ever closed them. On a long-running container
    that grows without bound. Figures are now built straight from
    matplotlib.figure.Figure, so there is no registry entry to leak.

    This assertion is the only way to catch a regression: the leak raises
    nothing and changes no output, it just consumes memory.
    """
    import matplotlib.pyplot as plt

    plt.close("all")
    for _ in range(5):
        plot_2d(["sin(x)"], -10, 10)
        plot_3d("x^2 + y^2", -5, 5, -5, 5, "x", "y")
        plot_parametric("cos(t)", "sin(t)", 0, 6.28)
    assert plt.get_fignums() == [], (
        "plotting registered figures with pyplot; they will never be freed"
    )
