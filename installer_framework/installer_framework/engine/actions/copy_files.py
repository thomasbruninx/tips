"""copy_files action implementation."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from installer_framework.engine.action_base import Action
from installer_framework.engine.context import InstallerContext
from installer_framework.engine.manifest import file_sha256
from installer_framework.util.fs import ensure_dir


class CopyFilesAction(Action):
    def __init__(self, params: dict[str, Any]) -> None:
        self.params = params

    def _resolve_manifest_file(self, ctx: InstallerContext, manifest_file: str) -> Path:
        candidate = Path(manifest_file).expanduser()
        if candidate.is_absolute() and candidate.exists():
            return candidate

        local = (ctx.config.source_root / manifest_file).resolve()
        if local.exists():
            return local

        try:
            from installer_framework.app.resources import resource_path

            bundled = resource_path(manifest_file)
            if bundled.exists():
                return bundled
        except Exception:
            pass

        raise FileNotFoundError(f"copy_files manifest not found: {manifest_file}")

    def _load_manifest(self, manifest_path: Path) -> list[dict[str, Any]]:
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"copy_files manifest is not valid JSON: {manifest_path}: {exc}") from exc

        if not isinstance(payload, dict):
            raise ValueError("copy_files manifest must be a JSON object")

        version = payload.get("schema_version")
        if version != 1:
            raise ValueError("copy_files manifest must contain schema_version=1")

        files = payload.get("files")
        if not isinstance(files, list) or not files:
            raise ValueError("copy_files manifest must contain a non-empty 'files' array")

        normalized: list[dict[str, Any]] = []
        for index, entry in enumerate(files, start=1):
            if not isinstance(entry, dict):
                raise ValueError(f"copy_files manifest entry #{index} must be an object")
            source = entry.get("source")
            target = entry.get("target")
            overwrite = entry.get("overwrite", True)

            if not isinstance(source, str) or not source.strip():
                raise ValueError(f"copy_files manifest entry #{index} requires non-empty string 'source'")
            if not isinstance(target, str) or not target.strip():
                raise ValueError(f"copy_files manifest entry #{index} requires non-empty string 'target'")
            if not isinstance(overwrite, bool):
                raise ValueError(f"copy_files manifest entry #{index} 'overwrite' must be boolean when provided")

            normalized.append(
                {
                    "source": source,
                    "target": target,
                    "overwrite": overwrite,
                }
            )
        return normalized

    def _resolve_entry_source(self, ctx: InstallerContext, manifest_path: Path, source: str) -> Path:
        candidate = Path(source).expanduser()
        if candidate.is_absolute() and candidate.exists():
            return candidate

        from_manifest = (manifest_path.parent / source).resolve()
        if from_manifest.exists():
            return from_manifest

        from_source_root = (ctx.config.source_root / source).resolve()
        if from_source_root.exists():
            return from_source_root

        try:
            from installer_framework.app.resources import resource_path

            bundled = resource_path(source)
            if bundled.exists():
                return bundled
        except Exception:
            pass

        raise FileNotFoundError(f"copy_files source not found: {source}")

    def _resolve_target_path(self, install_dir: Path, target: str) -> Path:
        target_path = Path(target)
        if target_path.is_absolute():
            raise ValueError(f"copy_files target must be install-relative, got absolute path: {target}")

        install_root = install_dir.resolve()
        resolved = (install_root / target_path).resolve()
        try:
            resolved.relative_to(install_root)
        except ValueError as exc:
            raise ValueError(f"copy_files target escapes install_dir: {target}") from exc
        return resolved

    def _copy_path(
        self,
        src: Path,
        dst: Path,
        overwrite: bool,
        preserve_permissions: bool,
        records: list[dict[str, Any]],
        rollback_policy: str,
        ctx: InstallerContext,
    ) -> bool:
        if src.is_dir():
            raise ValueError(f"copy_files manifest source must be a file, not directory: {src}")
        if dst.exists() and not overwrite:
            return False

        existed_before = dst.exists()
        backup_path: str | None = None
        if existed_before and rollback_policy == "auto" and dst.is_file():
            tx = getattr(ctx, "transaction", None)
            if tx is not None:
                try:
                    backup_path = str(tx.create_file_backup(dst))
                except Exception:
                    backup_path = None

        ensure_dir(dst.parent)
        if preserve_permissions:
            shutil.copy2(src, dst)
        else:
            shutil.copy(src, dst)
        hash_after = file_sha256(dst) if dst.exists() and dst.is_file() else None
        records.append(
            {
                "kind": "file",
                "path": str(dst),
                "existed_before": existed_before,
                "backup_path": backup_path,
                "hash_after": hash_after,
            }
        )
        return True

    def execute(self, ctx: InstallerContext, progress, log) -> dict:
        install_dir = Path(ctx.state.install_dir)
        ensure_dir(install_dir)

        manifest_file = self.params.get("manifest_file")
        if not isinstance(manifest_file, str) or not manifest_file.strip():
            raise ValueError("copy_files action requires non-empty string 'manifest_file'")

        preserve_permissions = bool(self.params.get("preserve_permissions", True))
        rollback_policy = getattr(ctx, "action_rollback_policy", "auto")
        manifest_path = self._resolve_manifest_file(ctx, manifest_file)
        files = self._load_manifest(manifest_path)

        copied = 0
        skipped = 0
        total = len(files)
        records: list[dict[str, Any]] = []

        for index, item in enumerate(files, start=1):
            if ctx.is_cancelled():
                log("copy_files cancelled")
                break

            src = self._resolve_entry_source(ctx, manifest_path, item["source"])
            dst = self._resolve_target_path(install_dir, item["target"])
            overwrite = item["overwrite"]
            was_copied = self._copy_path(src, dst, overwrite, preserve_permissions, records, rollback_policy, ctx)
            if was_copied:
                copied += 1
                log(f"Copied '{src}' to '{dst}'")
            else:
                skipped += 1
                log(f"Skipped existing file (overwrite=false): '{dst}'")
            pct = int((index / total) * 100)
            progress(pct, f"Processed {index}/{total}: {dst}")

        return {
            "action": "copy_files",
            "copied_items": copied,
            "skipped_items": skipped,
            "install_dir": str(install_dir),
            "rollback_records": records,
        }
