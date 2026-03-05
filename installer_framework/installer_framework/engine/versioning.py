"""Semantic version helpers."""

from __future__ import annotations

from packaging.version import Version, InvalidVersion



def compare_versions(left: str, right: str) -> int:
    """Return -1 if left<right, 0 if equal, 1 if left>right."""
    try:
        l = Version(left)
        r = Version(right)
    except InvalidVersion:
        if left == right:
            return 0
        return -1 if left < right else 1

    if l == r:
        return 0
    return -1 if l < r else 1
