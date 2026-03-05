"""Linux desktop entry creation action."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from installer_framework.engine.action_base import Action
from installer_framework.engine.context import InstallerContext
from installer_framework.util.fs import ensure_dir


class CreateDesktopEntryAction(Action):
    def __init__(self, params: dict[str, Any]) -> None:
        self.params = params

    def _entry_path(self, scope: str, app_id: str) -> Path:
        if scope == "system":
            return Path("/usr/share/applications") / f"{app_id}.desktop"
        return Path.home() / ".local" / "share" / "applications" / f"{app_id}.desktop"

    def execute(self, ctx: InstallerContext, progress, log) -> dict:
        if not ctx.env.is_linux:
            log("create_desktop_entry skipped on non-Linux platform")
            return {"action": "create_desktop_entry", "skipped": True}

        app_name = self.params.get("name") or ctx.config.branding.product_name
        app_id = self.params.get("id") or ctx.config.product_id
        icon = self.params.get("icon", "")
        target = self.params.get("exec")
        if not target:
            target = str(Path(ctx.state.install_dir) / self.params.get("exec_relative", app_name.lower()))

        path = self._entry_path(ctx.state.install_scope, app_id)
        ensure_dir(path.parent)
        content = "\n".join(
            [
                "[Desktop Entry]",
                "Type=Application",
                f"Name={app_name}",
                f"Exec={target}",
                f"Icon={icon}",
                "Terminal=false",
                "Categories=Utility;",
                "",
            ]
        )
        path.write_text(content, encoding="utf-8")
        path.chmod(0o755)

        progress(100, f"Desktop entry created at {path}")
        log(f"Desktop entry created: {path}")
        return {"action": "create_desktop_entry", "path": str(path)}
