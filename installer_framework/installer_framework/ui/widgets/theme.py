"""Widget theming abstractions and factory selection.

This module is the canonical UI widget entrypoint for themed widget creation.
Concrete implementations live in `classic_theme.py` and `modern_theme.py`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Protocol

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


class ThemeCheckboxRow(Protocol):
    """Protocol for themed checkbox row widgets."""

    checkbox: QCheckBox


class ThemeGroupBox(Protocol):
    """Protocol for themed group box widgets."""

    content_layout: QVBoxLayout


class ThemeDialogFrame(Protocol):
    """Protocol for themed dialog frames."""

    title_label: QLabel
    message_label: QLabel
    buttons_layout: QHBoxLayout


class ThemeWidgetFactory(ABC):
    """Factory interface for theme-specific widget creation."""

    def __init__(self, theme: UITheme) -> None:
        self.theme = theme

    @abstractmethod
    def create_panel(self, **kwargs) -> QFrame:
        """Create a content panel container."""

    @abstractmethod
    def create_separator(self, **kwargs) -> QFrame:
        """Create a horizontal separator widget."""

    @abstractmethod
    def create_button(self, text: str, default_action: bool = False, **kwargs) -> QPushButton:
        """Create a themed push button."""

    @abstractmethod
    def create_header(self, title: str, description: str, image_path: str | None = None, **kwargs) -> QWidget:
        """Create a themed header strip."""

    @abstractmethod
    def create_sidebar(self, title: str, subtitle: str = "", image_path: str | None = None, **kwargs) -> QWidget:
        """Create a themed sidebar widget."""

    @abstractmethod
    def create_checkbox_row(self, text: str, active: bool = False, **kwargs) -> ThemeCheckboxRow:
        """Create a themed checkbox row."""

    @abstractmethod
    def create_group_box(self, title: str, **kwargs) -> ThemeGroupBox:
        """Create a themed group box wrapper."""

    @abstractmethod
    def create_dialog_frame(self, title: str, message: str, **kwargs) -> ThemeDialogFrame:
        """Create a themed dialog content frame."""

    @abstractmethod
    def message_dialog_size(self) -> tuple[int, int]:
        """Return message dialog size (w, h)."""

    @abstractmethod
    def confirm_dialog_size(self) -> tuple[int, int]:
        """Return confirm dialog size (w, h)."""

    @abstractmethod
    def dialog_margins(self) -> tuple[int, int, int, int]:
        """Return dialog content margins (l, t, r, b)."""


class WizardShellStyler(ABC):
    """Shell-level styling strategy for the installer wizard window."""

    def __init__(self, theme: UITheme) -> None:
        self.theme = theme

    @abstractmethod
    def root_margins(self) -> tuple[int, int, int, int]:
        """Return root layout margins (l, t, r, b)."""

    @abstractmethod
    def main_layout_spacing(self) -> int:
        """Return spacing between top-level shell columns."""

    @abstractmethod
    def show_sidebar(self) -> bool:
        """Whether the shell should render the branding sidebar."""

    @abstractmethod
    def header_height(self) -> int:
        """Return fixed header height."""

    @abstractmethod
    def content_margins(self) -> tuple[int, int, int, int]:
        """Return content panel margins (l, t, r, b)."""

    @abstractmethod
    def nav_margins(self) -> tuple[int, int, int, int]:
        """Return navigation bar margins (l, t, r, b)."""

    @abstractmethod
    def configure_main_column_layout(self, layout: QVBoxLayout) -> None:
        """Apply main-column margins/spacing."""

    @abstractmethod
    def style_content_panel(self, panel: QFrame) -> None:
        """Apply content panel stylesheet/attributes."""

    @abstractmethod
    def style_nav_widget(self, nav_widget: QWidget) -> None:
        """Apply nav area stylesheet/attributes."""

    @abstractmethod
    def include_separator(self) -> bool:
        """Whether to include a separator above nav area."""

    @abstractmethod
    def apply_window_style(self, window: QMainWindow) -> None:
        """Apply top-level window styling."""

    @abstractmethod
    def apply_global_control_style(self, root: QWidget) -> None:
        """Apply theme-wide control styling within the wizard root."""

    @abstractmethod
    def resolve_header_image(
        self,
        branding_logo: Path | None,
        theme_header: Path | None,
        theme_sidebar: Path | None,
    ) -> Path | None:
        """Resolve the header image source according to theme-specific rules."""


def build_widget_factory(theme: UITheme) -> ThemeWidgetFactory:
    """Create a style-specific widget factory."""
    if theme.is_modern:
        from installer_framework.ui.widgets.modern_theme import ModernWidgetFactory

        return ModernWidgetFactory(theme)

    from installer_framework.ui.widgets.classic_theme import ClassicWidgetFactory

    return ClassicWidgetFactory(theme)


def build_shell_styler(theme: UITheme) -> WizardShellStyler:
    """Create a style-specific wizard shell styler."""
    if theme.is_modern:
        from installer_framework.ui.widgets.modern_theme import ModernShellStyler

        return ModernShellStyler(theme)

    from installer_framework.ui.widgets.classic_theme import ClassicShellStyler

    return ClassicShellStyler(theme)


__all__ = [
    "ThemeCheckboxRow",
    "ThemeGroupBox",
    "ThemeDialogFrame",
    "ThemeWidgetFactory",
    "WizardShellStyler",
    "build_widget_factory",
    "build_shell_styler",
]
