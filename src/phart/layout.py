"""Layout management for PHART ASCII graph rendering.

This module handles the calculation of node positions and edge routing
for ASCII graph visualization.
"""

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
        prefix, suffix = self.options.get_node_decorators(str(node))
        return len(str(node)) + len(prefix) + len(suffix)

    def calculate_layout(self) -> Tuple[Dict[str, Tuple[int, int]], int, int]:
        """
        Calculate node positions using hierarchical layout.

        Returns
        -------
        positions : dict
            Dictionary mapping nodes to (x, y) coordinates
        width : int
            Maximum width of the layout
        height : int
            Maximum height of the layout

        Notes
        -----
        The layout algorithm:
        1. Groups nodes into layers based on path length from roots
        2. Within each layer, spaces nodes evenly
        3. Centers each layer horizontally
        4. Maintains consistent vertical spacing between layers
        """

        if not self.graph:
            return {}, 0, 0

        # Group nodes by connected component
        components = list(
            nx.weakly_connected_components(self.graph)
            if self.graph.is_directed()
            else nx.connected_components(self.graph)
        )

        # Handle each component separately
        component_layouts = {}
        max_width = 0
        total_height = 0

        for component in components:
            subgraph = self.graph.subgraph(component)

            # Find root nodes for this component
            if self.graph.is_directed():
                roots = [n for n, d in subgraph.in_degree() if d == 0]
            else:
                roots = [max(subgraph.nodes(), key=lambda n: subgraph.degree(n))]

            if not roots:  # Handle cycles by picking arbitrary start
                roots = [next(iter(subgraph.nodes()))]

            # Calculate distances within component
            distances: Dict[int, int] = {}
            for root in roots:
                lengths = nx.single_source_shortest_path_length(subgraph, root)
                for node, dist in lengths.items():
                    distances[node] = max(distances.get(node, 0), dist)

            # Layout this component
            layers: Dict[int, Set[str]] = {}
            for node, layer in distances.items():
                if layer not in layers:
                    layers[layer] = set()
                layers[layer].add(node)

            # Calculate component dimensions
            layer_widths = {}
            for layer, nodes in layers.items():
                total_width = sum(self._get_node_width(n) for n in nodes)
                min_spacing = (len(nodes) - 1) * self.options.node_spacing
                layer_widths[layer] = total_width + min_spacing

            component_width = max(layer_widths.values()) + 4  # Add margins
            component_height = (max(layers.keys()) + 1) * (
                self.options.layer_spacing + 1
            )
            max_width = max(max_width, component_width)

            # Position nodes in this component
            positions = {}
            for layer, nodes in layers.items():
                y = layer * (self.options.layer_spacing + 1) + total_height
                total_width = layer_widths[layer]
                start_x = (max_width - total_width) // 2
                current_x = start_x

                for node in sorted(nodes):  # Sort for consistent layout
                    positions[node] = (current_x, y)
                    current_x += self._get_node_width(node) + self.options.node_spacing

            component_layouts.update(positions)
            total_height += component_height + self.options.layer_spacing

        return component_layouts, max_width, total_height
