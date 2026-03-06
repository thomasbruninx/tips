from __future__ import annotations

from installer_framework.config.models import StepConfig
from installer_framework.ui.steps.finish import FinishStep
from tests.helpers.context_factory import make_context
from tests.helpers.qt_helpers import WizardStub, make_theme


def test_finish_step_shows_success_summary(qtbot, tmp_path):
    ctx = make_context(tmp_path)
    ctx.state.result_summary = {"success": True, "install_dir": "/tmp/app", "scope": "user"}

    wizard = WizardStub(make_theme("classic", source_root=tmp_path))
    step = FinishStep(StepConfig(id="finish", type="finish", title="Finish"), ctx, wizard)
    qtbot.addWidget(step)

    step.on_show()
    assert "completed successfully" in step.summary.text().lower()
