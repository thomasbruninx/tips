from __future__ import annotations

from installer_framework.config.models import ActionConfig
from installer_framework.engine.action_base import Action
from installer_framework.engine.runner import ActionRunner
from installer_framework.plugins.registry import build_registry_with_builtins
from tests.helpers.context_factory import make_context


class DemoAction(Action):
    def __init__(self, params):
        self.params = params

    def execute(self, ctx, progress, log):
        progress(100, "ok")
        log("ran demo")
        return {
            "action": "demo_action",
            "rollback_records": [{"kind": "file", "path": ctx.state.install_dir + "/x", "existed_before": False}],
        }


class FailingAction(Action):
    def __init__(self, params):
        self.params = params

    def execute(self, ctx, progress, log):
        raise RuntimeError("boom")


def test_action_runner_runs_actions_and_writes_manifest(tmp_path):
    ctx = make_context(tmp_path)
    registry = build_registry_with_builtins()
    registry.register_action("demo_action", DemoAction, source="test")
    ctx.plugin_registry = registry

    runner = ActionRunner([ActionConfig(type="demo_action", params={})])
    result = runner.run(ctx, lambda *_: None, lambda *_: None)

    assert result.success is True
    assert result.manifest_path is not None


def test_action_runner_rolls_back_on_error(tmp_path):
    ctx = make_context(tmp_path)
    registry = build_registry_with_builtins()
    registry.register_action("failing_action", FailingAction, source="test")
    ctx.plugin_registry = registry

    runner = ActionRunner([ActionConfig(type="failing_action", params={})])
    result = runner.run(ctx, lambda *_: None, lambda *_: None)

    assert result.success is False
    assert result.rollback_performed is True
