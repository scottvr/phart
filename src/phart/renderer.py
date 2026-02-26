from __future__ import annotations
from typing import Any, Dict, List, Optional, TextIO, Tuple, ClassVar, Set, cast
import os
from html import escape as html_escape

import networkx as nx  # type: ignore

from .layout import LayoutManager
from .rendering.ansi import (
    ANSI_RESET,
    ANSI_SUBWAY_PALETTE,
    ansi_to_hex as _ansi_to_hex_impl,
    normalize_edge_attr_value as _normalize_edge_attr_value_impl,
    resolve_color_spec as _resolve_color_spec_impl,
    xterm_index_to_hex as _xterm_index_to_hex_impl,
)
from .rendering import ports as ports_mod
from .rendering import routing as routing_mod
from .styles import LayoutOptions, NodeStyle

import sys
import io


class ASCIIRenderer:
    """
    ASCII art renderer for graphs.

    This class provides functionality to render graphs as ASCII art, with
    support for different node styles and layout options.

    Parameters
    ----------
    graph : NetworkX graph
        The graph to render
    node_style : NodeStyle, optional (default=NodeStyle.MINIMAL)
        Style for node representation
    node_spacing : int, optional (default=4)
        Minimum horizontal space between nodes
    layer_spacing : int, optional (default=2)
        Number of lines between layers

    Attributes
    ----------
    graph : NetworkX graph
        The graph being rendered
    options : LayoutOptions
        Layout and style configuration

    See Also
    --------
    render : Render the graph as ASCII art
    from_dot : Create renderer from DOT format
    """

    @staticmethod
    def _is_redirected() -> bool:
        """Check if output is being redirected."""
        if sys.platform == "win32":
            import msvcrt
            import ctypes

            try:
                fileno = sys.stdout.fileno()
                handle = msvcrt.get_osfhandle(fileno)
                return not bool(ctypes.windll.kernel32.GetConsoleMode(handle, None))
            except OSError:
                return True
            except AttributeError:
                return True
        return not sys.stdout.isatty()

    @staticmethod
    def _can_use_unicode() -> bool:
        """Internal check for Unicode support."""
        if sys.platform == "win32":
            try:
                import ctypes

                kernel32 = ctypes.windll.kernel32
                return bool(kernel32.GetConsoleOutputCP() == 65001)
            except BaseException:
                return False
        return True

    default_options: ClassVar[Optional[LayoutOptions]] = None

    def __init__(
        self,
        graph: nx.DiGraph,
        *,  # Force keyword args after this
        node_style: NodeStyle = NodeStyle.SQUARE,
        node_spacing: int = 4,
        layer_spacing: int = 2,
        use_ascii: Optional[bool] = None,
        custom_decorators: Optional[Dict[str, Tuple[str, str]]] = None,
        options: Optional[LayoutOptions] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the ASCII renderer.

        Args:
            graph: The networkx graph to render
            node_style: Style for nodes (must be passed as keyword arg)
            node_spacing: Horizontal spacing between nodes (must be passed as keyword arg)
            layer_spacing: Vertical spacing between layers (must be passed as keyword arg)
            use_ascii: Force ASCII output (must be passed as keyword arg)
            custom_decorators: Custom node decorations (must be passed as keyword arg)
            options: LayoutOptions instance (must be passed as keyword arg)
        """
        options = self._resolve_options(options=options)
        self.options = options

        self.graph = graph

        if options is not None and options.use_ascii is not None:
            use_ascii = options.use_ascii
        elif use_ascii is None:
            use_ascii = not self._can_use_unicode()

        if options is not None:
            self.options = options
            self.options.use_ascii = use_ascii
            if custom_decorators is not None:
                self.options.custom_decorators = custom_decorators
            # Make sure node_style is properly set to just the style enum
            if isinstance(self.options, LayoutOptions):
                self.options.node_style = self.options.node_style
        elif self.default_options is not None:
            self.options = self.default_options
        else:
            self.options = LayoutOptions(
                node_style=node_style,
                node_spacing=node_spacing,
                layer_spacing=layer_spacing,
                use_ascii=use_ascii,
                custom_decorators=custom_decorators,
            )
        self.layout_manager = LayoutManager(graph, self.options)
        self.canvas: List[List[str]] = []
        self._color_canvas: List[List[Optional[str]]] = []
        self._edge_anchor_map: Dict[Tuple[Any, Any], Dict[str, Tuple[int, int]]] = {}
        self._node_color_map: Dict[Any, str] = {}
        self._edge_color_map: Dict[Tuple[Any, Any], str] = {}
        self._edge_conflict_cells: Set[Tuple[int, int]] = set()
        self._locked_arrow_cells: Set[Tuple[int, int]] = set()

    @classmethod
    def _resolve_options(cls, options: Optional[LayoutOptions]) -> LayoutOptions:
        if cls.default_options is None:
            # no CLI overrides; if no options passed, create defaults however you do it
            return options if options is not None else LayoutOptions()

        if options is None:
            return cls.default_options

        # precedence: CLI overrides user script options
        return merge_layout_options(options, cls.default_options)

    def _ensure_encoding(self, text: str) -> str:
        """Internal method to handle encoding safely."""
        try:
            return text.encode("utf-8").decode("utf-8")
        except UnicodeEncodeError:
            return text.encode("ascii", errors="replace").decode("ascii")

    def _use_ansi_colors(self) -> bool:
        return bool(
            self.options.ansi_colors
            and (not self.options.use_ascii or self.options.allow_ansi_in_ascii)
        )

    @staticmethod
    def _normalize_edge_attr_value(value: Any) -> str:
        return _normalize_edge_attr_value_impl(value)

    @staticmethod
    def _resolve_color_spec(spec: Any) -> Optional[str]:
        return _resolve_color_spec_impl(spec)

    def _resolve_attr_edge_color(
        self,
        edge: Tuple[Any, Any],
        idx: int,
        node_palette_map: Optional[Dict[Any, str]] = None,
    ) -> Optional[str]:
        """Resolve edge color from configured attribute rules."""
        node_palette = node_palette_map if node_palette_map is not None else {}
        fallback = (
            node_palette.get(edge[0])
            or self._node_color_map.get(edge[0])
            or ANSI_SUBWAY_PALETTE[idx % len(ANSI_SUBWAY_PALETTE)]
        )
        edge_data = self.graph.get_edge_data(edge[0], edge[1]) or {}
        normalized_data = {
            str(key).strip().lower(): self._normalize_edge_attr_value(value)
            for key, value in edge_data.items()
        }

        for attr_name, mapping in self.options.edge_color_rules.items():
            attr_value = normalized_data.get(attr_name)
            if attr_value is None:
                continue
            color_spec = mapping.get(attr_value)
            if color_spec is None:
                continue
            resolved = self._resolve_color_spec(color_spec)
            if resolved is not None:
                return resolved
            break

        return fallback

    def _normalized_edge_attrs(self, start: Any, end: Any) -> Dict[str, str]:
        edge_data = self.graph.get_edge_data(start, end) or {}
        return {
            str(key).strip().lower(): self._normalize_edge_attr_value(value)
            for key, value in edge_data.items()
        }

    def _attr_rules_match_for_reverse_edge(self, start: Any, end: Any) -> bool:
        """Return True when attr-color rule attributes agree in both directions."""
        if self.options.edge_color_mode != "attr":
            return True
        if not self.options.edge_color_rules:
            return True

        forward_attrs = self._normalized_edge_attrs(start, end)
        reverse_attrs = self._normalized_edge_attrs(end, start)
        for attr_name in self.options.edge_color_rules:
            if forward_attrs.get(attr_name) != reverse_attrs.get(attr_name):
                return False
        return True

    def _is_bidirectional_edge(self, start: Any, end: Any) -> bool:
        """Determine whether an edge should render as bidirectional."""
        if not self.graph.is_directed():
            return True
        if (end, start) not in self.graph.edges():
            return False
        return self._attr_rules_match_for_reverse_edge(start, end)

    def _should_use_ports_for_edge(self, start: Any, end: Any) -> bool:
        """Decide whether this edge should use distributed box ports."""
        if not self.options.bboxes:
            return False
        if self.options.edge_anchor_mode == "ports":
            return True
        if self.options.edge_anchor_mode != "auto":
            return False
        if (end, start) not in self.graph.edges():
            return False
        return not self._attr_rules_match_for_reverse_edge(start, end)

    def _initialize_color_maps(self, positions: Dict[Any, Tuple[int, int]]) -> None:
        self._node_color_map = {}
        self._edge_color_map = {}
        if not self._use_ansi_colors():
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

        if self.options.color_nodes:
            self._node_color_map = node_palette_map.copy()

        sorted_edges = sorted(
            (
                edge
                for edge in self.graph.edges()
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

        edge_mode = self.options.edge_color_mode
        for idx, edge in enumerate(sorted_edges):
            if edge_mode == "target":
                color = node_palette_map.get(edge[1])
            elif edge_mode == "source":
                color = node_palette_map.get(edge[0])
            elif edge_mode == "attr":
                color = self._resolve_attr_edge_color(edge, idx, node_palette_map)
            else:  # path
                color = ANSI_SUBWAY_PALETTE[idx % len(ANSI_SUBWAY_PALETTE)]

            if color is None:
                color = ANSI_SUBWAY_PALETTE[idx % len(ANSI_SUBWAY_PALETTE)]
            self._edge_color_map[edge] = color

    def _paint_cell(
        self, x: int, y: int, char: str, color: Optional[str] = None
    ) -> None:
        self.canvas[y][x] = char
        if not self._use_ansi_colors():
            return
        self._color_canvas[y][x] = color
        self._edge_conflict_cells.discard((x, y))
        self._locked_arrow_cells.discard((x, y))

    def _is_arrow_glyph(self, char: str) -> bool:
        return char in {
            self.options.edge_arrow_up,
            self.options.edge_arrow_down,
            self.options.edge_arrow_l,
            self.options.edge_arrow_r,
        }

    def _merge_edge_cell_color(self, x: int, y: int, color: Optional[str]) -> None:
        if not self._use_ansi_colors():
            return

        key = (x, y)
        if key in self._edge_conflict_cells:
            self._color_canvas[y][x] = None
            return

        existing = self._color_canvas[y][x]
        if existing is None:
            self._color_canvas[y][x] = color
            return

        if color is None or existing == color:
            return

        self._color_canvas[y][x] = None
        self._edge_conflict_cells.add(key)

    def _paint_edge_cell(
        self, x: int, y: int, char: str, color: Optional[str] = None
    ) -> None:
        key = (x, y)
        if key in self._locked_arrow_cells and not self._is_arrow_glyph(char):
            # Preserve terminal arrow glyphs even when later edges overlap.
            self._merge_edge_cell_color(x, y, color)
            return

        self.canvas[y][x] = char
        if self._is_arrow_glyph(char):
            self._locked_arrow_cells.add(key)

        self._merge_edge_cell_color(x, y, color)

    def _render_row(self, row: List[str], colors: List[Optional[str]]) -> str:
        last = -1
        for idx, ch in enumerate(row):
            if ch != " ":
                last = idx
        if last < 0:
            return ""

        if not self._use_ansi_colors():
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

    @staticmethod
    def _normalize_label_value(label: Any) -> str:
        """Normalize node labels for single-line display."""
        text = str(label).strip()
        if len(text) >= 2 and text[0] == text[-1] and text[0] in {"'", '"'}:
            text = text[1:-1]
        text = text.replace("\r\n", " ").replace("\n", " ")
        return text.strip()

    def _get_display_node_text(self, node: Any) -> str:
        """Resolve display text for a node key."""
        if self.options.use_labels:
            label = self.graph.nodes[node].get("label") if node in self.graph else None
            if label is not None:
                normalized = self._normalize_label_value(label)
                if normalized:
                    return normalized
        return str(node)

    def _get_widest_node_text_width(self) -> Optional[int]:
        if not self.options.uniform:
            return None
        return max(
            (
                len(self.options.get_node_text(self._get_display_node_text(node)))
                for node in self.graph.nodes()
            ),
            default=0,
        )

    def _get_node_dimensions(self, node: Any) -> Tuple[int, int]:
        return self.options.get_node_dimensions(
            self._get_display_node_text(node),
            widest_text_width=self._get_widest_node_text_width(),
        )

    def _get_node_bounds(
        self, node: Any, positions: Dict[Any, Tuple[int, int]]
    ) -> Dict[str, int]:
        x, y = positions[node]
        width, height = self._get_node_dimensions(node)
        left = x
        right = x + width - 1
        top = y
        bottom = y + height - 1
        center_x = left + (width // 2)
        center_y = top + (height // 2)
        return {
            "left": left,
            "right": right,
            "top": top,
            "bottom": bottom,
            "center_x": center_x,
            "center_y": center_y,
        }

    def _get_edge_sides(
        self, start_bounds: Dict[str, int], end_bounds: Dict[str, int]
    ) -> Tuple[str, str]:
        return ports_mod.get_edge_sides(self, start_bounds, end_bounds)

    def _get_center_anchor_for_side(
        self, bounds: Dict[str, int], side: str
    ) -> Tuple[int, int]:
        return ports_mod.get_center_anchor_for_side(self, bounds, side)

    def _get_side_port_values(self, bounds: Dict[str, int], side: str) -> List[int]:
        return ports_mod.get_side_port_values(self, bounds, side)

    def _port_value_to_xy(
        self, bounds: Dict[str, int], side: str, value: int
    ) -> Tuple[int, int]:
        return ports_mod.port_value_to_xy(self, bounds, side, value)

    @staticmethod
    def _crowding_cost(value: int, used_values: List[int]) -> float:
        return ports_mod.crowding_cost(value, used_values)

    @staticmethod
    def _values_with_min_separation(
        candidates: List[int], used_values: List[int], min_sep: int
    ) -> List[int]:
        return ports_mod.values_with_min_separation(candidates, used_values, min_sep)

    @staticmethod
    def _port_pair_jog_cost(start_value: int, end_value: int) -> int:
        return ports_mod.port_pair_jog_cost(start_value, end_value)

    @staticmethod
    def _side_center_value(bounds: Dict[str, int], side: str) -> int:
        return ports_mod.side_center_value(bounds, side)

    @staticmethod
    def _nearest_candidate_to_center(candidates: List[int], center_value: int) -> int:
        return ports_mod.nearest_candidate_to_center(candidates, center_value)

    def _choose_port_pair(
        self,
        *,
        start_candidates: List[int],
        end_candidates: List[int],
        start_counter: int,
        end_counter: int,
        used_start_values: List[int],
        used_end_values: List[int],
    ) -> Tuple[int, int]:
        return ports_mod.choose_port_pair(
            self,
            start_candidates=start_candidates,
            end_candidates=end_candidates,
            start_counter=start_counter,
            end_counter=end_counter,
            used_start_values=used_start_values,
            used_end_values=used_end_values,
        )

    def _assign_monotone_port_values(
        self, counters: List[int], candidates: List[int]
    ) -> List[int]:
        return ports_mod.assign_monotone_port_values(self, counters, candidates)

    def _assign_monotone_port_indices(
        self, counters: List[int], candidates: List[int]
    ) -> List[int]:
        return ports_mod.assign_monotone_port_indices(self, counters, candidates)

    def _compute_edge_anchor_map(
        self, positions: Dict[Any, Tuple[int, int]]
    ) -> Dict[Tuple[Any, Any], Dict[str, Tuple[int, int]]]:
        return ports_mod.compute_edge_anchor_map(self, positions)

    def _get_edge_anchor_points(
        self, start: Any, end: Any, positions: Dict[Any, Tuple[int, int]]
    ) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        return ports_mod.get_edge_anchor_points(self, start, end, positions)

    def _draw_node(self, node: Any, x: int, y: int) -> None:
        label = self.options.get_node_text(self._get_display_node_text(node))
        node_width, node_height = self._get_node_dimensions(node)
        node_color = self._node_color_map.get(node)

        if not self.options.bboxes:
            for i, char in enumerate(label):
                self._paint_cell(x + i, y, char, node_color)
            return

        right_x = x + node_width - 1
        bottom_y = y + node_height - 1
        inner_width = max(0, node_width - 2 - (2 * self.options.hpad))
        label_offset = (
            max(0, (inner_width - len(label)) // 2) if self.options.uniform else 0
        )
        inner_start_x = x + 1 + self.options.hpad + label_offset
        label_y = y + 1 + self.options.vpad

        self._paint_cell(x, y, self.options.box_top_left, node_color)
        self._paint_cell(right_x, y, self.options.box_top_right, node_color)
        for col in range(x + 1, right_x):
            self._paint_cell(col, y, self.options.edge_horizontal, node_color)

        self._paint_cell(x, bottom_y, self.options.box_bottom_left, node_color)
        self._paint_cell(right_x, bottom_y, self.options.box_bottom_right, node_color)
        for col in range(x + 1, right_x):
            self._paint_cell(col, bottom_y, self.options.edge_horizontal, node_color)

        for row in range(y + 1, bottom_y):
            self._paint_cell(x, row, self.options.edge_vertical, node_color)
            self._paint_cell(right_x, row, self.options.edge_vertical, node_color)

        for i, char in enumerate(label):
            self._paint_cell(inner_start_x + i, label_y, char, node_color)

    def _should_skip_edge_draw(
        self,
        start: Any,
        end: Any,
        drawn_bidirectional_pairs: Set[frozenset[Any]],
    ) -> bool:
        return routing_mod.should_skip_edge_draw(
            self, start, end, drawn_bidirectional_pairs
        )

    def render(self, print_config: Optional[bool] = False) -> str:
        """Render the graph as ASCII art."""
        positions, width, height = self.layout_manager.calculate_layout()
        if not positions:
            return ""

        # Initialize canvas with adjusted positions
        self._init_canvas(width, height, positions)
        self._initialize_color_maps(positions)
        self._edge_anchor_map = self._compute_edge_anchor_map(positions)

        # Only try to draw edges if we have any
        if self.graph.edges():
            drawn_bidirectional_pairs: Set[frozenset[Any]] = set()
            for start, end in self.graph.edges():
                if start in positions and end in positions:
                    if self._should_skip_edge_draw(
                        start, end, drawn_bidirectional_pairs
                    ):
                        continue
                    try:
                        self._draw_edge(start, end, positions)
                    except IndexError as e:
                        # For debugging, print more info about what failed
                        pos_info = (
                            f"start_pos={positions[start]}, end_pos={positions[end]}"
                        )
                        edge_info = f"edge={start}->{end}"
                        canvas_info = f"canvas={len(self.canvas)}x{len(self.canvas[0])}"
                        raise IndexError(
                            f"Edge drawing failed: {edge_info}, {pos_info}, {canvas_info}"
                        ) from e

        # Draw nodes
        for node, (x, y) in positions.items():
            try:
                self._draw_node(node, x, y)
            except IndexError as e:
                pos_info = f"pos=({x},{y}), node={node}"
                canvas_info = f"canvas={len(self.canvas)}x{len(self.canvas[0])}"
                raise IndexError(
                    f"Node drawing failed: {pos_info}, {canvas_info}"
                ) from e

        return "\n".join(
            self._render_row(row, colors)
            for row, colors in zip(self.canvas, self._color_canvas)
        )

    def draw(self, file: Optional[TextIO] = None) -> None:
        """
        Draw the graph to a file or stdout.

        Parameters
        ----------
        file : Optional[TextIO]
            File to write to. If None, writes to stdout
        """

        is_redirected = self._is_redirected() if file is None else False

        if file is None:
            if is_redirected or self.options.use_ascii:
                # Use ASCII when redirected or explicitly requested
                old_use_ascii = self.options.use_ascii
                self.options.use_ascii = True
                try:
                    print(self.render(), file=sys.stdout)
                finally:
                    self.options.use_ascii = old_use_ascii
            else:
                # Direct to console, try Unicode
                sys.stdout = io.TextIOWrapper(
                    sys.stdout.buffer, encoding="utf-8", errors="replace"
                )
                print(self.render(), file=sys.stdout)
        else:
            print(self.render(), file=file)

    @staticmethod
    def _ansi_to_hex(ansi: str) -> Optional[str]:
        return _ansi_to_hex_impl(ansi)

    @staticmethod
    def _xterm_index_to_hex(idx: int) -> str:
        return _xterm_index_to_hex_impl(idx)

    def _normalized_canvas_rows(self) -> List[str]:
        from .rendering.output import normalized_canvas_rows

        return normalized_canvas_rows(self)

    def render_ditaa(self, wrap_plantuml: bool = False) -> str:
        from .rendering.output import render_ditaa

        return render_ditaa(self, wrap_plantuml=wrap_plantuml)

    def render_svg(
        self,
        *,
        cell_px: int = 12,
        font_family: str = "monospace",
        text_mode: str = "text",
        font_path: Optional[str] = None,
        fg_color: str = "#111111",
        bg_color: str = "#ffffff",
    ) -> str:
        from .rendering.output import render_svg

        return render_svg(
            self,
            cell_px=cell_px,
            font_family=font_family,
            text_mode=text_mode,
            font_path=font_path,
            fg_color=fg_color,
            bg_color=bg_color,
        )

    def _append_svg_glyph_paths(
        self,
        *,
        lines: List[str],
        rows: List[str],
        cell_px: int,
        font_family: str,
        font_path: Optional[str],
        fg_color: str,
    ) -> None:
        try:
            from fontTools.ttLib import TTFont  # type: ignore
            from fontTools.pens.svgPathPen import SVGPathPen  # type: ignore
            from fontTools.pens.boundsPen import BoundsPen  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "SVG path glyph mode requires fonttools. Install it and retry."
            ) from exc

        resolved_font = self._resolve_svg_font_path(
            font_family=font_family,
            font_path=font_path,
        )
        font = TTFont(resolved_font)
        glyph_set = font.getGlyphSet()
        cmap = font.getBestCmap() or {}
        units_per_em = max(1, int(font["head"].unitsPerEm))
        scale = float(cell_px) / float(units_per_em)
        glyph_cache: Dict[
            str, Optional[Tuple[str, Tuple[float, float, float, float]]]
        ] = {}

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
                        cache_item = self._glyph_outline_for_char(
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
                    tx = (
                        (x * cell_px) + ((cell_px - glyph_w_px) / 2.0) - (x_min * scale)
                    )
                    ty = (
                        (y * cell_px) + ((cell_px - glyph_h_px) / 2.0) + (y_max * scale)
                    )

                    fill = fg_color
                    if y < len(self._color_canvas) and x < len(self._color_canvas[y]):
                        ansi = self._color_canvas[y][x]
                        parsed = self._ansi_to_hex(ansi) if ansi else None
                        if parsed:
                            fill = parsed

                    lines.append(
                        f'    <path d="{html_escape(path_data)}" fill="{html_escape(fill)}" '
                        f'transform="translate({tx:.2f} {ty:.2f}) scale({scale:.6f} {-scale:.6f})" />'
                    )
            lines.append("  </g>")
        finally:
            font.close()

    @staticmethod
    def _resolve_svg_font_path(*, font_family: str, font_path: Optional[str]) -> str:
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

    @staticmethod
    def _glyph_outline_for_char(
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

    def render_html(
        self,
        *,
        fg_color: str = "#111111",
        bg_color: str = "#ffffff",
        font_family: str = "monospace",
    ) -> str:
        from .rendering.output import render_html

        return render_html(
            self,
            fg_color=fg_color,
            bg_color=bg_color,
            font_family=font_family,
        )

    def write_to_file(self, filename: str) -> None:
        """
        Write graph representation to a file.

        Parameters
        ----------
        filename : str
            Path to output file
        """

        with open(filename, "w", encoding="utf-8") as f:
            f.write(self.render())

    def _init_canvas(
        self, width: int, height: int, positions: Dict[Any, Tuple[int, int]]
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
                x + self._get_node_dimensions(node)[0]
                for node, (x, _) in positions.items()
            ),
            default=1,
        )
        max_bottom = max(
            (
                y + self._get_node_dimensions(node)[1]
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

        self.canvas = [[" " for _ in range(final_width)] for _ in range(final_height)]
        self._color_canvas = [
            [None for _ in range(final_width)] for _ in range(final_height)
        ]
        self._edge_conflict_cells = set()
        self._locked_arrow_cells = set()

    def _draw_vertical_segment(
        self,
        x: int,
        start_y: int,
        end_y: int,
        marker: Optional[str],
        color: Optional[str] = None,
    ) -> None:
        routing_mod.draw_vertical_segment(self, x, start_y, end_y, marker, color)

    def _draw_horizontal_segment(
        self,
        y: int,
        start_x: int,
        end_x: int,
        marker: Optional[str],
        color: Optional[str] = None,
    ) -> None:
        routing_mod.draw_horizontal_segment(self, y, start_x, end_x, marker, color)

    def _safe_draw(
        self, x: int, y: int, char: str, color: Optional[str] = None
    ) -> None:
        routing_mod.safe_draw(self, x, y, char, color)

    def _line_dirs_for_char(self, ch: str) -> Set[str]:
        return routing_mod.line_dirs_for_char(self, ch)

    def _glyph_for_line_dirs(self, dirs: Set[str]) -> str:
        return routing_mod.glyph_for_line_dirs(self, dirs)

    def _merge_line_cell(
        self, x: int, y: int, add_dirs: Set[str], color: Optional[str] = None
    ) -> None:
        routing_mod.merge_line_cell(self, x, y, add_dirs, color)

    def _is_terminal(
        self, positions: Dict[Any, Tuple[int, int]], node: Any, x: int, y: int
    ) -> bool:
        return routing_mod.is_terminal(self, positions, node, x, y)

    def _draw_direction(
        self,
        y: int,
        x: int,
        direction: str,
        is_terminal: bool = False,
        color: Optional[str] = None,
    ) -> None:
        routing_mod.draw_direction(self, y, x, direction, is_terminal, color)

    def _get_jog_row(
        self,
        top_center: int,
        bottom_center: int,
        top_y: int,
        bottom_y: int,
    ) -> int:
        return routing_mod.get_jog_row(self, top_center, bottom_center, top_y, bottom_y)

    def _draw_edge(
        self, start: Any, end: Any, positions: Dict[Any, Tuple[int, int]]
    ) -> None:
        routing_mod.draw_edge(self, start, end, positions)

    @classmethod
    def from_dot(cls, dot_string: str, **kwargs: Any) -> "ASCIIRenderer":
        """
        Create a renderer from a DOT format string.

        Parameters
        ----------
        dot_string : str
            Graph description in DOT format
        **kwargs
            Additional arguments passed to the constructor

        Returns
        -------
        ASCIIRenderer
            New renderer instance

        Raises
        ------
        ImportError
            If pydot is not available
        ValueError
            If DOT string doesn't contain any valid graphs

        Examples
        --------
        >>> dot = '''
        ... digraph {
        ...     A -> B
        ...     B -> C
        ... }
        ... '''
        >>> renderer = ASCIIRenderer.from_dot(dot)
        >>> print(renderer.render())
        A
        |
        B
        |
        C
        """

        from phart.io.input.dot import parse_dot_to_digraph

        G = parse_dot_to_digraph(dot_string)
        return cls(G, **kwargs)

    @classmethod
    def from_graphml(cls, graphml_file: str, **kwargs: Any) -> "ASCIIRenderer":
        """
        Create a renderer from a GraphML file.

        Parameters
        ----------
        graphml_file : str
            Path to GraphML file
        **kwargs
            Additional arguments passed to the constructor

        Returns
        -------
        ASCIIRenderer
            New renderer instance

        Raises
        ------
        ImportError
            If NetworkX graphml support is not available
        ValueError
            If file cannot be read as GraphML
        """
        from phart.io.input.graphml import parse_graphml_to_digraph

        G = parse_graphml_to_digraph(graphml_file)
        return cls(G, **kwargs)

    @classmethod
    def from_plantuml(cls, plantuml_str: str, **kwargs: Any) -> "ASCIIRenderer":
        """Create a renderer from a PlantUML text diagram.

        Supported subset:
        - Common participant/class/object declarations
        - Relationship lines using PlantUML arrows (e.g. A --> B, A <- B, A <-> B)
        - Optional edge labels using ``: label``
        """

        from phart.io.input.plantuml import parse_plantuml_to_digraph

        G = parse_plantuml_to_digraph(plantuml_str)
        return cls(G, **kwargs)


def merge_layout_options(
    base: LayoutOptions, overrides: LayoutOptions
) -> LayoutOptions:
    from dataclasses import asdict, fields

    base_dict = asdict(base)
    override_dict = asdict(overrides)
    merged_dict: dict[str, Any] = {}
    explicit_cli_fields_raw = getattr(overrides, "_explicit_cli_fields", None)
    explicit_cli_fields: set[str] = (
        set(explicit_cli_fields_raw) if explicit_cli_fields_raw is not None else set()
    )
    has_explicit_field_metadata = explicit_cli_fields_raw is not None

    # Define which fields are "rendering" vs "semantic"
    rendering_fields = {
        "use_ascii",
        "node_style",
        "node_spacing",
        "layer_spacing",
        "binary_tree_layout",
        "layout_strategy",
        "left_padding",
        "right_padding",
        "margin",
        "flow_direction",
        "bboxes",
        "hpad",
        "vpad",
        "uniform",
        "edge_anchor_mode",
        "use_labels",
        "ansi_colors",
        "allow_ansi_in_ascii",
        "edge_color_mode",
        "edge_color_rules",
        "color_nodes",
    }

    for field in fields(LayoutOptions):
        field_name = field.name
        if field_name == "instance_id":
            continue

        override_val = override_dict.get(field_name)
        base_val = base_dict.get(field_name)

        # For rendering fields: CLI (override) takes precedence if not None
        if field_name in rendering_fields:
            if has_explicit_field_metadata:
                if field_name == "node_style":
                    if field_name in explicit_cli_fields:
                        merged_dict[field_name] = override_val
                    elif "bboxes" in explicit_cli_fields and bool(
                        override_dict.get("bboxes")
                    ):
                        # When CLI explicitly enables bboxes but does not set style,
                        # preserve explicit script styles, otherwise default to minimal.
                        base_style_explicit = bool(
                            getattr(base, "_node_style_explicit", False)
                        )
                        merged_dict[field_name] = (
                            base_val if base_style_explicit else NodeStyle.MINIMAL
                        )
                    else:
                        merged_dict[field_name] = base_val
                else:
                    merged_dict[field_name] = (
                        override_val if field_name in explicit_cli_fields else base_val
                    )
            else:
                merged_dict[field_name] = (
                    override_val if override_val is not None else base_val
                )
        # For semantic fields: User (base) takes precedence if not None
        else:
            merged_dict[field_name] = base_val if base_val is not None else override_val

    # Special handling for custom_decorators - merge dicts
    if base.custom_decorators and overrides.custom_decorators:
        merged_dict["custom_decorators"] = {
            **base.custom_decorators,
            **overrides.custom_decorators,
        }
    elif base.custom_decorators:
        merged_dict["custom_decorators"] = base.custom_decorators.copy()
    elif overrides.custom_decorators:
        merged_dict["custom_decorators"] = overrides.custom_decorators.copy()

    return LayoutOptions(**merged_dict)
