"""CLI entry point for TIPS installer framework."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

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



def main() -> None:
    configure_logging()
    args = parse_args()
    config_path = Path(args.config).resolve()
    config = load_config(config_path)
    # Prevent Kivy from consuming installer CLI args like --config.
    os.environ.setdefault("KIVY_NO_ARGS", "1")
    from installer_framework.app.kivy_app import InstallerKivyApp

    app = InstallerKivyApp(config=config, resume=args.resume)
    app.run()


if __name__ == "__main__":
    main()
