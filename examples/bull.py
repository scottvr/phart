import networkx as nx
import phart

print("Bull Graph:")
G = nx.bull_graph()
options = phart.LayoutOptions(
    node_style=phart.NodeStyle.MINIMAL, node_spacing=6, layer_spacing=4
)
phart.ASCIIRenderer(G, options=options).draw()
print(G.edges())

print("Converted to digraph:")
G = nx.DiGraph(G)  # Convert to directed
phart.ASCIIRenderer(G, options=options).draw()
print(G.edges())
