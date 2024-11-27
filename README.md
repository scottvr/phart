# phart
phart: Python Hierarchical ASCII Representation Tool - A Pure Python graph visualization in ASCII, no external dependencies* 

(* except NetworkX, which we should probably mention prominently. We just mean no dependencies of the Perl or PHP/webserver types.)

## Installation

```bash
pip install git+https://github.com/scottvr/phart
```

## Quick Start

```python
import networkx as nx
from phart import ASCIIGraphRenderer

# Create a simple graph
G = nx.DiGraph()
G.add_edges_from([("A", "B"), ("A", "C"), ("B", "D")])

# Render it in ASCII
renderer = ASCIIGraphRenderer(G)
print(renderer.render())
```

Output:
```
    [A]
     |
  ---|---
  |     |
[B]    [C]
  |
  |
 [D]
```

## Features

- Pure Python implementation
- No external dependencies (except NetworkX)
- Multiple node styles (square, round, diamond)
- Customizable edge characters
- Support for directed and undirected graphs
- Handles cycles and complex layouts
- Bidirectional edge support

## License

MIT License
