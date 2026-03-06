from __future__ import annotations

import json

from installer_framework.engine.actions.dotfile import WriteDotfileAction
from tests.helpers.context_factory import make_context


def test_write_dotfile_overwrite_and_append(tmp_path):
    ctx = make_context(tmp_path)
    target = tmp_path / "cfg" / "demo.txt"

    write = WriteDotfileAction({"target_path": str(target), "content": "one"})
    write.execute(ctx, lambda *_: None, lambda *_: None)
    assert target.read_text(encoding="utf-8") == "one"

    append = WriteDotfileAction({"target_path": str(target), "append": True, "content": "two"})
    append.execute(ctx, lambda *_: None, lambda *_: None)
    assert target.read_text(encoding="utf-8").endswith("two\n")


def test_write_dotfile_structured_content(tmp_path):
    ctx = make_context(tmp_path)
    target = tmp_path / "state.json"
    action = WriteDotfileAction({"target_path": str(target), "content": {"x": "{version}"}})
    action.execute(ctx, lambda *_: None, lambda *_: None)
    data = json.loads(target.read_text(encoding="utf-8"))
    assert data["x"] == ctx.config.branding.version
