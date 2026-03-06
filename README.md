# TIPS Framework

TIPS = **TIPS Instructable Python Setup**.

This project provides a JSON-driven, **PyQt6**-based installer framework for Windows, Linux, and macOS. It supports classic and modern installer wizard UI themes, validation, install scope (`user`/`system`/`ask`), background action execution with progress/logging, and upgrade detection.

## Features

- Installer shell UI themes:
  - `classic`
  - `modern`
  - left branding/sidebar panel (classic)
  - top header + flat content shell (modern)
  - step header area
  - content area for step widgets
  - navigation bar (`< Back`, `Next >`, `Install`, `Finish`, `Cancel`)
- JSON-defined installer flow:
  - step order
  - optional conditions (`show_if`)
  - field definitions and validations
  - install actions
- Theme block (`theme.style = "classic"` or `"modern"`) with colors, metrics, typography, and artwork paths
- Install scopes:
  - `user`
  - `system`
  - `ask`
- Threaded install execution:
  - actions run in worker thread
  - progress/logs marshaled to UI via Qt signals
- Action engine:
  - `copy_files`
  - `write_registry` / `read_registry` (Windows)
  - `write_dotfile`
  - `create_shortcut` (Windows)
  - `create_desktop_entry` (Linux)
  - `show_message`
  - `run_script` (restricted context)
- Transactional install safety:
  - per-action rollback policy (`auto`, `delete_only`, `none`)
  - rollback journal during install
  - automatic rollback on failure or cancellation
- Manifest-driven uninstall:
  - tracked artifacts in `install_dir/.tips/manifest.json`
  - Windows GUI uninstaller executable
  - Linux/macOS CLI uninstaller script
  - modified-file handling (`prompt`/`skip`/`delete`)
- Upgrade detection:
  - Windows registry (HKCU/HKLM)
  - Unix metadata file in user/system config paths
- PyInstaller build scripts for all target platforms

## Repository Layout

```text
installer_framework/
  pyproject.toml
  README.md
  LICENSE
  installer_framework/
    main.py
    uninstaller_main.py
    uninstall_cli.py
    app/
      qt_app.py
      qt_uninstaller_app.py
      paths.py
      resources.py
    config/
      schema.json
      loader.py
      models.py
      validation.py
      conditions.py
    ui/
      theme.py
      wizard.py
      step_base.py
      step_factory.py
      steps/
        welcome.py
        license.py
        scope.py
        directory.py
        options.py
        form.py
        ready.py
        install.py
        finish.py
      uninstall_wizard.py
      widgets/
        theme.py
        classic_theme.py
        modern_theme.py
        dialogs.py
        validated_text_input.py
        feature_list.py
        log_pane.py
    engine/
      context.py
      runner.py
      manifest.py
      rollback.py
      uninstall_runner.py
      action_base.py
      actions/
        copy_files.py
        registry.py
        dotfile.py
        shortcut_windows.py
        desktop_entry_linux.py
        show_message.py
        run_script.py
      upgrade.py
      versioning.py
    util/
      safe_eval.py
      fs.py
      platform.py
      privileges.py
  examples/
    sample_installer.json
    assets/
      logo.png
      appicon.ico
      appicon.icns
      license.txt
      payload/
        README.txt
  build/
    build_windows.ps1
    build_linux.sh
    build_macos.sh
```

## Run From Source

```bash
cd installer_framework
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .[dev]
python -m installer_framework.main --config examples/sample_installer.json
```

Optional resume mode:

```bash
python -m installer_framework.main --config examples/sample_installer.json --resume
```

Resume state file: temp path `tips_installer_resume.json`.

## JSON Config Model

Full schema: `installer_framework/config/schema.json`.

### Branding

```json
"branding": {
  "productName": "TIPS Demo App",
  "publisher": "TIPS",
  "version": "1.0.0",
  "logoPath": "assets/logo.png",
  "windowIconPath": "assets/logo.png"
}
```

For packaged installer executable icons, use platform-specific keys:

```json
"windows": {
  "installer_icon_ico": "assets/appicon.ico"
},
"macos": {
  "installer_icon_icns": "assets/appicon.icns"
}
```

Build scripts resolve these paths relative to the JSON config file directory.

### Theme

`theme` is optional; defaults are applied if omitted. Available styles are `classic` and `modern`.
Theme widget implementations live in:
- `installer_framework/ui/widgets/theme.py` (abstractions + factory selection)
- `installer_framework/ui/widgets/classic_theme.py`
- `installer_framework/ui/widgets/modern_theme.py`

Modern theme behavior:
- Uses a macOS Installer-inspired shell (no left sidebar).
- Keeps wizard labels unchanged (`< Back`, `Next >`, `Install`, `Finish`, `Cancel`).
- Header artwork resolution order:
  1. `branding.logoPath`
  2. `theme.assets.header_image_path`
  3. `theme.assets.sidebar_image_path`
  4. text-only header fallback

```json
"theme": {
  "style": "classic",
  "assets": {
    "sidebar_image_path": "assets/logo.png",
    "header_image_path": "assets/logo.png"
  },
  "colors": {
    "window_bg": "#ECE9D8",
    "panel_bg": "#FFFFFF",
    "text_primary": "#000000",
    "border_light": "#FFFFFF",
    "border_dark": "#7F7F7F",
    "accent": "#0A246A"
  },
  "metrics": {
    "window_width": 780,
    "window_height": 560,
    "sidebar_width": 164,
    "padding": 10,
    "button_height": 28
  },
  "typography": {
    "font_name": "Tahoma",
    "base_size": 14,
    "title_size": 18
  }
}
```

### Install Scope

```json
"install_scope": "ask"
```

Values:
- `user`
- `system`
- `ask`

### Step Types

Implemented step types:
- `welcome`
- `license`
- `scope`
- `directory`
- `options`
- `form`
- `ready`
- `install`
- `finish`

Step text fields:
- `description`: legacy shared description used by header and body when no overrides are set.
- `header_description`: optional override for the wizard header description.
- `body_description`: optional override for the description rendered inside the step widget.

You can hide one side explicitly by setting that override to an empty string.

### Validation Rules

Field-level validation:
- `required`
- `regex`
- `min_length`
- `max_length`
- validators:
  - `path_writable`
  - `dir_exists_or_create`

### Conditional Visibility

`show_if` expressions are evaluated with a restricted safe evaluator (no Python `eval`).

Available symbols:
- `answers`
- `selected_features`
- `scope` / `install_scope`

### `write_dotfile` (v2)

`write_dotfile` now uses an explicit file target path and supports append mode.

Supported keys:
- `target_path` (required): file path, supports `~` and environment variables.
- `append` (optional, default `false`): append rendered payload instead of overwrite.
- `content` (optional): string (templated) or structured JSON payload.

Examples:

```json
{
  "type": "write_dotfile",
  "target_path": "~/.example"
}
```

```json
{
  "type": "write_dotfile",
  "target_path": "~/.example",
  "append": true,
  "content": "installed={version} dir={install_dir}"
}
```

```json
{
  "type": "write_dotfile",
  "target_path": "~/.examplefolder/settings.ini",
  "content": {
    "product_id": "{product_id}",
    "scope": "{scope}"
  }
}
```

Notes:
- Parent directories are created automatically only when missing.
- Relative `target_path` values are resolved from the config directory (`source_root`).
- Legacy keys are no longer supported for this action:
  - `scope`
  - `user_base`
  - `system_base`
  - `file_name`

### Rollback Policy

Every action accepts optional:

```json
"rollback": "auto"
```

Values:
- `auto` (default): restore previous state where possible; remove created artifacts.
- `delete_only`: remove created artifacts only (no restore of overwritten originals).
- `none`: skip rollback for that action.

### `run_script` rollback/uninstall hooks

For `run_script`, `undo_path` is required unless `rollback` is explicitly `none`.
Optional `uninstall_path` can be used to run dedicated uninstall logic.

```json
{
  "type": "run_script",
  "path": "hooks/install_hook.py",
  "undo_path": "hooks/undo_hook.py",
  "uninstall_path": "hooks/uninstall_hook.py",
  "rollback": "auto"
}
```

### Uninstall block

```json
"uninstall": {
  "enabled": true,
  "modified_file_policy": "prompt",
  "unix": {
    "create_symlink": false,
    "user_link_path": "~/.local/bin/<product_id>-uninstall",
    "system_link_path": "/usr/local/bin/<product_id>-uninstall"
  }
}
```

`modified_file_policy`:
- `prompt` (interactive mode)
- `skip`
- `delete`

## Install Scope Paths and Permissions

### Windows
- User: `%LOCALAPPDATA%\<ProductName>`
- System: `%ProgramFiles%\<ProductName>`
- System installs require admin rights.

Optional UAC relaunch:

```json
"windows": { "allow_uac_elevation": true }
```

Windows uninstall registration (ARP) is written under HKCU/HKLM based on install scope using:
- `DisplayName`
- `Publisher`
- `DisplayVersion`
- `InstallLocation`
- `UninstallString`
- `QuietUninstallString`

### Linux
- User: `~/.local/share/<product_id>`
- System: `/opt/<product_id>`
- System installs require root.

Desktop entries:
- User: `~/.local/share/applications/<id>.desktop`
- System: `/usr/share/applications/<id>.desktop`

### macOS
- User: `~/Applications/<ProductName>.app`
- System: `/Applications/<ProductName>.app`
- System installs require admin/root.

Optional sudo relaunch:

```json
"unix": { "allow_sudo_relaunch": true }
```

## Extend the Framework

### Add a New Step Type

1. Add a new step widget in `installer_framework/ui/steps/` inheriting `StepWidget`.
2. Implement `apply_state`, `get_data`, `validate`, and optionally `on_show`.
3. Register in `installer_framework/ui/step_factory.py`.
4. Add new step type to schema enum in `installer_framework/config/schema.json`.

### Add a New Action Type

1. Add action class in `installer_framework/engine/actions/` inheriting `Action`.
2. Implement `execute(ctx, progress_callback, log_callback)`.
3. Register type mapping in `installer_framework/engine/runner.py`.
4. Add the type to schema enum in `installer_framework/config/schema.json`.

## Build Distributables

All scripts output to `dist/<platform>/`.

### Windows

```powershell
pwsh ./build/build_windows.ps1 -ConfigPath examples/sample_installer.json
```

Outputs:
- `dist/windows/tips-installer.exe`
- `dist/windows/tips-uninstaller.exe`

### Linux

```bash
./build/build_linux.sh
```

Output: `dist/linux/tips-installer/` (onefolder)

### macOS

```bash
./build/build_macos.sh examples/sample_installer.json
```

Output: `dist/macos/tips-installer.app`

## PyQt6 + PyInstaller Troubleshooting

- Ensure required Qt modules are explicitly included:
  - `--hidden-import PyQt6.QtCore`
  - `--hidden-import PyQt6.QtGui`
  - `--hidden-import PyQt6.QtWidgets`
  - `--hidden-import PyQt6.sip`
- If startup fails with Qt plugin errors, inspect packaged `platforms` plugin files.
- If assets are missing, verify `--add-data` paths for `examples` and `schema.json`.

## Rollback and Uninstall Usage

- Install journal: `install_dir/.tips/rollback_journal.json`
- Install manifest: `install_dir/.tips/manifest.json`

On install failure/cancel:
- completed actions are rolled back in reverse order
- rollback errors are reported separately from the original failure

### Windows uninstaller (GUI)

```powershell
tips-uninstaller --manifest "C:\\Path\\To\\Install\\.tips\\manifest.json"
```

Silent:

```powershell
tips-uninstaller --manifest "C:\\Path\\To\\Install\\.tips\\manifest.json" --silent
```

### Linux/macOS uninstaller (CLI)

Generated script (inside install dir):

```bash
python3 /path/to/install/.tips/uninstall.py
```

The generated Unix script is self-contained and does not require `installer_framework` to be installed on the target machine.

Silent + force modified deletion:

```bash
python3 /path/to/install/.tips/uninstall.py --silent --delete-modified
```

## Security Notes

- Condition evaluation uses safe parser, not Python `eval`.
- `run_script` exposes only restricted helper API (`copy`, `write_config`, `log`).
- Hook scripts execute with installer privileges; keep them trusted.
- No network downloads are performed by the framework.
