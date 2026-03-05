"""Windows shortcut creation action."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from installer_framework.engine.action_base import Action
from installer_framework.engine.context import InstallerContext
from installer_framework.util.fs import ensure_dir


class CreateShortcutAction(Action):
    def __init__(self, params: dict[str, Any]) -> None:
        self.params = params

    def _start_menu_dir(self, scope: str) -> Path:
        if scope == "system":
            base = Path(os.environ.get("ProgramData", r"C:\\ProgramData"))
            return base / "Microsoft" / "Windows" / "Start Menu" / "Programs"
        base = Path(os.environ.get("APPDATA", str(Path.home())))
        return base / "Microsoft" / "Windows" / "Start Menu" / "Programs"

    def _desktop_dir(self, scope: str) -> Path:
        if scope == "system":
            base = Path(os.environ.get("PUBLIC", r"C:\\Users\\Public"))
            return base / "Desktop"
        return Path.home() / "Desktop"

    def _create_with_pywin32(self, shortcut_path: Path, target: str, icon: str | None) -> None:
        import win32com.client  # type: ignore

        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortcut(str(shortcut_path))
        shortcut.TargetPath = target
        shortcut.WorkingDirectory = str(Path(target).parent)
        if icon:
            shortcut.IconLocation = icon
        shortcut.save()

    def _create_with_winshell(self, shortcut_path: Path, target: str, icon: str | None) -> None:
        import winshell  # type: ignore

        with winshell.shortcut(str(shortcut_path)) as shortcut:
            shortcut.path = target
            shortcut.working_directory = str(Path(target).parent)
            if icon:
                shortcut.icon_location = (icon, 0)

    def execute(self, ctx: InstallerContext, progress, log) -> dict:
        if not ctx.env.is_windows:
            log("create_shortcut skipped on non-Windows platform")
            return {"action": "create_shortcut", "skipped": True}

        app_name = self.params.get("name") or ctx.config.branding.product_name
        target = self.params.get("target")
        if not target:
            target = str(Path(ctx.state.install_dir) / self.params.get("target_relative", f"{app_name}.exe"))
        icon = self.params.get("icon")

        created: list[str] = []
        if self.params.get("start_menu", True):
            folder = ensure_dir(self._start_menu_dir(ctx.state.install_scope))
            path = folder / f"{app_name}.lnk"
            if self._create_shortcut(path, target, icon, log):
                created.append(str(path))

        if self.params.get("desktop", False):
            folder = ensure_dir(self._desktop_dir(ctx.state.install_scope))
            path = folder / f"{app_name}.lnk"
            if self._create_shortcut(path, target, icon, log):
                created.append(str(path))

        progress(100, "Shortcut creation complete")
        return {"action": "create_shortcut", "created": created}

    def _create_shortcut(self, path: Path, target: str, icon: str | None, log) -> bool:
        try:
            self._create_with_pywin32(path, target, icon)
            log(f"Shortcut created via pywin32: {path}")
            return True
        except Exception:
            pass

        try:
            self._create_with_winshell(path, target, icon)
            log(f"Shortcut created via winshell: {path}")
            return True
        except Exception:
            log("Unable to create Windows shortcut: pywin32/winshell unavailable")
            return False
