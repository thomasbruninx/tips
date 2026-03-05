"""Ready step with summary before install."""

from __future__ import annotations

from kivy.uix.label import Label

from installer_framework.ui.step_base import StepWidget
from installer_framework.ui.widgets.classic import ClassicGroupBox


class ReadyStep(StepWidget):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        group = ClassicGroupBox(theme=self.theme, title="Ready to Install")
        self.summary = Label(text="", color=self.theme.text_primary, halign="left", valign="top")
        self.summary.bind(size=lambda instance, value: setattr(instance, "text_size", value))
        if self.theme.font_name:
            self.summary.font_name = self.theme.font_name

        group.content.add_widget(self.summary)
        self.add_widget(group)

    def on_show(self) -> None:
        features = ", ".join(self.ctx.state.selected_features) if self.ctx.state.selected_features else "(none)"
        answers = "\n".join(f"- {k}: {v}" for k, v in self.ctx.state.answers.items() if "password" not in k.lower())
        self.summary.text = (
            f"Setup is ready to begin.\n\n"
            f"Install scope: {self.ctx.state.install_scope}\n"
            f"Target folder: {self.ctx.state.install_dir}\n"
            f"Selected features: {features}\n\n"
            f"Options:\n{answers or '- (none)'}\n\n"
            "Click Install to start copying files and creating shortcuts."
        )
