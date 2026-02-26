"""Python source execution helpers for CLI input mode."""

from __future__ import annotations

import ast
import importlib.util
import io
import sys
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any

from phart.renderer import ASCIIRenderer
from phart.styles import LayoutOptions


def _load_python_module(file_path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("dynamic_module", file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load {file_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules["dynamic_module"] = module
    spec.loader.exec_module(module)
    return module


def _run_python_as_main(file_path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("__main__", file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load {file_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules["__main__"] = module
    spec.loader.exec_module(module)
    return module


def _module_defines_function(file_path: Path, function_name: str) -> bool:
    source = file_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(file_path))
    return any(
        isinstance(node, ast.FunctionDef) and node.name == function_name
        for node in tree.body
    )


def run_python_source(
    source: Path,
    *,
    function_name: str,
    module_argv: list[str],
    options: LayoutOptions,
) -> str:
    """Execute a Python source entrypoint and capture rendered stdout text."""
    old_argv = sys.argv
    old_default_options = ASCIIRenderer.default_options
    sys.argv = [str(source)] + module_argv

    try:
        ASCIIRenderer.default_options = options
        capture = io.StringIO()
        with redirect_stdout(capture):
            if function_name != "main":
                module = _load_python_module(source)
                try:
                    func = getattr(module, function_name)
                except AttributeError as exc:
                    raise ValueError(
                        f"Function '{function_name}' not found in {source}"
                    ) from exc
                func()
            elif _module_defines_function(source, "main"):
                module = _load_python_module(source)
                module.main()
            else:
                _run_python_as_main(source)
        return capture.getvalue()
    finally:
        sys.argv = old_argv
        ASCIIRenderer.default_options = old_default_options
