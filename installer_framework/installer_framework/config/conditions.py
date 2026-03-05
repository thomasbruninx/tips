"""Condition evaluation for step/field visibility and navigation."""

from __future__ import annotations

from installer_framework.engine.context import InstallerState
from installer_framework.util.safe_eval import SafeEvalError, safe_eval



def evaluate_condition(expr: str | None, state: InstallerState) -> bool:
    if not expr:
        return True

    context = {
        "answers": state.answers,
        "selected_features": state.selected_features,
        "scope": state.install_scope,
        "install_scope": state.install_scope,
    }
    try:
        return bool(safe_eval(expr, context))
    except SafeEvalError:
        return False
