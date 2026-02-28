"""Color helpers for ASCIIRenderer"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional, Set, Tuple

from .ansi import ANSI_SUBWAY_PALETTE

if TYPE_CHECKING:
    from phart.renderer import ASCIIRenderer


## this seems unused - renderer refactor
def resolve_attr_edge_color(
    renderer: ASCIIRenderer,
    edge: Tuple[Any, Any],
    idx: int,
    node_palette_map: Optional[Dict[Any, str]] = None,
) -> Optional[str]:
    """Resolve edge color from configured attribute rules."""
    node_palette = node_palette_map if node_palette_map is not None else {}
    fallback = (
        node_palette.get(edge[0])
        or renderer._node_color_map.get(edge[0])
        or ANSI_SUBWAY_PALETTE[idx % len(ANSI_SUBWAY_PALETTE)]
    )
    edge_data = renderer.graph.get_edge_data(edge[0], edge[1]) or {}
    normalized_data = {
        str(key).strip().lower(): renderer._normalize_edge_attr_value(value)
        for key, value in edge_data.items()
    }

    for attr_name, mapping in renderer.options.edge_color_rules.items():
        attr_value = normalized_data.get(attr_name)
        if attr_value is None:
            continue
        color_spec = mapping.get(attr_value)
        if color_spec is None:
            continue
        resolved = renderer._resolve_color_spec(color_spec)
        if resolved is not None:
            return resolved
        break

    return fallback


def initialize_color_maps(
    renderer: ASCIIRenderer, positions: Dict[Any, Tuple[int, int]]
) -> None:
    renderer._node_color_map = {}
    renderer._edge_color_map = {}
    if not renderer._use_ansi_colors():
        return

    if not ANSI_SUBWAY_PALETTE:
        return

    sorted_nodes = sorted(
        positions.items(),
        key=lambda item: (item[1][1], item[1][0], str(item[0])),
    )
    node_palette_map: Dict[Any, str] = {}
    for idx, (node, _) in enumerate(sorted_nodes):
        node_palette_map[node] = ANSI_SUBWAY_PALETTE[idx % len(ANSI_SUBWAY_PALETTE)]

    if renderer.options.color_nodes:
        renderer._node_color_map = node_palette_map.copy()

    sorted_edges = sorted(
        (
            edge
            for edge in renderer.graph.edges()
            if edge[0] in positions and edge[1] in positions
        ),
        key=lambda edge: (
            positions[edge[0]][1],
            positions[edge[0]][0],
            positions[edge[1]][1],
            positions[edge[1]][0],
            str(edge[0]),
            str(edge[1]),
        ),
    )

    # see TODO in styles.py re: edge_color_mode, etc
    edge_mode = renderer.options.edge_color_mode
    for idx, edge in enumerate(sorted_edges):
        if edge_mode == "target":
            color = node_palette_map.get(edge[1])
        elif edge_mode == "source":
            color = node_palette_map.get(edge[0])
        elif edge_mode == "attr":
            color = renderer._resolve_attr_edge_color(edge, idx, node_palette_map)
        else:  # path
            color = ANSI_SUBWAY_PALETTE[idx % len(ANSI_SUBWAY_PALETTE)]

        if color is None:
            color = ANSI_SUBWAY_PALETTE[idx % len(ANSI_SUBWAY_PALETTE)]
        renderer._edge_color_map[edge] = color


def paint_cell(
    renderer: ASCIIRenderer, x: int, y: int, char: str, color: Optional[str] = None
) -> None:
    renderer.canvas[y][x] = char
    if not (renderer._use_ansi_colors or renderer.options.edge_color_mode):
        return
    renderer._color_canvas[y][x] = color
    renderer._edge_conflict_cells.discard((x, y))
    renderer._locked_arrow_cells.discard((x, y))


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
    if key in renderer._locked_arrow_cells and not renderer._is_arrow_glyph(char):
        # Preserve terminal arrow glyphs even when later edges overlap.
        renderer._merge_edge_cell_color(x, y, color)
        return

    renderer.canvas[y][x] = char
    if renderer._is_arrow_glyph(char):
        renderer._locked_arrow_cells.add(key)

    renderer._merge_edge_cell_color(x, y, color)
