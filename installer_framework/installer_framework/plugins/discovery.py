"""Discovery and loading for external .tipsplugin extensions."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import logging
import os
import re
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

from packaging.version import Version, InvalidVersion

from installer_framework import __version__
from installer_framework.app.resources import resource_path
from installer_framework.engine.action_base import Action
from installer_framework.plugins.models import PluginDiscoveryResult, PluginMetadata, PluginSchemaExtension, PluginStatus
from installer_framework.plugins.registry import PluginRegistry
from installer_framework.ui.step_base import StepWidget

LOGGER = logging.getLogger(__name__)


class PluginLoadError(RuntimeError):
    """Raised when plugin content is invalid and cannot be loaded."""



def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise PluginLoadError(f"Failed to read JSON file {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise PluginLoadError(f"Expected object JSON in {path}")
    return payload



def _find_repo_root(start: Path) -> Path | None:
    for candidate in (start, *start.parents):
        if (candidate / ".git").exists():
            return candidate
    return None



def resolve_plugin_roots(source_root: Path, plugins_dir: str | None = None) -> list[Path]:
    """Resolve plugin roots by configured discovery order."""
    roots: list[Path] = []

    def _add(value: str | Path | None) -> None:
        if not value:
            return
        path = Path(value).expanduser()
        if not path.is_absolute():
            path = (Path.cwd() / path).resolve()
        if path not in roots:
            roots.append(path)

    _add(plugins_dir)
    _add(os.environ.get("TIPS_PLUGINS_DIR"))

    is_frozen = bool(getattr(sys, "frozen", False) or getattr(sys, "_MEIPASS", None))
    if not is_frozen:
        repo_root = _find_repo_root(source_root.resolve())
        if repo_root is not None:
            _add(repo_root / "plugins")

    bundled = resource_path("plugins")
    _add(bundled)

    return [path for path in roots if path.exists() and path.is_dir()]



def _metadata_from_dir(plugin_dir: Path) -> PluginMetadata:
    metadata_path = plugin_dir / "metadata.json"
    plugin_path = plugin_dir / "plugin.py"
    schema_path = plugin_dir / "schema.json"

    missing = [str(path.name) for path in (metadata_path, plugin_path, schema_path) if not path.exists()]
    if missing:
        raise PluginLoadError(f"Plugin {plugin_dir} is missing required file(s): {', '.join(missing)}")

    raw = _read_json(metadata_path)
    required = ["type", "handle", "version", "min_framework_version", "max_framework_version"]
    missing_keys = [key for key in required if key not in raw]
    if missing_keys:
        raise PluginLoadError(f"Plugin {plugin_dir} metadata missing required key(s): {', '.join(missing_keys)}")

    plugin_type = str(raw["type"]).strip()
    if plugin_type not in {"action", "step"}:
        raise PluginLoadError(f"Plugin {plugin_dir} has invalid metadata type: {plugin_type}")

    handle = str(raw["handle"]).strip()
    if not handle:
        raise PluginLoadError(f"Plugin {plugin_dir} has empty metadata handle")

    return PluginMetadata(
        plugin_type=plugin_type,
        handle=handle,
        version=str(raw["version"]),
        min_framework_version=str(raw["min_framework_version"]),
        max_framework_version=str(raw["max_framework_version"]),
        plugin_dir=plugin_dir,
        name=str(raw.get("name")) if raw.get("name") is not None else None,
        description=str(raw.get("description")) if raw.get("description") is not None else None,
        author=str(raw.get("author")) if raw.get("author") is not None else None,
    )



def _is_version_compatible(metadata: PluginMetadata, framework_version: str) -> tuple[bool, str | None]:
    try:
        framework_v = Version(framework_version)
        min_v = Version(metadata.min_framework_version)
        max_v = Version(metadata.max_framework_version)
    except InvalidVersion as exc:
        raise PluginLoadError(f"Plugin {metadata.plugin_dir} has invalid version metadata: {exc}") from exc

    if framework_v < min_v or framework_v > max_v:
        reason = (
            f"framework {framework_version} is outside supported range "
            f"[{metadata.min_framework_version}, {metadata.max_framework_version}]"
        )
        return False, reason
    return True, None



def _schema_extension_from_dir(plugin_dir: Path, metadata: PluginMetadata) -> PluginSchemaExtension:
    schema_path = plugin_dir / "schema.json"
    payload = _read_json(schema_path)

    required = ["kind", "handle", "schema"]
    missing = [key for key in required if key not in payload]
    if missing:
        raise PluginLoadError(f"Plugin {plugin_dir} schema.json missing key(s): {', '.join(missing)}")

    kind = str(payload["kind"]).strip()
    if kind not in {"action", "step"}:
        raise PluginLoadError(f"Plugin {plugin_dir} schema kind must be 'action' or 'step', got: {kind}")

    handle = str(payload["handle"]).strip()
    if handle != metadata.handle:
        raise PluginLoadError(
            f"Plugin {plugin_dir} schema handle '{handle}' does not match metadata handle '{metadata.handle}'"
        )

    if kind != metadata.plugin_type:
        raise PluginLoadError(
            f"Plugin {plugin_dir} schema kind '{kind}' does not match metadata type '{metadata.plugin_type}'"
        )

    extension_schema = payload["schema"]
    if not isinstance(extension_schema, dict):
        raise PluginLoadError(f"Plugin {plugin_dir} schema field 'schema' must be an object")

    return PluginSchemaExtension(kind=kind, handle=handle, schema=extension_schema)



def _load_plugin_module(plugin_dir: Path, handle: str) -> ModuleType:
    plugin_file = plugin_dir / "plugin.py"
    token = hashlib.sha1(str(plugin_file).encode("utf-8")).hexdigest()[:12]
    safe_handle = re.sub(r"[^a-zA-Z0-9_]", "_", handle)
    module_name = f"tips_plugin_{safe_handle}_{token}"
    spec = importlib.util.spec_from_file_location(module_name, plugin_file)
    if spec is None or spec.loader is None:
        raise PluginLoadError(f"Could not create import spec for plugin {plugin_file}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module



def _validate_registration_payload(module: ModuleType, metadata: PluginMetadata) -> dict[str, Any]:
    register = getattr(module, "register", None)
    if register is None or not callable(register):
        raise PluginLoadError(f"Plugin {metadata.plugin_dir} must define callable register() in plugin.py")

    payload = register()
    if not isinstance(payload, dict):
        raise PluginLoadError(f"Plugin {metadata.plugin_dir} register() must return a dict")

    if metadata.plugin_type == "action":
        action_class = payload.get("action_class")
        if not isinstance(action_class, type) or not issubclass(action_class, Action):
            raise PluginLoadError(
                f"Plugin {metadata.plugin_dir} must return action_class subclassing Action for type=action"
            )
    else:
        step_class = payload.get("step_class")
        if not isinstance(step_class, type) or not issubclass(step_class, StepWidget):
            raise PluginLoadError(
                f"Plugin {metadata.plugin_dir} must return step_class subclassing StepWidget for type=step"
            )

    return payload



def discover_and_register_plugins(
    registry: PluginRegistry,
    roots: list[Path],
    framework_version: str = __version__,
) -> PluginDiscoveryResult:
    result = PluginDiscoveryResult(roots=[str(root) for root in roots])

    plugin_dirs: list[Path] = []
    for root in roots:
        for candidate in sorted(root.glob("*.tipsplugin")):
            if candidate.is_dir():
                plugin_dirs.append(candidate.resolve())

    for plugin_dir in plugin_dirs:
        metadata = _metadata_from_dir(plugin_dir)

        compatible, reason = _is_version_compatible(metadata, framework_version)
        if not compatible:
            warning = (
                f"Skipping incompatible plugin '{metadata.handle}' at {plugin_dir}: {reason}"
            )
            LOGGER.warning(warning)
            status = PluginStatus(
                handle=metadata.handle,
                plugin_type=metadata.plugin_type,
                plugin_dir=str(plugin_dir),
                version=metadata.version,
                status="skipped",
                reason=reason,
            )
            registry.add_status(status)
            result.statuses.append(status)
            continue

        extension = _schema_extension_from_dir(plugin_dir, metadata)
        module = _load_plugin_module(plugin_dir, metadata.handle)
        payload = _validate_registration_payload(module, metadata)

        if metadata.plugin_type == "action":
            registry.register_action(metadata.handle, payload["action_class"], source=str(plugin_dir))
        else:
            registry.register_step(metadata.handle, payload["step_class"], source=str(plugin_dir))

        registry.add_extension(extension)
        status = PluginStatus(
            handle=metadata.handle,
            plugin_type=metadata.plugin_type,
            plugin_dir=str(plugin_dir),
            version=metadata.version,
            status="loaded",
            reason=None,
        )
        registry.add_status(status)
        result.statuses.append(status)
        result.schema_extensions.append(extension)
        LOGGER.info("Loaded plugin '%s' (%s) from %s", metadata.handle, metadata.plugin_type, plugin_dir)

    return result
