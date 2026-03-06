from __future__ import annotations

import json

from installer_framework.uninstall_cli import main


def test_uninstall_cli_main_success(monkeypatch, tmp_path):
    manifest = tmp_path / ".tips" / "manifest.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps({"install_dir": str(tmp_path), "artifacts": [], "uninstall": {}}), encoding="utf-8")

    monkeypatch.setattr("sys.argv", ["prog", "--manifest", str(manifest), "--silent"])
    code = main()
    assert code == 0
