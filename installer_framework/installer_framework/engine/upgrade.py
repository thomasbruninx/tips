"""Upgrade detection across Windows/Linux/macOS."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from installer_framework.app.paths import system_config_dir, user_config_dir
from installer_framework.engine.context import InstallerContext
from installer_framework.engine.versioning import compare_versions



def _detect_windows_registry(ctx: InstallerContext) -> dict[str, Any] | None:
    try:
        import winreg
    except ImportError:
        return None

    hive = winreg.HKEY_LOCAL_MACHINE if ctx.state.install_scope == "system" else winreg.HKEY_CURRENT_USER
    key_path = f"Software\\{ctx.config.branding.publisher}\\{ctx.config.product_id}"

    try:
        with winreg.OpenKey(hive, key_path, 0, winreg.KEY_READ) as key:
            version, _ = winreg.QueryValueEx(key, "Version")
            install_dir, _ = winreg.QueryValueEx(key, "InstallDir")
            scope, _ = winreg.QueryValueEx(key, "Scope")
            return {"version": version, "install_dir": install_dir, "scope": scope, "source": "registry"}
    except OSError:
        return None



def _metadata_file(ctx: InstallerContext, scope: str) -> Path:
    store_name = ctx.config.upgrade.store_file or "install-info.json"
    base = system_config_dir(ctx.config.product_id) if scope == "system" else user_config_dir(ctx.config.product_id)
    return base / store_name



def _detect_unix_file(ctx: InstallerContext) -> dict[str, Any] | None:
    for scope in (ctx.state.install_scope, "system", "user"):
        path = _metadata_file(ctx, scope)
        if path.exists():
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            payload["source"] = str(path)
            return payload
    return None



def detect_existing_install(ctx: InstallerContext) -> dict[str, Any] | None:
    if not ctx.config.upgrade.enabled:
        return None

    if ctx.env.is_windows:
        detected = _detect_windows_registry(ctx)
    else:
        detected = _detect_unix_file(ctx)

    if not detected:
        return None

    detected["comparison_to_current"] = compare_versions(
        str(detected.get("version", "0")),
        ctx.config.branding.version,
    )
    return detected
