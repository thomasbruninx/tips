"""CLI/GUI entrypoint for TIPS uninstaller."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from uuid import uuid4

from installer_framework.engine.manifest import load_json
from installer_framework.engine.uninstall_runner import UninstallOptions
from installer_framework.uninstall_cli import run_uninstall


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TIPS Uninstaller")
    parser.add_argument("--manifest", default=None, help="Path to .tips/manifest.json")
    parser.add_argument("--install-dir", default=None, help="Install directory (manifest resolved as .tips/manifest.json)")
    parser.add_argument("--silent", action="store_true", help="Run in CLI mode without GUI")
    parser.add_argument(
        "--delete-modified",
        action="store_true",
        help="Delete files that were modified after install",
    )
    parser.add_argument(
        "--modified-file-policy",
        choices=["prompt", "skip", "delete"],
        default="prompt",
        help="Policy used when modified files are detected",
    )
    parser.add_argument("--windows-temp-handoff", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--original-uninstaller-path", default=None, help=argparse.SUPPRESS)
    parser.add_argument("--temp-cleanup-dir", default=None, help=argparse.SUPPRESS)
    return parser.parse_args()


def is_windows_runtime() -> bool:
    return os.name == "nt"


def resolve_manifest(args: argparse.Namespace) -> Path:
    if args.manifest:
        return Path(args.manifest).expanduser().resolve()
    if args.install_dir:
        return (Path(args.install_dir).expanduser().resolve() / ".tips" / "manifest.json")
    exe_dir = Path(sys.argv[0]).resolve().parent
    manifest_file = exe_dir / ".tips" / "manifest.json"
    if manifest_file.exists():
        return manifest_file
    raise ValueError("Either --manifest, --install-dir, or a neighboring .tips/manifest.json is required")


def should_use_windows_temp_handoff(args: argparse.Namespace, manifest_file: Path) -> bool:
    if getattr(args, "windows_temp_handoff", False) or not is_windows_runtime():
        return False

    current_executable = Path(sys.argv[0]).expanduser().resolve()
    if current_executable.suffix.lower() != ".exe":
        return False

    payload = load_json(manifest_file, default={})
    uninstall_meta = payload.get("uninstall", {}) or {}
    configured_uninstaller = uninstall_meta.get("windows_uninstaller_path")
    if configured_uninstaller:
        try:
            if Path(configured_uninstaller).expanduser().resolve() == current_executable:
                return True
        except Exception:
            return False

    install_dir = payload.get("install_dir")
    if not install_dir:
        return False

    try:
        return current_executable.is_relative_to(Path(install_dir).expanduser().resolve())
    except Exception:
        return False


def build_temp_uninstaller_command(
    args: argparse.Namespace,
    manifest_file: Path,
    *,
    temp_executable: Path,
    original_uninstaller_path: Path,
    temp_cleanup_dir: Path,
) -> list[str]:
    command = [
        str(temp_executable),
        "--manifest",
        str(manifest_file),
        "--modified-file-policy",
        args.modified_file_policy,
        "--windows-temp-handoff",
        "--original-uninstaller-path",
        str(original_uninstaller_path),
        "--temp-cleanup-dir",
        str(temp_cleanup_dir),
    ]
    if args.silent:
        command.append("--silent")
    if args.delete_modified:
        command.append("--delete-modified")
    return command


def perform_windows_temp_handoff(args: argparse.Namespace, manifest_file: Path) -> int | None:
    current_executable = Path(sys.argv[0]).expanduser().resolve()
    temp_dir = Path(tempfile.gettempdir()) / f"tips-uninstall-{uuid4().hex}"
    temp_executable = temp_dir / current_executable.name

    try:
        temp_dir.mkdir(parents=True, exist_ok=False)
        shutil.copy2(current_executable, temp_executable)
        command = build_temp_uninstaller_command(
            args,
            manifest_file,
            temp_executable=temp_executable,
            original_uninstaller_path=current_executable,
            temp_cleanup_dir=temp_dir,
        )
        creationflags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NO_WINDOW", 0)
        subprocess.Popen(command, cwd=str(temp_dir), creationflags=creationflags, close_fds=True)
        return 0
    except Exception as exc:
        print(f"WARNING: Windows temp handoff failed, continuing in place: {exc}")
        return None


def schedule_windows_temp_self_cleanup(temp_executable: Path, temp_dir: Path) -> None:
    if not is_windows_runtime():
        return

    cleanup_command = (
        f'ping 127.0.0.1 -n 2 > nul & del /f /q "{temp_executable}" & '
        f'rmdir /s /q "{temp_dir}"'
    )
    creationflags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NO_WINDOW", 0)
    subprocess.Popen(
        ["cmd.exe", "/c", cleanup_command],
        creationflags=creationflags,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        close_fds=True,
    )


def main() -> int:
    args = parse_args()
    try:
        manifest_file = resolve_manifest(args)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1

    if should_use_windows_temp_handoff(args, manifest_file):
        handoff_result = perform_windows_temp_handoff(args, manifest_file)
        if handoff_result is not None:
            return handoff_result

    original_path_value = getattr(args, "original_uninstaller_path", None)
    cleanup_dir_value = getattr(args, "temp_cleanup_dir", None)
    original_uninstaller_path = Path(original_path_value).expanduser().resolve() if original_path_value else None
    temp_cleanup_dir = Path(cleanup_dir_value).expanduser().resolve() if cleanup_dir_value else None
    running_executable = Path(sys.argv[0]).expanduser().resolve()

    if args.silent:
        options = UninstallOptions(
            silent=True,
            delete_modified=args.delete_modified,
            modified_file_policy=args.modified_file_policy,
        )
        result = run_uninstall(
            manifest_file,
            options=options,
            interactive_prompt=False,
            running_executable=running_executable,
            original_uninstaller_path=original_uninstaller_path,
        )
        if temp_cleanup_dir:
            try:
                schedule_windows_temp_self_cleanup(running_executable, temp_cleanup_dir)
            except Exception as exc:
                print(f"WARNING: Failed to schedule temp cleanup: {exc}")
        if result.success:
            return 0
        if result.cancelled:
            return 2
        return 1

    from installer_framework.app.qt_uninstaller_app import UninstallerQtApp

    app = UninstallerQtApp(
        manifest_file=manifest_file,
        delete_modified=args.delete_modified,
        modified_file_policy=args.modified_file_policy,
        original_uninstaller_path=original_uninstaller_path,
        temp_cleanup_dir=temp_cleanup_dir,
    )
    return app.run()


if __name__ == "__main__":
    raise SystemExit(main())
