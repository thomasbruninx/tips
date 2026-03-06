from __future__ import annotations

import json
import sys
from pathlib import Path
from types import ModuleType

import pytest

from installer_framework.engine.actions.copy_files import CopyFilesAction
from tests.helpers.context_factory import make_context


def _write_manifest(path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_copy_files_copies_from_manifest(tmp_path):
    src = tmp_path / "payload" / "a.txt"
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_text("hello", encoding="utf-8")
    _write_manifest(
        tmp_path / "copy_manifest.json",
        {"schema_version": 1, "files": [{"source": "payload/a.txt", "target": "bin/a.txt"}]},
    )

    ctx = make_context(tmp_path, install_dir=str(tmp_path / "install"))
    action = CopyFilesAction({"manifest_file": "copy_manifest.json"})
    result = action.execute(ctx, lambda *_: None, lambda *_: None)

    assert (tmp_path / "install" / "bin" / "a.txt").read_text(encoding="utf-8") == "hello"
    assert result["copied_items"] == 1
    assert result["skipped_items"] == 0
    assert result["rollback_records"]


def test_copy_files_requires_manifest_file(tmp_path):
    ctx = make_context(tmp_path)
    action = CopyFilesAction({})
    with pytest.raises(ValueError, match="manifest_file"):
        action.execute(ctx, lambda *_: None, lambda *_: None)


def test_copy_files_fails_when_manifest_file_missing(tmp_path):
    ctx = make_context(tmp_path)
    action = CopyFilesAction({"manifest_file": "missing.json"})
    with pytest.raises(FileNotFoundError, match="manifest not found"):
        action.execute(ctx, lambda *_: None, lambda *_: None)


def test_copy_files_fails_for_invalid_manifest_json(tmp_path):
    manifest = tmp_path / "copy_manifest.json"
    manifest.write_text("{bad", encoding="utf-8")
    ctx = make_context(tmp_path)
    action = CopyFilesAction({"manifest_file": str(manifest)})
    with pytest.raises(ValueError, match="not valid JSON"):
        action.execute(ctx, lambda *_: None, lambda *_: None)


def test_copy_files_fails_for_invalid_manifest_shape(tmp_path):
    _write_manifest(tmp_path / "copy_manifest.json", {"schema_version": 2, "files": []})
    ctx = make_context(tmp_path)
    action = CopyFilesAction({"manifest_file": "copy_manifest.json"})
    with pytest.raises(ValueError, match="schema_version=1"):
        action.execute(ctx, lambda *_: None, lambda *_: None)


def test_copy_files_overwrite_defaults_true(tmp_path):
    src = tmp_path / "payload" / "a.txt"
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_text("new", encoding="utf-8")
    _write_manifest(
        tmp_path / "copy_manifest.json",
        {"schema_version": 1, "files": [{"source": "payload/a.txt", "target": "a.txt"}]},
    )

    ctx = make_context(tmp_path, install_dir=str(tmp_path / "install"))
    dst = tmp_path / "install" / "a.txt"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text("old", encoding="utf-8")

    action = CopyFilesAction({"manifest_file": "copy_manifest.json"})
    result = action.execute(ctx, lambda *_: None, lambda *_: None)

    assert dst.read_text(encoding="utf-8") == "new"
    assert result["copied_items"] == 1


def test_copy_files_respects_entry_overwrite_false(tmp_path):
    src = tmp_path / "payload" / "a.txt"
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_text("new", encoding="utf-8")
    _write_manifest(
        tmp_path / "copy_manifest.json",
        {"schema_version": 1, "files": [{"source": "payload/a.txt", "target": "a.txt", "overwrite": False}]},
    )

    ctx = make_context(tmp_path, install_dir=str(tmp_path / "install"))
    dst = tmp_path / "install" / "a.txt"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text("old", encoding="utf-8")

    action = CopyFilesAction({"manifest_file": "copy_manifest.json"})
    result = action.execute(ctx, lambda *_: None, lambda *_: None)

    assert dst.read_text(encoding="utf-8") == "old"
    assert result["copied_items"] == 0
    assert result["skipped_items"] == 1
    assert result["rollback_records"] == []


def test_copy_files_rejects_target_traversal(tmp_path):
    src = tmp_path / "payload" / "a.txt"
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_text("x", encoding="utf-8")
    _write_manifest(
        tmp_path / "copy_manifest.json",
        {"schema_version": 1, "files": [{"source": "payload/a.txt", "target": "../outside.txt"}]},
    )

    ctx = make_context(tmp_path, install_dir=str(tmp_path / "install"))
    action = CopyFilesAction({"manifest_file": "copy_manifest.json"})

    with pytest.raises(ValueError, match="escapes install_dir"):
        action.execute(ctx, lambda *_: None, lambda *_: None)


def test_copy_files_manifest_helpers_and_validation_branches(monkeypatch, tmp_path):
    action = CopyFilesAction({"manifest_file": "x"})
    ctx = make_context(tmp_path, install_dir=str(tmp_path / "install"))

    abs_manifest = tmp_path / "abs_manifest.json"
    _write_manifest(abs_manifest, {"schema_version": 1, "files": [{"source": "s", "target": "t"}]})
    assert action._resolve_manifest_file(ctx, str(abs_manifest)) == abs_manifest

    bundled_manifest = tmp_path / "bundled_manifest.json"
    _write_manifest(bundled_manifest, {"schema_version": 1, "files": [{"source": "s", "target": "t"}]})
    monkeypatch.setattr("installer_framework.app.resources.resource_path", lambda _rel: bundled_manifest)
    assert action._resolve_manifest_file(ctx, "missing.json") == bundled_manifest

    bad_object = tmp_path / "bad_object.json"
    bad_object.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="JSON object"):
        action._load_manifest(bad_object)

    bad_files = tmp_path / "bad_files.json"
    _write_manifest(bad_files, {"schema_version": 1, "files": "x"})
    with pytest.raises(ValueError, match="non-empty 'files' array"):
        action._load_manifest(bad_files)

    bad_entry = tmp_path / "bad_entry.json"
    _write_manifest(bad_entry, {"schema_version": 1, "files": ["x"]})
    with pytest.raises(ValueError, match="entry #1 must be an object"):
        action._load_manifest(bad_entry)

    missing_source = tmp_path / "missing_source.json"
    _write_manifest(missing_source, {"schema_version": 1, "files": [{"target": "t"}]})
    with pytest.raises(ValueError, match="requires non-empty string 'source'"):
        action._load_manifest(missing_source)

    missing_target = tmp_path / "missing_target.json"
    _write_manifest(missing_target, {"schema_version": 1, "files": [{"source": "s"}]})
    with pytest.raises(ValueError, match="requires non-empty string 'target'"):
        action._load_manifest(missing_target)

    bad_overwrite = tmp_path / "bad_overwrite.json"
    _write_manifest(
        bad_overwrite,
        {"schema_version": 1, "files": [{"source": "s", "target": "t", "overwrite": "yes"}]},
    )
    with pytest.raises(ValueError, match="'overwrite' must be boolean"):
        action._load_manifest(bad_overwrite)


def test_copy_files_source_and_target_resolution_branches(monkeypatch, tmp_path):
    action = CopyFilesAction({"manifest_file": "x"})
    ctx = make_context(tmp_path, install_dir=str(tmp_path / "install"))
    manifest = tmp_path / "copy_manifest.json"
    _write_manifest(manifest, {"schema_version": 1, "files": [{"source": "s", "target": "t"}]})

    abs_source = tmp_path / "abs.txt"
    abs_source.write_text("x", encoding="utf-8")
    assert action._resolve_entry_source(ctx, manifest, str(abs_source)) == abs_source

    manifest_source = tmp_path / "manifest_rel.txt"
    manifest_source.write_text("x", encoding="utf-8")
    assert action._resolve_entry_source(ctx, manifest, "manifest_rel.txt") == manifest_source.resolve()

    root_source = tmp_path / "root_rel.txt"
    root_source.write_text("x", encoding="utf-8")
    assert action._resolve_entry_source(ctx, manifest, "root_rel.txt") == root_source.resolve()

    bundled_source = tmp_path / "bundled.txt"
    bundled_source.write_text("x", encoding="utf-8")
    monkeypatch.setattr("installer_framework.app.resources.resource_path", lambda _rel: bundled_source)
    assert action._resolve_entry_source(ctx, manifest, "missing.txt") == bundled_source

    assert action._resolve_target_path(Path(ctx.state.install_dir), "ok/file.txt").name == "file.txt"
    with pytest.raises(ValueError, match="install-relative"):
        action._resolve_target_path(Path(ctx.state.install_dir), str((tmp_path / "abs-target.txt").resolve()))


def test_copy_files_copy_path_and_execute_cancel_branches(monkeypatch, tmp_path):
    src = tmp_path / "a.txt"
    src.write_text("a", encoding="utf-8")
    dst = tmp_path / "install" / "a.txt"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text("old", encoding="utf-8")

    class _Tx:
        def create_file_backup(self, _path):
            raise RuntimeError("backup failed")

    ctx = make_context(tmp_path, install_dir=str(tmp_path / "install"))
    ctx.transaction = _Tx()
    action = CopyFilesAction({"manifest_file": "copy_manifest.json", "preserve_permissions": False})

    records = []
    copied = action._copy_path(src, dst, True, False, records, "auto", ctx)
    assert copied is True
    assert records and records[0]["backup_path"] is None

    with pytest.raises(ValueError, match="must be a file"):
        action._copy_path(tmp_path, dst, True, True, [], "auto", ctx)

    _write_manifest(
        tmp_path / "copy_manifest.json",
        {"schema_version": 1, "files": [{"source": "a.txt", "target": "out.txt"}]},
    )
    ctx.cancel()
    logs: list[str] = []
    result = action.execute(ctx, lambda *_: None, logs.append)
    assert result["copied_items"] == 0
    assert any("cancelled" in line for line in logs)


def test_copy_files_entry_source_raises_when_resource_lookup_fails(monkeypatch, tmp_path):
    action = CopyFilesAction({"manifest_file": "x"})
    ctx = make_context(tmp_path, install_dir=str(tmp_path / "install"))
    manifest = tmp_path / "copy_manifest.json"
    _write_manifest(manifest, {"schema_version": 1, "files": [{"source": "s", "target": "t"}]})

    resources_mod = ModuleType("installer_framework.app.resources")

    def _boom(_value):
        raise RuntimeError("resource failure")

    resources_mod.resource_path = _boom  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "installer_framework.app.resources", resources_mod)

    with pytest.raises(FileNotFoundError, match="source not found"):
        action._resolve_entry_source(ctx, manifest, "missing-source.txt")
