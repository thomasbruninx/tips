from __future__ import annotations

from installer_framework.config.models import ThemeConfig
from installer_framework.ui.theme import UITheme
from installer_framework.ui.widgets.theme import build_shell_styler, build_widget_factory


def test_theme_factory_selects_classic():
    theme = UITheme(config=ThemeConfig(style="classic"), source_root=__import__("pathlib").Path.cwd())
    factory = build_widget_factory(theme)
    styler = build_shell_styler(theme)
    assert factory.__class__.__name__ == "ClassicWidgetFactory"
    assert styler.__class__.__name__ == "ClassicShellStyler"


def test_theme_factory_selects_modern():
    theme = UITheme(config=ThemeConfig(style="modern"), source_root=__import__("pathlib").Path.cwd())
    factory = build_widget_factory(theme)
    styler = build_shell_styler(theme)
    assert factory.__class__.__name__ == "ModernWidgetFactory"
    assert styler.__class__.__name__ == "ModernShellStyler"
