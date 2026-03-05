"""PyQt6 app bootstrap for the installer wizard."""

from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from installer_framework.app.paths import default_install_dir
from installer_framework.config.models import InstallerConfig
from installer_framework.engine.context import InstallerContext, InstallerState
from installer_framework.engine.upgrade import detect_existing_install
from installer_framework.ui.theme import build_theme, set_active_theme
from installer_framework.ui.wizard import Wizard


class InstallerQtApp:
    """Bootstrapper that owns QApplication and main wizard window."""

    def __init__(self, config: InstallerConfig, resume: bool = False) -> None:
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
        if resume:
            self.ctx.load_resume()

        self.ui_theme = build_theme(config.theme, config.source_root)
        set_active_theme(self.ui_theme)

        self.ctx.state.detected_upgrade = detect_existing_install(self.ctx)

    def run(self) -> int:
        app = QApplication.instance() or QApplication(sys.argv)
        app.setApplicationName(self.installer_config.branding.product_name)

        window = Wizard(config=self.installer_config, ctx=self.ctx)
        window.setWindowTitle(self.installer_config.branding.product_name)
        self._apply_icon(window)

        width, height = self.ui_theme.window_size
        min_width, min_height = self.ui_theme.min_window_size
        window.resize(width, height)
        window.setMinimumSize(min_width, min_height)
        window.show()

        return app.exec()

    def _apply_icon(self, window) -> None:
        icon = self.installer_config.branding.window_icon_path
        if not icon:
            return
        path = Path(icon)
        if not path.is_absolute():
            path = (self.installer_config.source_root / icon).resolve()
        if path.exists():
            window.setWindowIcon(QIcon(str(path)))
