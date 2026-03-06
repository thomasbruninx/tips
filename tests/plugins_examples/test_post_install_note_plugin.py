from __future__ import annotations

import importlib.util
from pathlib import Path

from tests.helpers.context_factory import make_context


PLUGIN_FILE = Path("/Users/thomasbruninx/Projecten/tips/plugins/post_install_note.tipsplugin/plugin.py")


def _load_module():
    spec = importlib.util.spec_from_file_location("post_install_note_plugin", PLUGIN_FILE)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_post_install_note_plugin_registers_action():
    module = _load_module()
    payload = module.register()
    assert "action_class" in payload


def test_post_install_note_action_writes_file(tmp_path):
    module = _load_module()
    ActionClass = module.register()["action_class"]

    ctx = make_context(tmp_path)
    ctx.state.install_dir = str(tmp_path / "install")
    Path(ctx.state.install_dir).mkdir(parents=True, exist_ok=True)

    action = ActionClass(
        {
            "note_file": "note.txt",
            "lines": ["Product: {product_name}", "Scope: {scope}"],
        }
    )
    result = action.execute(ctx, lambda *_: None, lambda *_: None)
    target = Path(result["path"])

    assert target.exists()
    text = target.read_text(encoding="utf-8")
    assert "Product:" in text
    assert result["rollback_records"]
