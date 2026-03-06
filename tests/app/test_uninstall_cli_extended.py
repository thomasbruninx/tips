from __future__ import annotations

from argparse import Namespace
from pathlib import Path

from installer_framework.engine.uninstall_runner import UninstallResult
from installer_framework import uninstall_cli


def test_prompt_modified_loops_until_valid(monkeypatch):
    answers = iter(["?", "skip"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))
    assert uninstall_cli._prompt_modified(Path("/tmp/x"), "delete") == "skip"


def test_resolve_manifest_variants(tmp_path):
    ns = Namespace(manifest=str(tmp_path / "m.json"), install_dir=None)
    assert uninstall_cli._resolve_manifest(ns) == (tmp_path / "m.json").resolve()

    ns = Namespace(manifest=None, install_dir=str(tmp_path / "install"))
    resolved = uninstall_cli._resolve_manifest(ns)
    assert resolved == (tmp_path / "install" / ".tips" / "manifest.json").resolve()

    default_manifest = tmp_path / "default.json"
    ns = Namespace(manifest=None, install_dir=None)
    assert uninstall_cli._resolve_manifest(ns, default_manifest=default_manifest) == default_manifest


def test_main_cancelled_and_error_paths(monkeypatch, tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text("{}", encoding="utf-8")

    monkeypatch.setattr(
        uninstall_cli,
        "parse_args",
        lambda default_manifest=None: Namespace(
            manifest=str(manifest),
            install_dir=None,
            silent=False,
            delete_modified=False,
            modified_file_policy="prompt",
        ),
    )
    monkeypatch.setattr(
        uninstall_cli,
        "run_uninstall",
        lambda **kwargs: UninstallResult(success=False, cancelled=True),
    )
    assert uninstall_cli.main() == 2

    monkeypatch.setattr(
        uninstall_cli,
        "run_uninstall",
        lambda **kwargs: UninstallResult(success=False, cancelled=False, errors=["boom"]),
    )
    assert uninstall_cli.main() == 1


def test_run_uninstall_disables_prompt_callback_when_not_interactive(monkeypatch, tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text("{}", encoding="utf-8")
    captured: dict[str, object] = {}

    class _Runner:
        def __init__(self, manifest_file, options):
            captured["manifest"] = manifest_file
            captured["options"] = options

        def run(self, progress_callback, log_callback, prompt_callback=None):
            captured["prompt_callback"] = prompt_callback
            progress_callback(5, "x")
            log_callback("y")
            return UninstallResult(success=True, cancelled=False)

    monkeypatch.setattr(uninstall_cli, "UninstallRunner", _Runner)
    result = uninstall_cli.run_uninstall(
        manifest,
        uninstall_cli.UninstallOptions(silent=True, modified_file_policy="skip"),
        interactive_prompt=False,
    )
    assert result.success is True
    assert captured["prompt_callback"] is None
