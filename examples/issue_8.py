import networkx as nx
from phart import ASCIIRenderer


# Create a directed graph
G = nx.DiGraph()

# Add edges to form a triangle
G.add_edge(1, 2)
G.add_edge(2, 3)
G.add_edge(3, 1)

renderer = ASCIIRenderer(G)
print(renderer.render())
