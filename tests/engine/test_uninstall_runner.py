from __future__ import annotations

import json

from installer_framework.engine.uninstall_runner import UninstallOptions, UninstallRunner


def test_uninstall_runner_removes_file_record(tmp_path):
    install_dir = tmp_path / "install"
    tracked = install_dir / "file.txt"
    tracked.parent.mkdir(parents=True, exist_ok=True)
    tracked.write_text("hello", encoding="utf-8")

    manifest = install_dir / ".tips" / "manifest.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        json.dumps(
            {
                "install_dir": str(install_dir),
                "artifacts": [{"kind": "file", "path": str(tracked), "existed_before": False}],
                "uninstall": {},
            }
        ),
        encoding="utf-8",
    )

    runner = UninstallRunner(manifest, options=UninstallOptions(silent=True, modified_file_policy="skip"))
    result = runner.run(lambda *_: None, lambda *_: None)
    assert result.success is True
    assert tracked.exists() is False


def test_uninstall_runner_skips_modified_file_when_policy_skip(tmp_path):
    install_dir = tmp_path / "install"
    tracked = install_dir / "file.txt"
    tracked.parent.mkdir(parents=True, exist_ok=True)
    tracked.write_text("hello", encoding="utf-8")

    manifest = install_dir / ".tips" / "manifest.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        json.dumps(
            {
                "install_dir": str(install_dir),
                "artifacts": [
                    {
                        "kind": "file",
                        "path": str(tracked),
                        "existed_before": False,
                        "hash_after": "different",
                    }
                ],
                "uninstall": {},
            }
        ),
        encoding="utf-8",
    )

    runner = UninstallRunner(manifest, options=UninstallOptions(silent=True, modified_file_policy="skip"))
    result = runner.run(lambda *_: None, lambda *_: None)
    assert result.success is True
    assert str(tracked) in result.skipped
