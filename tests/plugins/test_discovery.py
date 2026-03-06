from __future__ import annotations

import json
from pathlib import Path

import pytest

from installer_framework.plugins.discovery import (
    PluginLoadError,
    discover_and_register_plugins,
    resolve_plugin_roots,
)
from installer_framework.plugins.registry import build_registry_with_builtins


STEP_PLUGIN_BODY = """
from installer_framework.ui.step_base import StepWidget

class DemoStep(StepWidget):
    pass


def register():
    return {'step_class': DemoStep}
"""


def _create_step_plugin(root: Path, *, handle: str = "demo_step", min_v: str = "0.1.0", max_v: str = "9.9.9") -> Path:
    plugin = root / "demo.tipsplugin"
    plugin.mkdir(parents=True, exist_ok=True)
    (plugin / "metadata.json").write_text(
        json.dumps(
            {
                "type": "step",
                "handle": handle,
                "version": "1.0.0",
                "min_framework_version": min_v,
                "max_framework_version": max_v,
            }
        ),
        encoding="utf-8",
    )
    (plugin / "schema.json").write_text(
        json.dumps({"kind": "step", "handle": handle, "schema": {"type": "object"}}),
        encoding="utf-8",
    )
    (plugin / "plugin.py").write_text(STEP_PLUGIN_BODY, encoding="utf-8")
    return plugin


def test_discovery_loads_compatible_plugin(tmp_path):
    root = tmp_path / "plugins"
    root.mkdir()
    _create_step_plugin(root)

    registry = build_registry_with_builtins()
    result = discover_and_register_plugins(registry=registry, roots=[root], framework_version="0.1.0")
    assert registry.get_step_class("demo_step") is not None
    assert any(status.status == "loaded" for status in result.statuses)


def test_discovery_skips_incompatible_version(tmp_path):
    root = tmp_path / "plugins"
    root.mkdir()
    _create_step_plugin(root, min_v="2.0.0", max_v="2.1.0")

    registry = build_registry_with_builtins()
    result = discover_and_register_plugins(registry=registry, roots=[root], framework_version="0.1.0")
    assert registry.get_step_class("demo_step") is None
    assert any(status.status == "skipped" for status in result.statuses)


def test_discovery_missing_required_file_raises(tmp_path):
    root = tmp_path / "plugins"
    plugin = root / "broken.tipsplugin"
    plugin.mkdir(parents=True)
    (plugin / "metadata.json").write_text("{}", encoding="utf-8")

    registry = build_registry_with_builtins()
    with pytest.raises(PluginLoadError):
        discover_and_register_plugins(registry=registry, roots=[root], framework_version="0.1.0")


def test_resolve_plugin_roots_includes_cli_and_env(monkeypatch, tmp_path):
    source_root = tmp_path / "src"
    source_root.mkdir(parents=True)
    cli_root = tmp_path / "cli_plugins"
    cli_root.mkdir()
    env_root = tmp_path / "env_plugins"
    env_root.mkdir()

    monkeypatch.setenv("TIPS_PLUGINS_DIR", str(env_root))
    roots = resolve_plugin_roots(source_root=source_root, plugins_dir=str(cli_root))
    assert cli_root in roots
    assert env_root in roots


def test_resolve_plugin_roots_skips_repo_root_when_frozen(monkeypatch, tmp_path):
    source_root = tmp_path / "src"
    source_root.mkdir(parents=True)
    repo_plugins = tmp_path / "repo_plugins"
    repo_plugins.mkdir()
    bundled_plugins = tmp_path / "bundled_plugins"
    bundled_plugins.mkdir()

    monkeypatch.setattr("installer_framework.plugins.discovery._find_repo_root", lambda _src: tmp_path)
    monkeypatch.setattr("installer_framework.plugins.discovery.resource_path", lambda _p: bundled_plugins)
    monkeypatch.setattr("installer_framework.plugins.discovery.sys.frozen", True, raising=False)
    monkeypatch.setattr("installer_framework.plugins.discovery.sys._MEIPASS", str(tmp_path / "bundle"), raising=False)

    roots = resolve_plugin_roots(source_root=source_root, plugins_dir=None)
    assert (tmp_path / "plugins") not in roots
    assert bundled_plugins in roots
