from __future__ import annotations

import json
from pathlib import Path


def create_plugin(
    root: Path,
    *,
    name: str,
    plugin_type: str,
    handle: str,
    register_body: str,
    schema_fragment: dict,
    min_version: str = "0.1.0",
    max_version: str = "9.9.9",
) -> Path:
    plugin_dir = root / f"{name}.tipsplugin"
    plugin_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "type": plugin_type,
        "handle": handle,
        "version": "1.0.0",
        "min_framework_version": min_version,
        "max_framework_version": max_version,
    }
    (plugin_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

    schema = {
        "kind": plugin_type,
        "handle": handle,
        "schema": schema_fragment,
    }
    (plugin_dir / "schema.json").write_text(json.dumps(schema), encoding="utf-8")

    (plugin_dir / "plugin.py").write_text(register_body, encoding="utf-8")
    return plugin_dir
