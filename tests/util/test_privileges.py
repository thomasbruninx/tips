from __future__ import annotations

from installer_framework.util import privileges


def test_has_elevated_privileges_windows_branch(monkeypatch):
    monkeypatch.setattr(privileges.sys, "platform", "win32")
    monkeypatch.setattr(privileges, "is_admin_windows", lambda: True)
    assert privileges.has_elevated_privileges() is True


def test_has_elevated_privileges_unix_branch(monkeypatch):
    monkeypatch.setattr(privileges.sys, "platform", "linux")
    monkeypatch.setattr(privileges, "is_root_unix", lambda: False)
    assert privileges.has_elevated_privileges() is False
