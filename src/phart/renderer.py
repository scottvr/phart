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
        """
        Render the graph as ASCII art.

        Returns
        -------
        str
            ASCII representation of the graph
        """

        # Calculate layout
        positions, width, height = self.layout_manager.calculate_layout()
        if not positions:
            return ""

        print("DEBUG: Original positions:", positions)

        # Add left padding to all positions
        padding_left = 4 if not self.options.use_ascii else 6
        adjusted_positions = {
            node: (x + padding_left, y) for node, (x, y) in positions.items()
        }

        print("DEBUG: Adjusted positions:", adjusted_positions)

        # Initialize canvas with adjusted positions
        self._init_canvas(width, height, adjusted_positions)

        # Draw edges first
        for start, end in self.graph.edges():
            try:
                self._draw_edge(start, end, adjusted_positions)
            except IndexError as e:
                print(f"DEBUG: Error drawing edge {start}->{end}: {e}")
                print(f"DEBUG: Start pos: {adjusted_positions[start]}")
                print(f"DEBUG: End pos: {adjusted_positions[end]}")
                print(f"DEBUG: Canvas size: {len(self.canvas[0])}x{len(self.canvas)}")
                raise

        # Draw nodes
        for node, (x, y) in adjusted_positions.items():
            prefix, suffix = self.options.get_node_decorators(str(node))
            label = f"{prefix}{node}{suffix}"
            for i, char in enumerate(label):
                self.canvas[y][x + i] = char

        # Build final string, trimming trailing spaces
        preamble = str(self.options) + "\n" if print_config else ""
        result = "\n".join("".join(row).rstrip() for row in self.canvas)
        return f"{preamble}{result}" if preamble else result

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
        Initialize the rendering canvas with given dimensions.

        Args:
            width: Canvas width in characters
            height: Canvas height in characters

        Raises:
            ValueError: If dimensions are negative or zero
        """
        if width <= 0 or height <= 0:
            raise ValueError(
                f"Canvas dimensions must be positive (got {width}x{height})"
            )

        # Calculate required width based on rightmost node position plus its width
        max_node_end = 0
        for node, (x, y) in positions.items():
            node_width = sum(
                len(part) for part in self.options.get_node_decorators(str(node))
            ) + len(str(node))
            node_end = x + node_width
            max_node_end = max(max_node_end, node_end)

        # Add padding for edge decorators and bidirectional markers
        padding_right = (
            4 if not self.options.use_ascii else 6
        )  # Extra space for ASCII markers
        final_width = max_node_end + padding_right

        # Add vertical padding
        final_height = height + 2

        print(f"DEBUG: Canvas initialized with {final_width}x{final_height}")
        print(f"DEBUG: Max node end position: {max_node_end}")

        self.canvas = [[" " for _ in range(final_width)] for _ in range(final_height)]

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

        # Account for node decoration width
        prefix, _ = self.options.get_node_decorators(str(start))
        start_x += len(prefix) + len(str(start)) // 2
        end_x += len(prefix) + len(str(end)) // 2

        # Check if this is a bidirectional edge
        is_bidirectional = (
            not self.graph.is_directed()  # Undirected graphs are always bidirectional
            or (end, start) in self.graph.edges()  # Explicit reverse edge exists
        )

        try:
            # Case 1: Straight vertical connection
            if start_x == end_x:
                # Draw vertical line
                for y in range(start_y + 1, end_y - 1):
                    self.canvas[y][start_x] = self.options.edge_vertical

                if is_bidirectional:
                    # Place bidirectional marker in middle
                    mid_y = (start_y + end_y) // 2
                    self.canvas[mid_y][start_x] = self.options.edge_arrow_bidir_h
                else:
                    # Add down arrow at end
                    self.canvas[end_y - 1][start_x] = self.options.edge_arrow_down
                return

            # Case 2: Edges that turn (down and left/right)
            if start_y != end_y:
                # Draw vertical segment
                for y in range(start_y + 1, end_y - 1):
                    self.canvas[y][start_x] = self.options.edge_vertical

                # Add down arrow at bottom of vertical
                self.canvas[end_y - 1][start_x] = self.options.edge_arrow_down

                # Add crossing point
                self.canvas[end_y][start_x] = self.options.edge_cross

                # Draw horizontal segment with arrow
                if start_x < end_x:  # Moving right
                    for x in range(start_x + 1, end_x):
                        self.canvas[end_y][x] = self.options.edge_horizontal
                    self.canvas[end_y][end_x - 1] = self.options.edge_arrow_r
                else:  # Moving left
                    for x in range(end_x + 1, start_x):
                        self.canvas[end_y][x] = self.options.edge_horizontal
                    self.canvas[end_y][end_x + 1] = self.options.edge_arrow_l
                return

            # Case 3: Same level horizontal
            if start_y == end_y:
                x_start, x_end = min(start_x, end_x), max(start_x, end_x)

                if is_bidirectional:
                    # Draw horizontal line with bidirectional marker
                    for x in range(x_start + 1, x_end):
                        self.canvas[start_y][x] = self.options.edge_horizontal
                    mid_x = (x_start + x_end) // 2
                    self.canvas[start_y][mid_x] = self.options.edge_arrow_bidir_v
                else:
                    # Draw full horizontal line with arrow
                    for x in range(x_start + 1, x_end - 1):
                        self.canvas[start_y][x] = self.options.edge_horizontal
                    if start_x < end_x:  # Moving right
                        self.canvas[start_y][x_end - 1] = self.options.edge_arrow_r
                    else:  # Moving left
                        self.canvas[start_y][x_start + 1] = self.options.edge_arrow_l

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
