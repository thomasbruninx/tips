"""Factory mapping step.type to concrete Kivy widget."""

from __future__ import annotations

from installer_framework.config.models import StepConfig
from installer_framework.engine.context import InstallerContext
from installer_framework.ui.step_base import StepWidget
from installer_framework.ui.steps.directory import DirectoryStep
from installer_framework.ui.steps.finish import FinishStep
from installer_framework.ui.steps.form import FormStep
from installer_framework.ui.steps.install import InstallStep
from installer_framework.ui.steps.license import LicenseStep
from installer_framework.ui.steps.options import OptionsStep
from installer_framework.ui.steps.ready import ReadyStep
from installer_framework.ui.steps.scope import ScopeStep
from installer_framework.ui.steps.welcome import WelcomeStep


class StepFactory:
    _mapping = {
        "welcome": WelcomeStep,
        "license": LicenseStep,
        "scope": ScopeStep,
        "directory": DirectoryStep,
        "options": OptionsStep,
        "form": FormStep,
        "ready": ReadyStep,
        "install": InstallStep,
        "finish": FinishStep,
    }

    @classmethod
    def create(cls, step: StepConfig, ctx: InstallerContext, wizard) -> StepWidget:
        widget_cls = cls._mapping.get(step.type)
        if widget_cls is None:
            raise ValueError(f"Unknown step type: {step.type}")
        return widget_cls(step_config=step, ctx=ctx, wizard=wizard)
