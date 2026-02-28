"""Dispatch output rendering from a prepared ASCIIRenderer instance."""

from __future__ import annotations

from phart.core.contracts import RendererOutputConfig
from phart.renderer import ASCIIRenderer


def render_renderer_output(
    renderer: ASCIIRenderer, *, config: RendererOutputConfig
) -> str:
    """Render output from ``renderer`` according to ``config.output_format``."""
    if config.output_format == "text":
        return renderer.render()
    if config.output_format == "ditaa":
        return renderer.render_ditaa(wrap_plantuml=False)
    if config.output_format == "ditaa-puml":
        return renderer.render_ditaa(wrap_plantuml=True)
    if config.output_format == "svg":
        return renderer.render_svg(
            cell_px=config.svg_cell_size,
            font_family=config.svg_font_family,
            text_mode=config.svg_text_mode,
            font_path=config.svg_font_path,
            fg_color=config.svg_fg,
            bg_color=config.svg_bg,
        )
    if config.output_format == "html":
        return renderer.render_html(
            fg_color=config.svg_fg,
            bg_color=config.svg_bg,
            font_family=config.svg_font_family,
        )
    if config.output_format == "latex-markdown":
        return renderer.render_latex_markdown(fg_color=config.svg_fg)

    raise ValueError(f"Unsupported output format '{config.output_format}'")
