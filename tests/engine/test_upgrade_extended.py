from __future__ import annotations

import json
import sys

from installer_framework.engine.upgrade import detect_existing_install
from tests.helpers.context_factory import default_env, make_context
from tests.helpers.fake_winreg import FakeWinReg


def test_detect_existing_install_windows_registry_success(monkeypatch, tmp_path):
    fake = FakeWinReg()
    monkeypatch.setitem(sys.modules, "winreg", fake)

    ctx = make_context(tmp_path)
    ctx.env = default_env(os_name="windows")
    ctx.state.install_scope = "user"
    key_path = f"Software\\{ctx.config.branding.publisher}\\{ctx.config.product_id}"

    with fake.CreateKeyEx(fake.HKEY_CURRENT_USER, key_path, 0, fake.KEY_WRITE) as key:
        fake.SetValueEx(key, "Version", 0, fake.REG_SZ, "0.9.0")
        fake.SetValueEx(key, "InstallDir", 0, fake.REG_SZ, "C:\\App")
        fake.SetValueEx(key, "Scope", 0, fake.REG_SZ, "user")

    detected = detect_existing_install(ctx)
    assert detected is not None
    assert detected["source"] == "registry"
    assert detected["comparison_to_current"] == -1


def test_detect_existing_install_windows_registry_missing_returns_none(tmp_path):
    ctx = make_context(tmp_path)
    ctx.env = default_env(os_name="windows")
    ctx.state.install_scope = "system"
    assert detect_existing_install(ctx) is None


def test_detect_existing_install_windows_registry_key_missing(monkeypatch, tmp_path):
    fake = FakeWinReg()
    monkeypatch.setitem(sys.modules, "winreg", fake)
    ctx = make_context(tmp_path)
    ctx.env = default_env(os_name="windows")
    ctx.state.install_scope = "system"
    assert detect_existing_install(ctx) is None


def test_detect_existing_install_unix_skips_invalid_json_and_falls_back(monkeypatch, tmp_path):
    ctx = make_context(tmp_path, config_overrides={"upgrade": {"enabled": True, "store_file": "upgrade.json"}})
    ctx.state.install_scope = "user"

    user_dir = tmp_path / "user-meta"
    system_dir = tmp_path / "system-meta"
    user_dir.mkdir(parents=True, exist_ok=True)
    system_dir.mkdir(parents=True, exist_ok=True)

    (user_dir / "upgrade.json").write_text("{bad-json", encoding="utf-8")
    (system_dir / "upgrade.json").write_text(
        json.dumps({"version": "2.0.0", "install_dir": "/opt/test", "scope": "system"}),
        encoding="utf-8",
    )

    monkeypatch.setattr("installer_framework.engine.upgrade.user_config_dir", lambda _pid: user_dir)
    monkeypatch.setattr("installer_framework.engine.upgrade.system_config_dir", lambda _pid: system_dir)

    detected = detect_existing_install(ctx)
    assert detected is not None
    assert detected["scope"] == "system"
    assert str(system_dir / "upgrade.json") == detected["source"]
    assert detected["comparison_to_current"] == 1
