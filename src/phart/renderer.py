from __future__ import annotations

import io
import os
import sys

from typing import Any, ClassVar, Dict, List, Optional, Set, TextIO, Tuple, cast

import networkx as nx  # type: ignore

from .layout import LayoutManager
from .rendering import colors as colors_mod
from .rendering import nodes as nodes_mod
from .rendering import ports as ports_mod
from .rendering import routing as routing_mod
from .rendering import svg as svg_mod
from .rendering.ansi import (
    ANSI_RESET,
    ANSI_SUBWAY_PALETTE,
    ANSI_NAMED_COLORS,
)
from .rendering.ansi import ansi_to_hex as _ansi_to_hex_impl
from .rendering.ansi import normalize_edge_attr_value as _normalize_edge_attr_value_impl
from .rendering.ansi import resolve_color_spec as _resolve_color_spec_impl
from .rendering.ansi import xterm_index_to_hex as _xterm_index_to_hex_impl

from .styles import LayoutOptions, NodeStyle
from .style_rules import evaluate_style_rule_color


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
            import ctypes
            import msvcrt

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
        text = str(value).strip()
        if len(text) >= 2 and text[0] == text[-1] and text[0] in {"'", '"'}:
            text = text[1:-1]
        return text.strip().lower()

    @staticmethod
    def _resolve_color_spec(spec: Any) -> Optional[str]:
        """Resolve a color spec into an ANSI escape sequence."""
        token = str(spec).strip()
        if not token:
            return None

        lowered = token.lower()
        if lowered in ANSI_NAMED_COLORS:
            return ANSI_NAMED_COLORS[lowered]

        if token.startswith("\x1b[") and token.endswith("m"):
            return token

        if lowered.startswith("color") and lowered[5:].isdigit():
            lowered = lowered[5:]

        if lowered.isdigit():
            color_index = int(lowered)
            if 0 <= color_index <= 255:
                return f"\x1b[38;5;{color_index}m"

        if lowered.startswith("#") and len(lowered) == 7:
            try:
                r = int(lowered[1:3], 16)
                g = int(lowered[3:5], 16)
                b = int(lowered[5:7], 16)
                return f"\x1b[38;2;{r};{g};{b}m"
            except ValueError:
                return None

        return None

    def _resolve_attr_edge_color(
        self: ASCIIRenderer,
        edge: Tuple[Any, Any],
        idx: int,
        node_palette_map: Optional[Dict[Any, str]] = None,
    ) -> Optional[str]:
        return colors_mod.resolve_attr_edge_color(self, edge, idx, node_palette_map)

    def _normalized_edge_attrs(self, start: Any, end: Any) -> Dict[str, str]:
        edge_data = self.graph.get_edge_data(start, end) or {}
        return {
            str(key).strip().lower(): self._normalize_edge_attr_value(value)
            for key, value in edge_data.items()
        }

    def _resolve_edge_style_color_spec(self, start: Any, end: Any) -> Optional[str]:
        edge_data = self.graph.get_edge_data(start, end) or {}
        context = {
            "self": edge_data,
            "edge": edge_data,
            "u": self.graph.nodes.get(start, {}),
            "v": self.graph.nodes.get(end, {}),
        }
        return evaluate_style_rule_color(
            getattr(self.options, "_compiled_style_rules", []),
            "edge",
            context,
        )

    def _attr_rules_match_for_reverse_edge(self, start: Any, end: Any) -> bool:
        """Return True when attr-color rule attributes agree in both directions."""
        if self.options.edge_color_mode != "attr":
            return True
        has_style_rules = bool(getattr(self.options, "_compiled_style_rules", []))
        if not self.options.edge_color_rules and not has_style_rules:
            return True
        if has_style_rules:
            return self._resolve_edge_style_color_spec(
                start, end
            ) == self._resolve_edge_style_color_spec(end, start)

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
        if self.options.bidirectional_mode == "separate":
            return False
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
        if self.options.bidirectional_mode == "separate":
            return True
        return not self._attr_rules_match_for_reverse_edge(start, end)

    def _initialize_color_maps(self, positions: Dict[Any, Tuple[int, int]]) -> None:
        return colors_mod.initialize_color_maps(self, positions)

    def mermaid_out(self: ASCIIRenderer) -> str:
        str_ = "flowchart TD"
        try:
            # maybe do something where we find the shortest and longest edges
            # and depending on the disparity, maybe we make them longer here. Or, we  couldl expose a flag
            for u, v in self.graph.edges():
                ulabel = vlabel = ""
                if self.options.use_labels:
                    if "label" in self.graph.nodes[u]:
                        ulabel = self.graph.nodes[u]["label"]
                    if "label" in self.graph.nodes[v]:
                        vlabel = self.graph.nodes[v]["label"]
                if ulabel == "":
                    ulabel = u
                if vlabel == "":
                    vlabel = v
                unostr = ulabel.replace(" ", "")
                vnostr = vlabel.replace(" ", "")
                unostr = ulabel.replace('"', "")
                vnostr = vlabel.replace('"', "")
                str_ += f"\n    {unostr}[{ulabel}] ---> {vnostr}[{vlabel}]"
        except nx.NetworkXError as e:
            print(f"An error occurred: {e}")

        finally:
            pass
        return str(str_)

    def _paint_cell(
        self, x: int, y: int, char: str, color: Optional[str] = None
    ) -> None:
        colors_mod.paint_cell(self, x, y, char, color)

    def _is_arrow_glyph(self, char: str) -> bool:
        return char in {
            self.options.edge_arrow_up,
            self.options.edge_arrow_down,
            self.options.edge_arrow_l,
            self.options.edge_arrow_r,
        }

    def _merge_edge_cell_color(self, x: int, y: int, color: Optional[str]) -> None:
        colors_mod.merge_edge_cell_color(self, x, y, color)

    def _paint_edge_cell(
        self, x: int, y: int, char: str, color: Optional[str] = None
    ) -> None:
        colors_mod.paint_edge_cell(self, x, y, char, color)

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
        return nodes_mod.normalize_label_value(label)

    def _get_display_node_text(self, node: Any) -> str:
        """Resolve display text for a node key."""
        return nodes_mod.get_display_node_text(self, node)

    def _get_widest_node_text_width(self) -> Optional[int]:
        return nodes_mod.get_widest_node_text_width(self)

    def _get_node_dimensions(self, node: Any) -> Tuple[int, int]:
        return nodes_mod.get_node_dimensions(self, node)

    def _get_node_bounds(
        self, node: Any, positions: Dict[Any, Tuple[int, int]]
    ) -> Dict[str, int]:
        return nodes_mod.get_node_bounds(self, node, positions)

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
    ) -> Dict[Tuple[Any, Any], Dict[str, Any]]:
        return ports_mod.compute_edge_anchor_map(self, positions)

    def _get_edge_anchor_points(
        self, start: Any, end: Any, positions: Dict[Any, Tuple[int, int]]
    ) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        return ports_mod.get_edge_anchor_points(self, start, end, positions)

    def _should_skip_edge_draw(
        self,
        start: Any,
        end: Any,
        drawn_bidirectional_pairs: Set[frozenset[Any]],
    ) -> bool:
        return routing_mod.should_skip_edge_draw(
            self, start, end, drawn_bidirectional_pairs
        )

    def _draw_node(self, node: Any, x: int, y: int) -> None:
        nodes_mod.draw_node(self, node, x, y)

    def get_edge_route_length(self, start: Any, end: Any) -> int:
        """Return the orthogonal route length for an edge."""
        if not self.graph.has_edge(start, end):
            raise KeyError(f"Edge not found: {start!r}->{end!r}")

        positions, _width, _height = self.layout_manager.calculate_layout()
        if start not in positions or end not in positions:
            raise KeyError(
                f"Node position not found: {start if start not in positions else end}"
            )

        self._edge_anchor_map = self._compute_edge_anchor_map(positions)
        start_anchor, end_anchor = self._get_edge_anchor_points(start, end, positions)
        return abs(start_anchor[0] - end_anchor[0]) + abs(
            start_anchor[1] - end_anchor[1]
        )

    def render(
        self, print_config: Optional[bool] = False, *, markdown_safe: bool = False
    ) -> str:
        """Render the graph as ASCII art."""
        positions, width, height = self.layout_manager.calculate_layout()
        if not positions:
            return ""

        if not print_config:
            pass

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

        text = "\n".join(
            self._render_row(row, colors)
            for row, colors in zip(self.canvas, self._color_canvas, strict=True)
        )
        padding_char = self.options.resolve_padding_char(markdown_safe=markdown_safe)
        if padding_char != " ":
            from .rendering.output import apply_padding_char

            text = apply_padding_char(text, padding_char=padding_char)
        return text

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
        from .rendering.output import render_svg as render_svg_impl

        return render_svg_impl(
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
        svg_mod.append_svg_glyph_paths(
            #    renderer=self,
            lines=lines,
            rows=rows,
            cell_px=cell_px,
            font_family=font_family,
            font_path=font_path,
            fg_color=fg_color,
        )

    @staticmethod
    def _resolve_svg_font_path(*, font_family: str, font_path: Optional[str]) -> str:
        return svg_mod.resolve_svg_font_path(
            font_family=font_family, font_path=font_path
        )

    @staticmethod
    def _glyph_outline_for_char(
        *,
        ch: str,
        cmap: Dict[int, str],
        glyph_set: Any,
        svg_path_pen_cls: Any,
        bounds_pen_cls: Any,
    ) -> Optional[Tuple[str, Tuple[float, float, float, float]]]:
        return svg_mod.glyph_outline_for_char(
            ch=ch,
            cmap=cmap,
            glyph_set=glyph_set,
            svg_path_pen_cls=svg_path_pen_cls,
            bounds_pen_cls=bounds_pen_cls,
        )

    def render_html(
        self,
        *,
        fg_color: str = "#111111",
        bg_color: str = "#ffffff",
        font_family: str = "monospace",
    ) -> str:
        from .rendering.output import render_html as render_html_impl

        return render_html_impl(
            self,
            fg_color=fg_color,
            bg_color=bg_color,
            font_family=font_family,
        )

    def render_latex_markdown(
        self,
        *,
        fg_color: str = "#111111",
    ) -> str:
        from .rendering.output import (
            render_latex_markdown as render_latex_markdown_impl,
        )

        return render_latex_markdown_impl(
            self,
            fg_color=fg_color,
        )

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
        max_edge_label_width = 0
        for _start, _end, edge_data in self.graph.edges(data=True):
            label = edge_data.get("label") if isinstance(edge_data, dict) else None
            if label is None:
                continue
            normalized = self._normalize_label_value(label)
            if not normalized:
                continue
            max_edge_label_width = max(
                max_edge_label_width, self.options.get_text_display_width(normalized)
            )
        if max_edge_label_width > 0:
            min_width += max_edge_label_width + 2

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
        from phart.io.input.dot import parse_dot_to_digraph

        G = parse_dot_to_digraph(dot_string)
        return cls(G, **kwargs)

    @classmethod
    def from_graphml(cls, graphml_file: str, **kwargs: Any) -> "ASCIIRenderer":
        from phart.io.input.graphml import parse_graphml_to_digraph

        G = parse_graphml_to_digraph(graphml_file)
        return cls(G, **kwargs)

    @classmethod
    def from_plantuml(cls, plantuml_str: str, **kwargs: Any) -> "ASCIIRenderer":

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
        "node_order_mode",
        "node_order_attr",
        "node_order_reverse",
        "left_padding",
        "right_padding",
        "margin",
        "flow_direction",
        "bboxes",
        "hpad",
        "vpad",
        "uniform",
        "edge_anchor_mode",
        "shared_ports_mode",
        "bidirectional_mode",
        "use_labels",
        "node_label_lines",
        "node_label_sep",
        "node_label_max_lines",
        "bbox_multiline_labels",
        "ansi_colors",
        "allow_ansi_in_ascii",
        "edge_color_mode",
        "edge_color_rules",
        "style_rules",
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
