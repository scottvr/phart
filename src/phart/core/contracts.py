"""Core contracts for phased architecture refactors.

These interfaces are intentionally narrow so the CLI can orchestrate without
owning parsing/serialization internals.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import networkx as nx  # type: ignore

from phart.styles import LayoutOptions


@dataclass(frozen=True)
class OutputRenderConfig:
    """Settings required to render captured text into non-text output formats."""

    output_format: str
    svg_cell_size: int = 12
    svg_font_family: str = "monospace"
    svg_fg: str = "#111111"
    svg_bg: str = "#ffffff"


class GraphLoader(Protocol):
    """Contract for loading a graph from an input source."""

    def load(self, source: Path, *, options: LayoutOptions) -> nx.DiGraph: ...


class PythonEntryRunner(Protocol):
    """Contract for executing python entry sources and capturing rendered text."""

    def run(
        self,
        source: Path,
        *,
        function_name: str,
        module_argv: list[str],
        options: LayoutOptions,
    ) -> str: ...


class CapturedOutputFormatter(Protocol):
    """Contract for converting captured text into a selected output format."""

    def format(self, text: str, *, config: OutputRenderConfig) -> str: ...
