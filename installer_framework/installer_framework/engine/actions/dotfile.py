"""write_dotfile action implementation for Linux/macOS (and fallback metadata)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from installer_framework.app.paths import system_config_dir, user_config_dir
from installer_framework.engine.action_base import Action
from installer_framework.engine.context import InstallerContext
from installer_framework.util.fs import ensure_dir


class WriteDotfileAction(Action):
    def __init__(self, params: dict[str, Any]) -> None:
        self.params = params

    def execute(self, ctx: InstallerContext, progress, log) -> dict:
        scope = self.params.get("scope") or ctx.state.install_scope
        file_name = self.params.get("file_name", "install-info.json")
        content = self.params.get("content")

        if scope == "system":
            base = Path(self.params.get("system_base", str(system_config_dir(ctx.config.product_id))))
        else:
            base = Path(self.params.get("user_base", str(user_config_dir(ctx.config.product_id))))

        ensure_dir(base)
        target = base / file_name

        if content is None:
            content = {
                "product_id": ctx.config.product_id,
                "product_name": ctx.config.branding.product_name,
                "publisher": ctx.config.branding.publisher,
                "version": ctx.config.branding.version,
                "install_dir": ctx.state.install_dir,
                "scope": ctx.state.install_scope,
                "selected_features": ctx.state.selected_features,
            }

        serialized = json.dumps(content, indent=2)
        serialized = serialized.format(
            install_dir=ctx.state.install_dir,
            scope=ctx.state.install_scope,
            version=ctx.config.branding.version,
        )
        target.write_text(serialized, encoding="utf-8")

        progress(100, f"Wrote configuration to {target}")
        log(f"Dotfile written: {target}")
        return {"action": "write_dotfile", "path": str(target)}
