"""Utilities for converting captured renderer text to alternate output formats."""

from __future__ import annotations

import re
from html import escape as html_escape
from typing import Optional

from phart.core.contracts import OutputRenderConfig
from phart.rendering.ansi import ANSI_ESCAPE_RE, UNICODE_DITAA_MAP, ansi_to_hex

_ANSI_TOKEN_RE = re.compile(r"\x1b\[[0-9;]*m|.", re.DOTALL)


def _rows_and_colors_from_ansi_text(
    text: str,
) -> tuple[list[str], list[list[Optional[str]]]]:
    rows: list[list[str]] = []
    color_rows: list[list[Optional[str]]] = []
    for line in text.splitlines():
        row_chars: list[str] = []
        row_colors: list[Optional[str]] = []
        active_ansi: Optional[str] = None
        for token in _ANSI_TOKEN_RE.findall(line):
            if token.startswith("\x1b["):
                active_ansi = None if token == "\x1b[0m" else token
                continue
            row_chars.append(token)
            row_colors.append(active_ansi)
        rows.append(row_chars)
        color_rows.append(row_colors)

    width = max((len(r) for r in rows), default=0)
    normalized_rows = ["".join(r).ljust(width) for r in rows]
    normalized_colors: list[list[Optional[str]]] = []
    for color_row in color_rows:
        normalized_colors.append(color_row + [None] * (width - len(color_row)))
    return normalized_rows, normalized_colors


def _render_ditaa(raw_text: str, *, wrap_plantuml: bool) -> str:
    text = ANSI_ESCAPE_RE.sub("", raw_text)
    text = "".join(UNICODE_DITAA_MAP.get(ch, ch) for ch in text)
    lines = [line.rstrip() for line in text.splitlines()]
    while lines and lines[-1] == "":
        lines.pop()
    body = "\n".join(lines)
    if wrap_plantuml:
        return f"@startditaa\n{body}\n@endditaa\n"
    return body + ("\n" if body else "")


def _render_svg(
    rows: list[str],
    color_canvas: list[list[Optional[str]]],
    *,
    config: OutputRenderConfig,
) -> str:
    height = len(rows)
    width = max((len(row) for row in rows), default=0)
    cell_px = config.svg_cell_size
    svg_w = width * cell_px
    svg_h = height * cell_px
    text_x = cell_px / 2
    text_y0 = cell_px * 0.8

    lines: list[str] = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_w}" height="{svg_h}" '
        f'viewBox="0 0 {svg_w} {svg_h}">'
    )
    lines.append(
        f'  <rect x="0" y="0" width="{svg_w}" height="{svg_h}" fill="{html_escape(config.svg_bg)}" />'
    )
    lines.append(
        "  <g "
        f'font-family="{html_escape(config.svg_font_family)}" '
        f'font-size="{cell_px}" fill="{html_escape(config.svg_fg)}" '
        'text-anchor="middle" xml:space="preserve">'
    )
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == " ":
                continue
            cx = text_x + x * cell_px
            cy = text_y0 + y * cell_px
            fill = config.svg_fg
            if y < len(color_canvas) and x < len(color_canvas[y]):
                ansi = color_canvas[y][x]
                parsed = ansi_to_hex(ansi) if ansi else None
                if parsed:
                    fill = parsed
            lines.append(
                f'    <text x="{cx:.2f}" y="{cy:.2f}" fill="{html_escape(fill)}">{html_escape(ch)}</text>'
            )
    lines.append("  </g>")
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def _render_html(
    rows: list[str],
    color_canvas: list[list[Optional[str]]],
    *,
    config: OutputRenderConfig,
) -> str:
    html_lines: list[str] = []
    html_lines.append("<!DOCTYPE html>")
    html_lines.append('<html><head><meta charset="utf-8"></head><body>')
    html_lines.append(
        "<pre style="
        f'"background:{html_escape(config.svg_bg)};'
        f"color:{html_escape(config.svg_fg)};"
        f"font-family:{html_escape(config.svg_font_family)};"
        'line-height:1.1;">'
    )
    for y, row in enumerate(rows):
        current_color: Optional[str] = None
        for x, ch in enumerate(row):
            target_color = config.svg_fg
            if y < len(color_canvas) and x < len(color_canvas[y]):
                ansi = color_canvas[y][x]
                parsed = ansi_to_hex(ansi) if ansi else None
                if parsed:
                    target_color = parsed
            if target_color != current_color:
                if current_color is not None:
                    html_lines.append("</span>")
                if target_color != config.svg_fg:
                    html_lines.append(
                        f'<span style="color:{html_escape(target_color)}">'
                    )
                else:
                    html_lines.append("<span>")
                current_color = target_color
            html_lines.append(html_escape(ch))
        if current_color is not None:
            html_lines.append("</span>")
        html_lines.append("\n")
    html_lines.append("</pre></body></html>\n")
    return "".join(html_lines)


def render_captured_text(raw_text: str, *, config: OutputRenderConfig) -> str:
    """Convert captured text output into the selected output format."""
    if config.output_format == "text":
        return raw_text
    if config.output_format == "ditaa":
        return _render_ditaa(raw_text, wrap_plantuml=False)
    if config.output_format == "ditaa-puml":
        return _render_ditaa(raw_text, wrap_plantuml=True)

    rows, color_canvas = _rows_and_colors_from_ansi_text(raw_text)
    if config.output_format == "svg":
        return _render_svg(rows, color_canvas, config=config)
    if config.output_format == "html":
        return _render_html(rows, color_canvas, config=config)

    raise ValueError(f"Unsupported output format '{config.output_format}'")
