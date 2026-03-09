from __future__ import annotations

import ast
import operator
from dataclasses import dataclass
from typing import Any, Callable

class MathToolError(ValueError):
    """Raised when the math tool receives invalid inputs."""


@dataclass
class _EvalResult:
    value: float
    operations: int
    steps: list[str]
    expression: str


def _evaluate_ast(node: ast.AST) -> _EvalResult:
    if isinstance(node, ast.Expression):
        return _evaluate_ast(node.body)

    if isinstance(node, ast.BinOp):
        left = _evaluate_ast(node.left)
        right = _evaluate_ast(node.right)
        op_type = type(node.op)
        symbol: str
        func: Callable[[float, float], float]
        if op_type is ast.Add:
            func = operator.add
            symbol = "+"
        elif op_type is ast.Sub:
            func = operator.sub
            symbol = "-"
        elif op_type is ast.Mult:
            func = operator.mul
            symbol = "×"
        elif op_type is ast.Div:
            if right.value == 0:
                raise MathToolError("Division by zero is not allowed.")
            func = operator.truediv
            symbol = "÷"
        else:
            raise MathToolError(f"Unsupported operator: {op_type.__name__}")

        value = func(left.value, right.value)
        expr = ast.unparse(node)
        step = f"{ast.unparse(node.left)} {symbol} {ast.unparse(node.right)} = {value}"
        return _EvalResult(
            value=value,
            operations=left.operations + right.operations + 1,
            steps=[*left.steps, *right.steps, step],
            expression=expr,
        )

    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        operand = _evaluate_ast(node.operand)
        value = operand.value if isinstance(node.op, ast.UAdd) else -operand.value
        expr = ast.unparse(node)
        return _EvalResult(
            value=value,
            operations=operand.operations,
            steps=[*operand.steps, f"{expr} = {value}"],
            expression=expr,
        )

    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        value = float(node.value)
        expr = ast.unparse(node)
        return _EvalResult(
            value=value,
            operations=0,
            steps=[f"{expr} = {value}"],
            expression=expr,
        )

    raise MathToolError(f"Unsupported expression component: {ast.dump(node)}")


def compute_basic_math(expression: str) -> dict[str, Any]:
    """Evaluate an arithmetic expression composed of +, -, *, /, and parentheses."""
    if not expression:
        raise MathToolError("Expression must be a non-empty string.")

    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise MathToolError(f"Invalid expression '{expression}'.") from exc

    result = _evaluate_ast(tree)
    return {
        "expression": result.expression,
        "result": result.value,
        "operations_count": result.operations,
        "steps": result.steps,
    }


class MathTools:
    def __init__(self, context: Any | None = None, session_id: str | None = None) -> None:
        self._context = context
        self._session_id = session_id

    def _record_error(self, message: str) -> None:
        if self._context is None:
            return

        errors = getattr(self._context, "errors", None)
        before_len = len(errors) if isinstance(errors, list) else None

        record_error = getattr(self._context, "record_error", None)
        if callable(record_error):
            try:
                record_error(message)
            except Exception:
                pass

        errors = getattr(self._context, "errors", None)
        if isinstance(errors, list):
            if before_len is None or len(errors) == before_len:
                errors.append(message)

    def _execute(self, op: Callable[[], Any]) -> Any:
        try:
            return op()
        except Exception as exc:
            self._record_error(str(exc))
            raise

    def add(self, a: float, b: float) -> float:
        return self._execute(lambda: a + b)

    def subtract(self, a: float, b: float) -> float:
        return self._execute(lambda: a - b)

    def multiply(self, a: float, b: float) -> float:
        return self._execute(lambda: a * b)

    def divide(self, a: float, b: float) -> float:
        def op() -> float:
            if b == 0:
                raise ZeroDivisionError("divide by zero")
            return a / b

        return self._execute(op)

    def compute_basic_math(self, expression: str) -> dict[str, Any]:
        """Evaluate an arithmetic expression composed of +, -, *, /, and parentheses."""
        return self._execute(lambda: compute_basic_math(expression))
