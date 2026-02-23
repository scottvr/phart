import networkx as nx
from phart import ASCIIRenderer, NodeStyle

G = nx.balanced_tree(2, 2, create_using=nx.DiGraph)
renderer = ASCIIRenderer(G, node_style=NodeStyle.SQUARE)
print(renderer.render())
