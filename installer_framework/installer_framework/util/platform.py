"""Platform/environment helpers."""

from __future__ import annotations

import os
import platform
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class EnvironmentInfo:
    """Resolved environment details used by the installer runtime."""

    os_name: str
    arch: str
    python_version: str
    home_dir: Path
    is_windows: bool
    is_linux: bool
    is_macos: bool



def get_environment_info() -> EnvironmentInfo:
    system = platform.system().lower()
    return EnvironmentInfo(
        os_name=system,
        arch=platform.machine(),
        python_version=sys.version.split()[0],
        home_dir=Path.home(),
        is_windows=system == "windows",
        is_linux=system == "linux",
        is_macos=system == "darwin",
    )



def get_env_var(name: str, default: str = "") -> str:
    """Return an environment variable value with fallback."""
    return os.environ.get(name, default)
