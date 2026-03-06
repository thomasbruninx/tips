from __future__ import annotations

from installer_framework.engine.actions.show_message import ShowMessageAction
from tests.helpers.context_factory import make_context


def test_show_message_formats_template(tmp_path):
    ctx = make_context(tmp_path)
    logs: list[str] = []
    action = ShowMessageAction({"title": "Done", "message": "Installed to {install_dir} ({scope})"})
    result = action.execute(ctx, lambda *_: None, logs.append)

    assert result["title"] == "Done"
    assert ctx.state.install_dir in result["message"]
    assert logs and "Done" in logs[0]
