"""Runtime UI theme helpers for installer styling."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from PyQt6.QtGui import QFontDatabase
from PyQt6.QtWidgets import QApplication

from installer_framework.app.resources import resource_path
from installer_framework.config.models import ThemeConfig

ColorTuple = tuple[int, int, int, int]

_ACTIVE_THEME: "UITheme | None" = None
LOGGER = logging.getLogger(__name__)



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
    r, g, b, _a = hex_to_rgba_int(value)
    delta = int(round(255 * amount))
    tr = _clamp_channel(r + delta)
    tg = _clamp_channel(g + delta)
    tb = _clamp_channel(b + delta)
    # Return Qt-safe opaque color format to avoid alpha-order ambiguity in QSS.
    return f"#{tr:02X}{tg:02X}{tb:02X}"



def hex_to_rgb_css(value: str) -> str:
    r, g, b, _a = hex_to_rgba_int(value)
    return f"rgb({r}, {g}, {b})"


@dataclass(slots=True)
class UITheme:
    """Resolved runtime theme values and utilities."""

    config: ThemeConfig
    source_root: Path
    _fonts_loaded: bool = field(init=False, default=False)
    _catalog_families: set[str] = field(init=False, default_factory=set)
    _available_families: set[str] = field(init=False, default_factory=set)
    _warned_missing_ttf: set[str] = field(init=False, default_factory=set)
    _warned_missing_catalog_family: set[str] = field(init=False, default_factory=set)

    def _family_key(self, value: str) -> str:
        return value.strip().casefold()

    def _warn_once(self, bucket: set[str], key: str, message: str) -> None:
        if key in bucket:
            return
        bucket.add(key)
        LOGGER.warning(message)

    def _resolve_font_ttf(self, value: str) -> Path | None:
        raw_path = Path(value).expanduser()
        if raw_path.is_absolute():
            if raw_path.exists():
                return raw_path
            bundled_absolute_fallback = resource_path(f"fonts/{raw_path.name}")
            if bundled_absolute_fallback.exists():
                return bundled_absolute_fallback
            return None

        source_relative = (self.source_root / raw_path).resolve()
        if source_relative.exists():
            return source_relative
        bundled_relative = resource_path(str(raw_path))
        if bundled_relative.exists():
            return bundled_relative
        return None

    def _ensure_fonts_loaded(self) -> None:
        if self._fonts_loaded:
            return
        if QApplication.instance() is None:
            return

        self._catalog_families = {self._family_key(entry.font_family) for entry in self.config.typography.fonts}
        self._available_families = {self._family_key(name) for name in QFontDatabase.families()}

        for entry in self.config.typography.fonts:
            ttf = (entry.font_ttf_path or "").strip()
            if not ttf:
                continue
            resolved_ttf = self._resolve_font_ttf(ttf)
            if not resolved_ttf:
                self._warn_once(
                    self._warned_missing_ttf,
                    ttf,
                    f"Typography font_ttf_path not found, falling back to next candidate: {ttf}",
                )
                continue
            font_id = QFontDatabase.addApplicationFont(str(resolved_ttf))
            if font_id < 0:
                self._warn_once(
                    self._warned_missing_ttf,
                    str(resolved_ttf),
                    f"Failed to load font TTF, falling back to next candidate: {resolved_ttf}",
                )
                continue
            for family in QFontDatabase.applicationFontFamilies(font_id):
                self._available_families.add(self._family_key(family))

        # Refresh from the DB after registering custom fonts.
        self._available_families = {self._family_key(name) for name in QFontDatabase.families()} | self._available_families
        self._fonts_loaded = True

    def _default_preset_name(self) -> str:
        presets = self.config.typography.presets
        if self.config.typography.default_preset and self.config.typography.default_preset in presets:
            return self.config.typography.default_preset
        if presets:
            return next(iter(presets.keys()))
        return ""

    def effective_preset_for_step(self, step_preset: str | None) -> str:
        if step_preset and step_preset in self.config.typography.presets:
            return step_preset
        return self._default_preset_name()

    def resolve_role_font(self, role: str, preset_name: str | None = None) -> tuple[str | None, int]:
        selected_preset = self.effective_preset_for_step(preset_name)
        preset = self.config.typography.presets.get(selected_preset)
        if not preset:
            return (None, 12)

        role_entries = preset.title if role == "title" else preset.text
        if not role_entries:
            return (None, 12)

        if QApplication.instance() is None:
            entry = role_entries[0]
            return (entry.font_family.strip() or None, entry.font_size)

        self._ensure_fonts_loaded()
        for entry in role_entries:
            family = entry.font_family.strip()
            if not family:
                continue
            if self._family_key(family) not in self._catalog_families:
                self._warn_once(
                    self._warned_missing_catalog_family,
                    family,
                    f"Typography family '{family}' is not declared in theme.typography.fonts. Falling back if unavailable.",
                )
            if self._family_key(family) in self._available_families:
                return (family, entry.font_size)

        fallback = role_entries[0]
        return (fallback.font_family.strip() or None, fallback.font_size)

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
            bundled = resource_path(value)
            if bundled.exists():
                return bundled
            return None
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
        family, _size = self.resolve_role_font("text")
        return family

    @property
    def base_size(self) -> int:
        _family, size = self.resolve_role_font("text")
        return size

    @property
    def title_size(self) -> int:
        _family, size = self.resolve_role_font("title")
        return size

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
