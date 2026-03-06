"""Ready step with summary before install."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel

from installer_framework.ui.step_base import StepWidget


class ReadyStep(StepWidget):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        group = self.widget_factory.create_group_box(title="Ready to Install")
        self.summary = QLabel("")
        self.summary.setWordWrap(True)
        self.summary.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.summary.setStyleSheet(f"color: {self.theme.text_primary};")

        group.content_layout.addWidget(self.summary)
        self.main_layout.addWidget(group)

    def on_show(self) -> None:
        features = ", ".join(self.ctx.state.selected_features) if self.ctx.state.selected_features else "(none)"
        answers = "\n".join(f"- {k}: {v}" for k, v in self.ctx.state.answers.items() if "password" not in k.lower())
        self.summary.setText(
            "Setup is ready to begin.\n\n"
            f"Install scope: {self.ctx.state.install_scope}\n"
            f"Target folder: {self.ctx.state.install_dir}\n"
            f"Selected features: {features}\n\n"
            f"Options:\n{answers or '- (none)'}\n\n"
            "Click Install to start copying files and creating shortcuts."
        )
