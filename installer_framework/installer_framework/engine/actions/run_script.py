"""run_script action with constrained execution context."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Callable

from installer_framework.engine.action_base import Action
from installer_framework.engine.context import InstallerContext
from installer_framework.util.fs import ensure_dir


class RunScriptAction(Action):
    def __init__(self, params: dict[str, Any]) -> None:
        self.params = params

    def _resolve_script(self, ctx: InstallerContext, value: str) -> Path:
        path = Path(value)
        if path.is_absolute():
            return path
        return (ctx.config.source_root / value).resolve()

    def execute(self, ctx: InstallerContext, progress, log) -> dict:
        script_path = self._resolve_script(ctx, self.params["path"])
        if not script_path.exists():
            raise FileNotFoundError(f"Script hook not found: {script_path}")

        install_dir = Path(ctx.state.install_dir)

        def helper_copy(src: str, dest: str) -> str:
            src_path = Path(src)
            if not src_path.is_absolute():
                src_path = (ctx.config.source_root / src).resolve()
            dst_path = install_dir / dest
            ensure_dir(dst_path.parent)
            if src_path.is_dir():
                shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
            else:
                shutil.copy2(src_path, dst_path)
            return str(dst_path)

        def helper_write_config(name: str, payload: dict[str, Any]) -> str:
            target = install_dir / name
            ensure_dir(target.parent)
            target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            return str(target)

        allowed_builtins = {
            "len": len,
            "range": range,
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "dict": dict,
            "list": list,
            "set": set,
            "min": min,
            "max": max,
            "sum": sum,
            "print": lambda *args, **kwargs: log(" ".join(str(x) for x in args)),
        }

        api: dict[str, Callable[..., Any]] = {
            "copy": helper_copy,
            "write_config": helper_write_config,
            "log": log,
        }

        ctx_data = {
            "answers": ctx.state.answers,
            "selected_features": ctx.state.selected_features,
            "install_scope": ctx.state.install_scope,
            "install_dir": ctx.state.install_dir,
            "version": ctx.config.branding.version,
        }

        code = script_path.read_text(encoding="utf-8")
        globals_dict = {
            "__builtins__": allowed_builtins,
            "api": api,
            "ctx": ctx_data,
        }
        locals_dict: dict[str, Any] = {}

        exec(compile(code, str(script_path), "exec"), globals_dict, locals_dict)

        progress(100, f"Script executed: {script_path.name}")
        log(f"Hook script executed: {script_path}")
        return {"action": "run_script", "path": str(script_path)}
