from __future__ import annotations

from pathlib import Path

from installer_framework.engine.actions.copy_files import CopyFilesAction
from tests.helpers.context_factory import make_context


def test_copy_files_copies_from_source_root(tmp_path):
    src_dir = tmp_path / "payload"
    src_dir.mkdir()
    (src_dir / "a.txt").write_text("hello", encoding="utf-8")

    ctx = make_context(tmp_path)
    target_dir = tmp_path / "install"
    ctx.state.install_dir = str(target_dir)

    action = CopyFilesAction({"items": [{"from": "payload", "to": "."}], "overwrite": True})
    result = action.execute(ctx, lambda *_: None, lambda *_: None)

    assert (target_dir / "a.txt").exists()
    assert result["copied_items"] == 1
    assert result["rollback_records"]


def test_copy_files_requires_items(tmp_path):
    ctx = make_context(tmp_path)
    action = CopyFilesAction({"items": []})
    try:
        action.execute(ctx, lambda *_: None, lambda *_: None)
    except ValueError as exc:
        assert "requires non-empty items" in str(exc)
    else:
        raise AssertionError("expected ValueError")
