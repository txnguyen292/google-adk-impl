from core import RunContext
from adk_agent.skills.math.tools.math_tools import MathTools
from adk_agent.skills.math.tools.differential_tools import (
    DifferentialToolError,
    solve_differential_equation,
)


def test_math_tools_basic_ops():
    ctx = RunContext(run_id="run", session_id="sess")
    tools = MathTools(ctx, "sess")
    assert tools.add(2, 3) == 5
    assert tools.subtract(5, 2) == 3
    assert tools.multiply(4, 2.5) == 10.0
    assert tools.divide(9, 3) == 3


def test_math_tools_divide_by_zero():
    ctx = RunContext(run_id="run", session_id="sess")
    tools = MathTools(ctx, "sess")
    try:
        tools.divide(1, 0)
    except ZeroDivisionError:
        pass
    else:
        raise AssertionError("Expected divide-by-zero to raise ZeroDivisionError")
    assert ctx.errors, "divide-by-zero should be recorded as an error"


def test_solve_differential_equation():
    result = solve_differential_equation("dy/dx - y = 0")

    assert result["status"] == "success"
    assert result["normalized_equation"] == "dy/dx-y=0"
    assert result["solution"] == "y(x) = C1*exp(x)"
    assert result["pretty_solution"]
    assert result["latex_solution"] == "y{\\left(x \\right)} = C_{1} e^{x}"


def test_solve_differential_equation_accepts_sympy_eq_notation():
    result = solve_differential_equation("Eq(Derivative(y(x), x), x + y(x))")

    assert result["status"] == "success"
    assert result["equation"] == "Derivative(y(x), x) = x + y(x)"
    assert result["solution"] == "y(x) = C1*exp(x) - x - 1"


def test_solve_differential_equation_rejects_tuple_rhs():
    try:
        solve_differential_equation("dy/dx = x, y")
    except DifferentialToolError as exc:
        assert "comma-separated tuple" in str(exc)
    else:
        raise AssertionError("Expected tuple-style RHS to raise DifferentialToolError")


def test_solve_differential_equation_handles_multiple_solution_branches():
    result = solve_differential_equation("dy/dx = (3*x^2 + 4*x - 4)/(2*y - 4)")

    assert result["status"] == "success"
    assert "y(x) = 2 - sqrt(C1 + x**3 + 2*x**2 - 4*x)" in result["solution"]
    assert "y(x) = sqrt(C1 + x**3 + 2*x**2 - 4*x) + 2" in result["solution"]
    assert "; " in result["solution"]
