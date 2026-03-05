"""Installer action runner with progress/log/cancellation support."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from installer_framework.config.models import ActionConfig
from installer_framework.engine.actions.copy_files import CopyFilesAction
from installer_framework.engine.actions.desktop_entry_linux import CreateDesktopEntryAction
from installer_framework.engine.actions.dotfile import WriteDotfileAction
from installer_framework.engine.actions.registry import ReadRegistryAction, WriteRegistryAction
from installer_framework.engine.actions.run_script import RunScriptAction
from installer_framework.engine.actions.shortcut_windows import CreateShortcutAction
from installer_framework.engine.actions.show_message import ShowMessageAction
from installer_framework.engine.context import InstallerContext

ProgressCallback = Callable[[int, str], None]
LogCallback = Callable[[str], None]
MessageCallback = Callable[[str, str, str], None]


class ActionRunnerError(RuntimeError):
    """Action runner failure."""


@dataclass(slots=True)
class ActionResult:
    success: bool
    cancelled: bool
    results: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None


class ActionRunner:
    """Executes configured actions sequentially."""

    def __init__(self, actions: list[ActionConfig]) -> None:
        self.actions = actions

    def _create_action(self, cfg: ActionConfig):
        mapping = {
            "copy_files": CopyFilesAction,
            "write_registry": WriteRegistryAction,
            "read_registry": ReadRegistryAction,
            "write_dotfile": WriteDotfileAction,
            "create_shortcut": CreateShortcutAction,
            "create_desktop_entry": CreateDesktopEntryAction,
            "show_message": ShowMessageAction,
            "run_script": RunScriptAction,
        }
        cls = mapping.get(cfg.type)
        if not cls:
            raise ActionRunnerError(f"Unsupported action type: {cfg.type}")
        return cls(cfg.params)

    def run(
        self,
        ctx: InstallerContext,
        progress_callback: ProgressCallback,
        log_callback: LogCallback,
        message_callback: MessageCallback | None = None,
    ) -> ActionResult:
        results: list[dict[str, Any]] = []
        total = len(self.actions)
        try:
            for index, cfg in enumerate(self.actions, start=1):
                if ctx.is_cancelled():
                    return ActionResult(success=False, cancelled=True, results=results, error="Cancelled")

                action = self._create_action(cfg)
                action_start = int(((index - 1) / total) * 100)
                action_end = int((index / total) * 100)

                def sub_progress(value: int, message: str) -> None:
                    span = max(action_end - action_start, 1)
                    overall = action_start + int((max(0, min(value, 100)) / 100) * span)
                    progress_callback(overall, message)

                log_callback(f"Starting action: {cfg.type}")
                result = action.execute(ctx, sub_progress, log_callback)
                results.append(result)

                if cfg.type == "show_message" and message_callback:
                    message_callback(result.get("level", "info"), result.get("title", "Installer"), result.get("message", ""))

                progress_callback(action_end, f"Finished action: {cfg.type}")

            return ActionResult(success=True, cancelled=False, results=results)
        except Exception as exc:
            log_callback(f"ERROR: {exc}")
            return ActionResult(success=False, cancelled=ctx.is_cancelled(), results=results, error=str(exc))
