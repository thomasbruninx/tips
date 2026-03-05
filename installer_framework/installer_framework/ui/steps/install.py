"""Install execution step."""

from __future__ import annotations

from PyQt6.QtCore import QObject, Qt, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import QLabel, QProgressBar

from installer_framework.engine.runner import ActionRunner
from installer_framework.ui.step_base import StepWidget
from installer_framework.ui.widgets.classic import ClassicGroupBox
from installer_framework.ui.widgets.dialogs import show_message_dialog
from installer_framework.ui.widgets.log_pane import LogPane


class InstallWorker(QObject):
    progress = pyqtSignal(int, str)
    log = pyqtSignal(str)
    message = pyqtSignal(str, str, str)
    finished = pyqtSignal(object)

    def __init__(self, ctx) -> None:
        super().__init__()
        self.ctx = ctx

    @pyqtSlot()
    def run(self) -> None:
        runner = ActionRunner(self.ctx.config.actions)

        result = runner.run(
            self.ctx,
            progress_callback=lambda value, message: self.progress.emit(value, message),
            log_callback=lambda message: self.log.emit(message),
            message_callback=lambda level, title, message: self.message.emit(level, title, message),
        )

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
        self.finished.emit(result)


class InstallStep(StepWidget):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.started = False
        self._thread: QThread | None = None
        self._worker: InstallWorker | None = None

        group = ClassicGroupBox(theme=self.theme, title="Installing")
        self.progress_label = QLabel("Preparing installation...")
        self.progress_label.setStyleSheet(f"color: {self.theme.text_primary};")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)

        self.log_pane = LogPane()

        group.content_layout.addWidget(self.progress_label)
        group.content_layout.addWidget(self.progress)
        group.content_layout.addWidget(self.log_pane)

        self.main_layout.addWidget(group)

    def on_show(self) -> None:
        if not self.started:
            self.started = True
            self.start_install()

    def start_install(self) -> None:
        self._thread = QThread(self)
        self._worker = InstallWorker(self.ctx)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._set_progress)
        self._worker.log.connect(self.log_pane.append)
        self._worker.message.connect(show_message_dialog)
        self._worker.finished.connect(self._on_finished)

        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)

        self._thread.start()

    @pyqtSlot(int, str)
    def _set_progress(self, value: int, message: str) -> None:
        self.progress.setValue(value)
        self.progress_label.setText(f"{value}% - {message}")

    @pyqtSlot(object)
    def _on_finished(self, result) -> None:
        self.wizard.on_install_finished(result)
