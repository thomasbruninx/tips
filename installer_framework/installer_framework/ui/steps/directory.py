"""Install directory selection step."""

from __future__ import annotations

from pathlib import Path

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.textinput import TextInput

from installer_framework.app.paths import default_install_dir
from installer_framework.config.validation import validate_field_value
from installer_framework.ui.step_base import StepWidget
from installer_framework.ui.widgets.classic import ClassicButton, ClassicGroupBox
from installer_framework.util.fs import ensure_dir, is_writable


class DirectoryStep(StepWidget):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.path_input = TextInput(multiline=False, size_hint_y=None, height=dp(30))
        self.path_input.background_normal = ""
        self.path_input.background_active = ""
        self.path_input.background_color = self.theme.panel_bg
        self.path_input.foreground_color = self.theme.text_primary
        if self.theme.font_name:
            self.path_input.font_name = self.theme.font_name

        row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(32), spacing=dp(8))
        browse = ClassicButton(theme=self.theme, text="Browse...", size_hint_x=None, width=dp(110))
        browse.bind(on_release=lambda *_: self.open_picker())
        row.add_widget(self.path_input)
        row.add_widget(browse)

        self.error = Label(text="", color=(0.8, 0.1, 0.1, 1), size_hint_y=None, height=dp(24), halign="left", valign="middle")
        self.error.bind(size=lambda instance, value: setattr(instance, "text_size", value))
        if self.theme.font_name:
            self.error.font_name = self.theme.font_name

        group = ClassicGroupBox(theme=self.theme, title="Installation Directory")
        group.content.add_widget(self.description_label(height=40))
        group.content.add_widget(row)
        group.content.add_widget(self.error)
        self.add_widget(group)

    def on_show(self) -> None:
        if self.ctx.state.install_dir:
            self.path_input.text = self.ctx.state.install_dir
            return
        default = default_install_dir(
            self.ctx.config.branding.product_name,
            self.ctx.state.install_scope,
            prefer_program_files_x86=bool(self.ctx.config.windows.get("prefer_program_files_x86", False)),
        )
        self.path_input.text = str(default)

    def open_picker(self) -> None:
        try:
            from plyer import filechooser

            def on_selection(selection) -> None:
                if selection:
                    self.path_input.text = selection[0]

            filechooser.choose_dir(on_selection=on_selection)
        except Exception:
            self._open_fallback_modal()

    def _open_fallback_modal(self) -> None:
        modal = ModalView(size_hint=(0.7, 0.3), auto_dismiss=False)
        content = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(10))
        input_box = TextInput(text=self.path_input.text, multiline=False)
        row = BoxLayout(size_hint_y=None, height=dp(32), spacing=dp(8))
        ok = ClassicButton(theme=self.theme, text="Use this path")
        cancel = ClassicButton(theme=self.theme, text="Cancel")

        def apply_path(*_) -> None:
            self.path_input.text = input_box.text.strip()
            modal.dismiss()

        ok.bind(on_release=apply_path)
        cancel.bind(on_release=lambda *_: modal.dismiss())

        row.add_widget(ok)
        row.add_widget(cancel)
        content.add_widget(Label(text="Enter installation directory:"))
        content.add_widget(input_box)
        content.add_widget(row)
        modal.add_widget(content)
        modal.open()

    def get_data(self) -> dict:
        return {"install_dir": self.path_input.text.strip()}

    def validate(self) -> tuple[bool, str | None]:
        raw = self.path_input.text.strip()
        self.error.text = ""

        if not raw:
            self.error.text = "Installation path is required"
            return False, self.error.text
        path = Path(raw)

        if self.step_config.fields:
            ok, message = validate_field_value(self.step_config.fields[0], raw)
            if not ok:
                self.error.text = message or "Invalid directory"
                return False, self.error.text

        try:
            ensure_dir(path)
        except Exception as exc:
            self.error.text = f"Unable to create directory: {exc}"
            return False, self.error.text

        if not is_writable(path):
            self.error.text = "Directory is not writable"
            return False, self.error.text

        return True, None
