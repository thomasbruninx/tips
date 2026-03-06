"""Plugin registry for step/action handlers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from installer_framework.engine.action_base import Action
from installer_framework.plugins.models import PluginSchemaExtension, PluginStatus
from installer_framework.ui.step_base import StepWidget


@dataclass(slots=True)
class PluginRegistry:
    action_classes: dict[str, type[Action]] = field(default_factory=dict)
    step_classes: dict[str, type[StepWidget]] = field(default_factory=dict)
    action_sources: dict[str, str] = field(default_factory=dict)
    step_sources: dict[str, str] = field(default_factory=dict)
    schema_extensions: list[PluginSchemaExtension] = field(default_factory=list)
    statuses: list[PluginStatus] = field(default_factory=list)

    def register_action(self, handle: str, action_class: type[Action], source: str) -> None:
        if handle in self.action_classes:
            existing = self.action_sources.get(handle, "<unknown>")
            raise ValueError(f"Duplicate action handle '{handle}' from {source}; already registered by {existing}")
        self.action_classes[handle] = action_class
        self.action_sources[handle] = source

    def register_step(self, handle: str, step_class: type[StepWidget], source: str) -> None:
        if handle in self.step_classes:
            existing = self.step_sources.get(handle, "<unknown>")
            raise ValueError(f"Duplicate step handle '{handle}' from {source}; already registered by {existing}")
        self.step_classes[handle] = step_class
        self.step_sources[handle] = source

    def get_action_class(self, handle: str) -> type[Action] | None:
        return self.action_classes.get(handle)

    def get_step_class(self, handle: str) -> type[StepWidget] | None:
        return self.step_classes.get(handle)

    def add_extension(self, extension: PluginSchemaExtension) -> None:
        self.schema_extensions.append(extension)

    def add_status(self, status: PluginStatus) -> None:
        self.statuses.append(status)

    def step_handles(self) -> set[str]:
        return set(self.step_classes.keys())

    def action_handles(self) -> set[str]:
        return set(self.action_classes.keys())



def build_registry_with_builtins() -> PluginRegistry:
    """Create a registry pre-populated with framework built-ins."""
    from installer_framework.engine.actions.copy_files import CopyFilesAction
    from installer_framework.engine.actions.desktop_entry_linux import CreateDesktopEntryAction
    from installer_framework.engine.actions.dotfile import WriteDotfileAction
    from installer_framework.engine.actions.registry import ReadRegistryAction, WriteRegistryAction
    from installer_framework.engine.actions.run_script import RunScriptAction
    from installer_framework.engine.actions.shortcut_windows import CreateShortcutAction
    from installer_framework.engine.actions.show_message import ShowMessageAction
    from installer_framework.ui.steps.directory import DirectoryStep
    from installer_framework.ui.steps.finish import FinishStep
    from installer_framework.ui.steps.form import FormStep
    from installer_framework.ui.steps.install import InstallStep
    from installer_framework.ui.steps.license import LicenseStep
    from installer_framework.ui.steps.options import OptionsStep
    from installer_framework.ui.steps.ready import ReadyStep
    from installer_framework.ui.steps.scope import ScopeStep
    from installer_framework.ui.steps.welcome import WelcomeStep

    registry = PluginRegistry()

    builtin_actions: dict[str, type[Action]] = {
        "copy_files": CopyFilesAction,
        "write_registry": WriteRegistryAction,
        "read_registry": ReadRegistryAction,
        "write_dotfile": WriteDotfileAction,
        "create_shortcut": CreateShortcutAction,
        "create_desktop_entry": CreateDesktopEntryAction,
        "show_message": ShowMessageAction,
        "run_script": RunScriptAction,
    }
    for handle, action_class in builtin_actions.items():
        registry.register_action(handle, action_class, source="builtin")

    builtin_steps: dict[str, type[StepWidget]] = {
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
    for handle, step_class in builtin_steps.items():
        registry.register_step(handle, step_class, source="builtin")

    return registry



def registry_summary(registry: PluginRegistry) -> dict[str, Any]:
    return {
        "actions": sorted(registry.action_classes.keys()),
        "steps": sorted(registry.step_classes.keys()),
        "statuses": [asdict(status) for status in registry.statuses],
    }
