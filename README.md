# phart

**PHART:** The Python Hierarchical ASCII Representation Tool - A Pure Python graph visualization in ASCII, no external dependencies\*

*\*except NetworkX, which should be mentioned prominently, as rendering NX digraphs as ASCII was the entire reason for phart's creation. but **phart** will **not** require you to stand up a webserver to run PHP and install Perl and some libraries just to render a Graph in 7-bit text (or UTF-8 or Unicode) from Python.*

## Features

- Render using 7-bit ASCII or unicode characters
- Multiple node styles (square, round, diamond, custom)
- Customizable edge characters
- Support for directed and undirected graphs
- Handles cycles and complex layouts
- Bidirectional edge support
- Orthogonal (yet correct, though perhaps unexpected) Triad Layout

## New Layout Strategies

See [LAYOUT-STRATEGIES.md](https://github.com/scottvr/phart/blob/main/LAYOUT-STRATEGIES.md) in the repo for demos.
   

## NEW Features Feb 2026
 * binary_tree sort mode
 * binary_tree sort can respect "side" properties ("left", 'right")
 * bounding box mode (line art rectangles with configurable inner padding)
 *(optionally) use labels instead of node names when rendering diagram.
 *(optionally) color edges with ANSI colors to help discern edge paths in dense complex diagrams
 * and several **new layout strategies** including `circular`, `bfs`, `shell`, `Kamada-Kawai`, and others.


### Labelling with label properties

The label support can make an interesting but uninformative diagram suddenly more meaningful, and beautiful IMHO. 
Take a look at this **Unix Family Tree** (also from a .dot file); I think it's gorgeous.

<img width="700" height="600" alt="unix-family-tree" src="https://github.com/user-attachments/assets/1475614f-0f6b-425e-b088-7f121bef27d9" />


### ANSI color edge paths

ANSI color support turned out more interesting than I expected. Not completely satisfied with it, I ended up enabling three modes to the feature: color by source, color by target, and color by path. Here's an example of `edge_anchors=ports`, `colors=source`, using a graph of Golang package dependencies. 

<img width="700" height="600" alt="go-package-dependencies" src="https://github.com/user-attachments/assets/932ce0db-cc4e-42ce-b77e-895ecf80fb56" />

I'm  not sure it's all *that* much easier to discern what goes to where, but it sure is fun to look at.

----

## Usage Examples

phart can be used **programmatically**:
```python
import networkx as nx
from phart import ASCIIRenderer, NodeStyle

def demonstrate_basic_graph():
    print("\nBasic Directed Graph:")
    G = nx.DiGraph()
    G.add_edges_from([("A", "B"), ("A", "C"), ("B", "D"), ("C", "D")])

    renderer = ASCIIRenderer(G)
    print(renderer.render())
```
which will output this very underwhelming diagram:
```
Basic Directed Graph:

   [A]
 +--+---+
 v      v
[B]    [C]
 +--+---+
    v
   [D]
```

phart also comes as a handy **CLI tool**, set up for you when you `pip install` phart.
The phart **CLI** can read graphs in **graphml** or **dot** format. Additionally, the phart CLI
can reaad *python code* that itseslf makes use of phart such as that above, so that it can be tested from the command-line, allowing you to try out various display options without having to edit your code repeatedly to see what works best.

phart supports ASCII and Unicode, and will try to use the sensible default for your 
terminal environment.

### Let's try another one

Let's make a simple balanced tree:
```bash
$ cat > balanced_tree.py
```
```python
import networkx as nx
from phart import ASCIIRenderer, NodeStyle
G = nx.balanced_tree(2, 2, create_using=nx.DiGraph)
renderer = ASCIIRenderer(G, inode_style=NodeStyle.SQUARE)
print(renderer.render())
```
and when we run that tiny script, we see:
```bash
$ python balanced_tree.py
```
```
          [0]
    ┌──────┴──────┐
    ↓             ↓
   [1]           [2]
 ┌──┴───┐      ┌──┴───┐
 ↓      ↓      ↓      ↓
[3]    [4]    [5]    [6]
```

----

### Output options

phart has lots of output options. Here's a good use for the **cli** as I described above. 
We can test other options, without having to edit that python script we just wrote.

Let's see how the balanced tree looks with the nodes in bounding boxes:
```bash
$ phart balanced_tree.py --bbox --hpad 2 --style minimal --layer-spacing 3  --ascii
                +-----+
                |  0  |
                +-----+
        +----------+----------+
        v                     v
     +-----+               +-----+
     |  1  |               |  2  |
     +-----+               +-----+
   +----+-----+          +----+-----+
   v          v          v          v
+-----+    +-----+    +-----+    +-----+
|  3  |    |  4  |    |  5  |    |  6  |
+-----+    +-----+    +-----+    +-----+
```

We can increasae the space between "layers" of nodes, we can move the edges to connect to/from "ports" on the most efficient side of the nodes, and we can render in unicode, using the same script, by passing the options via the command-line until we find what we like:

```
$ phart balanced_tree.py --bbox --hpad 2 --style minimal --layer-spacing 4 --edge-anchors ports    
                ┌─────┐
                │  0  │
                └─────┘
        ┌────────┘   └────────┐
        │                     │
        ↓                     ↓
     ┌─────┐               ┌─────┐
     │  1  │               │  2  │
     └─────┘               └─────┘
   ┌──┘   └───┐          ┌──┘   └───┐
   │          │          │          │
   ↓          ↓          ↓          ↓
┌─────┐    ┌─────┐    ┌─────┐    ┌─────┐
│  3  │    │  4  │    │  5  │    │  6  │
└─────┘    └─────┘    └─────┘    └─────┘
```
We can put a NodeStyle around our label, and put a bounding box around that, and have all 
edges come out of the center of the boxes.

```
$ phart balanced_tree.py --bbox --hpad 0 --style round --layer-spacing 4 --edge-anchors center
             ┌───┐
             │(0)│
             └───┘
      ┌────────┤
      │        └────────┐
      ↓                 ↓
    ┌───┐             ┌───┐
    │(1)│             │(2)│
    └───┘             └───┘
  ┌───┤             ┌───┤
  │   └────┐        │   └────┐
  ↓        ↓        ↓        ↓
┌───┐    ┌───┐    ┌───┐    ┌───┐
│(3)│    │(4)│    │(5)│    │(6)│
└───┘    └───┘    └───┘    └───┘
```

Let's look a slightly more interesting graph, courtesy of phart user @deostroll, in the [Discussions](https://github.com/scottvr/phart/discussions/15).

His script generates a Collatz Tree, and takes an argument for the depth for which you wish to calculate terms. As you will see, we can pass arguments for the **phart cli** to use as 
arguments for the script you've given it as an input file.  We will just separate the
switches meant for phart from any switches meant for the script it is loading by an extra
 `--`, like so:

`phart --charset unicode --style minimal  --hpad 1 --binary-tree 
  --node-spacing 1 --layer-spacing 4  --vpad 0  --edge-anchors ports --bboxes 
  deostroll/collatz.py -- 3`

This results in the following graph:
```
                    ┌───┐
                    │ 1 │
                    └───┘
                 ┌────┤
                 │    └────────────────────┐
                 ↓                         ↓
               ┌───┐                    ┌────┐
               │ 2 │                    │ Z1 │
               └───┘                    └────┘
            ┌────┤
            │    └───────────────┐
            ↓                    ↓
          ┌───┐               ┌────┐
          │ 4 │               │ F1 │
          └───┘               └────┘
       ┌────┤
       │    └──────────┐
       ↓               ↓
     ┌───┐          ┌────┐
     │ 8 │          │ E1 │
     └───┘          └────┘
   ┌───┤
   │   └─────┐
   ↓         ↓
┌────┐    ┌────┐
│ L1 │    │ L2 │
└────┘    └────┘
```
You can see that all of the number terms are on the left, while Leaves, Zero, Fractals, 
etc  are to the right (and also the terminal Leaves at the bottom of the tree.)

We can see what this graph would look like without the binary-tree sorting (which respects "side" properties such as "left" and "right" in your graph.) We'll pass a `4` to deostroll's `collatz.py`, this time with ascii output, and a simple "diamond" styling, without the "left/right" properties being read:

`phart --charset unicode --layer-spacing 4  --vpad 0 --style diamond  --charset ascii deostroll/collatz.py -- 4`
This gives us:
```
                      <001>
                        +----+
  +---------------------+    |
  v                          v
<#Z1>                      <002>
                             +---+
           +-----------------+   |
           v                     v
         <#F1>                 <004>
                                 +----+
                    +------------+    |
                    v                 v
                  <#E1>             <008>
                                      +---+
                             +--------+   |
                             v            v
                           <#F2>        <016>
                                      +---+
                                      |   +----+
                                      v        v
                                    <#L1>    <#L2>
```

There are plenty more examples in the repo, along with a README in the examples/ directory
that includes the output of a very early release of phart.

----

## NEW! Feb 2026 - Layout Strategies

Now, explicitly exposed and selectable by the user, phart's layout_strategy is now configurable.
See [LAYOUT-STRATEGIES.md](https://github.com/scottvr/phart/blob/main/LAYOUT-STRATEGIES.md) in the repo for demos.

## Why "PHART"?

The acronym was a fortuitous accident from the non-abbreviated words that the letters represent: **Python Hierarchical ASCII Rendering Tool**.

### Really, why?

When I point out that phart is not a Perl or a PHP webapp, it may appear that I am
*throwing shade* at the existing solutions, but it is meant in a good-hearted way. 
Wrapping the OG perl Graph::Easy is a straightforward way to go about it, and a web interface to the same is a project I might create have created as well, but it is no 
longer a certainty that a system you are working on will have Perl installed these days, 
and spinning up a Docker container in order to add ascii line art graph visualizations to 
a python tool seemed a bit excessive, *even for me.*

Also, I'm not sure how I didn't find *pydot2ascii* - which is native python - when I first
looked for a solution, but even if I had, it may not have obvious to me that I could have
exported my NX DAG to DOT, and then used pydot2ascii to go from DOT to an ascii diagram.

So, for better or worse, we have PHART, and the ability to render a NX digraph in ASCII and Unicode, to read a DOT file, read GraphML, and a few other things in a well-tested Python module published to PyPi. I hope you find it useful.

# Installation

requires Python >= 3.10 and NetworkX >= 3.3

From PyPi (the phart package there is out of date at the moment):
```bash
pip install phart
```
Or for the latest version:
```
git clone https://github.com/scottvr/phart
cd phart
python -mvenv .venv
. .venv/bin/activate
# or .venv\Scripts\activate on Windows
pip install .
```

## The CLI
```bash
usage: phart [-h] [--output OUTPUT] [--style {minimal,square,round,diamond,custom,bbox}]
             [--node-spacing NODE_SPACING] [--layer-spacing LAYER_SPACING]
             [--charset {ascii,unicode}] [--ascii] [--function FUNCTION] [--binary-tree]
             [--layout {arf,auto,bfs,bipartite,circular,kamada-kawai,multipartite,planar,random,shell,spiral,spring}]
             [--flow-direction {down,up,left,right}] [--bboxes] [--hpad HPAD] [--vpad VPAD]
             [--uniform] [--edge-anchors {center,ports}] [--labels]
             [--colors {none,path,source,target}]
             input

PHART: Python Hierarchical ASCII Rendering Tool

positional arguments:
  input                 Input file (.dot, .graphml, or .py format)

options:
  -h, --help            show this help message and exit
  --output, -o OUTPUT   Output file (if not specified, prints to stdout)
  --style {minimal,square,round,diamond,custom,bbox}
                        Node style (default: square, or minimal when --bboxes is enabled)
  --node-spacing NODE_SPACING
                        Horizontal space between nodes (default: 4)
  --layer-spacing LAYER_SPACING
                        Vertical space between layers (default: 3)
  --charset {ascii,unicode}
                        Character set to use for rendering (default: unicode)
  --ascii               Force ASCII output (deprecated, use --charset ascii instead)
  --function, -f FUNCTION
                        Function to call in Python file (default: main)
  --binary-tree         Enable binary tree layout (respects edge 'side' attributes)
  --layout, --layout-strategy {arf,auto,bfs,bipartite,circular,kamada-kawai,multipartite,planar,random,shell,spiral,spring}
                        Node positioning strategy (default: auto)
  --flow-direction, --flow {down,up,left,right}
                        Layout flow direction: down (default, root at top), up (root at
                        bottom), left (root at right), right (root at left)
  --bboxes              Draw line-art boxes around nodes
  --hpad HPAD           Horizontal padding inside node boxes (default: 1)
  --vpad VPAD           Vertical padding inside node boxes (default: 0)
  --uniform, --size-to-widest
                        Use widest node text as the width baseline for all node boxes
  --edge-anchors {center,ports}
                        Edge anchor strategy: center (default) or ports (distributed on box
                        edges)
  --labels              Use node labels (if present) for displayed node text
  --colors {none,path,source,target}
                        ANSI edge coloring mode: none (default), source, target, or path```
```

## Quick Start

```python
import networkx as nx
from phart import ASCIIRenderer

def create_circular_deps():
    """Create a dependency graph with circular references."""
    G = nx.DiGraph()

    # Circular dependency example
    dependencies = {
        "package_a": ["package_b", "requests"],
        "package_b": ["package_c"],
        "package_c": ["package_a"],  # Creates cycle
        "requests": ["urllib3", "certifi"],
    }

    for package, deps in dependencies.items():
        for dep in deps:
            G.add_edge(package, dep)

    return G
     
def main():
    # Circular dependencies
    print("\nCircular Dependencies:")
    G = create_circular_deps()
    renderer = ASCIIRenderer(G)
    print(renderer.render())     
     
if __name__ == "__main__":
    main()
```

This will output:

```
Circular Dependencies:
             [package_a]
           ┌──────┼───────┐
           ↓      ↑       ↓
      [package_b] │  [requests]
    ┌──────┴──────┼───────┴─────┐
    ↓             │             ↓
[certifi]    [package_c]    [urllib3]
```

You can also run `phart yourscript.py` and tweak the output variables via command-line arguments.

We might want to tweak the spacing, the character set, add some bounding boxes, etc. The phart cli is your friend for experimenting with styling.

The renderer shows edge direction using arrows:

- v : downward flow
- ^ : upward flow
- &gt; or < : horizontal flow

Speaking of "circular", there's a bunch of exampels of the Circular Layout strategy, among with many others in a documented dedicated to that purpose.

See [LAYOUT-STRATEGIES.md](https://github.com/scottvr/phart/blob/main/LAYOUT-STRATEGIES.md) in the repo for these demos.
   


# Extras

## Character Sets

- `--charset unicode` (default): Uses Unicode box drawing characters and arrows for
  cleaner visualization
- `--charset ascii`: Uses only 7-bit ASCII characters, ensuring maximum compatibility
  with all terminals

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

### DOT Example
```bash
$ python
>>> from phart import ASCIIRenderer
>>> import networkx as nx
>>> dot = '''
... digraph G {
...     A -> B
...     B -> C
... }
... '''
>>> renderer = ASCIIRenderer.from_dot(dot)
>>> print(renderer.render())
[A]
 │
 ↓
[B]
 │
 ↓
[C]
```

### Note on DOT format support:

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

or, of course just
`phart [--options] graph.graphml`

## Python Files

While developing and testing some new functionality, I had some demo scripts that themselves contained functions for spitting out various graphs and I wanted to test just a specific graph's function from a given file, so this feature was added; likely no one else will ever need this functionality.

PHART can directly execute Python files that create and render graphs. When given a Python file, PHART will:

1. First try to execute the specified function (if `--function` is provided)
2. Otherwise, try to execute a `main()` function if one exists
3. Finally, execute code in the `if __name__ == "__main__":` block

You can execute the phart python file in a couple of ways:

```bash
# Execute main() or __main__ block (default behavior)
phart graph.py

# Execute a specific function
phart graph.py --function demonstrate_graph

# Use specific rendering options (as already shown)
phart graph.py --charset ascii --style round
```

### Option handling when passed a .py file

- Command-line options will override general settings (like --charset or --style)
- Custom settings (like custom_decorators) are ~~never~~mostly never overridden by command-line defaults. Sometimes you can even combine multiple conflicting style options
to interesting effect. (I will get around to fixing those things.)

This means you can set specific options in your code while still using command-line
options to adjust general rendering settings.

#### I hope you enjoy it, and include many surprising plain-text diagrams in your next paper/book/website/video. Let me know if you do something cool with it, or if it breaks on your graph.

## License

MIT License
