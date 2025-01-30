import networkx as nx
from phart import ASCIIRenderer, NodeStyle


def generate_basic_graphlets():
    """Generate a set of basic canonical graphlets."""
    graphlets = {}

    # Single directed edge
    g = nx.DiGraph()
    g.add_edge("A", "B")
    graphlets["directed_edge"] = g

    # Bidirectional edge
    g = nx.DiGraph()
    g.add_edge("A", "B")
    g.add_edge("B", "A")
    graphlets["bidirectional"] = g

    # Triangle patterns
    # Directed cycle
    g = nx.DiGraph()
    g.add_edges_from([("A", "B"), ("B", "C"), ("C", "A")])
    graphlets["triangle_cycle"] = g

    # Feed-forward triangle
    g = nx.DiGraph()
    g.add_edges_from([("A", "B"), ("B", "C"), ("A", "C")])
    graphlets["triangle_feedforward"] = g

    # Square patterns
    # Directed cycle
    g = nx.DiGraph()
    g.add_edges_from([("A", "B"), ("B", "C"), ("C", "D"), ("D", "A")])
    graphlets["square_cycle"] = g

    # Square with diagonals
    g = nx.DiGraph()
    g.add_edges_from(
        [("A", "B"), ("B", "C"), ("C", "D"), ("D", "A"), ("A", "C"), ("B", "D")]
    )
    graphlets["square_cross"] = g

    return graphlets


def test_render_graphlets():
    """Test rendering of each graphlet."""
    graphlets = generate_basic_graphlets()

    print("Testing basic graphlet renderings:")
    for name, g in graphlets.items():
        print(f"\n{name}:")
        renderer = ASCIIRenderer(g, node_style=NodeStyle.SQUARE)
        print(renderer.render())


if __name__ == "__main__":
    test_render_graphlets()
