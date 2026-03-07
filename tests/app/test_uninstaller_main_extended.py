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
    assert args.windows_temp_handoff is False
    assert args.original_uninstaller_path is None
    assert args.temp_cleanup_dir is None


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
            windows_temp_handoff=False,
            original_uninstaller_path=None,
            temp_cleanup_dir=None,
        ),
    )
    assert uninstaller_main.main() == 1

    manifest_args = Namespace(
        manifest="/tmp/manifest.json",
        install_dir=None,
        silent=True,
        delete_modified=False,
        modified_file_policy="skip",
        windows_temp_handoff=False,
        original_uninstaller_path=None,
        temp_cleanup_dir=None,
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
            windows_temp_handoff=False,
            original_uninstaller_path=None,
            temp_cleanup_dir=None,
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


def test_build_temp_uninstaller_command_preserves_args(tmp_path):
    args = Namespace(
        manifest=None,
        install_dir=None,
        silent=True,
        delete_modified=True,
        modified_file_policy="delete",
        windows_temp_handoff=False,
        original_uninstaller_path=None,
        temp_cleanup_dir=None,
    )
    command = uninstaller_main.build_temp_uninstaller_command(
        args,
        tmp_path / "manifest.json",
        temp_executable=tmp_path / "temp" / "tips-uninstaller.exe",
        original_uninstaller_path=tmp_path / "installed" / "tips-uninstaller.exe",
        temp_cleanup_dir=tmp_path / "temp",
    )
    assert "--manifest" in command
    assert "--silent" in command
    assert "--delete-modified" in command
    assert "--windows-temp-handoff" in command
    assert "--original-uninstaller-path" in command
    assert "--temp-cleanup-dir" in command


def test_should_use_windows_temp_handoff_detects_installed_exe(monkeypatch, tmp_path):
    install_dir = tmp_path / "install"
    current_exe = install_dir / "tips-uninstaller.exe"
    current_exe.parent.mkdir(parents=True, exist_ok=True)
    current_exe.write_text("exe", encoding="utf-8")
    manifest = install_dir / ".tips" / "manifest.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        '{"install_dir": "%s", "uninstall": {"windows_uninstaller_path": "%s"}}'
        % (install_dir.as_posix(), current_exe.as_posix()),
        encoding="utf-8",
    )
    args = Namespace(windows_temp_handoff=False)

    monkeypatch.setattr(uninstaller_main, "is_windows_runtime", lambda: True)
    monkeypatch.setattr(sys, "argv", [str(current_exe)])

    assert uninstaller_main.should_use_windows_temp_handoff(args, manifest) is True


def test_should_use_windows_temp_handoff_skips_when_already_handed_off(monkeypatch, tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text("{}", encoding="utf-8")
    args = Namespace(windows_temp_handoff=True)
    monkeypatch.setattr(uninstaller_main, "is_windows_runtime", lambda: True)
    assert uninstaller_main.should_use_windows_temp_handoff(args, manifest) is False


def test_perform_windows_temp_handoff_relaunches_copy(monkeypatch, tmp_path):
    install_dir = tmp_path / "install"
    current_exe = install_dir / "tips-uninstaller.exe"
    current_exe.parent.mkdir(parents=True, exist_ok=True)
    current_exe.write_text("exe", encoding="utf-8")
    manifest = install_dir / ".tips" / "manifest.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text("{}", encoding="utf-8")

    args = Namespace(
        manifest=None,
        install_dir=None,
        silent=True,
        delete_modified=True,
        modified_file_policy="delete",
        windows_temp_handoff=False,
        original_uninstaller_path=None,
        temp_cleanup_dir=None,
    )
    launches: list[tuple[list[str], str | None]] = []

    class _Proc:
        def __init__(self, cmd, cwd=None, **kwargs):
            launches.append((cmd, cwd))

    monkeypatch.setattr(uninstaller_main, "is_windows_runtime", lambda: True)
    monkeypatch.setattr(sys, "argv", [str(current_exe)])
    monkeypatch.setattr("installer_framework.uninstaller_main.subprocess.Popen", _Proc)
    monkeypatch.setattr("installer_framework.uninstaller_main.tempfile.gettempdir", lambda: str(tmp_path / "temp-root"))

    result = uninstaller_main.perform_windows_temp_handoff(args, manifest)

    assert result == 0
    assert launches
    command, cwd = launches[0]
    assert command[0].endswith("tips-uninstaller.exe")
    assert "--windows-temp-handoff" in command
    assert "--manifest" in command
    assert cwd is not None


def test_schedule_windows_temp_self_cleanup_uses_cmd(monkeypatch, tmp_path):
    launches: list[list[str]] = []

    class _Proc:
        def __init__(self, cmd, **kwargs):
            launches.append(cmd)

    monkeypatch.setattr(uninstaller_main, "is_windows_runtime", lambda: True)
    monkeypatch.setattr("installer_framework.uninstaller_main.subprocess.Popen", _Proc)

    uninstaller_main.schedule_windows_temp_self_cleanup(
        tmp_path / "temp" / "tips-uninstaller.exe",
        tmp_path / "temp",
    )

    assert launches
    assert launches[0][0:2] == ["cmd.exe", "/c"]


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
