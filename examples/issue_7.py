import networkx as nx
from phart import ASCIIRenderer

g = nx.DiGraph()

g.add_edge("Alice", "Bob", relationship="friend")  
g.add_edge("Bob", "Alice", relationship="friend")  
g.add_edge("Bob", "Charlie", relationship="friend")  
g.add_edge("Charlie", "Bob", relationship="enemy")  

renderer = ASCIIRenderer(g)
print(renderer.render())
