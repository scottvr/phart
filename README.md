# phart

phart: Python Hierarchical ASCII Representation Tool - A Pure Python graph visualization in ASCII, no external dependencies\*

(\* except NetworkX, which we should probably mention prominently. We just mean no dependencies of the Perl or PHP/webserver types.)

## Features

- Pure Python implementation
- No external dependencies (except NetworkX)
- Multiple node styles (square, round, diamond)
- Customizable edge characters
- Support for directed and undirected graphs
- Handles cycles and complex layouts
- Bidirectional edge support

<details>
     <summary>Example output PHARTs [click arrow to expand]</summary>

## PHART Graph Visualization Examples
=================================

### Software Dependency Example:
```
            [main.py]
                |
         v      |       v
    [config.py]----[utils.py]
         |              |
         v              | v
  [constants.py]----[helpers.py]
```


### Organizational Hierarchy Example:
```
                                       [CEO]
                                         |
                                v        v        v
                              [CFO]----[COO]----[CTO]
                                |        |        |
        v              v        |      v |        |       v                v
  [Controller]----[Dev Lead]----[Marketing Dir]----[Research Lead]----[Sales Dir]
```


### Network Topology Example:
```
                     [Router1]
                         |
                   v     |      v
               [Switch1]----[Switch2]
                   |            |
      v            v            |            v
  [Server1]----[Server2]    [Server3]----[Server4]
```

### Workflow Example:
```
        [Start]
           |
           v
        [Input]
           |
           |v
       [Validate]
            |
           v|
     --[Process]
     |     ^
     |     v
     |  [Check]
     |     |
     |     |     v
  [Error]----[Success]
                 |
            v    |
        [Output]--
            |
           v|
         [End]
```

### DOT Import Example:
```
     [A]
      |
   v  |   v
  [B]----[D]
   |      |
   |  v   |
   --[C]---
      |
      v
     [E]
```


## Custom Styling Example:
Different node styles for the same graph:

### Using MINIMAL style:
```
         0
         |
       v |  v
       1----2
       |    |
  v    v    |    v
  3----4    5----6
```

### Using SQUARE style:
```
            [0]
             |
          v  |   v
         [1]----[2]
          |      |
   v      v      |      v
  [3]----[4]    [5]----[6]
```

### Using ROUND style:
```
            (0)
             |
          v  |   v
         (1)----(2)
          |      |
   v      v      |      v
  (3)----(4)    (5)----(6)
```

### Using DIAMOND style:
```
            <0>
             |
          v  |   v
         <1>----<2>
          |      |
   v      v      |      v
  <3>----<4>    <5>----<6>
```
   
</details>

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

     [A]
      │
   v  │   v
  [B]────[C]
   │
   │  v
   ──[D]
```

The renderer shows edge direction using arrows:

- v : downward flow
- ^ : upward flow
- > or < : horizontal flow

These directional indicators are particularly useful for:

- Dependency graphs
- Workflow diagrams
- Process flows
- Any directed relationships

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

### Note on DOT format support:

---

PHART uses pydot for DOT format support. When processing DOT strings containing
multiple graph definitions, only the first graph will be rendered. For more
complex DOT processing needs, you can convert your graphs using NetworkX's
various graph reading utilities before passing them to PHART.

## License

MIT License

```

```
