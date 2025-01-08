# phart

**PHART:** The Python Hierarchical ASCII Representation Tool - A Pure Python graph visualization in ASCII, no external dependencies\*

(\* except NetworkX, which we should probably mention prominently. We just mean no dependencies of the Perl or PHP/webserver types.)

## Features

- Pure Python implementation
- Render using 7-bit ASCII or unicode characters
- No external dependencies (except NetworkX)
- Multiple node styles (square, round, diamond)
- Customizable edge characters
- Support for directed and undirected graphs
- Handles cycles and complex layouts
- Bidirectional edge support

## Examples

<details>

<summary>Example output PHARTs [click triangle/arrow to expand/collapse]</summary>

{% include EXAMPLES.MD %}
</details>

## Why PHART?

Because it is necessary? OK, sorry... Actually it had a few other names early on, but when it came time to upload to PyPi, we discovered the early names we chose were already taken so we had to choose a new name. We wanted to mash up the relevant terms ("graph", "ascii", "art", "chart", and such) and bonus if the new name is a fitting acronym.

In the case of PHART, the acronym made from the first letters of the obvious first words to come to mind was discovered to spell PHART after the non abbreviated words were suggested. Fortuitous; so it had to be.

You may pronounce it the obvious monosyllabic way, or as "eff art", or perhaps "pee heart", or any way that you like, so long as the audience you are speaking it to knows it is PHART you are referring to.

## Really, why?

The mention of not being Perl or a PHP webapp may appear to be throwing shade at the existing solutions, but it is meant in a good-hearted way. Wrapping the OG Graph::Easy is a straightforeard way to go about it, and a web interface to the same is a project I might create as well, but Perl being installed is not the sure ubiquitous thing it omce was, and spinning up a Docker container in order to add ascii art graph output to a python tool seemed a bit excessive.

Additionally, I'm not sure how I didn't find pydot2ascii - which is native python - when I first looked for a solution, but even if I had seen it I may not have realized that I could have exported my NX DAG to DOT, and then used pydot2ascii to go from DOT to ascii art.

So now we have PHART, and the ability to render a NX digraph in ASCII/Unicode, read a DOT file, read GraphML, and a few other things in a well-tested Python module published to PyPi. I hope you find it useful.

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

## Character Sets

PHART supports multiple character sets for rendering:

- `--charset unicode` (default): Uses Unicode box drawing characters and arrows for
  cleaner visualization
- `--charset ascii`: Uses only 7-bit ASCII characters, ensuring maximum compatibility
  with all terminals

Example:

```bash
# Using Unicode (default)
phart graph.dot
# ┌─A─┐
# │   │
# └─B─┘

# Using ASCII only
phart --charset ascii graph.dot
# +-A-+
# |   |
# +-B-+
```

## File Format Support

### DOT Files

- DOT file support
- requires pydot

```bash
pip install phart[extras]
```

or using requirements file

```bash
pip install -r requirements\extra.txt
```

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
