"""Installer runtime context and persisted state."""

from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from threading import Event
from typing import Any

from installer_framework.config.models import InstallerConfig
from installer_framework.util.platform import EnvironmentInfo, get_environment_info
from installer_framework.util.privileges import has_elevated_privileges


@dataclass(slots=True)
class InstallerState:
    answers: dict[str, Any] = field(default_factory=dict)
    selected_features: list[str] = field(default_factory=list)
    install_scope: str = "user"
    install_dir: str = ""
    environment: dict[str, Any] = field(default_factory=dict)
    result_summary: dict[str, Any] = field(default_factory=dict)
    detected_upgrade: dict[str, Any] | None = None


@dataclass(slots=True)
class InstallerContext:
    config: InstallerConfig
    state: InstallerState
    env: EnvironmentInfo = field(default_factory=get_environment_info)
    is_elevated: bool = field(default_factory=has_elevated_privileges)
    cancel_event: Event = field(default_factory=Event)

    def __post_init__(self) -> None:
        if not self.state.environment:
            self.state.environment = {
                "os": self.env.os_name,
                "arch": self.env.arch,
                "python_version": self.env.python_version,
                "home_dir": str(self.env.home_dir),
                "is_elevated": self.is_elevated,
            }

    def cancel(self) -> None:
        self.cancel_event.set()

    def is_cancelled(self) -> bool:
        return self.cancel_event.is_set()

    def resume_path(self) -> Path:
        return Path(tempfile.gettempdir()) / "tips_installer_resume.json"

    def save_resume(self) -> None:
        payload = {
            "answers": self.state.answers,
            "selected_features": self.state.selected_features,
            "install_scope": self.state.install_scope,
            "install_dir": self.state.install_dir,
            "environment": self.state.environment,
            "result_summary": self.state.result_summary,
            "detected_upgrade": self.state.detected_upgrade,
        }
        self.resume_path().write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def load_resume(self) -> bool:
        path = self.resume_path()
        if not path.exists():
            return False
        data = json.loads(path.read_text(encoding="utf-8"))
        self.state.answers = dict(data.get("answers", {}))
        self.state.selected_features = list(data.get("selected_features", []))
        self.state.install_scope = data.get("install_scope", self.state.install_scope)
        self.state.install_dir = data.get("install_dir", self.state.install_dir)
        self.state.environment = dict(data.get("environment", self.state.environment))
        self.state.result_summary = dict(data.get("result_summary", {}))
        self.state.detected_upgrade = data.get("detected_upgrade")
        return True

    def clear_resume(self) -> None:
        self.resume_path().unlink(missing_ok=True)
