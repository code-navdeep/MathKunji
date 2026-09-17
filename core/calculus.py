"""
Calculus operations: derivatives, integrals, limits.
"""

from sympy import diff, integrate, limit, oo, series, Symbol
from utils.parser import parse_expression, validate_variable
from utils.latex_formatter import format_step_by_step, to_latex, numeric_note


def calculus_result_value(operation, expr_string, var_string="x", order=1, point="0"):
    """
    Return the plain SymPy result of a calculus operation, unformatted.

    Counterpart to algebra_result_value() -- see the note there for why this
    recomputes rather than changing what the display functions return.

    "limit" is absent on purpose: a limit evaluates to a single number, so
    there is no curve to graph.

    Args:
        operation (str): one of "derivative", "integral", "taylor"
        expr_string (str): the user's input
        var_string (str): the variable
        order (int): derivative order / Taylor order
        point (str): Taylor expansion point

    Returns:
        tuple: (success: bool, sympy.Expr or error_message: str)
    """
    success, expr = parse_expression(expr_string)
    if not success:
        return False, expr

    var_success, var = validate_variable(var_string)
    if not var_success:
        return False, var

    try:
        if operation == "derivative":
            return True, diff(expr, var, order)
        if operation == "integral":
            # The indefinite integral without the "+ C", which is not
            # something the plotter can evaluate.
            return True, integrate(expr, var)
        if operation == "taylor":
            point_success, point_expr = parse_expression(point)
            if not point_success:
                return False, point_expr
            return True, series(expr, var, point_expr, n=order + 1).removeO()
        return False, f"no graphable value for operation: {operation}"
    except Exception as e:
        return False, str(e)


def calculate_derivative(expr_string, var_string="x", order=1, show_numeric=False):
    """
    Calculate the derivative of an expression.

    Args:
        expr_string (str): The expression to differentiate
        var_string (str): Variable to differentiate with respect to
        order (int): Order of derivative (default: 1)

    Returns:
        str: Formatted result showing original and derivative
    """
    # Parse expression
    success, expr = parse_expression(expr_string)
    if not success:
        return f"❌ {expr}"

    # Validate variable
    var_success, var = validate_variable(var_string)
    if not var_success:
        return f"❌ {var}"

    try:
        # Calculate derivative
        result = diff(expr, var, order)

        # Format output
        if order == 1:
            operation = f"Derivative: d/d{var_string}"
        else:
            operation = f"Derivative: d^{order}/d{var_string}^{order}"

        output = f"### {operation}\n\n"
        output += f"**Function:** {to_latex(expr)}\n\n"
        output += f"**Result:** {to_latex(result)}\n"
        output += numeric_note(result, show_numeric)

        return output

    except Exception as e:
        return f"❌ Error calculating derivative: {str(e)}"


def calculate_integral(expr_string, var_string="x", definite=False, lower=None, upper=None, show_numeric=False):
    """
    Calculate the integral of an expression.

    Args:
        expr_string (str): The expression to integrate
        var_string (str): Variable to integrate with respect to
        definite (bool): Whether to calculate definite integral
        lower: Lower bound for definite integral
        upper: Upper bound for definite integral

    Returns:
        str: Formatted result showing original and integral
    """
    # Parse expression
    success, expr = parse_expression(expr_string)
    if not success:
        return f"❌ {expr}"

    # Validate variable
    var_success, var = validate_variable(var_string)
    if not var_success:
        return f"❌ {var}"

    try:
        # Calculate integral
        if definite and lower is not None and upper is not None:
            # Parse bounds
            lower_success, lower_expr = parse_expression(str(lower))
            upper_success, upper_expr = parse_expression(str(upper))

            if not lower_success:
                return f"❌ Invalid lower bound: {lower_expr}"
            if not upper_success:
                return f"❌ Invalid upper bound: {upper_expr}"

            result = integrate(expr, (var, lower_expr, upper_expr))
            operation = f"Definite Integral: ∫[{lower} to {upper}]"
        else:
            # Add the constant of integration for indefinite integrals so
            # both branches render through the same to_latex() call below.
            result = integrate(expr, var) + Symbol('C')
            operation = f"Indefinite Integral: ∫ ... d{var_string}"

        # Format output
        output = f"### {operation}\n\n"
        output += f"**Function:** {to_latex(expr)}\n\n"
        output += f"**Result:** {to_latex(result)}\n"
        output += numeric_note(result, show_numeric)

        return output

    except Exception as e:
        return f"❌ Error calculating integral: {str(e)}"


def calculate_limit(expr_string, var_string="x", point="0", direction="+", show_numeric=False):
    """
    Calculate the limit of an expression.

    Args:
        expr_string (str): The expression
        var_string (str): Variable approaching the limit
        point (str): Point to approach (can be 'oo' for infinity)
        direction (str): Direction to approach from ('+', '-', or '+-')

    Returns:
        str: Formatted result showing limit
    """
    # Parse expression
    success, expr = parse_expression(expr_string)
    if not success:
        return f"❌ {expr}"

    # Validate variable
    var_success, var = validate_variable(var_string)
    if not var_success:
        return f"❌ {var}"

    try:
        # Parse the point
        if point.lower() in ['oo', 'inf', 'infinity']:
            point_expr = oo
            point_display = "∞"
        elif point.lower() in ['-oo', '-inf', '-infinity']:
            point_expr = -oo
            point_display = "-∞"
        else:
            point_success, point_expr = parse_expression(point)
            if not point_success:
                return f"❌ Invalid limit point: {point_expr}"
            point_display = point

        # Calculate limit
        result = limit(expr, var, point_expr, direction)

        # Format output
        dir_symbol = {"+" : "⁺", "-": "⁻", "+-": "±"}.get(direction, "")
        output = f"### Limit\n\n"
        output += f"**Expression:** {to_latex(expr)}\n\n"
        output += f"**Limit:** lim [{var_string} → {point_display}{dir_symbol}]\n\n"
        output += f"**Result:** {to_latex(result)}\n"
        output += numeric_note(result, show_numeric)

        return output

    except Exception as e:
        return f"❌ Error calculating limit: {str(e)}"


def taylor_series(expr_string, var_string="x", point="0", order=5):
    """
    Calculate the Taylor series expansion.

    Args:
        expr_string (str): The expression to expand
        var_string (str): Variable to expand around
        point (str): Point to expand around (default: "0")
        order (int): Order of the expansion (default: 5)

    Returns:
        str: Formatted Taylor series expansion
    """
    # Parse expression
    success, expr = parse_expression(expr_string)
    if not success:
        return f"❌ {expr}"

    # Validate variable
    var_success, var = validate_variable(var_string)
    if not var_success:
        return f"❌ {var}"

    try:
        # Parse point
        point_success, point_expr = parse_expression(point)
        if not point_success:
            return f"❌ Invalid expansion point: {point_expr}"

        # Calculate series
        result = series(expr, var, point_expr, n=order+1).removeO()

        # Format output
        output = f"### Taylor Series (Order {order})\n\n"
        output += f"**Function:** {to_latex(expr)}\n\n"
        output += f"**Expansion point:** {var_string} = {point}\n\n"
        output += f"**Series:** {to_latex(result)}\n"

        return output

    except Exception as e:
        return f"❌ Error calculating series: {str(e)}"
