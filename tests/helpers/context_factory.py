from __future__ import annotations

from pathlib import Path
from typing import Any

from installer_framework.config.models import InstallerConfig, installer_config_from_dict
from installer_framework.engine.context import InstallerContext, InstallerState
from installer_framework.plugins.registry import build_registry_with_builtins
from installer_framework.util.platform import EnvironmentInfo


def base_config_dict() -> dict[str, Any]:
    return {
        "product_id": "tips-test-app",
        "install_scope": "ask",
        "branding": {
            "productName": "TIPS Test App",
            "publisher": "TIPS",
            "version": "1.0.0",
        },
        "steps": [
            {"id": "welcome", "type": "welcome", "title": "Welcome"},
            {"id": "license", "type": "license", "title": "License", "license_path": "license.txt"},
            {"id": "scope", "type": "scope", "title": "Scope"},
            {
                "id": "directory",
                "type": "directory",
                "title": "Directory",
                "fields": [{"id": "install_dir", "type": "directory", "label": "Install Directory", "required": True}],
            },
            {"id": "ready", "type": "ready", "title": "Ready"},
            {"id": "install", "type": "install", "title": "Install"},
            {"id": "finish", "type": "finish", "title": "Finish"},
        ],
        "actions": [{"type": "show_message", "message": "ok"}],
        "features": [{"id": "core", "label": "Core", "default": True}],
        "theme": {"style": "classic"},
    }


def make_config(source_root: Path, overrides: dict[str, Any] | None = None) -> InstallerConfig:
    payload = base_config_dict()
    if overrides:
        payload.update(overrides)
    cfg = installer_config_from_dict(payload, source_root=source_root)
    cfg.plugin_registry = build_registry_with_builtins()
    return cfg


def default_env(*, os_name: str = "linux") -> EnvironmentInfo:
    return EnvironmentInfo(
        os_name=os_name,
        arch="x86_64",
        python_version="3.12.0",
        home_dir=Path.home(),
        is_windows=os_name == "windows",
        is_linux=os_name == "linux",
        is_macos=os_name == "darwin",
    )


def make_context(
    source_root: Path,
    *,
    install_dir: str | None = None,
    scope: str = "user",
    config_overrides: dict[str, Any] | None = None,
    env: EnvironmentInfo | None = None,
) -> InstallerContext:
    cfg = make_config(source_root=source_root, overrides=config_overrides)
    state = InstallerState(
        install_scope=scope,
        install_dir=install_dir or str(source_root / "install"),
        selected_features=["core"],
    )
    ctx = InstallerContext(config=cfg, state=state, env=env or default_env())
    return ctx
