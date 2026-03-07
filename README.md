# TIPS Framework

TIPS = **TIPS Instructable Python Setup**.

This project provides a JSON-driven, **PyQt6**-based installer framework for Windows, Linux, and macOS. It supports classic and modern installer wizard UI themes, validation, install scope (`user`/`system`/`ask`), background action execution with progress/logging, and upgrade detection.

## Features

- Installer shell UI themes:
  - `classic` or `modern` layout
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
- External plugin extensions:
  - plugin root discovery (`--plugins-dir`, `TIPS_PLUGINS_DIR`, repo-root `plugins/`, bundled `plugins/`)
  - custom step/action handlers from `*.tipsplugin`
  - plugin schema fragments merged into runtime config validation
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
    plugins/
      models.py
      discovery.py
      registry.py
      schema_compose.py
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
../plugins/
  <name>.tipsplugin/
    metadata.json
    schema.json
    plugin.py
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

Optional plugin root override:

```bash
python -m installer_framework.main --config examples/sample_installer.json --plugins-dir /absolute/path/to/plugins
```

Resume state file: temp path `tips_installer_resume.json`.

## Running Tests

Install dev dependencies in the installer virtualenv:

```bash
cd installer_framework
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .[dev]
```

Run the full suite from repo root:

```bash
cd /Users/thomasbruninx/Projecten/tips
./installer_framework/.venv/bin/python -m pytest tests -q
```

Run with coverage:

```bash
./installer_framework/.venv/bin/python -m pytest tests --cov=installer_framework/installer_framework --cov-report=term-missing
```

## Configuration an installer

Check the [docs/CONFIGURATION.md](docs/CONFIGURATION.md) documentation file for more information.

## Building an installer

Check the [docs/BUILDING.md](docs/BUILDING.md) documentation file for more information.

## Extending the framework

Check the [docs/EXTENDING.md](docs/EXTENDING.md) documentation file for more information.

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

The Windows uninstaller executable is installed into the application install directory for ARP integration and discoverability. When launched, it transparently copies itself to a temporary directory, relaunches from there, removes the installed `tips-uninstaller.exe`, and then schedules deletion of the temp copy after exit. This is required because a running Windows executable cannot delete itself in place.

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
