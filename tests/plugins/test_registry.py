from __future__ import annotations

import pytest

from installer_framework.plugins.registry import build_registry_with_builtins
from installer_framework.ui.step_base import StepWidget


class DummyStep(StepWidget):
    pass


def test_registry_has_builtin_step_and_action():
    registry = build_registry_with_builtins()
    assert registry.get_step_class("welcome") is not None
    assert registry.get_action_class("copy_files") is not None


def test_registry_duplicate_step_handle_fails():
    registry = build_registry_with_builtins()
    with pytest.raises(ValueError):
        registry.register_step("welcome", DummyStep, source="test")
