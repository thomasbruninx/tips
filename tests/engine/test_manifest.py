from __future__ import annotations

from installer_framework.engine import manifest


def test_manifest_paths_and_json_roundtrip(tmp_path):
    install_dir = tmp_path / "install"
    manifest.ensure_meta_layout(install_dir)

    mpath = manifest.manifest_path(install_dir)
    payload = {"ok": True}
    manifest.save_json(mpath, payload)

    assert mpath.exists()
    assert manifest.load_json(mpath) == payload
    assert manifest.tips_meta_dir(install_dir).name == ".tips"


def test_file_sha256_changes_with_content(tmp_path):
    target = tmp_path / "a.txt"
    target.write_text("one", encoding="utf-8")
    first = manifest.file_sha256(target)
    target.write_text("two", encoding="utf-8")
    second = manifest.file_sha256(target)
    assert first != second
