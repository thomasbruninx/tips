from __future__ import annotations

from installer_framework.ui.widgets.log_pane import LogPane


def test_log_pane_toggle_and_append(qtbot):
    pane = LogPane()
    qtbot.addWidget(pane)
    pane.show()

    assert pane.output.isHidden() is True
    pane.toggle()
    assert pane.output.isHidden() is False

    pane.append("line")
    assert "line" in pane.get_text()
