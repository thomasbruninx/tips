"""Install execution step."""

from __future__ import annotations

from threading import Thread

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar

from installer_framework.engine.runner import ActionRunner
from installer_framework.ui.step_base import StepWidget
from installer_framework.ui.widgets.classic import ClassicGroupBox
from installer_framework.ui.widgets.dialogs import show_message_dialog
from installer_framework.ui.widgets.log_pane import LogPane


class InstallStep(StepWidget):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.started = False

        group = ClassicGroupBox(theme=self.theme, title="Installing")
        self.progress_label = Label(text="Preparing installation...", color=self.theme.text_primary, size_hint_y=None, height=dp(24), halign="left", valign="middle")
        self.progress_label.bind(size=lambda instance, value: setattr(instance, "text_size", value))
        if self.theme.font_name:
            self.progress_label.font_name = self.theme.font_name

        self.progress = ProgressBar(max=100, value=0, size_hint_y=None, height=dp(20))
        self.log_pane = LogPane(size_hint=(1, 1))

        group.content.add_widget(self.progress_label)
        group.content.add_widget(self.progress)
        group.content.add_widget(self.log_pane)

        self.add_widget(group)

    def on_show(self) -> None:
        if not self.started:
            self.started = True
            self.start_install()

    def start_install(self) -> None:
        runner = ActionRunner(self.ctx.config.actions)

        def progress_cb(value: int, message: str) -> None:
            Clock.schedule_once(lambda *_: self._set_progress(value, message), 0)

        def log_cb(message: str) -> None:
            Clock.schedule_once(lambda *_: self.log_pane.append(message), 0)

        def message_cb(level: str, title: str, message: str) -> None:
            Clock.schedule_once(lambda *_: show_message_dialog(level, title, message), 0)

        def worker() -> None:
            result = runner.run(self.ctx, progress_cb, log_cb, message_callback=message_cb)
            self.ctx.state.result_summary = {
                "success": result.success,
                "cancelled": result.cancelled,
                "error": result.error,
                "results": result.results,
                "install_dir": self.ctx.state.install_dir,
                "scope": self.ctx.state.install_scope,
                "features": self.ctx.state.selected_features,
            }
            self.ctx.save_resume()
            Clock.schedule_once(lambda *_: self.wizard.on_install_finished(result), 0)

        Thread(target=worker, daemon=True).start()

    def _set_progress(self, value: int, message: str) -> None:
        self.progress.value = value
        self.progress_label.text = f"{value}% - {message}"
