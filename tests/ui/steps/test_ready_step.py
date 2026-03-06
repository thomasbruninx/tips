from __future__ import annotations

from installer_framework.config.models import StepConfig
from installer_framework.ui.steps.ready import ReadyStep
from tests.helpers.context_factory import make_context
from tests.helpers.qt_helpers import WizardStub, make_theme


def test_ready_step_renders_summary(qtbot, tmp_path):
    ctx = make_context(tmp_path)
    ctx.state.answers = {"username": "alice", "password": "secret"}
    ctx.state.selected_features = ["core"]

    wizard = WizardStub(make_theme("classic", source_root=tmp_path))
    step = ReadyStep(StepConfig(id="ready", type="ready", title="Ready"), ctx, wizard)
    qtbot.addWidget(step)

    step.on_show()
    text = step.summary.text()
    assert "Install scope" in text
    assert "password" not in text.lower()
