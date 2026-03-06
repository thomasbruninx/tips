from __future__ import annotations

from installer_framework.config.models import FieldConfig
from installer_framework.ui.widgets.validated_text_input import ValidatedTextInput


def test_validated_text_input_required(qtbot):
    widget = ValidatedTextInput(FieldConfig(id="x", type="text", label="X", required=True))
    qtbot.addWidget(widget)
    ok, msg = widget.validate()
    assert ok is False
    assert msg


def test_validated_text_input_password_complexity(qtbot):
    field = FieldConfig(id="pw", type="password", label="Password", complexity=True)
    widget = ValidatedTextInput(field)
    qtbot.addWidget(widget)
    widget.set_value("abc")
    ok, _ = widget.validate()
    assert ok is False
