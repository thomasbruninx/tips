from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from installer_framework.engine.uninstall_runner import UninstallAborted, UninstallOptions, UninstallRunner
from tests.helpers.fake_winreg import FakeWinReg


def _write_manifest(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_handle_modified_policy_matrix(tmp_path):
    manifest = _write_manifest(tmp_path / ".tips" / "manifest.json", {"install_dir": str(tmp_path), "artifacts": [], "uninstall": {}})
    runner = UninstallRunner(manifest, options=UninstallOptions(delete_modified=True, modified_file_policy="prompt"))
    assert runner._handle_modified(tmp_path / "x", "delete", None, lambda *_: None) == "apply"

    runner = UninstallRunner(manifest, options=UninstallOptions(silent=True, modified_file_policy="delete"))
    assert runner._handle_modified(tmp_path / "x", "delete", None, lambda *_: None) == "apply"

    runner = UninstallRunner(manifest, options=UninstallOptions(silent=False, modified_file_policy="prompt"))
    assert runner._handle_modified(tmp_path / "x", "delete", lambda *_: "abort", lambda *_: None) == "abort"
    assert runner._handle_modified(tmp_path / "x", "delete", lambda *_: "delete", lambda *_: None) == "apply"
    assert runner._handle_modified(tmp_path / "x", "delete", lambda *_: "anything", lambda *_: None) == "skip"


def test_handle_modified_non_silent_direct_policies_and_no_prompt(tmp_path):
    manifest = _write_manifest(tmp_path / ".tips" / "manifest.json", {"install_dir": str(tmp_path), "artifacts": [], "uninstall": {}})
    path = tmp_path / "x"
    runner = UninstallRunner(manifest, options=UninstallOptions(silent=False, modified_file_policy="skip"))
    assert runner._handle_modified(path, "delete", None, lambda *_: None) == "skip"

    runner = UninstallRunner(manifest, options=UninstallOptions(silent=False, modified_file_policy="delete"))
    assert runner._handle_modified(path, "delete", None, lambda *_: None) == "apply"

    runner = UninstallRunner(manifest, options=UninstallOptions(silent=False, modified_file_policy="prompt"))
    assert runner._handle_modified(path, "delete", None, lambda *_: None) == "skip"


def test_restore_or_delete_file_directory_and_backup_paths(tmp_path):
    install_dir = tmp_path / "install"
    manifest = _write_manifest(install_dir / ".tips" / "manifest.json", {"install_dir": str(install_dir), "artifacts": [], "uninstall": {}})
    runner = UninstallRunner(manifest, options=UninstallOptions(silent=True, modified_file_policy="skip"))

    removed: list[str] = []
    skipped: list[str] = []
    logs: list[str] = []

    dir_path = install_dir / "folder"
    (dir_path / "x.txt").parent.mkdir(parents=True, exist_ok=True)
    (dir_path / "x.txt").write_text("x", encoding="utf-8")
    runner._restore_or_delete_file(
        {"path": str(dir_path), "kind": "file", "existed_before": False},
        removed,
        skipped,
        None,
        logs.append,
    )
    assert not dir_path.exists()

    preexisting = install_dir / "config.ini"
    backup = install_dir / "backup.ini"
    preexisting.parent.mkdir(parents=True, exist_ok=True)
    preexisting.write_text("new", encoding="utf-8")
    backup.write_text("old", encoding="utf-8")
    runner._restore_or_delete_file(
        {"path": str(preexisting), "kind": "file", "existed_before": True, "backup_path": str(backup)},
        removed,
        skipped,
        None,
        logs.append,
    )
    assert preexisting.read_text(encoding="utf-8") == "old"

    missing_backup_target = install_dir / "restore-me.txt"
    missing_backup_target.write_text("new", encoding="utf-8")
    runner._restore_or_delete_file(
        {
            "path": str(missing_backup_target),
            "kind": "file",
            "existed_before": True,
            "backup_path": str(install_dir / "missing.bak"),
        },
        removed,
        skipped,
        None,
        logs.append,
    )
    assert str(missing_backup_target) in skipped

    no_backup_target = install_dir / "no-backup.txt"
    no_backup_target.write_text("new", encoding="utf-8")
    runner._restore_or_delete_file(
        {"path": str(no_backup_target), "kind": "file", "existed_before": True},
        removed,
        skipped,
        None,
        logs.append,
    )
    assert str(no_backup_target) in skipped


def test_restore_or_delete_file_early_return_and_hash_error(monkeypatch, tmp_path):
    install_dir = tmp_path / "install"
    manifest = _write_manifest(install_dir / ".tips" / "manifest.json", {"install_dir": str(install_dir), "artifacts": [], "uninstall": {}})
    runner = UninstallRunner(manifest, options=UninstallOptions(silent=True, modified_file_policy="skip"))

    removed: list[str] = []
    skipped: list[str] = []
    logs: list[str] = []

    missing = install_dir / "missing.txt"
    runner._restore_or_delete_file(
        {"path": str(missing), "kind": "file", "existed_before": False},
        removed,
        skipped,
        None,
        logs.append,
    )
    assert removed == []
    assert skipped == []

    tracked = install_dir / "tracked.txt"
    tracked.parent.mkdir(parents=True, exist_ok=True)
    tracked.write_text("content", encoding="utf-8")
    monkeypatch.setattr("installer_framework.engine.uninstall_runner.file_sha256", lambda _p: (_ for _ in ()).throw(RuntimeError("hash error")))
    runner._restore_or_delete_file(
        {"path": str(tracked), "kind": "file", "existed_before": False, "hash_after": "abc"},
        removed,
        skipped,
        None,
        logs.append,
    )
    assert str(tracked) in removed


def test_restore_or_delete_file_aborts_on_prompt(tmp_path):
    install_dir = tmp_path / "install"
    target = install_dir / "tracked.txt"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("current", encoding="utf-8")
    manifest = _write_manifest(install_dir / ".tips" / "manifest.json", {"install_dir": str(install_dir), "artifacts": [], "uninstall": {}})

    runner = UninstallRunner(manifest, options=UninstallOptions(silent=False, modified_file_policy="prompt"))
    with pytest.raises(UninstallAborted):
        runner._restore_or_delete_file(
            {"path": str(target), "kind": "file", "existed_before": False, "hash_after": "not-current"},
            [],
            [],
            lambda *_: "abort",
            lambda *_: None,
        )


def test_registry_and_hook_branches(monkeypatch, tmp_path):
    manifest = _write_manifest(tmp_path / ".tips" / "manifest.json", {"install_dir": str(tmp_path), "artifacts": [], "uninstall": {}})
    runner = UninstallRunner(manifest, options=UninstallOptions(silent=True, modified_file_policy="skip"))

    logs: list[str] = []
    runner._restore_or_delete_registry({"key_path": "Software\\X", "value_name": "Y"}, logs.append)
    assert any("winreg unavailable" in line for line in logs)

    fake = FakeWinReg()
    monkeypatch.setitem(sys.modules, "winreg", fake)
    with fake.CreateKeyEx(fake.HKEY_CURRENT_USER, "Software\\X", 0, fake.KEY_WRITE) as key:
        fake.SetValueEx(key, "Value", 0, fake.REG_SZ, "new")
    runner._restore_or_delete_registry(
        {"hive": "HKCU", "key_path": "Software\\X", "value_name": "Value", "existed_before": True, "old_type": "REG_SZ", "old_value": "old"},
        logs.append,
    )
    with fake.OpenKey(fake.HKEY_CURRENT_USER, "Software\\X", 0, fake.KEY_READ) as key:
        value, _ = fake.QueryValueEx(key, "Value")
        assert value == "old"

    runner._run_uninstall_hook({"kind": "script_hook", "undo_path": "missing.py"}, logs.append)
    assert any("Uninstall hook missing" in line for line in logs)

    hook = tmp_path / ".tips" / "bad_hook.py"
    hook.write_text("print('hook')", encoding="utf-8")

    class _Proc:
        returncode = 1
        stdout = ""
        stderr = "failed"

    monkeypatch.setattr("installer_framework.engine.uninstall_runner.subprocess.run", lambda *args, **kwargs: _Proc())
    with pytest.raises(RuntimeError, match="Uninstall hook failed"):
        runner._run_uninstall_hook({"kind": "script_hook", "undo_path": str(hook)}, logs.append)

    runner._run_uninstall_hook({"kind": "script_hook"}, logs.append)


def test_uninstall_runner_run_manifest_and_cleanup_error_paths(monkeypatch, tmp_path):
    runner = UninstallRunner(tmp_path / "missing.json", options=UninstallOptions(silent=True, modified_file_policy="skip"))
    result = runner.run(lambda *_: None, lambda *_: None)
    assert result.success is False
    assert result.errors

    install_dir = tmp_path / "install"
    manifest = _write_manifest(
        install_dir / ".tips" / "manifest.json",
        {
            "install_dir": str(install_dir),
            "artifacts": "not-a-list",
            "uninstall": {
                "unix_script_path": sys.argv[0],
                "windows_uninstaller_path": sys.argv[0],
            },
        },
    )
    runner = UninstallRunner(manifest, options=UninstallOptions(silent=True, modified_file_policy="skip"))
    logs: list[str] = []
    result = runner.run(lambda *_: None, logs.append)
    assert result.success is True
    assert any("currently running launcher" in line for line in logs)
    assert sys.argv[0] in result.skipped

    manifest2 = _write_manifest(
        (tmp_path / "install2/.tips/manifest.json"),
        {"install_dir": str(tmp_path / "install2"), "artifacts": [], "uninstall": {}},
    )
    runner2 = UninstallRunner(manifest2, options=UninstallOptions(silent=True, modified_file_policy="skip"))
    monkeypatch.setattr("installer_framework.engine.uninstall_runner.remove_empty_parents", lambda *_: (_ for _ in ()).throw(RuntimeError("boom")))
    failed = runner2.run(lambda *_: None, lambda *_: None)
    assert failed.success is False
    assert any("boom" in err for err in failed.errors)


def test_registry_delete_and_windows_arp_paths(monkeypatch, tmp_path):
    manifest = _write_manifest(tmp_path / ".tips" / "manifest.json", {"install_dir": str(tmp_path), "artifacts": [], "uninstall": {}})
    runner = UninstallRunner(manifest, options=UninstallOptions(silent=True, modified_file_policy="skip"))
    logs: list[str] = []

    runner._remove_windows_arp({"windows_arp": {"root_hive": "HKCU", "key_path": "Software\\X"}}, logs.append)

    fake = FakeWinReg()
    monkeypatch.setitem(sys.modules, "winreg", fake)
    key_path = "Software\\TIPS\\Uninstall"
    with fake.CreateKeyEx(fake.HKEY_CURRENT_USER, key_path, 0, fake.KEY_WRITE) as key:
        fake.SetValueEx(key, "Value", 0, fake.REG_SZ, "new")
    runner._restore_or_delete_registry(
        {"hive": "HKCU", "key_path": key_path, "value_name": "Value", "existed_before": False},
        logs.append,
    )
    assert any("Deleted registry value" in line for line in logs)

    runner._remove_windows_arp({"windows_arp": {"root_hive": "HKCU"}}, logs.append)
    runner._remove_windows_arp({"windows_arp": {"root_hive": "HKCU", "key_path": key_path}}, logs.append)
    assert any("Removed ARP entry" in line for line in logs)


def test_uninstall_runner_run_record_error_and_launcher_cleanup_branches(monkeypatch, tmp_path):
    install_dir = tmp_path / "install"
    meta_dir = install_dir / ".tips"
    unix_script = meta_dir / "uninstall.py"
    unix_link = meta_dir / "uninstall-link"
    win_uninstaller = meta_dir / "tips-uninstaller.exe"
    bad_win_dir = meta_dir / "bad-win-uninstaller"
    hook = meta_dir / "hook.py"
    backup_dir = meta_dir / "backups"

    meta_dir.mkdir(parents=True, exist_ok=True)
    unix_script.write_text("script", encoding="utf-8")
    unix_link.write_text("link", encoding="utf-8")
    win_uninstaller.write_text("exe", encoding="utf-8")
    bad_win_dir.mkdir(parents=True, exist_ok=True)
    hook.write_text("print('hook')", encoding="utf-8")
    backup_dir.mkdir(parents=True, exist_ok=True)
    (backup_dir / "x.bak").write_text("bak", encoding="utf-8")

    manifest = _write_manifest(
        meta_dir / "manifest.json",
        {
            "install_dir": str(install_dir),
            "artifacts": ["skip-me", {"kind": "script_hook", "undo_path": str(hook)}],
            "uninstall": {
                "unix_script_path": str(unix_script),
                "unix_symlink_path": str(unix_link),
                "windows_uninstaller_path": str(win_uninstaller),
            },
        },
    )

    class _BadProc:
        returncode = 1
        stdout = ""
        stderr = "failed"

    monkeypatch.setattr("installer_framework.engine.uninstall_runner.subprocess.run", lambda *args, **kwargs: _BadProc())
    logs: list[str] = []
    runner = UninstallRunner(manifest, options=UninstallOptions(silent=True, modified_file_policy="skip"))
    result = runner.run(lambda *_: None, logs.append)
    assert result.success is False
    assert any("uninstall error:" in line for line in logs)
    assert str(unix_script) in result.removed
    assert str(unix_link) in result.removed
    assert str(win_uninstaller) in result.removed
    assert not backup_dir.exists()

    manifest2 = _write_manifest(
        (tmp_path / "install2/.tips/manifest.json"),
        {
            "install_dir": str(tmp_path / "install2"),
            "artifacts": [],
            "uninstall": {"windows_uninstaller_path": str(bad_win_dir)},
        },
    )
    runner2 = UninstallRunner(manifest2, options=UninstallOptions(silent=True, modified_file_policy="skip"))
    result2 = runner2.run(lambda *_: None, lambda *_: None)
    assert result2.success is True
    assert str(bad_win_dir) in result2.skipped


def test_uninstall_runner_removes_original_windows_uninstaller_from_temp_process(tmp_path):
    install_dir = tmp_path / "install"
    meta_dir = install_dir / ".tips"
    meta_dir.mkdir(parents=True, exist_ok=True)
    installed_uninstaller = install_dir / "tips-uninstaller.exe"
    installed_uninstaller.write_text("exe", encoding="utf-8")
    temp_uninstaller = tmp_path / "temp" / "tips-uninstaller.exe"
    temp_uninstaller.parent.mkdir(parents=True, exist_ok=True)
    temp_uninstaller.write_text("temp", encoding="utf-8")

    manifest = _write_manifest(
        meta_dir / "manifest.json",
        {
            "install_dir": str(install_dir),
            "artifacts": [],
            "uninstall": {"windows_uninstaller_path": str(installed_uninstaller)},
        },
    )

    runner = UninstallRunner(
        manifest,
        options=UninstallOptions(silent=True, modified_file_policy="skip"),
        running_executable=temp_uninstaller,
        original_uninstaller_path=installed_uninstaller,
    )
    result = runner.run(lambda *_: None, lambda *_: None)

    assert result.success is True
    assert installed_uninstaller.exists() is False
    assert install_dir.exists() is False
