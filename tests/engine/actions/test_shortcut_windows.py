from __future__ import annotations

from pathlib import Path

from installer_framework.engine.actions.shortcut_windows import CreateShortcutAction
from tests.helpers.context_factory import default_env, make_context


def test_shortcut_action_skips_on_non_windows(tmp_path):
    ctx = make_context(tmp_path)
    ctx.env = default_env(os_name="linux")
    action = CreateShortcutAction({"name": "App"})
    result = action.execute(ctx, lambda *_: None, lambda *_: None)
    assert result["skipped"] is True


def test_shortcut_action_records_created_paths(monkeypatch, tmp_path):
    ctx = make_context(tmp_path)
    ctx.env = default_env(os_name="windows")

    action = CreateShortcutAction({"name": "App", "desktop": True, "start_menu": True})
    monkeypatch.setattr(action, "_start_menu_dir", lambda _scope: tmp_path / "start")
    monkeypatch.setattr(action, "_desktop_dir", lambda _scope: tmp_path / "desktop")

    def _create(path: Path, _target: str, _icon: str | None, _log):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("lnk", encoding="utf-8")
        return True

    monkeypatch.setattr(action, "_create_shortcut", _create)

    result = action.execute(ctx, lambda *_: None, lambda *_: None)
    assert len(result["created"]) == 2
    assert result["rollback_records"]
