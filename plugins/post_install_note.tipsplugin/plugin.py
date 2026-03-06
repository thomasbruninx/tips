"""Custom action plugin that writes a post-install note file."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from installer_framework.engine.action_base import Action
from installer_framework.engine.context import InstallerContext
from installer_framework.engine.manifest import file_sha256
from installer_framework.util.fs import ensure_dir


class PostInstallNoteAction(Action):
    def __init__(self, params: dict[str, Any]) -> None:
        self.params = params

    def _resolve_target(self, ctx: InstallerContext) -> Path:
        value = str(self.params["note_file"]).strip()
        expanded = os.path.expandvars(os.path.expanduser(value))
        path = Path(expanded)
        if not path.is_absolute():
            path = Path(ctx.state.install_dir) / path
        return path.resolve()

    def _render_lines(self, ctx: InstallerContext) -> str:
        raw = self.params.get("lines", "")
        if isinstance(raw, str):
            lines = [raw]
        elif isinstance(raw, list):
            lines = [str(item) for item in raw]
        else:
            raise ValueError("post_install_note 'lines' must be a string or list of strings")

        substitutions = {
            "install_dir": ctx.state.install_dir,
            "scope": ctx.state.install_scope,
            "version": ctx.config.branding.version,
            "product_id": ctx.config.product_id,
            "product_name": ctx.config.branding.product_name,
            "publisher": ctx.config.branding.publisher,
        }
        rendered = [line.format(**substitutions) for line in lines]
        return "\n".join(rendered).rstrip("\n") + "\n"

    def execute(self, ctx: InstallerContext, progress, log) -> dict:
        target = self._resolve_target(ctx)
        rollback_policy = getattr(ctx, "action_rollback_policy", "auto")

        existed_before = target.exists()
        backup_path: str | None = None
        if existed_before and rollback_policy == "auto" and target.is_file():
            tx = getattr(ctx, "transaction", None)
            if tx is not None:
                try:
                    backup_path = str(tx.create_file_backup(target))
                except Exception:
                    backup_path = None

        ensure_dir(target.parent)
        payload = self._render_lines(ctx)
        target.write_text(payload, encoding="utf-8")
        progress(100, f"Wrote post-install note to {target}")
        log(f"post_install_note wrote: {target}")

        return {
            "action": "post_install_note",
            "path": str(target),
            "rollback_records": [
                {
                    "kind": "file",
                    "path": str(target),
                    "existed_before": existed_before,
                    "backup_path": backup_path,
                    "hash_after": file_sha256(target) if target.exists() and target.is_file() else None,
                }
            ],
        }


def register() -> dict:
    return {"action_class": PostInstallNoteAction}
