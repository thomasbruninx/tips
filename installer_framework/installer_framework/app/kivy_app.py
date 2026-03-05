"""Kivy App bootstrap for the installer wizard."""

from __future__ import annotations

from pathlib import Path

from kivy.app import App
from kivy.core.window import Window

from installer_framework.app.paths import default_install_dir
from installer_framework.config.models import InstallerConfig
from installer_framework.engine.context import InstallerContext, InstallerState
from installer_framework.ui.theme import build_theme
from installer_framework.engine.upgrade import detect_existing_install
from installer_framework.ui.wizard import Wizard


class InstallerKivyApp(App):
    def __init__(self, config: InstallerConfig, resume: bool = False, **kwargs) -> None:
        super().__init__(**kwargs)
        self.installer_config = config
        initial_scope = "user" if config.install_scope == "ask" else config.install_scope
        initial_dir = str(
            default_install_dir(
                config.branding.product_name,
                initial_scope,
                prefer_program_files_x86=bool(config.windows.get("prefer_program_files_x86", False)),
            )
        )
        self.ctx = InstallerContext(
            config=config,
            state=InstallerState(
                install_scope=initial_scope,
                install_dir=initial_dir,
                selected_features=[feature.id for feature in config.features if feature.default],
            ),
        )
        self.ui_theme = build_theme(config.theme, config.source_root)
        if resume:
            self.ctx.load_resume()

    def build(self):
        self.title = self.installer_config.branding.product_name
        self._apply_window_theme()
        self._apply_icon()
        self.ctx.state.detected_upgrade = detect_existing_install(self.ctx)
        return Wizard(config=self.installer_config, ctx=self.ctx)

    def _apply_icon(self) -> None:
        icon = self.installer_config.branding.window_icon_path
        if not icon:
            return
        path = Path(icon)
        if not path.is_absolute():
            path = (self.installer_config.source_root / icon).resolve()
        if path.exists():
            try:
                Window.set_icon(str(path))
            except Exception:
                pass

    def _apply_window_theme(self) -> None:
        Window.size = self.ui_theme.window_size
        try:
            Window.minimum_size = self.ui_theme.min_window_size
        except Exception:
            Window.minimum_width = self.ui_theme.min_window_size[0]
            Window.minimum_height = self.ui_theme.min_window_size[1]
        Window.clearcolor = self.ui_theme.window_bg
