from __future__ import annotations

from pathlib import Path

from installer_framework.engine.actions.desktop_entry_linux import CreateDesktopEntryAction
from tests.helpers.context_factory import default_env, make_context


def test_desktop_entry_skips_on_non_linux(tmp_path):
    ctx = make_context(tmp_path)
    ctx.env = default_env(os_name="windows")
    action = CreateDesktopEntryAction({"id": "tips", "name": "TIPS"})
    result = action.execute(ctx, lambda *_: None, lambda *_: None)
    assert result["skipped"] is True


def test_desktop_entry_writes_file(monkeypatch, tmp_path):
    ctx = make_context(tmp_path)
    ctx.env = default_env(os_name="linux")
    ctx.state.install_dir = str(tmp_path / "install")

    monkeypatch.setattr("installer_framework.engine.actions.desktop_entry_linux.Path.home", lambda: tmp_path)

    action = CreateDesktopEntryAction({"id": "tips-demo", "name": "TIPS Demo", "exec_relative": "bin/app"})
    result = action.execute(ctx, lambda *_: None, lambda *_: None)

    path = Path(result["path"])
    assert path.exists()
    assert "[Desktop Entry]" in path.read_text(encoding="utf-8")
