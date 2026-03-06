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
if [[ $# -lt 1 || -z "${1:-}" ]]; then
  echo "Error: missing config path." >&2
  echo "Usage: ./build/build_linux.sh <config.json>" >&2
  exit 1
fi
CONFIG_ARG="$1"
CONFIG_PATH="$($PYTHON_BIN - "$PROJECT_ROOT" "$CONFIG_ARG" <<'PY'
from pathlib import Path
import sys

root = Path(sys.argv[1])
arg = Path(sys.argv[2]).expanduser()
if not arg.is_absolute():
    arg = root / arg
print(arg.resolve())
PY
)"
"$PYTHON_BIN" - "$CONFIG_PATH" <<'PY'
import json
import sys
from pathlib import Path

config_path = Path(sys.argv[1]).resolve()
if config_path.suffix.lower() != ".json":
    print(f"Error: config path must point to a .json file: {config_path}", file=sys.stderr)
    raise SystemExit(1)
if not config_path.exists():
    print(f"Error: config file not found: {config_path}", file=sys.stderr)
    raise SystemExit(1)
if not config_path.is_file():
    print(f"Error: config path is not a file: {config_path}", file=sys.stderr)
    raise SystemExit(1)

try:
    payload = json.loads(config_path.read_text(encoding="utf-8"))
except Exception as exc:
    print(f"Error: invalid JSON in config file '{config_path}': {exc}", file=sys.stderr)
    raise SystemExit(1)

if not isinstance(payload, dict):
    print(f"Error: config root must be a JSON object: {config_path}", file=sys.stderr)
    raise SystemExit(1)
PY
PACKAGED_CONFIG_FILE="$PROJECT_ROOT/build/packaged_installer_config.json"
mkdir -p "$(dirname "$PACKAGED_CONFIG_FILE")"
cp "$CONFIG_PATH" "$PACKAGED_CONFIG_FILE"

resolve_typography_font_data_entries() {
  "$PYTHON_BIN" - "$PROJECT_ROOT" "$CONFIG_PATH" <<'PY'
import json
import sys
from pathlib import Path

project_root = Path(sys.argv[1]).resolve()
config_path = Path(sys.argv[2]).resolve()
if not config_path.exists():
    sys.exit(0)

try:
    payload = json.loads(config_path.read_text(encoding="utf-8"))
except Exception as exc:
    print(f"Warning: failed to parse config for typography font discovery: {exc}", file=sys.stderr)
    sys.exit(0)

fonts = (((payload.get("theme") or {}).get("typography") or {}).get("fonts") or [])
config_dir = config_path.parent

try:
    config_dir_rel = config_dir.relative_to(project_root)
except ValueError:
    config_dir_rel = Path("config_assets")

seen: set[tuple[str, str]] = set()
for item in fonts:
    if not isinstance(item, dict):
        continue
    raw_path = item.get("font_ttf_path")
    if not isinstance(raw_path, str) or not raw_path.strip():
        continue
    candidate = Path(raw_path).expanduser()
    if candidate.is_absolute():
        source = candidate.resolve()
        dest_dir = Path("fonts")
    else:
        source = (config_dir / candidate).resolve()
        parent = candidate.parent if str(candidate.parent) != "." else Path("")
        dest_dir = config_dir_rel / parent

    if not source.exists():
        print(f"Warning: configured font_ttf_path not found: {source}", file=sys.stderr)
        continue

    key = (str(source), dest_dir.as_posix())
    if key in seen:
        continue
    seen.add(key)
    print(f"{key[0]}|{key[1]}")
PY
}

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
  --add-data "$PACKAGED_CONFIG_FILE:build"
  --add-data "installer_framework/config/schema.json:installer_framework/config"
)

while IFS='|' read -r font_src font_dest; do
  [[ -z "${font_src:-}" || -z "${font_dest:-}" ]] && continue
  echo "Bundling typography font: $font_src -> $font_dest"
  PYINSTALLER_ARGS+=(--add-data "$font_src:$font_dest")
done < <(resolve_typography_font_data_entries)

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
