"""Plugin subsystem exports."""

from installer_framework.plugins.discovery import PluginLoadError, discover_and_register_plugins, resolve_plugin_roots
from installer_framework.plugins.models import PluginDiscoveryResult, PluginMetadata, PluginSchemaExtension, PluginStatus
from installer_framework.plugins.registry import PluginRegistry, build_registry_with_builtins
from installer_framework.plugins.schema_compose import compose_schema

__all__ = [
    "PluginDiscoveryResult",
    "PluginLoadError",
    "PluginMetadata",
    "PluginRegistry",
    "PluginSchemaExtension",
    "PluginStatus",
    "build_registry_with_builtins",
    "compose_schema",
    "discover_and_register_plugins",
    "resolve_plugin_roots",
]
