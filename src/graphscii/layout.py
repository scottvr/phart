from typing import Dict, Set, Tuple, List, Optional
from pathlib import Path
import networkx as nx
from .styles import LayoutOptions

class LayoutManager:
    """Handles the calculation of node positions and layout logic"""
    
    def __init__(self, graph: nx.DiGraph, options: LayoutOptions):
        self.graph = graph
        self.options = options
        self.node_positions: Dict[str, Tuple[int, int]] = {}
        self.max_width = 0
        self.max_height = 0
        
    def _get_node_width(self, node: str) -> int:
        """Calculate display width of a node including decorators"""
        prefix, suffix = self.options.get_node_decorators(str(node))
        return len(str(node)) + len(prefix) + len(suffix)
        
    def calculate_layout(self) -> Tuple[Dict[str, Tuple[int, int]], int, int]:
        """
        Calculate node positions using hierarchical layout
        
        Returns:
            Tuple containing:
            - Dictionary of node positions (x, y)
            - Maximum width of the layout
            - Maximum height of the layout
        """
        # Group nodes by layer using longest path from any root
        layers: Dict[int, Set[str]] = {}
        roots = [n for n, d in self.graph.in_degree() if d == 0]
        if not roots:  # Handle cycles by picking arbitrary start
            roots = [list(self.graph.nodes())[0]]
            
        # Calculate longest path to each node
        distances = {}
        for root in roots:
            for node in self.graph.nodes():
                try:
                    length = max(len(p) for p in nx.all_simple_paths(self.graph, root, node))
                    distances[node] = max(distances.get(node, 0), length)
                except nx.NetworkXNoPath:
                    continue
                    
        # Group nodes by their layer
        for node, layer in distances.items():
            if layer not in layers:
                layers[layer] = set()
            layers[layer].add(node)
            
        # Handle any nodes not reached (disconnected components)
        unreached = set(self.graph.nodes()) - set(distances.keys())
        if unreached:
            max_layer = max(layers.keys()) if layers else 0
            layers[max_layer + 1] = unreached
            
        # Calculate positions
        self.max_height = (max(layers.keys()) + 1) * (self.options.layer_spacing + 1)
        
        # Calculate required width based on node labels
        layer_widths = {}
        for layer, nodes in layers.items():
            total_node_width = sum(self._get_node_width(n) for n in nodes)
            min_spacing = (len(nodes) - 1) * self.options.node_spacing
            layer_widths[layer] = total_node_width + min_spacing
            
        self.max_width = max(layer_widths.values()) + 4  # Add margins
        
        # Assign positions
        for layer, nodes in layers.items():
            y = layer * (self.options.layer_spacing + 1)
            total_width = layer_widths[layer]
            start_x = (self.max_width - total_width) // 2
            current_x = start_x
            
            for node in sorted(nodes):  # Sort for consistent layout
                self.node_positions[node] = (current_x, y)
                current_x += self._get_node_width(node) + self.options.node_spacing
                
        return self.node_positions, self.max_width, self.max_height
