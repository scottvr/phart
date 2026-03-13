"""Output format renderers operating on ASCIIRenderer state."""

from __future__ import annotations

import math
from html import escape as html_escape
from typing import TYPE_CHECKING, List, Optional

from .ansi import ANSI_ESCAPE_RE, UNICODE_DITAA_MAP, ansi_to_hex

if TYPE_CHECKING:
    from phart.renderer import ASCIIRenderer

_TILDE_SPACE_RATIO = 32.0 / 15.0


def apply_padding_char(text: str, *, padding_char: str) -> str:
    """Replace ASCII spaces in rendered output with a configured padding glyph."""
    if padding_char == " ":
        return text
    return text.replace(" ", padding_char)


def normalized_canvas_rows(renderer: ASCIIRenderer) -> List[str]:
    width = max((len(row) for row in renderer.canvas), default=0)
    return ["".join(row).ljust(width) for row in renderer.canvas]


def render_ditaa(renderer: ASCIIRenderer, *, wrap_plantuml: bool = False) -> str:
    renderer._render_single_canvas()
    rows = normalized_canvas_rows(renderer)
    text = "\n".join(rows)
    text = ANSI_ESCAPE_RE.sub("", text)
    text = "".join(UNICODE_DITAA_MAP.get(ch, ch) for ch in text)
    lines = [line.rstrip() for line in text.splitlines()]
    while lines and lines[-1] == "":
        lines.pop()
    body = "\n".join(lines)
    if wrap_plantuml:
        return f"@startditaa\n{body}\n@endditaa\n"
    return body + ("\n" if body else "")


def render_svg(
    renderer: ASCIIRenderer,
    *,
    cell_px: int = 12,
    font_family: str = "monospace",
    text_mode: str = "text",
    font_path: Optional[str] = None,
    fg_color: str = "#111111",
    bg_color: str = "#ffffff",
) -> str:
    renderer._render_single_canvas()
    rows = normalized_canvas_rows(renderer)
    height = len(rows)
    width = max((len(row) for row in rows), default=0)
    svg_w = width * cell_px
    svg_h = height * cell_px
    text_x = cell_px / 2
    text_y0 = cell_px * 0.8

    lines: List[str] = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_w}" height="{svg_h}" '
        f'viewBox="0 0 {svg_w} {svg_h}">'
    )
    lines.append(
        f'  <rect x="0" y="0" width="{svg_w}" height="{svg_h}" fill="{html_escape(bg_color)}" />'
    )
    if text_mode == "text":
        lines.append(
            "  <g "
            f'font-family="{html_escape(font_family)}" '
            f'font-size="{cell_px}" fill="{html_escape(fg_color)}" '
            'text-anchor="middle" xml:space="preserve">'
        )
        for y, row in enumerate(rows):
            for x, ch in enumerate(row):
                if ch == " ":
                    continue
                cx = text_x + x * cell_px
                cy = text_y0 + y * cell_px
                fill = fg_color
                if y < len(renderer._color_canvas) and x < len(
                    renderer._color_canvas[y]
                ):
                    ansi = renderer._color_canvas[y][x]
                    parsed = ansi_to_hex(ansi) if ansi else None
                    if parsed:
                        fill = parsed
                lines.append(
                    f'    <text x="{cx:.2f}" y="{cy:.2f}" fill="{html_escape(fill)}">{html_escape(ch)}</text>'
                )
        lines.append("  </g>")
    elif text_mode == "path":
        renderer._append_svg_glyph_paths(
            lines=lines,
            rows=rows,
            cell_px=cell_px,
            font_family=font_family,
            font_path=font_path,
            fg_color=fg_color,
        )
    else:
        raise ValueError("text_mode must be one of: text, path")
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def render_html(
    renderer: ASCIIRenderer,
    *,
    fg_color: str = "#111111",
    bg_color: str = "#ffffff",
    font_family: str = "monospace",
) -> str:
    renderer._render_single_canvas()
    rows = normalized_canvas_rows(renderer)
    html_lines: List[str] = []
    html_lines.append("<!DOCTYPE html>")
    html_lines.append('<html><head><meta charset="utf-8"></head><body>')
    html_lines.append(
        "<pre style="
        f'"background:{html_escape(bg_color)};'
        f"color:{html_escape(fg_color)};"
        f"font-family:{html_escape(font_family)};"
        'line-height:1.1;">'
    )
    for y, row in enumerate(rows):
        current_color: Optional[str] = None
        for x, ch in enumerate(row):
            target_color = fg_color
            if y < len(renderer._color_canvas) and x < len(renderer._color_canvas[y]):
                ansi = renderer._color_canvas[y][x]
                parsed = ansi_to_hex(ansi) if ansi else None
                if parsed:
                    target_color = parsed
            if target_color != current_color:
                if current_color is not None:
                    html_lines.append("</span>")
                if target_color != fg_color:
                    html_lines.append(
                        f'<span style="color:{html_escape(target_color)}">'
                    )
                else:
                    html_lines.append("<span>")
                current_color = target_color
            html_lines.append(html_escape(ch))
        if current_color is not None:
            html_lines.append("</span>")
            current_color = None
        html_lines.append("\n")
    html_lines.append("</pre></body></html>\n")
    return "".join(html_lines)


def _latex_escape_text(text: str) -> str:
    escaped: List[str] = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == " ":
            j = i
            while j < len(text) and text[j] == " ":
                j += 1
            run_len = max(4, int(math.ceil((j - i) * _TILDE_SPACE_RATIO)))
            escaped.append("~" * run_len)
            i = j
            continue

        if ch == "\\":
            escaped.append(r"\textbackslash{}")
        elif ch == "_":
            # GitHub markdown+math parsing is brittle around underscores.
            # Prefer visual fidelity over strict literal preservation.
            escaped.append("-")
        elif ch == "#":
            # Avoid parser errors seen in GFM math around '#'.
            escaped.append("-")
        elif ch in {"{", "}", "$", "#", "%", "&"}:
            escaped.append(f"\\{ch}")
        elif ch == "^":
            escaped.append(r"\^{}")
        else:
            escaped.append(ch)
        i += 1

    encoded = "".join(escaped)
    if encoded.startswith("~"):
        encoded = "." + encoded
    if encoded.endswith("~"):
        encoded += "."
    return encoded


def render_as_mmd(
    renderer: ASCIIRenderer,
    *,
    type: str = "flowchart",
    direction: str = "TD",
) -> str:
    renderer._render_single_canvas()
    type = "flowchart"
    direction = "TD"
    return "\n".join([type, direction])


def render_latex_markdown(
    renderer: ASCIIRenderer,
    *,
    fg_color: str = "#111111",
) -> str:
    renderer._render_single_canvas()
    rows = normalized_canvas_rows(renderer)
    latex_lines: List[str] = []
    for y, row in enumerate(rows):
        row_colors = (
            renderer._color_canvas[y]
            if y < len(renderer._color_canvas)
            else [None] * len(row)
        )

        segments: List[str] = []
        current_color: Optional[str] = None
        current_text: List[str] = []
        for ch, ansi in zip(row, row_colors, strict=True):
            target_color = fg_color
            parsed = ansi_to_hex(ansi) if ansi else None
            if parsed:
                target_color = parsed

            if target_color != current_color:
                if current_text:
                    escaped = _latex_escape_text("".join(current_text))
                    segments.append(
                        r"\mathtt{\textbf{\textcolor{"
                        f"{current_color}"
                        r"}{"
                        f"{escaped}"
                        r"}}}"
                    )
                    current_text = []
                current_color = target_color
            current_text.append(ch)

        if current_text and current_color is not None:
            escaped = _latex_escape_text("".join(current_text))
            segments.append(
                r"\mathtt{\textbf{\textcolor{"
                f"{current_color}"
                r"}{"
                f"{escaped}"
                r"}}}"
            )

        latex_lines.append("${" + "".join(segments) + "}$")
        # Blank lines are required; otherwise GFM can merge adjacent math lines.
    return "\n\n".join(latex_lines) + ("\n" if latex_lines else "")
