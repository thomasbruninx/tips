from __future__ import annotations

import json

from installer_framework.engine.upgrade import detect_existing_install
from tests.helpers.context_factory import make_context, make_config


def test_detect_existing_install_from_unix_metadata(monkeypatch, tmp_path):
    cfg = make_config(tmp_path)
    ctx = make_context(tmp_path, config_overrides={"upgrade": {"enabled": True, "store_file": "install-info.json"}})

    info_dir = tmp_path / ".config" / cfg.product_id
    info_dir.mkdir(parents=True, exist_ok=True)
    info_file = info_dir / "install-info.json"
    info_file.write_text(json.dumps({"version": "0.9.0", "install_dir": "/tmp/x", "scope": "user"}), encoding="utf-8")

    monkeypatch.setattr("installer_framework.engine.upgrade.user_config_dir", lambda _pid: info_dir)
    monkeypatch.setattr("installer_framework.engine.upgrade.system_config_dir", lambda _pid: tmp_path / "etc")

    detected = detect_existing_install(ctx)
    assert detected is not None
    assert detected["comparison_to_current"] == -1


def test_detect_existing_install_disabled_returns_none(tmp_path):
    ctx = make_context(tmp_path, config_overrides={"upgrade": {"enabled": False}})
    assert detect_existing_install(ctx) is None
