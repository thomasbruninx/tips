#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

resolve_python() {
  if [[ -n "${PYTHON:-}" ]]; then
    echo "$PYTHON"
    return
  fi
  if [[ -x "$PROJECT_ROOT/.venv/bin/python" ]]; then
    echo "$PROJECT_ROOT/.venv/bin/python"
    return
  fi
  if command -v python3 >/dev/null 2>&1; then
    command -v python3
    return
  fi
  if command -v python >/dev/null 2>&1; then
    command -v python
    return
  fi
  echo "No Python interpreter found. Set PYTHON or create .venv/bin/python." >&2
  exit 1
}

PYTHON_BIN="$(resolve_python)"
OUT_DIR="$PROJECT_ROOT/dist/linux"
mkdir -p "$OUT_DIR"
REPO_ROOT="$(cd "$PROJECT_ROOT/.." && pwd)"
PLUGINS_DIR="$REPO_ROOT/plugins"

PYINSTALLER_ARGS=(
  --noconfirm
  --clean
  --onedir
  --windowed
  --name tips-installer
  --hidden-import PyQt6.QtCore
  --hidden-import PyQt6.QtGui
  --hidden-import PyQt6.QtWidgets
  --hidden-import PyQt6.sip
  --add-data "examples:examples"
  --add-data "installer_framework/config/schema.json:installer_framework/config"
)

if [[ -d "$PLUGINS_DIR" ]]; then
  echo "Checking plugins in: $PLUGINS_DIR"
  "$PYTHON_BIN" - "$PROJECT_ROOT" "$PLUGINS_DIR" <<'PY'
from pathlib import Path
import sys

project_root = Path(sys.argv[1]).resolve()
plugins_dir = Path(sys.argv[2]).resolve()
sys.path.insert(0, str(project_root))

from installer_framework import __version__
from installer_framework.plugins.discovery import discover_and_register_plugins
from installer_framework.plugins.registry import build_registry_with_builtins

registry = build_registry_with_builtins()
result = discover_and_register_plugins(registry=registry, roots=[plugins_dir], framework_version=__version__)
if not result.statuses:
    print("No plugins discovered.")
for status in result.statuses:
    suffix = f" ({status.reason})" if status.reason else ""
    print(f"{status.status.upper()}: {status.plugin_type}:{status.handle} @ {status.plugin_dir}{suffix}")
PY
  PYINSTALLER_ARGS+=(--add-data "$PLUGINS_DIR:plugins")
fi

"$PYTHON_BIN" -m PyInstaller "${PYINSTALLER_ARGS[@]}" installer_framework/main.py

rm -rf "$OUT_DIR/tips-installer"
cp -R "dist/tips-installer" "$OUT_DIR/tips-installer"
echo "Build complete: $OUT_DIR"
