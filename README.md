# phart

phart: Python Hierarchical ASCII Representation Tool - A Pure Python graph visualization in ASCII, no external dependencies\*

(\* except NetworkX, which we should probably mention prominently. We just mean no dependencies of the Perl or PHP/webserver types.)

## Installation

```bash
# not yet in Pypi so, from github:
pip install git+https://github.com/scottvr/phart

# or if you are reading this from where you cloned the repo:
pip install -e .
```

## Quick Start

```python
import networkx as nx
from phart import ASCIIRenderer

# Create a simple graph
G = nx.DiGraph()
G.add_edges_from([("A", "B"), ("A", "C"), ("B", "D")])

# Render it in ASCII
renderer = ASCIIRenderer(G)
print(renderer.render())
<<<<<<< HEAD

     [A]
      │
   v  │   v
  [B]────[C]
   │
   │  v
   ──[D]


=======
```

       [A]
        │
     v  │   v
    [B]────[C]
     │
     │  v
     -─[D]

```
>>>>>>> de7f4431607bb76e68c679bf66819963e613eac4
The renderer shows edge direction using arrows:

- v : downward flow
- ^ : upward flow
- > or < : horizontal flow

These directional indicators are particularly useful for:

- Dependency graphs
- Workflow diagrams
- Process flows
- Any directed relationships

## Features

- Pure Python implementation
- No external dependencies (except NetworkX)
- Multiple node styles (square, round, diamond)
- Customizable edge characters
- Support for directed and undirected graphs
- Handles cycles and complex layouts
- Bidirectional edge support

## Extras

- DOT file support
- requires pydot
   `pip install -r requirements\extra.txt`
### Example
    >>> dot = '''
    ... digraph {
    ...     A -> B
    ...     B -> C
    ... }
    ... '''
    >>> renderer = ASCIIRenderer.from_dot(dot)
    >>> print(renderer.render())
    A
    |
    B
    |
    C
    >>>

## License

MIT License
```
