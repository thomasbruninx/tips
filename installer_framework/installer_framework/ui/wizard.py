"""Wizard container and navigation orchestration."""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication, QHBoxLayout, QMainWindow, QVBoxLayout, QWidget

from installer_framework.app.paths import default_install_dir
from installer_framework.config.conditions import evaluate_condition
from installer_framework.config.models import InstallerConfig, StepConfig
from installer_framework.engine.context import InstallerContext
from installer_framework.engine.runner import ActionResult
from installer_framework.ui.step_factory import StepFactory
from installer_framework.ui.theme import UITheme, get_active_theme
from installer_framework.ui.widgets.classic import (
    ClassicButton,
    ClassicHeader,
    ClassicPanel,
    ClassicSeparator,
    ClassicSidebar,
)
from installer_framework.ui.widgets.dialogs import show_confirm_dialog, show_message_dialog
from installer_framework.util.privileges import relaunch_as_admin_windows, relaunch_with_sudo_unix


class Wizard(QMainWindow):
    """Top-level wizard window with classic branding, content, and navigation."""

    def __init__(self, config: InstallerConfig, ctx: InstallerContext, **kwargs) -> None:
        super().__init__(**kwargs)
        self.config = config
        self.ctx = ctx
        self.theme: UITheme = get_active_theme() or UITheme(config=config.theme, source_root=config.source_root)
        self.step_cache: dict[str, QWidget] = {}
        self.visible_steps: list[StepConfig] = []
        self.current_index = 0

        self._build_shell()
        self.refresh_visible_steps()
        self.show_step(0)

    def _build_shell(self) -> None:
        metrics = self.theme.config.metrics

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        sidebar_source = self.theme.sidebar_image
        sidebar_path = str(sidebar_source) if sidebar_source else None
        self.sidebar = ClassicSidebar(
            theme=self.theme,
            title=self.config.branding.product_name,
            subtitle=f"Version {self.config.branding.version}\n{self.config.branding.publisher}",
            image_path=sidebar_path,
        )
        self.sidebar.setFixedWidth(metrics.sidebar_width)

        self.main_column = QWidget()
        main_layout = QVBoxLayout(self.main_column)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.header_host = QWidget()
        self.header_layout = QVBoxLayout(self.header_host)
        self.header_layout.setContentsMargins(0, 0, 0, 0)
        self.header_layout.setSpacing(0)
        self.header_host.setFixedHeight(82)

        self.content_panel = ClassicPanel(theme=self.theme)
        self.content_panel.setObjectName("WizardContentPanel")
        self.content_panel.setStyleSheet(
            f"QFrame#WizardContentPanel {{ background-color: {self.theme.content_bg}; border: 1px solid {self.theme.border_dark}; }}"
        )
        content_layout = QVBoxLayout(self.content_panel)
        content_layout.setContentsMargins(metrics.padding, metrics.padding, metrics.padding, metrics.padding)
        content_layout.setSpacing(8)
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        content_layout.addWidget(self.content)

        self.nav_widget = QWidget()
        nav_layout = QHBoxLayout(self.nav_widget)
        nav_layout.setContentsMargins(10, 8, 10, 8)
        nav_layout.setSpacing(6)

        self.back_btn = ClassicButton(theme=self.theme, text="< Back")
        self.next_btn = ClassicButton(theme=self.theme, text="Next >", default_action=True)
        self.install_btn = ClassicButton(theme=self.theme, text="Install", default_action=True)
        self.cancel_btn = ClassicButton(theme=self.theme, text="Cancel")

        btn_width = 95
        for btn in (self.back_btn, self.next_btn, self.install_btn, self.cancel_btn):
            btn.setFixedWidth(btn_width)
            btn.setFixedHeight(metrics.button_height)

        self.back_btn.clicked.connect(self.go_back)
        self.next_btn.clicked.connect(self.go_next)
        self.install_btn.clicked.connect(self.begin_install)
        self.cancel_btn.clicked.connect(lambda: self.cancel_install("Cancelled by user"))

        nav_layout.addStretch(1)
        nav_layout.addWidget(self.back_btn)
        nav_layout.addWidget(self.next_btn)
        nav_layout.addWidget(self.install_btn)
        nav_layout.addWidget(self.cancel_btn)

        main_layout.addWidget(self.header_host)
        main_layout.addWidget(self.content_panel, 1)
        main_layout.addWidget(ClassicSeparator(theme=self.theme))
        main_layout.addWidget(self.nav_widget)

        root.addWidget(self.sidebar)
        root.addWidget(self.main_column, 1)

        self.setStyleSheet(f"QMainWindow {{ background-color: {self.theme.window_bg}; }}")

    def refresh_visible_steps(self) -> None:
        visible: list[StepConfig] = []
        for step in self.config.steps:
            if step.type == "scope" and self.config.install_scope != "ask":
                continue
            if evaluate_condition(step.show_if, self.ctx.state):
                visible.append(step)
        self.visible_steps = visible

    def _current_step(self):
        step_cfg = self.visible_steps[self.current_index]
        if step_cfg.id not in self.step_cache:
            self.step_cache[step_cfg.id] = StepFactory.create(step_cfg, self.ctx, self)
        return self.step_cache[step_cfg.id], step_cfg

    def _clear_layout(self, layout: QVBoxLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)

    def _set_header(self, step_cfg: StepConfig) -> None:
        self._clear_layout(self.header_layout)
        header_image = self.theme.header_image
        header = ClassicHeader(
            theme=self.theme,
            title=step_cfg.title,
            description=step_cfg.description or f"Setup for {self.config.branding.product_name}",
            image_path=str(header_image) if header_image else None,
        )
        self.header_layout.addWidget(header)

    def show_step(self, index: int) -> None:
        self.refresh_visible_steps()
        if not self.visible_steps:
            raise RuntimeError("No visible wizard steps")

        self.current_index = max(0, min(index, len(self.visible_steps) - 1))
        self._clear_layout(self.content_layout)

        step_widget, step_cfg = self._current_step()
        step_widget.apply_state()
        step_widget.on_show()
        self.content_layout.addWidget(step_widget)

        self._set_header(step_cfg)
        self._update_nav(step_cfg)

    def _set_visible(self, widget, visible: bool) -> None:
        widget.setVisible(visible)
        widget.setEnabled(visible)

    def _update_nav(self, step_cfg: StepConfig) -> None:
        self.back_btn.setDisabled(self.current_index == 0 or step_cfg.type == "install")
        is_ready = step_cfg.type == "ready"
        is_install = step_cfg.type == "install"
        is_finish = step_cfg.type == "finish"

        self.install_btn.setText("Install")
        self._set_visible(self.install_btn, is_ready)

        self.next_btn.setText("Finish" if is_finish else "Next >")
        self.next_btn.setDisabled(is_install or is_ready)
        self._set_visible(self.next_btn, not is_ready)

        if is_finish:
            self.next_btn.setDisabled(False)
        if is_install:
            self.next_btn.setDisabled(True)
            self.back_btn.setDisabled(True)

    def _commit_step(self) -> bool:
        step_widget, step_cfg = self._current_step()
        valid, error = step_widget.validate()
        if not valid:
            show_message_dialog("error", "Validation error", error or "Please correct this step")
            return False

        data = step_widget.get_data()
        self.ctx.state.answers.update(
            {k: v for k, v in data.items() if k not in {"selected_features", "install_scope", "install_dir"}}
        )
        if "selected_features" in data:
            self.ctx.state.selected_features = list(data["selected_features"])
        if "install_scope" in data:
            previous_scope = self.ctx.state.install_scope
            self.ctx.state.install_scope = data["install_scope"]
            if previous_scope != self.ctx.state.install_scope:
                self.ctx.state.install_dir = str(
                    default_install_dir(
                        self.config.branding.product_name,
                        self.ctx.state.install_scope,
                        prefer_program_files_x86=bool(self.config.windows.get("prefer_program_files_x86", False)),
                    )
                )
        if "install_dir" in data:
            self.ctx.state.install_dir = data["install_dir"]

        self.ctx.save_resume()

        next_step_id = step_cfg.navigation.get("next") if step_cfg.navigation else None
        if next_step_id:
            for idx, step in enumerate(self.visible_steps):
                if step.id == next_step_id:
                    self.show_step(idx)
                    return False
        return True

    def go_next(self) -> None:
        _, step_cfg = self._current_step()
        if step_cfg.type == "finish":
            self.close()
            QApplication.instance().quit()
            return

        if not self._commit_step():
            return
        self.show_step(self.current_index + 1)

    def go_back(self) -> None:
        self.show_step(self.current_index - 1)

    def begin_install(self) -> None:
        if not self._commit_step():
            return
        if not self._ensure_scope_privileges():
            return
        install_index = self._index_of_type("install")
        self.show_step(install_index)

    def on_install_finished(self, result: ActionResult) -> None:
        if result.success:
            show_message_dialog("info", "Install complete", "Installation completed successfully.")
            self.ctx.clear_resume()
        elif result.cancelled:
            show_message_dialog("warn", "Install cancelled", "Installation was cancelled.")
        else:
            show_message_dialog("error", "Install failed", result.error or "Unknown error")

        finish_idx = self._index_of_type("finish")
        self.show_step(finish_idx)

    def _index_of_type(self, step_type: str) -> int:
        for idx, step in enumerate(self.visible_steps):
            if step.type == step_type:
                return idx
        raise ValueError(f"Missing required step type: {step_type}")

    def cancel_install(self, reason: str) -> None:
        _, step_cfg = self._current_step()
        if step_cfg.type == "install":
            self.ctx.cancel()
            show_message_dialog("warn", "Cancelling", "Cancellation requested. Waiting for current action to stop.")
            return

        def _close(confirm: bool) -> None:
            if not confirm:
                return
            self.ctx.cancel()
            show_message_dialog("warn", "Installer closed", reason)
            self.close()
            QApplication.instance().quit()

        show_confirm_dialog("Cancel installation", "Are you sure you want to cancel setup?", _close)

    def _ensure_scope_privileges(self) -> bool:
        if self.ctx.state.install_scope != "system" or self.ctx.is_elevated:
            return True

        if self.ctx.env.is_windows:
            if self.config.windows.get("allow_uac_elevation", False):
                relaunched = relaunch_as_admin_windows(sys.argv[1:])
                if relaunched:
                    self.close()
                    QApplication.instance().quit()
                    return False
            show_message_dialog(
                "error",
                "Administrator privileges required",
                "System-wide install needs elevation. Please re-run this installer as Administrator.",
            )
            return False

        if self.config.unix.get("allow_sudo_relaunch", False):
            relaunched = relaunch_with_sudo_unix(sys.argv[1:])
            if relaunched:
                self.close()
                QApplication.instance().quit()
                return False

        show_message_dialog(
            "error",
            "Root privileges required",
            "System-wide install requires root/admin privileges. Re-run with sudo.",
        )
        return False
