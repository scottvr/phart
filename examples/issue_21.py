import networkx as nx
from phart import ASCIIRenderer, LayoutOptions

G = nx.DiGraph()


nodes = [
    ("[ 测试测试测试测试1 ]", {}),
    ("conn_1", {"label": "+"}),
    ("[ 测试测试测试测试测试2 ]", {}),
    ("[ 测试测试测试测试测试3 ]", {}),
    ("[ 测试测试测试测试测试4 ]", {}),
]

G.add_nodes_from(nodes)


edges = [
    ("[ 测试测试测试测试测试1 ]", "conn_1"),
    ("conn_1", "[ 测试测试测试测试测试2 ]"),
    ("conn_1", "[ 测试测试测试测试测试3 ]"),
    ("conn_1", "[ 测试测试测试测试测试4 ]"),
]

G.add_edges_from(edges)

renderer = ASCIIRenderer(G)
result = renderer.render(G)
renderer2 = ASCIIRenderer(G, options=LayoutOptions(bboxes=True))
result2 = renderer2.render(G)

with open("output.issue21.txt", "w", encoding="utf-8") as f:
    f.write(result + "\n\n\n" + result2)
print("Output written to output.issue21.txt")
