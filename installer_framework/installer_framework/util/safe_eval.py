"""Tiny safe expression evaluator for JSON step/action conditions."""

from __future__ import annotations

import ast
import re
from typing import Any

_LITERAL_REPLACEMENTS = {
    "true": "True",
    "false": "False",
    "null": "None",
}


class SafeEvalError(ValueError):
    """Raised for unsupported or unsafe expressions."""



def _normalize_literals(expr: str) -> str:
    out = expr
    for src, dst in _LITERAL_REPLACEMENTS.items():
        out = re.sub(rf"\b{src}\b", dst, out)
    return out


class _Evaluator(ast.NodeVisitor):
    def __init__(self, context: dict[str, Any]) -> None:
        self.context = context

    def visit_Expression(self, node: ast.Expression) -> Any:
        return self.visit(node.body)

    def visit_Name(self, node: ast.Name) -> Any:
        if node.id in self.context:
            return self.context[node.id]
        raise SafeEvalError(f"Unknown symbol: {node.id}")

    def visit_Constant(self, node: ast.Constant) -> Any:
        return node.value

    def visit_List(self, node: ast.List) -> Any:
        return [self.visit(item) for item in node.elts]

    def visit_Tuple(self, node: ast.Tuple) -> Any:
        return tuple(self.visit(item) for item in node.elts)

    def visit_Dict(self, node: ast.Dict) -> Any:
        return {self.visit(k): self.visit(v) for k, v in zip(node.keys, node.values)}

    def visit_BoolOp(self, node: ast.BoolOp) -> bool:
        values = [bool(self.visit(v)) for v in node.values]
        if isinstance(node.op, ast.And):
            return all(values)
        if isinstance(node.op, ast.Or):
            return any(values)
        raise SafeEvalError("Unsupported boolean operator")

    def visit_UnaryOp(self, node: ast.UnaryOp) -> Any:
        operand = self.visit(node.operand)
        if isinstance(node.op, ast.Not):
            return not bool(operand)
        raise SafeEvalError("Unsupported unary operator")

    def visit_Compare(self, node: ast.Compare) -> bool:
        left = self.visit(node.left)
        for op, right_node in zip(node.ops, node.comparators):
            right = self.visit(right_node)
            if isinstance(op, ast.Eq):
                ok = left == right
            elif isinstance(op, ast.NotEq):
                ok = left != right
            elif isinstance(op, ast.Gt):
                ok = left > right
            elif isinstance(op, ast.GtE):
                ok = left >= right
            elif isinstance(op, ast.Lt):
                ok = left < right
            elif isinstance(op, ast.LtE):
                ok = left <= right
            elif isinstance(op, ast.In):
                ok = left in right
            elif isinstance(op, ast.NotIn):
                ok = left not in right
            else:
                raise SafeEvalError("Unsupported comparison operator")
            if not ok:
                return False
            left = right
        return True

    def visit_Attribute(self, node: ast.Attribute) -> Any:
        base = self.visit(node.value)
        if isinstance(base, dict):
            return base.get(node.attr)
        return getattr(base, node.attr)

    def visit_Subscript(self, node: ast.Subscript) -> Any:
        base = self.visit(node.value)
        key = self.visit(node.slice)
        return base[key]

    def visit_IfExp(self, node: ast.IfExp) -> Any:
        return self.visit(node.body) if self.visit(node.test) else self.visit(node.orelse)

    def generic_visit(self, node: ast.AST) -> Any:
        raise SafeEvalError(f"Unsupported expression node: {type(node).__name__}")



def safe_eval(expr: str, context: dict[str, Any]) -> Any:
    """Evaluate a restricted boolean/data expression safely."""
    normalized = _normalize_literals(expr)
    parsed = ast.parse(normalized, mode="eval")
    evaluator = _Evaluator(context)
    return evaluator.visit(parsed)
