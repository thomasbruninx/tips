"""Plugin model objects for discovery, registration, and schema composition."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class PluginMetadata:
    plugin_type: str
    handle: str
    version: str
    min_framework_version: str
    max_framework_version: str
    plugin_dir: Path
    name: str | None = None
    description: str | None = None
    author: str | None = None


@dataclass(slots=True)
class PluginSchemaExtension:
    kind: str
    handle: str
    schema: dict[str, Any]


@dataclass(slots=True)
class PluginStatus:
    handle: str
    plugin_type: str
    plugin_dir: str
    version: str
    status: str
    reason: str | None = None


@dataclass(slots=True)
class PluginDiscoveryResult:
    schema_extensions: list[PluginSchemaExtension] = field(default_factory=list)
    statuses: list[PluginStatus] = field(default_factory=list)
    roots: list[str] = field(default_factory=list)
