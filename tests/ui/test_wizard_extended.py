from __future__ import annotations

from pathlib import Path

from installer_framework.engine.runner import ActionResult
from installer_framework.ui.wizard import Wizard
from tests.helpers.context_factory import default_env, make_context


def test_wizard_commit_license_validation_error_shows_dialog(qtbot, tmp_path, monkeypatch):
    ctx = make_context(tmp_path)
    calls = []
    monkeypatch.setattr("installer_framework.ui.wizard.show_message_dialog", lambda *args, **kwargs: calls.append(args))
    monkeypatch.setattr("installer_framework.ui.wizard.show_confirm_dialog", lambda *_args, **_kwargs: None)

    wizard = Wizard(config=ctx.config, ctx=ctx)
    qtbot.addWidget(wizard)
    wizard.show_step(wizard._index_of_type("license"))

    assert wizard._commit_step() is False
    assert calls


def test_wizard_commit_scope_updates_install_dir(qtbot, tmp_path, monkeypatch):
    ctx = make_context(tmp_path)
    monkeypatch.setattr("installer_framework.ui.wizard.default_install_dir", lambda *args, **kwargs: Path("/tmp/system-dir"))
    monkeypatch.setattr("installer_framework.ui.wizard.show_message_dialog", lambda *args, **kwargs: None)

    wizard = Wizard(config=ctx.config, ctx=ctx)
    qtbot.addWidget(wizard)
    wizard.show_step(wizard._index_of_type("scope"))

    step, _cfg = wizard._current_step()
    step.system_radio.setChecked(True)
    assert wizard._commit_step() is True
    assert ctx.state.install_scope == "system"
    assert ctx.state.install_dir == "/tmp/system-dir"


def test_wizard_on_install_finished_error_path(qtbot, tmp_path, monkeypatch):
    ctx = make_context(tmp_path)
    calls = []
    monkeypatch.setattr("installer_framework.ui.wizard.show_message_dialog", lambda *args, **kwargs: calls.append(args))
    wizard = Wizard(config=ctx.config, ctx=ctx)
    qtbot.addWidget(wizard)

    wizard.on_install_finished(
        ActionResult(success=False, cancelled=False, error="boom", rollback_performed=True, rollback_errors=[])
    )
    assert calls
    assert wizard.visible_steps[wizard.current_index].type == "finish"


def test_wizard_ensure_scope_privileges_windows_error(qtbot, tmp_path, monkeypatch):
    ctx = make_context(tmp_path)
    ctx.state.install_scope = "system"
    ctx.is_elevated = False
    ctx.env = default_env(os_name="windows")

    calls = []
    monkeypatch.setattr("installer_framework.ui.wizard.show_message_dialog", lambda *args, **kwargs: calls.append(args))
    monkeypatch.setattr("installer_framework.ui.wizard.relaunch_as_admin_windows", lambda _argv: False)

    wizard = Wizard(config=ctx.config, ctx=ctx)
    qtbot.addWidget(wizard)

    assert wizard._ensure_scope_privileges() is False
    assert calls
