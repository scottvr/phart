"""Layout management for PHART ASCII graph rendering.

This module handles the calculation of node positions and edge routing
for ASCII graph visualization.
"""
# src path: src\phart\layout.py

from typing import Dict, Tuple, Set

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

        # Calculate max node width for spacing adjustment
        max_node_width = max(
            self._get_node_width(str(node)) for node in self.graph.nodes()
        )
        # Base spacing is max(configured spacing, node width)
        effective_spacing = max(self.options.node_spacing, max_node_width)

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

            if is_triangle:
                positions = self._layout_triangle(subgraph, effective_spacing)
            else:
                positions = self._layout_hierarchical(subgraph, effective_spacing)

            # Get component dimensions
            component_width = max(x for x, _ in positions.values()) + 4
            component_height = max(y for _, y in positions.values()) + 2

            # Update layout dimensions
            max_width = max(max_width, component_width)

            # Shift positions to account for previous components
            shifted_positions = {
                node: (x, y + total_height) for node, (x, y) in positions.items()
            }

            component_layouts.update(shifted_positions)
            total_height += component_height + self.options.layer_spacing

        return component_layouts, max_width, total_height

    def _layout_hierarchical(
        self, graph: nx.Graph, spacing: int
    ) -> Dict[str, Tuple[int, int]]:
        """Standard hierarchical layout with adjusted spacing."""
        if graph.is_directed():
            roots = [n for n, d in graph.in_degree() if d == 0]
            if not roots:
                roots = [max(graph.nodes(), key=lambda n: graph.out_degree(n))]
        else:
            roots = [max(graph.nodes(), key=lambda n: graph.degree(n))]

        # Calculate distances within component
        distances: Dict[str, int] = {}
        for root in roots:
            lengths = nx.single_source_shortest_path_length(graph, root)
            for node, dist in lengths.items():
                distances[node] = min(distances.get(node, dist), dist)

        # Group nodes by layer
        layers: Dict[int, Set[str]] = {}
        for node, layer in distances.items():
            if layer not in layers:
                layers[layer] = set()
            layers[layer].add(node)

        # Calculate positions
        positions = {}
        layer_widths = {}

        for layer, nodes in layers.items():
            total_width = sum(self._get_node_width(str(n)) for n in nodes)
            # Use provided spacing parameter instead of self.options.node_spacing
            total_spacing = (len(nodes) - 1) * spacing
            layer_widths[layer] = total_width + total_spacing

        max_width = max(layer_widths.values()) if layer_widths else 0

        for layer, nodes in layers.items():
            y = layer * (
                1 if self.options.layer_spacing == 0 else self.options.layer_spacing
            )
            total_width = layer_widths[layer]
            start_x = (max_width - total_width) // 2
            current_x = start_x

            for node in sorted(nodes):
                positions[node] = (current_x, y)
                current_x += self._get_node_width(str(node)) + spacing

        return positions

    def _layout_triangle(
        self, graph: nx.Graph, spacing: int
    ) -> Dict[str, Tuple[int, int]]:
        """Triangle layout with adjusted spacing, respecting cycle order."""
        positions = {}

        # Get cycle order if directed
        if graph.is_directed():
            cycles = list(nx.simple_cycles(graph))
            if cycles:
                nodes = cycles[0]  # Use first cycle's order
            else:
                nodes = list(graph.nodes())
        else:
            nodes = list(graph.nodes())

        # Calculate node widths
        widths = {node: self._get_node_width(str(node)) for node in nodes}

        # Calculate total width needed including spacing
        total_width = max(
            widths[nodes[0]],  # Width of top node
            widths[nodes[1]]
            + spacing
            + widths[nodes[2]],  # Width of bottom nodes plus spacing
        )

        # Position first node in cycle at top center
        center_x = total_width // 2
        positions[nodes[0]] = (center_x - widths[nodes[0]] // 2, 0)

        # Position second node at bottom left
        left_x = 0
        positions[nodes[1]] = (left_x, 2)

        # Position third node at bottom right
        right_x = total_width - widths[nodes[2]]
        positions[nodes[2]] = (right_x, 2)

        # Debug the layout
        #        print(f"DEBUG: Triangle cycle order: {nodes}")
        #        print(f"DEBUG: Triangle positions: {positions}")

        return positions
