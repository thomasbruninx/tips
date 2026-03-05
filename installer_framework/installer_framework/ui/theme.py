"""Runtime UI theme helpers for classic installer styling."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from kivy.app import App

from installer_framework.config.models import ThemeConfig

Color = tuple[float, float, float, float]



def _normalize_hex(value: str) -> str:
    v = value.strip()
    if not v.startswith("#"):
        v = f"#{v}"
    return v



def hex_to_rgba(value: str, alpha: float | None = None) -> Color:
    v = _normalize_hex(value).lstrip("#")
    if len(v) == 6:
        r = int(v[0:2], 16) / 255.0
        g = int(v[2:4], 16) / 255.0
        b = int(v[4:6], 16) / 255.0
        a = 1.0 if alpha is None else alpha
    elif len(v) == 8:
        r = int(v[0:2], 16) / 255.0
        g = int(v[2:4], 16) / 255.0
        b = int(v[4:6], 16) / 255.0
        a = int(v[6:8], 16) / 255.0 if alpha is None else alpha
    else:
        r, g, b, a = (1.0, 1.0, 1.0, 1.0)
    return (r, g, b, a)



def _clamp(v: float) -> float:
    return max(0.0, min(1.0, v))



def tint(color: Color, amount: float) -> Color:
    r, g, b, a = color
    return (_clamp(r + amount), _clamp(g + amount), _clamp(b + amount), a)


@dataclass(slots=True)
class UITheme:
    """Resolved runtime theme values and utilities."""

    config: ThemeConfig
    source_root: Path

    @property
    def window_bg(self) -> Color:
        return hex_to_rgba(self.config.colors.window_bg)

    @property
    def panel_bg(self) -> Color:
        return hex_to_rgba(self.config.colors.panel_bg)

    @property
    def text_primary(self) -> Color:
        return hex_to_rgba(self.config.colors.text_primary)

    @property
    def border_light(self) -> Color:
        return hex_to_rgba(self.config.colors.border_light)

    @property
    def border_dark(self) -> Color:
        return hex_to_rgba(self.config.colors.border_dark)

    @property
    def accent(self) -> Color:
        return hex_to_rgba(self.config.colors.accent)

    @property
    def sidebar_top(self) -> Color:
        return self.accent

    @property
    def sidebar_bottom(self) -> Color:
        return tint(self.accent, 0.25)

    @property
    def button_face(self) -> Color:
        return self.window_bg

    @property
    def button_hover(self) -> Color:
        return tint(self.button_face, 0.06)

    @property
    def button_pressed(self) -> Color:
        return tint(self.button_face, -0.10)

    @property
    def content_bg(self) -> Color:
        return self.panel_bg

    def resolve_asset(self, value: str | None) -> Path | None:
        if not value:
            return None
        path = Path(value)
        if not path.is_absolute():
            path = (self.source_root / value).resolve()
        if path.exists():
            return path
        return None

    @property
    def sidebar_image(self) -> Path | None:
        return self.resolve_asset(self.config.assets.sidebar_image_path)

    @property
    def header_image(self) -> Path | None:
        return self.resolve_asset(self.config.assets.header_image_path)

    @property
    def font_name(self) -> str | None:
        font_value = self.config.typography.font_name.strip()
        if not font_value:
            return None
        font_path = self.resolve_asset(font_value)
        return str(font_path) if font_path else None

    @property
    def base_size(self) -> int:
        return self.config.typography.base_size

    @property
    def title_size(self) -> int:
        return self.config.typography.title_size

    @property
    def window_size(self) -> tuple[int, int]:
        return (self.config.metrics.window_width, self.config.metrics.window_height)

    @property
    def min_window_size(self) -> tuple[int, int]:
        return (720, 520)



def build_theme(config: ThemeConfig, source_root: Path) -> UITheme:
    return UITheme(config=config, source_root=source_root)



def get_active_theme() -> UITheme | None:
    app = App.get_running_app()
    if not app:
        return None
    return getattr(app, "ui_theme", None)
