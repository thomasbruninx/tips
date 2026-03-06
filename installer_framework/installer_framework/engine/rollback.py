"""Install transaction + rollback helpers."""

from __future__ import annotations

import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

from installer_framework.app.resources import resource_path
from installer_framework.engine.context import InstallerContext
from installer_framework.engine.manifest import (
    backups_dir,
    ensure_meta_layout,
    file_sha256,
    journal_path,
    load_json,
    manifest_path,
    save_json,
    tips_meta_dir,
    uninstall_script_path,
    utc_now_iso,
    WINDOWS_UNINSTALLER_NAME,
    windows_uninstaller_path,
)
from installer_framework.util.fs import ensure_dir, expand_user


class InstallCancelledError(RuntimeError):
    """Raised when cancellation was requested during installation."""


class InstallTransaction:
    """Collects reversible artifacts and applies rollback on failure/cancel."""

    def __init__(self, ctx: InstallerContext, log_callback) -> None:
        self.ctx = ctx
        self.log = log_callback
        self.install_dir = Path(ctx.state.install_dir)
        self.records: list[dict[str, Any]] = []
        self.rollback_errors: list[str] = []
        self.started_at = utc_now_iso()

    def start(self) -> None:
        ensure_meta_layout(self.install_dir)
        save_json(
            journal_path(self.install_dir),
            {
                "product_id": self.ctx.config.product_id,
                "install_dir": str(self.install_dir),
                "started_at": self.started_at,
                "records": [],
            },
        )

    def create_file_backup(self, path: Path) -> Path:
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(path)
        backup_root = backups_dir(self.install_dir)
        ensure_dir(backup_root)
        backup = backup_root / f"{uuid.uuid4().hex}.bak"
        shutil.copy2(path, backup)
        return backup

    def register_records(self, action_type: str, rollback_policy: str, records: list[dict[str, Any]] | None) -> None:
        if not records:
            return
        for record in records:
            rec = dict(record)
            rec.setdefault("action_type", action_type)
            rec.setdefault("rollback_policy", rollback_policy)
            self.records.append(rec)
        self._flush_journal()

    def _flush_journal(self) -> None:
        save_json(
            journal_path(self.install_dir),
            {
                "product_id": self.ctx.config.product_id,
                "install_dir": str(self.install_dir),
                "started_at": self.started_at,
                "updated_at": utc_now_iso(),
                "records": self.records,
            },
        )

    def _restore_or_delete_file(self, record: dict[str, Any], delete_only: bool = False) -> None:
        path = Path(record["path"])
        existed_before = bool(record.get("existed_before", False))
        backup_path = record.get("backup_path")

        if existed_before and not delete_only and backup_path:
            backup = Path(backup_path)
            if backup.exists():
                ensure_dir(path.parent)
                shutil.copy2(backup, path)
                return

        if existed_before and not delete_only and not backup_path:
            # We cannot safely restore overwritten content without a snapshot.
            self.log(f"rollback: skipped restore for {path} (no backup available)")
            return

        if path.exists():
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
            else:
                path.unlink(missing_ok=True)

    def _rollback_registry_value(self, record: dict[str, Any], delete_only: bool = False) -> None:
        if not self.ctx.env.is_windows:
            return
        try:
            import winreg
        except ImportError:
            self.log("rollback: winreg unavailable, skipping registry restore")
            return

        hive_name = record.get("hive", "HKCU")
        hive = winreg.HKEY_CURRENT_USER if hive_name == "HKCU" else winreg.HKEY_LOCAL_MACHINE
        key_path = record["key_path"]
        value_name = record.get("value_name", "")

        existed_before = bool(record.get("existed_before", False))
        old_value = record.get("old_value")
        old_type_name = record.get("old_type")

        try:
            with winreg.CreateKeyEx(hive, key_path, 0, winreg.KEY_WRITE) as key:
                if existed_before and not delete_only and old_type_name is not None:
                    reg_type = getattr(winreg, old_type_name)
                    winreg.SetValueEx(key, value_name, 0, reg_type, old_value)
                else:
                    try:
                        winreg.DeleteValue(key, value_name)
                    except OSError:
                        pass
        except OSError as exc:
            raise RuntimeError(f"Registry rollback failed for {hive_name}\\{key_path}::{value_name}: {exc}") from exc

    def _run_script_hook(self, script_path: str, phase: str) -> None:
        path = Path(script_path)
        if not path.is_absolute():
            path = (self.ctx.config.source_root / script_path).resolve()
        if not path.exists():
            self.log(f"rollback: script hook missing ({phase}): {path}")
            return

        proc = subprocess.run(
            [sys.executable, str(path)],
            cwd=str(self.ctx.config.source_root),
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.stdout.strip():
            self.log(proc.stdout.strip())
        if proc.returncode != 0:
            raise RuntimeError(f"Script {phase} hook failed ({path}): {proc.stderr.strip()}")

    def rollback(self) -> list[str]:
        for record in reversed(self.records):
            policy = record.get("rollback_policy", "auto")
            if policy == "none":
                continue
            delete_only = policy == "delete_only"
            kind = record.get("kind")

            try:
                if kind == "file":
                    self._restore_or_delete_file(record, delete_only=delete_only)
                elif kind == "registry_value":
                    self._rollback_registry_value(record, delete_only=delete_only)
                elif kind == "script_hook":
                    if policy != "none":
                        undo_path = record.get("undo_path")
                        if undo_path:
                            self._run_script_hook(undo_path, "undo")
            except Exception as exc:  # noqa: BLE001
                self.rollback_errors.append(str(exc))
                self.log(f"rollback error: {exc}")

        return self.rollback_errors

    def _register_windows_arp(self, manifest_file: Path, uninstaller_exe: Path) -> dict[str, Any] | None:
        if not self.ctx.env.is_windows:
            return None

        try:
            import winreg
        except ImportError:
            self.log("Unable to register ARP entry: winreg unavailable")
            return None

        root_hive_name = "HKLM" if self.ctx.state.install_scope == "system" else "HKCU"
        hive = winreg.HKEY_LOCAL_MACHINE if root_hive_name == "HKLM" else winreg.HKEY_CURRENT_USER
        key_path = (
            "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\"
            f"{self.ctx.config.product_id}"
        )

        uninstall_cmd = f'"{uninstaller_exe}" --manifest "{manifest_file}"'
        quiet_cmd = f"{uninstall_cmd} --silent"

        with winreg.CreateKeyEx(hive, key_path, 0, winreg.KEY_WRITE) as key:
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, self.ctx.config.branding.product_name)
            winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, self.ctx.config.branding.publisher)
            winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, self.ctx.config.branding.version)
            winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, str(self.install_dir))
            winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, uninstall_cmd)
            winreg.SetValueEx(key, "QuietUninstallString", 0, winreg.REG_SZ, quiet_cmd)

        return {
            "root_hive": root_hive_name,
            "key_path": key_path,
            "uninstall_string": uninstall_cmd,
            "quiet_uninstall_string": quiet_cmd,
        }

    def _write_unix_uninstall_script(self, manifest_file: Path) -> tuple[Path, Path | None]:
        script_path = uninstall_script_path(self.install_dir)
        ensure_dir(script_path.parent)
        script_template = """#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_MANIFEST = "__DEFAULT_MANIFEST__"


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def file_sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def prompt_modified(path: Path, operation: str) -> str:
    prompt = (
        "File was modified since install:\\n"
        + str(path)
        + "\\nOperation: "
        + operation
        + ". Choose [d]elete/[s]kip/[a]bort: "
    )
    while True:
        answer = input(prompt).strip().lower()
        if answer in {"d", "delete"}:
            return "delete"
        if answer in {"s", "skip"}:
            return "skip"
        if answer in {"a", "abort"}:
            return "abort"


def remove_empty_parents(start: Path, stop_at: Path) -> None:
    current = start
    stop_at_resolved = stop_at.resolve()
    while True:
        if not current.exists():
            current = current.parent
            continue
        if current.resolve() == stop_at_resolved:
            break
        try:
            current.rmdir()
        except OSError:
            break
        parent = current.parent
        if parent == current:
            break
        current = parent


def should_apply_modified(*, path: Path, operation: str, args: argparse.Namespace) -> str:
    if args.delete_modified:
        return "apply"
    if args.silent:
        return "apply" if args.modified_file_policy == "delete" else "skip"
    if args.modified_file_policy == "delete":
        return "apply"
    if args.modified_file_policy == "skip":
        return "skip"
    return prompt_modified(path, operation)


def restore_or_delete_file(record: dict, args: argparse.Namespace, removed: list[str], skipped: list[str]) -> None:
    path = Path(record["path"])
    try:
        if path.resolve() == Path(sys.argv[0]).resolve():
            skipped.append(str(path))
            print("Skipping currently running script:", path)
            return
    except Exception:
        pass
    existed_before = bool(record.get("existed_before", False))
    backup_path = record.get("backup_path")
    expected_hash = record.get("hash_after")

    if not path.exists() and not (existed_before and backup_path and Path(backup_path).exists()):
        return

    operation = "restore" if existed_before and backup_path else "delete"
    if path.exists() and path.is_file() and expected_hash:
        try:
            current_hash = file_sha256(path)
        except Exception:
            current_hash = None
        if current_hash and current_hash != expected_hash:
            decision = should_apply_modified(path=path, operation=operation, args=args)
            if decision in {"abort", "a"}:
                raise RuntimeError("Uninstall aborted by user.")
            if decision in {"skip", "s"}:
                skipped.append(str(path))
                print("Skipped modified file:", path)
                return

    if existed_before and backup_path:
        backup = Path(backup_path)
        if backup.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(backup.read_bytes())
            removed.append(str(path))
            print("Restored original file:", path)
            return
        skipped.append(str(path))
        print("Skipped restore (missing backup):", path)
        return

    if existed_before and not backup_path:
        skipped.append(str(path))
        print("Skipped restore (no backup):", path)
        return

    if path.exists():
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        else:
            path.unlink(missing_ok=True)
        removed.append(str(path))
        print("Removed file:", path)


def run_script_hook(record: dict) -> None:
    script = record.get("uninstall_path") or record.get("undo_path")
    if not script:
        return
    path = Path(script).expanduser()
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    if not path.exists():
        print("Uninstall hook missing:", path)
        return
    proc = subprocess.run([sys.executable, str(path)], cwd=str(path.parent), check=False, capture_output=True, text=True)
    if proc.stdout.strip():
        print(proc.stdout.strip())
    if proc.returncode != 0:
        raise RuntimeError("Uninstall hook failed: " + str(path))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TIPS uninstall script")
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST)
    parser.add_argument("--silent", action="store_true")
    parser.add_argument("--delete-modified", action="store_true")
    parser.add_argument("--modified-file-policy", choices=["prompt", "skip", "delete"], default="prompt")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_file = Path(args.manifest).expanduser().resolve()
    payload = load_json(manifest_file)
    if not manifest_file.exists() or not payload:
        print("Manifest not found or invalid:", manifest_file, file=sys.stderr)
        return 1

    artifacts = payload.get("artifacts", [])
    if not isinstance(artifacts, list):
        artifacts = []
    removed: list[str] = []
    skipped: list[str] = []

    try:
        for record in reversed(artifacts):
            if not isinstance(record, dict):
                continue
            kind = record.get("kind")
            if kind == "file":
                restore_or_delete_file(record, args, removed, skipped)
            elif kind == "script_hook":
                run_script_hook(record)

        uninstall_meta = payload.get("uninstall", {}) or {}
        script_path = uninstall_meta.get("unix_script_path")
        symlink_path = uninstall_meta.get("unix_symlink_path")
        for value in (symlink_path, script_path):
            if not value:
                continue
            path = Path(value)
            try:
                if path.resolve() == Path(sys.argv[0]).resolve():
                    continue
            except Exception:
                pass
            if path.exists() or path.is_symlink():
                path.unlink(missing_ok=True)

        meta_dir = manifest_file.parent
        manifest_file.unlink(missing_ok=True)
        (meta_dir / "rollback_journal.json").unlink(missing_ok=True)
        backups = meta_dir / "backups"
        if backups.exists():
            shutil.rmtree(backups, ignore_errors=True)
        try:
            meta_dir.rmdir()
        except OSError:
            pass

        install_dir = Path(payload.get("install_dir") or meta_dir.parent)
        remove_empty_parents(install_dir, install_dir.parent)
    except Exception as exc:
        print("Uninstall failed:", exc, file=sys.stderr)
        return 1

    print("Uninstall complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""
        script_content = script_template.replace("__DEFAULT_MANIFEST__", str(manifest_file))
        script_path.write_text(script_content, encoding="utf-8")
        script_path.chmod(0o755)

        link_path: Path | None = None
        unix_cfg = self.ctx.config.uninstall.unix
        if unix_cfg.create_symlink:
            if self.ctx.state.install_scope == "system":
                raw = unix_cfg.system_link_path or f"/usr/local/bin/{self.ctx.config.product_id}-uninstall"
            else:
                raw = unix_cfg.user_link_path or f"~/.local/bin/{self.ctx.config.product_id}-uninstall"
            link_path = expand_user(raw)
            ensure_dir(link_path.parent)
            if link_path.exists() or link_path.is_symlink():
                link_path.unlink(missing_ok=True)
            link_path.symlink_to(script_path)

        return script_path, link_path

    def _install_windows_uninstaller(self) -> Path | None:
        src = self._resolve_windows_uninstaller_source()
        if src is None:
            self.log("Windows uninstaller binary not found in any known location; skipping drop into install directory")
            return None
        dst = windows_uninstaller_path(self.install_dir)
        ensure_dir(dst.parent)
        shutil.copy2(src, dst)
        return dst

    def _resolve_windows_uninstaller_source(self) -> Path | None:
        candidates: list[Path] = []

        candidates.append(resource_path("tools/tips-uninstaller.exe"))
        candidates.append(Path.cwd() / "tools" / WINDOWS_UNINSTALLER_NAME)

        try:
            installer_runtime_dir = Path(sys.argv[0]).resolve().parent
        except Exception:
            installer_runtime_dir = None

        if installer_runtime_dir:
            candidates.append(installer_runtime_dir / WINDOWS_UNINSTALLER_NAME)

        candidates.append(Path("dist") / "windows" / WINDOWS_UNINSTALLER_NAME)

        for candidate in candidates:
            if candidate.exists():
                if candidate.is_file():
                    self.log(f"Using Windows uninstaller source: {candidate}")
                    return candidate
                self.log(f"Windows uninstaller path exists but is not a file: {candidate}")

        self.log("Windows uninstaller source candidates checked:")
        for candidate in candidates:
            self.log(f" - {candidate}")
        return None

    def finalize_success(self, action_results: list[dict[str, Any]]) -> Path:
        ensure_meta_layout(self.install_dir)

        manifest_file = manifest_path(self.install_dir)
        uninstall_meta: dict[str, Any] = {
            "enabled": self.ctx.config.uninstall.enabled,
            "modified_file_policy": self.ctx.config.uninstall.modified_file_policy,
        }

        if self.ctx.config.uninstall.enabled:
            if self.ctx.env.is_windows:
                win_uninstaller = self._install_windows_uninstaller()
                if win_uninstaller:
                    uninstall_meta["windows_uninstaller_path"] = str(win_uninstaller)
                    self.records.append(
                        {
                            "kind": "file",
                            "path": str(win_uninstaller),
                            "existed_before": False,
                            "hash_after": file_sha256(win_uninstaller),
                            "rollback_policy": "auto",
                            "action_type": "transaction",
                        }
                    )
                    arp = self._register_windows_arp(manifest_file, win_uninstaller)
                    if arp:
                        uninstall_meta["windows_arp"] = arp
                else:
                    self.log("Windows ARP registration skipped: bundled uninstaller executable was not found")
            else:
                script_path, link_path = self._write_unix_uninstall_script(manifest_file)
                uninstall_meta["unix_script_path"] = str(script_path)
                self.records.append(
                    {
                        "kind": "file",
                        "path": str(script_path),
                        "existed_before": False,
                        "hash_after": file_sha256(script_path),
                        "rollback_policy": "auto",
                        "action_type": "transaction",
                    }
                )
                if link_path:
                    uninstall_meta["unix_symlink_path"] = str(link_path)

        manifest = {
            "schema_version": 1,
            "product_id": self.ctx.config.product_id,
            "product_name": self.ctx.config.branding.product_name,
            "publisher": self.ctx.config.branding.publisher,
            "version": self.ctx.config.branding.version,
            "install_dir": str(self.install_dir),
            "scope": self.ctx.state.install_scope,
            "created_at": self.started_at,
            "updated_at": utc_now_iso(),
            "artifacts": self.records,
            "action_results": action_results,
            "uninstall": uninstall_meta,
        }
        save_json(manifest_file, manifest)

        journal = journal_path(self.install_dir)
        journal.unlink(missing_ok=True)
        return manifest_file

    def load_records_from_journal(self) -> list[dict[str, Any]]:
        payload = load_json(journal_path(self.install_dir), default={})
        records = payload.get("records", [])
        if isinstance(records, list):
            return [r for r in records if isinstance(r, dict)]
        return []


def remove_empty_parents(start: Path, stop_at: Path) -> None:
    """Remove empty parents from start up to stop_at (exclusive)."""
    current = start
    stop_at_resolved = stop_at.resolve()
    while True:
        if not current.exists():
            current = current.parent
            continue
        if current.resolve() == stop_at_resolved:
            break
        try:
            current.rmdir()
        except OSError:
            break
        parent = current.parent
        if parent == current:
            break
        current = parent
