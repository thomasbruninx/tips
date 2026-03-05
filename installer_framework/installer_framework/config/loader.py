"""Config loading and schema validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema

from installer_framework.config.models import InstallerConfig, installer_config_from_dict
from installer_framework.config.validation import validate_config_semantics



def _load_schema() -> dict[str, Any]:
    schema_path = Path(__file__).with_name("schema.json")
    return json.loads(schema_path.read_text(encoding="utf-8"))



def load_config(config_path: str | Path) -> InstallerConfig:
    path = Path(config_path).resolve()
    data = json.loads(path.read_text(encoding="utf-8"))
    schema = _load_schema()
    jsonschema.validate(instance=data, schema=schema)

    cfg = installer_config_from_dict(data, source_root=path.parent)
    validate_config_semantics(cfg)
    return cfg
