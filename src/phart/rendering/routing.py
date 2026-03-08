"""Edge routing and line-drawing helpers for ASCIIRenderer."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional, Set, Tuple

if TYPE_CHECKING:
    from phart.renderer import ASCIIRenderer


def should_skip_edge_draw(
    renderer: ASCIIRenderer,
    start: Any,
    end: Any,
    drawn_bidirectional_pairs: Set[frozenset[Any]],
) -> bool:
    """Skip second pass when a reciprocal edge can share one route."""
    if not renderer._is_bidirectional_edge(start, end):
        return False
    if (end, start) not in renderer.graph.edges():
        return False

    if renderer._edge_color_map.get((start, end)) != renderer._edge_color_map.get(
        (
            end,
            start,
        )
    ):
        return False

    pair_key = frozenset((start, end))
    if pair_key in drawn_bidirectional_pairs:
        return True

    drawn_bidirectional_pairs.add(pair_key)
    return False


def draw_vertical_segment(
    renderer: ASCIIRenderer,
    x: int,
    start_y: int,
    end_y: int,
    marker: Optional[str],
    color: Optional[str] = None,
) -> None:
    # TODO(width): Edge routing currently treats line glyphs as single-cell.
    # Supporting wide/custom edge glyphs will require width-aware stepping.
    for y in range(start_y + 1, end_y):
        renderer._paint_edge_cell(x, y, renderer.options.edge_vertical, color)
    if marker is not None:
        mid_y = (start_y + end_y) // 2
        renderer._paint_edge_cell(x, mid_y, marker, color)


def draw_horizontal_segment(
    renderer: ASCIIRenderer,
    y: int,
    start_x: int,
    end_x: int,
    marker: Optional[str],
    color: Optional[str] = None,
) -> None:
    # TODO(width): Edge routing currently treats line glyphs as single-cell.
    # Supporting wide/custom edge glyphs will require width-aware stepping.
    for x in range(start_x + 1, end_x):
        renderer._paint_edge_cell(x, y, renderer.options.edge_horizontal, color)
    if marker is not None:
        mid_x = (start_x + end_x) // 2
        renderer._paint_edge_cell(mid_x, y, marker, color)


def safe_draw(
    renderer: ASCIIRenderer, x: int, y: int, char: str, color: Optional[str] = None
) -> None:
    try:
        renderer._paint_edge_cell(x, y, char, color)
    except IndexError as exc:
        raise IndexError(f"Drawing exceeded canvas bounds at ({x}, {y})") from exc


def line_dirs_for_char(renderer: ASCIIRenderer, ch: str) -> Set[str]:
    """Map existing glyphs to line connection directions."""
    if ch in (
        renderer.options.edge_vertical,
        renderer.options.edge_arrow_up,
        renderer.options.edge_arrow_down,
    ):
        return {"up", "down"}
    if ch in (
        renderer.options.edge_horizontal,
        renderer.options.edge_arrow_l,
        renderer.options.edge_arrow_r,
    ):
        return {"left", "right"}

    unicode_map: Dict[str, Set[str]] = {
        "┌": {"right", "down"},
        "┐": {"left", "down"},
        "└": {"right", "up"},
        "┘": {"left", "up"},
        "┬": {"left", "right", "down"},
        "┴": {"left", "right", "up"},
        "├": {"up", "down", "right"},
        "┤": {"up", "down", "left"},
        "┼": {"up", "down", "left", "right"},
        "+": {"up", "down", "left", "right"},
        "|": {"up", "down"},
        "-": {"left", "right"},
    }
    return unicode_map.get(ch, set())


def glyph_for_line_dirs(renderer: ASCIIRenderer, dirs: Set[str]) -> str:
    """Choose ASCII/Unicode line-art glyph for a connection set."""
    if not dirs:
        return " "

    if renderer.options.use_ascii:
        if ("left" in dirs or "right" in dirs) and ("up" in dirs or "down" in dirs):
            return "+"
        if "left" in dirs or "right" in dirs:
            return "-"
        return "|"

    key = frozenset(dirs)
    unicode_glyphs = {
        frozenset({"up", "down"}): renderer.options.edge_vertical,
        frozenset({"left", "right"}): renderer.options.edge_horizontal,
        frozenset({"right", "down"}): renderer.options.edge_corner_ul,
        frozenset({"left", "down"}): renderer.options.edge_corner_ur,
        frozenset({"right", "up"}): renderer.options.edge_corner_ll,
        frozenset({"left", "up"}): renderer.options.edge_corner_lr,
        frozenset({"left", "right", "down"}): renderer.options.edge_tee_down,
        frozenset({"left", "right", "up"}): renderer.options.edge_tee_up,
        frozenset({"up", "down", "right"}): renderer.options.edge_tee_right,
        frozenset({"up", "down", "left"}): renderer.options.edge_tee_left,
        frozenset({"up", "down", "left", "right"}): renderer.options.edge_cross,
    }

    if key in unicode_glyphs:
        return unicode_glyphs[key]
    if "left" in dirs or "right" in dirs:
        return renderer.options.edge_horizontal
    return renderer.options.edge_vertical


def merge_line_cell(
    renderer: ASCIIRenderer,
    x: int,
    y: int,
    add_dirs: Set[str],
    color: Optional[str] = None,
) -> None:
    current = renderer.canvas[y][x]
    merged_dirs = renderer._line_dirs_for_char(current) | add_dirs
    renderer._paint_edge_cell(x, y, renderer._glyph_for_line_dirs(merged_dirs), color)


def is_terminal(
    renderer: ASCIIRenderer,
    positions: Dict[Any, Tuple[int, int]],
    node: Any,
    x: int,
    y: int,
) -> bool:
    if node not in positions:
        return False
    bounds = renderer._get_node_bounds(node, positions)
    return y == bounds["center_y"] and x in {
        bounds["left"],
        bounds["right"],
        bounds["center_x"],
    }


def draw_direction(
    renderer: ASCIIRenderer,
    y: int,
    x: int,
    direction: str,
    is_terminal: bool = False,
    color: Optional[str] = None,
) -> None:
    if is_terminal:
        renderer._paint_edge_cell(x, y, direction, color)
    elif renderer.canvas[y][x] not in (
        renderer.options.edge_arrow_up,
        renderer.options.edge_arrow_down,
    ):
        renderer._paint_edge_cell(x, y, direction, color)


def get_jog_row(
    renderer: ASCIIRenderer,
    top_center: int,
    bottom_center: int,
    top_y: int,
    bottom_y: int,
) -> int:
    """Choose a jog row for a parent→child edge that avoids conflicts."""
    min_x = min(top_center, bottom_center)
    max_x = max(top_center, bottom_center)
    latest_jog = bottom_y - 2
    if latest_jog < top_y + 1:
        return top_y + 1

    for jog_y in range(top_y + 1, latest_jog + 1):
        conflict = False
        for x in range(min_x, max_x + 1):
            cell = renderer.canvas[jog_y][x]
            if cell == " ":
                continue
            if cell == renderer.options.edge_vertical and x in (
                top_center,
                bottom_center,
            ):
                continue
            conflict = True
            break
        if not conflict:
            return jog_y

    return latest_jog


def draw_edge(
    renderer: ASCIIRenderer,
    start: Any,
    end: Any,
    positions: Dict[Any, Tuple[int, int]],
) -> None:
    """Draw an edge between two nodes on the canvas."""
    if start not in positions or end not in positions:
        raise KeyError(
            f"Node position not found: {start if start not in positions else end}"
        )

    start_anchor, end_anchor = renderer._get_edge_anchor_points(start, end, positions)
    start_x, start_y = start_anchor
    end_x, end_y = end_anchor
    edge_color = renderer._edge_color_map.get((start, end))

    is_bidirectional = renderer._is_bidirectional_edge(start, end)

    try:
        if start_y == end_y:
            y = start_y
            min_x = min(start_x, end_x) + 1
            max_x = max(start_x, end_x) - 1

            for x in range(min_x, max_x + 1):
                renderer._merge_line_cell(x, y, {"left", "right"}, edge_color)

            if is_bidirectional:
                if min_x <= max_x:
                    renderer._paint_edge_cell(
                        min_x,
                        y,
                        renderer.options.get_arrow_for_direction("left"),
                        edge_color,
                    )
                    renderer._paint_edge_cell(
                        max_x,
                        y,
                        renderer.options.get_arrow_for_direction("right"),
                        edge_color,
                    )
            elif min_x <= max_x:
                if start_x < end_x:
                    renderer._paint_edge_cell(
                        max_x,
                        y,
                        renderer.options.get_arrow_for_direction("right"),
                        edge_color,
                    )
                else:
                    renderer._paint_edge_cell(
                        min_x,
                        y,
                        renderer.options.get_arrow_for_direction("left"),
                        edge_color,
                    )

        else:
            top_anchor = start_anchor if start_y < end_y else end_anchor
            bottom_anchor = end_anchor if start_y < end_y else start_anchor

            top_center = top_anchor[0]
            bottom_center = bottom_anchor[0]
            top_y = top_anchor[1]
            bottom_y = bottom_anchor[1]

            if bottom_y <= top_y + 1:
                return

            if top_center == bottom_center:
                jog_y = top_y + 1
            else:
                jog_y = renderer._get_jog_row(
                    top_center, bottom_center, top_y, bottom_y
                )

            for y in range(top_y + 1, jog_y):
                if renderer.canvas[y][top_center] != renderer.options.edge_cross:
                    renderer._merge_line_cell(top_center, y, {"up", "down"}, edge_color)

            if top_center != bottom_center:
                top_dirs: Set[str] = {"up"}
                bottom_dirs: Set[str] = {"down"}
                if bottom_center > top_center:
                    top_dirs.add("right")
                    bottom_dirs.add("left")
                else:
                    top_dirs.add("left")
                    bottom_dirs.add("right")

                renderer._merge_line_cell(top_center, jog_y, top_dirs, edge_color)
                renderer._merge_line_cell(bottom_center, jog_y, bottom_dirs, edge_color)

                min_x = min(top_center, bottom_center)
                max_x = max(top_center, bottom_center)
                for x in range(min_x + 1, max_x):
                    renderer._merge_line_cell(x, jog_y, {"left", "right"}, edge_color)
            else:
                renderer._merge_line_cell(top_center, jog_y, {"up", "down"}, edge_color)

            for y in range(jog_y + 1, bottom_y):
                renderer._merge_line_cell(bottom_center, y, {"up", "down"}, edge_color)

            top_terminal_y = top_y + 1
            bottom_terminal_y = bottom_y - 1
            if is_bidirectional:
                renderer._paint_edge_cell(
                    top_center,
                    top_terminal_y,
                    renderer.options.get_arrow_for_direction("up"),
                    edge_color,
                )
                renderer._paint_edge_cell(
                    bottom_center,
                    bottom_terminal_y,
                    renderer.options.get_arrow_for_direction("down"),
                    edge_color,
                )
            else:
                if start_y < end_y:
                    renderer._paint_edge_cell(
                        bottom_center,
                        bottom_terminal_y,
                        renderer.options.get_arrow_for_direction("down"),
                        edge_color,
                    )
                else:
                    renderer._paint_edge_cell(
                        top_center,
                        top_terminal_y,
                        renderer.options.get_arrow_for_direction("up"),
                        edge_color,
                    )

    except IndexError as exc:
        raise IndexError(f"Edge drawing exceeded canvas boundaries: {exc}") from exc
