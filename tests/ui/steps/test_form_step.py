from __future__ import annotations

from installer_framework.config.models import FieldConfig, StepConfig
from installer_framework.ui.steps.form import FormStep
from tests.helpers.context_factory import make_context
from tests.helpers.qt_helpers import WizardStub, make_theme


def test_form_step_validation_for_text_and_checkbox(qtbot, tmp_path):
    ctx = make_context(tmp_path)
    wizard = WizardStub(make_theme("classic", source_root=tmp_path))
    step_cfg = StepConfig(
        id="form",
        type="form",
        title="Form",
        fields=[
            FieldConfig(id="username", type="text", label="Username", required=True, min_length=3),
            FieldConfig(id="enable", type="checkbox", label="Enable", default=True),
        ],
    )
    step = FormStep(step_cfg, ctx, wizard)
    qtbot.addWidget(step)

    step.controls["username"].set_value("ab")
    ok, _ = step.validate()
    assert ok is False

    step.controls["username"].set_value("abcd")
    ok, _ = step.validate()
    assert ok is True
