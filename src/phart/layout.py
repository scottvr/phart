"""Layout management for PHART ASCII graph rendering.

This module handles the calculation of node positions and edge routing
for ASCII graph visualization.
"""

from typing import Dict, Tuple, Any, Set, List, Optional
import math
from collections import deque
import networkx as nx
from .styles import LayoutOptions


class LayoutManager:
    def __init__(self, graph: nx.DiGraph, options: LayoutOptions):
        self.graph = graph
        self.options = options
        self.node_positions: Dict[str, Tuple[int, int]] = {}
        self.max_width = 0
        self.max_height = 0
        self._widest_node_text_width = (
            max(
                (
                    len(self.options.get_node_text(self._get_node_display_text(node)))
                    for node in self.graph.nodes()
                ),
                default=0,
            )
            if self.options.uniform
            else None
        )

    @staticmethod
    def _normalize_label_value(label: Any) -> str:
        """Normalize node labels for single-line display."""
        text = str(label).strip()
        if len(text) >= 2 and text[0] == text[-1] and text[0] in {"'", '"'}:
            text = text[1:-1]
        text = text.replace("\r\n", " ").replace("\n", " ")
        return text.strip()

    def _get_node_display_text(self, node: Any) -> str:
        """Resolve display text for a node key."""
        if self.options.use_labels:
            label = self.graph.nodes[node].get("label") if node in self.graph else None
            if label is not None:
                normalized = self._normalize_label_value(label)
                if normalized:
                    return normalized
        return str(node)

    def _get_node_height(self) -> int:
        """Get rendered node height for current options."""
        return self.options.get_node_height()

    def _get_layer_step(self) -> int:
        """Get vertical step between layer top rows."""
        # Preserve prior semantics for 1-line nodes while expanding for boxed nodes.
        return max(1, self.options.layer_spacing) + self._get_node_height() - 1

    def _get_node_width(self, node: Any) -> int:
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
        width, _ = self.options.get_node_dimensions(
            self._get_node_display_text(node),
            widest_text_width=self._widest_node_text_width,
        )
        return width

    def _node_rect(
        self, node: Any, x: int, y: int, node_height: Optional[int] = None
    ) -> Tuple[int, int, int, int]:
        """Get node rectangle as (left, top, right, bottom)."""
        width = self._get_node_width(node)
        h = node_height if node_height is not None else self._get_node_height()
        return (x, y, x + width - 1, y + h - 1)

    @staticmethod
    def _rectangles_overlap(
        a: Tuple[int, int, int, int], b: Tuple[int, int, int, int]
    ) -> bool:
        """Return True if two axis-aligned rectangles overlap."""
        return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])

    def _normalize_positions_to_origin(
        self, positions: Dict[Any, Tuple[int, int]]
    ) -> Dict[str, Tuple[int, int]]:
        """Shift positions so minimum x/y start at zero."""
        if not positions:
            return {}

        min_x = min(x for x, _ in positions.values())
        min_y = min(y for _, y in positions.values())
        if min_x >= 0 and min_y >= 0:
            return {node: (int(x), int(y)) for node, (x, y) in positions.items()}

        return {
            node: (int(x - min_x), int(y - min_y)) for node, (x, y) in positions.items()
        }

    def _binary_tree_node_sorter(
        self,
        graph: nx.DiGraph,
        layer: int,
        nodes: Set[str],
        positions: Dict[str, Tuple[int, int]],
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
                parent_children[parent] = {"left": None, "right": None, "other": []}

            # Check edge attributes for side information
            edge_data = graph.get_edge_data(parent, node)
            side = None

            if edge_data:
                # Check common attribute names for left/right designation
                side = (
                    edge_data.get("side")
                    or edge_data.get("position")
                    or edge_data.get("dir")
                    or edge_data.get("child")
                )

            if side:
                side_str = str(side).lower()
                if side_str in ["left", "l", "0"]:
                    if parent_children[parent]["left"] is not None:
                        # Already have a left child, add to other
                        parent_children[parent]["other"].append(node)
                    else:
                        parent_children[parent]["left"] = node
                elif side_str in ["right", "r", "1"]:
                    if parent_children[parent]["right"] is not None:
                        # Already have a right child, add to other
                        parent_children[parent]["other"].append(node)
                    else:
                        parent_children[parent]["right"] = node
                else:
                    parent_children[parent]["other"].append(node)
            else:
                # No side specified - add to other list
                parent_children[parent]["other"].append(node)

        # Build result by processing parents left to right
        result = []

        # Sort parents by their x position (left to right)
        sorted_parents = sorted(parent_children.keys(), key=lambda p: positions[p][0])

        for parent in sorted_parents:
            group = parent_children[parent]

            # Add left child first
            if group["left"] is not None:
                result.append(group["left"])

            # Add unspecified children in middle (alphabetically sorted)
            result.extend(sorted(group["other"]))

            # Add right child last
            if group["right"] is not None:
                result.append(group["right"])

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

        return float(score)

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
        widths = {node: self._get_node_width(node) for node in nodes}

        # Calculate total width needed
        bottom_width = widths[bottom_nodes[0]] + widths[bottom_nodes[1]] + spacing

        # Position nodes with proper centering
        top_x = (bottom_width - widths[top_node]) // 2

        # Use layer spacing plus node height for vertical distance.
        layer_height = self._get_layer_step()

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
        strategy = self.options.layout_strategy

        if strategy == "bfs":
            positions = self._layout_bfs(self.graph, effective_spacing)
        elif strategy == "bipartite":
            positions = self._layout_bipartite(self.graph, effective_spacing)
        elif strategy == "circular":
            positions = self._layout_circular(self.graph, effective_spacing)
        elif strategy == "planar":
            positions = self._layout_planar(self.graph, effective_spacing)
        elif strategy == "kamada_kawai":
            positions = self._layout_kamada_kawai(self.graph, effective_spacing)
        elif strategy == "spring":
            positions = self._layout_spring(self.graph, effective_spacing)
        elif strategy == "arf":
            positions = self._layout_arf(self.graph, effective_spacing)
        elif strategy == "spiral":
            positions = self._layout_spiral(self.graph, effective_spacing)
        elif strategy == "shell":
            positions = self._layout_shell(self.graph, effective_spacing)
        elif strategy == "random":
            positions = self._layout_random(self.graph, effective_spacing)
        elif strategy == "multipartite":
            positions = self._layout_multipartite(self.graph, effective_spacing)
        else:
            # Auto mode preserves the original heuristics.
            if (
                isinstance(self.graph, nx.DiGraph)
                and len(self.graph) == 3
                and self._should_use_vertical_layout(self.graph)
            ):
                positions = self._layout_vertical(self.graph, effective_spacing)
            else:
                positions = self._layout_hierarchical(self.graph, effective_spacing)

        # Apply flow direction transformation
        positions = self._transform_positions(positions)

        # Calculate base dimensions from full node bounds.
        base_width = max(
            (x + self._get_node_width(node) - 1 for node, (x, _) in positions.items()),
            default=0,
        )
        node_height = self._get_node_height()
        base_height = max(
            (y + node_height - 1 for _, y in positions.values()), default=0
        )

        return positions, base_width, base_height

    def _transform_positions(
        self, positions: Dict[str, Tuple[int, int]]
    ) -> Dict[str, Tuple[int, int]]:
        """Transform positions based on flow direction.

        Transforms coordinates from the default DOWN orientation to the
        requested flow direction.

        Args:
            positions: Node positions in DOWN orientation

        Returns:
            Transformed positions for the desired flow direction
        """
        from .styles import FlowDirection

        if not positions:
            return positions

        # DOWN is the default - no transformation needed
        if self.options.flow_direction == FlowDirection.DOWN:
            return positions

        # Find bounding box
        max_y = max(y for _, y in positions.values())

        transformed = {}

        if self.options.flow_direction == FlowDirection.UP:
            # Flip Y-axis: put root at bottom instead of top
            for node, (x, y) in positions.items():
                transformed[node] = (x, max_y - y)

        elif self.options.flow_direction == FlowDirection.RIGHT:
            # Rotate 90 deg clockwise: (x, y) -> (y, x)
            # Root moves from top to left
            for node, (x, y) in positions.items():
                transformed[node] = (y, x)

        elif self.options.flow_direction == FlowDirection.LEFT:
            # Rotate 90 deg counter-clockwise: (x, y) -> (max_y - y, x)
            # Root moves from top to right
            for node, (x, y) in positions.items():
                transformed[node] = (max_y - y, x)

        return transformed

    def _get_subtree_width(
        self,
        graph: nx.DiGraph,
        node: Any,
        spacing: int,
        cache: Dict,
    ) -> int:
        """Recursively compute the minimum x-width a subtree needs.

        A leaf node needs exactly its own display width.
        An internal node needs the sum of its children's subtree widths plus
        the spacing gaps between them, with a minimum of its own display width
        so the parent label is never wider than its allocated slot.
        """
        if node in cache:
            return int(cache[node])

        children = list(graph.successors(node))
        if not children:
            w = self._get_node_width(node)
        else:
            total = sum(
                self._get_subtree_width(graph, c, spacing, cache) for c in children
            )
            total += spacing * (len(children) - 1)
            w = max(total, self._get_node_width(node))

        cache[node] = w
        return w

    def _layout_subtree(
        self,
        graph: nx.DiGraph,
        node: Any,
        x_left: int,
        y: int,
        spacing: int,
        subtree_widths: Dict,
        positions: Dict,
        layer_height: int,
    ) -> None:
        """Recursively assign positions so each node is centred over its subtree."""
        my_width = self._get_node_width(node)
        slot_width = subtree_widths[node]

        # Centre the node label within its allocated slot
        node_x = x_left + (slot_width - my_width) // 2
        positions[node] = (node_x, y)

        children = list(graph.successors(node))
        if not children:
            return

        # Sort children: respect left/right attributes when binary_tree_layout
        # is enabled, otherwise sort alphabetically.
        if self.options.binary_tree_layout:
            children_sorted = self._binary_tree_node_sorter(
                graph, y // layer_height, set(children), positions
            )
        else:
            children_sorted = sorted(children, key=lambda n: str(n))

        # Assign each child its slice of the horizontal space
        cx = x_left
        for child in children_sorted:
            child_slot = subtree_widths[child]
            self._layout_subtree(
                graph,
                child,
                cx,
                y + layer_height,
                spacing,
                subtree_widths,
                positions,
                layer_height,
            )
            cx += child_slot + spacing

    def _layout_hierarchical(
        self, graph: nx.DiGraph, spacing: int
    ) -> Dict[str, Tuple[int, int]]:
        """Position nodes in a hierarchical layout preserving layers.

        This is the standard layout for non-triad cases, organizing nodes into
        clear hierarchical layers based on graph structure.

        When binary_tree_layout=True and the graph is a directed tree, uses a
        subtree-aware (Reingold-Tilford-style) layout so that each node's
        children are placed within that node's exclusive horizontal territory.
        This prevents edge routing for one subtree from visually passing through
        a sibling subtree.
        """
        if graph.is_directed():
            roots = [n for n, d in graph.in_degree() if d == 0]
            if not roots:
                root = max(graph.nodes(), key=lambda n: graph.out_degree(n))
                roots = [root]
        else:
            root = max(graph.nodes(), key=lambda n: graph.degree(n))
            roots = [root]

        layer_height = self._get_layer_step()

        # Subtree-aware layout is great for trees, but expands badly on DAGs
        # with shared descendants (multi-parent nodes). Use it only for
        # directed acyclic graphs where each node has at most one parent and
        # the graph is a single connected component.
        is_acyclic = graph.is_directed() and nx.is_directed_acyclic_graph(graph)
        component_count = (
            nx.number_weakly_connected_components(graph)
            if graph.is_directed()
            else nx.number_connected_components(graph)
        )
        is_parent_unique = (
            is_acyclic
            and all(deg <= 1 for _, deg in graph.in_degree())
            and component_count == 1
        )
        if not is_parent_unique:
            return self._layout_layered_fallback(
                graph, spacing, layer_height, layer_mode="auto"
            )

        # Subtree-aware (Reingold-Tilford-style) layout.
        #
        # Every node is centred over its own subtree's horizontal territory,
        # guaranteeing that sibling subtrees never share x-space and edge
        # routing between layers cannot be confused with sibling connections.
        #
        # For directed graphs with a single root this is exact.
        # For multi-root directed graphs or undirected graphs each root gets
        # its own subtree block laid out left-to-right.
        # For DAGs where a node has multiple parents the node's subtree width
        # may be over-counted (once per parent path), resulting in extra
        # horizontal whitespace — a harmless trade-off for unambiguous routing.
        #
        # binary_tree_layout controls only child *sort order*:
        #   True  → respect 'side'/'position'/'dir'/'child' edge attributes
        #   False → alphabetical

        subtree_widths: Dict = {}
        for root in roots:
            self._get_subtree_width(graph, root, spacing, subtree_widths)

        positions: Dict[str, Tuple[int, int]] = {}
        cx = 0
        for root in roots:
            self._layout_subtree(
                graph, root, cx, 0, spacing, subtree_widths, positions, layer_height
            )
            cx += subtree_widths[root] + spacing

        return positions

        # (The old centred-layer layout has been superseded by the subtree-aware
        #  layout above and is intentionally removed.)

    def _layout_bfs(
        self, graph: nx.DiGraph, spacing: int
    ) -> Dict[str, Tuple[int, int]]:
        """Layer nodes by BFS depth regardless of DAG status."""
        layer_height = self._get_layer_step()
        return self._layout_layered_fallback(
            graph, spacing, layer_height, layer_mode="bfs"
        )

    @staticmethod
    def _classify_side_value(value: Any) -> Optional[int]:
        """Map edge side hints to bipartite partition index (0=left, 1=right)."""
        if value is None:
            return None
        side_str = str(value).strip().lower()
        if side_str in {"left", "l", "0"}:
            return 0
        if side_str in {"right", "r", "1"}:
            return 1
        return None

    def _layout_bipartite(
        self, graph: nx.DiGraph, spacing: int
    ) -> Dict[str, Tuple[int, int]]:
        """Two-column layout using side hints first, then bipartite inference."""
        if not graph.nodes():
            return {}

        side_scores: Dict[Any, int] = {node: 0 for node in graph.nodes()}
        for u, v, data in graph.edges(data=True):
            side_hint = (
                data.get("side")
                or data.get("position")
                or data.get("dir")
                or data.get("child")
            )
            cls = self._classify_side_value(side_hint)
            if cls is None:
                continue
            if cls == 0:
                side_scores[v] -= 2
                side_scores[u] += 1
            else:
                side_scores[v] += 2
                side_scores[u] -= 1

        left_nodes: Set[Any] = {n for n, s in side_scores.items() if s < 0}
        right_nodes: Set[Any] = {n for n, s in side_scores.items() if s > 0}
        unresolved = set(graph.nodes()) - left_nodes - right_nodes

        if unresolved:
            try:
                colors = nx.algorithms.bipartite.color(nx.Graph(graph))
            except nx.NetworkXError:
                colors = {}
            for node in list(unresolved):
                if node not in colors:
                    continue
                if colors[node] == 0:
                    left_nodes.add(node)
                else:
                    right_nodes.add(node)
                unresolved.discard(node)

        if unresolved:
            bfs_layers = self._build_layers_bfs(nx.DiGraph(graph))
            depth_map: Dict[Any, int] = {}
            for depth, layer in enumerate(bfs_layers):
                for node in layer:
                    depth_map[node] = depth
            for node in list(unresolved):
                depth = depth_map.get(node, 0)
                if depth % 2 == 0:
                    left_nodes.add(node)
                else:
                    right_nodes.add(node)
                unresolved.discard(node)

        if not left_nodes or not right_nodes:
            all_nodes = sorted(graph.nodes(), key=lambda n: str(n))
            midpoint = max(1, len(all_nodes) // 2)
            left_nodes = set(all_nodes[:midpoint])
            right_nodes = set(all_nodes[midpoint:])

        left_ordered = sorted(left_nodes, key=lambda n: str(n))
        right_ordered = sorted(right_nodes, key=lambda n: str(n))

        left_col_width = max((self._get_node_width(n) for n in left_ordered), default=1)
        right_col_width = max(
            (self._get_node_width(n) for n in right_ordered), default=1
        )
        column_gap = max(spacing, self.options.get_effective_node_spacing(True))
        x_left = 0
        x_right = left_col_width + column_gap
        layer_height = self._get_layer_step()

        max_rows = max(len(left_ordered), len(right_ordered), 1)
        left_start_y = ((max_rows - len(left_ordered)) * layer_height) // 2
        right_start_y = ((max_rows - len(right_ordered)) * layer_height) // 2

        positions: Dict[Any, Tuple[int, int]] = {}
        for idx, node in enumerate(left_ordered):
            x = x_left + (left_col_width - self._get_node_width(node)) // 2
            positions[node] = (x, left_start_y + (idx * layer_height))

        for idx, node in enumerate(right_ordered):
            x = x_right + (right_col_width - self._get_node_width(node)) // 2
            positions[node] = (x, right_start_y + (idx * layer_height))

        return self._normalize_positions_to_origin(positions)

    def _layout_circular(
        self, graph: nx.DiGraph, spacing: int
    ) -> Dict[str, Tuple[int, int]]:
        """Place nodes around a circle and nudge to avoid node overlaps."""
        nodes = sorted(graph.nodes(), key=lambda n: str(n))
        if not nodes:
            return {}

        node_height = self._get_node_height()
        layer_height = self._get_layer_step()
        max_node_width = max((self._get_node_width(n) for n in nodes), default=1)

        node_count = len(nodes)
        circumference_hint = node_count * (max_node_width + spacing + 1)
        radius_x = max(
            int(math.ceil(circumference_hint / (2 * math.pi))), max_node_width
        )
        radius_y = max(layer_height, int(radius_x * 0.7))
        center_x = radius_x + max_node_width
        center_y = radius_y + node_height

        positions: Dict[Any, Tuple[int, int]] = {}
        placed_rects: List[Tuple[int, int, int, int]] = []

        for idx, node in enumerate(nodes):
            theta = (-math.pi / 2) + ((2 * math.pi * idx) / max(node_count, 1))
            node_width = self._get_node_width(node)
            proposed_x = int(round(center_x + (radius_x * math.cos(theta)))) - (
                node_width // 2
            )
            proposed_y = int(round(center_y + (radius_y * math.sin(theta))))

            candidate_x = proposed_x
            candidate_y = proposed_y
            candidate_rect = self._node_rect(
                node, candidate_x, candidate_y, node_height
            )
            while any(
                self._rectangles_overlap(candidate_rect, existing)
                for existing in placed_rects
            ):
                candidate_y += layer_height
                candidate_rect = self._node_rect(
                    node, candidate_x, candidate_y, node_height
                )

            positions[node] = (candidate_x, candidate_y)
            placed_rects.append(candidate_rect)

        return self._normalize_positions_to_origin(positions)

    @staticmethod
    def _to_ordered_undirected_graph(graph: nx.DiGraph) -> nx.Graph:
        """Create a deterministic undirected graph preserving stable node order."""
        ordered_graph: nx.Graph = nx.Graph()
        ordered_graph.add_nodes_from(sorted(graph.nodes(), key=lambda n: str(n)))
        ordered_graph.add_edges_from(
            sorted(graph.edges(), key=lambda edge: (str(edge[0]), str(edge[1])))
        )
        return ordered_graph

    @staticmethod
    def _as_float_xy(coord: Any) -> Tuple[float, float]:
        """Convert a coordinate-like value to a float pair."""
        try:
            return float(coord[0]), float(coord[1])  # type: ignore[index]
        except Exception:
            return 0.0, 0.0

    def _compact_positions_axis(
        self,
        positions: Dict[Any, Tuple[int, int]],
        *,
        axis: str,
        min_gap: int,
        node_height: int,
    ) -> Dict[Any, Tuple[int, int]]:
        """Compact whitespace between disjoint node bands on one axis."""
        if not positions:
            return {}

        intervals: List[Tuple[int, int, Any]] = []
        for node, (x, y) in positions.items():
            if axis == "x":
                start = x
                end = x + self._get_node_width(node) - 1
            else:
                start = y
                end = y + node_height - 1
            intervals.append((start, end, node))

        intervals.sort(key=lambda item: (item[0], item[1], str(item[2])))
        if not intervals:
            return dict(positions)

        bands: List[Tuple[int, int, List[Any]]] = []
        band_start, band_end, first_node = intervals[0]
        band_nodes: List[Any] = [first_node]

        for start, end, node in intervals[1:]:
            if start <= band_end:
                band_end = max(band_end, end)
                band_nodes.append(node)
            else:
                bands.append((band_start, band_end, band_nodes))
                band_start, band_end = start, end
                band_nodes = [node]
        bands.append((band_start, band_end, band_nodes))

        compacted = dict(positions)
        next_start = 0
        axis_gap = max(1, min_gap)
        for start, end, nodes in bands:
            shift = start - next_start
            for node in nodes:
                x, y = compacted[node]
                if axis == "x":
                    compacted[node] = (x - shift, y)
                else:
                    compacted[node] = (x, y - shift)
            new_end = end - shift
            next_start = new_end + axis_gap + 1

        return compacted

    def _layout_from_coordinate_map(
        self, coord_map: Dict[Any, Any], spacing: int
    ) -> Dict[str, Tuple[int, int]]:
        """Convert continuous coordinates to non-overlapping integer grid positions."""
        if not coord_map:
            return {}

        widths = {node: self._get_node_width(node) for node in coord_map}
        max_node_width = max(widths.values(), default=1)
        node_height = self._get_node_height()
        layer_step = self._get_layer_step()
        node_count = len(coord_map)

        xy_map = {node: self._as_float_xy(coord) for node, coord in coord_map.items()}
        x_values = [xy[0] for xy in xy_map.values()]
        y_values = [xy[1] for xy in xy_map.values()]
        min_x = min(x_values, default=0.0)
        max_x = max(x_values, default=0.0)
        min_y = min(y_values, default=0.0)
        max_y = max(y_values, default=0.0)
        span_x = max(max_x - min_x, 1e-9)
        span_y = max(max_y - min_y, 1e-9)

        grid_factor = max(2, int(math.ceil(math.sqrt(node_count))) * 2)
        base_x_span = max(1, (max_node_width + spacing) * grid_factor)
        base_y_span = max(1, layer_step * grid_factor)
        step_x = max(1, max_node_width + spacing)
        step_y = max(1, layer_step)
        row_limit = max(4, node_count * 2)

        positions: Dict[Any, Tuple[int, int]] = {}
        placed_rects: List[Tuple[int, int, int, int]] = []
        nodes_ordered = sorted(
            coord_map.keys(),
            key=lambda n: (xy_map[n][1], xy_map[n][0], str(n)),
        )

        for node in nodes_ordered:
            raw_x, raw_y = xy_map[node]
            nx_norm = (raw_x - min_x) / span_x
            ny_norm = (raw_y - min_y) / span_y

            proposed_x = int(round(nx_norm * base_x_span))
            proposed_y = int(round(ny_norm * base_y_span))

            candidate_x = proposed_x
            candidate_y = proposed_y
            candidate_rect = self._node_rect(
                node, candidate_x, candidate_y, node_height
            )
            attempts = 0
            while any(
                self._rectangles_overlap(candidate_rect, existing)
                for existing in placed_rects
            ):
                attempts += 1
                candidate_x += step_x
                if attempts % row_limit == 0:
                    candidate_x = proposed_x
                    candidate_y += step_y
                candidate_rect = self._node_rect(
                    node, candidate_x, candidate_y, node_height
                )

            positions[node] = (candidate_x, candidate_y)
            placed_rects.append(candidate_rect)

        positions = self._compact_positions_axis(
            positions,
            axis="x",
            min_gap=spacing,
            node_height=node_height,
        )
        positions = self._compact_positions_axis(
            positions,
            axis="y",
            min_gap=max(1, self.options.layer_spacing),
            node_height=node_height,
        )

        return self._normalize_positions_to_origin(positions)

    def _layout_planar(
        self, graph: nx.DiGraph, spacing: int
    ) -> Dict[str, Tuple[int, int]]:
        """Planar layout with hierarchical fallback for non-planar graphs."""
        planar_graph = nx.Graph(graph)
        try:
            coord_map = nx.planar_layout(planar_graph)
            return self._layout_from_coordinate_map(coord_map, spacing)
        except (nx.NetworkXException, ValueError):
            return self._layout_hierarchical(graph, spacing)

    def _layout_spring(
        self, graph: nx.DiGraph, spacing: int, seed: int = 42
    ) -> Dict[str, Tuple[int, int]]:
        """Fruchterman-Reingold spring layout."""
        coord_map = nx.spring_layout(nx.Graph(graph), seed=seed)
        return self._layout_from_coordinate_map(coord_map, spacing)

    def _layout_arf(
        self, graph: nx.DiGraph, spacing: int, seed: int = 42
    ) -> Dict[str, Tuple[int, int]]:
        """Attractive-repulsive force-directed layout."""
        arf_layout = getattr(nx, "arf_layout", None)
        if arf_layout is None:
            return self._layout_spring(graph, spacing, seed=seed)

        ordered_graph = self._to_ordered_undirected_graph(graph)
        try:
            coord_map = arf_layout(ordered_graph, seed=seed)
        except TypeError:
            coord_map = arf_layout(ordered_graph)
        return self._layout_from_coordinate_map(coord_map, spacing)

    def _layout_spiral(
        self, graph: nx.DiGraph, spacing: int
    ) -> Dict[str, Tuple[int, int]]:
        """Spiral layout for progressive radial sequencing."""
        ordered_graph = self._to_ordered_undirected_graph(graph)
        coord_map = nx.spiral_layout(ordered_graph)
        return self._layout_from_coordinate_map(coord_map, spacing)

    def _layout_shell(
        self, graph: nx.DiGraph, spacing: int
    ) -> Dict[str, Tuple[int, int]]:
        """Concentric shell layout using BFS-derived rings."""
        ordered_graph = self._to_ordered_undirected_graph(graph)
        layers = self._build_layers_bfs(nx.DiGraph(graph))
        shells = [sorted(layer, key=lambda n: str(n)) for layer in layers if layer]
        if not shells:
            shells = [sorted(ordered_graph.nodes(), key=lambda n: str(n))]
        coord_map = nx.shell_layout(ordered_graph, nlist=shells)
        return self._layout_from_coordinate_map(coord_map, spacing)

    def _layout_kamada_kawai(
        self, graph: nx.DiGraph, spacing: int
    ) -> Dict[str, Tuple[int, int]]:
        """Kamada-Kawai force-directed layout."""
        try:
            coord_map = nx.kamada_kawai_layout(nx.Graph(graph), weight=None)
        except (ModuleNotFoundError, ImportError):
            # NetworkX's Kamada-Kawai solver depends on SciPy; fallback keeps
            # the strategy usable in minimal environments.
            coord_map = nx.spring_layout(nx.Graph(graph), seed=42)
        return self._layout_from_coordinate_map(coord_map, spacing)

    def _layout_random(
        self, graph: nx.DiGraph, spacing: int
    ) -> Dict[str, Tuple[int, int]]:
        """Random node positioning layout."""
        coord_map = nx.random_layout(graph)
        return self._layout_from_coordinate_map(coord_map, spacing)

    def _infer_multipartite_subset_map(self, graph: nx.DiGraph) -> Dict[Any, Any]:
        """Infer multipartite subset assignment from node attrs, then BFS depth."""
        subset_map: Dict[Any, Any] = {}
        attr_keys = ("subset", "part", "partition", "layer", "level", "rank", "group")
        for node, attrs in graph.nodes(data=True):
            for key in attr_keys:
                if key in attrs and attrs[key] is not None:
                    subset_map[node] = attrs[key]
                    break

        if len(subset_map) == len(graph.nodes()):
            return subset_map

        layers = self._build_layers_bfs(nx.DiGraph(graph))
        depth_map: Dict[Any, int] = {}
        for depth, layer in enumerate(layers):
            for node in layer:
                depth_map[node] = depth

        for node in graph.nodes():
            subset_map.setdefault(node, depth_map.get(node, 0))

        return subset_map

    def _layout_multipartite(
        self, graph: nx.DiGraph, spacing: int
    ) -> Dict[str, Tuple[int, int]]:
        """Multipartite layout driven by subset-like node attributes or BFS depth."""
        multipartite_graph = nx.Graph(graph).copy()
        subset_map = self._infer_multipartite_subset_map(graph)
        nx.set_node_attributes(multipartite_graph, subset_map, "_phart_subset")
        coord_map = nx.multipartite_layout(
            multipartite_graph, subset_key="_phart_subset", align="horizontal"
        )
        return self._layout_from_coordinate_map(coord_map, spacing)

    def _layout_layered_fallback(
        self,
        graph: nx.DiGraph,
        spacing: int,
        layer_height: int,
        layer_mode: str = "auto",
    ) -> Dict[str, Tuple[int, int]]:
        """Fallback layered layout for general DAGs and non-tree graphs.

        Nodes are assigned to topological layers (for DAGs) or BFS-like depth
        layers (for cyclic/non-DAG directed graphs), then centered per layer.
        """

        components = (
            [
                graph.subgraph(nodes).copy()
                for nodes in nx.weakly_connected_components(graph)
            ]
            if graph.is_directed()
            else [
                graph.subgraph(nodes).copy() for nodes in nx.connected_components(graph)
            ]
        )
        components.sort(
            key=lambda comp: min(str(n) for n in comp.nodes()), reverse=False
        )

        positions: Dict[str, Tuple[int, int]] = {}
        y_offset = 0
        component_gap = layer_height

        for component in components:
            if layer_mode == "bfs":
                layers = self._build_layers_bfs(nx.DiGraph(component))
            else:
                layers = self._build_layers_auto(nx.DiGraph(component))
            widths = {node: self._get_node_width(node) for node in component.nodes()}
            ordered_layers = [
                sorted(layer, key=lambda n: str(n)) for layer in layers if layer
            ]
            if not ordered_layers:
                continue

            layer_widths: List[int] = []
            for layer in ordered_layers:
                total = sum(widths[node] for node in layer)
                total += spacing * max(0, len(layer) - 1)
                layer_widths.append(total)
            max_layer_width = max(layer_widths, default=0)

            for layer_idx, layer in enumerate(ordered_layers):
                current_x = (max_layer_width - layer_widths[layer_idx]) // 2
                y = y_offset + (layer_idx * layer_height)
                for node in layer:
                    positions[node] = (current_x, y)
                    current_x += widths[node] + spacing

            y_offset += (len(ordered_layers) * layer_height) + component_gap

        return positions

    def _build_layers_auto(self, subgraph: nx.DiGraph) -> List[List[Any]]:
        if subgraph.is_directed() and nx.is_directed_acyclic_graph(subgraph):
            return [list(layer) for layer in nx.topological_generations(subgraph)]
        return self._build_layers_bfs(subgraph)

    def _build_layers_bfs(self, subgraph: nx.DiGraph) -> List[List[Any]]:
        roots: List[Any]
        if subgraph.is_directed():
            roots = [n for n, d in subgraph.in_degree() if d == 0]
            if not roots:
                roots = [max(subgraph.nodes(), key=lambda n: subgraph.out_degree(n))]
        else:
            roots = [max(subgraph.nodes(), key=lambda n: subgraph.degree(n))]

        node_depth: Dict[Any, int] = {}
        queue: deque[Any] = deque(roots)
        for root in roots:
            node_depth[root] = 0

        while queue:
            current = queue.popleft()
            current_depth = node_depth[current]
            neighbors = (
                list(subgraph.successors(current))
                if subgraph.is_directed()
                else list(subgraph.neighbors(current))
            )
            for neighbor in neighbors:
                next_depth = current_depth + 1
                if neighbor not in node_depth or next_depth < node_depth[neighbor]:
                    node_depth[neighbor] = next_depth
                    queue.append(neighbor)

        for node in subgraph.nodes():
            node_depth.setdefault(node, 0)

        max_depth = max(node_depth.values(), default=0)
        layers: List[List[Any]] = [[] for _ in range(max_depth + 1)]
        for node, depth in node_depth.items():
            layers[depth].append(node)
        return layers

    def calculate_canvas_dimensions(
        self, positions: Dict[str, Tuple[int, int]]
    ) -> Tuple[int, int]:
        """Calculate required canvas dimensions based on layout and node decorations."""
        if not positions:
            return 0, 0

        # Calculate width needed for full node bounds.
        max_node_end = 0
        for node, (x, _) in positions.items():
            node_end = x + self._get_node_width(node)
            max_node_end = max(max_node_end, node_end)

        # Add configured padding plus extra space for edge decorators
        extra_edge_space = (
            6 if self.options.use_ascii else 4
        )  # ASCII needs more space for markers
        final_width = max(
            1, max_node_end + self.options.right_padding + extra_edge_space
        )

        # Calculate height including full node height and extra rendering room.
        node_height = self._get_node_height()
        max_y = max((y + node_height for _, y in positions.values()), default=0)
        final_height = max(1, max_y + 1)

        return final_width, final_height
