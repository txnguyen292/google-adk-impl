from __future__ import annotations

from typing import Any

from sympy import (
    Derivative,
    Eq,
    Function,
    Symbol,
    Tuple,
    classify_ode,
    dsolve,
    latex,
    pretty,
    sympify,
)
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)


class DifferentialToolError(ValueError):
    """Raised when the differential equation tool receives invalid input."""


_TRANSFORMATIONS = standard_transformations + (
    implicit_multiplication_application,
    convert_xor,
)
_DERIVATIVE_MARKER = "__DERIVATIVE__"


def _normalize_equation(equation: str, *, function_name: str, variable: str) -> str:
    normalized = equation.strip().replace(" ", "")
    if not normalized:
        raise DifferentialToolError("Equation must be a non-empty string.")

    normalized = normalized.replace(f"d{function_name}/d{variable}", _DERIVATIVE_MARKER)
    normalized = normalized.replace(f"{function_name}'({variable})", _DERIVATIVE_MARKER)
    normalized = normalized.replace(f"{function_name}'", _DERIVATIVE_MARKER)
    return normalized


def _to_sympy_equation(
    normalized: str,
    *,
    function_name: str,
    variable: str,
):
    variable_symbol = Symbol(variable)
    function_expr = Function(function_name)(variable_symbol)
    local_dict = {
        variable: variable_symbol,
        function_name: function_expr,
        "Derivative": Derivative,
        "Eq": Eq,
    }

    source = normalized.replace("^", "**")
    source = source.replace(
        _DERIVATIVE_MARKER,
        f"Derivative({function_name},{variable})",
    )
    source = source.replace(f"{function_name}({variable})", function_name)

    if source.startswith("Eq(") and source.endswith(")"):
        try:
            parsed_equation = sympify(source, locals=local_dict)
        except Exception as exc:
            raise DifferentialToolError(
                "The equation could not be parsed. Use standard notation such as dy/dx = x*y."
            ) from exc
        lhs = parsed_equation.lhs
        rhs = parsed_equation.rhs
        if isinstance(lhs, (Tuple, tuple)) or isinstance(rhs, (Tuple, tuple)):
            raise DifferentialToolError(
                "The equation contains a comma-separated tuple. Use multiplication like x*y, not x, y."
            )
        return Eq(lhs, rhs, evaluate=False), function_expr
    elif "=" in source:
        lhs_text, rhs_text = source.split("=", 1)
    else:
        lhs_text, rhs_text = source, "0"

    try:
        lhs = parse_expr(
            lhs_text,
            local_dict=local_dict,
            transformations=_TRANSFORMATIONS,
            evaluate=False,
        )
        rhs = parse_expr(
            rhs_text,
            local_dict=local_dict,
            transformations=_TRANSFORMATIONS,
            evaluate=False,
        )
    except Exception as exc:  # pragma: no cover - parse_expr exposes mixed exceptions
        raise DifferentialToolError(
            "The equation could not be parsed. Use standard notation such as dy/dx = x*y."
        ) from exc

    if isinstance(lhs, (Tuple, tuple)) or isinstance(rhs, (Tuple, tuple)):
        raise DifferentialToolError(
            "The equation contains a comma-separated tuple. Use multiplication like x*y, not x, y."
        )

    return Eq(lhs, rhs, evaluate=False), function_expr


def _equation_branch_text(solution_eq: Eq) -> str:
    return f"{solution_eq.lhs} = {solution_eq.rhs}"


def _render_solution_text(solution: Any, renderer) -> str:
    if isinstance(solution, Eq):
        return renderer(solution)
    if isinstance(solution, (list, tuple)):
        branches = [renderer(branch) for branch in solution if isinstance(branch, Eq)]
        if branches:
            return "; ".join(branches)
    return str(solution)


def _display_normalized_equation(
    normalized: str,
    *,
    function_name: str,
    variable: str,
) -> str:
    return normalized.replace(
        _DERIVATIVE_MARKER,
        f"d{function_name}/d{variable}",
    )


def solve_differential_equation(
    equation: str,
    function_name: str = "y",
    variable: str = "x",
) -> dict[str, Any]:
    """Solve an ODE with SymPy and return plain, pretty, and LaTeX forms."""

    normalized = _normalize_equation(
        equation,
        function_name=function_name,
        variable=variable,
    )
    ode_eq, function_expr = _to_sympy_equation(
        normalized,
        function_name=function_name,
        variable=variable,
    )

    try:
        families = list(classify_ode(ode_eq, function_expr))
        solution_eq = dsolve(ode_eq, function_expr)
    except Exception as exc:  # pragma: no cover - sympy error surface varies
        raise DifferentialToolError(
            "This differential equation is outside the supported SymPy solving path."
        ) from exc

    plain_equation = _equation_branch_text(ode_eq)
    plain_solution = _render_solution_text(solution_eq, _equation_branch_text)
    pretty_solution = _render_solution_text(
        solution_eq,
        lambda branch: pretty(branch, use_unicode=True),
    )
    latex_solution = _render_solution_text(solution_eq, latex)

    return {
        "status": "success",
        "input_equation": equation,
        "normalized_equation": _display_normalized_equation(
            normalized,
            function_name=function_name,
            variable=variable,
        ),
        "family": families[0] if families else "unknown",
        "families": families,
        "equation": plain_equation,
        "solution": plain_solution,
        "pretty_equation": pretty(ode_eq, use_unicode=True),
        "pretty_solution": pretty_solution,
        "latex_equation": latex(ode_eq),
        "latex_solution": latex_solution,
    }


__all__ = ["DifferentialToolError", "solve_differential_equation"]
