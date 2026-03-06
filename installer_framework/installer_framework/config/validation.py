"""Semantic validation beyond JSON schema."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from installer_framework.config.models import FieldConfig
from installer_framework.config.models import InstallerConfig
from installer_framework.util.fs import ensure_dir, is_writable


class ConfigValidationError(ValueError):
    """Raised when config content is semantically invalid."""


_HEX_COLOR_RE = re.compile(r"^#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")



def _validate_theme(config: InstallerConfig) -> None:
    theme = config.theme

    if theme.style not in {"classic", "modern"}:
        raise ConfigValidationError(f"Unsupported theme.style: {theme.style}")

    colors = theme.colors
    for name, value in (
        ("window_bg", colors.window_bg),
        ("panel_bg", colors.panel_bg),
        ("text_primary", colors.text_primary),
        ("border_light", colors.border_light),
        ("border_dark", colors.border_dark),
        ("accent", colors.accent),
    ):
        if not _HEX_COLOR_RE.match(value):
            raise ConfigValidationError(f"Invalid theme color '{name}': {value}")

    metrics = theme.metrics
    for name, value in (
        ("window_width", metrics.window_width),
        ("window_height", metrics.window_height),
        ("sidebar_width", metrics.sidebar_width),
        ("padding", metrics.padding),
        ("button_height", metrics.button_height),
    ):
        if value <= 0:
            raise ConfigValidationError(f"Theme metric '{name}' must be > 0")

    typography = theme.typography
    if typography.base_size <= 0 or typography.title_size <= 0:
        raise ConfigValidationError("Theme typography sizes must be > 0")



def validate_config_semantics(config: InstallerConfig) -> None:
    step_ids = {step.id for step in config.steps}
    if len(step_ids) != len(config.steps):
        raise ConfigValidationError("Step ids must be unique")

    step_types = {step.type for step in config.steps}
    for required in ("welcome", "license", "directory", "ready", "install", "finish"):
        if required not in step_types:
            raise ConfigValidationError(f"Required step type missing: {required}")

    if config.install_scope == "ask" and "scope" not in step_types:
        raise ConfigValidationError("install_scope='ask' requires a scope step")

    for step in config.steps:
        field_ids = {field.id for field in step.fields}
        if len(field_ids) != len(step.fields):
            raise ConfigValidationError(f"Duplicate field ids in step '{step.id}'")

    for feature in config.features:
        if not feature.id.strip():
            raise ConfigValidationError("Feature id may not be empty")

    if not config.actions:
        raise ConfigValidationError("At least one install action is required")

    for action in config.actions:
        if action.rollback not in {"auto", "delete_only", "none"}:
            raise ConfigValidationError(
                f"Unsupported rollback policy '{action.rollback}' for action type '{action.type}'"
            )

        if action.type != "write_dotfile":
            if action.type == "run_script" and action.rollback != "none":
                if "undo_path" not in action.params:
                    raise ConfigValidationError(
                        "run_script requires 'undo_path' unless rollback policy is set to 'none'"
                    )
            if action.type == "run_script":
                undo_path = action.params.get("undo_path")
                uninstall_path = action.params.get("uninstall_path")
                if undo_path is not None and not isinstance(undo_path, str):
                    raise ConfigValidationError("run_script 'undo_path' must be a string when provided")
                if uninstall_path is not None and not isinstance(uninstall_path, str):
                    raise ConfigValidationError("run_script 'uninstall_path' must be a string when provided")
            continue
        params = action.params
        target_path = params.get("target_path")
        if not isinstance(target_path, str) or not target_path.strip():
            raise ConfigValidationError("write_dotfile requires non-empty string 'target_path'")

        append_value = params.get("append")
        if append_value is not None and not isinstance(append_value, bool):
            raise ConfigValidationError("write_dotfile 'append' must be boolean when provided")

        legacy_keys = {"scope", "user_base", "system_base", "file_name"}
        used_legacy = sorted(k for k in legacy_keys if k in params)
        if used_legacy:
            raise ConfigValidationError(
                "write_dotfile no longer supports legacy keys: "
                + ", ".join(used_legacy)
                + ". Use 'target_path' instead."
            )

    if config.uninstall.modified_file_policy not in {"prompt", "skip", "delete"}:
        raise ConfigValidationError(
            "uninstall.modified_file_policy must be one of: prompt, skip, delete"
        )
    unix_settings = config.uninstall.unix
    for name, value in (
        ("uninstall.unix.user_link_path", unix_settings.user_link_path),
        ("uninstall.unix.system_link_path", unix_settings.system_link_path),
    ):
        if value is not None and not str(value).strip():
            raise ConfigValidationError(f"{name} must be a non-empty string when provided")

    _validate_theme(config)



def validate_field_value(field: FieldConfig, value: Any) -> tuple[bool, str | None]:
    """Validate one field value against configured built-in rules."""
    text = "" if value is None else str(value)

    if field.required and not text.strip():
        return False, "This field is required"

    if field.min_length is not None and len(text) < field.min_length:
        return False, f"Minimum length is {field.min_length}"

    if field.max_length is not None and len(text) > field.max_length:
        return False, f"Maximum length is {field.max_length}"

    if field.regex and text and not re.match(field.regex, text):
        return False, "Value does not match required pattern"

    for validator in field.validators:
        if validator == "path_writable":
            if not is_writable(Path(text)):
                return False, "Path is not writable"
        elif validator == "dir_exists_or_create":
            try:
                ensure_dir(Path(text))
            except Exception as exc:
                return False, f"Unable to create directory: {exc}"

    return True, None
