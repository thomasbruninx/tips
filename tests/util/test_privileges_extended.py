from __future__ import annotations

from types import SimpleNamespace

from installer_framework.util import privileges


def test_is_root_unix_true(monkeypatch):
    monkeypatch.setattr(privileges.os, "geteuid", lambda: 0, raising=False)
    assert privileges.is_root_unix() is True


def test_relaunch_with_sudo_unix_success(monkeypatch):
    monkeypatch.setattr(privileges.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(returncode=0))
    assert privileges.relaunch_with_sudo_unix(["-m", "demo"]) is True


def test_relaunch_as_admin_windows_handles_exception(monkeypatch):
    monkeypatch.setitem(__import__("sys").modules, "ctypes", None)
    assert privileges.relaunch_as_admin_windows(["-m", "demo"]) is False
