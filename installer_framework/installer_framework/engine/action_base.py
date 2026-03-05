"""Action interface for installer engine."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable

from installer_framework.engine.context import InstallerContext

ProgressCallback = Callable[[int, str], None]
LogCallback = Callable[[str], None]


class Action(ABC):
    """Base action contract."""

    @abstractmethod
    def execute(self, ctx: InstallerContext, progress: ProgressCallback, log: LogCallback) -> dict:
        """Execute action and return a result payload."""
