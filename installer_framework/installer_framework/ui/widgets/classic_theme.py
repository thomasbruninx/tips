"""Classic widget and shell implementations."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QCheckBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from installer_framework.ui.theme import UITheme
from installer_framework.ui.widgets.theme import ThemeWidgetFactory, WizardShellStyler


def _set_font(widget, theme: UITheme, size: int, bold: bool = False) -> None:
    font = QFont(theme.font_name or "")
    if theme.font_name:
        font.setFamily(theme.font_name)
    font.setPointSize(size)
    font.setBold(bold)
    widget.setFont(font)


class _ClassicPanel(QFrame):
    def __init__(self, theme: UITheme, **kwargs) -> None:
        super().__init__(**kwargs)
        if not self.objectName():
            self.setObjectName("ThemePanel")
        self.setFrameShape(QFrame.Shape.Panel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setLineWidth(1)
        self.setMidLineWidth(1)
        self.setStyleSheet(
            f"QFrame#{self.objectName()} {{ background-color: {theme.panel_bg}; border: 1px solid {theme.border_dark}; }}"
        )


class _ClassicSeparator(QFrame):
    def __init__(self, theme: UITheme, **kwargs) -> None:
        super().__init__(**kwargs)
        self.setFrameShape(QFrame.Shape.HLine)
        self.setFrameShadow(QFrame.Shadow.Sunken)
        self.setStyleSheet(f"QFrame {{ color: {theme.border_dark}; background-color: {theme.border_dark}; }}")


class _ClassicButton(QPushButton):
    def __init__(self, theme: UITheme, text: str, default_action: bool = False, **kwargs) -> None:
        super().__init__(text, **kwargs)
        border = theme.accent if default_action else theme.border_dark
        self.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {theme.button_face};
                color: {theme.text_primary};
                border: 1px solid {border};
                padding: 3px 10px;
            }}
            QPushButton:pressed {{
                background-color: {theme.button_pressed};
                border-style: inset;
            }}
            QPushButton:disabled {{
                color: #7A7A7A;
                background-color: #E6E6E6;
                border: 1px solid #B0B0B0;
            }}
            """
        )
        _set_font(self, theme, theme.base_size)


class _ClassicHeader(_ClassicPanel):
    def __init__(self, theme: UITheme, title: str, description: str, image_path: str | None = None, **kwargs) -> None:
        super().__init__(theme=theme, **kwargs)
        self.setObjectName("ThemeHeader")
        self.setStyleSheet(
            f"QFrame#ThemeHeader {{ background-color: {theme.panel_bg}; border: 1px solid {theme.border_dark}; }}"
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)

        text_wrap = QWidget()
        text_layout = QVBoxLayout(text_wrap)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"color: {theme.text_primary};")
        _set_font(title_lbl, theme, theme.title_size, bold=True)
        text_layout.addWidget(title_lbl)

        if description.strip():
            desc_lbl = QLabel(description)
            desc_lbl.setWordWrap(True)
            desc_lbl.setStyleSheet(f"color: {theme.text_primary};")
            _set_font(desc_lbl, theme, theme.base_size)
            text_layout.addWidget(desc_lbl)

        layout.addWidget(text_wrap, 1)

        if image_path:
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                img = QLabel()
                img.setPixmap(pixmap.scaledToHeight(56, Qt.TransformationMode.SmoothTransformation))
                layout.addWidget(img, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)


class _ClassicSidebar(QWidget):
    def __init__(self, theme: UITheme, title: str, subtitle: str = "", image_path: str | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.theme = theme
        self.title = title
        self.subtitle = subtitle
        self.pixmap = QPixmap(image_path) if image_path else QPixmap()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        rect = self.rect()

        grad = QLinearGradient(float(rect.left()), float(rect.top()), float(rect.left()), float(rect.bottom()))
        grad.setColorAt(0.0, QColor(self.theme.sidebar_top))
        grad.setColorAt(1.0, QColor(self.theme.sidebar_bottom))
        painter.fillRect(rect, grad)

        painter.setPen(QColor(self.theme.border_dark))
        painter.drawRect(rect.adjusted(0, 0, -1, -1))

        if not self.pixmap.isNull():
            scaled = self.pixmap.scaled(
                rect.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            x = rect.x() + (rect.width() - scaled.width()) // 2
            y = rect.y() + (rect.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
            return

        painter.setPen(Qt.GlobalColor.white)
        title_font = QFont(self.theme.font_name or "", self.theme.title_size)
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.drawText(
            rect.adjusted(10, rect.height() - 90, -10, -50),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
            self.title,
        )

        sub_font = QFont(self.theme.font_name or "", self.theme.base_size)
        painter.setFont(sub_font)
        painter.drawText(
            rect.adjusted(10, rect.height() - 55, -10, -10),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
            self.subtitle,
        )


class _ClassicCheckboxRow(QWidget):
    def __init__(self, theme: UITheme, text: str, active: bool = False, **kwargs) -> None:
        super().__init__(**kwargs)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.checkbox = QCheckBox()
        self.checkbox.setChecked(active)
        self.checkbox.setStyleSheet(f"QCheckBox {{ color: {theme.text_primary}; }}")

        self.button = QPushButton(text)
        self.button.setFlat(True)
        self.button.setStyleSheet(
            f"QPushButton {{ border: none; text-align: left; color: {theme.text_primary}; background: transparent; }}"
        )
        _set_font(self.button, theme, theme.base_size)
        self.button.clicked.connect(lambda: self.checkbox.setChecked(not self.checkbox.isChecked()))

        layout.addWidget(self.checkbox)
        layout.addWidget(self.button, 1)


class _ClassicGroupBox(QGroupBox):
    def __init__(self, theme: UITheme, title: str, **kwargs) -> None:
        super().__init__(title, **kwargs)
        self.setStyleSheet(
            f"""
            QGroupBox {{
                color: {theme.text_primary};
                border: 1px solid {theme.border_dark};
                margin-top: 8px;
                padding-top: 10px;
                background-color: {theme.panel_bg};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 3px;
            }}
            """
        )
        _set_font(self, theme, theme.base_size, bold=True)

        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(8, 8, 8, 8)
        self.content_layout.setSpacing(6)

        root = QVBoxLayout(self)
        root.setContentsMargins(4, 8, 4, 4)
        root.addWidget(self.content)


class _ClassicDialogFrame(QWidget):
    def __init__(self, theme: UITheme, title: str, message: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.setObjectName("ThemeDialogFrame")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(
            f"""
            QWidget#ThemeDialogFrame {{
                background-color: {theme.window_bg};
                border: none;
                border-radius: 0px;
            }}
            QLabel {{
                background: transparent;
                border: none;
            }}
            QWidget#DialogButtonsRow {{
                background: transparent;
                border: none;
            }}
            """
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        self.title_label = QLabel(title)
        _set_font(self.title_label, theme, theme.base_size, bold=True)
        self.title_label.setStyleSheet(f"color: {theme.text_primary};")

        self.message_label = QLabel(message)
        _set_font(self.message_label, theme, theme.base_size)
        self.message_label.setStyleSheet(f"color: {theme.text_primary};")
        self.message_label.setWordWrap(True)

        self.buttons = QWidget()
        self.buttons.setObjectName("DialogButtonsRow")
        self.buttons_layout = QHBoxLayout(self.buttons)
        self.buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.buttons_layout.setSpacing(8)

        root.addWidget(self.title_label)
        root.addWidget(self.message_label, 1)
        root.addWidget(self.buttons)


class ClassicWidgetFactory(ThemeWidgetFactory):
    """Classic concrete widget factory."""

    def create_panel(self, **kwargs) -> QFrame:
        return _ClassicPanel(theme=self.theme, **kwargs)

    def create_separator(self, **kwargs) -> QFrame:
        return _ClassicSeparator(theme=self.theme, **kwargs)

    def create_button(self, text: str, default_action: bool = False, **kwargs) -> QPushButton:
        return _ClassicButton(theme=self.theme, text=text, default_action=default_action, **kwargs)

    def create_header(self, title: str, description: str, image_path: str | None = None, **kwargs) -> QWidget:
        return _ClassicHeader(theme=self.theme, title=title, description=description, image_path=image_path, **kwargs)

    def create_sidebar(self, title: str, subtitle: str = "", image_path: str | None = None, **kwargs) -> QWidget:
        return _ClassicSidebar(theme=self.theme, title=title, subtitle=subtitle, image_path=image_path, **kwargs)

    def create_checkbox_row(self, text: str, active: bool = False, **kwargs):
        return _ClassicCheckboxRow(theme=self.theme, text=text, active=active, **kwargs)

    def create_group_box(self, title: str, **kwargs):
        return _ClassicGroupBox(theme=self.theme, title=title, **kwargs)

    def create_dialog_frame(self, title: str, message: str, **kwargs):
        return _ClassicDialogFrame(theme=self.theme, title=title, message=message, **kwargs)

    def message_dialog_size(self) -> tuple[int, int]:
        return (460, 220)

    def confirm_dialog_size(self) -> tuple[int, int]:
        return (470, 220)

    def dialog_margins(self) -> tuple[int, int, int, int]:
        return (0, 0, 0, 0)


class ClassicShellStyler(WizardShellStyler):
    """Classic concrete wizard-shell styler."""

    def root_margins(self) -> tuple[int, int, int, int]:
        return (0, 0, 0, 0)

    def main_layout_spacing(self) -> int:
        return 0

    def show_sidebar(self) -> bool:
        return True

    def header_height(self) -> int:
        return 82

    def content_margins(self) -> tuple[int, int, int, int]:
        padding = self.theme.config.metrics.padding
        return (padding, padding, padding, padding)

    def nav_margins(self) -> tuple[int, int, int, int]:
        return (10, 8, 10, 8)

    def configure_main_column_layout(self, layout: QVBoxLayout) -> None:
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

    def style_content_panel(self, panel: QFrame) -> None:
        panel.setObjectName("WizardContentPanel")
        panel.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        panel.setStyleSheet(
            f"QFrame#WizardContentPanel {{ background-color: {self.theme.panel_bg}; border: 1px solid {self.theme.border_dark}; }}"
        )

    def style_nav_widget(self, nav_widget: QWidget) -> None:
        nav_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        nav_widget.setStyleSheet("QWidget { background: transparent; border: none; }")

    def include_separator(self) -> bool:
        return True

    def apply_window_style(self, window: QMainWindow) -> None:
        window.setStyleSheet(f"QMainWindow {{ background-color: {self.theme.window_bg}; }}")

    def apply_global_control_style(self, root: QWidget) -> None:
        # Classic mode keeps per-widget styling and avoids global overrides.
        root.setStyleSheet("")

    def resolve_header_image(
        self,
        branding_logo: Path | None,
        theme_header: Path | None,
        theme_sidebar: Path | None,
    ) -> Path | None:
        _ = branding_logo, theme_sidebar
        return theme_header
