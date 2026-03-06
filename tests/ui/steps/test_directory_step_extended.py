from __future__ import annotations

from pathlib import Path

from installer_framework.config.models import FieldConfig, StepConfig
from installer_framework.ui.steps.directory import DirectoryStep
from tests.helpers.context_factory import make_context
from tests.helpers.qt_helpers import WizardStub, make_theme


def _make_step(tmp_path):
    ctx = make_context(tmp_path)
    wizard = WizardStub(make_theme("classic", source_root=tmp_path))
    step_cfg = StepConfig(
        id="directory",
        type="directory",
        title="Directory",
        fields=[FieldConfig(id="install_dir", type="directory", label="Install", required=True)],
    )
    return ctx, DirectoryStep(step_cfg, ctx, wizard)


def test_directory_step_on_show_and_picker(qtbot, monkeypatch, tmp_path):
    ctx, step = _make_step(tmp_path)
    qtbot.addWidget(step)
    step.show()

    ctx.state.install_dir = str(tmp_path / "existing")
    step.on_show()
    assert step.path_input.text() == str(tmp_path / "existing")

    monkeypatch.setattr(
        "installer_framework.ui.steps.directory.QFileDialog.getExistingDirectory",
        lambda *_args, **_kwargs: str(tmp_path / "picked"),
    )
    step.open_picker()
    assert step.path_input.text() == str(tmp_path / "picked")

    monkeypatch.setattr(
        "installer_framework.ui.steps.directory.QFileDialog.getExistingDirectory",
        lambda *_args, **_kwargs: "",
    )
    before = step.path_input.text()
    step.open_picker()
    assert step.path_input.text() == before


def test_directory_step_validate_empty_and_field_error(qtbot, monkeypatch, tmp_path):
    _ctx, step = _make_step(tmp_path)
    qtbot.addWidget(step)

    step.path_input.setText("")
    ok, msg = step.validate()
    assert ok is False
    assert "required" in (msg or "")

    step.path_input.setText(str(tmp_path / "x"))
    monkeypatch.setattr("installer_framework.ui.steps.directory.validate_field_value", lambda *_: (False, "bad path"))
    ok, msg = step.validate()
    assert ok is False
    assert msg == "bad path"


def test_directory_step_validate_dir_creation_and_writable_errors(qtbot, monkeypatch, tmp_path):
    _ctx, step = _make_step(tmp_path)
    qtbot.addWidget(step)

    step.path_input.setText(str(tmp_path / "target"))
    monkeypatch.setattr("installer_framework.ui.steps.directory.validate_field_value", lambda *_: (True, None))
    monkeypatch.setattr("installer_framework.ui.steps.directory.ensure_dir", lambda _p: (_ for _ in ()).throw(OSError("denied")))
    ok, msg = step.validate()
    assert ok is False
    assert "Unable to create directory" in (msg or "")

    step.path_input.setText(str(tmp_path / "target2"))
    monkeypatch.setattr("installer_framework.ui.steps.directory.ensure_dir", lambda _p: None)
    monkeypatch.setattr("installer_framework.ui.steps.directory.is_writable", lambda _p: False)
    ok, msg = step.validate()
    assert ok is False
    assert msg == "Directory is not writable"


def test_directory_step_validate_without_field_rules(qtbot, monkeypatch, tmp_path):
    ctx = make_context(tmp_path)
    wizard = WizardStub(make_theme("classic", source_root=tmp_path))
    step_cfg = StepConfig(id="directory", type="directory", title="Directory", fields=[])
    step = DirectoryStep(step_cfg, ctx, wizard)
    qtbot.addWidget(step)

    target = tmp_path / "ok"
    step.path_input.setText(str(target))
    monkeypatch.setattr("installer_framework.ui.steps.directory.ensure_dir", lambda p: Path(p).mkdir(parents=True, exist_ok=True))
    monkeypatch.setattr("installer_framework.ui.steps.directory.is_writable", lambda _p: True)
    ok, msg = step.validate()
    assert ok is True
    assert msg is None
