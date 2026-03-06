from __future__ import annotations

from pathlib import Path

import pytest

from installer_framework.config.models import ActionConfig
from installer_framework.engine.action_base import Action
from installer_framework.engine.manifest import manifest_path
from installer_framework.engine.runner import ActionRunner, ActionRunnerError
from installer_framework.engine.uninstall_runner import UninstallResult
from installer_framework.plugins.registry import build_registry_with_builtins
from tests.helpers.context_factory import make_context


class _DemoAction(Action):
    def __init__(self, params):
        self.params = params

    def execute(self, ctx, progress, log):
        progress(100, "done")
        log("demo")
        return {"action": "demo"}


def test_create_action_builds_registry_when_missing(tmp_path):
    ctx = make_context(tmp_path)
    ctx.config.plugin_registry = None
    ctx.plugin_registry = None

    runner = ActionRunner([])
    action = runner._create_action(ctx, ActionConfig(type="show_message", params={"message": "x"}))
    assert action.__class__.__name__ == "ShowMessageAction"
    assert ctx.plugin_registry is not None


def test_create_action_rejects_unsupported_type(tmp_path):
    ctx = make_context(tmp_path)
    ctx.plugin_registry = build_registry_with_builtins()
    runner = ActionRunner([])

    with pytest.raises(ActionRunnerError, match="Unsupported action type"):
        runner._create_action(ctx, ActionConfig(type="not_real", params={}))


def test_resolve_upgrade_manifest_priority(tmp_path):
    ctx = make_context(tmp_path)
    runner = ActionRunner([])

    detected_dir = tmp_path / "detected"
    current_dir = Path(ctx.state.install_dir)
    detected_manifest = manifest_path(detected_dir)
    current_manifest = manifest_path(current_dir)
    detected_manifest.parent.mkdir(parents=True, exist_ok=True)
    current_manifest.parent.mkdir(parents=True, exist_ok=True)
    detected_manifest.write_text("{}", encoding="utf-8")
    current_manifest.write_text("{}", encoding="utf-8")

    ctx.state.detected_upgrade = {"install_dir": str(detected_dir)}
    assert runner._resolve_upgrade_manifest(ctx) == detected_manifest

    detected_manifest.unlink()
    assert runner._resolve_upgrade_manifest(ctx) == current_manifest

    current_manifest.unlink()
    assert runner._resolve_upgrade_manifest(ctx) is None


def test_run_uninstall_first_requires_manifest(tmp_path):
    ctx = make_context(tmp_path)
    ctx.state.detected_upgrade = {"install_dir": str(tmp_path / "missing")}
    runner = ActionRunner([])

    with pytest.raises(ActionRunnerError, match="no uninstall manifest"):
        runner._run_uninstall_first(ctx, lambda *_: None, lambda *_: None, 0, 25)


def test_run_uninstall_first_cancellation_and_failure(monkeypatch, tmp_path):
    ctx = make_context(tmp_path)
    install_dir = tmp_path / "existing"
    mf = manifest_path(install_dir)
    mf.parent.mkdir(parents=True, exist_ok=True)
    mf.write_text("{}", encoding="utf-8")
    ctx.state.detected_upgrade = {"install_dir": str(install_dir)}
    runner = ActionRunner([])

    class _Cancelled:
        def __init__(self, *args, **kwargs):
            pass

        def run(self, **kwargs):
            return UninstallResult(success=False, cancelled=True)

    monkeypatch.setattr("installer_framework.engine.runner.UninstallRunner", _Cancelled)
    with pytest.raises(Exception, match="cancelled"):
        runner._run_uninstall_first(ctx, lambda *_: None, lambda *_: None, 0, 50)

    class _Failed:
        def __init__(self, *args, **kwargs):
            pass

        def run(self, **kwargs):
            return UninstallResult(success=False, cancelled=False, errors=["boom"])

    monkeypatch.setattr("installer_framework.engine.runner.UninstallRunner", _Failed)
    with pytest.raises(ActionRunnerError, match="Uninstall-first failed"):
        runner._run_uninstall_first(ctx, lambda *_: None, lambda *_: None, 0, 50)


def test_run_includes_uninstall_first_result_and_message_callback(monkeypatch, tmp_path):
    ctx = make_context(tmp_path)
    ctx.state.answers["upgrade_mode"] = "uninstall_first"
    existing_dir = tmp_path / "existing-install"
    mf = manifest_path(existing_dir)
    mf.parent.mkdir(parents=True, exist_ok=True)
    mf.write_text("{}", encoding="utf-8")
    ctx.state.detected_upgrade = {"install_dir": str(existing_dir)}

    registry = build_registry_with_builtins()
    registry.register_action("demo_action", _DemoAction, source="test")
    ctx.plugin_registry = registry

    class _UninstallOk:
        def __init__(self, *args, **kwargs):
            pass

        def run(self, **kwargs):
            return UninstallResult(success=True, cancelled=False, removed=["a"], skipped=[], errors=[])

    monkeypatch.setattr("installer_framework.engine.runner.UninstallRunner", _UninstallOk)

    callback_payloads: list[tuple[str, str, str]] = []
    runner = ActionRunner(
        [
            ActionConfig(type="show_message", params={"level": "info", "title": "T", "message": "M"}),
            ActionConfig(type="demo_action", params={}),
        ]
    )
    result = runner.run(ctx, lambda *_: None, lambda *_: None, lambda l, t, m: callback_payloads.append((l, t, m)))

    assert result.success is True
    assert result.results[0]["action"] == "uninstall_first"
    assert callback_payloads == [("info", "T", "M")]


def test_run_handles_pre_cancelled_context(tmp_path):
    ctx = make_context(tmp_path)
    ctx.cancel()
    runner = ActionRunner([ActionConfig(type="show_message", params={"message": "x"})])

    result = runner.run(ctx, lambda *_: None, lambda *_: None)
    assert result.success is False
    assert result.cancelled is True
    assert result.rollback_performed is True
