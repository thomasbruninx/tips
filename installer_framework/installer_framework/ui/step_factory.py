"""Factory mapping step.type to concrete Qt widget."""

from __future__ import annotations

from installer_framework.config.models import StepConfig
from installer_framework.engine.context import InstallerContext
from installer_framework.plugins.registry import build_registry_with_builtins
from installer_framework.ui.step_base import StepWidget


class StepFactory:
    @classmethod
    def create(cls, step: StepConfig, ctx: InstallerContext, wizard) -> StepWidget:
        registry = ctx.plugin_registry or getattr(ctx.config, "plugin_registry", None)
        if registry is None:
            registry = build_registry_with_builtins()
            ctx.plugin_registry = registry
        widget_cls = registry.get_step_class(step.type)
        if widget_cls is None:
            raise ValueError(f"Unknown step type: {step.type}")
        return widget_cls(step_config=step, ctx=ctx, wizard=wizard)
