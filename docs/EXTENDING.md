# Extending the Framework
You can write your own steps and actions without needing to touch the main framework codebase.
Two example plugins are available in this repo.

## General plugin file structure
A plugin is generally just a folder with a name ending in `.tipsplugin` which always contains at least three files:
```
<plugin-name>.tipsplugin/
    metadata.json
    schema.json
    plugin.py
```

The `metadata.json` file contains information about the type of plugin `step`/`action`, versioning and usag info and a unique handle. For example:
```json
{
  "type": "action",
  "handle": "post_install_note",
  "version": "1.0.0",
  "min_framework_version": "0.1.0",
  "max_framework_version": "0.1.99",
  "name": "Post Install Note",
  "description": "Writes a formatted post-install note file"
}
```

The `schema.json` file contains information on new properties and their validation rules to be used in the framework configuration when using the plugin. For example:
```json
{
  "kind": "action",
  "handle": "post_install_note",
  "schema": {
    "type": "object",
    "properties": {
      "note_file": {"type": "string", "minLength": 1},
      "lines": {
        "oneOf": [
          {"type": "string", "minLength": 1},
          {
            "type": "array",
            "items": {"type": "string", "minLength": 1},
            "minItems": 1
          }
        ]
      }
    },
    "required": ["note_file", "lines"]
  }
}
```

The `plugin.py` file contains the entrypoint to your actual plugin logic. For example:
```python
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
```

## Adding a New Step Plugin

1. Create `<repo-root>/plugins/<name>.tipsplugin/`.
2. Add `metadata.json` with `type: \"step\"` and unique `handle`.
3. Add `plugin.py` with a `StepWidget` subclass and `register() -> {\"step_class\": ...}`.
4. Add `schema.json` with `kind: \"step\"` and a schema fragment for step config validation.

## Adding a New Action Plugin

1. Create `<repo-root>/plugins/<name>.tipsplugin/`.
2. Add `metadata.json` with `type: \"action\"` and unique `handle`.
3. Add `plugin.py` with an `Action` subclass and `register() -> {\"action_class\": ...}`.
4. Add `schema.json` with `kind: \"action\"` and a schema fragment for action params validation.
