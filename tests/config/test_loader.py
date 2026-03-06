from __future__ import annotations

import json

import pytest

from installer_framework.config.loader import load_config


ACTION_PLUGIN_BODY = """
from installer_framework.engine.action_base import Action

class DemoAction(Action):
    def __init__(self, params):
        self.params = params

    def execute(self, ctx, progress, log):
        progress(100, 'done')
        return {'action': 'demo_action'}


def register():
    return {'action_class': DemoAction}
"""


def _base_payload() -> dict:
    return {
        "install_scope": "ask",
        "branding": {"productName": "Demo", "publisher": "ACME", "version": "1.0.0"},
        "steps": [
            {"id": "welcome", "type": "welcome", "title": "Welcome"},
            {"id": "license", "type": "license", "title": "License", "license_path": "license.txt"},
            {"id": "scope", "type": "scope", "title": "Scope"},
            {
                "id": "directory",
                "type": "directory",
                "title": "Directory",
                "fields": [{"id": "install_dir", "type": "directory", "label": "Install Directory"}],
            },
            {"id": "ready", "type": "ready", "title": "Ready"},
            {"id": "install", "type": "install", "title": "Install"},
            {"id": "finish", "type": "finish", "title": "Finish"},
        ],
        "actions": [{"type": "demo_action", "required_value": "x"}],
    }


def test_load_config_composes_plugin_schema(tmp_path, plugin_root_factory):
    root = plugin_root_factory(
        name="demo",
        plugin_type="action",
        handle="demo_action",
        register_body=ACTION_PLUGIN_BODY,
        schema_fragment={
            "type": "object",
            "properties": {"required_value": {"type": "string"}},
            "required": ["required_value"],
        },
    )

    cfg_file = tmp_path / "config.json"
    cfg_file.write_text(json.dumps(_base_payload()), encoding="utf-8")

    cfg = load_config(cfg_file, plugins_dir=str(root))
    assert cfg.plugin_registry is not None
    assert cfg.plugin_registry.get_action_class("demo_action") is not None
    assert any(item["status"] == "loaded" for item in cfg.plugin_statuses)


def test_load_config_fails_when_plugin_schema_requirement_missing(tmp_path, plugin_root_factory):
    root = plugin_root_factory(
        name="demo",
        plugin_type="action",
        handle="demo_action",
        register_body=ACTION_PLUGIN_BODY,
        schema_fragment={
            "type": "object",
            "properties": {"required_value": {"type": "string"}},
            "required": ["required_value"],
        },
    )
    payload = _base_payload()
    payload["actions"] = [{"type": "demo_action"}]

    cfg_file = tmp_path / "config.json"
    cfg_file.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(Exception):
        load_config(cfg_file, plugins_dir=str(root))


def test_load_config_fails_for_copy_files_without_manifest_file(tmp_path):
    payload = _base_payload()
    payload["actions"] = [{"type": "copy_files"}]
    cfg_file = tmp_path / "config.json"
    cfg_file.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(Exception):
        load_config(cfg_file)
