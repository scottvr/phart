"""
*****
PHART
*****

Python Hierarchical ASCII Rendering Tool for graphs.

This module provides functionality for rendering graphs as ASCII art, with particular
emphasis on dependency visualization and hierarchical structures.

The PHART renderer can visualize:
* NetworkX graphs
* DOT format graphs
* GraphML files
* Dependency structures

Examples
--------
>>> import networkx as nx
>>> from phart import ASCIIRenderer
>>>
>>> # Simple path graph
>>> G = nx.path_graph(3)
>>> renderer = ASCIIRenderer(G)
>>> print(renderer.render())
1
|
2
|
3

>>> # Directed graph with custom node style
>>> G = nx.DiGraph([('A', 'B'), ('A', 'C'), ('B', 'D'), ('C', 'D')])
>>> renderer = ASCIIRenderer(G, node_style=NodeStyle.SQUARE)
>>> print(renderer.render())
    [A]
     |
  ---|---
  |     |
[B]    [C]
  |     |
  |     |
   --[D]--

Notes
-----
While this module can work with any NetworkX graph, it is optimized for:
* Directed acyclic graphs (DAGs)
* Dependency trees
* Hierarchical structures

For dense or highly connected graphs, the ASCII representation may become
cluttered. Consider using dedicated visualization tools for such cases.

See Also
--------
* NetworkX: https://networkx.org/
* Graphviz: https://graphviz.org/
"""
# src path: src\phart\renderer.py

from typing import Any, Dict, List, Optional, TextIO, Tuple

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

    Examples
    --------
    >>> import networkx as nx
    >>> G = nx.DiGraph([('A', 'B'), ('B', 'C')])
    >>> renderer = ASCIIRenderer(G)
    >>> print(renderer.render())
    A
    |
    B
    |
    C

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

    default_options: Optional[LayoutOptions] = None

    def __init__(
        self,
        graph: nx.Graph,
        *,  # Force keyword args after this
        node_style: NodeStyle = NodeStyle.SQUARE,
        node_spacing: int = 4,
        layer_spacing: int = 2,
        use_ascii: Optional[bool] = None,
        custom_decorators: Optional[Dict[str, Tuple[str, str]]] = None,
        options: Optional[LayoutOptions] = None,
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

    def _ensure_encoding(self, text: str) -> str:
        """Internal method to handle encoding safely."""
        try:
            return text.encode("utf-8").decode("utf-8")
        except UnicodeEncodeError:
            return text.encode("ascii", errors="replace").decode("ascii")

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
            prefix, suffix = self.options.get_node_decorators(str(node))
            label = f"{prefix}{node}{suffix}"
            for i, char in enumerate(label):
                try:
                    self.canvas[y][x + i] = char
                except IndexError as e:
                    pos_info = f"pos=({x},{y}), i={i}, label={label}"
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
        max_x_pos = max(x for x, _ in positions.values()) if positions else 0
        max_y_pos = max(y for _, y in positions.values()) if positions else 0

        # Calculate width needed for widest node plus its position
        max_node_width = (
            max(
                sum(len(part) for part in self.options.get_node_decorators(str(node)))
                + len(str(node))
                for node in positions.keys()
            )
            if positions
            else 1
        )

        # Ensure minimum dimensions that can hold all nodes and edges
        min_width = max_x_pos + max_node_width + 1  # +1 for safety margin
        min_height = max_y_pos + 3  # +3 to ensure room for edges between layers

        final_width = max(width, min_width)
        final_height = max(height, min_height)

        if final_width < 0 or final_height < 0:
            raise ValueError(
                f"Canvas dimensions must not be negative (got {width}x{height})"
            )

        self.canvas = [[" " for _ in range(final_width)] for _ in range(final_height)]

    def _draw_vertical_segment(self, x, start_y, end_y, marker=None):
        for y in range(start_y + 1, end_y):
            self.canvas[y][x] = self.options.edge_vertical
        if marker:
            mid_y = (start_y + end_y) // 2
            self.canvas[mid_y][x] = marker

    def _draw_horizontal_segment(self, y, start_x, end_x, marker=None):
        for x in range(start_x + 1, end_x):
            self.canvas[y][x] = self.options.edge_horizontal
        if marker:
            mid_x = (start_x + end_x) // 2
            self.canvas[y][mid_x] = marker

    def _safe_draw(self, x, y, char):
        try:
            self.canvas[y][x] = char
        except IndexError:
            raise IndexError(f"Drawing exceeded canvas bounds at ({x}, {y})")

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
        node_x, node_y = positions[node]
        prefix, _ = self.options.get_node_decorators(str(node))
        node_width = len(str(node)) + len(str(prefix))
        node_center = node_x + node_width // 2

        return y == node_y and x == node_center

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

    def _draw_edge(
        self, start: str, end: str, positions: Dict[str, Tuple[int, int]]
    ) -> None:
        """Draw an edge between two nodes on the canvas."""
        if start not in positions or end not in positions:
            raise KeyError(
                f"Node position not found: {start if start not in positions else end}"
            )

        start_x, start_y = positions[start]
        end_x, end_y = positions[end]

        # Calculate node widths for edge positioning
        prefix, _ = self.options.get_node_decorators(str(start))
        start_width = len(str(start)) + len(str(prefix))
        end_width = len(str(end)) + len(str(prefix))

        start_center = start_x + start_width // 2
        end_center = end_x + end_width // 2

        # Check if this is a bidirectional edge
        is_bidirectional = (
            not self.graph.is_directed() or (end, start) in self.graph.edges()
        )

        try:
            # Case 1: Same level horizontal connection
            if start_y == end_y:
                min_x = min(start_center, end_center)
                max_x = max(start_center, end_center)
                for x in range(min_x + 1, max_x):
                    self.canvas[start_y][x] = self.options.edge_horizontal
                if is_bidirectional:
                    self.canvas[start_y][min_x + 1] = self.options.edge_arrow_r
                    self.canvas[start_y][max_x - 1] = self.options.edge_arrow_l
                else:
                    if start_center < end_center:
                        self.canvas[start_y][max_x - 1] = self.options.edge_arrow_r
                    else:
                        self.canvas[start_y][min_x + 1] = self.options.edge_arrow_l

            # Case 2: Top to bottom connection
            elif start_y < end_y or end_y < start_y:
                # Identify top and bottom nodes
                top_node = start if start_y < end_y else end
                bottom_node = end if start_y < end_y else start
                top_x, top_y = positions[top_node]
                bottom_x, bottom_y = positions[bottom_node]

                # Calculate centers
                top_center = top_x + (len(str(top_node)) + len(str(prefix))) // 2
                bottom_center = (
                    bottom_x + (len(str(bottom_node)) + len(str(prefix))) // 2
                )

                # Draw horizontal segment from top node to vertical drop point
                min_x = min(top_center, bottom_center)
                max_x = max(top_center, bottom_center)
                y = top_y
                for x in range(min_x + 1, max_x):
                    self.canvas[y][x] = self.options.edge_horizontal

                # Add crossing point
                self.canvas[y][bottom_center] = self.options.edge_cross

                # Draw vertical segment
                for y in range(top_y + 1, bottom_y):
                    self.canvas[y][bottom_center] = self.options.edge_vertical

                # Add direction indicators
                if is_bidirectional:
                    # Place arrows at both ends
                    self.canvas[top_y + 1][bottom_center] = self.options.edge_arrow_up
                    self.canvas[bottom_y - 1][bottom_center] = (
                        self.options.edge_arrow_down
                    )
                else:
                    # Add arrow based on direction
                    if start_y < end_y:  # Top to bottom
                        self.canvas[top_y + 1][bottom_center] = (
                            self.options.edge_arrow_up
                        )
                    else:  # Bottom to top
                        self.canvas[bottom_y - 1][bottom_center] = (
                            self.options.edge_arrow_down
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
