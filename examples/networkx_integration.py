"""Examples of PHART visualization with various NetworkX graph types."""
# src path: examples\networkx_integration.py

import networkx as nx
from phart import ASCIIRenderer, NodeStyle, LayoutOptions


def show_graph(G, title, style=NodeStyle.MINIMAL):
    """Helper to display a graph with title."""
    options = LayoutOptions(node_style=style, node_spacing=6, layer_spacing=2)
    print(f"\n{title}")
    print("=" * len(title))
    renderer = ASCIIRenderer(G, options=options)
    print(renderer.render())


def main():
    # Basic graph types
    G = nx.path_graph(4, create_using=nx.DiGraph)
    show_graph(G, "Path Graph")

    G = nx.cycle_graph(5, create_using=nx.DiGraph)
    show_graph(G, "Cycle Graph")

    G = nx.star_graph(4, create_using=nx.Graph)
    show_graph(G, "Star Graph (Directed)", NodeStyle.SQUARE)

    # Trees and DAGs
    G = nx.balanced_tree(2, 3, create_using=nx.DiGraph)
    show_graph(G, "Balanced Binary Tree", NodeStyle.ROUND)

    G = nx.random_labeled_tree(10)
    show_graph(G, "Random Tree")

    # Special graphs
    G = nx.bull_graph()
    G = nx.DiGraph(G)  # Convert to directed
    show_graph(G, "Bull Graph", NodeStyle.DIAMOND)

    G = nx.petersen_graph()
    G = nx.DiGraph(G)  # Convert to directed
    show_graph(G, "Petersen Graph")

    G = nx.watts_strogatz_graph(8, 2, 0.2)
    show_graph(G, "Small World Graph (Watts-Strogatz)")

    # Real-world examples
    G = nx.karate_club_graph()
    G = nx.DiGraph(G)  # Convert to directed
    show_graph(G, "Karate Club Social Network")


if __name__ == "__main__":
    print("PHART + NetworkX Graph Examples")
    print("===============================")
    main()
