from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from PyQt6.QtWidgets import QWidget

from installer_framework.config.models import StepConfig
from installer_framework.engine.runner import ActionResult
from installer_framework.ui.wizard import Wizard
from tests.helpers.context_factory import default_env, make_context


class _DummyStep(QWidget):
    def __init__(self, valid=(True, None), data=None):
        super().__init__()
        self._valid = valid
        self._data = data or {}
        self.apply_count = 0
        self.show_count = 0

    def apply_state(self):
        self.apply_count += 1

    def on_show(self):
        self.show_count += 1

    def validate(self):
        return self._valid

    def get_data(self):
        return dict(self._data)


class _FakeQApplication:
    @staticmethod
    def instance():
        return SimpleNamespace(quit=lambda: None)


def test_wizard_logo_resolution_and_visible_steps(qtbot, tmp_path, monkeypatch):
    ctx = make_context(tmp_path, config_overrides={"theme": {"style": "modern"}})
    logo = tmp_path / "logo.png"
    logo.write_text("x", encoding="utf-8")
    ctx.config.branding.logo_path = "logo.png"
    ctx.config.install_scope = "user"

    monkeypatch.setattr("installer_framework.ui.wizard.show_message_dialog", lambda *args, **kwargs: None)
    monkeypatch.setattr("installer_framework.ui.wizard.show_confirm_dialog", lambda *args, **kwargs: None)
    monkeypatch.setattr("installer_framework.ui.steps.install.InstallStep.start_install", lambda self: None)

    wizard = Wizard(config=ctx.config, ctx=ctx)
    qtbot.addWidget(wizard)

    assert wizard._resolve_branding_logo() == logo.resolve()
    wizard.refresh_visible_steps()
    assert "scope" not in {step.type for step in wizard.visible_steps}

    ctx.config.branding.logo_path = "missing.png"
    assert wizard._resolve_branding_logo() is None


def test_wizard_update_nav_states(qtbot, tmp_path, monkeypatch):
    ctx = make_context(tmp_path)
    monkeypatch.setattr("installer_framework.ui.wizard.show_message_dialog", lambda *args, **kwargs: None)
    monkeypatch.setattr("installer_framework.ui.wizard.show_confirm_dialog", lambda *args, **kwargs: None)
    monkeypatch.setattr("installer_framework.ui.steps.install.InstallStep.start_install", lambda self: None)

    wizard = Wizard(config=ctx.config, ctx=ctx)
    qtbot.addWidget(wizard)
    wizard.show()

    wizard.show_step(wizard._index_of_type("ready"))
    assert wizard.install_btn.isHidden() is False
    assert wizard.next_btn.isHidden() is True

    wizard.show_step(wizard._index_of_type("finish"))
    assert wizard.next_btn.text() == "Finish"
    assert wizard.next_btn.isEnabled() is True

    wizard.show_step(wizard._index_of_type("install"))
    assert wizard.next_btn.isEnabled() is False
    assert wizard.back_btn.isEnabled() is False


def test_wizard_header_receives_step_typography_preset(qtbot, tmp_path, monkeypatch):
    ctx = make_context(tmp_path)
    monkeypatch.setattr("installer_framework.ui.wizard.show_message_dialog", lambda *args, **kwargs: None)
    monkeypatch.setattr("installer_framework.ui.wizard.show_confirm_dialog", lambda *args, **kwargs: None)
    monkeypatch.setattr("installer_framework.ui.steps.install.InstallStep.start_install", lambda self: None)

    wizard = Wizard(config=ctx.config, ctx=ctx)
    qtbot.addWidget(wizard)
    wizard.visible_steps[0].typography_preset = "default"

    captured: list[str | None] = []

    def _capture_header(*args, **kwargs):
        captured.append(kwargs.get("typography_preset"))
        return QWidget()

    monkeypatch.setattr(wizard.widget_factory, "create_header", _capture_header)
    wizard.show_step(0)
    assert captured[-1] == "default"


def test_wizard_commit_step_navigation_override_and_state_updates(qtbot, tmp_path, monkeypatch):
    ctx = make_context(tmp_path)
    monkeypatch.setattr("installer_framework.ui.wizard.show_message_dialog", lambda *args, **kwargs: None)
    monkeypatch.setattr("installer_framework.ui.wizard.show_confirm_dialog", lambda *args, **kwargs: None)

    wizard = Wizard(config=ctx.config, ctx=ctx)
    qtbot.addWidget(wizard)

    step_cfg = StepConfig(
        id="dummy",
        type="welcome",
        title="Dummy",
        navigation={"next": "finish"},
    )
    dummy = _DummyStep(
        valid=(True, None),
        data={
            "username": "alice",
            "selected_features": ["core", "docs"],
            "install_scope": "system",
        },
    )

    called = {"saved": False, "shown": None}
    monkeypatch.setattr(wizard, "_current_step", lambda: (dummy, step_cfg))
    monkeypatch.setattr("installer_framework.ui.wizard.default_install_dir", lambda *args, **kwargs: Path("/tmp/system-default"))
    monkeypatch.setattr(type(ctx), "save_resume", lambda self: called.__setitem__("saved", True))
    monkeypatch.setattr(wizard, "show_step", lambda idx: called.__setitem__("shown", idx))

    assert wizard._commit_step() is False
    assert ctx.state.answers["username"] == "alice"
    assert ctx.state.selected_features == ["core", "docs"]
    assert ctx.state.install_scope == "system"
    assert ctx.state.install_dir == "/tmp/system-default"
    assert called["saved"] is True
    assert called["shown"] is not None


def test_wizard_go_next_finish_and_begin_install_branches(qtbot, tmp_path, monkeypatch):
    ctx = make_context(tmp_path)
    calls: list[tuple] = []
    monkeypatch.setattr("installer_framework.ui.wizard.show_message_dialog", lambda *args, **kwargs: calls.append(args))
    monkeypatch.setattr("installer_framework.ui.wizard.show_confirm_dialog", lambda *args, **kwargs: None)
    monkeypatch.setattr("installer_framework.ui.wizard.QApplication", _FakeQApplication)
    monkeypatch.setattr("installer_framework.ui.steps.install.InstallStep.start_install", lambda self: None)

    wizard = Wizard(config=ctx.config, ctx=ctx)
    qtbot.addWidget(wizard)

    close_called = {"value": False}
    monkeypatch.setattr(wizard, "close", lambda: close_called.__setitem__("value", True))
    wizard.show_step(wizard._index_of_type("finish"))
    wizard.go_next()
    assert close_called["value"] is True

    invoked = {"priv": False, "shown": None}
    monkeypatch.setattr(wizard, "_commit_step", lambda: False)
    monkeypatch.setattr(wizard, "_ensure_scope_privileges", lambda: invoked.__setitem__("priv", True) or True)
    wizard.begin_install()
    assert invoked["priv"] is False

    monkeypatch.setattr(wizard, "_commit_step", lambda: True)
    monkeypatch.setattr(wizard, "_ensure_scope_privileges", lambda: False)
    monkeypatch.setattr(wizard, "show_step", lambda idx: invoked.__setitem__("shown", idx))
    wizard.begin_install()
    assert invoked["shown"] is None

    ctx.state.answers["upgrade_mode"] = "uninstall_first"
    ctx.state.detected_upgrade = {"install_dir": str(tmp_path / "missing")}
    monkeypatch.setattr(wizard, "_ensure_scope_privileges", lambda: True)
    wizard.begin_install()
    assert calls and "Uninstall manifest not found" in calls[-1][1]


def test_wizard_install_finished_and_cancel_confirm_paths(qtbot, tmp_path, monkeypatch):
    ctx = make_context(tmp_path)
    messages: list[tuple] = []
    monkeypatch.setattr("installer_framework.ui.wizard.show_message_dialog", lambda *args, **kwargs: messages.append(args))
    monkeypatch.setattr("installer_framework.ui.wizard.show_confirm_dialog", lambda title, message, callback: callback(True))
    monkeypatch.setattr("installer_framework.ui.wizard.QApplication", _FakeQApplication)
    monkeypatch.setattr("installer_framework.ui.steps.install.InstallStep.start_install", lambda self: None)

    wizard = Wizard(config=ctx.config, ctx=ctx)
    qtbot.addWidget(wizard)
    cleared = {"value": False}
    monkeypatch.setattr(type(ctx), "clear_resume", lambda self: cleared.__setitem__("value", True))

    wizard.on_install_finished(ActionResult(success=True, cancelled=False))
    assert cleared["value"] is True
    assert wizard.visible_steps[wizard.current_index].type == "finish"

    shown_indices: list[int] = []
    monkeypatch.setattr(wizard, "show_step", lambda idx: shown_indices.append(idx))
    wizard.on_install_finished(
        ActionResult(
            success=False,
            cancelled=False,
            error="Uninstall-first failed: boom",
            rollback_performed=True,
            rollback_errors=["x"],
        )
    )
    assert shown_indices[-1] == wizard._index_of_type("ready")

    close_called = {"value": False}
    monkeypatch.setattr(wizard, "close", lambda: close_called.__setitem__("value", True))
    wizard.show_step(wizard._index_of_type("welcome"))
    wizard.cancel_install("user")
    assert close_called["value"] is True


def test_wizard_privilege_paths_with_relaunch(qtbot, tmp_path, monkeypatch):
    ctx = make_context(tmp_path, config_overrides={"windows": {"allow_uac_elevation": True}})
    ctx.state.install_scope = "system"
    ctx.is_elevated = False
    ctx.env = default_env(os_name="windows")

    monkeypatch.setattr("installer_framework.ui.wizard.show_message_dialog", lambda *args, **kwargs: None)
    monkeypatch.setattr("installer_framework.ui.wizard.show_confirm_dialog", lambda *args, **kwargs: None)
    monkeypatch.setattr("installer_framework.ui.wizard.QApplication", _FakeQApplication)
    monkeypatch.setattr("installer_framework.ui.wizard.relaunch_as_admin_windows", lambda _argv: True)
    monkeypatch.setattr("installer_framework.ui.steps.install.InstallStep.start_install", lambda self: None)

    wizard = Wizard(config=ctx.config, ctx=ctx)
    qtbot.addWidget(wizard)
    assert wizard._ensure_scope_privileges() is False

    ctx_macos = make_context(
        tmp_path,
        config_overrides={
            "macos": {"allow_rights_elevation": True},
            "unix": {"allow_sudo_relaunch": True},
        },
    )
    ctx_macos.state.install_scope = "system"
    ctx_macos.is_elevated = False
    ctx_macos.env = default_env(os_name="darwin")

    monkeypatch.setattr("installer_framework.ui.wizard.relaunch_as_admin_macos", lambda _argv: True)
    monkeypatch.setattr(
        "installer_framework.ui.wizard.relaunch_with_sudo_unix",
        lambda _argv: (_ for _ in ()).throw(AssertionError("macOS path must not use unix sudo relaunch")),
    )

    wizard_macos = Wizard(config=ctx_macos.config, ctx=ctx_macos)
    qtbot.addWidget(wizard_macos)
    assert wizard_macos._ensure_scope_privileges() is False

    ctx_macos_blocked = make_context(
        tmp_path,
        config_overrides={
            "macos": {"allow_rights_elevation": False},
            "unix": {"allow_sudo_relaunch": True},
        },
    )
    ctx_macos_blocked.state.install_scope = "system"
    ctx_macos_blocked.is_elevated = False
    ctx_macos_blocked.env = default_env(os_name="darwin")
    mac_error_calls: list[tuple] = []
    monkeypatch.setattr("installer_framework.ui.wizard.show_message_dialog", lambda *args, **kwargs: mac_error_calls.append(args))

    wizard_macos_blocked = Wizard(config=ctx_macos_blocked.config, ctx=ctx_macos_blocked)
    qtbot.addWidget(wizard_macos_blocked)
    assert wizard_macos_blocked._ensure_scope_privileges() is False
    assert mac_error_calls and "Administrator privileges required" in mac_error_calls[-1][1]

    ctx2 = make_context(
        tmp_path,
        config_overrides={"unix": {"allow_sudo_relaunch": True}},
    )
    ctx2.state.install_scope = "system"
    ctx2.is_elevated = False
    ctx2.env = default_env(os_name="linux")

    monkeypatch.setattr("installer_framework.ui.wizard.relaunch_with_sudo_unix", lambda _argv: True)
    wizard2 = Wizard(config=ctx2.config, ctx=ctx2)
    qtbot.addWidget(wizard2)
    assert wizard2._ensure_scope_privileges() is False

    ctx3 = make_context(
        tmp_path,
        config_overrides={"unix": {"allow_sudo_relaunch": False}},
    )
    ctx3.state.install_scope = "system"
    ctx3.is_elevated = False
    ctx3.env = default_env(os_name="linux")
    error_calls: list[tuple] = []
    monkeypatch.setattr("installer_framework.ui.wizard.show_message_dialog", lambda *args, **kwargs: error_calls.append(args))

    wizard3 = Wizard(config=ctx3.config, ctx=ctx3)
    qtbot.addWidget(wizard3)
    assert wizard3._ensure_scope_privileges() is False
    assert error_calls and "Root privileges required" in error_calls[-1][1]
