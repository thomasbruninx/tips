from __future__ import annotations

from pathlib import Path

from installer_framework.app.qt_app import InstallerQtApp
from tests.helpers.context_factory import make_config


class _FakeWindow:
    def __init__(self):
        self.icon = None
        self.shown = False

    def setWindowTitle(self, _title):
        return None

    def setWindowIcon(self, icon):
        self.icon = icon

    def resize(self, _w, _h):
        return None

    def setMinimumSize(self, _w, _h):
        return None

    def show(self):
        self.shown = True


def test_installer_qt_app_resume_branch(monkeypatch, tmp_path):
    cfg = make_config(tmp_path)
    called = {"resume": False}
    monkeypatch.setattr(
        "installer_framework.app.qt_app.InstallerContext.load_resume",
        lambda self: called.__setitem__("resume", True) or True,
    )
    monkeypatch.setattr("installer_framework.app.qt_app.detect_existing_install", lambda _ctx: None)
    InstallerQtApp(config=cfg, resume=True)
    assert called["resume"] is True


def test_installer_qt_app_run_constructs_qapplication_and_applies_icon(monkeypatch, tmp_path):
    cfg = make_config(tmp_path)
    cfg.branding.window_icon_path = "icon.png"
    icon_file = tmp_path / "icon.png"
    icon_file.write_text("x", encoding="utf-8")

    fake_window = _FakeWindow()
    created = {"app": None}

    class _FakeApp:
        def __init__(self):
            self.name = None

        def setApplicationName(self, name):
            self.name = name

        def exec(self):
            return 321

    class _FakeQApplication:
        @staticmethod
        def instance():
            return None

        def __init__(self, *_args, **_kwargs):
            created["app"] = _FakeApp()

        def setApplicationName(self, name):
            created["app"].setApplicationName(name)

        def exec(self):
            return created["app"].exec()

    monkeypatch.setattr("installer_framework.app.qt_app.QApplication", _FakeQApplication)
    monkeypatch.setattr("installer_framework.app.qt_app.Wizard", lambda config, ctx: fake_window)
    monkeypatch.setattr("installer_framework.app.qt_app.QIcon", lambda path: f"ICON:{path}")

    app = InstallerQtApp(config=cfg, resume=False)
    result = app.run()

    assert result == 321
    assert fake_window.shown is True
    assert str(fake_window.icon).startswith("ICON:")


def test_apply_icon_missing_file_noop(tmp_path):
    cfg = make_config(tmp_path)
    cfg.branding.window_icon_path = "missing.png"
    app = InstallerQtApp(config=cfg, resume=False)

    window = _FakeWindow()
    app._apply_icon(window)
    assert window.icon is None
