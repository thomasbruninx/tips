param(
  [string]$ConfigPath
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..")
Set-Location $ProjectRoot

function Resolve-ConfigPath([string]$PathArg) {
  if ([string]::IsNullOrWhiteSpace($PathArg)) {
    return $null
  }
  if ([System.IO.Path]::IsPathRooted($PathArg)) {
    return [System.IO.Path]::GetFullPath($PathArg)
  }
  return [System.IO.Path]::GetFullPath((Join-Path $ProjectRoot $PathArg))
}

function Assert-ValidConfigJson([string]$ResolvedConfigPath) {
  if ([string]::IsNullOrWhiteSpace($ResolvedConfigPath)) {
    throw "Error: missing config path. Usage: ./build/build_windows.ps1 -ConfigPath <config.json>"
  }

  if ([System.IO.Path]::GetExtension($ResolvedConfigPath).ToLowerInvariant() -ne ".json") {
    throw "Error: config path must point to a .json file: $ResolvedConfigPath"
  }

  if (-not (Test-Path -LiteralPath $ResolvedConfigPath -PathType Leaf)) {
    throw "Error: config file not found: $ResolvedConfigPath"
  }

  try {
    $payload = Get-Content -Raw -LiteralPath $ResolvedConfigPath | ConvertFrom-Json -ErrorAction Stop
  } catch {
    throw "Error: invalid JSON in config file '$ResolvedConfigPath': $($_.Exception.Message)"
  }

  if ($payload -isnot [pscustomobject] -and $payload -isnot [hashtable]) {
    throw "Error: config root must be a JSON object: $ResolvedConfigPath"
  }
}

function Get-WindowsIconPath([string]$ResolvedConfigPath) {
  if (-not $ResolvedConfigPath -or -not (Test-Path $ResolvedConfigPath)) {
    return $null
  }

  try {
    $raw = Get-Content -Raw -Path $ResolvedConfigPath
    $cfg = $raw | ConvertFrom-Json
  } catch {
    Write-Warning "Failed to parse config for icon lookup: $($_.Exception.Message)"
    return $null
  }

  $candidates = @()
  if ($cfg.windows -and $cfg.windows.installer_icon_ico) {
    $candidates += [string]$cfg.windows.installer_icon_ico
  }
  if ($cfg.branding -and $cfg.branding.windowIconPath) {
    $candidates += [string]$cfg.branding.windowIconPath
  }

  $configDir = Split-Path -Parent $ResolvedConfigPath
  foreach ($candidate in $candidates) {
    if ([string]::IsNullOrWhiteSpace($candidate)) {
      continue
    }

    $iconPath = if ([System.IO.Path]::IsPathRooted($candidate)) {
      [System.IO.Path]::GetFullPath($candidate)
    } else {
      [System.IO.Path]::GetFullPath((Join-Path $configDir $candidate))
    }

    if ([System.IO.Path]::GetExtension($iconPath).ToLowerInvariant() -ne ".ico") {
      continue
    }

    if (Test-Path $iconPath) {
      return $iconPath
    }

    Write-Warning "Configured Windows icon not found: $iconPath"
  }

  return $null
}

function Get-TypographyFontDataEntries([string]$ResolvedConfigPath) {
  if (-not $ResolvedConfigPath -or -not (Test-Path $ResolvedConfigPath)) {
    return @()
  }

  $DiscoveryScript = @'
import json
import sys
from pathlib import Path

project_root = Path(sys.argv[1]).resolve()
config_path = Path(sys.argv[2]).resolve()
config_dir = config_path.parent

try:
    payload = json.loads(config_path.read_text(encoding="utf-8"))
except Exception as exc:
    print(f"Warning: failed to parse config for typography font discovery: {exc}", file=sys.stderr)
    print("[]")
    raise SystemExit(0)

fonts = (((payload.get("theme") or {}).get("typography") or {}).get("fonts") or [])

try:
    config_dir_rel = config_dir.relative_to(project_root)
except ValueError:
    config_dir_rel = Path("config_assets")

entries: list[dict[str, str]] = []
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
        dest_dir = (config_dir_rel / parent).as_posix()
        dest_dir = Path(dest_dir)

    if not source.exists():
        print(f"Warning: configured font_ttf_path not found: {source}", file=sys.stderr)
        continue

    key = (str(source), dest_dir.as_posix())
    if key in seen:
        continue
    seen.add(key)
    entries.append({"src": str(source), "dest": dest_dir.as_posix()})

print(json.dumps(entries))
'@

  if ($UsePyLauncher) {
    $json = & $PythonExe -3 -c $DiscoveryScript $ProjectRoot $ResolvedConfigPath
  } else {
    $json = & $PythonExe -c $DiscoveryScript $ProjectRoot $ResolvedConfigPath
  }

  if ([string]::IsNullOrWhiteSpace($json)) {
    return @()
  }
  try {
    return $json | ConvertFrom-Json
  } catch {
    Write-Warning "Failed to parse typography font discovery output: $($_.Exception.Message)"
    return @()
  }
}

$PythonExe = $null
$UsePyLauncher = $false

if ($env:PYTHON) {
  $PythonExe = $env:PYTHON
} elseif (Test-Path (Join-Path $ProjectRoot ".venv/Scripts/python.exe")) {
  $PythonExe = Join-Path $ProjectRoot ".venv/Scripts/python.exe"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
  $PythonExe = (Get-Command python).Source
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
  $PythonExe = (Get-Command py).Source
  $UsePyLauncher = $true
} else {
  throw "No Python interpreter found. Set PYTHON or create .venv/Scripts/python.exe."
}

$ResolvedConfigPath = Resolve-ConfigPath $ConfigPath
Assert-ValidConfigJson $ResolvedConfigPath
$PackagedConfigFile = Join-Path $ProjectRoot "build/packaged_installer_config.json"
New-Item -ItemType Directory -Path (Split-Path -Parent $PackagedConfigFile) -Force | Out-Null
Copy-Item -Path $ResolvedConfigPath -Destination $PackagedConfigFile -Force
$IconPath = Get-WindowsIconPath $ResolvedConfigPath
$TypographyFontEntries = Get-TypographyFontDataEntries $ResolvedConfigPath
$RepoRoot = Resolve-Path (Join-Path $ProjectRoot "..")
$PluginsRoot = Join-Path $RepoRoot "plugins"

$OutDir = Join-Path $ProjectRoot "dist/windows"
New-Item -ItemType Directory -Path $OutDir -Force | Out-Null
$ToolsDir = Join-Path $ProjectRoot "tools"
New-Item -ItemType Directory -Path $ToolsDir -Force | Out-Null
$BundledUninstaller = Join-Path $ToolsDir "tips-uninstaller.exe"

function Invoke-PyInstaller([string[]]$ArgsList) {
  if ($UsePyLauncher) {
    & $PythonExe -3 @ArgsList
  } else {
    & $PythonExe @ArgsList
  }
}

$CommonArgs = @(
  "-m", "PyInstaller",
  "--noconfirm",
  "--clean",
  "--onefile",
  "--windowed",
  "--hidden-import", "PyQt6.QtCore",
  "--hidden-import", "PyQt6.QtGui",
  "--hidden-import", "PyQt6.QtWidgets",
  "--hidden-import", "PyQt6.sip",
  "--add-data", "examples;examples",
  "--add-data", "$PackagedConfigFile;build",
  "--add-data", "installer_framework/config/schema.json;installer_framework/config",
  "--add-data", "tools;tools"
)

if ($IconPath) {
  Write-Host "Using Windows installer icon: $IconPath"
  $CommonArgs += @("--icon", $IconPath)
}

if ($TypographyFontEntries.Count -gt 0) {
  foreach ($entry in $TypographyFontEntries) {
    if (-not $entry.src -or -not $entry.dest) {
      continue
    }
    Write-Host "Bundling typography font: $($entry.src) -> $($entry.dest)"
    $CommonArgs += @("--add-data", "$($entry.src);$($entry.dest)")
  }
}

if (Test-Path $PluginsRoot) {
  Write-Host "Checking plugins in: $PluginsRoot"
  $DiagScript = @'
from pathlib import Path
import sys

project_root = Path(sys.argv[1]).resolve()
plugins_root = Path(sys.argv[2]).resolve()
sys.path.insert(0, str(project_root))

from installer_framework import __version__
from installer_framework.plugins.discovery import discover_and_register_plugins
from installer_framework.plugins.registry import build_registry_with_builtins

registry = build_registry_with_builtins()
result = discover_and_register_plugins(registry=registry, roots=[plugins_root], framework_version=__version__)
if not result.statuses:
    print("No plugins discovered.")
for status in result.statuses:
    suffix = f" ({status.reason})" if status.reason else ""
    print(f"{status.status.upper()}: {status.plugin_type}:{status.handle} @ {status.plugin_dir}{suffix}")
'@
  if ($UsePyLauncher) {
    & $PythonExe -3 -c $DiagScript $ProjectRoot $PluginsRoot
  } else {
    & $PythonExe -c $DiagScript $ProjectRoot $PluginsRoot
  }
  $CommonArgs += @("--add-data", "$PluginsRoot;plugins")
}

$UninstallerArgs = @($CommonArgs + @("--name", "tips-uninstaller", "installer_framework/uninstaller_main.py"))
Invoke-PyInstaller -ArgsList $UninstallerArgs

if (-not (Test-Path "dist/tips-uninstaller.exe")) {
  throw "Expected dist/tips-uninstaller.exe after build, but it was not generated."
}
Copy-Item -Force "dist/tips-uninstaller.exe" $BundledUninstaller

$InstallerArgs = @($CommonArgs + @("--name", "tips-installer", "installer_framework/main.py"))
Invoke-PyInstaller -ArgsList $InstallerArgs

Copy-Item -Force "dist/tips-installer.exe" (Join-Path $OutDir "tips-installer.exe")
Copy-Item -Force $BundledUninstaller (Join-Path $OutDir "tips-uninstaller.exe")
Write-Host "Build complete: $OutDir"
