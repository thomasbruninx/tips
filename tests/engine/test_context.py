from __future__ import annotations

from tests.helpers.context_factory import make_context


def test_context_cancel_flag(tmp_path):
    ctx = make_context(tmp_path)
    assert ctx.is_cancelled() is False
    ctx.cancel()
    assert ctx.is_cancelled() is True


def test_context_resume_roundtrip(tmp_path):
    ctx = make_context(tmp_path)
    ctx.state.answers["x"] = 1
    ctx.state.install_dir = str(tmp_path / "install")
    ctx.save_resume()

    other = make_context(tmp_path)
    assert other.load_resume() is True
    assert other.state.answers["x"] == 1
    other.clear_resume()
    assert other.resume_path().exists() is False
