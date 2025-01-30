"""Layout management for PHART ASCII graph rendering.

This module handles the calculation of node positions and edge routing
for ASCII graph visualization.
"""
# src path: src\phart\layout.py

from typing import Dict, Tuple

import networkx as nx  # type: ignore

from .styles import LayoutOptions


class LayoutManager:
    """
    Manages the calculation of node positions and layout logic.

    This class handles the conversion of graph structure into a
    2D coordinate system suitable for ASCII rendering.

    Parameters
    ----------
    graph : NetworkX graph
        Graph to lay out
    options : LayoutOptions
        Layout configuration

    Notes
    -----
    The layout algorithm uses a hierarchical approach optimized for
    directed graphs and trees. For undirected graphs, a root node
    is chosen based on degree centrality.
    """

    def __init__(self, graph: nx.Graph, options: LayoutOptions):
        self.graph = graph
        self.options = options
        self.node_positions: Dict[str, Tuple[int, int]] = {}
        self.max_width = 0
        self.max_height = 0

    def calculate_canvas_dimensions(
        self, positions: Dict[str, Tuple[int, int]]
    ) -> Tuple[int, int]:
        """
        Calculate required canvas dimensions based on layout and node decorations.

        Args:
            positions: Dictionary of node positions

        Returns:
            Tuple of (width, height) for the canvas
        """
        if not positions:
            return 0, 0

        # Calculate width needed for nodes and decorations
        max_node_end = 0
        for node, (x, y) in positions.items():
            node_width = sum(
                len(part) for part in self.options.get_node_decorators(str(node))
            ) + len(str(node))
            node_end = x + node_width
            max_node_end = max(max_node_end, node_end)

        # Add configured padding plus extra space for edge decorators
        extra_edge_space = (
            6 if self.options.use_ascii else 4
        )  # ASCII needs more space for markers
        final_width = max_node_end + self.options.right_padding + extra_edge_space

        # Calculate height including padding
        max_y = max(y for _, y in positions.values())
        final_height = max_y + 2  # Add minimal vertical padding

        return final_width, final_height

    def _get_node_width(self, node: str) -> int:
        """Calculate display width of a node including decorators.

        Parameters
        ----------
        node : str
            Node identifier

        Returns
        -------
        int
            Total width of node when rendered
        """
        prefix, suffix = self.options.get_node_decorators(node)
        return len(str(node)) + len(str(prefix)) + len(str(suffix))

    def _calculate_minimum_x_position(self, node_width: int) -> int:
        """Calculate minimum x position that allows for edge drawing."""
        return 2 if not self.options.use_ascii else 3  # More space for ASCII markers

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

    def calculate_layout(self) -> Tuple[Dict[str, Tuple[int, int]], int, int]:
        """Calculate node positions using layout appropriate for graph structure."""
        if not self.graph:
            return {}, 0, 0

        # Use the effective node spacing considering edges
        effective_spacing = self.options.get_effective_node_spacing(has_edges=True)

        # Group nodes by connected component
        components = list(
            nx.weakly_connected_components(self.graph)
            if self.graph.is_directed()
            else nx.connected_components(self.graph)
        )

        component_layouts = {}
        max_width = 0
        total_height = 0

        for component in components:
            subgraph = self.graph.subgraph(component)

            # Special handling for triangular components
            is_triangle = len(component) == 3 and (
                not self.graph.is_directed()
                or len(list(nx.simple_cycles(subgraph))) > 0
            )

            if is_triangle and self.options.preserve_triangle_shape:
                positions = self._layout_triangle(subgraph, effective_spacing)
            else:
                positions = self._layout_hierarchical(subgraph, effective_spacing)

            # Get component dimensions
            component_width = (
                max(x for x, _ in positions.values()) + self.options.right_padding
            )
            component_height = max(y for _, y in positions.values()) + 2

            # Update layout dimensions
            max_width = max(max_width, component_width)

            # Shift positions to account for previous components and left padding
            shifted_positions = {
                node: (x + self.options.left_padding, y + total_height)
                for node, (x, y) in positions.items()
            }

            component_layouts.update(shifted_positions)
            total_height += component_height + self.options.layer_spacing

        return component_layouts, max_width, total_height

    def _is_true_triangle(self, graph: nx.Graph) -> bool:
        """
        Determine if the graph should use a triangular layout.
        """
        if len(graph) != 3:
            return False

        # Always use triangle layout for complete graphs (triad type 300)
        if len(graph.edges()) == 6:
            return True

        if graph.is_directed():
            cycles = list(nx.simple_cycles(graph))
            if cycles and len(cycles[0]) == 3:
                return True

            # Use triangle for balanced patterns
            in_degrees = [d for _, d in graph.in_degree()]
            out_degrees = [d for _, d in graph.out_degree()]
            degree_diff = max(abs(i - o) for i, o in zip(in_degrees, out_degrees))
            if degree_diff <= 1:
                return True

        return False

    def _is_true_triangle(self, graph: nx.Graph) -> bool:
        """
        Determine if the graph should use a triangular layout.
        """
        if len(graph) != 3:
            return False

        # Always use triangle layout for complete graphs (triad type 300)
        if len(graph.edges()) == 6:
            return True

        if graph.is_directed():
            cycles = list(nx.simple_cycles(graph))
            if cycles and len(cycles[0]) == 3:
                return True

            # Use triangle for balanced patterns
            in_degrees = [d for _, d in graph.in_degree()]
            out_degrees = [d for _, d in graph.out_degree()]
            degree_diff = max(abs(i - o) for i, o in zip(in_degrees, out_degrees))
            if degree_diff <= 1:
                return True

        return False

    def _layout_triangle(
        self, graph: nx.Graph, spacing: int
    ) -> Dict[str, Tuple[int, int]]:
        """
        Position nodes in an equilateral triangle pattern.
        Fully respects user's spacing preferences.
        """
        nodes = sorted(graph.nodes())
        positions = {}

        # Use exactly the spacing the user specified
        width = spacing * 3  # Total width of the triangle base
        height = spacing * 2  # Height of the triangle

        # Position nodes
        top_node = nodes[0]
        left_node = nodes[1]
        right_node = nodes[2]

        positions[top_node] = (width // 2, 0)  # Top center
        positions[left_node] = (0, height)  # Bottom left
        positions[right_node] = (width, height)  # Bottom right

        return positions

    def _layout_hierarchical(
        self, graph: nx.Graph, spacing: int
    ) -> Dict[str, Tuple[int, int]]:
        """
        Position nodes in a hierarchical layout.
        Fully respects user's spacing preferences.
        """
        positions = {}

        if not graph.is_directed():
            return super()._layout_hierarchical(graph, spacing)

        # For directed graphs, determine natural hierarchy
        in_degrees = dict(graph.in_degree())
        out_degrees = dict(graph.out_degree())

        # Find root nodes (more outgoing than incoming edges)
        roots = [n for n in graph.nodes() if out_degrees[n] > in_degrees[n]]

        if not roots:
            max_out = max(out_degrees.values())
            roots = [n for n, d in out_degrees.items() if d == max_out]

        # Position root nodes at top
        root_x = spacing
        for root in roots:
            positions[root] = (root_x, 0)
            root_x += spacing * 2

        # Position remaining nodes
        remaining = set(graph.nodes()) - set(roots)
        if remaining:
            y_pos = spacing * 2
            x_pos = 0
            for node in remaining:
                positions[node] = (x_pos, y_pos)
                x_pos += spacing * 2

        return positions
