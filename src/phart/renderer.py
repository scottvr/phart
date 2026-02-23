from __future__ import annotations
from typing import Any, Dict, List, Optional, TextIO, Tuple, ClassVar
import warnings

import networkx as nx  # type: ignore

from .layout import LayoutManager
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

    def _get_widest_node_text_width(self) -> Optional[int]:
        if not self.options.uniform:
            return None
        return max(
            (len(self.options.get_node_text(str(node))) for node in self.graph.nodes()),
            default=0,
        )

    def _get_node_dimensions(self, node: str) -> Tuple[int, int]:
        return self.options.get_node_dimensions(
            str(node), widest_text_width=self._get_widest_node_text_width()
        )

    def _get_node_bounds(
        self, node: str, positions: Dict[str, Tuple[int, int]]
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

    def _draw_node(self, node: str, x: int, y: int) -> None:
        label = self.options.get_node_text(str(node))
        node_width, node_height = self._get_node_dimensions(node)

        if not self.options.bboxes:
            for i, char in enumerate(label):
                self.canvas[y][x + i] = char
            return

        right_x = x + node_width - 1
        bottom_y = y + node_height - 1
        inner_start_x = x + 1 + self.options.hpad
        label_y = y + 1 + self.options.vpad

        self.canvas[y][x] = self.options.box_top_left
        self.canvas[y][right_x] = self.options.box_top_right
        for col in range(x + 1, right_x):
            self.canvas[y][col] = self.options.edge_horizontal

        self.canvas[bottom_y][x] = self.options.box_bottom_left
        self.canvas[bottom_y][right_x] = self.options.box_bottom_right
        for col in range(x + 1, right_x):
            self.canvas[bottom_y][col] = self.options.edge_horizontal

        for row in range(y + 1, bottom_y):
            self.canvas[row][x] = self.options.edge_vertical
            self.canvas[row][right_x] = self.options.edge_vertical

        for i, char in enumerate(label):
            self.canvas[label_y][inner_start_x + i] = char

    def render(self, print_config: Optional[bool] = False) -> str:
        """Render the graph as ASCII art."""
        positions, width, height = self.layout_manager.calculate_layout()
        if not positions:
            return ""

        # Initialize canvas with adjusted positions
        self._init_canvas(width, height, positions)

        # Only try to draw edges if we have any
        if self.graph.edges():
            for start, end in self.graph.edges():
                if start in positions and end in positions:
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
                self._draw_node(str(node), x, y)
            except IndexError as e:
                pos_info = f"pos=({x},{y}), node={node}"
                canvas_info = f"canvas={len(self.canvas)}x{len(self.canvas[0])}"
                raise IndexError(
                    f"Node drawing failed: {pos_info}, {canvas_info}"
                ) from e

        return "\n".join("".join(row).rstrip() for row in self.canvas)

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
        self, width: int, height: int, positions: Dict[str, Tuple[int, int]]
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
                x + self._get_node_dimensions(str(node))[0]
                for node, (x, _) in positions.items()
            ),
            default=1,
        )
        max_bottom = max(
            (
                y + self._get_node_dimensions(str(node))[1]
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

    def _draw_vertical_segment(
        self, x: int, start_y: int, end_y: int, marker: Optional[str]
    ) -> None:
        for y in range(start_y + 1, end_y):
            self.canvas[y][x] = self.options.edge_vertical
        if marker is not None:
            mid_y = (start_y + end_y) // 2
            self.canvas[mid_y][x] = marker
        return None

    def _draw_horizontal_segment(
        self, y: int, start_x: int, end_x: int, marker: Optional[str]
    ) -> None:
        for x in range(start_x + 1, end_x):
            self.canvas[y][x] = self.options.edge_horizontal
        if marker is not None:
            mid_x = (start_x + end_x) // 2
            self.canvas[y][mid_x] = marker
        return None

    def _safe_draw(self, x: int, y: int,  char: str) -> None:
        try:
            self.canvas[y][x] = char
        except IndexError:
            raise IndexError(f"Drawing exceeded canvas bounds at ({x}, {y})")
        return None

    def _is_terminal(
        self, positions: Dict[str, Tuple[int, int]], node: str, x: int, y: int
    ) -> bool:
        """
        Check if a position represents a node connection point.

        A terminal is the point where an edge connects to a node, typically the
        node's center point on its boundary.
        """
        if node not in positions:
            return False
        bounds = self._get_node_bounds(node, positions)
        return (
            y == bounds["center_y"]
            and x in {bounds["left"], bounds["right"], bounds["center_x"]}
        )

    def _draw_direction(
        self, y: int, x: int, direction: str, is_terminal: bool = False
    ) -> None:
        """
        Draw a directional indicator, respecting terminal points.

        Terminal points always show direction as they represent actual node connections.
        Non-terminal points preserve existing directional indicators to maintain path clarity.
        """
        if is_terminal:
            # Always show direction at node connection points
            self.canvas[y][x] = direction
        elif self.canvas[y][x] not in (
            self.options.edge_arrow_up,
            self.options.edge_arrow_down,
        ):
            # Only draw direction on non-terminals if there isn't already a direction
            self.canvas[y][x] = direction

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
                if cell == self.options.edge_vertical and x in (top_center, bottom_center):
                    continue
                conflict = True
                break
            if not conflict:
                return jog_y

        return latest_jog

    def _draw_edge(
        self, start: str, end: str, positions: Dict[str, Tuple[int, int]]
    ) -> None:
        """Draw an edge between two nodes on the canvas."""
        if start not in positions or end not in positions:
            raise KeyError(
                f"Node position not found: {start if start not in positions else end}"
            )

        start_bounds = self._get_node_bounds(start, positions)
        end_bounds = self._get_node_bounds(end, positions)

        start_center_x = start_bounds["center_x"]
        start_center_y = start_bounds["center_y"]
        end_center_x = end_bounds["center_x"]
        end_center_y = end_bounds["center_y"]

        # Check if this is a bidirectional edge
        is_bidirectional = (
            not self.graph.is_directed() or (end, start) in self.graph.edges()
        )

        try:
            # Case 1: Same level horizontal connection
            if start_center_y == end_center_y:
                y = start_center_y

                if start_center_x <= end_center_x:
                    left_node = start_bounds
                    right_node = end_bounds
                else:
                    left_node = end_bounds
                    right_node = start_bounds

                min_x = left_node["right"] + 1
                max_x = right_node["left"] - 1

                for x in range(min_x, max_x + 1):
                    self.canvas[y][x] = self.options.edge_horizontal

                if is_bidirectional:
                    if min_x <= max_x:
                        self.canvas[y][min_x] = self.options.get_arrow_for_direction("right")
                        self.canvas[y][max_x] = self.options.get_arrow_for_direction("left")
                elif min_x <= max_x:
                    if start_center_x < end_center_x:
                        self.canvas[y][max_x] = self.options.get_arrow_for_direction("right")
                    else:
                        self.canvas[y][min_x] = self.options.get_arrow_for_direction("left")

            # Case 2: Top to bottom (or bottom to top) connection
            else:
                # Identify top and bottom nodes
                top_node = start if start_center_y < end_center_y else end
                bottom_node = end if start_center_y < end_center_y else start
                top_bounds = start_bounds if top_node == start else end_bounds
                bottom_bounds = end_bounds if bottom_node == end else start_bounds

                top_center = top_bounds["center_x"]
                bottom_center = bottom_bounds["center_x"]
                top_y = top_bounds["bottom"]
                bottom_y = bottom_bounds["top"]

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
                        self.canvas[y][top_center] = self.options.edge_vertical

                if top_center != bottom_center:
                    # Corners at both ends of the horizontal jog
                    self.canvas[jog_y][top_center] = self.options.edge_cross
                    self.canvas[jog_y][bottom_center] = self.options.edge_cross

                    # Horizontal segment between the corners
                    min_x = min(top_center, bottom_center)
                    max_x = max(top_center, bottom_center)
                    for x in range(min_x + 1, max_x):
                        self.canvas[jog_y][x] = self.options.edge_horizontal
                else:
                    # Straight down: vertical bar at jog_y too
                    self.canvas[jog_y][top_center] = self.options.edge_vertical

                # Draw vertical segment from jog row down to child
                for y in range(jog_y + 1, bottom_y):
                    self.canvas[y][bottom_center] = self.options.edge_vertical

                # Direction indicators
                if is_bidirectional:
                    if bottom_y > jog_y + 1:
                        self.canvas[jog_y + 1][bottom_center] = self.options.get_arrow_for_direction("up")
                    self.canvas[bottom_y - 1][bottom_center] = (
                        self.options.get_arrow_for_direction("down")
                    )
                else:
                    if start_center_y < end_center_y:  # top-to-bottom: arrow points down toward child
                        if bottom_y > jog_y + 1:
                            self.canvas[bottom_y - 1][bottom_center] = (
                                self.options.get_arrow_for_direction("down")
                            )
                    else:  # bottom-to-top: arrow points up toward parent
                        if bottom_y > jog_y + 1:
                            self.canvas[jog_y + 1][bottom_center] = (
                                self.options.get_arrow_for_direction("up")
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

                warnings.filterwarnings(
                    "ignore", category=PyparsingDeprecationWarning
                )
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


def merge_layout_options(
    base: LayoutOptions, overrides: LayoutOptions
    ) -> LayoutOptions:
    from dataclasses import asdict, fields
        
    base_dict = asdict(base)
    override_dict = asdict(overrides)
    merged_dict: dict[str, Any] = {}
        
    # Define which fields are "rendering" vs "semantic"
    rendering_fields = {
        "use_ascii",
        "node_style",
        "node_spacing",
        "layer_spacing",
        "left_padding",
        "right_padding",
        "margin",
        "flow_direction",
        "bboxes",
        "hpad",
        "vpad",
        "uniform",
    }
       
    for field in fields(LayoutOptions):
        field_name = field.name
        if field_name == 'instance_id':
            continue
          
        override_val = override_dict.get(field_name)
        base_val = base_dict.get(field_name)
         
        # For rendering fields: CLI (override) takes precedence if not None
        if field_name in rendering_fields:
            merged_dict[field_name] = override_val if override_val is not None else base_val
        # For semantic fields: User (base) takes precedence if not None
        else:
            merged_dict[field_name] = base_val if base_val is not None else override_val
        
    # Special handling for custom_decorators - merge dicts
    if base.custom_decorators and overrides.custom_decorators:
        merged_dict['custom_decorators'] = {**base.custom_decorators, **overrides.custom_decorators}
    elif base.custom_decorators:
        merged_dict['custom_decorators'] = base.custom_decorators.copy()
    elif overrides.custom_decorators:
        merged_dict['custom_decorators'] = overrides.custom_decorators.copy()
        
    return LayoutOptions(**merged_dict)
