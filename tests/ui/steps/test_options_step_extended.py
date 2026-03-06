from __future__ import annotations

from installer_framework.config.models import FieldConfig, StepConfig
from installer_framework.ui.steps.options import OptionsStep
from tests.helpers.context_factory import make_context
from tests.helpers.qt_helpers import WizardStub, make_theme


def test_options_step_apply_state_and_get_data(qtbot, tmp_path):
    ctx = make_context(
        tmp_path,
        config_overrides={
            "features": [
                {"id": "core", "label": "Core", "default": True},
                {"id": "docs", "label": "Docs", "default": False},
            ]
        },
    )
    ctx.state.answers.update({"desktop": False, "channel": "beta"})
    ctx.state.selected_features = ["docs"]

    wizard = WizardStub(make_theme("classic", source_root=tmp_path))
    step_cfg = StepConfig(
        id="options",
        type="options",
        title="Options",
        fields=[
            FieldConfig(id="hidden", type="checkbox", label="Hidden", show_if="false"),
            FieldConfig(id="desktop", type="checkbox", label="Desktop", default=True),
            FieldConfig(id="channel", type="select", label="Channel", choices=["stable", "beta"], default="stable"),
            FieldConfig(id="selected_features", type="multiselect", label="Features"),
            FieldConfig(id="unused", type="text", label="Unused"),
        ],
    )
    step = OptionsStep(step_cfg, ctx, wizard)
    qtbot.addWidget(step)

    assert "hidden" not in step.controls
    assert "desktop" in step.controls
    assert "channel" in step.controls
    assert "selected_features" in step.controls
    assert step.feature_list is not None

    step.apply_state()
    assert step.controls["desktop"].isChecked() is False
    assert step.controls["channel"].currentText() == "beta"

    data = step.get_data()
    assert "selected_features" in data
    assert data["desktop"] is False
    assert data["channel"] == "beta"


def test_options_step_validate_failure_paths(monkeypatch, qtbot, tmp_path):
    ctx = make_context(
        tmp_path,
        config_overrides={"features": [{"id": "core", "label": "Core", "default": True}]},
    )
    wizard = WizardStub(make_theme("classic", source_root=tmp_path))
    step_cfg = StepConfig(
        id="options",
        type="options",
        title="Options",
        fields=[
            FieldConfig(id="desktop", type="checkbox", label="Desktop"),
            FieldConfig(id="channel", type="select", label="Channel", choices=["stable"], default="stable"),
            FieldConfig(id="selected_features", type="multiselect", label="Features"),
            FieldConfig(id="unknown", type="text", label="Unknown"),
        ],
    )
    step = OptionsStep(step_cfg, ctx, wizard)
    qtbot.addWidget(step)

    def _checkbox_fail(field, _value):
        if field.id == "desktop":
            return False, "checkbox fail"
        return True, None

    monkeypatch.setattr("installer_framework.ui.steps.options.validate_field_value", _checkbox_fail)
    ok, message = step.validate()
    assert ok is False
    assert message == "Desktop: checkbox fail"

    step = OptionsStep(step_cfg, ctx, wizard)
    qtbot.addWidget(step)

    def _select_fail(field, _value):
        if field.id == "channel":
            return False, "select fail"
        return True, None

    monkeypatch.setattr("installer_framework.ui.steps.options.validate_field_value", _select_fail)
    ok, message = step.validate()
    assert ok is False
    assert message == "Channel: select fail"

    step = OptionsStep(step_cfg, ctx, wizard)
    qtbot.addWidget(step)

    def _multiselect_fail(field, _value):
        if field.id == "selected_features":
            return False, "multi fail"
        return True, None

    monkeypatch.setattr("installer_framework.ui.steps.options.validate_field_value", _multiselect_fail)
    ok, message = step.validate()
    assert ok is False
    assert message == "Features: multi fail"
