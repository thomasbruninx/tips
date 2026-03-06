"""Manifest-driven uninstall runner."""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Any

from installer_framework.engine.manifest import file_sha256, load_json, manifest_path, tips_meta_dir
from installer_framework.engine.rollback import remove_empty_parents

PromptCallback = Callable[[Path, str], str]
ProgressCallback = Callable[[int, str], None]
LogCallback = Callable[[str], None]


@dataclass(slots=True)
class UninstallOptions:
    silent: bool = False
    delete_modified: bool = False
    modified_file_policy: str = "prompt"


@dataclass(slots=True)
class UninstallResult:
    success: bool
    cancelled: bool
    removed: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class UninstallAborted(RuntimeError):
    """Raised when interactive uninstall is aborted by user."""


class UninstallRunner:
    def __init__(self, manifest_file: Path, options: UninstallOptions) -> None:
        self.manifest_file = manifest_file
        self.options = options
        self.payload = load_json(manifest_file, default={})

    def _handle_modified(self, path: Path, operation: str, prompt_callback: PromptCallback | None, log: LogCallback) -> str:
        if self.options.delete_modified:
            return "apply"

        policy = self.options.modified_file_policy
        if self.options.silent:
            if policy == "delete":
                return "apply"
            return "skip"

        if policy == "skip":
            return "skip"
        if policy == "delete":
            return "apply"

        if prompt_callback:
            choice = prompt_callback(path, operation)
            if choice in {"delete", "restore", "apply"}:
                return "apply"
            if choice == "abort":
                return "abort"
            return "skip"

        return "skip"

    def _restore_or_delete_file(
        self,
        record: dict[str, Any],
        removed: list[str],
        skipped: list[str],
        prompt_callback: PromptCallback | None,
        log: LogCallback,
    ) -> None:
        path = Path(record["path"])
        existed_before = bool(record.get("existed_before", False))
        backup_path = record.get("backup_path")
        expected_hash = record.get("hash_after")

        if not path.exists() and not (existed_before and backup_path and Path(backup_path).exists()):
            return

        operation = "restore" if existed_before and backup_path else "delete"
        if path.exists() and path.is_file() and expected_hash:
            try:
                current_hash = file_sha256(path)
            except Exception:  # noqa: BLE001
                current_hash = None
            if current_hash and current_hash != expected_hash:
                decision = self._handle_modified(path, operation, prompt_callback, log)
                if decision == "abort":
                    raise UninstallAborted(f"Uninstall aborted for modified file: {path}")
                if decision == "skip":
                    skipped.append(str(path))
                    log(f"Skipped modified file: {path}")
                    return

        if existed_before and backup_path:
            backup = Path(backup_path)
            if backup.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(backup.read_bytes())
                removed.append(str(path))
                log(f"Restored original file: {path}")
                return
            skipped.append(str(path))
            log(f"Skipped restore for {path}: backup missing")
            return

        if existed_before and not backup_path:
            skipped.append(str(path))
            log(f"Skipped restore for {path}: no backup available")
            return

        if path.exists():
            if path.is_dir():
                import shutil

                shutil.rmtree(path, ignore_errors=True)
            else:
                path.unlink(missing_ok=True)
            removed.append(str(path))
            log(f"Removed file: {path}")

    def _restore_or_delete_registry(self, record: dict[str, Any], log: LogCallback) -> None:
        try:
            import winreg
        except ImportError:
            log("winreg unavailable; skipping registry uninstall step")
            return

        hive_name = record.get("hive", "HKCU")
        hive = winreg.HKEY_CURRENT_USER if hive_name == "HKCU" else winreg.HKEY_LOCAL_MACHINE
        key_path = record["key_path"]
        value_name = record.get("value_name", "")

        existed_before = bool(record.get("existed_before", False))
        old_value = record.get("old_value")
        old_type_name = record.get("old_type")

        with winreg.CreateKeyEx(hive, key_path, 0, winreg.KEY_WRITE) as key:
            if existed_before and old_type_name is not None:
                reg_type = getattr(winreg, old_type_name)
                winreg.SetValueEx(key, value_name, 0, reg_type, old_value)
                log(f"Restored registry value: {hive_name}\\{key_path}::{value_name}")
            else:
                try:
                    winreg.DeleteValue(key, value_name)
                    log(f"Deleted registry value: {hive_name}\\{key_path}::{value_name}")
                except OSError:
                    pass

    def _run_uninstall_hook(self, record: dict[str, Any], log: LogCallback) -> None:
        script = record.get("uninstall_path") or record.get("undo_path")
        if not script:
            return
        path = Path(script)
        if not path.is_absolute():
            path = (self.manifest_file.parent / path).resolve()
        if not path.exists():
            log(f"Uninstall hook missing: {path}")
            return

        proc = subprocess.run(
            [sys.executable, str(path)],
            cwd=str(path.parent),
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.stdout.strip():
            log(proc.stdout.strip())
        if proc.returncode != 0:
            raise RuntimeError(f"Uninstall hook failed: {path}: {proc.stderr.strip()}")

    def _remove_windows_arp(self, uninstall_meta: dict[str, Any], log: LogCallback) -> None:
        arp = uninstall_meta.get("windows_arp")
        if not isinstance(arp, dict):
            return
        try:
            import winreg
        except ImportError:
            return

        root = arp.get("root_hive", "HKCU")
        hive = winreg.HKEY_CURRENT_USER if root == "HKCU" else winreg.HKEY_LOCAL_MACHINE
        key_path = arp.get("key_path")
        if not key_path:
            return
        try:
            winreg.DeleteKey(hive, key_path)
            log(f"Removed ARP entry: {root}\\{key_path}")
        except OSError:
            pass

    def run(
        self,
        progress_callback: ProgressCallback,
        log_callback: LogCallback,
        prompt_callback: PromptCallback | None = None,
    ) -> UninstallResult:
        if not self.manifest_file.exists():
            return UninstallResult(success=False, cancelled=False, errors=[f"Manifest not found: {self.manifest_file}"])

        artifacts = self.payload.get("artifacts", [])
        uninstall_meta = self.payload.get("uninstall", {}) or {}
        if not isinstance(artifacts, list):
            artifacts = []

        removed: list[str] = []
        skipped: list[str] = []
        errors: list[str] = []
        total = max(len(artifacts), 1)

        try:
            for idx, record in enumerate(reversed(artifacts), start=1):
                if not isinstance(record, dict):
                    continue
                kind = record.get("kind")
                try:
                    if kind == "file":
                        self._restore_or_delete_file(record, removed, skipped, prompt_callback, log_callback)
                    elif kind == "registry_value":
                        self._restore_or_delete_registry(record, log_callback)
                    elif kind == "script_hook":
                        self._run_uninstall_hook(record, log_callback)
                except UninstallAborted as exc:
                    return UninstallResult(success=False, cancelled=True, removed=removed, skipped=skipped, errors=[str(exc)])
                except Exception as exc:  # noqa: BLE001
                    errors.append(str(exc))
                    log_callback(f"uninstall error: {exc}")

                progress_callback(int((idx / total) * 90), f"Processed uninstall record {idx}/{total}")

            # Remove uninstall launchers/scripts last.
            script_path_value = uninstall_meta.get("unix_script_path")
            symlink_value = uninstall_meta.get("unix_symlink_path")
            for value in (symlink_value, script_path_value):
                if not value:
                    continue
                path = Path(value)
                try:
                    if path.resolve() == Path(sys.argv[0]).resolve():
                        log_callback(f"Skipping removal of currently running launcher: {path}")
                        continue
                except Exception:
                    pass
                if path.exists() or path.is_symlink():
                    path.unlink(missing_ok=True)
                    removed.append(str(path))

            win_uninstaller = uninstall_meta.get("windows_uninstaller_path")
            if win_uninstaller:
                win_path = Path(win_uninstaller)
                try:
                    if win_path.resolve() != Path(sys.argv[0]).resolve():
                        win_path.unlink(missing_ok=True)
                        removed.append(str(win_path))
                    else:
                        skipped.append(str(win_path))
                except Exception:
                    skipped.append(str(win_path))

            self._remove_windows_arp(uninstall_meta, log_callback)

            # Remove manifest metadata last.
            meta_dir = tips_meta_dir(self.payload.get("install_dir") or self.manifest_file.parent.parent)
            if self.manifest_file.exists():
                self.manifest_file.unlink(missing_ok=True)
            journal = meta_dir / "rollback_journal.json"
            journal.unlink(missing_ok=True)
            backups = meta_dir / "backups"
            if backups.exists():
                import shutil

                shutil.rmtree(backups, ignore_errors=True)
            try:
                meta_dir.rmdir()
            except OSError:
                pass

            install_dir = Path(self.payload.get("install_dir") or meta_dir.parent)
            remove_empty_parents(install_dir, install_dir.parent)

            progress_callback(100, "Uninstall complete")
            return UninstallResult(success=not errors, cancelled=False, removed=removed, skipped=skipped, errors=errors)
        except Exception as exc:  # noqa: BLE001
            errors.append(str(exc))
            return UninstallResult(success=False, cancelled=False, removed=removed, skipped=skipped, errors=errors)


def default_manifest_from_install_dir(install_dir: str | Path) -> Path:
    return manifest_path(install_dir)
