from __future__ import annotations

from pathlib import Path

from installer_framework.config.models import ThemeConfig
from installer_framework.ui.theme import UITheme
from installer_framework.ui.widgets.classic_theme import ClassicShellStyler, ClassicWidgetFactory


def test_classic_widget_factory_button_styles(qtbot):
    theme = UITheme(config=ThemeConfig(style="classic"), source_root=Path.cwd())
    factory = ClassicWidgetFactory(theme)
    btn = factory.create_button("Next", default_action=True)
    qtbot.addWidget(btn)
    assert "QPushButton" in btn.styleSheet()


def test_classic_shell_styler_has_sidebar():
    theme = UITheme(config=ThemeConfig(style="classic"), source_root=Path.cwd())
    styler = ClassicShellStyler(theme)
    assert styler.show_sidebar() is True
    assert styler.include_separator() is True
