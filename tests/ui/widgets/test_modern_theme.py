from __future__ import annotations

from pathlib import Path

from installer_framework.config.models import ThemeConfig
from installer_framework.ui.theme import UITheme
from installer_framework.ui.widgets.modern_theme import ModernShellStyler, ModernWidgetFactory


def test_modern_widget_factory_primary_button(qtbot):
    theme = UITheme(config=ThemeConfig(style="modern"), source_root=Path.cwd())
    factory = ModernWidgetFactory(theme)
    btn = factory.create_button("Install", default_action=True)
    qtbot.addWidget(btn)
    assert "background-color" in btn.styleSheet()


def test_modern_shell_styler_no_sidebar():
    theme = UITheme(config=ThemeConfig(style="modern"), source_root=Path.cwd())
    styler = ModernShellStyler(theme)
    assert styler.show_sidebar() is False
    assert styler.include_separator() is False
