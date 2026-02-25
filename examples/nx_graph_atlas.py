import networkx as nx

# Load atlas, pick a specific graph (e.g., index 100)
G = nx.graph_atlas_g()[100]
## Use Graphviz layout
pos = nx.nx_agraph.graphviz_layout(G, prog="neato")
nx.draw(G, pos)
# plt.show()
