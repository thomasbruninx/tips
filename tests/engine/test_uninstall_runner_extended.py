from __future__ import annotations

import json
import sys
from pathlib import Path

from installer_framework.engine.uninstall_runner import UninstallOptions, UninstallRunner
from tests.helpers.fake_winreg import FakeWinReg


def test_uninstall_runner_handles_registry_and_script_hooks(monkeypatch, tmp_path):
    fake_reg = FakeWinReg()
    monkeypatch.setitem(sys.modules, "winreg", fake_reg)

    install_dir = tmp_path / "install"
    manifest = install_dir / ".tips" / "manifest.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)

    hook = manifest.parent / "hook.py"
    hook.write_text("print('ok')", encoding="utf-8")

    payload = {
        "install_dir": str(install_dir),
        "artifacts": [
            {"kind": "registry_value", "hive": "HKCU", "key_path": "Software\\TIPS", "value_name": "X", "existed_before": False},
            {"kind": "script_hook", "path": str(hook), "undo_path": str(hook)},
        ],
        "uninstall": {"windows_arp": {"root_hive": "HKCU", "key_path": "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\x"}},
    }
    manifest.write_text(json.dumps(payload), encoding="utf-8")

    class _Proc:
        returncode = 0
        stdout = "ok"
        stderr = ""

    monkeypatch.setattr("installer_framework.engine.uninstall_runner.subprocess.run", lambda *args, **kwargs: _Proc())

    runner = UninstallRunner(manifest, options=UninstallOptions(silent=True, modified_file_policy="skip"))
    result = runner.run(lambda *_: None, lambda *_: None)
    assert result.success is True


def test_uninstall_runner_abort_modified_via_prompt(tmp_path):
    install_dir = tmp_path / "install"
    target = install_dir / "a.txt"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("data", encoding="utf-8")

    manifest = install_dir / ".tips" / "manifest.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        json.dumps(
            {
                "install_dir": str(install_dir),
                "artifacts": [{"kind": "file", "path": str(target), "existed_before": False, "hash_after": "different"}],
                "uninstall": {},
            }
        ),
        encoding="utf-8",
    )

    runner = UninstallRunner(manifest, options=UninstallOptions(silent=False, modified_file_policy="prompt"))
    result = runner.run(lambda *_: None, lambda *_: None, prompt_callback=lambda *_: "abort")
    assert result.cancelled is True
