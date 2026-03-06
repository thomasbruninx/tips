"""Windows registry actions."""

from __future__ import annotations

from typing import Any

from installer_framework.engine.action_base import Action
from installer_framework.engine.context import InstallerContext


_HIVE_MAP = {
    "HKCU": "HKEY_CURRENT_USER",
    "HKLM": "HKEY_LOCAL_MACHINE",
}


def _reg_type_name(winreg_module, reg_type: int) -> str:
    for attr in (
        "REG_SZ",
        "REG_EXPAND_SZ",
        "REG_DWORD",
        "REG_QWORD",
        "REG_BINARY",
        "REG_MULTI_SZ",
    ):
        if getattr(winreg_module, attr, None) == reg_type:
            return attr
    return "REG_SZ"


class WriteRegistryAction(Action):
    def __init__(self, params: dict[str, Any]) -> None:
        self.params = params

    def execute(self, ctx: InstallerContext, progress, log) -> dict:
        if not ctx.env.is_windows:
            log("write_registry skipped on non-Windows platform")
            return {"action": "write_registry", "skipped": True}

        try:
            import winreg
        except ImportError as exc:
            raise RuntimeError("pywin32/winreg support not available") from exc

        default_hive = "HKLM" if ctx.state.install_scope == "system" else "HKCU"
        hive_name = self.params.get("hive", default_hive)
        value_type = self.params.get("value_type", "REG_SZ")
        key_path = self.params["key_path"]
        value_name = self.params.get("value_name", "")
        value = self.params.get("value")

        resolved_value = str(value).format(
            install_dir=ctx.state.install_dir,
            scope=ctx.state.install_scope,
            version=ctx.config.branding.version,
        )

        hive = getattr(winreg, _HIVE_MAP.get(hive_name, hive_name))
        reg_type = getattr(winreg, value_type)

        existed_before = False
        old_value: Any = None
        old_type_name: str | None = None
        try:
            with winreg.OpenKey(hive, key_path, 0, winreg.KEY_READ) as key:
                old_value, old_type = winreg.QueryValueEx(key, value_name)
                existed_before = True
                old_type_name = _reg_type_name(winreg, old_type)
        except OSError:
            existed_before = False

        with winreg.CreateKeyEx(hive, key_path, 0, winreg.KEY_WRITE) as key:
            winreg.SetValueEx(key, value_name, 0, reg_type, resolved_value)

        progress(100, f"Registry updated {hive_name}\\{key_path}")
        log(f"Registry value '{value_name}' written in {hive_name}\\{key_path}")
        return {
            "action": "write_registry",
            "hive": hive_name,
            "key_path": key_path,
            "value_name": value_name,
            "rollback_records": [
                {
                    "kind": "registry_value",
                    "hive": hive_name,
                    "key_path": key_path,
                    "value_name": value_name,
                    "existed_before": existed_before,
                    "old_value": old_value,
                    "old_type": old_type_name,
                }
            ],
        }


class ReadRegistryAction(Action):
    def __init__(self, params: dict[str, Any]) -> None:
        self.params = params

    def execute(self, ctx: InstallerContext, progress, log) -> dict:
        if not ctx.env.is_windows:
            return {"action": "read_registry", "skipped": True}

        try:
            import winreg
        except ImportError as exc:
            raise RuntimeError("pywin32/winreg support not available") from exc

        default_hive = "HKLM" if ctx.state.install_scope == "system" else "HKCU"
        hive_name = self.params.get("hive", default_hive)
        key_path = self.params["key_path"]
        value_name = self.params.get("value_name", "")

        hive = getattr(winreg, _HIVE_MAP.get(hive_name, hive_name))
        value: Any = None
        try:
            with winreg.OpenKey(hive, key_path, 0, winreg.KEY_READ) as key:
                value, _ = winreg.QueryValueEx(key, value_name)
                log(f"Read registry value {hive_name}\\{key_path}::{value_name}")
        except OSError:
            log(f"Registry key/value not found: {hive_name}\\{key_path}::{value_name}")

        progress(100, "Registry read complete")
        output_key = self.params.get("output_key")
        if output_key:
            ctx.state.answers[output_key] = value
        return {
            "action": "read_registry",
            "hive": hive_name,
            "key_path": key_path,
            "value_name": value_name,
            "value": value,
        }
