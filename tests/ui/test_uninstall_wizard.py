from __future__ import annotations

import json

from installer_framework.engine.uninstall_runner import UninstallResult
from installer_framework.ui.uninstall_wizard import UninstallWizard


class FakeRunner:
    def __init__(self, manifest_file, options, **kwargs):
        self.manifest_file = manifest_file
        self.options = options
        self.kwargs = kwargs

    def run(self, progress_callback, log_callback, prompt_callback=None):
        progress_callback(100, "done")
        log_callback("done")
        return UninstallResult(success=True, cancelled=False)


def test_uninstall_wizard_start_uninstall(qtbot, tmp_path, monkeypatch):
    manifest = tmp_path / ".tips" / "manifest.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps({"product_name": "Demo", "install_dir": str(tmp_path), "artifacts": []}), encoding="utf-8")

    monkeypatch.setattr("installer_framework.ui.uninstall_wizard.UninstallRunner", FakeRunner)

    wizard = UninstallWizard(manifest)
    qtbot.addWidget(wizard)
    wizard.start_uninstall()

    assert wizard.result is not None
    assert wizard.result.success is True
