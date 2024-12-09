# phart

**PHART:** The Python Hierarchical ASCII Representation Tool - A Pure Python graph visualization in ASCII, no external dependencies\*

(\* except NetworkX, which we should probably mention prominently. We just mean no dependencies of the Perl or PHP/webserver types.)

## Features

- Pure Python implementation
- No external dependencies (except NetworkX)
- Multiple node styles (square, round, diamond)
- Customizable edge characters
- Support for directed and undirected graphs
- Handles cycles and complex layouts
- Bidirectional edge support

## Examples

<details>

<summary>Example output PHARTs [click triangle/arrow to expand/collapse]</summary>

## PHART Graph Visualization Examples

=================================

### In preparation for a 1.0 PyPi release

I was doing some last-minute testing and came across this, from the networkx gallery:

https://networkx.org/documentation/latest/auto_examples/drawing/plot_chess_masters.html#sphx-glr-auto-examples-drawing-plot-chess-masters-py

The code there creates a graph from some data pulled from a database of Chess masters tournaments and such at this site:

https://chessproblem.my-free-games.com/chess/games/Download-PGN.php

And plots it with matplotlib. It looked pretty complex so I thought as a lark I would see how difficult it would be to get phart to render the graph. The matplot can be seen here:

![screen capture of graph plot](https://github.com/scottvr/phart/blob/67bd3d02b6ad9cc4a8a09fe6fc2920a6712f5c7a/examples/WCC-plt-Capture.png)

So, I added the following to the code at the networkx gallery page linked above:

```
from phart import ASCIIRenderer, NodeStyle

.. existing code remains here ...

... then directly below the existing lines to create the nx graph:
# make new undirected graph H without multi-edges
H = nx.Graph(G)
... I added this:
renderer=ASCIIRenderer(H)
renderer.write_to_file("wcc.txt")
```

and ran the code. Immediately this was written to wcc.txt:

```
                               ---------------------------------[Botvinnik, Mikhail M]---------------------------------
                               |               |                           |                 |                        |
            v                  |               |                    v      |                 |                        |                     v
  [Bronstein, David I]----[Euwe, Max]----[Keres, Paul]----[Petrosian, Tigran V]----[Reshevsky, Samuel H]----[Smyslov, Vassily V]----[Tal, Mikhail N]
                               ^                               |    |
                                                               |    |                   v
                                                    [Alekhine, Alexander A]----[Spassky, Boris V]
                                                               |           |            |
                                                  v            |           |            |           v
                                        [Bogoljubow, Efim D]----[Capablanca, Jose Raul] ---[Fischer, Robert J]
                                                                          |^
                                                                          |
                                                                  [Lasker, Emanuel]--------------
                                                                          |                     |
                            v                      v                      v                     |                       v
                   [Janowski, Dawid M]----[Marshall, Frank J]----[Schlechter, Carl]----[Steinitz, Wilhelm]----[Tarrasch, Siegbert]
                                                                                                |  |
                                                 v                        v                     |  |
                                       [Chigorin, Mikhail I]----[Gunsberg, Isidor A]----[Zukertort, Johannes H]


                                            [Karpov, Anatoly]----[Kasparov, Gary]----[Korchnoi, Viktor L]
```

No fuss. No muss. Just phart.

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

## Why PHART?

Because it is necessary? OK, sorry... Actually it had a few other names early on, but when it came time to upload to PyPi, we discovered the early names we chose were already taken so we had to choose a new name. We wanted to mash up the relevant terms ("graph", "ascii", "art", "chart", and such) and bonus if the new name is a fitting acronym.

In the case of PHART, the acronym made from the first letters of the obvious first words to come to mind was discovered to spell PHART after the non abbreviated words were suggested. Fortuitous; so it had to be.

You may pronounce it the obvious monosyllabic way, or as "eff art", or perhaps "pee heart", or any way that you like, so long as the audience you are speaking it to knows it is PHART you are referring to.

## Really, why?

The mention of not being Perl or a PHP webapp may appear to be throwing shade at the existing solutions, but it is meant in a good-hearted way. Wrapping the OG Graph::Easy is a straightforeard way to go about it, and a web interface to the same is a project I might create as well, but Perl being installed is not the sure ubiquitous thing it omce was, and spinning up a Docker container in order to add ascii art graph output to a python tool seemed a bit excessive.

Additionally, I'm not sure how I didn't find pydot2ascii - which is native pythom - when I first looked for a solution, but even if I had seen it I may not have realized that I could have exported my NX DAG to DOT, and then used pydot2ascii to go from DOT to ascii art.

So now we have PHART, and the ability to render a NX digraph in ASCII/Unicode, read a DOT file, read GraphML, and a few other things in a well-tested Pythom module published to PyPi. I hope ypu find it usedul.

## Installation

requires Python >= 3.10 and NetworkX >= 3.3

```bash
pip install phart
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
- &gt; or < : horizontal flow

These directional indicators are particularly useful for:

- Dependency graphs
- Workflow diagrams
- Process flows
- Any directed relationships

# Extras

## File Format Support

### DOT Files

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

### GraphML Files

PHART supports reading GraphML files:

```python
renderer = ASCIIRenderer.from_graphml("graph.graphml")
print(renderer.render())
```

## Command Line Usage

PHART can be used from the command line to render graph files:

```bash
# Basic usage
phart input.dot

# Save to file instead of stdout
phart input.dot -o output.txt

# GraphML input
phart input.graphml --output viz.txt

# Change node style
phart --style round input.dot

# Force ASCII output (no Unicode)
phart --ascii input.dot

# Adjust spacing
phart --node-spacing 6 --layer-spacing 3 input.dot
```

## License

MIT License
