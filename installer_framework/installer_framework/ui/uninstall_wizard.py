"""Simple GUI uninstaller wizard for Windows packaging."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from installer_framework.engine.manifest import load_json
from installer_framework.engine.uninstall_runner import UninstallOptions, UninstallResult, UninstallRunner


class UninstallWizard(QMainWindow):
    """Single-window uninstaller UI with confirm -> progress -> complete behavior."""

    def __init__(
        self,
        manifest_file: Path,
        *,
        delete_modified: bool = False,
        modified_file_policy: str = "prompt",
    ) -> None:
        super().__init__()
        self.manifest_file = manifest_file
        self.modified_file_policy = modified_file_policy

        payload = load_json(manifest_file, default={})
        self.product_name = str(payload.get("product_name") or "Application")
        self.install_dir = str(payload.get("install_dir") or manifest_file.parent.parent)
        self._result: UninstallResult | None = None

        self.setWindowTitle(f"Uninstall {self.product_name}")
        self.setMinimumSize(640, 420)

        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        self.title_label = QLabel(f"Uninstall {self.product_name}")
        self.title_label.setStyleSheet("font-size: 20px; font-weight: 600;")
        self.message_label = QLabel(
            "This will remove installed files tracked by the manifest. "
            "Unknown files are kept unless they are tracked artifacts."
        )
        self.message_label.setWordWrap(True)

        self.delete_modified_checkbox = QCheckBox("Delete files modified after install")
        self.delete_modified_checkbox.setChecked(delete_modified)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        self.uninstall_btn = QPushButton("Uninstall")
        self.cancel_btn = QPushButton("Cancel")
        self.close_btn = QPushButton("Close")
        self.close_btn.setVisible(False)

        self.uninstall_btn.clicked.connect(self.start_uninstall)
        self.cancel_btn.clicked.connect(self.close)
        self.close_btn.clicked.connect(self.close)

        buttons.addWidget(self.uninstall_btn)
        buttons.addWidget(self.cancel_btn)
        buttons.addWidget(self.close_btn)

        layout.addWidget(self.title_label)
        layout.addWidget(self.message_label)
        layout.addWidget(self.delete_modified_checkbox)
        layout.addWidget(self.progress)
        layout.addWidget(self.log_view, 1)
        layout.addLayout(buttons)

        self._append_log(f"Manifest: {self.manifest_file}")
        self._append_log(f"Install directory: {self.install_dir}")

    def _append_log(self, message: str) -> None:
        self.log_view.appendPlainText(message)
        QApplication.processEvents()

    def _set_progress(self, value: int, message: str) -> None:
        self.progress.setValue(value)
        self._append_log(f"[{value:03d}%] {message}")

    def _prompt_modified(self, path: Path, operation: str) -> str:
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle("Modified file detected")
        box.setText(
            "A tracked file was modified after installation.\n\n"
            f"File: {path}\nOperation: {operation}\n\n"
            "Choose how to continue."
        )
        delete_btn = box.addButton("Delete", QMessageBox.ButtonRole.AcceptRole)
        skip_btn = box.addButton("Skip", QMessageBox.ButtonRole.ActionRole)
        abort_btn = box.addButton("Abort", QMessageBox.ButtonRole.RejectRole)
        box.exec()
        clicked = box.clickedButton()
        if clicked is delete_btn:
            return "delete"
        if clicked is abort_btn:
            return "abort"
        return "skip"

    def _finish(self, result: UninstallResult) -> None:
        self._result = result
        self.uninstall_btn.setVisible(False)
        self.cancel_btn.setVisible(False)
        self.close_btn.setVisible(True)

        if result.success:
            self.message_label.setText("Uninstall completed successfully.")
        elif result.cancelled:
            self.message_label.setText("Uninstall cancelled.")
        else:
            self.message_label.setText("Uninstall completed with errors. See log for details.")

    def start_uninstall(self) -> None:
        if not self.manifest_file.exists():
            QMessageBox.critical(self, "Manifest not found", f"Manifest not found:\n{self.manifest_file}")
            return

        self.uninstall_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)

        options = UninstallOptions(
            silent=False,
            delete_modified=self.delete_modified_checkbox.isChecked(),
            modified_file_policy=self.modified_file_policy,
        )
        runner = UninstallRunner(self.manifest_file, options=options)
        prompt_cb = self._prompt_modified if self.modified_file_policy == "prompt" else None

        result = runner.run(
            progress_callback=self._set_progress,
            log_callback=self._append_log,
            prompt_callback=prompt_cb,
        )

        if result.errors:
            for error in result.errors:
                self._append_log(f"ERROR: {error}")

        self._finish(result)

    @property
    def result(self) -> UninstallResult | None:
        return self._result
