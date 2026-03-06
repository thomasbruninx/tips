from __future__ import annotations

import json
from pathlib import Path

import pytest

from installer_framework.engine.actions.run_script import RunScriptAction
from tests.helpers.context_factory import make_context


def test_run_script_missing_path_raises_file_not_found(tmp_path):
    ctx = make_context(tmp_path)
    action = RunScriptAction({"path": str(tmp_path / "missing.py"), "undo_path": str(tmp_path / "undo.py")})
    with pytest.raises(FileNotFoundError, match="Script hook not found"):
        action.execute(ctx, lambda *_: None, lambda *_: None)


def test_run_script_relative_path_and_rollback_none(tmp_path):
    ctx = make_context(tmp_path)
    ctx.action_rollback_policy = "none"
    ctx.state.install_dir = str(tmp_path / "install")
    Path(ctx.state.install_dir).mkdir(parents=True, exist_ok=True)

    script = tmp_path / "hook.py"
    script.write_text("print('hello', 42)", encoding="utf-8")
    logs: list[str] = []
    result = RunScriptAction({"path": "hook.py"}).execute(ctx, lambda *_: None, lambda msg: logs.append(msg))

    assert result["rollback_records"] == []
    assert any("hello 42" in line for line in logs)


def test_run_script_helper_copy_file_and_dir_and_write_config(tmp_path):
    ctx = make_context(tmp_path)
    ctx.state.install_dir = str(tmp_path / "install")
    Path(ctx.state.install_dir).mkdir(parents=True, exist_ok=True)

    (tmp_path / "a.txt").write_text("file", encoding="utf-8")
    source_dir = tmp_path / "folder"
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / "b.txt").write_text("dir", encoding="utf-8")

    script = tmp_path / "hook_copy.py"
    script.write_text(
        "\n".join(
            [
                "api['copy']('a.txt', 'copied/a.txt')",
                "api['copy']('folder', 'copied_dir')",
                "api['write_config']('cfg/out.json', {'k': 'v'})",
            ]
        ),
        encoding="utf-8",
    )
    undo = tmp_path / "undo.py"
    undo.write_text("print('undo')", encoding="utf-8")

    result = RunScriptAction({"path": str(script), "undo_path": str(undo)}).execute(ctx, lambda *_: None, lambda *_: None)

    assert (Path(ctx.state.install_dir) / "copied" / "a.txt").read_text(encoding="utf-8") == "file"
    assert (Path(ctx.state.install_dir) / "copied_dir" / "b.txt").read_text(encoding="utf-8") == "dir"
    cfg = json.loads((Path(ctx.state.install_dir) / "cfg" / "out.json").read_text(encoding="utf-8"))
    assert cfg["k"] == "v"
    assert result["rollback_records"]


def test_run_script_resolves_relative_undo_and_uninstall_paths(tmp_path):
    ctx = make_context(tmp_path)
    ctx.state.install_dir = str(tmp_path / "install")
    Path(ctx.state.install_dir).mkdir(parents=True, exist_ok=True)

    script = tmp_path / "hook.py"
    undo = tmp_path / "undo.py"
    uninstall = tmp_path / "uninstall.py"
    for path in (script, undo, uninstall):
        path.write_text("print('ok')", encoding="utf-8")

    result = RunScriptAction({"path": "hook.py", "undo_path": "undo.py", "uninstall_path": "uninstall.py"}).execute(
        ctx, lambda *_: None, lambda *_: None
    )
    record = result["rollback_records"][0]
    assert record["undo_path"] == str(undo.resolve())
    assert record["uninstall_path"] == str(uninstall.resolve())
