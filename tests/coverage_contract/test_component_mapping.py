from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "installer_framework" / "installer_framework"
TEST_ROOT = REPO_ROOT / "tests"

EXCEPTIONS: set[str] = set()

MODULE_TO_TESTS: dict[str, list[str]] = {
    "app/paths.py": ["tests/app/test_paths.py"],
    "app/qt_app.py": ["tests/app/test_qt_app.py"],
    "app/qt_uninstaller_app.py": ["tests/app/test_qt_uninstaller_app.py"],
    "app/resources.py": ["tests/app/test_resources.py"],
    "config/conditions.py": ["tests/config/test_conditions.py"],
    "config/loader.py": ["tests/config/test_loader.py"],
    "config/models.py": ["tests/config/test_models.py"],
    "config/validation.py": ["tests/config/test_validation.py"],
    "engine/action_base.py": ["tests/engine/test_runner.py"],
    "engine/context.py": ["tests/engine/test_context.py"],
    "engine/manifest.py": ["tests/engine/test_manifest.py"],
    "engine/rollback.py": ["tests/engine/test_rollback.py"],
    "engine/runner.py": ["tests/engine/test_runner.py"],
    "engine/uninstall_runner.py": ["tests/engine/test_uninstall_runner.py"],
    "engine/upgrade.py": ["tests/engine/test_upgrade.py"],
    "engine/versioning.py": ["tests/engine/test_versioning.py"],
    "engine/actions/copy_files.py": ["tests/engine/actions/test_copy_files.py"],
    "engine/actions/desktop_entry_linux.py": ["tests/engine/actions/test_desktop_entry_linux.py"],
    "engine/actions/dotfile.py": ["tests/engine/actions/test_dotfile.py"],
    "engine/actions/registry.py": ["tests/engine/actions/test_registry.py"],
    "engine/actions/run_script.py": ["tests/engine/actions/test_run_script.py"],
    "engine/actions/shortcut_windows.py": ["tests/engine/actions/test_shortcut_windows.py"],
    "engine/actions/show_message.py": ["tests/engine/actions/test_show_message.py"],
    "main.py": ["tests/app/test_main.py"],
    "plugins/discovery.py": ["tests/plugins/test_discovery.py"],
    "plugins/models.py": ["tests/plugins/test_registry.py"],
    "plugins/registry.py": ["tests/plugins/test_registry.py"],
    "plugins/schema_compose.py": ["tests/plugins/test_schema_compose.py"],
    "ui/step_base.py": ["tests/ui/test_step_base.py"],
    "ui/step_factory.py": ["tests/ui/test_step_factory.py"],
    "ui/theme.py": ["tests/ui/test_theme_runtime.py"],
    "ui/uninstall_wizard.py": ["tests/ui/test_uninstall_wizard.py"],
    "ui/wizard.py": ["tests/ui/test_wizard.py"],
    "ui/steps/directory.py": ["tests/ui/steps/test_directory_step.py"],
    "ui/steps/finish.py": ["tests/ui/steps/test_finish_step.py"],
    "ui/steps/form.py": ["tests/ui/steps/test_form_step.py"],
    "ui/steps/install.py": ["tests/ui/steps/test_install_step.py"],
    "ui/steps/license.py": ["tests/ui/steps/test_license_step.py"],
    "ui/steps/options.py": ["tests/ui/steps/test_options_step.py"],
    "ui/steps/ready.py": ["tests/ui/steps/test_ready_step.py"],
    "ui/steps/scope.py": ["tests/ui/steps/test_scope_step.py"],
    "ui/steps/welcome.py": ["tests/ui/steps/test_welcome_step.py"],
    "ui/widgets/classic_theme.py": ["tests/ui/widgets/test_classic_theme.py"],
    "ui/widgets/dialogs.py": ["tests/ui/widgets/test_dialogs.py"],
    "ui/widgets/feature_list.py": ["tests/ui/widgets/test_feature_list.py"],
    "ui/widgets/log_pane.py": ["tests/ui/widgets/test_log_pane.py"],
    "ui/widgets/modern_theme.py": ["tests/ui/widgets/test_modern_theme.py"],
    "ui/widgets/theme.py": ["tests/ui/widgets/test_theme_factory.py"],
    "ui/widgets/validated_text_input.py": ["tests/ui/widgets/test_validated_text_input.py"],
    "uninstall_cli.py": ["tests/app/test_uninstall_cli.py"],
    "uninstaller_main.py": ["tests/app/test_uninstaller_main.py"],
    "util/fs.py": ["tests/util/test_fs.py"],
    "util/logging.py": ["tests/util/test_logging.py"],
    "util/platform.py": ["tests/util/test_platform.py"],
    "util/privileges.py": ["tests/util/test_privileges.py"],
    "util/safe_eval.py": ["tests/util/test_safe_eval.py"],
}


def test_every_production_module_is_mapped_to_tests():
    modules = sorted(
        str(path.relative_to(SRC_ROOT)).replace("\\", "/")
        for path in SRC_ROOT.rglob("*.py")
        if path.name != "__init__.py"
    )

    missing = [module for module in modules if module not in MODULE_TO_TESTS and module not in EXCEPTIONS]
    assert not missing, f"Unmapped production modules: {missing}"


def test_mapping_points_to_existing_test_files():
    broken: list[tuple[str, str]] = []
    for module, tests in MODULE_TO_TESTS.items():
        module_path = SRC_ROOT / module
        if not module_path.exists():
            broken.append((module, "<module missing>"))
            continue
        for test_file in tests:
            path = REPO_ROOT / test_file
            if not path.exists():
                broken.append((module, test_file))
    assert not broken, f"Broken component mapping entries: {broken}"
