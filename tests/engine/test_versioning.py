from __future__ import annotations

from installer_framework.engine.versioning import compare_versions


def test_compare_versions_semver():
    assert compare_versions("1.0.0", "1.0.1") == -1
    assert compare_versions("1.0.1", "1.0.1") == 0
    assert compare_versions("2.0.0", "1.9.9") == 1


def test_compare_versions_invalid_fallback():
    assert compare_versions("alpha", "beta") == -1
    assert compare_versions("same", "same") == 0
