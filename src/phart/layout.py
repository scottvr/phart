"""Layout management for PHART ASCII graph rendering.

This module handles the calculation of node positions and edge routing
for ASCII graph visualization.
"""

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

    def calculate_layout(self) -> Tuple[Dict[str, Tuple[int, int]], int, int]:
        """Calculate node positions using layout appropriate for graph structure."""
        if not self.graph:
            return {}, 0, 0

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

            # Special handling for 3-node cycles
            is_triangle = len(component) == 3 and (
                not self.graph.is_directed()
                or len(list(nx.simple_cycles(subgraph))) > 0
            )

            if is_triangle:
                positions = self._layout_triangle(subgraph)
            else:
                positions = self._layout_hierarchical(subgraph)

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

    def _layout_triangle(self, graph: nx.Graph) -> Dict[str, Tuple[int, int]]:
        """Layout specifically optimized for 3-node graphs."""
        nodes = list(graph.nodes())
        positions = {}

        # Calculate node widths
        widths = {node: self._get_node_width(str(node)) for node in nodes}

        # Calculate total width needed
        total_width = max(
            # Width of top node
            widths[nodes[0]],
            # Width of bottom two nodes plus spacing
            widths[nodes[1]] + self.options.node_spacing + widths[nodes[2]],
        )

        # Center the top node
        center_x = total_width // 2
        positions[nodes[0]] = (center_x - widths[nodes[0]] // 2, 0)

        # Position bottom nodes with even spacing
        left_x = 0
        positions[nodes[1]] = (left_x, 2)

        right_x = total_width - widths[nodes[2]]
        positions[nodes[2]] = (right_x, 2)

        return positions

    def _layout_hierarchical(self, graph: nx.Graph) -> Dict[str, Tuple[int, int]]:
        """Standard hierarchical layout for non-triangle components."""
        if graph.is_directed():
            roots = [n for n, d in graph.in_degree() if d == 0]
            if not roots:  # Handle cycles by picking highest out-degree node
                roots = [max(graph.nodes(), key=lambda n: graph.out_degree(n))]
        else:
            roots = [max(graph.nodes(), key=lambda n: graph.degree(n))]

        # Calculate distances within component
        distances = {}
        for root in roots:
            lengths = nx.single_source_shortest_path_length(graph, root)
            for node, dist in lengths.items():
                distances[node] = min(distances.get(node, dist), dist)

        # Group nodes by layer
        layers = {}
        for node, layer in distances.items():
            if layer not in layers:
                layers[layer] = set()
            layers[layer].add(node)

        # Calculate positions using existing logic
        positions = {}
        layer_widths = {}
        for layer, nodes in layers.items():
            total_width = sum(self._get_node_width(n) for n in nodes)
            spacing = (len(nodes) - 1) * self.options.node_spacing
            layer_widths[layer] = total_width + spacing

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
                current_x += self._get_node_width(node) + self.options.node_spacing

        return positions
