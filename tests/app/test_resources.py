from __future__ import annotations

from pathlib import Path

from installer_framework.app import resources


def test_resource_path_uses_package_root_when_not_frozen(monkeypatch):
    monkeypatch.delattr(resources.sys, "_MEIPASS", raising=False)
    result = resources.resource_path("examples/sample_installer.json")
    assert isinstance(result, Path)
    assert str(result).endswith("examples/sample_installer.json")


def test_resource_path_uses_meipass_when_frozen(monkeypatch, tmp_path):
    monkeypatch.setattr(resources.sys, "_MEIPASS", str(tmp_path), raising=False)
    result = resources.resource_path("x")
    assert result == tmp_path / "x"
