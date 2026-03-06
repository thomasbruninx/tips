from __future__ import annotations

import sys
from pathlib import Path

from installer_framework.engine.rollback import InstallTransaction
from tests.helpers.context_factory import default_env, make_context
from tests.helpers.fake_winreg import FakeWinReg


def test_transaction_restores_backup_file(tmp_path):
    ctx = make_context(tmp_path)
    ctx.state.install_dir = str(tmp_path / "install")
    logs = []
    tx = InstallTransaction(ctx, log_callback=logs.append)
    tx.start()

    target = Path(ctx.state.install_dir) / "x.txt"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("old", encoding="utf-8")
    backup = tx.create_file_backup(target)
    target.write_text("new", encoding="utf-8")

    tx.register_records(
        "copy_files",
        "auto",
        [{"kind": "file", "path": str(target), "existed_before": True, "backup_path": str(backup)}],
    )
    tx.rollback()
    assert target.read_text(encoding="utf-8") == "old"


def test_transaction_finalize_success_unix_writes_manifest_and_script(tmp_path):
    ctx = make_context(
        tmp_path,
        config_overrides={
            "uninstall": {
                "enabled": True,
                "modified_file_policy": "prompt",
                "unix": {"create_symlink": True, "user_link_path": str(tmp_path / "bin" / "uninstall")},
            }
        },
    )
    ctx.state.install_dir = str(tmp_path / "install")
    logs = []
    tx = InstallTransaction(ctx, log_callback=logs.append)
    tx.start()

    manifest = tx.finalize_success([])
    assert manifest.exists()
    assert (Path(ctx.state.install_dir) / ".tips" / "uninstall.py").exists()


def test_transaction_finalize_success_windows_registers_arp(monkeypatch, tmp_path):
    fake_reg = FakeWinReg()
    monkeypatch.setitem(sys.modules, "winreg", fake_reg)

    bundled = tmp_path / "tips-uninstaller.exe"
    bundled.write_text("exe", encoding="utf-8")
    monkeypatch.setattr("installer_framework.engine.rollback.resource_path", lambda _rel: bundled)

    ctx = make_context(tmp_path)
    ctx.env = default_env(os_name="windows")
    ctx.state.install_scope = "user"
    ctx.state.install_dir = str(tmp_path / "install")

    tx = InstallTransaction(ctx, log_callback=lambda *_: None)
    tx.start()
    manifest = tx.finalize_success([])

    assert manifest.exists()
    assert (Path(ctx.state.install_dir) / ".tips" / "tips-uninstaller.exe").exists()
