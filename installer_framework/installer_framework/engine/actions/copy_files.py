"""copy_files action implementation."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from installer_framework.engine.action_base import Action
from installer_framework.engine.context import InstallerContext
from installer_framework.util.fs import ensure_dir


class CopyFilesAction(Action):
    def __init__(self, params: dict[str, Any]) -> None:
        self.params = params

    def _resolve_source(self, ctx: InstallerContext, source: str) -> Path:
        candidate = Path(source)
        if candidate.is_absolute() and candidate.exists():
            return candidate

        local = (ctx.config.source_root / source).resolve()
        if local.exists():
            return local

        try:
            from installer_framework.app.resources import resource_path

            bundled = resource_path(source)
            if bundled.exists():
                return bundled
        except Exception:
            pass

        raise FileNotFoundError(f"Copy source not found: {source}")

    def _copy_path(self, src: Path, dst: Path, overwrite: bool, preserve_permissions: bool) -> None:
        if src.is_dir():
            ensure_dir(dst)
            for item in src.iterdir():
                self._copy_path(item, dst / item.name, overwrite, preserve_permissions)
            return

        if dst.exists() and not overwrite:
            return

        ensure_dir(dst.parent)
        if preserve_permissions:
            shutil.copy2(src, dst)
        else:
            shutil.copy(src, dst)

    def execute(self, ctx: InstallerContext, progress, log) -> dict:
        install_dir = Path(ctx.state.install_dir)
        ensure_dir(install_dir)

        items = self.params.get("items") or []
        overwrite = bool(self.params.get("overwrite", True))
        preserve_permissions = bool(self.params.get("preserve_permissions", True))

        if not items:
            raise ValueError("copy_files action requires non-empty items")

        copied = 0
        total = len(items)

        for index, item in enumerate(items, start=1):
            if ctx.is_cancelled():
                log("copy_files cancelled")
                break

            src = self._resolve_source(ctx, item["from"])
            relative_target = item.get("to", ".")
            dst = install_dir / relative_target
            if src.is_file() and relative_target in (".", ""):
                dst = install_dir / src.name
            self._copy_path(src, dst, overwrite, preserve_permissions)
            copied += 1
            pct = int((index / total) * 100)
            progress(pct, f"Copied {src} -> {dst}")
            log(f"Copied '{src}' to '{dst}'")

        return {"action": "copy_files", "copied_items": copied, "install_dir": str(install_dir)}
