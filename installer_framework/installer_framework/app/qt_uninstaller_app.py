"""PyQt6 bootstrap for the GUI uninstaller."""

from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from installer_framework.ui.uninstall_wizard import UninstallWizard


class UninstallerQtApp:
    def __init__(
        self,
        *,
        manifest_file: Path,
        delete_modified: bool = False,
        modified_file_policy: str = "prompt",
    ) -> None:
        self.manifest_file = manifest_file
        self.delete_modified = delete_modified
        self.modified_file_policy = modified_file_policy

    def run(self) -> int:
        app = QApplication.instance() or QApplication(sys.argv)
        app.setApplicationName("TIPS Uninstaller")

        window = UninstallWizard(
            self.manifest_file,
            delete_modified=self.delete_modified,
            modified_file_policy=self.modified_file_policy,
        )
        window.show()
        return app.exec()
