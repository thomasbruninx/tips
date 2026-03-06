from __future__ import annotations

from pathlib import Path

from installer_framework.engine.actions.shortcut_windows import CreateShortcutAction
from tests.helpers.context_factory import default_env, make_context


class _TxOk:
    def __init__(self, root: Path) -> None:
        self.root = root

    def create_file_backup(self, path: Path) -> Path:
        backup = self.root / f"{path.name}.bak"
        backup.write_bytes(path.read_bytes())
        return backup


class _TxFail:
    def create_file_backup(self, path: Path) -> Path:
        raise RuntimeError(f"cannot backup {path}")


def test_start_menu_and_desktop_dirs_for_scope(monkeypatch):
    action = CreateShortcutAction({})
    monkeypatch.setenv("ProgramData", r"C:\ProgramData")
    monkeypatch.setenv("APPDATA", r"C:\Users\me\AppData\Roaming")
    monkeypatch.setenv("PUBLIC", r"C:\Users\Public")

    system_menu = action._start_menu_dir("system")
    user_menu = action._start_menu_dir("user")
    system_desktop = action._desktop_dir("system")
    user_desktop = action._desktop_dir("user")

    assert str(system_menu).replace("\\", "/").endswith("C:/ProgramData/Microsoft/Windows/Start Menu/Programs")
    assert str(user_menu).replace("\\", "/").endswith("C:/Users/me/AppData/Roaming/Microsoft/Windows/Start Menu/Programs")
    assert str(system_desktop).replace("\\", "/").endswith("C:/Users/Public/Desktop")
    assert user_desktop.name == "Desktop"


def test_create_shortcut_fallback_paths(monkeypatch, tmp_path):
    action = CreateShortcutAction({})
    logs: list[str] = []
    shortcut_path = tmp_path / "x.lnk"

    monkeypatch.setattr(action, "_create_with_pywin32", lambda *_args, **_kwargs: None)
    assert action._create_shortcut(shortcut_path, "C:/app.exe", None, logs.append) is True
    assert any("pywin32" in line for line in logs)

    logs.clear()

    def _raise(*_args, **_kwargs):
        raise RuntimeError("fail")

    monkeypatch.setattr(action, "_create_with_pywin32", _raise)
    monkeypatch.setattr(action, "_create_with_winshell", lambda *_args, **_kwargs: None)
    assert action._create_shortcut(shortcut_path, "C:/app.exe", None, logs.append) is True
    assert any("winshell" in line for line in logs)

    logs.clear()
    monkeypatch.setattr(action, "_create_with_winshell", _raise)
    assert action._create_shortcut(shortcut_path, "C:/app.exe", None, logs.append) is False
    assert any("unavailable" in line for line in logs)


def test_execute_records_backups_when_overwriting(monkeypatch, tmp_path):
    ctx = make_context(tmp_path)
    ctx.env = default_env(os_name="windows")
    ctx.transaction = _TxOk(tmp_path / "backups")
    (tmp_path / "backups").mkdir(parents=True, exist_ok=True)

    action = CreateShortcutAction({"name": "App", "desktop": True, "start_menu": True})
    monkeypatch.setattr(action, "_start_menu_dir", lambda _scope: tmp_path / "start")
    monkeypatch.setattr(action, "_desktop_dir", lambda _scope: tmp_path / "desktop")

    existing_start = tmp_path / "start" / "App.lnk"
    existing_desktop = tmp_path / "desktop" / "App.lnk"
    existing_start.parent.mkdir(parents=True, exist_ok=True)
    existing_desktop.parent.mkdir(parents=True, exist_ok=True)
    existing_start.write_text("old", encoding="utf-8")
    existing_desktop.write_text("old", encoding="utf-8")

    def _create(path: Path, _target: str, _icon: str | None, _log):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("new", encoding="utf-8")
        return True

    monkeypatch.setattr(action, "_create_shortcut", _create)
    result = action.execute(ctx, lambda *_: None, lambda *_: None)

    assert len(result["created"]) == 2
    assert len(result["rollback_records"]) == 2
    assert all(record["existed_before"] for record in result["rollback_records"])
    assert all(record["backup_path"] for record in result["rollback_records"])


def test_execute_handles_backup_failures_and_shortcut_creation_failure(monkeypatch, tmp_path):
    ctx = make_context(tmp_path)
    ctx.env = default_env(os_name="windows")
    ctx.transaction = _TxFail()
    ctx.action_rollback_policy = "auto"

    action = CreateShortcutAction({"name": "App", "desktop": False, "start_menu": True})
    monkeypatch.setattr(action, "_start_menu_dir", lambda _scope: tmp_path / "start")
    path = tmp_path / "start" / "App.lnk"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("old", encoding="utf-8")

    monkeypatch.setattr(action, "_create_shortcut", lambda *_args, **_kwargs: False)
    result = action.execute(ctx, lambda *_: None, lambda *_: None)

    assert result["created"] == []
    assert result["rollback_records"] == []


def test_execute_without_target_uses_target_relative(monkeypatch, tmp_path):
    ctx = make_context(tmp_path, install_dir=str(tmp_path / "install"))
    ctx.env = default_env(os_name="windows")
    captured_targets: list[str] = []

    action = CreateShortcutAction({"name": "App", "desktop": False, "start_menu": True, "target_relative": "bin/app.exe"})
    monkeypatch.setattr(action, "_start_menu_dir", lambda _scope: tmp_path / "start")

    def _create(path: Path, target: str, _icon: str | None, _log):
        captured_targets.append(target)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("lnk", encoding="utf-8")
        return True

    monkeypatch.setattr(action, "_create_shortcut", _create)
    result = action.execute(ctx, lambda *_: None, lambda *_: None)

    assert result["created"]
    assert captured_targets == [str(Path(ctx.state.install_dir) / "bin/app.exe")]
