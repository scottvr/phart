"""triad_generator.py - Generates and visualizes all possible directed triads."""

from phart import ASCIIRenderer, NodeStyle
from phart.layout import LayoutManager
import networkx as nx
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def should_use_triangle_layout(graph: nx.Graph) -> bool:
    """Determine if triangle layout is appropriate for this graph."""
    if len(graph) != 3:
        return False

    # Only use triangle layout for specific simple patterns
    if graph.is_directed():
        edge_count = len(graph.edges())
        if edge_count <= 3:  # Simple triangle patterns only
            return True

        # Check for specific patterns we know work well with triangle layout
        if edge_count == 4 and any(
            len(list(nx.simple_cycles(graph))) == 1 for cycle in nx.simple_cycles(graph)
        ):
            return True

    return False


# Monkey patch the LayoutManager's calculate_layout method
original_calculate_layout = LayoutManager.calculate_layout


def new_calculate_layout(self):
    """Patched version of calculate_layout that's more selective about triangle layouts."""
    if not self.graph:
        return {}, 0, 0

    # Calculate max node width for spacing adjustment
    max_node_width = max(self._get_node_width(str(node)) for node in self.graph.nodes())
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

        # Modified decision logic for using triangle layout
        is_triangle = should_use_triangle_layout(subgraph)

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


# Apply the monkey patch
LayoutManager.calculate_layout = new_calculate_layout


def generate_triads():
    """Generate all 16 possible directed triads with their standard naming."""
    triads = {
        "003": [],  # Empty triad
        "012": [(1, 2)],  # Single edge
        "102": [(1, 2), (2, 1)],  # Mutual edge
        "021D": [(3, 1), (3, 2)],  # Two edges down
        "021U": [(1, 3), (2, 3)],  # Two edges up
        "021C": [(1, 3), (3, 2)],  # Two edges chain
        "111D": [(1, 2), (2, 1), (3, 1)],  # Mutual + single down
        "111U": [(1, 2), (2, 1), (1, 3)],  # Mutual + single up
        "030T": [(1, 2), (3, 2), (1, 3)],  # Three edges triangle
        "030C": [(1, 3), (3, 2), (2, 1)],  # Three edges cyclic
        "201": [(1, 2), (2, 1), (3, 1), (1, 3)],  # Four edges
        "120D": [(1, 2), (2, 1), (3, 1), (3, 2)],  # Four edges down
        "120U": [(1, 2), (2, 1), (1, 3), (2, 3)],  # Four edges up
        "120C": [(1, 2), (2, 1), (1, 3), (3, 2)],  # Four edges cycle
        "210": [(1, 2), (2, 1), (1, 3), (3, 2), (2, 3)],  # Five edges
        "300": [(1, 2), (2, 1), (2, 3), (3, 2), (1, 3), (3, 1)],  # Complete
    }

    graphs = {}
    for name, edge_list in triads.items():
        G = nx.DiGraph()
        G.add_nodes_from([1, 2, 3])  # Always add all three nodes
        G.add_edges_from(edge_list)
        logger.debug(f"Created {name} with edges: {G.edges()}")
        graphs[name] = G

    return graphs


def render_triad(name: str, graph: nx.DiGraph) -> str:
    """Render a single triad with its name."""
    try:
        logger.debug(f"Attempting to render {name}")

        # Create renderer with minimal spacing
        renderer = ASCIIRenderer(
            graph,
            node_style=NodeStyle.SQUARE,
            node_spacing=2,  # Reduce horizontal spacing
            layer_spacing=1,  # Reduce vertical spacing
        )

        # Get the rendered output
        rendered = renderer.render()
        logger.debug(f"Raw rendered output:\n{rendered}")

        # Clean up excess whitespace while preserving structure
        lines = [line.rstrip() for line in rendered.split("\n")]
        while lines and not lines[-1].strip():
            lines.pop()

        # Find the maximum line width
        max_width = max(len(line) for line in lines) + 2

        # Create bordered output
        output = []
        output.append("=" * max_width)
        output.append(f"|{name:^{max_width-2}}|")
        output.append("-" * max_width)
        for line in lines:
            output.append(f"|{line:<{max_width-2}}|")
        output.append("=" * max_width)

        return "\n".join(output)

    except Exception as e:
        logger.exception(f"Error rendering {name}")
        return f"Error rendering {name}: {str(e)}\nGraph edges: {list(graph.edges())}"


def render_all_triads():
    """Render all triads using PHART."""
    triads = generate_triads()

    print("Rendering all triads:")
    print()

    for name, graph in triads.items():
        print(render_triad(name, graph))
        print()


if __name__ == "__main__":
    render_all_triads()
