"""Wizard container and navigation orchestration."""

from __future__ import annotations

import sys

from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget

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


class Wizard(BoxLayout):
    """Top-level wizard layout with classic branding, content, and navigation."""

    def __init__(self, config: InstallerConfig, ctx: InstallerContext, **kwargs) -> None:
        super().__init__(orientation="vertical", spacing=0, padding=0, **kwargs)
        self.config = config
        self.ctx = ctx
        self.theme: UITheme = get_active_theme() or UITheme(config=config.theme, source_root=config.source_root)
        self.step_cache: dict[str, Widget] = {}
        self.visible_steps: list[StepConfig] = []
        self.current_index = 0

        self._build_shell()
        self.refresh_visible_steps()
        self.show_step(0)

    def _build_shell(self) -> None:
        metrics = self.theme.config.metrics
        pad = dp(metrics.padding)

        self.root_panel = ClassicPanel(
            theme=self.theme,
            orientation="horizontal",
            fill_color=self.theme.window_bg,
            border=True,
            spacing=0,
            padding=0,
        )

        sidebar_source = self.theme.sidebar_image
        sidebar_path = str(sidebar_source) if sidebar_source else None
        self.sidebar = ClassicSidebar(
            theme=self.theme,
            title=self.config.branding.product_name,
            subtitle=f"Version {self.config.branding.version}\n{self.config.branding.publisher}",
            image_path=sidebar_path,
            size_hint_x=None,
            width=dp(metrics.sidebar_width),
        )
        self.root_panel.add_widget(self.sidebar)

        self.main_column = BoxLayout(orientation="vertical", spacing=0)

        header_image = self.theme.header_image
        self.header_host = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(82))
        self.header = ClassicHeader(
            theme=self.theme,
            title=self.config.branding.product_name,
            description=f"Version {self.config.branding.version} | {self.config.branding.publisher}",
            image_path=str(header_image) if header_image else None,
        )
        self.header_host.add_widget(self.header)
        self.main_column.add_widget(self.header_host)

        self.content_panel = ClassicPanel(
            theme=self.theme,
            orientation="vertical",
            fill_color=self.theme.content_bg,
            border=True,
            padding=(pad, pad),
            spacing=dp(8),
        )
        self.content = BoxLayout(orientation="vertical")
        self.content_panel.add_widget(self.content)
        self.main_column.add_widget(self.content_panel)

        self.main_column.add_widget(ClassicSeparator(theme=self.theme))
        self._build_nav()

        self.root_panel.add_widget(self.main_column)
        self.add_widget(self.root_panel)

    def _build_nav(self) -> None:
        h = dp(self.theme.config.metrics.button_height + 14)
        nav = BoxLayout(orientation="horizontal", size_hint_y=None, height=h, spacing=dp(6), padding=(dp(10), dp(8)))
        nav.add_widget(Widget())

        self.back_btn = ClassicButton(theme=self.theme, text="< Back", size_hint_x=None, width=dp(95), size_hint_y=None, height=dp(self.theme.config.metrics.button_height))
        self.next_btn = ClassicButton(theme=self.theme, text="Next >", default_action=True, size_hint_x=None, width=dp(95), size_hint_y=None, height=dp(self.theme.config.metrics.button_height))
        self.install_btn = ClassicButton(theme=self.theme, text="Install", default_action=True, size_hint_x=None, width=dp(95), size_hint_y=None, height=dp(self.theme.config.metrics.button_height))
        self.cancel_btn = ClassicButton(theme=self.theme, text="Cancel", size_hint_x=None, width=dp(95), size_hint_y=None, height=dp(self.theme.config.metrics.button_height))

        self.back_btn.bind(on_release=lambda *_: self.go_back())
        self.next_btn.bind(on_release=lambda *_: self.go_next())
        self.install_btn.bind(on_release=lambda *_: self.begin_install())
        self.cancel_btn.bind(on_release=lambda *_: self.cancel_install("Cancelled by user"))

        nav.add_widget(self.back_btn)
        nav.add_widget(self.next_btn)
        nav.add_widget(self.install_btn)
        nav.add_widget(self.cancel_btn)
        self.main_column.add_widget(nav)

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

    def show_step(self, index: int) -> None:
        self.refresh_visible_steps()
        if not self.visible_steps:
            raise RuntimeError("No visible wizard steps")

        self.current_index = max(0, min(index, len(self.visible_steps) - 1))
        self.content.clear_widgets()

        step_widget, step_cfg = self._current_step()
        step_widget.apply_state()
        step_widget.on_show()
        self.content.add_widget(step_widget)

        header_image = self.theme.header_image
        self.header = ClassicHeader(
            theme=self.theme,
            title=step_cfg.title,
            description=step_cfg.description or f"Setup for {self.config.branding.product_name}",
            image_path=str(header_image) if header_image else None,
        )
        self.header_host.clear_widgets()
        self.header_host.add_widget(self.header)

        self._update_nav(step_cfg)

    def _set_visible(self, widget, visible: bool) -> None:
        widget.disabled = not visible
        widget.opacity = 1 if visible else 0

    def _update_nav(self, step_cfg: StepConfig) -> None:
        self.back_btn.disabled = self.current_index == 0 or step_cfg.type == "install"
        is_ready = step_cfg.type == "ready"
        is_install = step_cfg.type == "install"
        is_finish = step_cfg.type == "finish"

        self.install_btn.text = "Install"
        self._set_visible(self.install_btn, is_ready)

        self.next_btn.text = "Finish" if is_finish else "Next >"
        self.next_btn.disabled = is_install or is_ready
        self._set_visible(self.next_btn, not is_ready)

        if is_finish:
            self.next_btn.disabled = False
        if is_install:
            self.next_btn.disabled = True
            self.back_btn.disabled = True

    def _commit_step(self) -> bool:
        step_widget, step_cfg = self._current_step()
        valid, error = step_widget.validate()
        if not valid:
            show_message_dialog("error", "Validation error", error or "Please correct this step")
            return False

        data = step_widget.get_data()
        self.ctx.state.answers.update({k: v for k, v in data.items() if k not in {"selected_features", "install_scope", "install_dir"}})
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
            App.get_running_app().stop()
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
            App.get_running_app().stop()

        show_confirm_dialog("Cancel installation", "Are you sure you want to cancel setup?", _close)

    def _ensure_scope_privileges(self) -> bool:
        if self.ctx.state.install_scope != "system" or self.ctx.is_elevated:
            return True

        if self.ctx.env.is_windows:
            if self.config.windows.get("allow_uac_elevation", False):
                relaunched = relaunch_as_admin_windows(sys.argv[1:])
                if relaunched:
                    App.get_running_app().stop()
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
                App.get_running_app().stop()
                return False

        show_message_dialog(
            "error",
            "Root privileges required",
            "System-wide install requires root/admin privileges. Re-run with sudo.",
        )
        return False
