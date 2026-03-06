"""License agreement step."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import QPlainTextEdit

from installer_framework.ui.step_base import StepWidget


class LicenseStep(StepWidget):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.agree_row = self.widget_factory.create_checkbox_row(text="I agree to the license terms", active=False)

        license_text = self._load_license_text()
        self.license_view = QPlainTextEdit(license_text)
        self.license_view.setReadOnly(True)
        self.license_view.setStyleSheet(
            f"QPlainTextEdit {{ background-color: {self.theme.panel_bg}; color: {self.theme.text_primary}; border: 1px solid {self.theme.border_dark}; }}"
        )

        group = self.widget_factory.create_group_box(title="License Agreement")
        group.content_layout.addWidget(self.license_view, 1)

        self.main_layout.addWidget(group, 1)
        self.main_layout.addWidget(self.agree_row)

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
