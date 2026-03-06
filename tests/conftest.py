from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Callable

import pytest
from PyQt6.QtWidgets import QDialog

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

REPO_ROOT = Path(__file__).resolve().parents[1]
PKG_ROOT = REPO_ROOT / "installer_framework"
if str(PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(PKG_ROOT))

from tests.helpers.context_factory import make_context
from tests.helpers.plugin_factory import create_plugin


@pytest.fixture
def sample_config_path() -> Path:
    return REPO_ROOT / "installer_framework" / "examples" / "sample_installer.json"


@pytest.fixture
def tmp_install_ctx(tmp_path):
    def _factory(**kwargs):
        return make_context(source_root=tmp_path, **kwargs)

    return _factory


@pytest.fixture
def fake_env() -> Callable:
    from installer_framework.util.platform import EnvironmentInfo

    def _factory(os_name: str = "linux") -> EnvironmentInfo:
        return EnvironmentInfo(
            os_name=os_name,
            arch="x86_64",
            python_version="3.12.0",
            home_dir=Path.home(),
            is_windows=os_name == "windows",
            is_linux=os_name == "linux",
            is_macos=os_name == "darwin",
        )

    return _factory


@pytest.fixture
def plugin_root_factory(tmp_path):
    def _factory(*, name: str, plugin_type: str, handle: str, register_body: str, schema_fragment: dict) -> Path:
        root = tmp_path / "plugins"
        root.mkdir(parents=True, exist_ok=True)
        create_plugin(
            root,
            name=name,
            plugin_type=plugin_type,
            handle=handle,
            register_body=register_body,
            schema_fragment=schema_fragment,
        )
        return root

    return _factory


@pytest.fixture
def no_modal_exec(monkeypatch):
    calls: list[str] = []

    def _exec(self):
        calls.append(self.windowTitle())
        self.accept()
        return 0

    monkeypatch.setattr(QDialog, "exec", _exec)
    return calls
