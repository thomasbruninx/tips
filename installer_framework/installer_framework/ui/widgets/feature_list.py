"""Multi-select feature list widget with search filter."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import QCheckBox, QLineEdit, QScrollArea, QVBoxLayout, QWidget

from installer_framework.config.models import FeatureConfig
from installer_framework.config.models import ThemeConfig
from installer_framework.ui.theme import UITheme, get_active_theme

_DEFAULT_THEME = UITheme(config=ThemeConfig(), source_root=Path.cwd())


class FeatureListWidget(QWidget):
    def __init__(self, features: list[FeatureConfig], selected: list[str] | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.theme: UITheme = get_active_theme() or _DEFAULT_THEME
        self.features = features
        self.selected = set(selected or [])
        self.rows: list[tuple[FeatureConfig, QWidget, QCheckBox]] = []

        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(6)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search features...")
        self.search.textChanged.connect(self._apply_filter)
        self.search.setStyleSheet(
            f"QLineEdit {{ background-color: {self.theme.panel_bg}; color: {self.theme.text_primary}; border: 1px solid {self.theme.border_dark}; padding: 2px 4px; }}"
        )

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_container = QWidget()
        self.scroll_container.setObjectName("FeatureListContainer")
        self.container_layout = QVBoxLayout(self.scroll_container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(4)
        self.scroll.setWidget(self.scroll_container)
        self._apply_scroll_style()

        root.addWidget(self.search)
        root.addWidget(self.scroll, 1)

        self._build_rows()

    def _apply_scroll_style(self) -> None:
        panel_bg = self.theme.panel_bg
        border = self.theme.border_dark
        text = self.theme.text_primary

        self.scroll.setStyleSheet(
            f"""
            QScrollArea {{
                border: 1px solid {border};
                background-color: {panel_bg};
            }}
            QScrollArea > QWidget > QWidget {{
                background-color: {panel_bg};
            }}
            QWidget#FeatureListContainer {{
                background-color: {panel_bg};
            }}
            """
        )
        viewport = self.scroll.viewport()
        viewport.setObjectName("FeatureListViewport")
        viewport.setStyleSheet(f"background-color: {panel_bg};")
        self.scroll_container.setStyleSheet(f"QWidget#FeatureListContainer {{ background-color: {panel_bg}; color: {text}; }}")

    def _build_rows(self) -> None:
        while self.container_layout.count():
            item = self.container_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        self.rows.clear()
        for feature in self.features:
            row = QWidget()
            row.setObjectName("FeatureListRow")
            row.setStyleSheet(f"QWidget#FeatureListRow {{ background-color: {self.theme.panel_bg}; color: {self.theme.text_primary}; }}")
            layout = QVBoxLayout(row)
            layout.setContentsMargins(0, 0, 0, 0)
            checkbox = QCheckBox(feature.label)
            checkbox.setChecked(feature.id in self.selected or feature.default)
            checkbox.setStyleSheet(f"QCheckBox {{ color: {self.theme.text_primary}; }}")
            layout.addWidget(checkbox)
            self.container_layout.addWidget(row)
            self.rows.append((feature, row, checkbox))

        self.container_layout.addStretch(1)

    def _apply_filter(self, text: str) -> None:
        needle = text.strip().lower()
        for feature, row, _checkbox in self.rows:
            visible = not needle or needle in feature.label.lower() or needle in feature.description.lower()
            row.setVisible(visible)

    def get_selected(self) -> list[str]:
        result: list[str] = []
        for feature, _row, checkbox in self.rows:
            if checkbox.isChecked():
                result.append(feature.id)
        return result
