"""CLI entrypoint for manifest-driven uninstall."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from installer_framework.engine.uninstall_runner import (
    UninstallOptions,
    UninstallResult,
    UninstallRunner,
    default_manifest_from_install_dir,
)


def _prompt_modified(path: Path, operation: str) -> str:
    prompt = (
        f"File was modified since install: {path}\n"
        f"Operation: {operation}. Choose [d]elete/[s]kip/[a]bort: "
    )
    while True:
        answer = input(prompt).strip().lower()
        if answer in {"d", "delete"}:
            return "delete"
        if answer in {"s", "skip"}:
            return "skip"
        if answer in {"a", "abort"}:
            return "abort"


def parse_args(default_manifest: Path | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TIPS manifest-driven uninstaller")
    parser.add_argument("--manifest", default=str(default_manifest) if default_manifest else None)
    parser.add_argument("--install-dir", default=None, help="Install directory containing .tips/manifest.json")
    parser.add_argument("--silent", action="store_true", help="Run without interactive prompts")
    parser.add_argument(
        "--delete-modified",
        action="store_true",
        help="Force deletion of modified files (silent mode keeps modified files by default)",
    )
    parser.add_argument(
        "--modified-file-policy",
        choices=["prompt", "skip", "delete"],
        default="prompt",
        help="Policy used when modified files are detected",
    )
    return parser.parse_args()


def _resolve_manifest(args: argparse.Namespace, default_manifest: Path | None = None) -> Path:
    if args.manifest:
        return Path(args.manifest).expanduser().resolve()
    if args.install_dir:
        return default_manifest_from_install_dir(Path(args.install_dir).expanduser().resolve())
    if default_manifest is not None:
        return default_manifest
    raise ValueError("Either --manifest or --install-dir must be provided")


def run_uninstall(
    manifest_file: Path,
    options: UninstallOptions,
    *,
    interactive_prompt: bool,
) -> UninstallResult:
    runner = UninstallRunner(manifest_file=manifest_file, options=options)
    prompt_cb = _prompt_modified if interactive_prompt else None
    return runner.run(
        progress_callback=lambda value, message: print(f"[{value:03d}%] {message}"),
        log_callback=lambda message: print(message),
        prompt_callback=prompt_cb,
    )


def main(default_manifest: str | Path | None = None) -> int:
    default_manifest_path = Path(default_manifest).resolve() if default_manifest else None
    args = parse_args(default_manifest=default_manifest_path)
    try:
        manifest_file = _resolve_manifest(args, default_manifest=default_manifest_path)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    options = UninstallOptions(
        silent=args.silent,
        delete_modified=args.delete_modified,
        modified_file_policy=args.modified_file_policy,
    )

    result = run_uninstall(
        manifest_file=manifest_file,
        options=options,
        interactive_prompt=(not args.silent and args.modified_file_policy == "prompt"),
    )

    if result.success:
        print("Uninstall completed successfully.")
        return 0

    if result.cancelled:
        print("Uninstall cancelled.", file=sys.stderr)
        return 2

    if result.errors:
        print("Uninstall completed with errors:", file=sys.stderr)
        for err in result.errors:
            print(f"- {err}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
