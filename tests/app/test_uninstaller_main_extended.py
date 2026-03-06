from __future__ import annotations

from argparse import Namespace
import runpy
import sys

import pytest

from installer_framework import uninstaller_main
from installer_framework.engine.uninstall_runner import UninstallResult


def test_parse_args_roundtrip(monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        [
            "prog",
            "--manifest",
            "/tmp/m.json",
            "--silent",
            "--delete-modified",
            "--modified-file-policy",
            "delete",
        ],
    )
    args = uninstaller_main.parse_args()
    assert args.manifest == "/tmp/m.json"
    assert args.silent is True
    assert args.delete_modified is True
    assert args.modified_file_policy == "delete"


def test_resolve_manifest_from_install_dir(tmp_path):
    args = Namespace(manifest=None, install_dir=str(tmp_path / "app"))
    assert uninstaller_main.resolve_manifest(args) == (tmp_path / "app/.tips/manifest.json").resolve()


def test_main_parse_error_and_silent_non_success(monkeypatch):
    monkeypatch.setattr(
        uninstaller_main,
        "parse_args",
        lambda: Namespace(
            manifest=None,
            install_dir=None,
            silent=True,
            delete_modified=False,
            modified_file_policy="skip",
        ),
    )
    assert uninstaller_main.main() == 1

    manifest_args = Namespace(
        manifest="/tmp/manifest.json",
        install_dir=None,
        silent=True,
        delete_modified=False,
        modified_file_policy="skip",
    )
    monkeypatch.setattr(uninstaller_main, "parse_args", lambda: manifest_args)
    monkeypatch.setattr(uninstaller_main, "resolve_manifest", lambda _args: "/tmp/manifest.json")
    monkeypatch.setattr(
        uninstaller_main,
        "run_uninstall",
        lambda *args, **kwargs: UninstallResult(success=False, cancelled=True),
    )
    assert uninstaller_main.main() == 2

    monkeypatch.setattr(
        uninstaller_main,
        "run_uninstall",
        lambda *args, **kwargs: UninstallResult(success=False, cancelled=False, errors=["x"]),
    )
    assert uninstaller_main.main() == 1


def test_main_gui_branch(monkeypatch):
    monkeypatch.setattr(
        uninstaller_main,
        "parse_args",
        lambda: Namespace(
            manifest="/tmp/manifest.json",
            install_dir=None,
            silent=False,
            delete_modified=True,
            modified_file_policy="delete",
        ),
    )
    monkeypatch.setattr(uninstaller_main, "resolve_manifest", lambda _args: "/tmp/manifest.json")

    class _App:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def run(self):
            return 42

    monkeypatch.setattr("installer_framework.app.qt_uninstaller_app.UninstallerQtApp", _App)
    assert uninstaller_main.main() == 42


def test_module_main_guard_executes(monkeypatch, tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text("{}", encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["prog", "--manifest", str(manifest), "--silent"])
    monkeypatch.setattr(
        "installer_framework.uninstall_cli.run_uninstall",
        lambda *args, **kwargs: UninstallResult(success=True, cancelled=False),
    )
    sys.modules.pop("installer_framework.uninstaller_main", None)

    with pytest.raises(SystemExit) as exc:
        runpy.run_module("installer_framework.uninstaller_main", run_name="__main__")
    assert exc.value.code == 0
