"""Layout management for PHART ASCII graph rendering.

This module handles the calculation of node positions and edge routing
for ASCII graph visualization.
"""

from typing import Dict, Tuple, Any, Set, List
import networkx as nx
from .styles import LayoutOptions

class LayoutManager:
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

    def _binary_tree_node_sorter(
        self,
        graph: nx.DiGraph,
        layer: int,
        nodes: Set[str],
        positions: Dict[str, Tuple[int, int]]
    ) -> List[str]:
        """Sort nodes in a layer according to binary tree structure.
        
        Uses edge attributes to determine left/right placement:
        - 'side': 'left' or 'right'
        - 'position': 'left', 'right', 'l', 'r', '0', '1'
        - 'dir': same as position
        - 'child': same as position
        
        Parameters
        ----------
        graph : nx.DiGraph
            The graph being laid out
        layer : int
            Current layer number
        nodes : Set[str]
            Nodes in this layer to sort
        positions : Dict[str, Tuple[int, int]]
            Already-computed positions for previous layers
            
        Returns
        -------
        List[str]
            Sorted list of nodes (left to right)
            
        Examples
        --------
        >>> G = nx.DiGraph()
        >>> G.add_edge('A', 'B', side='left')
        >>> G.add_edge('A', 'C', side='right')
        # B will be positioned left of C under A
        """
        # Group nodes by their parent
        parent_children: Dict[str, Dict[str, Any]] = {}
        orphans = []
        
        for node in nodes:
            # Find parents (predecessors that are already positioned)
            parents = [p for p in graph.predecessors(node) if p in positions]
            
            if not parents:
                orphans.append(node)
                continue
            
            # For binary tree, should have exactly one parent
            # If multiple parents exist, use the first one
            parent = parents[0]
            
            if parent not in parent_children:
                parent_children[parent] = {'left': None, 'right': None, 'other': []}
            
            # Check edge attributes for side information
            edge_data = graph.get_edge_data(parent, node)
            side = None
            
            if edge_data:
                # Check common attribute names for left/right designation
                side = (edge_data.get('side') or 
                       edge_data.get('position') or 
                       edge_data.get('dir') or
                       edge_data.get('child'))
            
            if side:
                side_str = str(side).lower()
                if side_str in ['left', 'l', '0']:
                    if parent_children[parent]['left'] is not None:
                        # Already have a left child, add to other
                        parent_children[parent]['other'].append(node)
                    else:
                        parent_children[parent]['left'] = node
                elif side_str in ['right', 'r', '1']:
                    if parent_children[parent]['right'] is not None:
                        # Already have a right child, add to other
                        parent_children[parent]['other'].append(node)
                    else:
                        parent_children[parent]['right'] = node
                else:
                    parent_children[parent]['other'].append(node)
            else:
                # No side specified - add to other list
                parent_children[parent]['other'].append(node)
        
        # Build result by processing parents left to right
        result = []
        
        # Sort parents by their x position (left to right)
        sorted_parents = sorted(parent_children.keys(), 
                               key=lambda p: positions[p][0])
        
        for parent in sorted_parents:
            group = parent_children[parent]
            
            # Add left child first
            if group['left'] is not None:
                result.append(group['left'])
            
            # Add unspecified children in middle (alphabetically sorted)
            result.extend(sorted(group['other']))
            
            # Add right child last
            if group['right'] is not None:
                result.append(group['right'])
        
        # Add orphan nodes at the end (alphabetically sorted)
        result.extend(sorted(orphans))
        
        return result

    def _calculate_node_importance(self, graph: nx.DiGraph, node: Any) -> float:
        """
        Calculate node importance based on multiple factors.

        Higher score = more important node that should be positioned prominently.
        Factors:
        - Degree centrality (both in and out)
        - Number of bidirectional relationships
        - Position in any cycles
        """
        # Get basic degree information
        in_degree = graph.in_degree(node)
        out_degree = graph.out_degree(node)

        # Count bidirectional relationships
        bidir_count = sum(
            1 for nbr in graph.neighbors(node) if graph.has_edge(nbr, node)
        )

        # Calculate score based on:
        # - Overall connectivity (degrees)
        # - Bidirectional relationships (weighted more heavily)
        # - Balance of in/out edges
        score = (
            in_degree
            + out_degree  # Basic connectivity
            + bidir_count * 2  # Bidirectional relationships (weighted)
            + -abs(in_degree - out_degree)
        )  # Penalize imbalanced in/out

        return score

    def _should_use_vertical_layout(self, graph: nx.DiGraph) -> bool:
        """
        Determine if graph should use vertical layout based on edge density and patterns.

        A vertical layout (one node top, others below) is preferred when:
        - Graph is dense (many edges relative to possible edges)
        - Has significant bidirectional relationships
        """
        if len(graph) != 3:
            return False

        # Calculate edge density
        possible_edges = len(graph) * (len(graph) - 1)  # For directed graph
        actual_edges = len(graph.edges())
        density = actual_edges / possible_edges

        # Count bidirectional relationships
        bidir_count = (
            sum(1 for u, v in graph.edges() if graph.has_edge(v, u)) // 2
        )  # Divide by 2 as each bidir edge is counted twice

        # Use vertical layout if:
        # - Dense (>50% of possible edges) OR
        # - Has multiple bidirectional relationships
        return density > 0.5 or bidir_count > 1

    def _layout_vertical(
        self, graph: nx.DiGraph, spacing: int
    ) -> Dict[str, Tuple[int, int]]:
        """
        Layout graph vertically with most important node on top.

        Prioritizes:
        - Edge visibility
        - Minimal crossings
        - Clear bidirectional relationships
        """
        positions = {}
        nodes = list(graph.nodes())

        # Score nodes by importance
        node_scores = {
            node: self._calculate_node_importance(graph, node) for node in nodes
        }

        # Choose top node (highest score)
        top_node = max(nodes, key=lambda n: node_scores[n])

        # Get remaining nodes
        bottom_nodes = [n for n in nodes if n != top_node]

        # Sort bottom nodes by their relationships with top node
        bottom_nodes.sort(
            key=lambda n: (
                graph.has_edge(top_node, n),  # Edges from top
                graph.has_edge(n, top_node),  # Edges to top
                node_scores[n],  # Overall importance
            ),
            reverse=True,
        )

        # Calculate node widths
        widths = {node: self._get_node_width(str(node)) for node in nodes}

        # Calculate total width needed
        bottom_width = widths[bottom_nodes[0]] + widths[bottom_nodes[1]] + spacing

        # Position nodes with proper centering
        top_x = (bottom_width - widths[top_node]) // 2

        # Use layer_spacing for vertical distance (like hierarchical layout)
        layer_height = (
            1 if self.options.layer_spacing == 0 else self.options.layer_spacing
        )

        positions[top_node] = (top_x, 0)

        # Position bottom nodes using consistent layer height
        current_x = 0
        positions[bottom_nodes[0]] = (current_x, layer_height)
        current_x += widths[bottom_nodes[0]] + spacing
        positions[bottom_nodes[1]] = (current_x, layer_height)

        return positions

    def calculate_layout(self) -> Tuple[Dict[str, Tuple[int, int]], int, int]:
        """Calculate node positions using layout appropriate for graph structure."""
        if not self.graph:
            return {}, 0, 0

        effective_spacing = self.options.get_effective_node_spacing(has_edges=True)

        # For directed graphs with 3 nodes, check if we should use vertical layout
        # Get positions using appropriate layout method
        if (
            isinstance(self.graph, nx.DiGraph)
            and len(self.graph) == 3
            and self._should_use_vertical_layout(self.graph)
        ):
            positions = self._layout_vertical(self.graph, effective_spacing)
        else:
            # Fallback to standard hierarchical layout
            positions = self._layout_hierarchical(self.graph, effective_spacing)

        # Calculate base dimensions from positions
        # Ensure minimum width for node display
        node_widths = [self._get_node_width(str(node)) for node in self.graph.nodes()]
        min_width = max(node_widths) if node_widths else 0

        base_width = max(min_width, max((x for x, _ in positions.values()), default=0))

        # Ensure we have at least enough height for the nodes
        base_height = max(y for _, y in positions.values()) if positions else 0
        if base_height == 0 and positions:  # If we have nodes but no height
            base_height = self.options.layer_spacing  # Use at least one layer of height

        return positions, base_width, base_height

    def _layout_hierarchical(
        self, graph: nx.Graph, spacing: int
    ) -> Dict[str, Tuple[int, int]]:
        """Position nodes in a hierarchical layout preserving layers.

        This is the standard layout for non-triad cases, organizing nodes into
        clear hierarchical layers based on graph structure.
        """
        if graph.is_directed():
            roots = [n for n, d in graph.in_degree() if d == 0]
            if not roots:
                # If no clear root, use node with highest out-degree
                root = max(graph.nodes(), key=lambda n: graph.out_degree(n))
                roots = [root]
        else:
            # For undirected, use degree centrality
            root = max(graph.nodes(), key=lambda n: graph.degree(n))
            roots = [root]

        # Calculate distances from roots to organize layers
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

        # Calculate positions preserving layer structure
        positions = {}
        layer_widths = {}

        # Calculate width needed for each layer
        for layer, nodes in layers.items():
            total_width = sum(self._get_node_width(str(n)) for n in nodes)
            total_spacing = (len(nodes) - 1) * spacing
            layer_widths[layer] = total_width + total_spacing

        max_width = max(layer_widths.values()) if layer_widths else 0

        # Position nodes within their layers
        for layer, nodes in layers.items():
            y = layer * (
                1 if self.options.layer_spacing == 0 else self.options.layer_spacing
            )
            total_width = layer_widths[layer]
            start_x = (max_width - total_width) // 2
            current_x = start_x

            # Sort nodes - use binary tree sorter if enabled, otherwise alphabetical
            if self.options.binary_tree_layout and isinstance(graph, nx.DiGraph):
                sorted_nodes = self._binary_tree_node_sorter(graph, layer, nodes, positions)
            else:
                sorted_nodes = sorted(nodes)

            for node in sorted_nodes:
                positions[node] = (current_x, y)
                current_x += self._get_node_width(str(node)) + spacing

        return (
            positions  # Just return positions, let calculate_layout handle dimensions
        )

    def calculate_canvas_dimensions(
        self, positions: Dict[str, Tuple[int, int]]
    ) -> Tuple[int, int]:
        """Calculate required canvas dimensions based on layout and node decorations."""
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
        final_width = max(
            1, max_node_end + self.options.right_padding + extra_edge_space
        )

        # Calculate height including padding, ensuring minimum height
        max_y = max(y for _, y in positions.values())
        final_height = max(1, max_y + 2)  # Ensure at least height of 1

        return final_width, final_height
