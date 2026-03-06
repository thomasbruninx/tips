from __future__ import annotations

from installer_framework import uninstaller_main
from installer_framework.engine.uninstall_runner import UninstallResult


def test_uninstaller_main_resolve_manifest(tmp_path):
    ns = type("Args", (), {"manifest": str(tmp_path / "m.json"), "install_dir": None})
    assert uninstaller_main.resolve_manifest(ns) == (tmp_path / "m.json").resolve()


def test_uninstaller_main_silent_success(monkeypatch, tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text("{}", encoding="utf-8")

    monkeypatch.setattr(
        uninstaller_main,
        "parse_args",
        lambda: type(
            "Args",
            (),
            {
                "manifest": str(manifest),
                "install_dir": None,
                "silent": True,
                "delete_modified": False,
                "modified_file_policy": "skip",
            },
        )(),
    )
    monkeypatch.setattr(
        uninstaller_main,
        "run_uninstall",
        lambda *args, **kwargs: UninstallResult(success=True, cancelled=False),
    )

    assert uninstaller_main.main() == 0
