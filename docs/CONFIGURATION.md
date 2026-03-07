# Configuring the framework

## JSON Config Model

Full schema is available at `installer_framework/config/schema.json`.

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
Typography font packaging:
- Build scripts auto-discover `theme.typography.fonts[*].font_ttf_path`.
- Relative TTF paths are resolved from the config directory and bundled into the app.
- Absolute TTF paths are bundled under `fonts/` in the package.
- Missing TTF paths produce warnings and are skipped (build continues).

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
    "fonts": [
      {
        "font_family": "SF Pro Text",
        "font_ttf_path": "assets/fonts/SF-Pro-Text-Regular.ttf"
      },
      {
        "font_family": "Segoe UI"
      }
    ],
    "default_preset": "default",
    "presets": {
      "default": {
        "title": [
          {"font_family": "SF Pro Text", "font_size": 18},
          {"font_family": "Segoe UI", "font_size": 18}
        ],
        "text": [
          {"font_family": "SF Pro Text", "font_size": 14},
          {"font_family": "Segoe UI", "font_size": 14}
        ]
      }
    }
  }
}
```

Typography notes:
- `theme.typography.fonts` is the global font catalog (family + optional TTF path).
- `theme.typography.presets` defines fallback stacks for `title` and `text` roles.
- `theme.typography.default_preset` is optional; if omitted, the first preset is used.
- Missing or unloadable TTF files are warned and skipped at runtime/build; fallback candidates continue.
- Legacy keys `font_name`, `base_size`, and `title_size` are no longer supported.

### Install Scope

```json
"install_scope": "ask"
```

Values:
- `user`
- `system`
- `ask`

### Step Types

Built-in step types:
- `welcome`
- `license`
- `scope`
- `directory`
- `options`
- `form`
- `ready`
- `install`
- `finish`

Additional custom step types can be provided by plugins.

Step text fields:
- `description`: legacy shared description used by header and body when no overrides are set.
- `header_description`: optional override for the wizard header description.
- `body_description`: optional override for the description rendered inside the step widget.
- `typography_preset`: optional preset key from `theme.typography.presets`; applies to step body and that step header.

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

### `copy_files`

`copy_files` now requires a manifest file and no longer accepts inline `items` or action-level `overwrite`.

Action format:

```json
{
  "type": "copy_files",
  "rollback": "auto",
  "manifest_file": "assets/copy_manifest.json",
  "preserve_permissions": true
}
```

Manifest file format:

```json
{
  "schema_version": 1,
  "files": [
    {
      "source": "assets/payload/README.txt",
      "target": "README.txt"
    },
    {
      "source": "assets/payload/README.txt",
      "target": "docs/README.txt",
      "overwrite": false
    }
  ]
}
```

Rules:
- `schema_version` must be `1`.
- `files` must be a non-empty array.
- each file entry requires:
  - `source` (file path)
  - `target` (install-relative target file path)
  - optional `overwrite` (default `true`)
- absolute targets are rejected.
- path traversal outside install directory (for example `../`) is rejected.
- sources are resolved from manifest-relative path first, then config directory, then bundled resources.

Migration note:
- removed keys for `copy_files`: `items`, `overwrite` (action-level)

Packaging note:
- the manifest file must be included in packaged assets. Example manifests under `examples/` are already included by the build scripts.

### Plugin System

Plugin discovery order:
1. `--plugins-dir` CLI option
2. `TIPS_PLUGINS_DIR` environment variable
3. repo-root `plugins/`
4. bundled `plugins/` (for packaged artifacts)

Each plugin lives in `<root>/<name>.tipsplugin/` and must contain:
- `metadata.json`
- `schema.json`
- `plugin.py`

`metadata.json` required keys:
- `type`: `action` or `step`
- `handle`
- `version`
- `min_framework_version`
- `max_framework_version`

`plugin.py` must expose `register()`:
- action plugin: `{\"action_class\": <Action subclass>}`
- step plugin: `{\"step_class\": <StepWidget subclass>}`

`schema.json` contract:
- `kind`: `action` or `step`
- `handle`: plugin handle
- `schema`: JSON schema fragment for that action/step object

Behavior:
- incompatible plugin versions are skipped with warnings
- duplicate handles fail fast
- missing required plugin files fail fast
- if config references an unknown/absent plugin handle, config load fails

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

Optional rights elevation relaunch:

```json
"macos": { "allow_rights_elevation": true }
```

Note: on macOS, `unix.allow_sudo_relaunch` is ignored.
