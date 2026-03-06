from __future__ import annotations

from pathlib import Path

from installer_framework.app.qt_uninstaller_app import UninstallerQtApp


class _FakeWizard:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.shown = False

    def show(self):
        self.shown = True


class _FakeApp:
    def __init__(self):
        self.name = None

    def setApplicationName(self, name):
        self.name = name

    def processEvents(self):
        return None

    def exec(self):
        return 5


def test_qt_uninstaller_app_run(monkeypatch, tmp_path):
    fake_app = _FakeApp()
    created = {}

    def _wizard(*args, **kwargs):
        obj = _FakeWizard(*args, **kwargs)
        created["wizard"] = obj
        return obj

    class _FakeQApplication:
        @staticmethod
        def instance():
            return fake_app

        def __init__(self, *_args, **_kwargs):
            pass

    monkeypatch.setattr("installer_framework.app.qt_uninstaller_app.QApplication", _FakeQApplication)
    monkeypatch.setattr("installer_framework.app.qt_uninstaller_app.UninstallWizard", _wizard)

    app = UninstallerQtApp(manifest_file=tmp_path / "manifest.json")
    result = app.run()

    assert result == 5
    assert created["wizard"].shown is True
