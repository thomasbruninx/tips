from __future__ import annotations

from installer_framework.config.models import StepConfig
from installer_framework.engine.runner import ActionResult
from installer_framework.ui.steps.install import InstallStep, InstallWorker
from tests.helpers.context_factory import make_context
from tests.helpers.qt_helpers import WizardStub, make_theme


class FakeRunner:
    def __init__(self, _actions):
        pass

    def run(self, ctx, progress_callback, log_callback, message_callback=None):
        progress_callback(50, "half")
        log_callback("log")
        if message_callback:
            message_callback("info", "Title", "Msg")
        return ActionResult(success=True, cancelled=False, results=[{"ok": True}], manifest_path="/tmp/m")


def test_install_worker_sets_result_summary(monkeypatch, tmp_path):
    ctx = make_context(tmp_path)
    monkeypatch.setattr("installer_framework.ui.steps.install.ActionRunner", FakeRunner)

    worker = InstallWorker(ctx)
    emitted = []
    worker.finished.connect(lambda result: emitted.append(result))
    worker.run()

    assert emitted
    assert ctx.state.result_summary["success"] is True


def test_install_step_on_show_triggers_start(monkeypatch, qtbot, tmp_path):
    ctx = make_context(tmp_path)
    wizard = WizardStub(make_theme("classic", source_root=tmp_path))
    step = InstallStep(StepConfig(id="install", type="install", title="Install"), ctx, wizard)
    qtbot.addWidget(step)

    called = []
    monkeypatch.setattr(step, "start_install", lambda: called.append(True))
    step.on_show()
    assert called == [True]
