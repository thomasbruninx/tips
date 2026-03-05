"""Finish step."""

from __future__ import annotations

import json

from kivy.uix.label import Label

from installer_framework.ui.step_base import StepWidget
from installer_framework.ui.widgets.classic import ClassicGroupBox


class FinishStep(StepWidget):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        group = ClassicGroupBox(theme=self.theme, title="Setup Complete")
        self.summary = Label(text="", color=self.theme.text_primary, halign="left", valign="top")
        self.summary.bind(size=lambda instance, value: setattr(instance, "text_size", value))
        if self.theme.font_name:
            self.summary.font_name = self.theme.font_name
        group.content.add_widget(self.summary)
        self.add_widget(group)

    def on_show(self) -> None:
        result = self.ctx.state.result_summary
        if not result:
            self.summary.text = "Installation has not run yet."
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
        self.summary.text = f"{header}\n\n{json.dumps(details, indent=2)}\n\nClick Finish to close Setup."
