from __future__ import annotations

from installer_framework.config.models import FieldConfig, StepConfig
from installer_framework.ui.steps.form import FormStep
from tests.helpers.context_factory import make_context
from tests.helpers.qt_helpers import WizardStub, make_theme


def test_form_step_builds_controls_apply_state_and_get_data(qtbot, tmp_path):
    ctx = make_context(tmp_path)
    ctx.state.answers.update({"username": "saved-user", "accept_terms": False, "channel": "beta"})

    wizard = WizardStub(make_theme("classic", source_root=tmp_path))
    step_cfg = StepConfig(
        id="form",
        type="form",
        title="Form",
        fields=[
            FieldConfig(id="hidden", type="text", label="Hidden", show_if="false"),
            FieldConfig(id="username", type="text", label="Username", required=True),
            FieldConfig(id="password", type="password", label="Password"),
            FieldConfig(id="accept_terms", type="checkbox", label="Accept terms", default=True),
            FieldConfig(id="channel", type="select", label="Channel", choices=["stable", "beta"], default="stable"),
        ],
    )
    step = FormStep(step_cfg, ctx, wizard)
    qtbot.addWidget(step)

    assert "hidden" not in step.controls
    assert {"username", "password", "accept_terms", "channel"}.issubset(set(step.controls.keys()))

    step.apply_state()
    assert step.controls["username"].value == "saved-user"
    assert step.controls["accept_terms"].isChecked() is False
    assert step.controls["channel"].currentText() == "beta"

    step.controls["username"].set_value("new-user")
    step.controls["password"].set_value("secret")
    step.controls["accept_terms"].setChecked(True)
    step.controls["channel"].setCurrentText("stable")
    data = step.get_data()
    assert data["username"] == "new-user"
    assert data["password"] == "secret"
    assert data["accept_terms"] is True
    assert data["channel"] == "stable"


def test_form_step_validate_failure_paths(monkeypatch, qtbot, tmp_path):
    ctx = make_context(tmp_path)
    wizard = WizardStub(make_theme("classic", source_root=tmp_path))
    step_cfg = StepConfig(
        id="form",
        type="form",
        title="Form",
        fields=[
            FieldConfig(id="username", type="text", label="Username", required=True),
            FieldConfig(id="accept_terms", type="checkbox", label="Accept terms"),
            FieldConfig(id="channel", type="select", label="Channel", choices=["stable"], default="stable"),
        ],
    )
    step = FormStep(step_cfg, ctx, wizard)
    qtbot.addWidget(step)
    step.controls["username"].set_value("ok")

    def _field_fail(field, _value):
        if field.id == "username":
            return False, "bad text"
        return True, None

    monkeypatch.setattr("installer_framework.ui.steps.form.validate_field_value", _field_fail)
    ok, message = step.validate()
    assert ok is False
    assert message == "Username: bad text"

    step = FormStep(step_cfg, ctx, wizard)
    qtbot.addWidget(step)
    step.controls["username"].set_value("ok")
    step.controls["accept_terms"].setChecked(False)

    def _checkbox_fail(field, _value):
        if field.id == "accept_terms":
            return False, "must accept"
        return True, None

    monkeypatch.setattr("installer_framework.ui.steps.form.validate_field_value", _checkbox_fail)
    ok, message = step.validate()
    assert ok is False
    assert message == "Accept terms: must accept"

    step = FormStep(step_cfg, ctx, wizard)
    qtbot.addWidget(step)
    step.controls["username"].set_value("ok")
    step.controls["accept_terms"].setChecked(True)

    def _select_fail(field, _value):
        if field.id == "channel":
            return False, "bad channel"
        return True, None

    monkeypatch.setattr("installer_framework.ui.steps.form.validate_field_value", _select_fail)
    ok, message = step.validate()
    assert ok is False
    assert message == "Channel: bad channel"
