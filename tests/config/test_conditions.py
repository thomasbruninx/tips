from __future__ import annotations

from installer_framework.config.conditions import evaluate_condition
from installer_framework.engine.context import InstallerState


def test_evaluate_condition_truthy_expression():
    state = InstallerState(answers={"advanced": True}, install_scope="user")
    assert evaluate_condition("answers.advanced == true and scope == 'user'", state) is True


def test_evaluate_condition_invalid_expression_is_false():
    state = InstallerState(answers={}, install_scope="user")
    assert evaluate_condition("lambda x: x", state) is False


def test_evaluate_condition_empty_expression_is_true():
    state = InstallerState()
    assert evaluate_condition(None, state) is True
