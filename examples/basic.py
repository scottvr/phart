import networkx as nx

import sys
from phart import ASCIIRenderer

num = 123

if len(sys.argv) > 1:
    num = int(sys.argv[1])


G = nx.graph_atlas_g()[num]

A = ASCIIRenderer(G)
print(A.render())
