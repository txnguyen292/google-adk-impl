from __future__ import annotations

import re
from typing import Any


def _pretty_expression(expression: str) -> str:
    return (
        expression.replace("*", " × ")
        .replace("/", " ÷ ")
        .replace("+", " + ")
        .replace("-", " - ")
    )


_SUPERSCRIPTS = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")
_SUBSCRIPTS = str.maketrans("0123456789-", "₀₁₂₃₄₅₆₇₈₉₋")


def _inline_math_text(text: str) -> str:
    inline = text.strip()
    inline = re.sub(r"\s+", " ", inline)
    inline = re.sub(r"C(\d+)", lambda m: f"C{m.group(1).translate(_SUBSCRIPTS)}", inline)
    inline = re.sub(
        r"\*\*(-?\d+)",
        lambda m: m.group(1).translate(_SUPERSCRIPTS),
        inline,
    )
    inline = re.sub(r"(\d)\*([A-Za-z(])", r"\1\2", inline)
    inline = re.sub(r"([A-Za-z₀₁₂₃₄₅₆₇₈₉)])\*(\d)", r"\1·\2", inline)
    inline = re.sub(r"([A-Za-z₀₁₂₃₄₅₆₇₈₉)])\*([A-Za-z(])", r"\1·\2", inline)
    return inline


def add(a: float, b: float) -> dict[str, Any]:
    """Add two numbers.

    Args:
        a: First addend.
        b: Second addend.

    Returns:
        status: "success" with result or "error" with error_message.
    """

    return {"status": "success", "result": a + b}


def subtract(a: float, b: float) -> dict[str, Any]:
    """Subtract one number from another.

    Args:
        a: The value to subtract from.
        b: The value to subtract.

    Returns:
        status: "success" with result or "error" with error_message.
    """

    return {"status": "success", "result": a - b}


def multiply(a: float, b: float) -> dict[str, Any]:
    """Multiply two numbers.

    Args:
        a: First factor.
        b: Second factor.

    Returns:
        status: "success" with result or "error" with error_message.
    """

    return {"status": "success", "result": a * b}


def divide(a: float, b: float) -> dict[str, Any]:
    """Divide one number by another.

    Args:
        a: Numerator.
        b: Denominator. Must not be zero.

    Returns:
        status: "success" with result or "error" with error_message.
    """

    if b == 0:
        return {
            "status": "error",
            "error_message": "Division by zero is not allowed.",
        }
    return {"status": "success", "result": a / b}


def format_math_response(expression: str, result: Any) -> dict[str, Any]:
    """Format a final math result as a compact equation string.

    When the result comes from the differential-equation solver, preserve the
    solver's plain, pretty, and LaTeX forms instead of flattening it into a
    calculator-style line.
    """

    if isinstance(result, dict) and result.get("status") == "success":
        plain_solution = str(
            result.get("solution")
            or result.get("equation")
            or result.get("result")
            or expression
        )
        inline_problem = _inline_math_text(expression)
        inline_solution = _inline_math_text(plain_solution)
        formatted: dict[str, Any] = {
            "status": "success",
            "equation": plain_solution,
            "pretty_equation": inline_solution,
            "final_answer": f"Result: {inline_solution}",
        }
        latex_solution = result.get("latex_solution")
        latex_equation = result.get("latex_equation")
        if "family" in result:
            formatted["family"] = result["family"]
            formatted["final_answer"] = (
                "Differential equation:\n"
                f"{inline_problem}\n\n"
                "Solution:\n"
                f"{inline_solution}"
            )
        if isinstance(latex_solution, str) and latex_solution.strip():
            formatted["latex_equation"] = latex_solution
        if isinstance(latex_equation, str) and latex_equation.strip():
            formatted["latex_problem"] = latex_equation
        if "families" in result:
            formatted["families"] = result["families"]
        return formatted

    rendered_result = str(result)
    pretty = (
        _pretty_expression(expression.strip()) if expression.strip() else rendered_result
    )
    equation = f"{pretty} = {result}" if pretty != str(result) else pretty
    return {
        "status": "success",
        "equation": equation,
        "final_answer": f"Result: {equation}",
    }


__all__ = ["add", "subtract", "multiply", "divide", "format_math_response"]
