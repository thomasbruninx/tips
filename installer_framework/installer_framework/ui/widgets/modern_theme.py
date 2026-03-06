"""Modern macOS Installer-like widget and shell implementations."""

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

from installer_framework.ui.theme import UITheme, tint_hex
from installer_framework.ui.widgets.theme import ThemeWidgetFactory, WizardShellStyler


def _set_font(widget, theme: UITheme, size: int, bold: bool = False) -> None:
    font = QFont(theme.font_name or "")
    if theme.font_name:
        font.setFamily(theme.font_name)
    font.setPointSize(size)
    font.setBold(bold)
    widget.setFont(font)


class _ModernPanel(QFrame):
    def __init__(self, theme: UITheme, **kwargs) -> None:
        super().__init__(**kwargs)
        if not self.objectName():
            self.setObjectName("ThemePanel")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet(
            f"QFrame#{self.objectName()} {{ background-color: {theme.panel_bg}; border: 1px solid {theme.border_dark}; border-radius: 4px; }}"
        )


class _ModernSeparator(QFrame):
    def __init__(self, theme: UITheme, **kwargs) -> None:
        super().__init__(**kwargs)
        self.setFrameShape(QFrame.Shape.HLine)
        self.setFrameShadow(QFrame.Shadow.Plain)
        self.setStyleSheet(f"QFrame {{ color: {theme.border_dark}; background-color: {theme.border_dark}; }}")


class _ModernButton(QPushButton):
    def __init__(self, theme: UITheme, text: str, default_action: bool = False, **kwargs) -> None:
        super().__init__(text, **kwargs)
        if default_action:
            base_bg = theme.accent
            hover_bg = tint_hex(base_bg, -0.04)
            pressed_bg = tint_hex(base_bg, -0.09)
            fg = "#FFFFFF"
            border = tint_hex(base_bg, -0.14)
        else:
            base_bg = tint_hex(theme.window_bg, 0.01)
            hover_bg = tint_hex(base_bg, -0.02)
            pressed_bg = tint_hex(base_bg, -0.06)
            fg = theme.text_primary
            border = theme.border_dark

        self.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {base_bg};
                color: {fg};
                border: 1px solid {border};
                border-radius: 7px;
                padding: 4px 12px;
            }}
            QPushButton:hover {{
                background-color: {hover_bg};
            }}
            QPushButton:pressed {{
                background-color: {pressed_bg};
            }}
            QPushButton:disabled {{
                color: #9A9AA0;
                background-color: #EFEFF0;
                border: 1px solid #D0D0D4;
            }}
            """
        )
        _set_font(self, theme, theme.base_size)


class _ModernHeader(QWidget):
    def __init__(self, theme: UITheme, title: str, description: str, image_path: str | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.setObjectName("ThemeHeader")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(
            f"QWidget#ThemeHeader {{ background-color: {theme.panel_bg}; border-bottom: 1px solid {theme.border_dark}; }}"
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 10, 18, 10)
        layout.setSpacing(12)

        text_wrap = QWidget()
        text_layout = QVBoxLayout(text_wrap)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(3)

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
                img.setPixmap(pixmap.scaledToHeight(44, Qt.TransformationMode.SmoothTransformation))
                layout.addWidget(img, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)


class _ModernSidebar(QWidget):
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
        painter.drawLine(rect.topRight(), rect.bottomRight())

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


class _ModernCheckboxRow(QWidget):
    def __init__(self, theme: UITheme, text: str, active: bool = False, **kwargs) -> None:
        super().__init__(**kwargs)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(7)

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


class _ModernGroupBox(QGroupBox):
    def __init__(self, theme: UITheme, title: str, **kwargs) -> None:
        super().__init__(title, **kwargs)
        self.setStyleSheet(
            f"""
            QGroupBox {{
                color: {theme.text_primary};
                border: 1px solid {theme.border_dark};
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 12px;
                background-color: {theme.panel_bg};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 4px;
            }}
            """
        )
        _set_font(self, theme, theme.base_size, bold=True)

        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        self.content_layout.setSpacing(7)

        root = QVBoxLayout(self)
        root.setContentsMargins(4, 8, 4, 4)
        root.addWidget(self.content)


class _ModernDialogFrame(QWidget):
    def __init__(self, theme: UITheme, title: str, message: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.setObjectName("ThemeDialogFrame")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(
            f"""
            QWidget#ThemeDialogFrame {{
                background-color: {theme.panel_bg};
                border: 1px solid {theme.border_dark};
                border-radius: 8px;
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
        root.setContentsMargins(14, 14, 14, 14)
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


class ModernWidgetFactory(ThemeWidgetFactory):
    """Modern concrete widget factory."""

    def create_panel(self, **kwargs) -> QFrame:
        return _ModernPanel(theme=self.theme, **kwargs)

    def create_separator(self, **kwargs) -> QFrame:
        return _ModernSeparator(theme=self.theme, **kwargs)

    def create_button(self, text: str, default_action: bool = False, **kwargs) -> QPushButton:
        return _ModernButton(theme=self.theme, text=text, default_action=default_action, **kwargs)

    def create_header(self, title: str, description: str, image_path: str | None = None, **kwargs) -> QWidget:
        return _ModernHeader(theme=self.theme, title=title, description=description, image_path=image_path, **kwargs)

    def create_sidebar(self, title: str, subtitle: str = "", image_path: str | None = None, **kwargs) -> QWidget:
        return _ModernSidebar(theme=self.theme, title=title, subtitle=subtitle, image_path=image_path, **kwargs)

    def create_checkbox_row(self, text: str, active: bool = False, **kwargs):
        return _ModernCheckboxRow(theme=self.theme, text=text, active=active, **kwargs)

    def create_group_box(self, title: str, **kwargs):
        return _ModernGroupBox(theme=self.theme, title=title, **kwargs)

    def create_dialog_frame(self, title: str, message: str, **kwargs):
        return _ModernDialogFrame(theme=self.theme, title=title, message=message, **kwargs)

    def message_dialog_size(self) -> tuple[int, int]:
        return (510, 235)

    def confirm_dialog_size(self) -> tuple[int, int]:
        return (520, 235)

    def dialog_margins(self) -> tuple[int, int, int, int]:
        return (10, 10, 10, 10)


class ModernShellStyler(WizardShellStyler):
    """Modern concrete wizard-shell styler."""

    def root_margins(self) -> tuple[int, int, int, int]:
        return (12, 12, 12, 12)

    def main_layout_spacing(self) -> int:
        return 0

    def show_sidebar(self) -> bool:
        return False

    def header_height(self) -> int:
        return 90

    def content_margins(self) -> tuple[int, int, int, int]:
        padding = max(12, self.theme.config.metrics.padding)
        return (padding, padding, padding, padding)

    def nav_margins(self) -> tuple[int, int, int, int]:
        return (12, 9, 12, 9)

    def configure_main_column_layout(self, layout: QVBoxLayout) -> None:
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

    def style_content_panel(self, panel: QFrame) -> None:
        panel.setObjectName("WizardContentPanel")
        panel.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        panel.setStyleSheet(
            f"QFrame#WizardContentPanel {{ background-color: {self.theme.panel_bg}; border: 1px solid {self.theme.border_dark}; border-radius: 4px; }}"
        )

    def style_nav_widget(self, nav_widget: QWidget) -> None:
        nav_widget.setObjectName("WizardNav")
        nav_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        nav_widget.setStyleSheet(
            f"QWidget#WizardNav {{ background-color: {tint_hex(self.theme.window_bg, -0.02)}; border-top: 1px solid {self.theme.border_dark}; }}"
        )

    def include_separator(self) -> bool:
        return False

    def apply_window_style(self, window: QMainWindow) -> None:
        window.setStyleSheet(f"QMainWindow {{ background-color: {self.theme.window_bg}; }}")

    def apply_global_control_style(self, root: QWidget) -> None:
        root.setStyleSheet(
            f"""
            QLineEdit, QComboBox, QPlainTextEdit, QTextEdit {{
                background-color: {self.theme.panel_bg};
                color: {self.theme.text_primary};
                border: 1px solid {self.theme.border_dark};
                border-radius: 6px;
                padding: 4px 6px;
                selection-background-color: {tint_hex(self.theme.accent, 0.12)};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 18px;
            }}
            QScrollArea {{
                border: 1px solid {self.theme.border_dark};
                background-color: {self.theme.panel_bg};
                border-radius: 6px;
            }}
            QProgressBar {{
                background-color: {tint_hex(self.theme.window_bg, 0.02)};
                color: {self.theme.text_primary};
                border: 1px solid {self.theme.border_dark};
                border-radius: 5px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {self.theme.accent};
                border-radius: 4px;
            }}
            QCheckBox, QRadioButton {{
                color: {self.theme.text_primary};
            }}
            """
        )

    def resolve_header_image(
        self,
        branding_logo: Path | None,
        theme_header: Path | None,
        theme_sidebar: Path | None,
    ) -> Path | None:
        return branding_logo or theme_header or theme_sidebar
