from __future__ import annotations

import logging
from pathlib import Path

from installer_framework.config.models import ThemeConfig
from installer_framework.ui.theme import build_theme, hex_to_rgba_int, tint_hex


def test_tint_hex_returns_opaque_rgb():
    value = tint_hex("#0071E3FF", -0.04)
    assert value.startswith("#")
    assert len(value) == 7


def test_hex_to_rgba_int_handles_8_digit():
    assert hex_to_rgba_int("#01020304") == (1, 2, 3, 4)


def test_build_theme_exposes_sizes():
    theme = build_theme(ThemeConfig(), Path.cwd())
    assert theme.window_size == (780, 560)


def test_theme_role_font_resolution_uses_preset_defaults():
    theme = build_theme(ThemeConfig(), Path.cwd())
    family, size = theme.resolve_role_font("text")
    assert family
    assert size > 0

    title_family, title_size = theme.resolve_role_font("title")
    assert title_family
    assert title_size > 0


def test_theme_role_font_resolution_for_missing_preset_falls_back_to_default():
    theme = build_theme(ThemeConfig(), Path.cwd())
    default_title = theme.resolve_role_font("title")
    assert theme.resolve_role_font("title", preset_name="missing") == default_title


def test_theme_warns_for_missing_ttf_and_unknown_catalog_family(caplog, qtbot):
    cfg = ThemeConfig()
    cfg.typography.fonts = [
        type(cfg.typography.fonts[0])(font_family="MissingFontOne", font_ttf_path="assets/fonts/missing.ttf"),
        type(cfg.typography.fonts[0])(font_family="MissingFontTwo"),
    ]
    cfg.typography.default_preset = "default"
    preset = cfg.typography.presets["default"]
    preset.text = [
        type(preset.text[0])(font_family="MissingFontOne", font_size=12),
        type(preset.text[0])(font_family="MissingFontTwo", font_size=12),
    ]
    preset.title = [
        type(preset.title[0])(font_family="UndeclaredFontFamily", font_size=16),
        type(preset.title[0])(font_family="MissingFontTwo", font_size=16),
    ]

    caplog.set_level(logging.WARNING)
    theme = build_theme(cfg, Path.cwd())
    _family, _size = theme.resolve_role_font("text")
    _family2, _size2 = theme.resolve_role_font("title")

    combined = "\n".join(record.message for record in caplog.records)
    assert "font_ttf_path not found" in combined
    assert "not declared in theme.typography.fonts" in combined
