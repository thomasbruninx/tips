"""Privilege detection and optional relaunch helpers."""

from __future__ import annotations

import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Sequence



def is_admin_windows() -> bool:
    """Return True when process has administrator token on Windows."""
    try:
        import ctypes

        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False



def is_root_unix() -> bool:
    """Return True for root UID on Unix."""
    return hasattr(os, "geteuid") and os.geteuid() == 0



def has_elevated_privileges() -> bool:
    if sys.platform.startswith("win"):
        return is_admin_windows()
    return is_root_unix()



def relaunch_as_admin_windows(argv: Sequence[str]) -> bool:
    """Attempt Windows UAC elevation through ShellExecuteW runas."""
    try:
        import ctypes

        script = Path(sys.executable)
        params = " ".join(argv)
        result = ctypes.windll.shell32.ShellExecuteW(None, "runas", str(script), params, None, 1)
        return result > 32
    except Exception:
        return False



def relaunch_with_sudo_unix(argv: Sequence[str]) -> bool:
    """Attempt Unix sudo relaunch. Returns True if launch command succeeded."""
    cmd = ["sudo", sys.executable, *argv]
    try:
        completed = subprocess.run(cmd, check=False)
        return completed.returncode == 0
    except Exception:
        return False


def _normalized_python_relaunch_args(argv: Sequence[str]) -> list[str]:
    """Normalize argv for python interpreter relaunch in source runs."""
    args = list(argv)
    is_frozen = bool(getattr(sys, "frozen", False) or getattr(sys, "_MEIPASS", None))
    if is_frozen:
        return args
    if not args:
        return ["-m", "installer_framework.main"]
    first = args[0]
    if first in {"-m", "-c"}:
        return args
    if first.startswith("-"):
        return ["-m", "installer_framework.main", *args]
    return args


def relaunch_as_admin_macos(argv: Sequence[str]) -> bool:
    """Attempt macOS elevation through AppleScript administrator privileges."""
    args = _normalized_python_relaunch_args(argv)
    command = " ".join(shlex.quote(token) for token in [sys.executable, *args])
    escaped = command.replace("\\", "\\\\").replace('"', '\\"')
    script = f'do shell script "{escaped}" with administrator privileges'
    try:
        completed = subprocess.run(["osascript", "-e", script], check=False)
        return completed.returncode == 0
    except Exception:
        return False
