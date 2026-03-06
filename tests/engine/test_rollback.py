from __future__ import annotations

from pathlib import Path

from installer_framework.engine.rollback import InstallTransaction, remove_empty_parents
from tests.helpers.context_factory import make_context


def test_remove_empty_parents_removes_chain(tmp_path):
    leaf = tmp_path / "a" / "b" / "c"
    leaf.mkdir(parents=True)
    remove_empty_parents(leaf, tmp_path)
    assert (tmp_path / "a").exists() is False


def test_install_transaction_journal_and_rollback_file(tmp_path):
    ctx = make_context(tmp_path)
    ctx.state.install_dir = str(tmp_path / "install")
    logs: list[str] = []
    tx = InstallTransaction(ctx, log_callback=logs.append)
    tx.start()

    target = Path(ctx.state.install_dir) / "data.txt"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("new", encoding="utf-8")

    tx.register_records(
        action_type="copy_files",
        rollback_policy="auto",
        records=[{"kind": "file", "path": str(target), "existed_before": False}],
    )

    assert tx.load_records_from_journal()
    errors = tx.rollback()
    assert errors == []
    assert target.exists() is False
