from __future__ import annotations

import sys
from pathlib import Path

import pytest

from installer_framework.engine.rollback import InstallTransaction, remove_empty_parents
from tests.helpers.context_factory import default_env, make_context
from tests.helpers.fake_winreg import FakeWinReg


def test_create_file_backup_missing_file_raises(tmp_path):
    ctx = make_context(tmp_path)
    tx = InstallTransaction(ctx, log_callback=lambda *_: None)
    with pytest.raises(FileNotFoundError):
        tx.create_file_backup(tmp_path / "missing.txt")


def test_register_records_ignores_none(tmp_path):
    ctx = make_context(tmp_path)
    tx = InstallTransaction(ctx, log_callback=lambda *_: None)
    tx.start()
    tx.register_records("copy_files", "auto", None)
    assert tx.records == []


def test_rollback_skips_restore_when_backup_missing(tmp_path):
    ctx = make_context(tmp_path)
    ctx.state.install_dir = str(tmp_path / "install")
    logs: list[str] = []
    tx = InstallTransaction(ctx, log_callback=logs.append)
    tx.start()

    target = Path(ctx.state.install_dir) / "data.txt"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("new", encoding="utf-8")

    tx.register_records(
        "copy_files",
        "auto",
        [{"kind": "file", "path": str(target), "existed_before": True}],
    )
    tx.rollback()

    assert target.exists()
    assert any("no backup available" in entry for entry in logs)


def test_rollback_removes_directory_record(tmp_path):
    ctx = make_context(tmp_path)
    ctx.state.install_dir = str(tmp_path / "install")
    tx = InstallTransaction(ctx, log_callback=lambda *_: None)
    tx.start()

    created_dir = Path(ctx.state.install_dir) / "x"
    (created_dir / "child.txt").parent.mkdir(parents=True, exist_ok=True)
    (created_dir / "child.txt").write_text("x", encoding="utf-8")
    tx.register_records("copy_files", "auto", [{"kind": "file", "path": str(created_dir), "existed_before": False}])
    tx.rollback()
    assert not created_dir.exists()


def test_rollback_registry_restore_and_delete(monkeypatch, tmp_path):
    fake = FakeWinReg()
    monkeypatch.setitem(sys.modules, "winreg", fake)

    ctx = make_context(tmp_path)
    ctx.env = default_env(os_name="windows")
    tx = InstallTransaction(ctx, log_callback=lambda *_: None)

    key_path = "Software\\TIPS\\App"
    with fake.CreateKeyEx(fake.HKEY_CURRENT_USER, key_path, 0, fake.KEY_WRITE) as key:
        fake.SetValueEx(key, "Version", 0, fake.REG_SZ, "current")

    tx._rollback_registry_value(
        {
            "hive": "HKCU",
            "key_path": key_path,
            "value_name": "Version",
            "existed_before": True,
            "old_value": "previous",
            "old_type": "REG_SZ",
        }
    )

    with fake.OpenKey(fake.HKEY_CURRENT_USER, key_path, 0, fake.KEY_READ) as key:
        value, _ = fake.QueryValueEx(key, "Version")
        assert value == "previous"

    with fake.CreateKeyEx(fake.HKEY_CURRENT_USER, key_path, 0, fake.KEY_WRITE) as key:
        fake.SetValueEx(key, "Transient", 0, fake.REG_SZ, "x")
    tx._rollback_registry_value(
        {"hive": "HKCU", "key_path": key_path, "value_name": "Transient", "existed_before": False}
    )
    with pytest.raises(OSError):
        with fake.OpenKey(fake.HKEY_CURRENT_USER, key_path, 0, fake.KEY_READ) as key:
            fake.QueryValueEx(key, "Transient")


def test_rollback_registry_importerror_path(tmp_path):
    logs: list[str] = []
    ctx = make_context(tmp_path)
    ctx.env = default_env(os_name="windows")
    tx = InstallTransaction(ctx, log_callback=logs.append)
    tx._rollback_registry_value({"hive": "HKCU", "key_path": "Software\\TIPS", "value_name": "X"})
    assert any("winreg unavailable" in line for line in logs)


def test_run_script_hook_missing_and_failure(monkeypatch, tmp_path):
    logs: list[str] = []
    ctx = make_context(tmp_path)
    tx = InstallTransaction(ctx, log_callback=logs.append)

    tx._run_script_hook("not-there.py", "undo")
    assert any("script hook missing" in line for line in logs)

    script = tmp_path / "hook.py"
    script.write_text("print('ok')", encoding="utf-8")

    class _Proc:
        returncode = 1
        stdout = "some output"
        stderr = "bad"

    monkeypatch.setattr("installer_framework.engine.rollback.subprocess.run", lambda *args, **kwargs: _Proc())
    with pytest.raises(RuntimeError, match="Script undo hook failed"):
        tx._run_script_hook(str(script), "undo")
    assert any("some output" in line for line in logs)


def test_register_windows_arp_non_windows_and_windows_without_winreg(tmp_path):
    logs: list[str] = []
    ctx = make_context(tmp_path)
    tx = InstallTransaction(ctx, log_callback=logs.append)

    assert tx._register_windows_arp(tmp_path / "manifest.json", tmp_path / "u.exe") is None

    ctx.env = default_env(os_name="windows")
    assert tx._register_windows_arp(tmp_path / "manifest.json", tmp_path / "u.exe") is None
    assert any("winreg unavailable" in line for line in logs)


def test_write_unix_uninstall_script_system_symlink_replaces_existing_file(tmp_path):
    link_path = tmp_path / "usr-local-bin" / "tips-test-uninstall"
    ctx = make_context(
        tmp_path,
        config_overrides={
            "uninstall": {
                "enabled": True,
                "modified_file_policy": "prompt",
                "unix": {
                    "create_symlink": True,
                    "system_link_path": str(link_path),
                    "user_link_path": str(tmp_path / "unused"),
                },
            }
        },
    )
    ctx.state.install_scope = "system"
    ctx.state.install_dir = str(tmp_path / "install")

    link_path.parent.mkdir(parents=True, exist_ok=True)
    link_path.write_text("old-launcher", encoding="utf-8")

    tx = InstallTransaction(ctx, log_callback=lambda *_: None)
    script_path, created_link = tx._write_unix_uninstall_script(tmp_path / "install/.tips/manifest.json")

    assert script_path.exists()
    assert created_link == link_path
    assert link_path.is_symlink()
    assert link_path.resolve() == script_path.resolve()


def test_finalize_success_windows_without_bundled_uninstaller_logs(monkeypatch, tmp_path):
    ctx = make_context(tmp_path)
    ctx.env = default_env(os_name="windows")
    ctx.state.install_dir = str(tmp_path / "install")
    logs: list[str] = []

    missing = tmp_path / "missing-uninstaller.exe"
    monkeypatch.setattr("installer_framework.engine.rollback.resource_path", lambda _rel: missing)

    tx = InstallTransaction(ctx, log_callback=logs.append)
    tx.start()
    manifest = tx.finalize_success([])

    assert manifest.exists()
    assert any("bundled uninstaller executable was not found" in line for line in logs)


def test_load_records_from_journal_non_list_returns_empty(tmp_path):
    ctx = make_context(tmp_path)
    ctx.state.install_dir = str(tmp_path / "install")
    tx = InstallTransaction(ctx, log_callback=lambda *_: None)
    tx.start()
    (Path(ctx.state.install_dir) / ".tips" / "rollback_journal.json").write_text(
        '{"records":"not-a-list"}',
        encoding="utf-8",
    )
    assert tx.load_records_from_journal() == []


def test_remove_empty_parents_handles_missing_start(tmp_path):
    missing_leaf = tmp_path / "does-not-exist" / "child"
    remove_empty_parents(missing_leaf, tmp_path)
    assert not (tmp_path / "does-not-exist").exists()
