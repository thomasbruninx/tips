from __future__ import annotations

import sys

import pytest

from installer_framework.engine.actions.registry import ReadRegistryAction, WriteRegistryAction, _reg_type_name
from tests.helpers.context_factory import default_env, make_context
from tests.helpers.fake_winreg import FakeWinReg


def test_reg_type_name_known_and_fallback():
    fake = FakeWinReg()
    assert _reg_type_name(fake, fake.REG_DWORD) == "REG_DWORD"
    assert _reg_type_name(fake, 999) == "REG_SZ"


def test_write_registry_importerror_on_windows(monkeypatch, tmp_path):
    monkeypatch.delitem(sys.modules, "winreg", raising=False)
    ctx = make_context(tmp_path)
    ctx.env = default_env(os_name="windows")
    with pytest.raises(RuntimeError, match="winreg support not available"):
        WriteRegistryAction({"key_path": "Software\\TIPS", "value": "x"}).execute(ctx, lambda *_: None, lambda *_: None)


def test_read_registry_importerror_on_windows(monkeypatch, tmp_path):
    monkeypatch.delitem(sys.modules, "winreg", raising=False)
    ctx = make_context(tmp_path)
    ctx.env = default_env(os_name="windows")
    with pytest.raises(RuntimeError, match="winreg support not available"):
        ReadRegistryAction({"key_path": "Software\\TIPS"}).execute(ctx, lambda *_: None, lambda *_: None)


def test_write_registry_existing_value_creates_restore_record(monkeypatch, tmp_path):
    fake = FakeWinReg()
    monkeypatch.setitem(sys.modules, "winreg", fake)

    ctx = make_context(tmp_path)
    ctx.env = default_env(os_name="windows")
    action = WriteRegistryAction({"key_path": "Software\\TIPS", "value_name": "Version", "value": "1", "value_type": "REG_DWORD"})
    action.execute(ctx, lambda *_: None, lambda *_: None)

    second = WriteRegistryAction({"key_path": "Software\\TIPS", "value_name": "Version", "value": "2", "value_type": "REG_DWORD"})
    result = second.execute(ctx, lambda *_: None, lambda *_: None)
    rec = result["rollback_records"][0]
    assert rec["existed_before"] is True
    assert rec["old_value"] == "1"
    assert rec["old_type"] == "REG_DWORD"


def test_read_registry_missing_value_logs_and_no_output_key(monkeypatch, tmp_path):
    fake = FakeWinReg()
    monkeypatch.setitem(sys.modules, "winreg", fake)

    logs: list[str] = []
    ctx = make_context(tmp_path)
    ctx.env = default_env(os_name="windows")
    result = ReadRegistryAction({"key_path": "Software\\Missing", "value_name": "X"}).execute(
        ctx, lambda *_: None, lambda m: logs.append(m)
    )
    assert result["value"] is None
    assert any("not found" in msg for msg in logs)
