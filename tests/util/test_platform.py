from __future__ import annotations

from installer_framework.util.platform import get_env_var, get_environment_info


def test_get_environment_info_flags_are_consistent():
    info = get_environment_info()
    flags = [info.is_windows, info.is_linux, info.is_macos]
    assert sum(1 for item in flags if item) <= 1
    assert info.os_name


def test_get_env_var_with_default(monkeypatch):
    monkeypatch.delenv("TIPS_MISSING", raising=False)
    assert get_env_var("TIPS_MISSING", "fallback") == "fallback"
