"""Dataclass models for JSON-driven installer definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class BrandingConfig:
    product_name: str
    publisher: str
    version: str
    logo_path: str | None = None
    window_icon_path: str | None = None


@dataclass(slots=True)
class ThemeAssetsConfig:
    sidebar_image_path: str | None = None
    header_image_path: str | None = None


@dataclass(slots=True)
class ThemeColorsConfig:
    window_bg: str = "#ECE9D8"
    panel_bg: str = "#FFFFFF"
    text_primary: str = "#000000"
    border_light: str = "#FFFFFF"
    border_dark: str = "#7F7F7F"
    accent: str = "#0A246A"


@dataclass(slots=True)
class ThemeMetricsConfig:
    window_width: int = 780
    window_height: int = 560
    sidebar_width: int = 164
    padding: int = 10
    button_height: int = 28


@dataclass(slots=True)
class ThemeFontCatalogEntry:
    font_family: str
    font_ttf_path: str | None = None


@dataclass(slots=True)
class ThemeTypographyRoleEntry:
    font_family: str
    font_size: int


@dataclass(slots=True)
class ThemeTypographyPreset:
    title: list[ThemeTypographyRoleEntry] = field(default_factory=list)
    text: list[ThemeTypographyRoleEntry] = field(default_factory=list)


def _default_classic_font_catalog() -> list[ThemeFontCatalogEntry]:
    return [
        ThemeFontCatalogEntry(font_family="Tahoma"),
        ThemeFontCatalogEntry(font_family="Segoe UI"),
        ThemeFontCatalogEntry(font_family="Arial"),
    ]


def _default_classic_typography_presets() -> dict[str, ThemeTypographyPreset]:
    return {
        "default": ThemeTypographyPreset(
            title=[
                ThemeTypographyRoleEntry(font_family="Tahoma", font_size=18),
                ThemeTypographyRoleEntry(font_family="Segoe UI", font_size=18),
                ThemeTypographyRoleEntry(font_family="Arial", font_size=18),
            ],
            text=[
                ThemeTypographyRoleEntry(font_family="Tahoma", font_size=14),
                ThemeTypographyRoleEntry(font_family="Segoe UI", font_size=14),
                ThemeTypographyRoleEntry(font_family="Arial", font_size=14),
            ],
        )
    }


@dataclass(slots=True)
class ThemeTypographyConfig:
    fonts: list[ThemeFontCatalogEntry] = field(default_factory=_default_classic_font_catalog)
    default_preset: str | None = "default"
    presets: dict[str, ThemeTypographyPreset] = field(default_factory=_default_classic_typography_presets)
    legacy_keys: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ThemeConfig:
    style: str = "classic"
    assets: ThemeAssetsConfig = field(default_factory=ThemeAssetsConfig)
    colors: ThemeColorsConfig = field(default_factory=ThemeColorsConfig)
    metrics: ThemeMetricsConfig = field(default_factory=ThemeMetricsConfig)
    typography: ThemeTypographyConfig = field(default_factory=ThemeTypographyConfig)


@dataclass(slots=True)
class FieldConfig:
    id: str
    type: str
    label: str
    default: Any = None
    placeholder: str | None = None
    required: bool = False
    regex: str | None = None
    min_length: int | None = None
    max_length: int | None = None
    choices: list[str] = field(default_factory=list)
    validators: list[str] = field(default_factory=list)
    complexity: bool = False
    show_if: str | None = None


@dataclass(slots=True)
class StepConfig:
    id: str
    type: str
    title: str
    description: str = ""
    header_description: str | None = None
    body_description: str | None = None
    fields: list[FieldConfig] = field(default_factory=list)
    show_if: str | None = None
    navigation: dict[str, Any] = field(default_factory=dict)
    license_path: str | None = None
    typography_preset: str | None = None
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class FeatureConfig:
    id: str
    label: str
    description: str = ""
    default: bool = False


@dataclass(slots=True)
class ActionConfig:
    type: str
    rollback: str = "auto"
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ShortcutSettings:
    app_name: str | None = None
    executable: str | None = None
    desktop: bool = False
    start_menu: bool = True


@dataclass(slots=True)
class UpgradeSettings:
    enabled: bool = True
    store_file: str | None = None


@dataclass(slots=True)
class UninstallUnixSettings:
    create_symlink: bool = False
    user_link_path: str | None = None
    system_link_path: str | None = None


@dataclass(slots=True)
class UninstallSettings:
    enabled: bool = True
    modified_file_policy: str = "prompt"
    unix: UninstallUnixSettings = field(default_factory=UninstallUnixSettings)


@dataclass(slots=True)
class InstallerConfig:
    branding: BrandingConfig
    product_id: str
    install_scope: str
    steps: list[StepConfig]
    actions: list[ActionConfig]
    features: list[FeatureConfig] = field(default_factory=list)
    windows: dict[str, Any] = field(default_factory=dict)
    macos: dict[str, Any] = field(default_factory=dict)
    unix: dict[str, Any] = field(default_factory=dict)
    shortcut: ShortcutSettings = field(default_factory=ShortcutSettings)
    upgrade: UpgradeSettings = field(default_factory=UpgradeSettings)
    uninstall: UninstallSettings = field(default_factory=UninstallSettings)
    hooks: dict[str, Any] = field(default_factory=dict)
    theme: ThemeConfig = field(default_factory=ThemeConfig)
    plugin_registry: Any | None = None
    plugin_statuses: list[dict[str, Any]] = field(default_factory=list)
    plugin_roots: list[str] = field(default_factory=list)
    source_root: Path = field(default_factory=lambda: Path.cwd())



def _field_from_dict(data: dict[str, Any]) -> FieldConfig:
    return FieldConfig(
        id=data["id"],
        type=data.get("type", "text"),
        label=data.get("label", data["id"]),
        default=data.get("default"),
        placeholder=data.get("placeholder"),
        required=bool(data.get("required", False)),
        regex=data.get("regex"),
        min_length=data.get("min_length"),
        max_length=data.get("max_length"),
        choices=list(data.get("choices", [])),
        validators=list(data.get("validators", [])),
        complexity=bool(data.get("complexity", False)),
        show_if=data.get("show_if"),
    )



def _step_from_dict(data: dict[str, Any]) -> StepConfig:
    payload = dict(data)
    step_id = payload.pop("id")
    step_type = payload.pop("type")
    title = payload.pop("title", step_id)
    description = payload.pop("description", "")
    header_description = payload.pop("header_description", None)
    body_description = payload.pop("body_description", None)
    fields = [_field_from_dict(f) for f in payload.pop("fields", [])]
    show_if = payload.pop("show_if", None)
    navigation = dict(payload.pop("navigation", {}))
    license_path = payload.pop("license_path", None)
    typography_preset = payload.pop("typography_preset", None)
    return StepConfig(
        id=step_id,
        type=step_type,
        title=title,
        description=description,
        header_description=header_description,
        body_description=body_description,
        fields=fields,
        show_if=show_if,
        navigation=navigation,
        license_path=license_path,
        typography_preset=typography_preset,
        params=payload,
    )



def _feature_from_dict(data: dict[str, Any]) -> FeatureConfig:
    return FeatureConfig(
        id=data["id"],
        label=data.get("label", data["id"]),
        description=data.get("description", ""),
        default=bool(data.get("default", False)),
    )



def _action_from_dict(data: dict[str, Any]) -> ActionConfig:
    payload = dict(data)
    action_type = payload.pop("type")
    rollback = str(payload.pop("rollback", "auto"))
    return ActionConfig(type=action_type, rollback=rollback, params=payload)



def _theme_from_dict(data: dict[str, Any]) -> ThemeConfig:
    style = data.get("style", "classic")
    default_assets = ThemeAssetsConfig()

    def _default_typography(theme_style: str) -> ThemeTypographyConfig:
        if theme_style == "modern":
            return ThemeTypographyConfig(
                fonts=[
                    ThemeFontCatalogEntry(font_family="SF Pro Text"),
                    ThemeFontCatalogEntry(font_family="SF Pro Display"),
                    ThemeFontCatalogEntry(font_family="Segoe UI"),
                    ThemeFontCatalogEntry(font_family="Segoe UI Semibold"),
                    ThemeFontCatalogEntry(font_family="Arial"),
                ],
                default_preset="default",
                presets={
                    "default": ThemeTypographyPreset(
                        title=[
                            ThemeTypographyRoleEntry(font_family="SF Pro Display", font_size=17),
                            ThemeTypographyRoleEntry(font_family="Segoe UI Semibold", font_size=17),
                            ThemeTypographyRoleEntry(font_family="Arial", font_size=17),
                        ],
                        text=[
                            ThemeTypographyRoleEntry(font_family="SF Pro Text", font_size=13),
                            ThemeTypographyRoleEntry(font_family="Segoe UI", font_size=13),
                            ThemeTypographyRoleEntry(font_family="Arial", font_size=13),
                        ],
                    )
                },
            )

        return ThemeTypographyConfig(
            fonts=_default_classic_font_catalog(),
            default_preset="default",
            presets=_default_classic_typography_presets(),
        )

    if style == "modern":
        default_colors = ThemeColorsConfig(
            window_bg="#F5F5F7",
            panel_bg="#FFFFFF",
            text_primary="#1D1D1F",
            border_light="#FFFFFF",
            border_dark="#D2D2D7",
            accent="#0071E3",
        )
        default_metrics = ThemeMetricsConfig(
            window_width=780,
            window_height=560,
            sidebar_width=164,
            padding=14,
            button_height=30,
        )
        default_typography = _default_typography("modern")
    else:
        default_colors = ThemeColorsConfig()
        default_metrics = ThemeMetricsConfig()
        default_typography = _default_typography("classic")

    assets_data = data.get("assets", {})
    colors_data = data.get("colors", {})
    metrics_data = data.get("metrics", {})
    typography_data = data.get("typography", {})

    assets = ThemeAssetsConfig(
        sidebar_image_path=assets_data.get("sidebar_image_path", default_assets.sidebar_image_path),
        header_image_path=assets_data.get("header_image_path", default_assets.header_image_path),
    )
    colors = ThemeColorsConfig(
        window_bg=colors_data.get("window_bg", default_colors.window_bg),
        panel_bg=colors_data.get("panel_bg", default_colors.panel_bg),
        text_primary=colors_data.get("text_primary", default_colors.text_primary),
        border_light=colors_data.get("border_light", default_colors.border_light),
        border_dark=colors_data.get("border_dark", default_colors.border_dark),
        accent=colors_data.get("accent", default_colors.accent),
    )
    metrics = ThemeMetricsConfig(
        window_width=metrics_data.get("window_width", default_metrics.window_width),
        window_height=metrics_data.get("window_height", default_metrics.window_height),
        sidebar_width=metrics_data.get("sidebar_width", default_metrics.sidebar_width),
        padding=metrics_data.get("padding", default_metrics.padding),
        button_height=metrics_data.get("button_height", default_metrics.button_height),
    )
    legacy_keys = [key for key in ("font_name", "base_size", "title_size") if key in typography_data]
    fonts_data = typography_data.get("fonts")
    presets_data = typography_data.get("presets")
    default_preset = typography_data.get("default_preset", default_typography.default_preset)

    fonts: list[ThemeFontCatalogEntry]
    if fonts_data is None:
        fonts = list(default_typography.fonts)
    else:
        fonts = [
            ThemeFontCatalogEntry(
                font_family=str(item.get("font_family", "")),
                font_ttf_path=item.get("font_ttf_path"),
            )
            for item in fonts_data
            if isinstance(item, dict)
        ]

    presets: dict[str, ThemeTypographyPreset]
    if presets_data is None:
        presets = dict(default_typography.presets)
    else:
        parsed_presets: dict[str, ThemeTypographyPreset] = {}
        for preset_name, preset_value in presets_data.items():
            if not isinstance(preset_value, dict):
                continue
            title_entries = [
                ThemeTypographyRoleEntry(
                    font_family=str(entry.get("font_family", "")),
                    font_size=int(entry.get("font_size", 0)),
                )
                for entry in preset_value.get("title", [])
                if isinstance(entry, dict)
            ]
            text_entries = [
                ThemeTypographyRoleEntry(
                    font_family=str(entry.get("font_family", "")),
                    font_size=int(entry.get("font_size", 0)),
                )
                for entry in preset_value.get("text", [])
                if isinstance(entry, dict)
            ]
            parsed_presets[str(preset_name)] = ThemeTypographyPreset(title=title_entries, text=text_entries)
        presets = parsed_presets

    typography = ThemeTypographyConfig(
        fonts=fonts,
        default_preset=default_preset,
        presets=presets,
        legacy_keys=legacy_keys,
    )
    return ThemeConfig(
        style=style,
        assets=assets,
        colors=colors,
        metrics=metrics,
        typography=typography,
    )



def installer_config_from_dict(data: dict[str, Any], source_root: Path | None = None) -> InstallerConfig:
    branding = data["branding"]
    return InstallerConfig(
        branding=BrandingConfig(
            product_name=branding["productName"],
            publisher=branding["publisher"],
            version=branding["version"],
            logo_path=branding.get("logoPath"),
            window_icon_path=branding.get("windowIconPath"),
        ),
        product_id=data.get("product_id")
        or data.get("productId")
        or data["branding"]["productName"].lower().replace(" ", "-"),
        install_scope=data.get("install_scope", "ask"),
        steps=[_step_from_dict(step) for step in data.get("steps", [])],
        actions=[_action_from_dict(action) for action in data.get("actions", [])],
        features=[_feature_from_dict(feature) for feature in data.get("features", [])],
        windows=dict(data.get("windows", {})),
        macos=dict(data.get("macos", {})),
        unix=dict(data.get("unix", {})),
        shortcut=ShortcutSettings(**data.get("shortcut", {})),
        upgrade=UpgradeSettings(**data.get("upgrade", {})),
        uninstall=UninstallSettings(
            enabled=bool(data.get("uninstall", {}).get("enabled", True)),
            modified_file_policy=str(data.get("uninstall", {}).get("modified_file_policy", "prompt")),
            unix=UninstallUnixSettings(
                create_symlink=bool((data.get("uninstall", {}).get("unix", {}) or {}).get("create_symlink", False)),
                user_link_path=(data.get("uninstall", {}).get("unix", {}) or {}).get("user_link_path"),
                system_link_path=(data.get("uninstall", {}).get("unix", {}) or {}).get("system_link_path"),
            ),
        ),
        hooks=dict(data.get("hooks", {})),
        theme=_theme_from_dict(data.get("theme", {})),
        source_root=source_root or Path.cwd(),
    )
