"""Resource loading helpers with PyInstaller compatibility."""

from __future__ import annotations

import sys
from pathlib import Path



def package_root() -> Path:
    return Path(__file__).resolve().parents[2]



def resource_path(relative_path: str) -> Path:
    """Resolve assets both from source and PyInstaller bundle."""
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return Path(meipass) / relative_path
    return package_root() / relative_path
