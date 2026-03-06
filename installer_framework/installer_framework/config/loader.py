"""Config loading and schema validation."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import jsonschema

from installer_framework.config.models import InstallerConfig, installer_config_from_dict
from installer_framework.config.validation import validate_config_semantics
from installer_framework.plugins.discovery import discover_and_register_plugins, resolve_plugin_roots
from installer_framework.plugins.registry import build_registry_with_builtins
from installer_framework.plugins.schema_compose import compose_schema

LOGGER = logging.getLogger(__name__)


def _load_schema() -> dict[str, Any]:
    schema_path = Path(__file__).with_name("schema.json")
    return json.loads(schema_path.read_text(encoding="utf-8"))



def load_config(config_path: str | Path, plugins_dir: str | None = None) -> InstallerConfig:
    path = Path(config_path).resolve()
    data = json.loads(path.read_text(encoding="utf-8"))
    base_schema = _load_schema()

    registry = build_registry_with_builtins()
    plugin_roots = resolve_plugin_roots(path.parent, plugins_dir=plugins_dir)
    discovery = discover_and_register_plugins(registry=registry, roots=plugin_roots)
    schema = compose_schema(base_schema, discovery.schema_extensions)
    jsonschema.validate(instance=data, schema=schema)

    cfg = installer_config_from_dict(data, source_root=path.parent)
    cfg.plugin_registry = registry
    cfg.plugin_statuses = [
        {
            "handle": status.handle,
            "type": status.plugin_type,
            "version": status.version,
            "plugin_dir": status.plugin_dir,
            "status": status.status,
            "reason": status.reason,
        }
        for status in discovery.statuses
    ]
    cfg.plugin_roots = discovery.roots
    validate_config_semantics(cfg, registry=registry)

    if discovery.statuses:
        loaded = [s for s in discovery.statuses if s.status == "loaded"]
        skipped = [s for s in discovery.statuses if s.status == "skipped"]
        LOGGER.info("Plugin discovery finished: loaded=%d skipped=%d", len(loaded), len(skipped))
    return cfg
