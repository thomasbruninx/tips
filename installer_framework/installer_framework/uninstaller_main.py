"""CLI/GUI entrypoint for TIPS uninstaller."""

from __future__ import annotations

import argparse
from pathlib import Path

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
    return parser.parse_args()


def resolve_manifest(args: argparse.Namespace) -> Path:
    if args.manifest:
        return Path(args.manifest).expanduser().resolve()
    if args.install_dir:
        return (Path(args.install_dir).expanduser().resolve() / ".tips" / "manifest.json")
    raise ValueError("Either --manifest or --install-dir must be specified")


def main() -> int:
    args = parse_args()
    try:
        manifest_file = resolve_manifest(args)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1

    if args.silent:
        options = UninstallOptions(
            silent=True,
            delete_modified=args.delete_modified,
            modified_file_policy=args.modified_file_policy,
        )
        result = run_uninstall(manifest_file, options=options, interactive_prompt=False)
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
    )
    return app.run()


if __name__ == "__main__":
    raise SystemExit(main())
