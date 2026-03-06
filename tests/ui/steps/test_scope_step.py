from __future__ import annotations

from installer_framework.config.models import StepConfig
from installer_framework.ui.steps.scope import ScopeStep
from tests.helpers.context_factory import make_context
from tests.helpers.qt_helpers import WizardStub, make_theme


def test_scope_step_get_data(qtbot, tmp_path):
    ctx = make_context(tmp_path)
    wizard = WizardStub(make_theme("classic", source_root=tmp_path))
    step = ScopeStep(StepConfig(id="scope", type="scope", title="Scope"), ctx, wizard)
    qtbot.addWidget(step)

    step.system_radio.setChecked(True)
    data = step.get_data()
    assert data["install_scope"] == "system"
