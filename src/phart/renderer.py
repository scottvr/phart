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

from typing import List
import networkx as nx
from .styles import NodeStyle, LayoutOptions
from .layout import LayoutManager


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

    def __init__(
        self,
        graph: nx.Graph,
        node_style: NodeStyle = NodeStyle.MINIMAL,
        node_spacing: int = 4,
        layer_spacing: int = 2,
    ):
        self.graph = graph
        self.options = LayoutOptions(
            node_style=node_style,
            node_spacing=node_spacing,
            layer_spacing=layer_spacing,
        )
        self.layout_manager = LayoutManager(graph, self.options)
        self.canvas: List[List[str]] = []

    def render(self) -> str:
        """
        Render the graph as ASCII art.

        Returns:
            String containing the ASCII representation of the graph

        Raises:
            RuntimeError: If layout calculation fails
            ValueError: If rendering encounters invalid node positions
        """
        try:
            # Calculate layout
            positions, width, height = self.layout_manager.calculate_layout()
            self._init_canvas(width, height)

            # Draw edges first (so nodes will overlay them)
            for start, end in self.graph.edges():
                self._draw_edge(start, end, positions)

            # Draw nodes
            for node, (x, y) in positions.items():
                prefix, suffix = self.options.get_node_decorators(str(node))
                label = f"{prefix}{node}{suffix}"
                try:
                    for i, char in enumerate(label):
                        self.canvas[y][x + i] = char
                except IndexError:
                    raise ValueError(
                        f"Node '{node}' position exceeds canvas boundaries"
                    )

            # Convert canvas to string, trimming trailing spaces
            return "\n".join("".join(row).rstrip() for row in self.canvas)

        except Exception as e:
            raise RuntimeError(f"Failed to render graph: {e}")

    @classmethod
    def from_dot(cls, dot_string: str, **kwargs) -> "ASCIIRenderer":
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
            import pydot
        except ImportError:
            raise ImportError("pydot is required for DOT format support")

        G = nx.nx_pydot.from_pydot(pydot.graph_from_dot_data(dot_string))
        if not isinstance(G, nx.DiGraph):
            G = nx.DiGraph(G)
        return cls(G, **kwargs)
