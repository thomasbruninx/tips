from __future__ import annotations

import importlib.util
from pathlib import Path

from installer_framework.config.models import StepConfig
from tests.helpers.context_factory import make_context
from tests.helpers.qt_helpers import WizardStub, make_theme


PLUGIN_FILE = Path("/Users/thomasbruninx/Projecten/tips/plugins/preflight_step.tipsplugin/plugin.py")


def _load_module():
    spec = importlib.util.spec_from_file_location("preflight_plugin", PLUGIN_FILE)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_preflight_plugin_registers_step_class():
    module = _load_module()
    payload = module.register()
    assert "step_class" in payload


def test_preflight_step_requires_ack(qtbot, tmp_path):
    module = _load_module()
    StepClass = module.register()["step_class"]

    ctx = make_context(tmp_path)
    wizard = WizardStub(make_theme("classic", source_root=tmp_path))
    step_cfg = StepConfig(
        id="preflight",
        type="preflight_step",
        title="Preflight",
        description="Check",
        params={
            "checklist": ["A", "B"],
            "required_ack": True,
            "ack_label": "I confirm",
        },
    )

    step = StepClass(step_cfg, ctx, wizard)
    qtbot.addWidget(step)

    ok, _ = step.validate()
    assert ok is False
    step.ack_checkbox.setChecked(True)
    ok, _ = step.validate()
    assert ok is True
