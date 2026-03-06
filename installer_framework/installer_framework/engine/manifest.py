"""Manifest and transaction metadata helpers."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from installer_framework.util.fs import ensure_dir


META_DIR_NAME = ".tips"
MANIFEST_FILE_NAME = "manifest.json"
JOURNAL_FILE_NAME = "rollback_journal.json"
BACKUPS_DIR_NAME = "backups"
UNINSTALL_SCRIPT_NAME = "uninstall.py"
WINDOWS_UNINSTALLER_NAME = "tips-uninstaller.exe"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def tips_meta_dir(install_dir: str | Path) -> Path:
    return Path(install_dir) / META_DIR_NAME


def manifest_path(install_dir: str | Path) -> Path:
    return tips_meta_dir(install_dir) / MANIFEST_FILE_NAME


def journal_path(install_dir: str | Path) -> Path:
    return tips_meta_dir(install_dir) / JOURNAL_FILE_NAME


def backups_dir(install_dir: str | Path) -> Path:
    return tips_meta_dir(install_dir) / BACKUPS_DIR_NAME


def uninstall_script_path(install_dir: str | Path) -> Path:
    return tips_meta_dir(install_dir) / UNINSTALL_SCRIPT_NAME


def windows_uninstaller_path(install_dir: str | Path) -> Path:
    return Path(install_dir) / WINDOWS_UNINSTALLER_NAME


def ensure_meta_layout(install_dir: str | Path) -> None:
    ensure_dir(tips_meta_dir(install_dir))
    ensure_dir(backups_dir(install_dir))


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path, default: dict[str, Any] | None = None) -> dict[str, Any]:
    if not path.exists():
        return default or {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default or {}


def save_json(path: Path, payload: dict[str, Any]) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
