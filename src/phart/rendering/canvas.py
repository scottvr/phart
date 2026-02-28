"""helpers for renderer - rendering.canvas"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from phart.renderer import ASCIIRenderer

from .ansi import ANSI_RESET


def init_canvas(
    renderer: ASCIIRenderer,
    width: int,
    height: int,
    positions: Dict[Any, Tuple[int, int]],
) -> None:
    """
    Initialize blank canvas with given dimensions.

    Args:
        width: Canvas width in characters
        height: Canvas height in characters
        positions: Node positions (kept for API compatibility)

    Raises:
        ValueError: If dimensions are negative
    """
    # Calculate minimum dimensions needed
    max_right = max(
        (
            x + renderer._get_node_dimensions(node)[0]
            for node, (x, _) in positions.items()
        ),
        default=1,
    )
    max_bottom = max(
        (
            y + renderer._get_node_dimensions(node)[1]
            for node, (_, y) in positions.items()
        ),
        default=1,
    )

    # Ensure minimum dimensions that can hold all nodes and edge routing.
    min_width = max_right + 1
    min_height = max_bottom + 2

    final_width = max(width, min_width)
    final_height = max(height, min_height)

    if final_width < 0 or final_height < 0:
        raise ValueError(
            f"Canvas dimensions must not be negative (got {width}x{height})"
        )

    renderer.canvas = [[" " for _ in range(final_width)] for _ in range(final_height)]
    renderer._color_canvas = [
        [None for _ in range(final_width)] for _ in range(final_height)
    ]
    renderer._edge_conflict_cells = set()
    renderer._locked_arrow_cells = set()


def render_row(
    renderer: ASCIIRenderer, row: List[str], colors: List[Optional[str]]
) -> str:
    last = -1
    for idx, ch in enumerate(row):
        if ch != " ":
            last = idx
    if last < 0:
        return ""

    if not renderer._use_ansi_colors():
        return "".join(row[: last + 1])

    rendered: List[str] = []
    active_color: Optional[str] = None
    for idx in range(last + 1):
        color = colors[idx]
        if color != active_color:
            if active_color is not None:
                rendered.append(ANSI_RESET)
            if color is not None:
                rendered.append(color)
            active_color = color
        rendered.append(row[idx])

    if active_color is not None:
        rendered.append(ANSI_RESET)
    return "".join(rendered)


def merge_edge_cell_color(
    renderer: ASCIIRenderer, x: int, y: int, color: Optional[str]
) -> None:
    if not renderer._use_ansi_colors():
        return

    key = (x, y)
    if key in renderer._edge_conflict_cells:
        renderer._color_canvas[y][x] = None
        return

    existing = renderer._color_canvas[y][x]
    if existing is None:
        renderer._color_canvas[y][x] = color
        return

    if color is None or existing == color:
        return

    renderer._color_canvas[y][x] = None
    renderer._edge_conflict_cells.add(key)


def paint_edge_cell(
    renderer: ASCIIRenderer, x: int, y: int, char: str, color: Optional[str] = None
) -> None:
    key = (x, y)
    if key in renderer._locked_arrow_cells and not is_arrow_glyph(renderer, char):
        # Preserve terminal arrow glyphs even when later edges overlap.
        merge_edge_cell_color(renderer, x, y, color)
        return


def paint_cell(
    renderer: ASCIIRenderer, x: int, y: int, char: str, color: Optional[str] = None
) -> None:
    renderer.canvas[y][x] = char
    if not renderer._use_ansi_colors():
        return
    renderer._color_canvas[y][x] = color
    renderer._edge_conflict_cells.discard((x, y))
    renderer._locked_arrow_cells.discard((x, y))


def is_arrow_glyph(renderer: ASCIIRenderer, char: str) -> bool:
    return char in {
        renderer.options.edge_arrow_up,
        renderer.options.edge_arrow_down,
        renderer.options.edge_arrow_l,
        renderer.options.edge_arrow_r,
    }
