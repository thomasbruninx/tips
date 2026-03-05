"""CLI entry point for TIPS installer framework."""

from __future__ import annotations

import argparse
from pathlib import Path

from installer_framework.app.resources import resource_path
from installer_framework.config.loader import load_config
from installer_framework.util.logging import configure_logging


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TIPS Installer Framework")
    parser.add_argument(
        "--config",
        default="examples/sample_installer.json",
        help="Path to installer definition JSON",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Load resume state from temp dir if available",
    )
    return parser.parse_args()


def resolve_config_path(config_arg: str) -> Path:
    """Resolve config path for source runs and frozen app bundles."""
    requested = Path(config_arg).expanduser()
    if requested.is_absolute():
        return requested

    cwd_candidate = (Path.cwd() / requested).resolve()
    if cwd_candidate.exists():
        return cwd_candidate

    bundled_candidate = resource_path(config_arg)
    if bundled_candidate.exists():
        return bundled_candidate

    return cwd_candidate


def main() -> None:
    configure_logging()
    args = parse_args()
    config_path = resolve_config_path(args.config)
    config = load_config(config_path)
    from installer_framework.app.qt_app import InstallerQtApp

    app = InstallerQtApp(config=config, resume=args.resume)
    app.run()


if __name__ == "__main__":
    main()
