"""
Step-by-step working for calculus operations.

MathKunji is called a solver but has only ever shown the final answer, which
is the one thing a student checking their own working does not need. This module
produces the intermediate steps instead: which rule applies, to what, and what
it produces.

The two halves work quite differently, because SymPy only ships half of it:

  * Integrals use ``sympy.integrals.manualintegrate.integral_steps``, which
    returns a tree of dataclass "rule" objects. Each carries the integrand it
    applies to, an ``eval()`` giving that sub-result, and child rules. This
    module renders that tree; it does not re-derive anything.

  * Derivatives have no equivalent in SymPy, so ``derivative_steps`` walks the
    expression itself and names the rule that applies at each node.

Both are bounded (see MAX_STEPS / MAX_DEPTH): a deeply nested expression would
otherwise produce a wall of output nobody reads, and this runs inside the same
timeout budget as everything else.
"""

import dataclasses

from sympy import Add, Derivative, Mul, Pow, diff, latex

from utils.parser import parse_expression, validate_variable
# STEPS_MARKER is shared, not written out again here: extract_latex() keys off
# this exact heading to tell where the result ends and the working begins, so
# two independent copies of the string could drift and silently make the
# "Copy LaTeX" button return an intermediate step instead of the answer.
from utils.latex_formatter import to_latex, STEPS_MARKER

MAX_STEPS = 40
MAX_DEPTH = 4


# ---------------------------------------------------------------------------
# Derivatives
# ---------------------------------------------------------------------------

def _describe_derivative_rule(expr, var):
    """
    Name the differentiation rule that applies at the top of ``expr``.

    Returns (rule_name, explanation) or None when the expression is a leaf
    that needs no rule (a bare constant or the variable itself).
    """
    if not expr.has(var):
        return None
    if expr == var:
        return None

    if isinstance(expr, Add):
        return ("Sum rule",
                "Differentiate each term separately and add the results.")

    if isinstance(expr, Mul):
        constant, rest = expr.as_independent(var, as_Add=False)
        if constant != 1:
            return ("Constant multiple rule",
                    f"The factor ${latex(constant)}$ does not depend on "
                    f"${latex(var)}$, so it stays put and we differentiate the rest.")
        # A quotient reaches us as a product with a negative power.
        if any(isinstance(f, Pow) and f.args[1].is_negative for f in expr.args):
            return ("Quotient rule",
                    "Written as a product with a negative power; "
                    "the product rule applies to the factors.")
        return ("Product rule",
                "For $u \\cdot v$ the derivative is $u'v + uv'$.")

    if isinstance(expr, Pow):
        base, exponent = expr.args
        if not exponent.has(var):
            if base == var:
                return ("Power rule",
                        f"$\\frac{{d}}{{d{latex(var)}}}{latex(var)}^n = "
                        f"n\\,{latex(var)}^{{n-1}}$.")
            return ("Chain rule (power)",
                    "Differentiate the outer power, then multiply by the "
                    "derivative of the inner expression.")
        return ("Exponential rule",
                "The variable appears in the exponent, so the derivative "
                "brings down a logarithm.")

    if expr.is_Function:
        if len(expr.args) == 1 and expr.args[0] == var:
            return (f"Derivative of {type(expr).__name__}",
                    "A standard derivative, applied directly.")
        return ("Chain rule",
                "Differentiate the outer function, then multiply by the "
                "derivative of what is inside.")

    return ("Direct differentiation", "Applied term by term.")


def _derivative_step_lines(expr, var, depth, budget):
    """Recursively collect markdown lines describing each differentiation step."""
    if budget["used"] >= MAX_STEPS or depth > MAX_DEPTH:
        return []

    described = _describe_derivative_rule(expr, var)
    if described is None:
        return []

    rule_name, explanation = described
    budget["used"] += 1
    indent = "    " * depth

    result = diff(expr, var)
    lines = [
        f"{indent}- **{rule_name}** — {explanation}",
        f"{indent}  $\\frac{{d}}{{d{latex(var)}}}\\left({latex(expr)}\\right) "
        f"= {latex(result)}$",
    ]

    for child in expr.args:
        if child.has(var) and child != var:
            lines.extend(_derivative_step_lines(child, var, depth + 1, budget))

    return lines


def derivative_steps(expr_string, var_string="x"):
    """
    Show the differentiation rules applied to an expression.

    Args:
        expr_string (str): The expression to differentiate
        var_string (str): Variable to differentiate with respect to

    Returns:
        str: Markdown describing each step, or "❌ ..." on failure
    """
    success, expr = parse_expression(expr_string)
    if not success:
        return f"❌ {expr}"

    var_success, var = validate_variable(var_string)
    if not var_success:
        return f"❌ {var}"

    try:
        if not expr.has(var):
            return (
                f"{STEPS_MARKER} ${latex(expr)}$ does not contain ${latex(var)}$, "
                f"so its derivative is $0$ — the constant rule."
            )

        budget = {"used": 0}
        lines = _derivative_step_lines(expr, var, 0, budget)
        if not lines:
            return f"{STEPS_MARKER} Differentiated directly; no intermediate rules to show."

        output = f"{STEPS_MARKER}\n\n" + "\n".join(lines)
        if budget["used"] >= MAX_STEPS:
            output += f"\n\n_(truncated at {MAX_STEPS} steps)_"
        return output

    except Exception as e:
        return f"❌ Error building derivative steps: {str(e)}"


# ---------------------------------------------------------------------------
# Integrals
# ---------------------------------------------------------------------------

# Plain-language names for SymPy's rule classes. Anything missing falls back to
# a de-camel-cased version of the class name, so a SymPy upgrade that adds new
# rules degrades to a readable label rather than breaking.
_INTEGRAL_RULE_NAMES = {
    "ConstantRule": "Integral of a constant",
    "ConstantTimesRule": "Constant multiple rule",
    "PowerRule": "Power rule",
    "AddRule": "Sum rule",
    "URule": "Substitution",
    "PartsRule": "Integration by parts",
    "CyclicPartsRule": "Integration by parts (cyclic)",
    "TrigRule": "Trigonometric integral",
    "SinRule": "Integral of sin",
    "CosRule": "Integral of cos",
    "ExpRule": "Integral of an exponential",
    "ReciprocalRule": "Integral of 1/x",
    "ArcsinRule": "Arcsine form",
    "ArctanRule": "Arctangent form",
    "AlternativeRule": "Several methods apply; taking the first",
    "DontKnowRule": "No elementary method found",
    "RewriteRule": "Rewrite the integrand first",
}


def _humanise_rule(rule):
    name = type(rule).__name__
    if name in _INTEGRAL_RULE_NAMES:
        return _INTEGRAL_RULE_NAMES[name]
    trimmed = name[:-4] if name.endswith("Rule") else name
    spaced = "".join(f" {c}" if c.isupper() else c for c in trimmed).strip()
    return spaced.capitalize() or name


def _child_rules(rule):
    """
    Find nested rules generically.

    Rules are dataclasses whose extra fields vary by rule type -- AddRule has
    `substeps`, PartsRule has `v_step`/`second_step`, others have `substep`.
    Rather than enumerate them (and silently miss any SymPy adds later), scan
    the dataclass fields for anything that is itself a rule.
    """
    children = []
    for field in dataclasses.fields(rule):
        value = getattr(rule, field.name, None)
        if dataclasses.is_dataclass(value) and hasattr(value, "integrand"):
            children.append(value)
        elif isinstance(value, (list, tuple)):
            children.extend(
                v for v in value
                if dataclasses.is_dataclass(v) and hasattr(v, "integrand")
            )
    return children


def _integral_step_lines(rule, var, depth, budget):
    if budget["used"] >= MAX_STEPS or depth > MAX_DEPTH:
        return []

    budget["used"] += 1
    indent = "    " * depth

    try:
        evaluated = rule.eval()
        result = f" $= {latex(evaluated)}$"
    except Exception:
        # A rule that cannot self-evaluate is still worth naming.
        result = ""

    lines = [
        f"{indent}- **{_humanise_rule(rule)}** — "
        f"$\\int {latex(rule.integrand)}\\,d{latex(var)}${result}"
    ]
    for child in _child_rules(rule):
        lines.extend(_integral_step_lines(child, var, depth + 1, budget))
    return lines


def integral_steps_markdown(expr_string, var_string="x"):
    """
    Show the integration rules applied to an expression.

    Only meaningful for indefinite integrals -- SymPy's stepper works on the
    antiderivative, so a definite integral is explained by its antiderivative
    and then evaluated at the bounds by the caller.

    Args:
        expr_string (str): The expression to integrate
        var_string (str): Variable of integration

    Returns:
        str: Markdown describing each step, or "❌ ..." on failure
    """
    success, expr = parse_expression(expr_string)
    if not success:
        return f"❌ {expr}"

    var_success, var = validate_variable(var_string)
    if not var_success:
        return f"❌ {var}"

    try:
        # Imported lazily: this pulls in a large chunk of SymPy's integration
        # machinery that the rest of the app never touches.
        from sympy.integrals.manualintegrate import integral_steps

        rule = integral_steps(expr, var)
        budget = {"used": 0}
        lines = _integral_step_lines(rule, var, 0, budget)
        if not lines:
            return f"{STEPS_MARKER} No intermediate steps to show."

        output = f"{STEPS_MARKER}\n\n" + "\n".join(lines)
        if budget["used"] >= MAX_STEPS:
            output += f"\n\n_(truncated at {MAX_STEPS} steps)_"
        return output

    except Exception as e:
        return f"❌ Error building integral steps: {str(e)}"
