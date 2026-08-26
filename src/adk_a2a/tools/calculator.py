"""Calculator tool with safe expression evaluation."""

import ast
import operator
from collections.abc import Callable
from typing import Any

from adk_a2a.core.logging import get_logger
from adk_a2a.domain.exceptions import ToolExecutionError
from adk_a2a.domain.models import CalculationResult

logger = get_logger(__name__)

# Supported safe arithmetic operators
_OPERATORS: dict[type[ast.AST], Callable[..., Any]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _eval_ast_node(node: ast.AST) -> float:
    """Recursively evaluates an AST node containing mathematical expressions safely."""
    if isinstance(node, ast.Expression):
        return _eval_ast_node(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.BinOp):
        bin_op_type = type(node.op)
        if bin_op_type not in _OPERATORS:
            raise ToolExecutionError(f"Unsupported binary operator: {bin_op_type.__name__}")
        left = _eval_ast_node(node.left)
        right = _eval_ast_node(node.right)
        return float(_OPERATORS[bin_op_type](left, right))
    if isinstance(node, ast.UnaryOp):
        unary_op_type = type(node.op)
        if unary_op_type not in _OPERATORS:
            raise ToolExecutionError(f"Unsupported unary operator: {unary_op_type.__name__}")
        operand = _eval_ast_node(node.operand)
        return float(_OPERATORS[unary_op_type](operand))
    raise ToolExecutionError(f"Unsupported AST node expression: {type(node).__name__}")


def calculate(expression: str) -> CalculationResult:
    """Calculates the mathematical result of a mathematical expression safely.

    Args:
        expression: The mathematical expression string (e.g., "15.5 * 2 + 10").

    Returns:
        A CalculationResult value object containing expression and numerical result.

    Raises:
        ToolExecutionError: If syntax is invalid or evaluation fails.
    """
    logger.info("Executing arithmetic calculation: %s", expression)
    clean_expr = expression.strip()
    if not clean_expr:
        raise ToolExecutionError("Calculation expression cannot be empty.")

    try:
        parsed_ast = ast.parse(clean_expr, mode="eval")
        result_value = _eval_ast_node(parsed_ast)
        return CalculationResult(expression=clean_expr, result=result_value)
    except Exception as exc:
        logger.error("Failed to evaluate expression %s: %s", clean_expr, exc)
        raise ToolExecutionError(f"Failed to evaluate expression '{clean_expr}': {exc}") from exc
