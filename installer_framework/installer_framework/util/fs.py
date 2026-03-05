"""Filesystem helpers for installer actions and validation."""

from __future__ import annotations

import os
from pathlib import Path



def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path



def is_writable(path: Path) -> bool:
    target = path
    if not target.exists():
        target = target.parent
    try:
        ensure_dir(target)
        probe = target / ".tips_write_test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return True
    except Exception:
        return False



def expand_user(path: str) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(path))).resolve()
