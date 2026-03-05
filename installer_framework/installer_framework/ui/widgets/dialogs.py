"""Kivy modal dialogs for messages and confirmations."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from kivy.metrics import dp
from kivy.uix.modalview import ModalView
from kivy.uix.widget import Widget

from installer_framework.config.models import ThemeConfig
from installer_framework.ui.theme import UITheme, get_active_theme
from installer_framework.ui.widgets.classic import ClassicButton, ClassicDialogFrame


_DEFAULT_THEME = UITheme(config=ThemeConfig(), source_root=Path.cwd())



def _theme() -> UITheme:
    return get_active_theme() or _DEFAULT_THEME



def show_message_dialog(level: str, title: str, message: str) -> None:
    theme = _theme()
    modal = ModalView(size_hint=(0.62, 0.34), auto_dismiss=False)
    frame = ClassicDialogFrame(theme=theme, title=title, message=message)

    frame.buttons.add_widget(Widget())
    close_btn = ClassicButton(theme=theme, text="OK", default_action=True, size_hint_x=None, width=dp(88), size_hint_y=None, height=dp(theme.config.metrics.button_height))
    close_btn.bind(on_release=lambda *_: modal.dismiss())
    frame.buttons.add_widget(close_btn)

    if level == "error":
        frame.title_label.color = (0.6, 0.0, 0.0, 1)
    elif level == "warn":
        frame.title_label.color = (0.5, 0.35, 0.0, 1)

    modal.add_widget(frame)
    modal.open()



def show_confirm_dialog(title: str, message: str, callback: Callable[[bool], None]) -> None:
    theme = _theme()
    modal = ModalView(size_hint=(0.64, 0.36), auto_dismiss=False)
    frame = ClassicDialogFrame(theme=theme, title=title, message=message)

    frame.buttons.add_widget(Widget())
    yes_btn = ClassicButton(theme=theme, text="Yes", default_action=True, size_hint_x=None, width=dp(88), size_hint_y=None, height=dp(theme.config.metrics.button_height))
    no_btn = ClassicButton(theme=theme, text="No", size_hint_x=None, width=dp(88), size_hint_y=None, height=dp(theme.config.metrics.button_height))

    def finish(value: bool) -> None:
        modal.dismiss()
        callback(value)

    yes_btn.bind(on_release=lambda *_: finish(True))
    no_btn.bind(on_release=lambda *_: finish(False))
    frame.buttons.add_widget(yes_btn)
    frame.buttons.add_widget(no_btn)

    modal.add_widget(frame)
    modal.open()
