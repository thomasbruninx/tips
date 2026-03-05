"""Classic InstallShield-like reusable UI widgets."""

from __future__ import annotations

from typing import Callable

from kivy.graphics import Color, Line, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.widget import Widget

from installer_framework.ui.theme import UITheme


class ClassicPanel(BoxLayout):
    """Panel with 3D bevel border and configurable fill color."""

    def __init__(self, theme: UITheme, fill_color=None, border: bool = True, **kwargs) -> None:
        super().__init__(**kwargs)
        self.theme = theme
        self.fill_color = fill_color or theme.panel_bg
        self.border = border

        with self.canvas.before:
            self._bg_color = Color(*self.fill_color)
            self._bg_rect = Rectangle(pos=self.pos, size=self.size)

        with self.canvas.after:
            self._border_light_color = Color(*self.theme.border_light)
            self._border_light_top = Line(points=[], width=1)
            self._border_light_left = Line(points=[], width=1)
            self._border_dark_color = Color(*self.theme.border_dark)
            self._border_dark_bottom = Line(points=[], width=1)
            self._border_dark_right = Line(points=[], width=1)

        self.bind(pos=self._redraw, size=self._redraw)
        self._redraw()

    def _redraw(self, *_args) -> None:
        x, y = self.pos
        w, h = self.size
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size
        self._bg_color.rgba = self.fill_color

        if not self.border:
            self._border_light_top.points = []
            self._border_light_left.points = []
            self._border_dark_bottom.points = []
            self._border_dark_right.points = []
            return

        self._border_light_top.points = [x, y + h - 1, x + w, y + h - 1]
        self._border_light_left.points = [x, y, x, y + h]
        self._border_dark_bottom.points = [x, y, x + w, y]
        self._border_dark_right.points = [x + w - 1, y, x + w - 1, y + h]


class ClassicSeparator(Widget):
    """Horizontal separator with light and dark edge."""

    def __init__(self, theme: UITheme, **kwargs) -> None:
        super().__init__(size_hint_y=None, height=dp(2), **kwargs)
        self.theme = theme
        with self.canvas:
            self._dark = Color(*self.theme.border_dark)
            self._line_dark = Line(points=[], width=1)
            self._light = Color(*self.theme.border_light)
            self._line_light = Line(points=[], width=1)
        self.bind(pos=self._redraw, size=self._redraw)
        self._redraw()

    def _redraw(self, *_args) -> None:
        x, y = self.pos
        w, _ = self.size
        self._line_dark.points = [x, y + 1, x + w, y + 1]
        self._line_light.points = [x, y, x + w, y]


class ClassicButton(Button):
    """Beveled button with classic visual states."""

    def __init__(self, theme: UITheme, default_action: bool = False, **kwargs) -> None:
        super().__init__(**kwargs)
        self.theme = theme
        self.default_action = default_action
        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0, 0, 0, 0)
        self.color = self.theme.text_primary

        with self.canvas.before:
            self._bg_color = Color(*self.theme.button_face)
            self._bg_rect = Rectangle(pos=self.pos, size=self.size)

        with self.canvas.after:
            self._line_color_top = Color(*self.theme.border_light)
            self._line_top = Line(points=[], width=1)
            self._line_left = Line(points=[], width=1)
            self._line_color_bottom = Color(*self.theme.border_dark)
            self._line_bottom = Line(points=[], width=1)
            self._line_right = Line(points=[], width=1)
            self._default_outline_color = Color(*self.theme.accent)
            self._default_outline = Line(points=[], width=1)

        self.bind(pos=self._redraw, size=self._redraw, state=self._redraw, disabled=self._redraw)
        self._redraw()

    def _redraw(self, *_args) -> None:
        x, y = self.pos
        w, h = self.size

        if self.disabled:
            face = self.theme.button_face
        elif self.state == "down":
            face = self.theme.button_pressed
        else:
            face = self.theme.button_face

        self._bg_color.rgba = face
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size

        top_color = self.theme.border_dark if self.state == "down" else self.theme.border_light
        bottom_color = self.theme.border_light if self.state == "down" else self.theme.border_dark

        self._line_color_top.rgba = top_color
        self._line_color_bottom.rgba = bottom_color

        self._line_top.points = [x, y + h - 1, x + w, y + h - 1]
        self._line_left.points = [x, y, x, y + h]
        self._line_bottom.points = [x, y, x + w, y]
        self._line_right.points = [x + w - 1, y, x + w - 1, y + h]

        if self.default_action and not self.disabled:
            self._default_outline.points = [
                x + 2,
                y + 2,
                x + w - 2,
                y + 2,
                x + w - 2,
                y + h - 2,
                x + 2,
                y + h - 2,
                x + 2,
                y + 2,
            ]
        else:
            self._default_outline.points = []


class ClassicHeader(ClassicPanel):
    """Wizard step header strip."""

    def __init__(self, theme: UITheme, title: str, description: str, image_path: str | None = None, **kwargs) -> None:
        super().__init__(
            theme=theme,
            orientation="horizontal",
            fill_color=theme.panel_bg,
            size_hint_y=None,
            height=dp(82),
            padding=(dp(10), dp(8)),
            spacing=dp(8),
            **kwargs,
        )
        text_block = BoxLayout(orientation="vertical", spacing=dp(2))
        title_lbl = Label(text=f"[b]{title}[/b]", markup=True, color=theme.text_primary, font_size=f"{theme.title_size}sp", halign="left")
        title_lbl.bind(size=lambda instance, value: setattr(instance, "text_size", value))
        desc_lbl = Label(text=description, color=theme.text_primary, font_size=f"{theme.base_size}sp", halign="left", valign="top")
        desc_lbl.bind(size=lambda instance, value: setattr(instance, "text_size", value))
        text_block.add_widget(title_lbl)
        text_block.add_widget(desc_lbl)
        self.add_widget(text_block)

        if image_path:
            self.add_widget(Image(source=image_path, size_hint_x=None, width=dp(120)))


class ClassicCheckboxRow(BoxLayout):
    """Checkbox row with click target label/button."""

    def __init__(self, theme: UITheme, text: str, active: bool = False, on_toggle: Callable[[bool], None] | None = None, **kwargs) -> None:
        super().__init__(orientation="horizontal", size_hint_y=None, height=dp(30), spacing=dp(6), **kwargs)
        self.theme = theme
        self.checkbox = CheckBox(active=active, size_hint_x=None, width=dp(32))
        self.btn = Button(text=text)
        self.btn.background_normal = ""
        self.btn.background_down = ""
        self.btn.background_color = (0, 0, 0, 0)
        self.btn.color = theme.text_primary
        self.btn.halign = "left"
        self.btn.valign = "middle"
        self.btn.bind(size=lambda instance, value: setattr(instance, "text_size", value))
        self.btn.bind(on_release=lambda *_: self._toggle())

        if on_toggle:
            self.checkbox.bind(active=lambda _i, value: on_toggle(value))

        self.add_widget(self.checkbox)
        self.add_widget(self.btn)

    def _toggle(self) -> None:
        self.checkbox.active = not self.checkbox.active


class ClassicGroupBox(ClassicPanel):
    """Classic group box frame with title label."""

    def __init__(self, theme: UITheme, title: str, **kwargs) -> None:
        super().__init__(
            theme=theme,
            orientation="vertical",
            fill_color=theme.panel_bg,
            padding=(dp(8), dp(8)),
            spacing=dp(6),
            **kwargs,
        )
        self.title_label = Label(text=f"[b]{title}[/b]", markup=True, color=theme.text_primary, size_hint_y=None, height=dp(22), halign="left")
        self.title_label.bind(size=lambda instance, value: setattr(instance, "text_size", value))
        self.content = BoxLayout(orientation="vertical", spacing=dp(6))
        self.add_widget(self.title_label)
        self.add_widget(self.content)


class ClassicDialogFrame(ClassicPanel):
    """Dialog shell with title/body/button rows."""

    def __init__(self, theme: UITheme, title: str, message: str, **kwargs) -> None:
        super().__init__(
            theme=theme,
            orientation="vertical",
            fill_color=theme.window_bg,
            padding=(dp(12), dp(12)),
            spacing=dp(10),
            **kwargs,
        )
        self.title_label = Label(text=f"[b]{title}[/b]", markup=True, color=theme.text_primary, size_hint_y=None, height=dp(24), halign="left")
        self.title_label.bind(size=lambda instance, value: setattr(instance, "text_size", value))
        self.message_label = Label(text=message, color=theme.text_primary, halign="left", valign="top")
        self.message_label.bind(size=lambda instance, value: setattr(instance, "text_size", value))
        self.buttons = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(32), spacing=dp(8))

        self.add_widget(self.title_label)
        self.add_widget(self.message_label)
        self.add_widget(self.buttons)


class ClassicSidebar(ClassicPanel):
    """Wizard sidebar with image or classic blue gradient fallback."""

    def __init__(self, theme: UITheme, title: str, subtitle: str = "", image_path: str | None = None, **kwargs) -> None:
        self._top_rect = None
        self._bottom_rect = None
        super().__init__(theme=theme, orientation="vertical", fill_color=theme.sidebar_top, border=True, **kwargs)
        self.theme = theme
        self._image_path = image_path

        with self.canvas.before:
            self._gradient_color_top = Color(*theme.sidebar_top)
            self._top_rect = Rectangle(pos=self.pos, size=self.size)
            self._gradient_color_bottom = Color(*theme.sidebar_bottom)
            self._bottom_rect = Rectangle(pos=self.pos, size=self.size)

        self.bind(pos=self._redraw, size=self._redraw)

        if image_path:
            self.add_widget(Image(source=image_path))
        else:
            self.padding = (dp(10), dp(10))
            self.spacing = dp(8)
            self.add_widget(Widget())
            title_lbl = Label(text=f"[b]{title}[/b]", markup=True, color=(1, 1, 1, 1), halign="left", valign="bottom", size_hint_y=None, height=dp(40))
            title_lbl.bind(size=lambda instance, value: setattr(instance, "text_size", value))
            subtitle_lbl = Label(text=subtitle, color=(1, 1, 1, 1), halign="left", valign="top", size_hint_y=None, height=dp(46))
            subtitle_lbl.bind(size=lambda instance, value: setattr(instance, "text_size", value))
            self.add_widget(title_lbl)
            self.add_widget(subtitle_lbl)
        self._redraw()

    def _redraw(self, *_args) -> None:
        super()._redraw()
        if self._top_rect is None or self._bottom_rect is None:
            return
        x, y = self.pos
        w, h = self.size
        half = h * 0.45
        self._top_rect.pos = (x, y + h - half)
        self._top_rect.size = (w, half)
        self._bottom_rect.pos = (x, y)
        self._bottom_rect.size = (w, h - half)
