from __future__ import annotations

from installer_framework.config.models import StepConfig
from installer_framework.ui.steps.welcome import WelcomeStep
from tests.helpers.context_factory import make_context
from tests.helpers.qt_helpers import WizardStub, make_theme


def test_welcome_step_upgrade_visibility(qtbot, tmp_path):
    ctx = make_context(tmp_path)
    wizard = WizardStub(make_theme("classic", source_root=tmp_path))
    step = WelcomeStep(StepConfig(id="welcome", type="welcome", title="Welcome", description="Hello"), ctx, wizard)
    qtbot.addWidget(step)
    step.show()

    ctx.state.detected_upgrade = None
    step.on_show()
    assert step.upgrade_group.isHidden() is True

    ctx.state.detected_upgrade = {"version": "1.0", "install_dir": "/tmp/app"}
    step.on_show()
    assert step.upgrade_group.isHidden() is False
