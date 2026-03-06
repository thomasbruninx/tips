"""Compose base installer schema with plugin-specific schema fragments."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from installer_framework.plugins.models import PluginSchemaExtension



def compose_schema(base_schema: dict[str, Any], extensions: list[PluginSchemaExtension]) -> dict[str, Any]:
    """Return a schema copy extended with plugin rules via allOf if/then clauses."""
    schema = deepcopy(base_schema)

    properties = schema.setdefault("properties", {})
    steps_items = (((properties.setdefault("steps", {})).setdefault("items", {})))
    actions_items = (((properties.setdefault("actions", {})).setdefault("items", {})))

    for extension in extensions:
        rule = {
            "if": {
                "properties": {"type": {"const": extension.handle}},
                "required": ["type"],
            },
            "then": extension.schema,
        }
        if extension.kind == "step":
            step_all_of = steps_items.setdefault("allOf", [])
            step_all_of.append(rule)
        elif extension.kind == "action":
            action_all_of = actions_items.setdefault("allOf", [])
            action_all_of.append(rule)

    return schema
