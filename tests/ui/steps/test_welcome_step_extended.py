from __future__ import annotations

from installer_framework.config.models import StepConfig
from installer_framework.ui.steps.welcome import WelcomeStep
from tests.helpers.context_factory import make_context
from tests.helpers.qt_helpers import WizardStub, make_theme


def test_welcome_step_apply_state_selects_expected_radio(qtbot, tmp_path):
    ctx = make_context(tmp_path)
    wizard = WizardStub(make_theme("classic", source_root=tmp_path))
    step = WelcomeStep(StepConfig(id="welcome", type="welcome", title="Welcome"), ctx, wizard)
    qtbot.addWidget(step)

    ctx.state.answers["upgrade_mode"] = "change_directory"
    step.apply_state()
    assert step.radio_change_dir.isChecked() is True

    ctx.state.answers["upgrade_mode"] = "uninstall_first"
    step.apply_state()
    assert step.radio_uninstall.isChecked() is True


def test_welcome_step_get_data_for_each_upgrade_mode(qtbot, tmp_path):
    ctx = make_context(tmp_path)
    wizard = WizardStub(make_theme("classic", source_root=tmp_path))
    step = WelcomeStep(StepConfig(id="welcome", type="welcome", title="Welcome"), ctx, wizard)
    qtbot.addWidget(step)
    step.show()

    assert step.get_data() == {}

    ctx.state.detected_upgrade = {"version": "1.0.0", "install_dir": "/tmp/tips"}
    step.on_show()

    step.radio_in_place.setChecked(True)
    assert step.get_data() == {"upgrade_mode": "upgrade_in_place"}

    step.radio_change_dir.setChecked(True)
    assert step.get_data() == {"upgrade_mode": "change_directory"}

    step.radio_uninstall.setChecked(True)
    assert step.get_data() == {"upgrade_mode": "uninstall_first"}
