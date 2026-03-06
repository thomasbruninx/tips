from __future__ import annotations

from installer_framework.config.models import StepConfig
from installer_framework.ui.step_base import StepWidget
from tests.helpers.context_factory import make_context
from tests.helpers.qt_helpers import WizardStub, make_theme


class DemoStep(StepWidget):
    pass


def test_step_base_description_resolution(qtbot, tmp_path):
    ctx = make_context(tmp_path)
    theme = make_theme("classic", source_root=tmp_path)
    wizard = WizardStub(theme)
    step_cfg = StepConfig(id="s1", type="demo", title="Title", description="Shared", body_description="Body")
    widget = DemoStep(step_cfg, ctx, wizard)
    qtbot.addWidget(widget)

    assert widget.resolved_body_description() == "Body"
    label = widget.description_label()
    assert label.text() == "Body"
