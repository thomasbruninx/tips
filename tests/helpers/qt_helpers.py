from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from installer_framework.config.models import ThemeConfig
from installer_framework.ui.theme import UITheme
from installer_framework.ui.widgets.theme import build_widget_factory


@dataclass
class WizardStub:
    theme: UITheme

    def __post_init__(self) -> None:
        self.widget_factory = build_widget_factory(self.theme)
        self.finished_result = None

    def on_install_finished(self, result) -> None:
        self.finished_result = result


def make_theme(style: str = "classic", source_root: Path | None = None) -> UITheme:
    return UITheme(config=ThemeConfig(style=style), source_root=source_root or Path.cwd())
