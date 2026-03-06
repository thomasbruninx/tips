from __future__ import annotations

from pathlib import Path

from installer_framework.app.qt_app import InstallerQtApp
from tests.helpers.context_factory import make_config


class _FakeWindow:
    def __init__(self):
        self.title = None
        self.icon = None
        self.size = None
        self.min_size = None
        self.shown = False

    def setWindowTitle(self, title):
        self.title = title

    def setWindowIcon(self, icon):
        self.icon = icon

    def resize(self, w, h):
        self.size = (w, h)

    def setMinimumSize(self, w, h):
        self.min_size = (w, h)

    def show(self):
        self.shown = True


class _FakeApp:
    def __init__(self):
        self.app_name = None

    def setApplicationName(self, name):
        self.app_name = name

    def processEvents(self):
        return None

    def exec(self):
        return 123


def test_installer_qt_app_initializes_context(monkeypatch, tmp_path):
    cfg = make_config(tmp_path)
    monkeypatch.setattr("installer_framework.app.qt_app.detect_existing_install", lambda _ctx: {"version": "0.9"})
    app = InstallerQtApp(config=cfg, resume=False)
    assert app.ctx.state.install_scope in {"user", "system"}
    assert app.ctx.state.detected_upgrade == {"version": "0.9"}


def test_installer_qt_app_run_wires_window(monkeypatch, tmp_path):
    cfg = make_config(tmp_path)
    fake_app = _FakeApp()
    fake_window = _FakeWindow()

    class _FakeQApplication:
        @staticmethod
        def instance():
            return fake_app

        def __init__(self, *_args, **_kwargs):
            pass

    monkeypatch.setattr("installer_framework.app.qt_app.Wizard", lambda config, ctx: fake_window)
    monkeypatch.setattr("installer_framework.app.qt_app.QApplication", _FakeQApplication)

    app = InstallerQtApp(config=cfg, resume=False)
    result = app.run()

    assert result == 123
    assert fake_window.shown is True
    assert fake_window.title == cfg.branding.product_name
