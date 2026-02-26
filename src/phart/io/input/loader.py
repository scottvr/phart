"""Input loader adapters for non-Python file sources."""

from __future__ import annotations

from pathlib import Path

from phart.renderer import ASCIIRenderer
from phart.styles import LayoutOptions


def load_renderer_from_file(
    input_path: Path, *, options: LayoutOptions
) -> ASCIIRenderer:
    """Load and parse a source file into an ``ASCIIRenderer`` instance.

    Supports PlantUML subset, GraphML files, and DOT content.
    Raises ``ValueError`` with a stable message if parsing fails.
    """
    content = input_path.read_text(encoding="utf-8")

    try:
        suffix = input_path.suffix.lower()
        if suffix in {".puml", ".plantuml", ".uml"}:
            return ASCIIRenderer.from_plantuml(content, options=options)
        if content.strip().startswith("<?xml") or content.strip().startswith(
            "<graphml"
        ):
            return ASCIIRenderer.from_graphml(str(input_path), options=options)
        return ASCIIRenderer.from_dot(content, options=options)
    except Exception as parse_error:
        raise ValueError(
            f"Could not parse file as PlantUML, GraphML, or DOT format: {parse_error}"
        ) from parse_error
