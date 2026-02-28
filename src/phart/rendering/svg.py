"""ASCIIRenderer helper for svg-related functiosn."""

from __future__ import annotations

import os
from html import escape as html_escape
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, cast

if TYPE_CHECKING:
    from phart.renderer import ASCIIRenderer


def append_svg_glyph_paths(
    renderer: ASCIIRenderer,
    *,
    lines: List[str],
    rows: List[str],
    cell_px: int,
    font_family: str,
    font_path: Optional[str],
    fg_color: str,
) -> None:
    try:
        from fontTools.pens.boundsPen import BoundsPen  # type: ignore
        from fontTools.pens.svgPathPen import SVGPathPen  # type: ignore
        from fontTools.ttLib import TTFont  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "SVG path glyph mode requires fonttools. Install it and retry."
        ) from exc

    resolved_font = renderer._resolve_svg_font_path(
        font_family=font_family,
        font_path=font_path,
    )
    font = TTFont(resolved_font)
    glyph_set = font.getGlyphSet()
    cmap = font.getBestCmap() or {}
    units_per_em = max(1, int(font["head"].unitsPerEm))
    scale = float(cell_px) / float(units_per_em)
    glyph_cache: Dict[str, Optional[Tuple[str, Tuple[float, float, float, float]]]] = {}

    try:
        lines.append(
            "  <g "
            f'fill="{html_escape(fg_color)}" '
            f'data-svg-font-path="{html_escape(resolved_font)}" '
            'xml:space="preserve">'
        )
        for y, row in enumerate(rows):
            for x, ch in enumerate(row):
                if ch == " ":
                    continue

                cache_item = glyph_cache.get(ch)
                if ch not in glyph_cache:
                    cache_item = renderer._glyph_outline_for_char(
                        ch=ch,
                        cmap=cmap,
                        glyph_set=glyph_set,
                        svg_path_pen_cls=SVGPathPen,
                        bounds_pen_cls=BoundsPen,
                    )
                    glyph_cache[ch] = cache_item
                if cache_item is None:
                    continue

                path_data, bounds = cache_item
                x_min, y_min, x_max, y_max = bounds
                glyph_w_px = (x_max - x_min) * scale
                glyph_h_px = (y_max - y_min) * scale
                tx = (x * cell_px) + ((cell_px - glyph_w_px) / 2.0) - (x_min * scale)
                ty = (y * cell_px) + ((cell_px - glyph_h_px) / 2.0) + (y_max * scale)

                fill = fg_color
                if y < len(renderer._color_canvas) and x < len(
                    renderer._color_canvas[y]
                ):
                    ansi = renderer._color_canvas[y][x]
                    parsed = renderer._ansi_to_hex(ansi) if ansi else None
                    if parsed:
                        fill = parsed

                lines.append(
                    f'    <path d="{html_escape(path_data)}" fill="{html_escape(fill)}" '
                    f'transform="translate({tx:.2f} {ty:.2f}) scale({scale:.6f} {-scale:.6f})" />'
                )
        lines.append("  </g>")
    finally:
        font.close()


def resolve_svg_font_path(*, font_family: str, font_path: Optional[str]) -> str:
    if font_path:
        if os.path.isfile(font_path):
            return os.path.abspath(font_path)
        raise ValueError(f"--svg-font-path not found: {font_path}")
    try:
        from matplotlib import font_manager  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "SVG path glyph mode needs either --svg-font-path or matplotlib for font lookup."
        ) from exc

    resolved = cast(
        str,
        font_manager.findfont(
            font_family,
            fallback_to_default=False,
        ),
    )
    if not resolved or not os.path.isfile(resolved):
        raise RuntimeError(
            f"Could not resolve font '{font_family}'. Pass --svg-font-path explicitly."
        )
    return os.path.abspath(resolved)


def glyph_outline_for_char(
    *,
    ch: str,
    cmap: Dict[int, str],
    glyph_set: Any,
    svg_path_pen_cls: Any,
    bounds_pen_cls: Any,
) -> Optional[Tuple[str, Tuple[float, float, float, float]]]:
    glyph_name = cmap.get(ord(ch))
    if not glyph_name:
        return None
    if glyph_name not in glyph_set:
        return None
    glyph = glyph_set[glyph_name]
    path_pen = svg_path_pen_cls(glyph_set)
    glyph.draw(path_pen)
    path_data = path_pen.getCommands()
    if not path_data:
        return None

    bounds_pen = bounds_pen_cls(glyph_set)
    glyph.draw(bounds_pen)
    if bounds_pen.bounds is None:
        return None
    x_min, y_min, x_max, y_max = bounds_pen.bounds
    if x_max <= x_min or y_max <= y_min:
        return None
    return path_data, (float(x_min), float(y_min), float(x_max), float(y_max))
