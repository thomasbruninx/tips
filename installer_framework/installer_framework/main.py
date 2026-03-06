"""CLI entry point for TIPS installer framework."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from installer_framework.app.resources import resource_path
from installer_framework.config.loader import load_config
from installer_framework.util.logging import configure_logging

DEFAULT_CONFIG = "examples/sample_installer.json"
BUNDLED_DEFAULT_CONFIG_MARKER = "build/default_config_path.txt"
LOGGER = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TIPS Installer Framework")
    parser.add_argument(
        "--config",
        default=None,
        help="Path to installer definition JSON",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Load resume state from temp dir if available",
    )
    parser.add_argument(
        "--plugins-dir",
        default=None,
        help="Optional plugin root directory containing *.tipsplugin subfolders",
    )
    return parser.parse_args()


def is_frozen_runtime() -> bool:
    return bool(getattr(sys, "frozen", False) or getattr(sys, "_MEIPASS", None))


def resolve_default_config_arg(cli_config: str | None) -> str:
    if cli_config:
        return cli_config

    if is_frozen_runtime():
        marker = resource_path(BUNDLED_DEFAULT_CONFIG_MARKER)
        if marker.exists():
            configured = marker.read_text(encoding="utf-8").strip()
            if configured:
                return configured

    return DEFAULT_CONFIG


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
    config_arg = resolve_default_config_arg(args.config)
    config_path = resolve_config_path(config_arg)
    LOGGER.info("Using installer config: %s", config_path)
    config = load_config(config_path, plugins_dir=args.plugins_dir)
    from installer_framework.app.qt_app import InstallerQtApp

    app = InstallerQtApp(config=config, resume=args.resume)
    app.run()


if __name__ == "__main__":
    main()
