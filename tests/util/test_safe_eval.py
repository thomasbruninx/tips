from __future__ import annotations

import pytest

from installer_framework.util.safe_eval import SafeEvalError, safe_eval


def test_safe_eval_boolean_and_compare():
    result = safe_eval("answers.enabled == true and scope == 'user'", {"answers": {"enabled": True}, "scope": "user"})
    assert result is True


def test_safe_eval_rejects_unknown_symbol():
    with pytest.raises(SafeEvalError):
        safe_eval("unknown == 1", {})


def test_safe_eval_supports_in_operator_and_subscript():
    expr = "'core' in selected_features and answers['x'] == 2"
    assert safe_eval(expr, {"selected_features": ["core"], "answers": {"x": 2}}) is True
