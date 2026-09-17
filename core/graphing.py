"""
Graphing utilities for 2D and 3D plotting.

Figures are built directly from ``matplotlib.figure.Figure`` rather than
through ``pyplot``. pyplot keeps every figure it creates in a process-global
registry that only ``plt.close()`` clears, and nothing in the Gradio request
path ever closed them -- so each plot leaked a figure for the lifetime of the
process, which matters for a container running under ``restart: unless-stopped``.
Bypassing pyplot means there is no registry entry to leak in the first place.
The 3d projection and ``fig.colorbar`` both work without pyplot ever being
imported.
"""

import numpy as np
from matplotlib.figure import Figure
from sympy import Symbol, lambdify, latex

from utils.parser import parse_expression


def _as_float(value, label):
    """
    Coerce a numeric field from the UI into a float.

    Gradio sends ``None`` for a ``gr.Number`` the user has cleared, and the
    range checks below use ``>=``, which raises ``TypeError`` against ``None``.
    That exception escaped ``guarded()`` in app.py -- it only catches
    ``ComputationTimeoutError`` -- and surfaced as a raw Gradio error instead
    of the usual "❌ ..." message this app returns for every other failure.

    Returns (float, None) on success or (None, error_message) on failure.
    """
    if value is None or (isinstance(value, str) and not value.strip()):
        return None, f"❌ {label} is empty — please enter a number"
    try:
        return float(value), None
    except (TypeError, ValueError):
        return None, f"❌ {label} must be a number (got {value!r})"


def _math_label(expr, fallback):
    """
    Build a matplotlib-safe label from an already-parsed expression.

    The raw user string must never reach matplotlib's mathtext parser. Mathtext
    resembles LaTeX but is not the same grammar, so input that SymPy accepts
    can be fatal to it: ``x^2^3`` parses fine as SymPy but makes mathtext raise
    "Double superscript", which took down the whole plot rather than just the
    label. Rendering through ``sympy.latex()`` always produces mathtext-valid
    output. If that somehow fails we drop the ``$`` delimiters entirely so
    mathtext is never entered at all.
    """
    try:
        return f'${latex(expr)}$'
    except Exception:
        return str(fallback).replace('$', '')


def plot_2d(expressions_list, x_min=-10, x_max=10, num_points=1000):
    """
    Plot one or more 2D functions.

    Args:
        expressions_list (list): List of expression strings to plot
        x_min (float): Minimum x value
        x_max (float): Maximum x value
        num_points (int): Number of points to plot

    Returns:
        tuple: (matplotlib.figure.Figure, str) - figure and status message
    """
    if not expressions_list or all(not (expr or "").strip() for expr in expressions_list):
        return None, "❌ No expressions provided"

    x_min, error = _as_float(x_min, "x min")
    if error:
        return None, error
    x_max, error = _as_float(x_max, "x max")
    if error:
        return None, error
    if x_min >= x_max:
        return None, "❌ x_min must be less than x_max"

    try:
        fig = Figure(figsize=(10, 6))
        ax = fig.add_subplot(111)

        x = Symbol('x')
        x_vals = np.linspace(x_min, x_max, num_points)

        plotted = 0
        failures = []
        for expr_string in expressions_list:
            if not expr_string or not expr_string.strip():
                continue

            success, expr = parse_expression(expr_string)
            if not success:
                failures.append(f"{expr_string}: {expr}")
                continue

            try:
                if x in expr.free_symbols:
                    f = lambdify(x, expr, modules=['numpy'])
                    y_vals = f(x_vals)
                else:
                    # Constant w.r.t. x -- broadcast instead of a bare
                    # scalar, which ax.plot() can't pair with x_vals.
                    y_vals = np.full_like(x_vals, float(expr))
                ax.plot(x_vals, y_vals, label=_math_label(expr, expr_string), linewidth=2)
                plotted += 1
            except Exception as e:
                failures.append(f"{expr_string}: {e}")
                continue

        if plotted == 0:
            detail = f" ({'; '.join(failures)})" if failures else ""
            return None, f"❌ No valid expressions could be plotted{detail}"

        ax.grid(True, alpha=0.3)
        ax.axhline(y=0, color='k', linewidth=0.5)
        ax.axvline(x=0, color='k', linewidth=0.5)
        ax.set_xlabel('x', fontsize=12)
        ax.set_ylabel('y', fontsize=12)
        ax.legend()
        ax.set_title('2D Plot', fontsize=14, fontweight='bold')

        fig.tight_layout()

        status = f"✓ Successfully plotted {plotted} function(s)"
        if failures:
            status += " — ⚠ failed: " + "; ".join(failures)
        return fig, status

    except Exception as e:
        return None, f"❌ Error creating plot: {str(e)}"


def plot_3d(expr_string, x_min=-5, x_max=5, y_min=-5, y_max=5, x_var="x", y_var="y", num_points=100):
    """
    Plot a 3D surface.

    Args:
        expr_string (str): Expression in terms of specified variables
        x_min (float): Minimum x value
        x_max (float): Maximum x value
        y_min (float): Minimum y value
        y_max (float): Maximum y value
        x_var (str): Variable name for x-axis
        y_var (str): Variable name for y-axis
        num_points (int): Number of points per axis

    Returns:
        tuple: (matplotlib.figure.Figure, str) - figure and status message
    """
    if not expr_string or not expr_string.strip():
        return None, "❌ No expression provided"

    x_min, error = _as_float(x_min, "x min")
    if error:
        return None, error
    x_max, error = _as_float(x_max, "x max")
    if error:
        return None, error
    y_min, error = _as_float(y_min, "y min")
    if error:
        return None, error
    y_max, error = _as_float(y_max, "y max")
    if error:
        return None, error
    if x_min >= x_max:
        return None, "❌ x_min must be less than x_max"
    if y_min >= y_max:
        return None, "❌ y_min must be less than y_max"

    try:
        success, expr = parse_expression(expr_string)
        if not success:
            return None, f"❌ {expr}"

        # Create symbols from user-specified variable names
        x_sym = Symbol(x_var.strip() if x_var else 'x')
        y_sym = Symbol(y_var.strip() if y_var else 'y')

        # Create mesh grid
        x_vals = np.linspace(x_min, x_max, num_points)
        y_vals = np.linspace(y_min, y_max, num_points)
        X, Y = np.meshgrid(x_vals, y_vals)

        if expr.free_symbols:
            # Convert to numerical function
            f = lambdify((x_sym, y_sym), expr, modules=['numpy'])
            Z = f(X, Y)
        else:
            # Constant expression -- broadcast instead of a bare scalar,
            # which ax.plot_surface() can't pair with the meshgrid.
            Z = np.full_like(X, float(expr))

        # Create 3D plot
        fig = Figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')

        surf = ax.plot_surface(X, Y, Z, cmap='viridis', alpha=0.8)

        ax.set_xlabel(x_var, fontsize=12)
        ax.set_ylabel(y_var, fontsize=12)
        ax.set_zlabel('z', fontsize=12)
        ax.set_title(
            f'3D Plot: {_math_label(expr, expr_string)}',
            fontsize=14, fontweight='bold',
        )

        fig.colorbar(surf, shrink=0.5, aspect=5)

        fig.tight_layout()

        return fig, "✓ Successfully created 3D plot"

    except Exception as e:
        return None, f"❌ Error creating 3D plot: {str(e)}"


def plot_parametric(x_expr, y_expr, t_min=0, t_max=10, num_points=1000):
    """
    Plot a parametric curve.

    Args:
        x_expr (str): Expression for x(t)
        y_expr (str): Expression for y(t)
        t_min (float): Minimum t value
        t_max (float): Maximum t value
        num_points (int): Number of points

    Returns:
        tuple: (matplotlib.figure.Figure, str) - figure and status message
    """
    if not x_expr or not y_expr:
        return None, "❌ Both x and y expressions required"

    t_min, error = _as_float(t_min, "t min")
    if error:
        return None, error
    t_max, error = _as_float(t_max, "t max")
    if error:
        return None, error
    if t_min >= t_max:
        return None, "❌ t_min must be less than t_max"

    try:
        # Parse expressions
        x_success, x_parsed = parse_expression(x_expr)
        if not x_success:
            return None, f"❌ X expression: {x_parsed}"

        y_success, y_parsed = parse_expression(y_expr)
        if not y_success:
            return None, f"❌ Y expression: {y_parsed}"

        # Infer the shared parameter symbol from whichever variable the
        # expressions actually use, instead of assuming 't'.
        combined_free = x_parsed.free_symbols | y_parsed.free_symbols
        if len(combined_free) > 1:
            names = ', '.join(sorted(str(s) for s in combined_free))
            return None, f"❌ x(t) and y(t) must use the same single variable (found: {names})"

        t = combined_free.pop() if combined_free else Symbol('t')

        # Convert to numerical functions
        x_func = lambdify(t, x_parsed, modules=['numpy'])
        y_func = lambdify(t, y_parsed, modules=['numpy'])

        # Generate values
        t_vals = np.linspace(t_min, t_max, num_points)
        x_vals = x_func(t_vals)
        y_vals = y_func(t_vals)
        if not isinstance(x_vals, np.ndarray):
            x_vals = np.full_like(t_vals, float(x_vals))
        if not isinstance(y_vals, np.ndarray):
            y_vals = np.full_like(t_vals, float(y_vals))

        # Create plot
        fig = Figure(figsize=(10, 8))
        ax = fig.add_subplot(111)
        ax.plot(x_vals, y_vals, linewidth=2)

        ax.grid(True, alpha=0.3)
        ax.axhline(y=0, color='k', linewidth=0.5)
        ax.axvline(x=0, color='k', linewidth=0.5)
        ax.set_xlabel('x', fontsize=12)
        ax.set_ylabel('y', fontsize=12)
        ax.set_title(
            f'Parametric Plot: x(t)={_math_label(x_parsed, x_expr)}, '
            f'y(t)={_math_label(y_parsed, y_expr)}',
            fontsize=14, fontweight='bold',
        )
        ax.set_aspect('equal')

        fig.tight_layout()

        return fig, "✓ Successfully created parametric plot"

    except Exception as e:
        return None, f"❌ Error creating parametric plot: {str(e)}"
