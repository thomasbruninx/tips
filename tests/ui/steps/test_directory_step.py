from __future__ import annotations

from installer_framework.config.models import FieldConfig, StepConfig
from installer_framework.ui.steps.directory import DirectoryStep
from tests.helpers.context_factory import make_context
from tests.helpers.qt_helpers import WizardStub, make_theme


def test_directory_step_validation(qtbot, tmp_path):
    ctx = make_context(tmp_path)
    wizard = WizardStub(make_theme("classic", source_root=tmp_path))
    step_cfg = StepConfig(
        id="directory",
        type="directory",
        title="Directory",
        fields=[FieldConfig(id="install_dir", type="directory", label="Install", required=True)],
    )
    step = DirectoryStep(step_cfg, ctx, wizard)
    qtbot.addWidget(step)

    step.path_input.setText(str(tmp_path / "target"))
    ok, _ = step.validate()
    assert ok is True
