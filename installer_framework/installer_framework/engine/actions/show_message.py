"""show_message action implementation."""

from __future__ import annotations

from typing import Any

from installer_framework.engine.action_base import Action
from installer_framework.engine.context import InstallerContext


class ShowMessageAction(Action):
    def __init__(self, params: dict[str, Any]) -> None:
        self.params = params

    def execute(self, ctx: InstallerContext, progress, log) -> dict:
        level = self.params.get("level", "info")
        title = self.params.get("title", "Installer")
        message = str(self.params.get("message", ""))
        message = message.format(
            install_dir=ctx.state.install_dir,
            scope=ctx.state.install_scope,
            version=ctx.config.branding.version,
        )
        log(f"[{level}] {title}: {message}")
        progress(100, "Message displayed")
        return {"action": "show_message", "level": level, "title": title, "message": message}
