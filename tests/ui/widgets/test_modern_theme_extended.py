from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QWidget

from installer_framework.config.models import ThemeConfig
from installer_framework.ui.theme import UITheme
from installer_framework.ui.widgets.modern_theme import ModernShellStyler, ModernWidgetFactory


def test_modern_factory_builds_all_widget_types(qtbot):
    theme = UITheme(config=ThemeConfig(style="modern"), source_root=Path.cwd())
    factory = ModernWidgetFactory(theme)

    panel = factory.create_panel()
    sep = factory.create_separator()
    primary = factory.create_button("Install", default_action=True)
    secondary = factory.create_button("Cancel", default_action=False)
    header = factory.create_header("Title", "Description")
    sidebar = factory.create_sidebar("Title", "Subtitle")
    checkbox_row = factory.create_checkbox_row("Agree", active=True)
    group = factory.create_group_box("Group")
    dialog = factory.create_dialog_frame("Info", "Message")

    for widget in [panel, sep, primary, secondary, header, sidebar, checkbox_row, group, dialog]:
        qtbot.addWidget(widget)

    assert checkbox_row.checkbox.isChecked() is True
    assert factory.message_dialog_size()[0] > 0
    assert factory.confirm_dialog_size()[0] > 0


def test_modern_shell_styler_methods(qtbot):
    theme = UITheme(config=ThemeConfig(style="modern"), source_root=Path.cwd())
    styler = ModernShellStyler(theme)

    window = QMainWindow()
    root = QWidget()
    layout = QVBoxLayout(root)
    panel = QWidget()
    nav = QWidget()

    qtbot.addWidget(window)
    qtbot.addWidget(root)

    styler.configure_main_column_layout(layout)
    styler.style_content_panel(panel)
    styler.style_nav_widget(nav)
    styler.apply_window_style(window)
    styler.apply_global_control_style(root)

    assert styler.show_sidebar() is False
    assert styler.resolve_header_image(Path("/a"), None, None) == Path("/a")
