"""License agreement step."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import QHBoxLayout, QPlainTextEdit, QWidget

from installer_framework.ui.step_base import StepWidget
from installer_framework.ui.widgets.classic import ClassicButton, ClassicCheckboxRow, ClassicGroupBox


class LicenseStep(StepWidget):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.agree_row = ClassicCheckboxRow(theme=self.theme, text="I agree to the license terms", active=False)

        license_text = self._load_license_text()
        self.license_view = QPlainTextEdit(license_text)
        self.license_view.setReadOnly(True)
        self.license_view.setStyleSheet(
            f"QPlainTextEdit {{ background-color: {self.theme.panel_bg}; color: {self.theme.text_primary}; border: 1px solid {self.theme.border_dark}; }}"
        )

        group = ClassicGroupBox(theme=self.theme, title="License Agreement")
        group.content_layout.addWidget(self.license_view, 1)

        button_row = QWidget()
        button_layout = QHBoxLayout(button_row)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.addStretch(1)
        disagree = ClassicButton(theme=self.theme, text="Disagree")
        disagree.setFixedWidth(100)
        disagree.clicked.connect(lambda: self.wizard.cancel_install("License not accepted"))
        button_layout.addWidget(disagree)

        self.main_layout.addWidget(group, 1)
        self.main_layout.addWidget(self.agree_row)
        self.main_layout.addWidget(button_row)

    def _load_license_text(self) -> str:
        candidate = self.step_config.license_path or ""
        if not candidate:
            return "No license configured."

        path = Path(candidate)
        if not path.is_absolute():
            path = (self.ctx.config.source_root / candidate).resolve()

        if not path.exists():
            return f"License file not found: {path}"
        return path.read_text(encoding="utf-8", errors="replace")

    def get_data(self) -> dict:
        return {"license_agree": self.agree_row.checkbox.isChecked()}

    def apply_state(self) -> None:
        self.agree_row.checkbox.setChecked(bool(self.ctx.state.answers.get("license_agree", False)))

    def validate(self) -> tuple[bool, str | None]:
        if not self.agree_row.checkbox.isChecked():
            return False, "You must accept the license to continue."
        return True, None
