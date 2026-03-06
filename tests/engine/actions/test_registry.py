from __future__ import annotations

import sys

from installer_framework.engine.actions.registry import ReadRegistryAction, WriteRegistryAction
from tests.helpers.context_factory import default_env, make_context
from tests.helpers.fake_winreg import FakeWinReg


def test_write_registry_skips_on_non_windows(tmp_path):
    ctx = make_context(tmp_path)
    ctx.env = default_env(os_name="linux")
    action = WriteRegistryAction({"key_path": "Software\\X", "value": "v"})
    result = action.execute(ctx, lambda *_: None, lambda *_: None)
    assert result["skipped"] is True


def test_write_and_read_registry_windows(monkeypatch, tmp_path):
    fake = FakeWinReg()
    monkeypatch.setitem(sys.modules, "winreg", fake)

    ctx = make_context(tmp_path)
    ctx.env = default_env(os_name="windows")

    write = WriteRegistryAction({"key_path": "Software\\TIPS", "value_name": "Version", "value": "{version}"})
    result_w = write.execute(ctx, lambda *_: None, lambda *_: None)
    assert result_w["rollback_records"]

    read = ReadRegistryAction({"key_path": "Software\\TIPS", "value_name": "Version", "output_key": "v"})
    result_r = read.execute(ctx, lambda *_: None, lambda *_: None)
    assert result_r["value"] == ctx.config.branding.version
    assert ctx.state.answers["v"] == ctx.config.branding.version
