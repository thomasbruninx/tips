"""Qt modal dialogs for messages and confirmations."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from PyQt6.QtWidgets import QDialog, QHBoxLayout, QWidget

from installer_framework.config.models import ThemeConfig
from installer_framework.ui.theme import UITheme, get_active_theme
from installer_framework.ui.widgets.theme import build_widget_factory

_DEFAULT_THEME = UITheme(config=ThemeConfig(), source_root=Path.cwd())



def _theme() -> UITheme:
    return get_active_theme() or _DEFAULT_THEME



def show_message_dialog(level: str, title: str, message: str) -> None:
    theme = _theme()
    widget_factory = build_widget_factory(theme)
    dialog = QDialog()
    dialog.setWindowTitle(title)
    dialog.setModal(True)
    width, height = widget_factory.message_dialog_size()
    dialog.resize(width, height)
    dialog.setObjectName("ThemeDialog")
    dialog.setStyleSheet(f"QDialog#ThemeDialog {{ background-color: {theme.window_bg}; }}")

    frame = widget_factory.create_dialog_frame(title=title, message=message)
    frame.buttons_layout.addStretch(1)
    ok_btn = widget_factory.create_button("OK", default_action=True)
    ok_btn.setFixedWidth(88)
    ok_btn.clicked.connect(dialog.accept)
    frame.buttons_layout.addWidget(ok_btn)

    if level == "error":
        frame.title_label.setStyleSheet("color: #8B0000;")
    elif level == "warn":
        frame.title_label.setStyleSheet("color: #8B5A00;")

    root = QHBoxLayout(dialog)
    root.setContentsMargins(*widget_factory.dialog_margins())
    root.addWidget(frame)
    dialog.exec()



def show_confirm_dialog(title: str, message: str, callback: Callable[[bool], None]) -> None:
    theme = _theme()
    widget_factory = build_widget_factory(theme)
    dialog = QDialog()
    dialog.setWindowTitle(title)
    dialog.setModal(True)
    width, height = widget_factory.confirm_dialog_size()
    dialog.resize(width, height)
    dialog.setObjectName("ThemeDialog")
    dialog.setStyleSheet(f"QDialog#ThemeDialog {{ background-color: {theme.window_bg}; }}")

    frame = widget_factory.create_dialog_frame(title=title, message=message)
    frame.buttons_layout.addStretch(1)
    yes_btn = widget_factory.create_button("Yes", default_action=True)
    yes_btn.setFixedWidth(88)
    no_btn = widget_factory.create_button("No")
    no_btn.setFixedWidth(88)

    yes_btn.clicked.connect(lambda: (callback(True), dialog.accept()))
    no_btn.clicked.connect(lambda: (callback(False), dialog.reject()))

    frame.buttons_layout.addWidget(yes_btn)
    frame.buttons_layout.addWidget(no_btn)

    root = QHBoxLayout(dialog)
    root.setContentsMargins(*widget_factory.dialog_margins())
    root.addWidget(frame)
    dialog.exec()
