from __future__ import annotations

import json
from pathlib import Path

import pytest

from installer_framework.plugins.discovery import PluginLoadError, discover_and_register_plugins
from installer_framework.plugins.registry import build_registry_with_builtins


def _write_plugin(root: Path, *, metadata: dict, schema: dict, plugin_code: str, name: str = "p") -> Path:
    p = root / f"{name}.tipsplugin"
    p.mkdir(parents=True, exist_ok=True)
    (p / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
    (p / "schema.json").write_text(json.dumps(schema), encoding="utf-8")
    (p / "plugin.py").write_text(plugin_code, encoding="utf-8")
    return p


def _base_meta(**overrides):
    data = {
        "type": "action",
        "handle": "x_action",
        "version": "1.0.0",
        "min_framework_version": "0.1.0",
        "max_framework_version": "9.9.9",
    }
    data.update(overrides)
    return data


def _base_schema(**overrides):
    data = {"kind": "action", "handle": "x_action", "schema": {"type": "object"}}
    data.update(overrides)
    return data


def _action_code(register_body: str):
    return (
        "from installer_framework.engine.action_base import Action\n"
        "class A(Action):\n"
        "    def __init__(self, params): self.params=params\n"
        "    def execute(self, ctx, progress, log): return {}\n\n"
        f"{register_body}\n"
    )


def test_discovery_metadata_invalid_type(tmp_path):
    root = tmp_path / "plugins"
    root.mkdir()
    _write_plugin(
        root,
        metadata=_base_meta(type="bad"),
        schema=_base_schema(),
        plugin_code=_action_code("def register(): return {'action_class': A}"),
    )
    with pytest.raises(PluginLoadError, match="invalid metadata type"):
        discover_and_register_plugins(build_registry_with_builtins(), [root], framework_version="0.1.0")


def test_discovery_metadata_empty_handle(tmp_path):
    root = tmp_path / "plugins"
    root.mkdir()
    _write_plugin(
        root,
        metadata=_base_meta(handle=" "),
        schema=_base_schema(handle=" "),
        plugin_code=_action_code("def register(): return {'action_class': A}"),
    )
    with pytest.raises(PluginLoadError, match="empty metadata handle"):
        discover_and_register_plugins(build_registry_with_builtins(), [root], framework_version="0.1.0")


def test_discovery_invalid_version_metadata(tmp_path):
    root = tmp_path / "plugins"
    root.mkdir()
    _write_plugin(
        root,
        metadata=_base_meta(min_framework_version="nope"),
        schema=_base_schema(),
        plugin_code=_action_code("def register(): return {'action_class': A}"),
    )
    with pytest.raises(PluginLoadError, match="invalid version"):
        discover_and_register_plugins(build_registry_with_builtins(), [root], framework_version="0.1.0")


def test_discovery_schema_contract_errors(tmp_path):
    root = tmp_path / "plugins"
    root.mkdir()
    _write_plugin(
        root,
        metadata=_base_meta(),
        schema={"kind": "action", "handle": "x_action"},
        plugin_code=_action_code("def register(): return {'action_class': A}"),
        name="missing_schema_key",
    )
    with pytest.raises(PluginLoadError, match=r"missing key\(s\): schema"):
        discover_and_register_plugins(build_registry_with_builtins(), [root], framework_version="0.1.0")

    (root / "missing_schema_key.tipsplugin").rename(root / "zz1.bak")
    _write_plugin(
        root,
        metadata=_base_meta(),
        schema=_base_schema(kind="step"),
        plugin_code=_action_code("def register(): return {'action_class': A}"),
        name="kind_mismatch",
    )
    with pytest.raises(PluginLoadError, match="schema kind 'step' does not match"):
        discover_and_register_plugins(build_registry_with_builtins(), [root], framework_version="0.1.0")


def test_discovery_registration_contract_errors(tmp_path):
    root = tmp_path / "plugins"
    root.mkdir()
    _write_plugin(
        root,
        metadata=_base_meta(),
        schema=_base_schema(),
        plugin_code=_action_code("x = 1"),
        name="no_register",
    )
    with pytest.raises(PluginLoadError, match="must define callable register"):
        discover_and_register_plugins(build_registry_with_builtins(), [root], framework_version="0.1.0")

    (root / "no_register.tipsplugin").rename(root / "zz2.bak")
    _write_plugin(
        root,
        metadata=_base_meta(),
        schema=_base_schema(),
        plugin_code=_action_code("def register(): return 1"),
        name="bad_register",
    )
    with pytest.raises(PluginLoadError, match="must return a dict"):
        discover_and_register_plugins(build_registry_with_builtins(), [root], framework_version="0.1.0")

    (root / "bad_register.tipsplugin").rename(root / "zz3.bak")
    _write_plugin(
        root,
        metadata=_base_meta(),
        schema=_base_schema(),
        plugin_code="def register(): return {'action_class': object}\n",
        name="bad_class",
    )
    with pytest.raises(PluginLoadError, match="subclassing Action"):
        discover_and_register_plugins(build_registry_with_builtins(), [root], framework_version="0.1.0")
