"""
Simple examples demonstrating basic PHART usage.
"""

import networkx as nx
from phart import ASCIIRenderer, NodeStyle


def demonstrate_basic_graph():
    """Simple directed graph example."""
    print("\nBasic Directed Graph:")
    G = nx.DiGraph()
    G.add_edges_from([("A", "B"), ("A", "C"), ("B", "D"), ("C", "D")])

    renderer = ASCIIRenderer(G)
    print(renderer.render())


def demonstrate_node_styles():
    """Show different node style options."""
    G = nx.balanced_tree(2, 2, create_using=nx.DiGraph)

    print("\nNode Styles:")
    for style in NodeStyle:
        print(f"\n{style.name} style:")
        renderer = ASCIIRenderer(G, node_style=style)
        print(renderer.render())


def demonstrate_cycle():
    """Show how PHART handles cycles."""
    print("\nGraph with Cycle:")
    G = nx.DiGraph(
        [
            ("Start", "Process"),
            ("Process", "Check"),
            ("Check", "End"),
            ("Check", "Process"),  # Creates cycle
        ]
    )
    renderer = ASCIIRenderer(G)
    print(renderer.render())


if __name__ == "__main__":
    print("PHART Simple Examples")
    print("===================")

    demonstrate_basic_graph()
    demonstrate_node_styles()
    demonstrate_cycle()
