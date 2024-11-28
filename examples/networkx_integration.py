"""Examples of PHART visualization with various NetworkX graph types."""

import networkx as nx
from phart import ASCIIRenderer, NodeStyle


def show_graph(G, title, style=NodeStyle.MINIMAL):
    """Helper to display a graph with title."""
    print(f"\n{title}")
    print("=" * len(title))
    renderer = ASCIIRenderer(G, node_style=style)
    print(renderer.render())


# Basic graph types
G = nx.path_graph(4, create_using=nx.DiGraph)
show_graph(G, "Path Graph")

G = nx.cycle_graph(5, create_using=nx.DiGraph)
show_graph(G, "Cycle Graph")

G = nx.star_graph(4, create_using=nx.DiGraph)
show_graph(G, "Star Graph (Directed)", NodeStyle.SQUARE)

# Trees and DAGs
G = nx.balanced_tree(2, 3, create_using=nx.DiGraph)
show_graph(G, "Balanced Binary Tree", NodeStyle.ROUND)

G = nx.random_tree(10, create_using=nx.DiGraph)
show_graph(G, "Random Tree")

# Special graphs
G = nx.bull_graph()
G = nx.DiGraph(G)  # Convert to directed
show_graph(G, "Bull Graph", NodeStyle.DIAMOND)

G = nx.petersen_graph()
G = nx.DiGraph(G)  # Convert to directed
show_graph(G, "Petersen Graph")

# Random graphs
G = nx.gnp_random_graph(8, 0.2, directed=True)
show_graph(G, "Random Graph (Erdős-Rényi)")

G = nx.watts_strogatz_graph(8, 2, 0.2, directed=True)
show_graph(G, "Small World Graph (Watts-Strogatz)")

# Real-world examples
G = nx.karate_club_graph()
G = nx.DiGraph(G)  # Convert to directed
show_graph(G, "Karate Club Social Network")

if __name__ == "__main__":
    print("PHART + NetworkX Graph Examples")
    print("===============================")
