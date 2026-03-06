from __future__ import annotations

import pytest

from installer_framework.config.models import StepConfig
from installer_framework.ui.step_factory import StepFactory
from tests.helpers.context_factory import make_context
from tests.helpers.qt_helpers import WizardStub, make_theme


def test_step_factory_creates_known_step(tmp_path):
    ctx = make_context(tmp_path)
    wizard = WizardStub(make_theme("classic", source_root=tmp_path))
    step = StepConfig(id="w", type="welcome", title="Welcome")
    widget = StepFactory.create(step, ctx, wizard)
    assert widget.step_config.id == "w"


def test_step_factory_unknown_type_raises(tmp_path):
    ctx = make_context(tmp_path)
    wizard = WizardStub(make_theme("classic", source_root=tmp_path))
    step = StepConfig(id="x", type="missing", title="Missing")
    with pytest.raises(ValueError):
        StepFactory.create(step, ctx, wizard)
