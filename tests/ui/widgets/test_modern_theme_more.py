from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

from installer_framework.config.models import ThemeConfig
from installer_framework.ui.theme import UITheme
from installer_framework.ui.widgets.modern_theme import ModernShellStyler, ModernWidgetFactory


def test_modern_header_image_and_empty_description_branch(qtbot, tmp_path):
    img = QPixmap(12, 12)
    img.fill(Qt.GlobalColor.white)
    image_path = tmp_path / "logo.png"
    assert img.save(str(image_path), "PNG")

    theme = UITheme(config=ThemeConfig(style="modern"), source_root=Path.cwd())
    factory = ModernWidgetFactory(theme)
    header = factory.create_header("Title", "", image_path=str(image_path))
    qtbot.addWidget(header)
    assert header.layout().count() >= 1


def test_modern_checkbox_row_toggles_from_button_click(qtbot):
    theme = UITheme(config=ThemeConfig(style="modern"), source_root=Path.cwd())
    row = ModernWidgetFactory(theme).create_checkbox_row("Agree", active=False)
    qtbot.addWidget(row)
    assert row.checkbox.isChecked() is False
    row.button.click()
    assert row.checkbox.isChecked() is True


def test_modern_sidebar_paint_branches(monkeypatch, qtbot):
    theme = UITheme(config=ThemeConfig(style="modern"), source_root=Path.cwd())
    factory = ModernWidgetFactory(theme)

    class _FakePainter:
        draw_pixmap_calls = 0
        draw_text_calls = 0

        def __init__(self, *_args, **_kwargs):
            return None

        def fillRect(self, *_args, **_kwargs):
            return None

        def setPen(self, *_args, **_kwargs):
            return None

        def drawLine(self, *_args, **_kwargs):
            return None

        def drawPixmap(self, *_args, **_kwargs):
            _FakePainter.draw_pixmap_calls += 1

        def setFont(self, *_args, **_kwargs):
            return None

        def drawText(self, *_args, **_kwargs):
            _FakePainter.draw_text_calls += 1

    monkeypatch.setattr("installer_framework.ui.widgets.modern_theme.QPainter", _FakePainter)

    # No pixmap branch -> draw text fallback.
    sidebar = factory.create_sidebar("Title", "Subtitle")
    qtbot.addWidget(sidebar)
    sidebar.resize(120, 180)
    sidebar.paintEvent(None)
    assert _FakePainter.draw_text_calls > 0

    # Pixmap branch -> drawPixmap and early return.
    sidebar_with_image = factory.create_sidebar("Title", "Subtitle")
    qtbot.addWidget(sidebar_with_image)
    pm = QPixmap(10, 10)
    pm.fill(Qt.GlobalColor.white)
    sidebar_with_image.pixmap = pm
    sidebar_with_image.resize(120, 180)
    before = _FakePainter.draw_pixmap_calls
    sidebar_with_image.paintEvent(None)
    assert _FakePainter.draw_pixmap_calls > before


def test_modern_shell_styler_metric_methods_and_fallbacks(qtbot):
    theme_low = UITheme(config=ThemeConfig(style="modern"), source_root=Path.cwd())
    styler_low = ModernShellStyler(theme_low)
    assert styler_low.root_margins() == (12, 12, 12, 12)
    assert styler_low.main_layout_spacing() == 0
    assert styler_low.header_height() == 90
    assert styler_low.nav_margins() == (12, 9, 12, 9)
    assert styler_low.content_margins() == (12, 12, 12, 12)

    theme_hi_cfg = ThemeConfig(style="modern")
    theme_hi_cfg.metrics.padding = 24
    theme_hi = UITheme(config=theme_hi_cfg, source_root=Path.cwd())
    styler_hi = ModernShellStyler(theme_hi)
    assert styler_hi.content_margins() == (24, 24, 24, 24)
    assert styler_hi.resolve_header_image(None, Path("/h"), Path("/s")) == Path("/h")
    assert styler_hi.resolve_header_image(None, None, Path("/s")) == Path("/s")
    assert styler_hi.resolve_header_image(None, None, None) is None

    # Ensure global style generation includes expected selectors.
    from PyQt6.QtWidgets import QWidget

    root = QWidget()
    qtbot.addWidget(root)
    styler_hi.apply_global_control_style(root)
    assert "QLineEdit" in root.styleSheet()
