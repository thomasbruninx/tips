"""Install path resolution based on scope + platform."""

from __future__ import annotations

import os
import re
from pathlib import Path

from installer_framework.util.platform import get_environment_info



def to_product_id(product_name: str) -> str:
    """Convert product name to filesystem-safe identifier."""
    text = product_name.strip().lower()
    return re.sub(r"[^a-z0-9._-]+", "-", text).strip("-") or "product"



def default_install_dir(product_name: str, scope: str, prefer_program_files_x86: bool = False) -> Path:
    env = get_environment_info()
    product_id = to_product_id(product_name)

    if env.is_windows:
        if scope == "system":
            key = "ProgramFiles(x86)" if prefer_program_files_x86 else "ProgramFiles"
            base = os.environ.get(key) or os.environ.get("ProgramFiles", r"C:\\Program Files")
            return Path(base) / product_name
        local_app_data = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or str(Path.home())
        return Path(local_app_data) / product_name

    if env.is_linux:
        if scope == "system":
            base = Path("/opt")
            return base / product_id
        return Path.home() / ".local" / "share" / product_id

    if env.is_macos:
        if scope == "system":
            return Path("/Applications") / f"{product_name}.app"
        return Path.home() / "Applications" / f"{product_name}.app"

    return Path.home() / product_name



def user_config_dir(product_id: str) -> Path:
    env = get_environment_info()
    if env.is_windows:
        base = os.environ.get("APPDATA", str(Path.home()))
        return Path(base) / product_id
    if env.is_macos:
        return Path.home() / "Library" / "Application Support" / product_id
    return Path.home() / ".config" / product_id



def system_config_dir(product_id: str) -> Path:
    env = get_environment_info()
    if env.is_windows:
        base = os.environ.get("ProgramData", r"C:\\ProgramData")
        return Path(base) / product_id
    return Path("/etc") / product_id
