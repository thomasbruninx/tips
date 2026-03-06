"""Runtime UI theme helpers for installer styling."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from installer_framework.config.models import ThemeConfig

ColorTuple = tuple[int, int, int, int]

_ACTIVE_THEME: "UITheme | None" = None



def _normalize_hex(value: str) -> str:
    v = value.strip()
    if not v.startswith("#"):
        v = f"#{v}"
    return v



def hex_to_rgba_int(value: str) -> ColorTuple:
    v = _normalize_hex(value).lstrip("#")
    if len(v) == 6:
        r = int(v[0:2], 16)
        g = int(v[2:4], 16)
        b = int(v[4:6], 16)
        a = 255
    elif len(v) == 8:
        r = int(v[0:2], 16)
        g = int(v[2:4], 16)
        b = int(v[4:6], 16)
        a = int(v[6:8], 16)
    else:
        r, g, b, a = (255, 255, 255, 255)
    return (r, g, b, a)



def _clamp_channel(v: int) -> int:
    return max(0, min(255, v))



def tint_hex(value: str, amount: float) -> str:
    r, g, b, a = hex_to_rgba_int(value)
    delta = int(round(255 * amount))
    tr = _clamp_channel(r + delta)
    tg = _clamp_channel(g + delta)
    tb = _clamp_channel(b + delta)
    return f"#{tr:02X}{tg:02X}{tb:02X}{a:02X}"



def hex_to_rgb_css(value: str) -> str:
    r, g, b, _a = hex_to_rgba_int(value)
    return f"rgb({r}, {g}, {b})"


@dataclass(slots=True)
class UITheme:
    """Resolved runtime theme values and utilities."""

    config: ThemeConfig
    source_root: Path

    @property
    def style(self) -> str:
        return self.config.style

    @property
    def is_modern(self) -> bool:
        return self.style == "modern"

    @property
    def window_bg(self) -> str:
        return self.config.colors.window_bg

    @property
    def panel_bg(self) -> str:
        return self.config.colors.panel_bg

    @property
    def text_primary(self) -> str:
        return self.config.colors.text_primary

    @property
    def border_light(self) -> str:
        return self.config.colors.border_light

    @property
    def border_dark(self) -> str:
        return self.config.colors.border_dark

    @property
    def accent(self) -> str:
        return self.config.colors.accent

    @property
    def sidebar_top(self) -> str:
        if self.is_modern:
            return tint_hex(self.accent, 0.04)
        return self.accent

    @property
    def sidebar_bottom(self) -> str:
        if self.is_modern:
            return tint_hex(self.accent, -0.12)
        return tint_hex(self.accent, 0.25)

    @property
    def button_face(self) -> str:
        if self.is_modern:
            return self.panel_bg
        return self.window_bg

    @property
    def button_pressed(self) -> str:
        if self.is_modern:
            return tint_hex(self.button_face, -0.06)
        return tint_hex(self.button_face, -0.10)

    @property
    def content_bg(self) -> str:
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
        return str(font_path) if font_path else font_value

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



def set_active_theme(theme: UITheme | None) -> None:
    global _ACTIVE_THEME
    _ACTIVE_THEME = theme



def get_active_theme() -> UITheme | None:
    return _ACTIVE_THEME
