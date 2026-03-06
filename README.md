# TIPS Framework

TIPS = **TIPS Instructable Python Setup**.

This project provides a JSON-driven, **PyQt6**-based installer framework for Windows, Linux, and macOS. It supports a classic installer wizard UI, validation, install scope (`user`/`system`/`ask`), background action execution with progress/logging, and upgrade detection.

## Features

- Classic installer shell UI (InstallShield-like):
  - left branding/sidebar panel
  - step header area
  - content area for step widgets
  - navigation bar (`< Back`, `Next >`, `Install`, `Finish`, `Cancel`)
- JSON-defined installer flow:
  - step order
  - optional conditions (`show_if`)
  - field definitions and validations
  - install actions
- Theme block (`theme.style = "classic"`) with colors, metrics, typography, and artwork paths
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
    app/
      qt_app.py
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
      widgets/
        classic.py
        dialogs.py
        validated_text_input.py
        feature_list.py
        log_pane.py
    engine/
      context.py
      runner.py
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

`theme` is optional; defaults are applied if omitted.

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

## Install Scope Paths and Permissions

### Windows
- User: `%LOCALAPPDATA%\<ProductName>`
- System: `%ProgramFiles%\<ProductName>`
- System installs require admin rights.

Optional UAC relaunch:

```json
"windows": { "allow_uac_elevation": true }
```

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

Output: `dist/windows/tips-installer.exe`

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

## Security Notes

- Condition evaluation uses safe parser, not Python `eval`.
- `run_script` exposes only restricted helper API (`copy`, `write_config`, `log`).
- Hook scripts execute with installer privileges; keep them trusted.
- No network downloads are performed by the framework.
