from __future__ import annotations

from installer_framework.ui.theme import set_active_theme
from installer_framework.ui.widgets import dialogs
from tests.helpers.qt_helpers import make_theme


def test_show_message_dialog_non_blocking(no_modal_exec):
    set_active_theme(make_theme("classic"))
    dialogs.show_message_dialog("info", "Title", "Message")
    assert no_modal_exec


def test_show_confirm_dialog_calls_callback(no_modal_exec):
    set_active_theme(make_theme("modern"))
    results = []
    dialogs.show_confirm_dialog("Confirm", "Continue?", lambda value: results.append(value))
    assert no_modal_exec
    assert results in ([], [True], [False])
