"""Installer action runner with progress/log/cancellation support."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from installer_framework.config.models import ActionConfig
from installer_framework.engine.context import InstallerContext
from installer_framework.engine.manifest import manifest_path
from installer_framework.engine.rollback import InstallCancelledError, InstallTransaction
from installer_framework.engine.uninstall_runner import UninstallOptions, UninstallRunner

ProgressCallback = Callable[[int, str], None]
LogCallback = Callable[[str], None]
MessageCallback = Callable[[str, str, str], None]


class ActionRunnerError(RuntimeError):
    """Action runner failure."""


@dataclass(slots=True)
class ActionResult:
    success: bool
    cancelled: bool
    results: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None
    rollback_performed: bool = False
    rollback_errors: list[str] = field(default_factory=list)
    manifest_path: str | None = None


class ActionRunner:
    """Executes configured actions sequentially."""

    def __init__(self, actions: list[ActionConfig]) -> None:
        self.actions = actions

    def _create_action(self, ctx: InstallerContext, cfg: ActionConfig):
        registry = ctx.plugin_registry or getattr(ctx.config, "plugin_registry", None)
        if registry is None:
            from installer_framework.plugins.registry import build_registry_with_builtins

            registry = build_registry_with_builtins()
            ctx.plugin_registry = registry
        cls = registry.get_action_class(cfg.type) if registry is not None else None
        if not cls:
            raise ActionRunnerError(f"Unsupported action type: {cfg.type}")
        return cls(cfg.params)

    def _resolve_upgrade_manifest(self, ctx: InstallerContext) -> Path | None:
        detected = ctx.state.detected_upgrade or {}
        install_dir = detected.get("install_dir")
        if isinstance(install_dir, str) and install_dir.strip():
            candidate = manifest_path(install_dir)
            if candidate.exists():
                return candidate

        candidate = manifest_path(ctx.state.install_dir)
        if candidate.exists():
            return candidate
        return None

    def _should_run_uninstall_first(self, ctx: InstallerContext) -> bool:
        return bool(ctx.state.detected_upgrade) and ctx.state.answers.get("upgrade_mode") == "uninstall_first"

    def _run_uninstall_first(
        self,
        ctx: InstallerContext,
        progress_callback: ProgressCallback,
        log_callback: LogCallback,
        progress_start: int,
        progress_end: int,
    ) -> dict[str, Any]:
        manifest_file = self._resolve_upgrade_manifest(ctx)
        if manifest_file is None:
            raise ActionRunnerError(
                "Uninstall-first mode selected, but no uninstall manifest was found for the existing installation."
            )

        options = UninstallOptions(
            silent=True,
            delete_modified=False,
            modified_file_policy=ctx.config.uninstall.modified_file_policy,
        )
        uninstall_runner = UninstallRunner(manifest_file=manifest_file, options=options)

        span = max(progress_end - progress_start, 1)

        def sub_progress(value: int, message: str) -> None:
            overall = progress_start + int((max(0, min(value, 100)) / 100) * span)
            progress_callback(overall, message)

        log_callback(f"Starting uninstall-first flow using manifest: {manifest_file}")
        uninstall_result = uninstall_runner.run(
            progress_callback=sub_progress,
            log_callback=log_callback,
            prompt_callback=None,
        )
        if uninstall_result.cancelled:
            raise InstallCancelledError("Uninstall-first operation was cancelled.")
        if not uninstall_result.success:
            detail = uninstall_result.errors[0] if uninstall_result.errors else "unknown uninstall error"
            raise ActionRunnerError(f"Uninstall-first failed: {detail}")

        progress_callback(progress_end, "Uninstall-first completed")
        return {
            "action": "uninstall_first",
            "manifest": str(manifest_file),
            "removed": uninstall_result.removed,
            "skipped": uninstall_result.skipped,
            "errors": uninstall_result.errors,
        }

    def run(
        self,
        ctx: InstallerContext,
        progress_callback: ProgressCallback,
        log_callback: LogCallback,
        message_callback: MessageCallback | None = None,
    ) -> ActionResult:
        results: list[dict[str, Any]] = []
        rollback_errors: list[str] = []
        rollback_performed = False
        manifest_file: Path | None = None

        run_uninstall_first = self._should_run_uninstall_first(ctx)
        total = max(len(self.actions) + (1 if run_uninstall_first else 0), 1)
        transaction = InstallTransaction(ctx, log_callback=log_callback)
        ctx.transaction = transaction
        transaction.start()

        try:
            current_task = 0

            if run_uninstall_first:
                current_task += 1
                start = int(((current_task - 1) / total) * 100)
                end = int((current_task / total) * 100)
                result = self._run_uninstall_first(ctx, progress_callback, log_callback, start, end)
                results.append(result)

            for cfg in self.actions:
                if ctx.is_cancelled():
                    raise InstallCancelledError("Installation cancelled by user.")

                action = self._create_action(ctx, cfg)
                current_task += 1
                action_start = int(((current_task - 1) / total) * 100)
                action_end = int((current_task / total) * 100)
                ctx.action_rollback_policy = cfg.rollback

                def sub_progress(value: int, message: str) -> None:
                    span = max(action_end - action_start, 1)
                    overall = action_start + int((max(0, min(value, 100)) / 100) * span)
                    progress_callback(overall, message)

                log_callback(f"Starting action: {cfg.type}")
                result = action.execute(ctx, sub_progress, log_callback)
                results.append(result)
                if isinstance(result, dict):
                    records = result.get("rollback_records")
                    if isinstance(records, list):
                        transaction.register_records(cfg.type, cfg.rollback, records)

                if cfg.type == "show_message" and message_callback:
                    message_callback(result.get("level", "info"), result.get("title", "Installer"), result.get("message", ""))

                progress_callback(action_end, f"Finished action: {cfg.type}")
                if ctx.is_cancelled():
                    raise InstallCancelledError("Installation cancelled by user.")

            manifest_file = transaction.finalize_success(results)
            return ActionResult(
                success=True,
                cancelled=False,
                results=results,
                manifest_path=str(manifest_file),
            )
        except InstallCancelledError as exc:
            log_callback(str(exc))
            log_callback("Install transaction is being rolled back...")
            rollback_performed = True
            rollback_errors = transaction.rollback()
            return ActionResult(
                success=False,
                cancelled=True,
                results=results,
                error=str(exc),
                rollback_performed=rollback_performed,
                rollback_errors=rollback_errors,
            )
        except Exception as exc:  # noqa: BLE001
            log_callback(f"ERROR: {exc}")
            log_callback("Install transaction is being rolled back...")
            rollback_performed = True
            rollback_errors = transaction.rollback()
            return ActionResult(
                success=False,
                cancelled=ctx.is_cancelled(),
                results=results,
                error=str(exc),
                rollback_performed=rollback_performed,
                rollback_errors=rollback_errors,
            )
        finally:
            ctx.transaction = None
            ctx.action_rollback_policy = "auto"
