from __future__ import annotations

from installer_framework.ui.wizard import Wizard
from tests.helpers.context_factory import make_context


def test_wizard_initializes_and_shows_first_step(qtbot, tmp_path, monkeypatch):
    ctx = make_context(tmp_path)
    monkeypatch.setattr("installer_framework.ui.wizard.show_message_dialog", lambda *args, **kwargs: None)
    monkeypatch.setattr("installer_framework.ui.wizard.show_confirm_dialog", lambda *_args, **_kwargs: None)

    wizard = Wizard(config=ctx.config, ctx=ctx)
    qtbot.addWidget(wizard)

    assert wizard.visible_steps
    assert wizard.current_index == 0


def test_wizard_cancel_during_install_requests_cancel(qtbot, tmp_path, monkeypatch):
    ctx = make_context(tmp_path)
    monkeypatch.setattr("installer_framework.ui.steps.install.InstallStep.start_install", lambda self: None)
    wizard = Wizard(config=ctx.config, ctx=ctx)
    qtbot.addWidget(wizard)
    wizard.show_step(wizard._index_of_type("install"))

    calls = []
    monkeypatch.setattr("installer_framework.ui.wizard.show_message_dialog", lambda *args, **kwargs: calls.append(args))
    wizard.cancel_install("x")

    assert ctx.is_cancelled() is True
    assert calls
