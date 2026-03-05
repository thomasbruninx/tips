"""Install directory selection step."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import QFileDialog, QHBoxLayout, QLabel, QLineEdit, QWidget

from installer_framework.app.paths import default_install_dir
from installer_framework.config.validation import validate_field_value
from installer_framework.ui.step_base import StepWidget
from installer_framework.ui.widgets.classic import ClassicButton, ClassicGroupBox
from installer_framework.util.fs import ensure_dir, is_writable


class DirectoryStep(StepWidget):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.path_input = QLineEdit()
        self.path_input.setStyleSheet(
            f"QLineEdit {{ background-color: {self.theme.panel_bg}; color: {self.theme.text_primary}; border: 1px solid {self.theme.border_dark}; padding: 2px 4px; }}"
        )

        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(8)
        browse = ClassicButton(theme=self.theme, text="Browse...")
        browse.setFixedWidth(110)
        browse.clicked.connect(self.open_picker)
        row_layout.addWidget(self.path_input, 1)
        row_layout.addWidget(browse)

        self.error = QLabel("")
        self.error.setStyleSheet("color: #B00020;")

        group = ClassicGroupBox(theme=self.theme, title="Installation Directory")
        group.content_layout.addWidget(self.description_label(height=40))
        group.content_layout.addWidget(row)
        group.content_layout.addWidget(self.error)

        self.main_layout.addWidget(group)
        self.main_layout.addStretch(1)

    def on_show(self) -> None:
        if self.ctx.state.install_dir:
            self.path_input.setText(self.ctx.state.install_dir)
            return
        default = default_install_dir(
            self.ctx.config.branding.product_name,
            self.ctx.state.install_scope,
            prefer_program_files_x86=bool(self.ctx.config.windows.get("prefer_program_files_x86", False)),
        )
        self.path_input.setText(str(default))

    def open_picker(self) -> None:
        selected = QFileDialog.getExistingDirectory(self, "Select installation directory", self.path_input.text().strip())
        if selected:
            self.path_input.setText(selected)

    def get_data(self) -> dict:
        return {"install_dir": self.path_input.text().strip()}

    def validate(self) -> tuple[bool, str | None]:
        raw = self.path_input.text().strip()
        self.error.setText("")

        if not raw:
            self.error.setText("Installation path is required")
            return False, self.error.text()
        path = Path(raw)

        if self.step_config.fields:
            ok, message = validate_field_value(self.step_config.fields[0], raw)
            if not ok:
                self.error.setText(message or "Invalid directory")
                return False, self.error.text()

        try:
            ensure_dir(path)
        except Exception as exc:
            self.error.setText(f"Unable to create directory: {exc}")
            return False, self.error.text()

        if not is_writable(path):
            self.error.setText("Directory is not writable")
            return False, self.error.text()

        return True, None
