from __future__ import annotations

import ast
from types import SimpleNamespace

import pytest

from installer_framework.util.safe_eval import SafeEvalError, _Evaluator, safe_eval


def test_safe_eval_supports_more_operators_and_ifexp():
    expr = (
        "3 > 2 and 3 >= 3 and 1 < 2 and 1 <= 1 and 1 != 2 and "
        "'a' not in ['b'] and (true if true else false)"
    )
    assert safe_eval(expr, {}) is True
    assert safe_eval("'yes' if flag else 'no'", {"flag": True}) == "yes"
    assert safe_eval("'yes' if flag else 'no'", {"flag": False}) == "no"


def test_safe_eval_attribute_lookup_for_dict_and_object():
    result = safe_eval(
        "mapping.value == 'ok' and obj.value == 7",
        {"mapping": {"value": "ok"}, "obj": SimpleNamespace(value=7)},
    )
    assert result is True


def test_safe_eval_supports_collections_and_chained_compare_false():
    assert safe_eval("{'x': [1, 2], 'y': (3, 4)}['x'][1] == 2", {}) is True
    assert safe_eval("1 < 2 < 1", {}) is False


def test_safe_eval_rejects_unsupported_nodes_and_ops():
    with pytest.raises(SafeEvalError, match="Unsupported expression node"):
        safe_eval("len([1])", {})

    with pytest.raises(SafeEvalError, match="Unsupported unary operator"):
        safe_eval("+1", {})

    with pytest.raises(SafeEvalError, match="Unsupported comparison operator"):
        safe_eval("1 is 1", {})


def test_evaluator_rejects_non_and_or_boolop():
    evaluator = _Evaluator({})
    node = ast.BoolOp(op=ast.BitAnd(), values=[ast.Constant(value=True), ast.Constant(value=False)])
    with pytest.raises(SafeEvalError, match="Unsupported boolean operator"):
        evaluator.visit_BoolOp(node)
