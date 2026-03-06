from __future__ import annotations

import pytest

from installer_framework.config.models import ActionConfig, FeatureConfig, FieldConfig
from installer_framework.config.validation import ConfigValidationError, validate_config_semantics, validate_field_value
from installer_framework.plugins.registry import build_registry_with_builtins
from tests.helpers.context_factory import make_config


def _cfg(tmp_path):
    return make_config(tmp_path)


def test_validate_semantics_duplicate_step_ids(tmp_path):
    cfg = _cfg(tmp_path)
    cfg.steps[1].id = cfg.steps[0].id
    with pytest.raises(ConfigValidationError, match="Step ids must be unique"):
        validate_config_semantics(cfg)


def test_validate_semantics_missing_required_step(tmp_path):
    cfg = _cfg(tmp_path)
    cfg.steps = [step for step in cfg.steps if step.type != "install"]
    with pytest.raises(ConfigValidationError, match="Required step type missing"):
        validate_config_semantics(cfg)


def test_validate_semantics_ask_requires_scope(tmp_path):
    cfg = _cfg(tmp_path)
    cfg.install_scope = "ask"
    cfg.steps = [step for step in cfg.steps if step.type != "scope"]
    with pytest.raises(ConfigValidationError, match="requires a scope step"):
        validate_config_semantics(cfg)


def test_validate_semantics_duplicate_field_ids(tmp_path):
    cfg = _cfg(tmp_path)
    directory_step = next(step for step in cfg.steps if step.type == "directory")
    directory_step.fields.append(directory_step.fields[0])
    with pytest.raises(ConfigValidationError, match="Duplicate field ids"):
        validate_config_semantics(cfg)


def test_validate_semantics_empty_feature_id(tmp_path):
    cfg = _cfg(tmp_path)
    cfg.features = [FeatureConfig(id="", label="X")]
    with pytest.raises(ConfigValidationError, match="Feature id may not be empty"):
        validate_config_semantics(cfg)


def test_validate_semantics_requires_actions(tmp_path):
    cfg = _cfg(tmp_path)
    cfg.actions = []
    with pytest.raises(ConfigValidationError, match="At least one install action"):
        validate_config_semantics(cfg)


def test_validate_semantics_invalid_rollback_policy(tmp_path):
    cfg = _cfg(tmp_path)
    cfg.actions = [ActionConfig(type="show_message", rollback="bad", params={"message": "x"})]
    with pytest.raises(ConfigValidationError, match="Unsupported rollback policy"):
        validate_config_semantics(cfg, registry=build_registry_with_builtins())


def test_validate_semantics_run_script_type_checks(tmp_path):
    cfg = _cfg(tmp_path)
    cfg.actions = [ActionConfig(type="run_script", rollback="auto", params={"path": "x.py", "undo_path": 1})]
    with pytest.raises(ConfigValidationError, match="undo_path"):
        validate_config_semantics(cfg, registry=build_registry_with_builtins())

    cfg.actions = [
        ActionConfig(type="run_script", rollback="auto", params={"path": "x.py", "undo_path": "u.py", "uninstall_path": 1})
    ]
    with pytest.raises(ConfigValidationError, match="uninstall_path"):
        validate_config_semantics(cfg, registry=build_registry_with_builtins())


def test_validate_semantics_write_dotfile_append_and_legacy(tmp_path):
    cfg = _cfg(tmp_path)
    cfg.actions = [ActionConfig(type="write_dotfile", params={"target_path": "x", "append": "yes"})]
    with pytest.raises(ConfigValidationError, match="append"):
        validate_config_semantics(cfg, registry=build_registry_with_builtins())

    cfg.actions = [ActionConfig(type="write_dotfile", params={"target_path": "x", "scope": "user"})]
    with pytest.raises(ConfigValidationError, match="legacy keys"):
        validate_config_semantics(cfg, registry=build_registry_with_builtins())


def test_validate_semantics_copy_files_manifest_contract(tmp_path):
    cfg = _cfg(tmp_path)
    cfg.actions = [ActionConfig(type="copy_files", params={})]
    with pytest.raises(ConfigValidationError, match="manifest_file"):
        validate_config_semantics(cfg, registry=build_registry_with_builtins())

    cfg.actions = [ActionConfig(type="copy_files", params={"manifest_file": "x.json", "items": []})]
    with pytest.raises(ConfigValidationError, match="legacy keys"):
        validate_config_semantics(cfg, registry=build_registry_with_builtins())

    cfg.actions = [ActionConfig(type="copy_files", params={"manifest_file": "x.json", "overwrite": False})]
    with pytest.raises(ConfigValidationError, match="legacy keys"):
        validate_config_semantics(cfg, registry=build_registry_with_builtins())


def test_validate_semantics_uninstall_policy_and_unix_links(tmp_path):
    cfg = _cfg(tmp_path)
    cfg.uninstall.modified_file_policy = "invalid"
    with pytest.raises(ConfigValidationError, match="modified_file_policy"):
        validate_config_semantics(cfg)

    cfg = _cfg(tmp_path)
    cfg.uninstall.unix.user_link_path = "   "
    with pytest.raises(ConfigValidationError, match="user_link_path"):
        validate_config_semantics(cfg)


def test_validate_semantics_theme_checks(tmp_path):
    cfg = _cfg(tmp_path)
    cfg.theme.style = "bad"
    with pytest.raises(ConfigValidationError, match="theme.style"):
        validate_config_semantics(cfg)

    cfg = _cfg(tmp_path)
    cfg.theme.colors.accent = "not-a-color"
    with pytest.raises(ConfigValidationError, match="Invalid theme color"):
        validate_config_semantics(cfg)

    cfg = _cfg(tmp_path)
    cfg.theme.metrics.button_height = 0
    with pytest.raises(ConfigValidationError, match="Theme metric"):
        validate_config_semantics(cfg)

    cfg = _cfg(tmp_path)
    cfg.theme.typography.base_size = 0
    with pytest.raises(ConfigValidationError, match="typography sizes"):
        validate_config_semantics(cfg)


def test_validate_field_value_additional_paths(monkeypatch):
    from installer_framework.config import validation as mod
    field = mod.FieldConfig(id="p", type="text", label="Path", validators=["path_writable"])
    monkeypatch.setattr(mod, "is_writable", lambda _path: False)
    ok, message = validate_field_value(field, "/tmp/x")
    assert ok is False
    assert "not writable" in message

    field2 = mod.FieldConfig(id="d", type="text", label="Dir", validators=["dir_exists_or_create"])

    def _boom(_path):
        raise RuntimeError("nope")

    monkeypatch.setattr(mod, "ensure_dir", _boom)
    ok, message = validate_field_value(field2, "/tmp/y")
    assert ok is False
    assert "Unable to create" in message


def test_validate_semantics_unknown_step_and_missing_run_script_undo(tmp_path):
    cfg = _cfg(tmp_path)
    cfg.install_scope = "user"
    cfg.steps[2].type = "custom_missing"
    with pytest.raises(ConfigValidationError, match="Unknown step type"):
        validate_config_semantics(cfg, registry=build_registry_with_builtins())

    cfg = _cfg(tmp_path)
    cfg.actions = [ActionConfig(type="run_script", rollback="auto", params={"path": "hook.py"})]
    with pytest.raises(ConfigValidationError, match="requires 'undo_path'"):
        validate_config_semantics(cfg, registry=build_registry_with_builtins())


def test_validate_field_value_required_max_and_regex():
    required_field = FieldConfig(id="a", type="text", label="A", required=True)
    ok, msg = validate_field_value(required_field, "   ")
    assert ok is False
    assert "required" in msg

    max_field = FieldConfig(id="b", type="text", label="B", max_length=2)
    ok, msg = validate_field_value(max_field, "abc")
    assert ok is False
    assert "Maximum length" in msg

    regex_field = FieldConfig(id="c", type="text", label="C", regex=r"^\d+$")
    ok, msg = validate_field_value(regex_field, "abc")
    assert ok is False
    assert "required pattern" in msg
