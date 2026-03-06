from __future__ import annotations

from types import SimpleNamespace

from installer_framework.util import privileges


def test_is_root_unix_true(monkeypatch):
    monkeypatch.setattr(privileges.os, "geteuid", lambda: 0, raising=False)
    assert privileges.is_root_unix() is True


def test_relaunch_with_sudo_unix_success(monkeypatch):
    monkeypatch.setattr(privileges.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(returncode=0))
    assert privileges.relaunch_with_sudo_unix(["-m", "demo"]) is True


def test_relaunch_as_admin_macos_success(monkeypatch):
    captured: dict[str, object] = {}

    def _run(cmd, check=False):
        captured["cmd"] = cmd
        captured["check"] = check
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(privileges.subprocess, "run", _run)
    monkeypatch.setattr(privileges.sys, "frozen", False, raising=False)
    monkeypatch.setattr(privileges.sys, "_MEIPASS", None, raising=False)
    monkeypatch.setattr(privileges.sys, "executable", "/usr/bin/python3")

    assert privileges.relaunch_as_admin_macos(["--config", "examples/sample_installer.json"]) is True
    cmd = captured["cmd"]
    assert isinstance(cmd, list)
    assert cmd[0] == "osascript"
    assert cmd[1] == "-e"
    assert "installer_framework.main" in cmd[2]


def test_relaunch_as_admin_windows_handles_exception(monkeypatch):
    monkeypatch.setitem(__import__("sys").modules, "ctypes", None)
    assert privileges.relaunch_as_admin_windows(["-m", "demo"]) is False
