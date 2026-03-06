"""Finish step."""

from __future__ import annotations

import json

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel

from installer_framework.ui.step_base import StepWidget


class FinishStep(StepWidget):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        group = self.widget_factory.create_group_box(title="Setup Complete")
        self.summary = QLabel("")
        self.summary.setWordWrap(True)
        self.summary.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.summary.setStyleSheet(f"color: {self.theme.text_primary};")
        group.content_layout.addWidget(self.summary)
        self.main_layout.addWidget(group)

    def on_show(self) -> None:
        result = self.ctx.state.result_summary
        if not result:
            self.summary.setText("Installation has not run yet.")
            return

        success = result.get("success", False)
        cancelled = result.get("cancelled", False)
        header = "Installation completed successfully" if success else "Installation incomplete"
        if cancelled:
            header = "Installation cancelled"

        details = {
            "install_dir": result.get("install_dir"),
            "scope": result.get("scope"),
            "features": result.get("features"),
            "error": result.get("error"),
        }
        self.summary.setText(f"{header}\n\n{json.dumps(details, indent=2)}\n\nClick Finish to close Setup.")
