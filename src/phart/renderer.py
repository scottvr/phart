from __future__ import annotations
from typing import Any, Dict, List, Optional, TextIO, Tuple, ClassVar, Set
import re
import warnings

import networkx as nx  # type: ignore

from .layout import LayoutManager
from .styles import LayoutOptions, NodeStyle

import sys
import io

ANSI_RESET = "\x1b[0m"
ANSI_SUBWAY_PALETTE: Tuple[str, ...] = (
    "\x1b[38;5;45m",  # cyan
    "\x1b[38;5;214m",  # orange
    "\x1b[38;5;118m",  # green
    "\x1b[38;5;199m",  # magenta
    "\x1b[38;5;39m",  # blue
    "\x1b[38;5;226m",  # yellow
    "\x1b[38;5;160m",  # red
    "\x1b[38;5;81m",  # aqua
)
ANSI_NAMED_COLORS: Dict[str, str] = {
    "black": "\x1b[30m",
    "red": "\x1b[31m",
    "green": "\x1b[32m",
    "yellow": "\x1b[33m",
    "blue": "\x1b[34m",
    "magenta": "\x1b[35m",
    "cyan": "\x1b[36m",
    "white": "\x1b[37m",
    "bright_black": "\x1b[90m",
    "bright_red": "\x1b[91m",
    "bright_green": "\x1b[92m",
    "bright_yellow": "\x1b[93m",
    "bright_blue": "\x1b[94m",
    "bright_magenta": "\x1b[95m",
    "bright_cyan": "\x1b[96m",
    "bright_white": "\x1b[97m",
    # Palette aliases used by existing subway colors.
    "orange": "\x1b[38;5;214m",
    "aqua": "\x1b[38;5;81m",
}


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
        """Choose source/target box sides for an edge based on relative geometry."""
        vertical_overlap = max(start_bounds["top"], end_bounds["top"]) <= min(
            start_bounds["bottom"], end_bounds["bottom"]
        )
        if (
            vertical_overlap and start_bounds["center_x"] != end_bounds["center_x"]
        ) or (start_bounds["center_y"] == end_bounds["center_y"]):
            if start_bounds["center_x"] <= end_bounds["center_x"]:
                return "right", "left"
            return "left", "right"
        if start_bounds["center_y"] < end_bounds["center_y"]:
            return "bottom", "top"
        return "top", "bottom"

    def _get_center_anchor_for_side(
        self, bounds: Dict[str, int], side: str
    ) -> Tuple[int, int]:
        if side == "top":
            return bounds["center_x"], bounds["top"]
        if side == "bottom":
            return bounds["center_x"], bounds["bottom"]
        if side == "left":
            return bounds["left"], bounds["center_y"]
        return bounds["right"], bounds["center_y"]

    def _get_side_port_values(self, bounds: Dict[str, int], side: str) -> List[int]:
        """Get candidate port coordinates along a side (axis-only values)."""
        if side in ("top", "bottom"):
            if bounds["right"] - bounds["left"] > 1:
                return list(range(bounds["left"] + 1, bounds["right"]))
            return [bounds["center_x"]]
        if bounds["bottom"] - bounds["top"] > 1:
            return list(range(bounds["top"] + 1, bounds["bottom"]))
        return [bounds["center_y"]]

    def _port_value_to_xy(
        self, bounds: Dict[str, int], side: str, value: int
    ) -> Tuple[int, int]:
        if side == "top":
            return value, bounds["top"]
        if side == "bottom":
            return value, bounds["bottom"]
        if side == "left":
            return bounds["left"], value
        return bounds["right"], value

    @staticmethod
    def _crowding_cost(value: int, used_values: List[int]) -> float:
        """Soft penalty for placing a port too close to existing ports."""
        if not used_values:
            return 0.0
        return sum(1.0 / (abs(value - used) + 1.0) for used in used_values)

    @staticmethod
    def _values_with_min_separation(
        candidates: List[int], used_values: List[int], min_sep: int
    ) -> List[int]:
        """Filter candidate values by minimum separation from existing values."""
        if not used_values:
            return list(candidates)

        filtered = [
            candidate
            for candidate in candidates
            if all(abs(candidate - used) >= min_sep for used in used_values)
        ]
        return filtered if filtered else list(candidates)

    @staticmethod
    def _port_pair_jog_cost(start_value: int, end_value: int) -> int:
        """Orthogonal jog distance in the routing axis for a port pair."""
        return abs(start_value - end_value)

    @staticmethod
    def _side_center_value(bounds: Dict[str, int], side: str) -> int:
        """Get the center axis coordinate for a given node side."""
        if side in ("top", "bottom"):
            return bounds["center_x"]
        return bounds["center_y"]

    @staticmethod
    def _nearest_candidate_to_center(candidates: List[int], center_value: int) -> int:
        """Pick candidate nearest to local side center (deterministic ties)."""
        return min(candidates, key=lambda value: (abs(value - center_value), value))

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
        """Choose best (start,end) port pair using spacing + route-awareness."""
        best_pair: Optional[Tuple[int, int]] = None
        best_key: Optional[Tuple[float, int, int, int, int]] = None

        for start_value in start_candidates:
            for end_value in end_candidates:
                start_cost = abs(start_value - start_counter)
                end_cost = abs(end_value - end_counter)
                jog_cost = self._port_pair_jog_cost(start_value, end_value)

                # Preserve spread unless route simplification is compelling.
                crowding = self._crowding_cost(
                    start_value, used_start_values
                ) + self._crowding_cost(end_value, used_end_values)

                straight_bonus = 3.0 if jog_cost == 0 else 0.0
                score = (
                    float(start_cost)
                    + float(end_cost)
                    + (0.75 * float(jog_cost))
                    + (2.0 * crowding)
                    - straight_bonus
                )
                pair_key = (
                    score,
                    start_cost + end_cost,
                    jog_cost,
                    start_value,
                    end_value,
                )
                if best_key is None or pair_key < best_key:
                    best_key = pair_key
                    best_pair = (start_value, end_value)

        if best_pair is None:
            return start_counter, end_counter
        return best_pair

    def _assign_monotone_port_values(
        self, counters: List[int], candidates: List[int]
    ) -> List[int]:
        """Assign candidate ports monotonically to ordered counters.

        Preserves left-to-right/top-to-bottom ordering to minimize surprising
        edge crossings on a shared node face.
        """
        if not counters:
            return []
        if not candidates:
            return list(counters)

        ordered_candidates = sorted(set(candidates))
        ordered_counters = list(counters)
        n = len(ordered_counters)
        m = len(ordered_candidates)

        if n == 1:
            center = ordered_counters[0]
            return [self._nearest_candidate_to_center(ordered_candidates, center)]

        # If there are fewer candidate slots than edges, keep monotonicity by
        # reusing slots in order.
        if m < n:
            max_index = m - 1
            return [
                ordered_candidates[round((i * max_index) / max(n - 1, 1))]
                for i in range(n)
            ]

        # Dynamic programming: choose strictly increasing candidate indices
        # that minimize total absolute deviation from desired counters.
        inf = float("inf")
        dp: List[List[float]] = [[inf for _ in range(m)] for _ in range(n)]
        prev: List[List[int]] = [[-1 for _ in range(m)] for _ in range(n)]

        for j in range(m):
            dp[0][j] = abs(ordered_counters[0] - ordered_candidates[j])

        for i in range(1, n):
            for j in range(i, m):
                local_cost = abs(ordered_counters[i] - ordered_candidates[j])
                best_prev_idx = -1
                best_prev_cost = inf
                for k in range(i - 1, j):
                    cand_cost = dp[i - 1][k]
                    if cand_cost < best_prev_cost:
                        best_prev_cost = cand_cost
                        best_prev_idx = k
                dp[i][j] = best_prev_cost + local_cost
                prev[i][j] = best_prev_idx

        best_last_idx = min(
            range(n - 1, m),
            key=lambda j: (dp[n - 1][j], j),
        )

        chosen_indices = [0 for _ in range(n)]
        chosen_indices[n - 1] = best_last_idx
        for i in range(n - 1, 0, -1):
            chosen_indices[i - 1] = prev[i][chosen_indices[i]]

        return [ordered_candidates[idx] for idx in chosen_indices]

    def _assign_monotone_port_indices(
        self, counters: List[int], candidates: List[int]
    ) -> List[int]:
        """Assign monotonically ordered candidate indices to ordered counters."""
        if not counters:
            return []
        ordered_candidates = sorted(set(candidates))
        if not ordered_candidates:
            return [0 for _ in counters]

        n = len(counters)
        m = len(ordered_candidates)
        if n == 1:
            target = counters[0]
            best_idx = min(
                range(m), key=lambda idx: (abs(ordered_candidates[idx] - target), idx)
            )
            return [best_idx]

        if m < n:
            max_index = m - 1
            return [round((i * max_index) / max(n - 1, 1)) for i in range(n)]

        # Dynamic programming: strictly increasing indices minimizing deviation.
        inf = float("inf")
        dp: List[List[float]] = [[inf for _ in range(m)] for _ in range(n)]
        prev: List[List[int]] = [[-1 for _ in range(m)] for _ in range(n)]

        for j in range(m):
            dp[0][j] = abs(counters[0] - ordered_candidates[j])

        for i in range(1, n):
            for j in range(i, m):
                local_cost = abs(counters[i] - ordered_candidates[j])
                best_prev_idx = -1
                best_prev_cost = inf
                for k in range(i - 1, j):
                    cand_cost = dp[i - 1][k]
                    if cand_cost < best_prev_cost:
                        best_prev_cost = cand_cost
                        best_prev_idx = k
                dp[i][j] = best_prev_cost + local_cost
                prev[i][j] = best_prev_idx

        best_last_idx = min(
            range(n - 1, m),
            key=lambda j: (dp[n - 1][j], j),
        )
        chosen = [0 for _ in range(n)]
        chosen[n - 1] = best_last_idx
        for i in range(n - 1, 0, -1):
            chosen[i - 1] = prev[i][chosen[i]]
        return chosen

    def _compute_edge_anchor_map(
        self, positions: Dict[Any, Tuple[int, int]]
    ) -> Dict[Tuple[Any, Any], Dict[str, Tuple[int, int]]]:
        """Precompute deterministic per-edge anchors for edges that use ports."""
        if not self.options.bboxes:
            return {}

        edge_specs: List[
            Tuple[
                Tuple[Any, Any],
                Any,
                str,
                int,
                List[int],
                Any,
                str,
                int,
                List[int],
                int,
            ]
        ] = []

        for start, end in sorted(
            self.graph.edges(), key=lambda edge: (str(edge[0]), str(edge[1]))
        ):
            if start not in positions or end not in positions:
                continue
            if not self._should_use_ports_for_edge(start, end):
                continue

            start_bounds = self._get_node_bounds(start, positions)
            end_bounds = self._get_node_bounds(end, positions)
            start_side, end_side = self._get_edge_sides(start_bounds, end_bounds)

            start_counter = (
                end_bounds["center_x"]
                if start_side in ("top", "bottom")
                else end_bounds["center_y"]
            )
            end_counter = (
                start_bounds["center_x"]
                if end_side in ("top", "bottom")
                else start_bounds["center_y"]
            )
            start_candidates = self._get_side_port_values(start_bounds, start_side)
            end_candidates = self._get_side_port_values(end_bounds, end_side)
            if not start_candidates:
                start_candidates = [start_counter]
            if not end_candidates:
                end_candidates = [end_counter]

            edge_specs.append(
                (
                    (start, end),
                    start,
                    start_side,
                    start_counter,
                    start_candidates,
                    end,
                    end_side,
                    end_counter,
                    end_candidates,
                    abs(start_counter - end_counter),
                )
            )

        edge_anchor_map: Dict[Tuple[Any, Any], Dict[str, Tuple[int, int]]] = {}
        used_by_side: Dict[Tuple[Any, str], List[int]] = {}
        min_port_separation = 1
        wiggle_radius = 1
        face_candidate_pools: Dict[Tuple[Tuple[Any, Any], str], List[int]] = {}
        face_requirements: Dict[
            Tuple[Any, str], List[Tuple[Tuple[Any, Any], str, int, str]]
        ] = {}
        for (
            edge_key,
            start_node,
            start_side,
            start_counter,
            _start_candidates_unused,
            end_node,
            end_side,
            end_counter,
            _end_candidates_unused,
            _axis_delta,
        ) in edge_specs:
            face_requirements.setdefault((start_node, start_side), []).append(
                (edge_key, "start", start_counter, str(end_node))
            )
            face_requirements.setdefault((end_node, end_side), []).append(
                (edge_key, "end", end_counter, str(start_node))
            )

        for (node, side), items in face_requirements.items():
            node_bounds = self._get_node_bounds(node, positions)
            candidates = sorted(set(self._get_side_port_values(node_bounds, side)))
            if not candidates:
                candidates = [self._side_center_value(node_bounds, side)]
            max_idx = len(candidates) - 1

            sorted_items = sorted(items, key=lambda item: (item[2], item[3]))
            if len(sorted_items) == 1:
                center = self._side_center_value(node_bounds, side)
                center_idx = min(
                    range(len(candidates)),
                    key=lambda idx: (abs(candidates[idx] - center), idx),
                )
                low_idx = max(0, center_idx - wiggle_radius)
                high_idx = min(max_idx, center_idx + wiggle_radius)
                edge_key, role, _counter, _peer = sorted_items[0]
                face_candidate_pools[(edge_key, role)] = candidates[
                    low_idx : high_idx + 1
                ]
            else:
                counters = [item[2] for item in sorted_items]
                base_indices = self._assign_monotone_port_indices(counters, candidates)
                n = len(base_indices)
                for idx, (edge_key, role, _counter, _peer) in enumerate(sorted_items):
                    base_idx = base_indices[idx]
                    left_limit = (
                        (base_indices[idx - 1] + base_idx + 1) // 2 if idx > 0 else 0
                    )
                    right_limit = (
                        (base_idx + base_indices[idx + 1] - 1) // 2
                        if idx < n - 1
                        else max_idx
                    )
                    if left_limit > right_limit:
                        left_limit = right_limit = min(max(base_idx, 0), max_idx)
                    low_idx = max(left_limit, base_idx - wiggle_radius)
                    high_idx = min(right_limit, base_idx + wiggle_radius)
                    if low_idx > high_idx:
                        low_idx = high_idx = min(max(base_idx, left_limit), right_limit)
                    face_candidate_pools[(edge_key, role)] = candidates[
                        low_idx : high_idx + 1
                    ]

        edge_specs_sorted = sorted(
            edge_specs,
            key=lambda spec: (
                spec[9],
                str(spec[1]),
                spec[2],
                str(spec[5]),
                spec[6],
                str(spec[0][0]),
                str(spec[0][1]),
            ),
        )

        for (
            edge_key,
            start_node,
            start_side,
            start_counter,
            start_candidates,
            end_node,
            end_side,
            end_counter,
            end_candidates,
            _axis_delta,
        ) in edge_specs_sorted:
            start_key = (start_node, start_side)
            end_key = (end_node, end_side)
            used_start_values = used_by_side.get(start_key, [])
            used_end_values = used_by_side.get(end_key, [])

            start_bounds = self._get_node_bounds(start_node, positions)
            end_bounds = self._get_node_bounds(end_node, positions)
            start_pool = face_candidate_pools.get((edge_key, "start"), start_candidates)
            end_pool = face_candidate_pools.get((edge_key, "end"), end_candidates)

            start_pool = self._values_with_min_separation(
                start_pool, used_start_values, min_port_separation
            )
            end_pool = self._values_with_min_separation(
                end_pool, used_end_values, min_port_separation
            )

            start_value, end_value = self._choose_port_pair(
                start_candidates=start_pool,
                end_candidates=end_pool,
                start_counter=start_counter,
                end_counter=end_counter,
                used_start_values=used_start_values,
                used_end_values=used_end_values,
            )

            used_by_side.setdefault(start_key, []).append(start_value)
            used_by_side.setdefault(end_key, []).append(end_value)

            edge_anchor_map.setdefault(edge_key, {})["start"] = self._port_value_to_xy(
                start_bounds, start_side, start_value
            )
            edge_anchor_map.setdefault(edge_key, {})["end"] = self._port_value_to_xy(
                end_bounds, end_side, end_value
            )

        return edge_anchor_map

    def _get_edge_anchor_points(
        self, start: Any, end: Any, positions: Dict[Any, Tuple[int, int]]
    ) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        start_bounds = self._get_node_bounds(start, positions)
        end_bounds = self._get_node_bounds(end, positions)
        start_side, end_side = self._get_edge_sides(start_bounds, end_bounds)

        horizontal_sides = (start_side, end_side) in {
            ("left", "right"),
            ("right", "left"),
        }
        overlap_top = max(start_bounds["top"], end_bounds["top"])
        overlap_bottom = min(start_bounds["bottom"], end_bounds["bottom"])
        has_vertical_overlap = overlap_top <= overlap_bottom

        def _clamp_to_overlap(y_val: int) -> int:
            return min(max(y_val, overlap_top), overlap_bottom)

        if self._should_use_ports_for_edge(start, end):
            cached = self._edge_anchor_map.get((start, end), {})
            start_anchor = cached.get("start")
            end_anchor = cached.get("end")
            if start_anchor is not None and end_anchor is not None:
                if (
                    horizontal_sides
                    and has_vertical_overlap
                    and start_anchor[1] != end_anchor[1]
                ):
                    target_y = _clamp_to_overlap(start_anchor[1])
                    start_anchor = (start_anchor[0], target_y)
                    end_anchor = (end_anchor[0], target_y)
                return start_anchor, end_anchor

        start_anchor = self._get_center_anchor_for_side(start_bounds, start_side)
        end_anchor = self._get_center_anchor_for_side(end_bounds, end_side)
        if horizontal_sides and has_vertical_overlap:
            target_y = (overlap_top + overlap_bottom) // 2
            start_anchor = (start_anchor[0], target_y)
            end_anchor = (end_anchor[0], target_y)
        return (
            start_anchor,
            end_anchor,
        )

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
        """Skip second pass when a reciprocal edge can share one route."""
        if not self._is_bidirectional_edge(start, end):
            return False
        if (end, start) not in self.graph.edges():
            return False

        # Only dedupe when both directed edges resolve to the same color;
        # otherwise keep separate draws so color semantics remain visible.
        if self._edge_color_map.get((start, end)) != self._edge_color_map.get(
            (end, start)
        ):
            return False

        pair_key = frozenset((start, end))
        if pair_key in drawn_bidirectional_pairs:
            return True

        drawn_bidirectional_pairs.add(pair_key)
        return False

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
        for y in range(start_y + 1, end_y):
            self._paint_edge_cell(x, y, self.options.edge_vertical, color)
        if marker is not None:
            mid_y = (start_y + end_y) // 2
            self._paint_edge_cell(x, mid_y, marker, color)
        return None

    def _draw_horizontal_segment(
        self,
        y: int,
        start_x: int,
        end_x: int,
        marker: Optional[str],
        color: Optional[str] = None,
    ) -> None:
        for x in range(start_x + 1, end_x):
            self._paint_edge_cell(x, y, self.options.edge_horizontal, color)
        if marker is not None:
            mid_x = (start_x + end_x) // 2
            self._paint_edge_cell(mid_x, y, marker, color)
        return None

    def _safe_draw(
        self, x: int, y: int, char: str, color: Optional[str] = None
    ) -> None:
        try:
            self._paint_edge_cell(x, y, char, color)
        except IndexError:
            raise IndexError(f"Drawing exceeded canvas bounds at ({x}, {y})")
        return None

    def _line_dirs_for_char(self, ch: str) -> Set[str]:
        """Map existing glyphs to line connection directions."""
        if ch in (
            self.options.edge_vertical,
            self.options.edge_arrow_up,
            self.options.edge_arrow_down,
        ):
            return {"up", "down"}
        if ch in (
            self.options.edge_horizontal,
            self.options.edge_arrow_l,
            self.options.edge_arrow_r,
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

    def _glyph_for_line_dirs(self, dirs: Set[str]) -> str:
        """Choose ASCII/Unicode line-art glyph for a connection set."""
        if not dirs:
            return " "

        if self.options.use_ascii:
            if ("left" in dirs or "right" in dirs) and ("up" in dirs or "down" in dirs):
                return "+"
            if "left" in dirs or "right" in dirs:
                return "-"
            return "|"

        key = frozenset(dirs)
        unicode_glyphs = {
            frozenset({"up", "down"}): self.options.edge_vertical,
            frozenset({"left", "right"}): self.options.edge_horizontal,
            frozenset({"right", "down"}): self.options.edge_corner_ul,
            frozenset({"left", "down"}): self.options.edge_corner_ur,
            frozenset({"right", "up"}): self.options.edge_corner_ll,
            frozenset({"left", "up"}): self.options.edge_corner_lr,
            frozenset({"left", "right", "down"}): self.options.edge_tee_down,
            frozenset({"left", "right", "up"}): self.options.edge_tee_up,
            frozenset({"up", "down", "right"}): self.options.edge_tee_right,
            frozenset({"up", "down", "left"}): self.options.edge_tee_left,
            frozenset({"up", "down", "left", "right"}): self.options.edge_cross,
        }

        if key in unicode_glyphs:
            return unicode_glyphs[key]
        if "left" in dirs or "right" in dirs:
            return self.options.edge_horizontal
        return self.options.edge_vertical

    def _merge_line_cell(
        self, x: int, y: int, add_dirs: Set[str], color: Optional[str] = None
    ) -> None:
        current = self.canvas[y][x]
        merged_dirs = self._line_dirs_for_char(current) | add_dirs
        self._paint_edge_cell(x, y, self._glyph_for_line_dirs(merged_dirs), color)

    def _is_terminal(
        self, positions: Dict[Any, Tuple[int, int]], node: Any, x: int, y: int
    ) -> bool:
        """
        Check if a position represents a node connection point.

        A terminal is the point where an edge connects to a node, typically the
        node's center point on its boundary.
        """
        if node not in positions:
            return False
        bounds = self._get_node_bounds(node, positions)
        return y == bounds["center_y"] and x in {
            bounds["left"],
            bounds["right"],
            bounds["center_x"],
        }

    def _draw_direction(
        self,
        y: int,
        x: int,
        direction: str,
        is_terminal: bool = False,
        color: Optional[str] = None,
    ) -> None:
        """
        Draw a directional indicator, respecting terminal points.

        Terminal points always show direction as they represent actual node connections.
        Non-terminal points preserve existing directional indicators to maintain path clarity.
        """
        if is_terminal:
            # Always show direction at node connection points
            self._paint_edge_cell(x, y, direction, color)
        elif self.canvas[y][x] not in (
            self.options.edge_arrow_up,
            self.options.edge_arrow_down,
        ):
            # Only draw direction on non-terminals if there isn't already a direction
            self._paint_edge_cell(x, y, direction, color)

    def _get_jog_row(
        self,
        top_center: int,
        bottom_center: int,
        top_y: int,
        bottom_y: int,
    ) -> int:
        """Choose a jog row for a parent→child edge that doesn't conflict with
        content already on the canvas.

        Scans downward from top_y+1 and returns the first row where the full
        horizontal span [min_x, max_x] is clear, treating an existing vertical
        bar at either endpoint as acceptable (it will become a corner).

        Requires at least 2 rows below jog_y before bottom_y (one vertical
        segment row + one arrow row), so the latest usable row is bottom_y - 2.
        Falls back to that row if no clean row is found.
        """
        min_x = min(top_center, bottom_center)
        max_x = max(top_center, bottom_center)
        latest_jog = bottom_y - 2
        if latest_jog < top_y + 1:
            return top_y + 1

        for jog_y in range(top_y + 1, latest_jog + 1):
            conflict = False
            for x in range(min_x, max_x + 1):
                cell = self.canvas[jog_y][x]
                if cell == " ":
                    continue
                # A vertical bar at one of our own columns is fine — we'll place
                # a corner there.
                if cell == self.options.edge_vertical and x in (
                    top_center,
                    bottom_center,
                ):
                    continue
                conflict = True
                break
            if not conflict:
                return jog_y

        return latest_jog

    def _draw_edge(
        self, start: Any, end: Any, positions: Dict[Any, Tuple[int, int]]
    ) -> None:
        """Draw an edge between two nodes on the canvas."""
        if start not in positions or end not in positions:
            raise KeyError(
                f"Node position not found: {start if start not in positions else end}"
            )

        start_anchor, end_anchor = self._get_edge_anchor_points(start, end, positions)
        start_x, start_y = start_anchor
        end_x, end_y = end_anchor
        edge_color = self._edge_color_map.get((start, end))

        # Check if this is a bidirectional edge (attribute-aware in attr color mode).
        is_bidirectional = self._is_bidirectional_edge(start, end)

        try:
            # Case 1: Same level horizontal connection
            if start_y == end_y:
                y = start_y
                min_x = min(start_x, end_x) + 1
                max_x = max(start_x, end_x) - 1

                for x in range(min_x, max_x + 1):
                    self._merge_line_cell(x, y, {"left", "right"}, edge_color)

                if is_bidirectional:
                    if min_x <= max_x:
                        self._paint_edge_cell(
                            min_x,
                            y,
                            self.options.get_arrow_for_direction("left"),
                            edge_color,
                        )
                        self._paint_edge_cell(
                            max_x,
                            y,
                            self.options.get_arrow_for_direction("right"),
                            edge_color,
                        )
                elif min_x <= max_x:
                    if start_x < end_x:
                        self._paint_edge_cell(
                            max_x,
                            y,
                            self.options.get_arrow_for_direction("right"),
                            edge_color,
                        )
                    else:
                        self._paint_edge_cell(
                            min_x,
                            y,
                            self.options.get_arrow_for_direction("left"),
                            edge_color,
                        )

            # Case 2: Top to bottom (or bottom to top) connection
            else:
                top_anchor = start_anchor if start_y < end_y else end_anchor
                bottom_anchor = end_anchor if start_y < end_y else start_anchor

                top_center = top_anchor[0]
                bottom_center = bottom_anchor[0]
                top_y = top_anchor[1]
                bottom_y = bottom_anchor[1]

                # --- Jog row selection ---
                #
                # Each edge gets its own horizontal routing row chosen to avoid
                # conflicts with lines already on the canvas.  Straight-down
                # edges always use top_y+1 since they need no horizontal span.
                #
                #   top_y      Parent          <- node row
                #   top_y+1    |  (or +--+)    <- vertical stub / jog row
                #   ...        |
                #   jog_y      +-------+       <- horizontal jog (chosen dynamically)
                #   jog_y+1    |               <- vertical drop begins
                #   ...        |
                #   bottom_y-1 v               <- arrow just above child
                #   bottom_y   Child           <- node row

                if bottom_y <= top_y + 1:
                    return

                if top_center == bottom_center:
                    jog_y = top_y + 1
                else:
                    jog_y = self._get_jog_row(
                        top_center, bottom_center, top_y, bottom_y
                    )

                # Draw vertical stub from parent down to (but not including) the
                # jog row.  Skip cells that already hold a corner so we don't
                # clobber a previously drawn edge.
                for y in range(top_y + 1, jog_y):
                    if self.canvas[y][top_center] != self.options.edge_cross:
                        self._merge_line_cell(top_center, y, {"up", "down"}, edge_color)

                if top_center != bottom_center:
                    # Junctions at both ends of the horizontal jog.
                    top_dirs: Set[str] = {"up"}
                    bottom_dirs: Set[str] = {"down"}
                    if bottom_center > top_center:
                        top_dirs.add("right")
                        bottom_dirs.add("left")
                    else:
                        top_dirs.add("left")
                        bottom_dirs.add("right")

                    self._merge_line_cell(top_center, jog_y, top_dirs, edge_color)
                    self._merge_line_cell(bottom_center, jog_y, bottom_dirs, edge_color)

                    # Horizontal segment between the corners
                    min_x = min(top_center, bottom_center)
                    max_x = max(top_center, bottom_center)
                    for x in range(min_x + 1, max_x):
                        self._merge_line_cell(x, jog_y, {"left", "right"}, edge_color)
                else:
                    # Straight down: vertical bar at jog_y too
                    self._merge_line_cell(top_center, jog_y, {"up", "down"}, edge_color)

                # Draw vertical segment from jog row down to child
                for y in range(jog_y + 1, bottom_y):
                    self._merge_line_cell(bottom_center, y, {"up", "down"}, edge_color)

                # Direction indicators
                top_terminal_y = top_y + 1
                bottom_terminal_y = bottom_y - 1
                if is_bidirectional:
                    self._paint_edge_cell(
                        top_center,
                        top_terminal_y,
                        self.options.get_arrow_for_direction("up"),
                        edge_color,
                    )
                    self._paint_edge_cell(
                        bottom_center,
                        bottom_terminal_y,
                        self.options.get_arrow_for_direction("down"),
                        edge_color,
                    )
                else:
                    if start_y < end_y:  # top-to-bottom: arrow points down toward child
                        self._paint_edge_cell(
                            bottom_center,
                            bottom_terminal_y,
                            self.options.get_arrow_for_direction("down"),
                            edge_color,
                        )
                    else:  # bottom-to-top: arrow points up toward parent
                        self._paint_edge_cell(
                            top_center,
                            top_terminal_y,
                            self.options.get_arrow_for_direction("up"),
                            edge_color,
                        )

        except IndexError as e:
            raise IndexError(f"Edge drawing exceeded canvas boundaries: {e}")

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

        try:
            import pydot  # type: ignore
        except ImportError:
            raise ImportError("pydot is required for DOT format support")

        with warnings.catch_warnings():
            # pyparsing emits deprecation warnings via pydot on newer versions.
            # Tests enforce warnings as errors, so suppress this third-party
            # warning only for the parse call.
            warnings.filterwarnings(
                "ignore",
                category=DeprecationWarning,
                module=r"pydot\.dot_parser",
            )
            try:
                from pyparsing import PyparsingDeprecationWarning  # type: ignore

                warnings.filterwarnings("ignore", category=PyparsingDeprecationWarning)
            except Exception:
                pass
            graphs = pydot.graph_from_dot_data(dot_string)
        if not graphs:
            raise ValueError("No valid graphs found in DOT string")

        # Take first graph from the list
        G = nx.nx_pydot.from_pydot(graphs[0])
        if not isinstance(G, nx.DiGraph):
            G = nx.DiGraph(G)
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
        try:
            G = nx.read_graphml(graphml_file)
            if not isinstance(G, nx.DiGraph):
                G = nx.DiGraph(G)
            return cls(G, **kwargs)
        except Exception as e:
            raise ValueError(f"Failed to read GraphML file: {e}")

    @classmethod
    def from_plantuml(cls, plantuml_string: str, **kwargs: Any) -> "ASCIIRenderer":
        """Create a renderer from a PlantUML text diagram.

        Supported subset:
        - Common participant/class/object declarations
        - Relationship lines using PlantUML arrows (e.g. A --> B, A <- B, A <-> B)
        - Optional edge labels using ``: label``
        """

        graph = nx.DiGraph()
        alias_to_id: Dict[str, str] = {}

        declaration_kinds = (
            "abstract class",
            "class",
            "interface",
            "enum",
            "entity",
            "annotation",
            "actor",
            "participant",
            "boundary",
            "control",
            "database",
            "collections",
            "queue",
            "component",
            "node",
            "usecase",
            "object",
            "artifact",
            "cloud",
            "folder",
            "frame",
            "rectangle",
        )
        decl_re = re.compile(
            r"^(?P<kind>"
            + "|".join(re.escape(kind) for kind in declaration_kinds)
            + r")\s+"
            r"(?P<lhs>\"[^\"]+\"|[A-Za-z_][\w.:$-]*)"
            r"(?:\s+as\s+(?P<rhs>\"[^\"]+\"|[A-Za-z_][\w.:$-]*))?"
            r"(?:\s+<<[^>]+>>)?\s*$",
            re.IGNORECASE,
        )
        rel_re = re.compile(
            r"^(?P<src>\"[^\"]+\"|[A-Za-z_][\w.:$-]*)\s*"
            r"(?P<arrow>[A-Za-z0-9_<>*#.\-/\\|]+)\s*"
            r"(?P<dst>\"[^\"]+\"|[A-Za-z_][\w.:$-]*)"
            r"(?:\s*:\s*(?P<label>.+))?\s*$"
        )

        def _unquote(token: str) -> str:
            token = token.strip()
            if len(token) >= 2 and token[0] == token[-1] == '"':
                return token[1:-1]
            return token

        def _ensure_node(node_id: str, label: Optional[str] = None) -> None:
            if node_id not in graph:
                graph.add_node(node_id)
            if label:
                graph.nodes[node_id]["label"] = label

        def _resolve_token(token: str) -> str:
            token = token.strip()
            if len(token) >= 2 and token[0] == token[-1] == '"':
                label = token[1:-1]
                _ensure_node(label, label=label)
                return label
            return alias_to_id.get(token, token)

        for raw_line in plantuml_string.splitlines():
            line = raw_line.strip()
            if "'" in line:
                line = line.split("'", 1)[0].rstrip()
            if not line or line.startswith("//"):
                continue
            lowered = line.lower()
            if lowered in {"@startuml", "@enduml", "{", "}", "end", "end note"}:
                continue
            if lowered.startswith(
                (
                    "skinparam ",
                    "title ",
                    "header ",
                    "footer ",
                    "legend ",
                    "note ",
                    "hide ",
                    "show ",
                    "left to right",
                    "top to bottom",
                    "scale ",
                    "caption ",
                    "newpage",
                    "page ",
                    "!",
                )
            ):
                continue

            decl = decl_re.match(line)
            if decl:
                lhs = decl.group("lhs")
                rhs = decl.group("rhs")
                if rhs:
                    lhs_unq = _unquote(lhs)
                    rhs_unq = _unquote(rhs)
                    if lhs.startswith('"') and rhs.startswith('"'):
                        node_id = lhs_unq
                        _ensure_node(node_id, label=lhs_unq)
                    elif lhs.startswith('"'):
                        node_id = rhs_unq
                        alias_to_id[rhs_unq] = node_id
                        _ensure_node(node_id, label=lhs_unq)
                    elif rhs.startswith('"'):
                        node_id = lhs_unq
                        alias_to_id[lhs_unq] = node_id
                        _ensure_node(node_id, label=rhs_unq)
                    else:
                        node_id = lhs_unq
                        alias_to_id[rhs_unq] = node_id
                        _ensure_node(node_id, label=lhs_unq)
                else:
                    node_id = _unquote(lhs)
                    _ensure_node(node_id, label=node_id)
                    alias_to_id[node_id] = node_id
                continue

            relation = rel_re.match(line)
            if not relation:
                continue

            arrow = relation.group("arrow")
            # Ignore non-link operator tokens.
            if not any(ch in arrow for ch in ("-", ".", "<", ">")):
                continue

            src = _resolve_token(relation.group("src"))
            dst = _resolve_token(relation.group("dst"))
            _ensure_node(src, label=graph.nodes[src].get("label", src))
            _ensure_node(dst, label=graph.nodes[dst].get("label", dst))

            label = relation.group("label")
            edge_attrs: Dict[str, Any] = {}
            if label:
                clean_label = label.strip()
                if clean_label:
                    edge_attrs["label"] = clean_label

            has_left = "<" in arrow
            has_right = ">" in arrow
            if has_left and not has_right:
                graph.add_edge(dst, src, **edge_attrs)
            elif has_right and not has_left:
                graph.add_edge(src, dst, **edge_attrs)
            elif has_left and has_right:
                graph.add_edge(src, dst, **edge_attrs)
                graph.add_edge(dst, src, **edge_attrs)
            else:
                # Undirected relation styles are represented as a single directed edge.
                graph.add_edge(src, dst, **edge_attrs)

        if graph.number_of_nodes() == 0:
            raise ValueError("No supported PlantUML nodes or relationships found")
        return cls(graph, **kwargs)


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
