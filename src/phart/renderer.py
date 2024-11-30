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
        node_style: NodeStyle = NodeStyle.SQUARE,
        node_spacing: int = 4,
        layer_spacing: int = 2,
        use_ascii: Optional[bool] = None,
        options: Optional[LayoutOptions] = None,
    ) -> None:
        self.graph = graph

        if use_ascii is None:
            use_ascii = not self._can_use_unicode()

        if options is not None:
            self.options = options
        else:
            self.options = LayoutOptions(
                node_style=node_style,
                node_spacing=node_spacing,
                layer_spacing=layer_spacing,
                use_ascii=use_ascii,
            )
        self.layout_manager = LayoutManager(graph, self.options)
        self.canvas: List[List[str]] = []

    def _ensure_encoding(self, text: str) -> str:
        """Internal method to handle encoding safely."""
        try:
            return text.encode("utf-8").decode("utf-8")
        except UnicodeEncodeError:
            return text.encode("ascii", errors="replace").decode("ascii")

    def render(self) -> str:
        """
        Render the graph as ASCII art.

        Returns
        -------
        str
            ASCII representation of the graph
        """
        # Calculate layout and render to canvas
        positions, width, height = self.layout_manager.calculate_layout()
        if not positions:
            return ""

        self._init_canvas(width, height)

        # Draw edges first
        for start, end in self.graph.edges():
            self._draw_edge(start, end, positions)

        # Draw nodes
        for node, (x, y) in positions.items():
            prefix, suffix = self.options.get_node_decorators(str(node))
            label = f"{prefix}{node}{suffix}"
            for i, char in enumerate(label):
                self.canvas[y][x + i] = char

        result = "\n".join("".join(row).rstrip() for row in self.canvas)
        return self._ensure_encoding(result)

    def draw(self, file: Optional[TextIO] = None) -> None:
        """
        Draw the graph to a file or stdout.

        Parameters
        ----------
        file : Optional[TextIO]
            File to write to. If None, writes to stdout
        """

        if file is None:
            import sys
            import io

            if not self.options.use_ascii:
                sys.stdout = io.TextIOWrapper(
                    sys.stdout.buffer, encoding="utf-8", errors="replace"
                )
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

    def _init_canvas(self, width: int, height: int) -> None:
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

        self.canvas = [[" " for _ in range(width)] for _ in range(height)]

    def _draw_edge(
        self, start: str, end: str, positions: Dict[str, Tuple[int, int]]
    ) -> None:
        """
        Draw an edge between two nodes on the canvas.

        Args:
            start: Source node identifier
            end: Target node identifier
            positions: Dictionary mapping nodes to their (x, y) coordinates

        Raises:
            KeyError: If either node is not in positions dictionary
            IndexError: If edge coordinates exceed canvas boundaries
        """
        if start not in positions or end not in positions:
            raise KeyError(
                f"Node position not found: {start if start not in positions else end}"
            )

        start_x, start_y = positions[start]
        end_x, end_y = positions[end]

        # Account for node decoration width
        prefix, _ = self.options.get_node_decorators(start)
        start_x += len(prefix) + len(str(start)) // 2
        end_x += len(prefix) + len(str(end)) // 2

        try:
            # Draw vertical line
            min_y, max_y = min(start_y, end_y), max(start_y, end_y)
            for y in range(min_y + 1, max_y):
                curr_char = self.canvas[y][start_x]
                if curr_char == self.options.edge_horizontal:
                    self.canvas[y][start_x] = self.options.edge_cross
                else:
                    self.canvas[y][start_x] = self.options.edge_vertical

            # Draw horizontal line if needed
            if start_x != end_x:
                y = end_y
                x_start, x_end = min(start_x, end_x), max(start_x, end_x)
                for x in range(x_start, x_end + 1):
                    curr_char = self.canvas[y][x]
                    if curr_char == self.options.edge_vertical:
                        self.canvas[y][x] = self.options.edge_cross
                    else:
                        self.canvas[y][x] = self.options.edge_horizontal

            # Add arrow
            if end_y > start_y:  # Downward arrow
                self.canvas[end_y - 1][end_x] = self.options.edge_arrow_down
            elif end_y < start_y:  # Upward arrow
                self.canvas[end_y + 1][end_x] = self.options.edge_arrow_up
            else:  # Horizontal arrow
                if end_x > start_x:
                    self.canvas[end_y][end_x - 1] = self.options.edge_arrow
                else:
                    self.canvas[end_y][start_x - 1] = "<"

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
