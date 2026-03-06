from __future__ import annotations

from installer_framework.config.models import StepConfig
from installer_framework.ui.steps.license import LicenseStep
from tests.helpers.context_factory import make_context
from tests.helpers.qt_helpers import WizardStub, make_theme


def test_license_step_requires_acceptance(qtbot, tmp_path):
    license_file = tmp_path / "license.txt"
    license_file.write_text("terms", encoding="utf-8")

    ctx = make_context(tmp_path)
    wizard = WizardStub(make_theme("classic", source_root=tmp_path))
    cfg = StepConfig(id="license", type="license", title="License", license_path=str(license_file))
    step = LicenseStep(cfg, ctx, wizard)
    qtbot.addWidget(step)

    ok, _ = step.validate()
    assert ok is False

    step.agree_row.checkbox.setChecked(True)
    ok, _ = step.validate()
    assert ok is True
