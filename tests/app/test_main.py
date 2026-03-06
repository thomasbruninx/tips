from __future__ import annotations

from pathlib import Path

import pytest

from installer_framework import main


def test_parse_args_supports_plugins_dir(monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        ["prog", "--config", "config.json", "--plugins-dir", "plugins", "--resume"],
    )
    args = main.parse_args()
    assert args.config == "config.json"
    assert args.plugins_dir == "plugins"
    assert args.resume is True


def test_parse_args_requires_config(monkeypatch):
    monkeypatch.setattr("sys.argv", ["prog"])
    args = main.parse_args()
    assert args.config is None


def test_resolve_config_path_prefers_existing_cwd_file(tmp_path, monkeypatch):
    cfg = tmp_path / "config.json"
    cfg.write_text("{}", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    resolved = main.resolve_config_path("config.json")
    assert resolved == cfg.resolve()


def test_resolve_config_path_falls_back_to_resource(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    bundled = tmp_path / "bundled.json"
    bundled.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(main, "resource_path", lambda _arg: bundled)
    resolved = main.resolve_config_path("missing.json")
    assert resolved == bundled


def test_resolve_runtime_config_arg_source_requires_config(monkeypatch):
    monkeypatch.setattr(main, "is_frozen_runtime", lambda: False)
    with pytest.raises(SystemExit):
        main.resolve_runtime_config_arg(None)


def test_resolve_runtime_config_arg_frozen_uses_packaged(monkeypatch, tmp_path):
    marker = tmp_path / "packaged_installer_config.json"
    marker.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(main, "is_frozen_runtime", lambda: True)
    monkeypatch.setattr(main, "resource_path", lambda _arg: marker)
    assert main.resolve_runtime_config_arg(None) == main.PACKAGED_CONFIG_PATH
