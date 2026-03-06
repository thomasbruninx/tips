from __future__ import annotations

from pathlib import Path

import pytest

from installer_framework.engine.actions.run_script import RunScriptAction
from tests.helpers.context_factory import make_context


def test_run_script_executes_and_returns_hook_record(tmp_path):
    ctx = make_context(tmp_path)
    ctx.state.install_dir = str(tmp_path / "install")
    Path(ctx.state.install_dir).mkdir(parents=True, exist_ok=True)

    script = tmp_path / "hook.py"
    undo = tmp_path / "undo.py"
    uninstall = tmp_path / "uninstall.py"
    script.write_text("api['write_config']('out.json', {'ok': True})", encoding="utf-8")
    undo.write_text("print('undo')", encoding="utf-8")
    uninstall.write_text("print('uninstall')", encoding="utf-8")

    action = RunScriptAction({"path": str(script), "undo_path": str(undo), "uninstall_path": str(uninstall)})
    result = action.execute(ctx, lambda *_: None, lambda *_: None)

    assert (Path(ctx.state.install_dir) / "out.json").exists()
    assert result["rollback_records"]


def test_run_script_requires_undo_hook_when_rollback_enabled(tmp_path):
    ctx = make_context(tmp_path)
    script = tmp_path / "hook.py"
    script.write_text("print('x')", encoding="utf-8")

    action = RunScriptAction({"path": str(script)})
    with pytest.raises(ValueError):
        action.execute(ctx, lambda *_: None, lambda *_: None)
