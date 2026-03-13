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
    line_vertical = renderer._edge_style_glyph(
        "line_vertical", renderer.options.edge_vertical
    )
    for y in range(start_y + 1, end_y):
        renderer._paint_edge_cell(x, y, line_vertical, color)
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
    line_horizontal = renderer._edge_style_glyph(
        "line_horizontal", renderer.options.edge_horizontal
    )
    for x in range(start_x + 1, end_x):
        renderer._paint_edge_cell(x, y, line_horizontal, color)
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
    override_dirs = renderer._line_dirs_override_map.get(ch)
    if override_dirs:
        return set(override_dirs)
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

    key = frozenset(dirs)
    glyph_map = {
        frozenset({"up", "down"}): renderer._edge_style_glyph(
            "line_vertical", renderer.options.edge_vertical
        ),
        frozenset({"left", "right"}): renderer._edge_style_glyph(
            "line_horizontal", renderer.options.edge_horizontal
        ),
        frozenset({"right", "down"}): renderer._edge_style_glyph(
            "corner_ul", renderer.options.edge_corner_ul
        ),
        frozenset({"left", "down"}): renderer._edge_style_glyph(
            "corner_ur", renderer.options.edge_corner_ur
        ),
        frozenset({"right", "up"}): renderer._edge_style_glyph(
            "corner_ll", renderer.options.edge_corner_ll
        ),
        frozenset({"left", "up"}): renderer._edge_style_glyph(
            "corner_lr", renderer.options.edge_corner_lr
        ),
        frozenset({"left", "right", "down"}): renderer._edge_style_glyph(
            "tee_down", renderer.options.edge_tee_down
        ),
        frozenset({"left", "right", "up"}): renderer._edge_style_glyph(
            "tee_up", renderer.options.edge_tee_up
        ),
        frozenset({"up", "down", "right"}): renderer._edge_style_glyph(
            "tee_right", renderer.options.edge_tee_right
        ),
        frozenset({"up", "down", "left"}): renderer._edge_style_glyph(
            "tee_left", renderer.options.edge_tee_left
        ),
        frozenset({"up", "down", "left", "right"}): renderer._edge_style_glyph(
            "cross", renderer.options.edge_cross
        ),
    }

    if key in glyph_map:
        return glyph_map[key]

    if "left" in dirs or "right" in dirs:
        return renderer._edge_style_glyph("line_horizontal", renderer.options.edge_horizontal)
    return renderer._edge_style_glyph("line_vertical", renderer.options.edge_vertical)


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
    elif not renderer._is_arrow_glyph(renderer.canvas[y][x]):
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
            line_dirs = renderer._line_dirs_for_char(cell)
            if line_dirs == {"up", "down"} and x in (top_center, bottom_center):
                continue
            conflict = True
            break
        if not conflict:
            return jog_y

    return latest_jog


def _edge_label_text(renderer: ASCIIRenderer, start: Any, end: Any) -> Optional[str]:
    edge_label_attr = renderer.options.edge_label_attr
    if not edge_label_attr:
        return None
    edge_data = renderer.graph.get_edge_data(start, end) or {}
    label: Any = None
    if isinstance(edge_data, dict):
        if edge_label_attr in edge_data:
            label = edge_data.get(edge_label_attr)
        else:
            for candidate in edge_data.values():
                if isinstance(candidate, dict) and edge_label_attr in candidate:
                    label = candidate.get(edge_label_attr)
                    break
    if label is None:
        return None
    text = renderer._normalize_label_value(label)
    return text if text else None


def _paint_label_text(
    renderer: ASCIIRenderer,
    x: int,
    y: int,
    text: str,
    color: Optional[str],
) -> None:
    if y < 0 or y >= len(renderer.canvas):
        return
    if x >= len(renderer.canvas[y]):
        return
    if x < 0:
        text = text[-x:]
        x = 0
    if not text:
        return
    text = text[: max(0, len(renderer.canvas[y]) - x)]
    for offset, char in enumerate(text):
        renderer._paint_edge_cell(x + offset, y, char, color)


def _draw_edge_label(
    renderer: ASCIIRenderer,
    *,
    text: str,
    start_x: int,
    start_y: int,
    end_x: int,
    end_y: int,
    jog_y: Optional[int],
    color: Optional[str],
) -> None:
    if not text:
        return

    def _fallback_label() -> None:
        mid_y = (min(start_y, end_y) + max(start_y, end_y)) // 2
        label_x = max(start_x, end_x) + 2
        _paint_label_text(renderer, label_x, mid_y, text, color)

    if start_y == end_y:
        min_x = min(start_x, end_x) + 1
        max_x = max(start_x, end_x) - 1
        available = max_x - min_x + 1
        if available < len(text):
            _fallback_label()
            return
        center_x = (min_x + max_x) // 2
        label_start = max(min_x, center_x - (len(text) // 2))
        _paint_label_text(renderer, label_start, start_y, text, color)
        return

    if jog_y is not None and start_x != end_x:
        min_x = min(start_x, end_x) + 1
        max_x = max(start_x, end_x) - 1
        available = max_x - min_x + 1
        if available >= len(text):
            center_x = (min_x + max_x) // 2
            label_start = max(min_x, center_x - (len(text) // 2))
            _paint_label_text(renderer, label_start, jog_y, text, color)
            return

    _fallback_label()


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
    edge_label = _edge_label_text(renderer, start, end)
    jog_y: Optional[int] = None

    is_bidirectional = renderer._is_bidirectional_edge(start, end)
    previous_style_set = renderer._active_edge_style_set
    renderer._active_edge_style_set = renderer._resolve_effective_edge_style_set(
        start, end
    )

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
                        renderer._edge_arrow_for_direction("left"),
                        edge_color,
                    )
                    renderer._paint_edge_cell(
                        max_x,
                        y,
                        renderer._edge_arrow_for_direction("right"),
                        edge_color,
                    )
            elif min_x <= max_x:
                if start_x < end_x:
                    renderer._paint_edge_cell(
                        max_x,
                        y,
                        renderer._edge_arrow_for_direction("right"),
                        edge_color,
                    )
                else:
                    renderer._paint_edge_cell(
                        min_x,
                        y,
                        renderer._edge_arrow_for_direction("left"),
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
                if renderer.canvas[y][top_center] != renderer._edge_style_glyph(
                    "cross", renderer.options.edge_cross
                ):
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
                    renderer._edge_arrow_for_direction("up"),
                    edge_color,
                )
                renderer._paint_edge_cell(
                    bottom_center,
                    bottom_terminal_y,
                    renderer._edge_arrow_for_direction("down"),
                    edge_color,
                )
            else:
                if start_y < end_y:
                    renderer._paint_edge_cell(
                        bottom_center,
                        bottom_terminal_y,
                        renderer._edge_arrow_for_direction("down"),
                        edge_color,
                    )
                else:
                    renderer._paint_edge_cell(
                        top_center,
                        top_terminal_y,
                        renderer._edge_arrow_for_direction("up"),
                        edge_color,
                    )

        if edge_label:
            _draw_edge_label(
                renderer,
                text=edge_label,
                start_x=start_x,
                start_y=start_y,
                end_x=end_x,
                end_y=end_y,
                jog_y=jog_y,
                color=edge_color,
            )

    except IndexError as exc:
        raise IndexError(f"Edge drawing exceeded canvas boundaries: {exc}") from exc
    finally:
        renderer._active_edge_style_set = previous_style_set
