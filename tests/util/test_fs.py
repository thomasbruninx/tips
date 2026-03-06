from __future__ import annotations

from pathlib import Path

from installer_framework.util.fs import ensure_dir, expand_user, is_writable


def test_ensure_dir_creates_path(tmp_path):
    target = tmp_path / "a" / "b"
    created = ensure_dir(target)
    assert created == target
    assert target.exists()


def test_is_writable_for_temp_dir(tmp_path):
    assert is_writable(tmp_path)


def test_expand_user_expands_home(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    path = expand_user("~/demo")
    assert str(path).startswith(str(Path(tmp_path).resolve()))
