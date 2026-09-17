"""
Algebraic operations: simplify, expand, factor, solve.
"""

from sympy import simplify, expand, factor, solve, Eq, latex
from utils.parser import parse_expression, validate_variable
from utils.latex_formatter import format_step_by_step, to_latex, to_latex_inline


def simplify_expression(expr_string):
    """
    Simplify a mathematical expression.

    Args:
        expr_string (str): The expression to simplify

    Returns:
        str: Formatted result with original and simplified expression
    """
    success, expr = parse_expression(expr_string)
    if not success:
        return f"❌ {expr}"

    try:
        result = simplify(expr)
        return format_step_by_step(expr, result, "Simplify")
    except Exception as e:
        return f"❌ Error simplifying: {str(e)}"


def expand_expression(expr_string):
    """
    Expand a mathematical expression.

    Args:
        expr_string (str): The expression to expand

    Returns:
        str: Formatted result with original and expanded expression
    """
    success, expr = parse_expression(expr_string)
    if not success:
        return f"❌ {expr}"

    try:
        result = expand(expr)
        return format_step_by_step(expr, result, "Expand")
    except Exception as e:
        return f"❌ Error expanding: {str(e)}"


def factor_expression(expr_string):
    """
    Factor a mathematical expression.

    Args:
        expr_string (str): The expression to factor

    Returns:
        str: Formatted result with original and factored expression
    """
    success, expr = parse_expression(expr_string)
    if not success:
        return f"❌ {expr}"

    try:
        result = factor(expr)
        return format_step_by_step(expr, result, "Factor")
    except Exception as e:
        return f"❌ Error factoring: {str(e)}"


def algebra_result_value(operation, expr_string):
    """
    Return the plain SymPy result of an algebra operation, unformatted.

    The "Graph result" button needs the expression itself; the display
    functions above return markdown with the maths already rendered as LaTeX,
    which cannot be fed back into the plotter. Rather than change what all the
    core functions return -- every function in core/ takes strings and returns
    finished markdown, and that contract is relied on throughout -- this
    recomputes the value.

    It does mean the operation runs twice for a click that also graphs. That
    is a deliberate trade: these are millisecond operations bounded by the same
    timeout as everything else, and the alternative is reshaping the return
    type of every function in core/.

    Args:
        operation (str): one of "simplify", "expand", "factor", "evaluate"
        expr_string (str): the user's input

    Returns:
        tuple: (success: bool, sympy.Expr or error_message: str)
    """
    success, expr = parse_expression(expr_string)
    if not success:
        return False, expr

    operations = {
        "simplify": simplify,
        "expand": expand,
        "factor": factor,
        # Evaluate's displayed result is the simplified expression when no
        # substitutions are supplied, which is the only case worth graphing.
        "evaluate": simplify,
    }
    if operation not in operations:
        return False, f"no graphable value for operation: {operation}"

    try:
        return True, operations[operation](expr)
    except Exception as e:
        return False, str(e)


def _normalize_solutions(solutions):
    """
    sympy.solve can return a list, a dict, or a list of dicts depending on
    the equation and variable shape. Normalize all of these into a flat
    list of solution expressions so callers can format uniformly.
    """
    if isinstance(solutions, dict):
        return list(solutions.values())
    if isinstance(solutions, list):
        flattened = []
        for sol in solutions:
            if isinstance(sol, dict):
                flattened.extend(sol.values())
            else:
                flattened.append(sol)
        return flattened
    return solutions


def solve_equation(expr_string, var_string="x"):
    """
    Solve an equation or expression for a variable.

    Args:
        expr_string (str): The equation to solve. Accepts either a bare
            expression that is implicitly set to zero (e.g. "x^2 - 4"),
            or a full equation containing "=" (e.g. "x^2 - 1 = 2*x").
        var_string (str): The variable to solve for (default: 'x')

    Returns:
        str: Formatted solution(s)
    """
    # Validate variable
    var_success, var = validate_variable(var_string)
    if not var_success:
        return f"❌ {var}"

    if '=' in expr_string:
        lhs_string, _, rhs_string = expr_string.partition('=')

        lhs_success, lhs = parse_expression(lhs_string)
        if not lhs_success:
            return f"❌ Left side: {lhs}"

        rhs_success, rhs = parse_expression(rhs_string)
        if not rhs_success:
            return f"❌ Right side: {rhs}"

        equation = Eq(lhs, rhs)
        display_expr = lhs - rhs
    else:
        success, equation = parse_expression(expr_string)
        if not success:
            return f"❌ {equation}"
        display_expr = equation

    try:
        solutions = _normalize_solutions(solve(equation, var))

        if not solutions:
            # sympy.solve returns an empty list for four quite different
            # situations, and reporting all of them as "no solution found" is
            # wrong for three. Tell them apart so the answer is accurate:
            # x = x has every value as a solution, and solving y^2-4 for x is
            # not unsolvable -- it just names a variable that isn't there.
            simplified = simplify(display_expr)
            header = (
                f"### Solve for ${var_string}$\n\n"
                f"**Equation:** {to_latex_inline(display_expr)} $= 0$\n\n"
            )

            if simplified == 0:
                return header + (
                    f"**Result:** Identity — this holds for **every** value of "
                    f"${var_string}$, so there is no single solution to report."
                )
            if not simplified.free_symbols:
                return header + (
                    f"**Result:** No solution — the equation reduces to "
                    f"{to_latex_inline(simplified)} $= 0$, which is never true."
                )
            if var not in simplified.free_symbols:
                present = ', '.join(f'${s}$' for s in sorted(simplified.free_symbols, key=str))
                return header + (
                    f"**Result:** ${var_string}$ does not appear in this equation "
                    f"(it involves {present}), so there is nothing to solve for. "
                    f"Check the **Variable** field."
                )
            return header + (
                f"**Result:** No closed-form solution found for ${var_string}$."
            )

        solutions_latex = [to_latex_inline(sol) for sol in solutions]
        solutions_str = ", ".join(solutions_latex)

        output = f"### Solve for ${var_string}$\n\n"
        output += f"**Equation:** {to_latex_inline(display_expr)} $= 0$\n\n"
        output += f"**Solutions:** {solutions_str}\n"

        return output

    except Exception as e:
        return f"❌ Error solving: {str(e)}"


def evaluate_expression(expr_string, substitutions=None, simplify_result=True):
    """
    Evaluate an expression with optional variable substitutions.

    Args:
        expr_string (str): The expression to evaluate
        substitutions (dict): Dictionary of variable:value pairs
        simplify_result (bool): Whether to simplify after substituting
            (default: True, matching prior always-simplify behavior)

    Returns:
        str: Formatted evaluation result
    """
    success, expr = parse_expression(expr_string)
    if not success:
        return f"❌ {expr}"

    try:
        if substitutions:
            result = expr.subs(substitutions)
        else:
            result = expr

        if simplify_result:
            result = simplify(result)

        output = "### Evaluate\n\n"
        output += f"**Expression:** {to_latex(expr)}\n\n"

        if substitutions:
            # latex(v), not str(v): these already sit inside a $...$ math
            # context, so the raw SymPy repr rendered "x=sqrt(2)" as the
            # literal text "sqrt(2)" instead of a radical, and "2/3" as flat
            # text instead of a fraction.
            #
            # The key is interpolated as-is. It is a plain variable name that
            # is already a valid LaTeX identifier, and passing a Python str
            # through latex() would wrap it as \mathtt{\text{x}} -- typewriter
            # text rather than an italic math variable.
            subs_str = ", ".join(
                f"${k} = {latex(v)}$" for k, v in substitutions.items()
            )
            output += f"**Substitutions:** {subs_str}\n\n"

        output += f"**Result:** {to_latex(result)}\n"

        return output

    except Exception as e:
        return f"❌ Error evaluating: {str(e)}"
