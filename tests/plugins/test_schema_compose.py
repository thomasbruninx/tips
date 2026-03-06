from __future__ import annotations

from installer_framework.plugins.models import PluginSchemaExtension
from installer_framework.plugins.schema_compose import compose_schema


def test_compose_schema_appends_step_and_action_rules():
    base = {
        "type": "object",
        "properties": {
            "steps": {"items": {"type": "object"}},
            "actions": {"items": {"type": "object"}},
        },
    }
    extensions = [
        PluginSchemaExtension(kind="step", handle="x_step", schema={"required": ["foo"]}),
        PluginSchemaExtension(kind="action", handle="x_action", schema={"required": ["bar"]}),
    ]

    composed = compose_schema(base, extensions)
    step_rules = composed["properties"]["steps"]["items"]["allOf"]
    action_rules = composed["properties"]["actions"]["items"]["allOf"]

    assert step_rules[0]["if"]["properties"]["type"]["const"] == "x_step"
    assert step_rules[0]["then"] == {"required": ["foo"]}
    assert action_rules[0]["if"]["properties"]["type"]["const"] == "x_action"
