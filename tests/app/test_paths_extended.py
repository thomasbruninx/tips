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


def test_default_install_dir_windows_branches(monkeypatch):
    monkeypatch.setattr(paths, "get_environment_info", lambda: _env("windows"))
    monkeypatch.setenv("ProgramFiles", r"C:\PF")
    monkeypatch.setenv("ProgramFiles(x86)", r"C:\PF86")
    monkeypatch.setenv("LOCALAPPDATA", r"C:\Users\me\AppData\Local")
    monkeypatch.setenv("APPDATA", r"C:\Users\me\AppData\Roaming")

    assert str(paths.default_install_dir("Demo", "system", prefer_program_files_x86=True)).replace("\\", "/").endswith(
        "C:/PF86/Demo"
    )
    assert str(paths.default_install_dir("Demo", "system", prefer_program_files_x86=False)).replace("\\", "/").endswith(
        "C:/PF/Demo"
    )
    assert str(paths.default_install_dir("Demo", "user")).replace("\\", "/").endswith(
        "C:/Users/me/AppData/Local/Demo"
    )


def test_default_install_dir_windows_fallbacks(monkeypatch):
    monkeypatch.setattr(paths, "get_environment_info", lambda: _env("windows"))
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    monkeypatch.delenv("APPDATA", raising=False)
    monkeypatch.delenv("ProgramFiles", raising=False)
    monkeypatch.delenv("ProgramFiles(x86)", raising=False)

    system_path = paths.default_install_dir("Demo", "system")
    assert str(system_path).endswith("Program Files/Demo")

    user_path = paths.default_install_dir("Demo", "user")
    assert user_path == Path.home() / "Demo"


def test_default_install_dir_other_platform_fallback(monkeypatch):
    monkeypatch.setattr(paths, "get_environment_info", lambda: _env("other"))
    assert paths.default_install_dir("Demo", "user") == Path.home() / "Demo"


def test_config_dir_windows_and_macos(monkeypatch):
    monkeypatch.setattr(paths, "get_environment_info", lambda: _env("windows"))
    monkeypatch.setenv("APPDATA", r"C:\Users\me\AppData\Roaming")
    monkeypatch.setenv("ProgramData", r"C:\ProgramData")
    assert str(paths.user_config_dir("demo")).replace("\\", "/").endswith("C:/Users/me/AppData/Roaming/demo")
    assert str(paths.system_config_dir("demo")).replace("\\", "/").endswith("C:/ProgramData/demo")

    monkeypatch.setattr(paths, "get_environment_info", lambda: _env("darwin"))
    assert paths.user_config_dir("demo") == Path.home() / "Library" / "Application Support" / "demo"
    assert paths.system_config_dir("demo") == Path("/etc/demo")
