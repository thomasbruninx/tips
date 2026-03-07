from __future__ import annotations

import json
from pathlib import Path

from installer_framework.engine.uninstall_runner import UninstallResult
from installer_framework.ui.uninstall_wizard import UninstallWizard


def _manifest(tmp_path: Path) -> Path:
    manifest = tmp_path / ".tips" / "manifest.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps({"product_name": "Demo", "install_dir": str(tmp_path), "artifacts": []}), encoding="utf-8")
    return manifest


def test_uninstall_wizard_start_uninstall_missing_manifest_shows_error(qtbot, tmp_path, monkeypatch):
    missing = tmp_path / ".tips" / "missing.json"
    calls: list[tuple[str, str]] = []
    monkeypatch.setattr(
        "installer_framework.ui.uninstall_wizard.QMessageBox.critical",
        lambda _parent, title, msg: calls.append((title, msg)),
    )

    wizard = UninstallWizard(missing)
    qtbot.addWidget(wizard)
    wizard.start_uninstall()

    assert calls
    assert calls[0][0] == "Manifest not found"


def test_uninstall_wizard_prompt_modified_branches(qtbot, tmp_path, monkeypatch):
    wizard = UninstallWizard(_manifest(tmp_path))
    qtbot.addWidget(wizard)

    class _FakeBox:
        class Icon:
            Warning = object()

        class ButtonRole:
            AcceptRole = object()
            ActionRole = object()
            RejectRole = object()

        click = "delete"

        def __init__(self, *_args, **_kwargs):
            self._buttons = {}

        def setIcon(self, *_args, **_kwargs):
            return None

        def setWindowTitle(self, *_args, **_kwargs):
            return None

        def setText(self, *_args, **_kwargs):
            return None

        def addButton(self, text, _role):
            btn = object()
            self._buttons[text] = btn
            return btn

        def exec(self):
            return 0

        def clickedButton(self):
            if self.click == "delete":
                return self._buttons["Delete"]
            if self.click == "abort":
                return self._buttons["Abort"]
            return self._buttons["Skip"]

    monkeypatch.setattr("installer_framework.ui.uninstall_wizard.QMessageBox", _FakeBox)

    _FakeBox.click = "delete"
    assert wizard._prompt_modified(Path("/tmp/a"), "delete") == "delete"
    _FakeBox.click = "abort"
    assert wizard._prompt_modified(Path("/tmp/a"), "delete") == "abort"
    _FakeBox.click = "skip"
    assert wizard._prompt_modified(Path("/tmp/a"), "delete") == "skip"


def test_uninstall_wizard_finish_states(qtbot, tmp_path):
    wizard = UninstallWizard(_manifest(tmp_path))
    qtbot.addWidget(wizard)

    wizard._finish(UninstallResult(success=True, cancelled=False))
    assert "successfully" in wizard.message_label.text()

    wizard._finish(UninstallResult(success=False, cancelled=True))
    assert "cancelled" in wizard.message_label.text().lower()

    wizard._finish(UninstallResult(success=False, cancelled=False, errors=["e"]))
    assert "errors" in wizard.message_label.text().lower()


def test_uninstall_wizard_logs_windows_temp_handoff(qtbot, tmp_path):
    wizard = UninstallWizard(
        _manifest(tmp_path),
        original_uninstaller_path=tmp_path / "install" / "tips-uninstaller.exe",
        temp_cleanup_dir=tmp_path / "temp",
    )
    qtbot.addWidget(wizard)

    assert "Windows temp handoff active" in wizard.log_view.toPlainText()


def test_uninstall_wizard_start_uninstall_with_errors(qtbot, tmp_path, monkeypatch):
    class _Runner:
        def __init__(self, _manifest_file, options, **kwargs):
            self.options = options
            self.kwargs = kwargs

        def run(self, progress_callback, log_callback, prompt_callback=None):
            assert prompt_callback is not None
            progress_callback(50, "half")
            log_callback("running")
            return UninstallResult(success=False, cancelled=False, errors=["boom"])

    monkeypatch.setattr("installer_framework.ui.uninstall_wizard.UninstallRunner", _Runner)
    wizard = UninstallWizard(_manifest(tmp_path), modified_file_policy="prompt")
    qtbot.addWidget(wizard)

    wizard.start_uninstall()
    text = wizard.log_view.toPlainText()
    assert "ERROR: boom" in text
    assert wizard.result is not None
