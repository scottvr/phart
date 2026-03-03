import sys
import networkx as nx
from phart import ASCIIRenderer, LayoutOptions

if len(sys.argv) > 1:
    nnodes = int(sys.argv[1])
    if nnodes % 2 == 0:
        nnodes = nnodes + 1
else:
    nnodes = 13

# A rainbow color mapping using matplotlib's tableau colors
node_dist_to_color = {
    1: "red",
    2: "orange",
    3: "green",
    4: "bright_green",
    5: "blue",
    6: "magenta",
}

# Create a complete graph with an odd number of nodes
G = nx.complete_graph(nnodes)

# make it directed, for colored spaghetti and testing node-pacement/routing changes
G = G.to_directed()

# A graph with (2n + 1) nodes requires n colors for the edges
n = (nnodes - 1) // 2 % len(node_dist_to_color)
ndist_iter = list(range(1, n + 1))

# Take advantage of circular symmetry in determining node distances
ndist_iter += ndist_iter[::-1]


def cycle(nlist, n):
    return nlist[-n:] + nlist[:-n]


# Rotate nodes around the circle and assign colors for each edge based on
# node distance
nodes = list(G.nodes())
for i, nd in enumerate(ndist_iter):
    for u, v in zip(nodes, cycle(nodes, i + 1), strict=True):
        G[u][v]["color"] = node_dist_to_color[nd]

options = LayoutOptions(
    ansi_colors=True,
    edge_color_mode="attr",
    edge_color_rules={
        "color": {
            "red": "red",
            "bright_green": "bright_green",
            "green": "green",
            "orange": "orange",
            "blue": "blue",
            "magenta": "magenta",
        }
    },
    node_spacing=8,
    layer_spacing=4,
    hpad=2,
    vpad=2,
    edge_anchor_mode="ports",
)

R = ASCIIRenderer(G, options=options)
print(R.render())
