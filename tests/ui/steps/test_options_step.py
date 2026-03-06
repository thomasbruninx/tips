from __future__ import annotations

from installer_framework.config.models import FeatureConfig, FieldConfig, StepConfig
from installer_framework.ui.steps.options import OptionsStep
from tests.helpers.context_factory import make_context
from tests.helpers.qt_helpers import WizardStub, make_theme


def test_options_step_collects_multiselect_and_checkbox(qtbot, tmp_path):
    ctx = make_context(
        tmp_path,
        config_overrides={
            "features": [
                {"id": "core", "label": "Core", "default": True},
                {"id": "docs", "label": "Docs", "default": False},
            ]
        },
    )
    wizard = WizardStub(make_theme("classic", source_root=tmp_path))
    step_cfg = StepConfig(
        id="options",
        type="options",
        title="Options",
        fields=[
            FieldConfig(id="desktop", type="checkbox", label="Desktop", default=True),
            FieldConfig(id="selected_features", type="multiselect", label="Features"),
        ],
    )
    step = OptionsStep(step_cfg, ctx, wizard)
    qtbot.addWidget(step)

    data = step.get_data()
    assert "selected_features" in data
    assert data["desktop"] is True
