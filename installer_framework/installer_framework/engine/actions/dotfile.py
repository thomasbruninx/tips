"""write_dotfile action implementation with explicit target path and append mode."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from installer_framework.engine.action_base import Action
from installer_framework.engine.context import InstallerContext
from installer_framework.engine.manifest import file_sha256
from installer_framework.util.fs import ensure_dir


class WriteDotfileAction(Action):
    def __init__(self, params: dict[str, Any]) -> None:
        self.params = params

    def _resolve_target(self, ctx: InstallerContext) -> Path:
        target_path = str(self.params.get("target_path", "")).strip()
        if not target_path:
            raise ValueError("write_dotfile requires non-empty 'target_path'")

        expanded = os.path.expandvars(os.path.expanduser(target_path))
        path = Path(expanded)
        if not path.is_absolute():
            path = ctx.config.source_root / path
        return path.resolve()

    def _default_content(self, ctx: InstallerContext) -> dict[str, Any]:
        return {
            "product_id": ctx.config.product_id,
            "product_name": ctx.config.branding.product_name,
            "publisher": ctx.config.branding.publisher,
            "version": ctx.config.branding.version,
            "install_dir": ctx.state.install_dir,
            "scope": ctx.state.install_scope,
            "selected_features": ctx.state.selected_features,
        }

    def _render_payload(self, ctx: InstallerContext, content: Any) -> str:
        substitutions = {
            "install_dir": ctx.state.install_dir,
            "scope": ctx.state.install_scope,
            "version": ctx.config.branding.version,
            "product_id": ctx.config.product_id,
            "product_name": ctx.config.branding.product_name,
            "publisher": ctx.config.branding.publisher,
        }

        def _render_value(value: Any) -> Any:
            if isinstance(value, str):
                return value.format(**substitutions)
            if isinstance(value, list):
                return [_render_value(item) for item in value]
            if isinstance(value, dict):
                return {key: _render_value(item) for key, item in value.items()}
            return value

        rendered = _render_value(content)
        if isinstance(rendered, str):
            return rendered
        return json.dumps(rendered, indent=2)

    def execute(self, ctx: InstallerContext, progress, log) -> dict:
        target = self._resolve_target(ctx)
        append = self.params.get("append", False)
        if not isinstance(append, bool):
            raise ValueError("write_dotfile 'append' must be boolean")
        content = self.params.get("content")
        if content is None:
            content = self._default_content(ctx)

        if not target.parent.exists():
            ensure_dir(target.parent)

        existed_before = target.exists()
        backup_path: str | None = None
        rollback_policy = getattr(ctx, "action_rollback_policy", "auto")
        if existed_before and rollback_policy == "auto" and target.is_file():
            tx = getattr(ctx, "transaction", None)
            if tx is not None:
                try:
                    backup_path = str(tx.create_file_backup(target))
                except Exception:
                    backup_path = None

        payload = self._render_payload(ctx, content)
        if append:
            if not payload.endswith("\n"):
                payload = f"{payload}\n"
            with target.open("a", encoding="utf-8") as fh:
                fh.write(payload)
            progress(100, f"Appended configuration to {target}")
            log(f"Dotfile appended: {target}")
            mode = "append"
        else:
            target.write_text(payload, encoding="utf-8")
            progress(100, f"Wrote configuration to {target}")
            log(f"Dotfile written: {target}")
            mode = "write"

        hash_after = file_sha256(target) if target.exists() and target.is_file() else None
        return {
            "action": "write_dotfile",
            "path": str(target),
            "mode": mode,
            "rollback_records": [
                {
                    "kind": "file",
                    "path": str(target),
                    "existed_before": existed_before,
                    "backup_path": backup_path,
                    "hash_after": hash_after,
                }
            ],
        }
