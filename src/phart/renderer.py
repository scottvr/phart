from typing import List, Optional
import networkx as nx
from .styles import LayoutOptions, NodeStyle
from .layout import LayoutManager

class ASCIIGraphRenderer:
    """Main class for rendering graphs as ASCII art"""

    def __init__(self, graph: nx.DiGraph, options: Optional[LayoutOptions] = None):
        """
        Initialize the renderer with a graph and optional style configuration.

        Args:
            graph: A NetworkX directed graph to render
            options: Layout and style options (uses defaults if None)
        """
        self.graph = graph
        self.options = options or LayoutOptions()
        self.layout_manager = LayoutManager(graph, self.options)
        self.canvas: List[List[str]] = []

    def _init_canvas(self, width: int, height: int) -> None:
        """Initialize empty canvas with given dimensions"""
        self.canvas = [[' ' for _ in range(width)]
                      for _ in range(height)]

    def _draw_edge(self, start: str, end: str, positions: dict) -> None:
        """Draw an edge between two nodes on the canvas"""
        start_x, start_y = positions[start]
        end_x, end_y = positions[end]

        # Account for node decoration width
        prefix, _ = self.options.get_node_decorators(start)
        start_x += len(prefix) + len(str(start)) // 2
        end_x += len(prefix) + len(str(end)) // 2

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
            self.canvas[end_y-1][end_x] = self.options.edge_arrow_down
        elif end_y < start_y:  # Upward arrow
            self.canvas[end_y+1][end_x] = self.options.edge_arrow_up
        else:  # Horizontal arrow
            if end_x > start_x:
                self.canvas[end_y][end_x-1] = self.options.edge_arrow
            else:
                self.canvas[end_y][start_x-1] = '<'
    def render(self) -> str:
        """
        Render the graph as ASCII art.

        Returns:
            String containing the ASCII representation of the graph
        """
        # Calculate layout
        positions, width, height = self.layout_manager.calculate_layout()

        # Handle empty graph
        if not positions:
            return ""

        self._init_canvas(width, height)

        # Draw edges first (so nodes will overlay them)
        for start, end in self.graph.edges():
            self._draw_edge(start, end, positions)

        # Draw nodes
        for node, (x, y) in positions.items():
            prefix, suffix = self.options.get_node_decorators(str(node))
            label = f"{prefix}{node}{suffix}"
            for i, char in enumerate(label):
                self.canvas[y][x + i] = char

        # Convert canvas to string, trimming trailing spaces
        return '\n'.join(''.join(row).rstrip() for row in self.canvas)

    @classmethod
    def from_dot(cls, dot_string: str, options: Optional[LayoutOptions] = None) -> 'ASCIIGraphRenderer':
        """
        Create a renderer from a DOT format string.

        Args:
            dot_string: Graph description in DOT format
            options: Optional layout configuration

        Returns:
            ASCIIGraphRenderer instance

        Raises:
            networkx.NetworkXError: If the DOT string cannot be parsed
        """
        G = nx.nx_pydot.from_pydot(pydot.graph_from_dot_data(dot_string))
        if not isinstance(G, nx.DiGraph):
            G = nx.DiGraph(G)
        return cls(G, options)
