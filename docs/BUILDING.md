
# Building Distributables
All scripts output to `dist/<platform>/`.
All build scripts require an explicit JSON config path and fail fast when the path is missing, does not exist, or contains invalid JSON.
The provided build config is bundled as the packaged app's default runtime config (for launches without CLI args).

## Windows

```powershell
pwsh ./build/build_windows.ps1 -ConfigPath examples/sample_installer.json
```

Outputs:
- `dist/windows/tips-installer.exe`
- `dist/windows/tips-uninstaller.exe`

If repo-root `plugins/` exists, compatible plugins are analyzed during build and bundled into the artifact.

## Linux

```bash
./build/build_linux.sh examples/sample_installer.json
```

Output: `dist/linux/tips-installer/` (onefolder)

If repo-root `plugins/` exists, compatible plugins are analyzed during build and bundled into the artifact.

## macOS

```bash
./build/build_macos.sh examples/sample_installer.json
```

Output: `dist/macos/tips-installer.app`

If repo-root `plugins/` exists, compatible plugins are analyzed during build and bundled into the artifact.
