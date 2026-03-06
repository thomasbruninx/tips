from __future__ import annotations

import sys
from types import SimpleNamespace

from installer_framework.util import privileges


def test_is_admin_windows_success(monkeypatch):
    fake_ctypes = SimpleNamespace(
        windll=SimpleNamespace(shell32=SimpleNamespace(IsUserAnAdmin=lambda: 1))
    )
    monkeypatch.setitem(sys.modules, "ctypes", fake_ctypes)
    assert privileges.is_admin_windows() is True


def test_is_admin_windows_exception_returns_false(monkeypatch):
    def _boom():
        raise RuntimeError("no token")

    fake_ctypes = SimpleNamespace(
        windll=SimpleNamespace(shell32=SimpleNamespace(IsUserAnAdmin=_boom))
    )
    monkeypatch.setitem(sys.modules, "ctypes", fake_ctypes)
    assert privileges.is_admin_windows() is False


def test_relaunch_as_admin_windows_success_and_failure(monkeypatch):
    fake_ctypes_success = SimpleNamespace(
        windll=SimpleNamespace(shell32=SimpleNamespace(ShellExecuteW=lambda *_args: 33))
    )
    monkeypatch.setitem(sys.modules, "ctypes", fake_ctypes_success)
    assert privileges.relaunch_as_admin_windows(["-m", "demo"]) is True

    fake_ctypes_fail = SimpleNamespace(
        windll=SimpleNamespace(shell32=SimpleNamespace(ShellExecuteW=lambda *_args: 10))
    )
    monkeypatch.setitem(sys.modules, "ctypes", fake_ctypes_fail)
    assert privileges.relaunch_as_admin_windows(["-m", "demo"]) is False


def test_relaunch_with_sudo_unix_failure_paths(monkeypatch):
    monkeypatch.setattr(privileges.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(returncode=1))
    assert privileges.relaunch_with_sudo_unix(["-m", "demo"]) is False

    def _raise(*_args, **_kwargs):
        raise RuntimeError("sudo missing")

    monkeypatch.setattr(privileges.subprocess, "run", _raise)
    assert privileges.relaunch_with_sudo_unix(["-m", "demo"]) is False
