from __future__ import annotations

from pathlib import Path

from installer_framework.app import paths
from installer_framework.util.platform import EnvironmentInfo


def _env(os_name: str) -> EnvironmentInfo:
    return EnvironmentInfo(
        os_name=os_name,
        arch="x86_64",
        python_version="3.12",
        home_dir=Path("/home/test"),
        is_windows=os_name == "windows",
        is_linux=os_name == "linux",
        is_macos=os_name == "darwin",
    )


def test_to_product_id_normalizes_text():
    assert paths.to_product_id(" Demo App! ") == "demo-app"


def test_default_install_dir_linux_user(monkeypatch):
    monkeypatch.setattr(paths, "get_environment_info", lambda: _env("linux"))
    result = paths.default_install_dir("Demo App", "user")
    assert str(result).endswith(".local/share/demo-app")


def test_default_install_dir_macos_system(monkeypatch):
    monkeypatch.setattr(paths, "get_environment_info", lambda: _env("darwin"))
    result = paths.default_install_dir("Demo App", "system")
    assert result == Path("/Applications/Demo App.app")
