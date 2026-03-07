from __future__ import annotations

import runpy
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

from installer_framework import main


def test_resolve_config_path_absolute_and_missing(tmp_path, monkeypatch):
    abs_cfg = (tmp_path / "abs.json").resolve()
    abs_cfg.write_text("{}", encoding="utf-8")
    assert main.resolve_config_path(str(abs_cfg)) == abs_cfg

    monkeypatch.chdir(tmp_path)
    missing = main.resolve_config_path("missing.json")
    assert missing == (tmp_path / "missing.json").resolve()


def test_main_wires_bootstrap(monkeypatch, tmp_path):
    called = {"logging": False, "run": False, "resume": None, "config_path": None, "plugins_dir": None}
    cfg = object()

    monkeypatch.setattr(main, "configure_logging", lambda: called.__setitem__("logging", True))
    monkeypatch.setattr(
        main,
        "parse_args",
        lambda: SimpleNamespace(config="cfg.json", resume=True, plugins_dir="plugins"),
    )
    monkeypatch.setattr(main, "resolve_config_path", lambda arg: tmp_path / arg)

    def _load_config(path, plugins_dir=None):
        called["config_path"] = path
        called["plugins_dir"] = plugins_dir
        return cfg

    monkeypatch.setattr(main, "load_config", _load_config)

    fake_qt_module = ModuleType("installer_framework.app.qt_app")

    class _FakeInstallerQtApp:
        def __init__(self, config, resume):
            assert config is cfg
            called["resume"] = resume

        def run(self):
            called["run"] = True
            return 0

    fake_qt_module.InstallerQtApp = _FakeInstallerQtApp  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "installer_framework.app.qt_app", fake_qt_module)

    main.main()
    assert called["logging"] is True
    assert called["run"] is True
    assert called["resume"] is True
    assert str(called["config_path"]).endswith("cfg.json")
    assert called["plugins_dir"] == "plugins"


def test_main_module_guard(monkeypatch, tmp_path):
    sample_cfg = Path(__file__).resolve().parents[2] / "installer_framework" / "examples" / "sample_installer.json"
    monkeypatch.setattr("sys.argv", ["prog", "--config", str(sample_cfg)])
    monkeypatch.delitem(sys.modules, "installer_framework.main", raising=False)

    fake_qt_module = ModuleType("installer_framework.app.qt_app")
    fake_qt_module.InstallerQtApp = type(  # type: ignore[attr-defined]
        "_FakeInstallerQtApp",
        (),
        {"__init__": lambda self, config, resume: None, "run": lambda self: 0},
    )
    monkeypatch.setitem(sys.modules, "installer_framework.app.qt_app", fake_qt_module)
    runpy.run_module("installer_framework.main", run_name="__main__")
