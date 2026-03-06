"""Options step: checkboxes, selects, and feature multi-select."""

from __future__ import annotations

from typing import Any

from PyQt6.QtWidgets import QCheckBox, QComboBox, QLabel

from installer_framework.config.conditions import evaluate_condition
from installer_framework.config.validation import validate_field_value
from installer_framework.ui.step_base import StepWidget
from installer_framework.ui.widgets.feature_list import FeatureListWidget


class OptionsStep(StepWidget):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.controls: dict[str, Any] = {}
        self.feature_list: FeatureListWidget | None = None

        group = self.widget_factory.create_group_box(title="Options")
        group.content_layout.addWidget(self.description_label(height=40))

        for field in self.step_config.fields:
            if not evaluate_condition(field.show_if, self.ctx.state):
                continue
            if field.type == "checkbox":
                row = self.widget_factory.create_checkbox_row(text=field.label, active=bool(field.default))
                self.controls[field.id] = row.checkbox
                group.content_layout.addWidget(row)
            elif field.type == "select":
                label = QLabel(field.label)
                label.setStyleSheet(f"color: {self.theme.text_primary};")
                combo = QComboBox()
                combo.addItems(field.choices)
                if field.default:
                    combo.setCurrentText(str(field.default))
                combo.setStyleSheet(
                    f"QComboBox {{ background-color: {self.theme.panel_bg}; color: {self.theme.text_primary}; border: 1px solid {self.theme.border_dark}; padding: 2px 4px; }}"
                )
                self.controls[field.id] = combo
                group.content_layout.addWidget(label)
                group.content_layout.addWidget(combo)
            elif field.type == "multiselect":
                label = QLabel(field.label)
                label.setStyleSheet(f"color: {self.theme.text_primary};")
                features = self.ctx.config.features or []
                self.feature_list = FeatureListWidget(features=features, selected=self.ctx.state.selected_features)
                self.controls[field.id] = self.feature_list
                group.content_layout.addWidget(label)
                group.content_layout.addWidget(self.feature_list, 1)

        self.main_layout.addWidget(group)

    def apply_state(self) -> None:
        for field in self.step_config.fields:
            control = self.controls.get(field.id)
            if control is None:
                continue
            current = self.ctx.state.answers.get(field.id, field.default)
            if field.type == "checkbox":
                control.setChecked(bool(current))
            elif field.type == "select" and current is not None:
                control.setCurrentText(str(current))

    def get_data(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        for field in self.step_config.fields:
            control = self.controls.get(field.id)
            if control is None:
                continue
            if field.type == "checkbox":
                data[field.id] = bool(control.isChecked())
            elif field.type == "select":
                data[field.id] = control.currentText()
            elif field.type == "multiselect" and self.feature_list:
                selected = self.feature_list.get_selected()
                data[field.id] = selected
                data["selected_features"] = selected
        return data

    def validate(self) -> tuple[bool, str | None]:
        for field in self.step_config.fields:
            control = self.controls.get(field.id)
            if control is None:
                continue
            if field.type == "checkbox":
                value = bool(control.isChecked())
            elif field.type == "select":
                value = control.currentText()
            elif field.type == "multiselect" and self.feature_list:
                value = self.feature_list.get_selected()
            else:
                continue
            ok, message = validate_field_value(field, value)
            if not ok:
                return False, f"{field.label}: {message}"
        return True, None
