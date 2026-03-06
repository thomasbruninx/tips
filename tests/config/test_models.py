from __future__ import annotations

from installer_framework.config.models import installer_config_from_dict


def test_step_params_preserved_for_plugin_fields(tmp_path):
    payload = {
        "install_scope": "ask",
        "branding": {"productName": "Demo", "publisher": "ACME", "version": "1.0.0"},
        "steps": [
            {"id": "welcome", "type": "welcome", "title": "Welcome"},
            {"id": "license", "type": "license", "title": "License", "license_path": "x"},
            {"id": "scope", "type": "scope", "title": "Scope"},
            {"id": "directory", "type": "directory", "title": "Dir", "fields": [{"id": "install_dir", "type": "directory", "label": "Dir"}]},
            {"id": "ready", "type": "ready", "title": "Ready"},
            {"id": "install", "type": "install", "title": "Install"},
            {"id": "finish", "type": "finish", "title": "Finish"},
            {"id": "plugin", "type": "preflight_step", "title": "Plugin", "ack_label": "ok", "required_ack": True},
        ],
        "actions": [{"type": "show_message", "message": "done"}],
    }
    cfg = installer_config_from_dict(payload, source_root=tmp_path)
    plugin_step = next(step for step in cfg.steps if step.id == "plugin")
    assert plugin_step.params["ack_label"] == "ok"
    assert plugin_step.params["required_ack"] is True


def test_modern_theme_defaults_are_applied(tmp_path):
    payload = {
        "install_scope": "user",
        "branding": {"productName": "Demo", "publisher": "ACME", "version": "1.0.0"},
        "theme": {"style": "modern"},
        "steps": [
            {"id": "welcome", "type": "welcome", "title": "Welcome"},
            {"id": "license", "type": "license", "title": "License", "license_path": "x"},
            {"id": "directory", "type": "directory", "title": "Dir", "fields": [{"id": "install_dir", "type": "directory", "label": "Dir"}]},
            {"id": "ready", "type": "ready", "title": "Ready"},
            {"id": "install", "type": "install", "title": "Install"},
            {"id": "finish", "type": "finish", "title": "Finish"},
        ],
        "actions": [{"type": "show_message", "message": "done"}],
    }
    cfg = installer_config_from_dict(payload, source_root=tmp_path)
    assert cfg.theme.colors.accent == "#0071E3"
    assert cfg.theme.typography.base_size == 13
