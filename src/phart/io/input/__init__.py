"""Input format and source runners."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from phart.renderer import ASCIIRenderer
    from phart.styles import LayoutOptions


def load_renderer_from_file(
    input_path: Path, *, options: LayoutOptions
) -> ASCIIRenderer:
    # Lazy import to keep package import stable while avoiding cycles with renderer.
    from .loader import load_renderer_from_file as _impl

    return _impl(input_path, options=options)


def run_python_source(
    source: Path,
    *,
    function_name: str,
    module_argv: list[str],
    options: LayoutOptions,
) -> str:
    # Lazy import to keep package import stable while avoiding cycles with renderer.
    from .python_runner import run_python_source as _impl

    return _impl(
        source,
        function_name=function_name,
        module_argv=module_argv,
        options=options,
    )


__all__ = ["load_renderer_from_file", "run_python_source"]
