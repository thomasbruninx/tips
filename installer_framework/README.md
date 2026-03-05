# TIPS Installer Framework

TIPS = **TIPS Instructable Python Setup**.

This project provides a JSON-driven, Kivy-based installer framework that runs on Windows, Linux, and macOS. It supports wizard steps, validation, install scope (`user`/`system`/`ask`), action execution with progress/logging, and upgrade detection.

## Features

- Kivy wizard container with:
  - classic InstallShield-style shell (left artwork pane + right content)
  - step header strip (title + description + optional header image)
  - dynamic content area (step widgets)
  - navigation bar (`< Back` / `Next >` / `Install` / `Finish` / `Cancel`)
- JSON-defined installer flow:
  - step order
  - optional conditions (`show_if`)
  - field definitions and validations
  - install actions
- Classic theme system:
  - optional JSON `theme` block
  - default theme when `theme` is omitted
  - classic layout is always used
- Install scopes:
  - `user`
  - `system`
  - `ask` (wizard scope step)
- Threaded install execution:
  - actions run on a background thread
  - UI updated via Kivy `Clock`
- Action engine with built-in action types:
  - `copy_files`
  - `write_registry` / `read_registry` (Windows)
  - `write_dotfile`
  - `create_shortcut` (Windows)
  - `create_desktop_entry` (Linux)
  - `show_message`
  - `run_script` (restricted context)
- Upgrade detection:
  - Windows registry for HKCU/HKLM
  - Unix metadata file under user/system config paths
- PyInstaller-friendly resource loading and build scripts.

## Repository Layout

```text
installer_framework/
  pyproject.toml
  README.md
  LICENSE
  installer_framework/
    __init__.py
    main.py
    app/
      kivy_app.py
      resources.py
      paths.py
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
        feature_list.py
        validated_text_input.py
        log_pane.py
        dialogs.py
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
      logging.py
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

1. Create an environment and install dependencies.

```bash
cd installer_framework
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .[dev]
```

2. Run the sample installer.

```bash
python -m installer_framework.main --config examples/sample_installer.json
```

3. Resume support (optional):

```bash
python -m installer_framework.main --config examples/sample_installer.json --resume
```

Resume state is saved to a temp file (`tips_installer_resume.json`).

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

### Theme (Classic)

`theme` is optional. If omitted, classic defaults are applied automatically.

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

Supported values:
- `user`: per-user install only.
- `system`: system-wide install only.
- `ask`: show scope step to let the user choose.

### Steps

Each step:

```json
{
  "id": "credentials",
  "type": "form",
  "title": "Account Setup",
  "description": "Provide account details.",
  "show_if": "answers.install_channel == 'beta'",
  "fields": [
    {
      "id": "username",
      "type": "text",
      "label": "Username",
      "required": true,
      "regex": "^[a-zA-Z0-9_.-]{3,20}$",
      "min_length": 3,
      "max_length": 20
    }
  ]
}
```

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

### Field Validation Rules

Supported validation keys:
- `required`
- `regex`
- `min_length`
- `max_length`
- `validators`:
  - `path_writable`
  - `dir_exists_or_create`

### Conditions (`show_if`)

Condition expressions are evaluated by a safe AST evaluator (`util/safe_eval.py`) with no Python `eval`.

Supported context:
- `answers`
- `selected_features`
- `scope` / `install_scope`

Supported operators:
- boolean: `and`, `or`, `not`
- comparisons: `==`, `!=`, `<`, `<=`, `>`, `>=`, `in`, `not in`

### Actions

Actions run in order after `Install`.

Example:

```json
"actions": [
  {"type": "copy_files", "items": [{"from": "assets/payload", "to": "."}]},
  {"type": "write_dotfile", "file_name": "install-info.json"},
  {"type": "show_message", "level": "info", "title": "Done", "message": "Installed to {install_dir}"}
]
```

## Install Scope Paths and Privileges

### Windows

- User scope default: `%LOCALAPPDATA%\<ProductName>`
- System scope default: `%ProgramFiles%\<ProductName>`
- System scope requires admin rights.

Behavior:
- If system scope is selected and the process is not elevated, the wizard shows a clear error.
- Optional relaunch can be enabled:

```json
"windows": { "allow_uac_elevation": true }
```

### Linux

- User scope default: `~/.local/share/<product_id>`
- System scope default: `/opt/<product_id>`
- System scope requires root.

Desktop entries:
- User: `~/.local/share/applications/<id>.desktop`
- System: `/usr/share/applications/<id>.desktop`

### macOS

- User scope default: `~/Applications/<ProductName>.app`
- System scope default: `/Applications/<ProductName>.app`
- System scope requires admin/root.

Optional relaunch for Unix-like systems:

```json
"unix": { "allow_sudo_relaunch": true }
```

## Upgrade Detection

Implemented in `engine/upgrade.py`.

- Windows: looks for install metadata under registry key:
  - `HKCU\Software\<Publisher>\<product_id>` (user scope)
  - `HKLM\Software\<Publisher>\<product_id>` (system scope)
- Linux/macOS: checks install metadata file in user/system config location.
- Semantic version compare is implemented in `engine/versioning.py`.

Detected upgrades are injected into runtime state and surfaced on the welcome screen.

## Add a New Step Type

1. Create a step widget class under `installer_framework/ui/steps/` inheriting `StepWidget`.
2. Implement:
   - `apply_state()`
   - `get_data()`
   - `validate()`
   - optional `on_show()`
3. Register it in `ui/step_factory.py`.
4. Add the new type to `config/schema.json` (`steps[].type` enum).

## Add a New Action Type

1. Create an action class under `installer_framework/engine/actions/` inheriting `Action`.
2. Implement `execute(ctx, progress_callback, log_callback)`.
3. Register in `engine/runner.py` mapping.
4. Add type to `config/schema.json` (`actions[].type` enum).

## Build Distributables

Scripts are under `build/` and output to `dist/<platform>/`.

### Windows

```powershell
pwsh ./build/build_windows.ps1
```

Output:
- `dist/windows/tips-installer.exe`

### Linux

```bash
./build/build_linux.sh
```

Output:
- `dist/linux/tips-installer/` (onefolder)

Notes:
- Linux script intentionally uses **onefolder** for better Kivy stability.

### macOS

```bash
./build/build_macos.sh
```

Output:
- `dist/macos/tips-installer.app`

## Kivy + PyInstaller Troubleshooting

- If Kivy modules are missing at runtime, ensure:
  - `--collect-all kivy`
  - `--collect-submodules plyer`
- If assets are missing:
  - verify `--add-data` entries include `examples` and schema file.
- If icon/branding doesn’t load:
  - use existing file paths relative to config file location.
- If OpenGL/window startup fails on Linux:
  - prefer onefolder build and run from a desktop session with proper GL drivers.

## Security and Safety Notes

- Condition logic does **not** use Python `eval`.
- `run_script` uses a restricted helper API:
  - `api.copy`
  - `api.write_config`
  - `api.log`
- Hook scripts still run with installer privileges; keep scripts trusted and minimal.
- The framework does not download content from the network.

## Example Installer Flow

`examples/sample_installer.json` demonstrates:

- welcome page
- license page
- scope selection (`ask`)
- install directory selection
- feature multiselect
- custom form (`username` + `password`)
- ready summary
- install progress + logs
- finish page

Install actions in the sample:
- copy bundled payload
- create shortcut/desktop entry where applicable
- write install metadata for upgrade detection
- show completion message
