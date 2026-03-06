from __future__ import annotations

import pytest

from installer_framework.config.models import ActionConfig, FieldConfig
from installer_framework.config.validation import ConfigValidationError, validate_config_semantics, validate_field_value
from installer_framework.plugins.registry import build_registry_with_builtins
from tests.helpers.context_factory import make_config


def test_validate_field_value_regex_and_length():
    field = FieldConfig(id="name", type="text", label="Name", required=True, regex=r"^[a-z]+$", min_length=2)
    ok, msg = validate_field_value(field, "A")
    assert ok is False
    assert msg


def test_validate_config_semantics_rejects_unknown_action(tmp_path):
    cfg = make_config(tmp_path)
    cfg.actions = [ActionConfig(type="missing_action", params={})]
    with pytest.raises(ConfigValidationError):
        validate_config_semantics(cfg, registry=build_registry_with_builtins())


def test_validate_config_semantics_write_dotfile_v2_contract(tmp_path):
    cfg = make_config(tmp_path)
    cfg.actions = [ActionConfig(type="write_dotfile", params={"target_path": ""})]
    with pytest.raises(ConfigValidationError):
        validate_config_semantics(cfg, registry=build_registry_with_builtins())
