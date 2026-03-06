from __future__ import annotations

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
