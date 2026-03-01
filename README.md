# phart

**PHART:** The Python Hierarchical ASCII Representation Tool - A Pure Python graph visualization in ASCII, no external dependencies\*
_\*except NetworkX, which should be mentioned prominently, as rendering NX digraphs as ASCII was the entire reason for phart's creation. but **phart** will **not** require you to stand up a webserver to run PHP and install Perl and some libraries just to render a Graph in 7-bit text (or UTF-8 or Unicode) from Python._

## Features

- Render using ASCII (7-bit) or Unicode characters
- Optional ANSI color for either charset
- Multiple node styles (square, round, diamond, custom)
- Customizable edge characters
- Support for directed and undirected graphs
- Handles cycles and complex layouts
- Bidirectional edge support
- Edge attribute support (and attribute-based coloring of edges)
- Over ten layout strategies
- Orthogonal edge paths (all 90 degree turns, "Manhattan" style)

## New Layout Strategies

See [LAYOUT-STRATEGIES.md](https://github.com/scottvr/phart/blob/main/LAYOUT-STRATEGIES.md) in the repo for some examples of output.
I have also documented one of the scripts in the `examples/` directory and shown its output here in [TRIADIC-CENSUS.md](https://github.com/scottvr/phart/blob/main/examples/docs/TRIADIC-CENSUS.md)

Anyone interested in representing potentially very dense and complex graphs with an ascii line-drawing generator
such that they find themselves here reading this is probably someone with a fair likelyhood to find this next
trick as amusing as I did.

There is a Gallery of some of the visualization capabilities native(-ish) to NetworkX using matplotlib and GraphViz,
and maybe some other tools. Among the things in that Gallery I found was this demonstration of ["Rainbow Coloring"](https://networkx.org/documentation/stable/auto_examples/drawing/plot_rainbow_coloring.html) that shows this neat image, which I will reproduce by way of a screenshot of their website:

<img width="800" height="800" alt="nx-rainbow-graph-screenshot" src="https://github.com/user-attachments/assets/ce5aea65-c086-48ae-9c4d-b2dc324b1da7" />

Pretty cool, huh? Well, one thing that was an early goal in the development of PHART was to be able to go to websites like the one linked above,and find demos of how these systems visualize various graphs, and then to try to get phart to ingest it and see how it works (or doesn't) to represent complex systems of relationships under the very tight constraints it is working with.. It does a pretty good job most of the time, and gets better as I and others attempt things that it hasn't yet done before.

### It's not a Spirograph, it's not yarn art, but better than that - it's from P-HART

So, of course when I saw the code used to generate the image above using NetworkX and matplotlib, I wanted to see if I could get **phart** to handle it. With the recent addition of ANSI color code escape sequences to its limited palettte with which to express itself, I am quite pleased to show you phart's interpretation of the geometric design made by the colored edge paths between nodes as in the image above. Recalll that while phart does have the capabilities originally planned for it - that of drawing rectangles with 7-bit terminal characters, and it has since acquired the ability to translate a graph into a circular layout within those means - still it is, after all, doing so using only orthogonal paths, 90 degree angles... "**Manhattan routing**", as it is sometimes called.

So, with only 90 degree jogs available to connect any node to another, and with this graph being comprised of 13 nodes, each connected to all the other nodes... (This complete connectivity is precisely why the circular layout with distance-based coloring gives the pleasing appearance that it does in the image above. My friends and colleagues working in fields involving computer networking, though, may be slightly triggered by [this concept](https://en.wikipedia.org/wiki/Network_topology#Fully_connected_network), and start thinking of things like [this](https://datatracker.ietf.org/doc/html/rfc7727) or [this](https://datatracker.ietf.org/doc/html/rfc2328). _I realize that STP is an IEEE standard, I found an RFC on the topic to link to because an IETF document will have 7-bit hand-drawn ASCII diagrams in it, which is a topic near and dear to me, as you possibly can tell._)

### You can get there from here, just probably not as a crow flies

If you did the math, you know that there are 78 connections to account for in this graph (or 156, depending on how you count a bidirectional path; we're going to use the same connection to go both ways in our diagram. You will see it is quite crowded already.)

Having rambled on long enough now, let me show you phart's latest masterpiece of ASCII Art (ok, I used Unicode characters in this one, and phart colored it them with ANSI color escape codes, but it's still plain text!). It's rendering is quite fetching in its own way I think.  


<img width="800" height="800" alt="NX-complete-graph" src="https://github.com/user-attachments/assets/ac28aa5c-b6b2-4a23-a03f-4a6839076c55" />  

<br />  

Maybe someday phart will get official acknowledgement from the folks in the space, such as NetworkX or GraphViz, by way of displaying some of its more pleasing and interesting output in their own Galleries. Maybe.


---  

## NEW Features Feb 2026

- binary_tree sort mode
- binary_tree sort can respect "side" properties ("left", 'right")
- bounding box mode (line art rectangles with configurable inner padding)
- (optionally) use labels instead of node names when rendering diagram.
- (optionally) color edges with ANSI colors to help discern edge paths in dense complex diagrams
- and several **new layout strategies** including `circular`, `bfs`, `shell`, `Kamada-Kawai`, and others.

### Labelling with label properties

The label support can make an interesting but uninformative diagram suddenly more meaningful, and beautiful IMHO.
Take a look at this **Unix Family Tree** (also from a .dot file); I think it's gorgeous.

<img width="700" height="600" alt="unix-family-tree" src="https://github.com/user-attachments/assets/1475614f-0f6b-425e-b088-7f121bef27d9" />

### ANSI color edge paths

ANSI color support turned out more interesting than I expected. Not completely satisfied with it, I ended up enabling four modes to the feature: color by source, color by target, color by path, and color by edge attributes. Here's an example of `edge_anchors=ports`, `colors=source`, using a graph of Golang package dependencies.

<img width="700" height="600" alt="go-package-dependencies" src="https://github.com/user-attachments/assets/932ce0db-cc4e-42ce-b77e-895ecf80fb56" />

I'm not sure it's all _that_ much easier to discern what goes to where, but it sure is fun to look at.

## NEWER! - Accidental Features 

So, I inadvertently merged some code into main that was not intended to be released yet, because it's - while not _**not**_ working, per se - still a little half-baked, and not documented well. 

Nevertheless, some might notice the command-line options, when runnning ``phart --help`` for example,  and try to use some of the features, so I figured I may as well explain one of the goofier ones. I've written about it here in [GHM-LAtEX.md](https://github.com/scottvr/phart/blob/main/docs/GHM-LATEX.md).


---

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
can read _python code_ that itself makes use of phart such as that above, so that it can be tested from the command-line, allowing you to try out various display options without having to edit your code repeatedly to see what works best.

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
renderer = ASCIIRenderer(G, node_style=NodeStyle.SQUARE)
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

---

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
arguments for the script you've given it as an input file. We will just separate the
switches meant for phart from any switches meant for the script it is loading by an extra
`--`, like so:

`phart --charset unicode --style minimal  --hpad 1 --binary-tree
  --node-spacing 1 --layer-spacing 4  --vpad 0  --edge-anchors ports --bboxes
  examples/collatz.py -- 1 `

This results in the following graph:

```
depth: 1
max_depth: 1
max_val 2
          ┌────┐
          │ 1  │
          └────┘
         ┌─┘  └──┐
         │       │
         v       v
     ┌────┐    ┌────┐
     │ 2  │    │ Z1 │
     └────┘    └────┘
    ┌─┘  └──┐
    │       │
    v       v
┌────┐    ┌────┐
│ L1 │    │ L2 │
└────┘    └────┘
```

You can see that all of the number terms are on the left, while Leaves, Zero, Fractals,
etc are to the right (and also the terminal Leaves at the bottom of the tree.)

Now that phart has ANSI color support, we can also use the same 'side' edge attribute
that enables the left/right sorting to apply color to the paths representing edges in
the output. (And, because it is simply console text, you can pipe it elsewhere, redirect it, and so on.
As we'll see here, I will `tail` to just the last 15 lines of output so I can just see
something new and interesting, further down the tree:

``` bash
$ phart --colors attr --edge-color-rule side:left=green,right=red --bbox --btree \
 --charset unicode --no-color-nodes examples/collatz.py -- 5 | tail -15
```


This gives us the following output, which I'll share via screenshot, because GitHub is picky&ast;&ast; about letting one color a markdown document:

<img width="325" height="218" alt="collatz-5-tail-15" src="https://github.com/user-attachments/assets/bcd4cd1b-322a-464a-b1b6-e0e1359332a0" />

There are more examples scripts in the repo, along with a README in the examples/ directory

&ast;&ast; [There's' an app for that!(tm)](https://github.com/scottvr/phart/blob/main/docs/GHM-LATEX.md)

---

## NEW! Feb 2026 - Layout Strategies

Now, explicitly exposed and selectable by the user, phart's layout_strategy is now configurable.
See [LAYOUT-STRATEGIES.md](https://github.com/scottvr/phart/blob/main/LAYOUT-STRATEGIES.md) in the repo for demos.

### NEWER! - Accidental Features 

So, I inadvertently merged some code into main that was not intended to be released yet, because it's - while not _not_ working, per se - still a little half-baked, so it's not documented well. Nevertheless, some might notice the command-line options when runnning ``phart --help``, for example and try to use some of the features, so I figured I may as well explain one of the goofier ones. I've written about it here in [GHM-LAtEX.md](https://github.com/scottvr/phart/blob/main/docs/GHM-LATEX.md)


## Why "PHART"?

The acronym was a fortuitous accident from the non-abbreviated words that the letters represent: **Python Hierarchical ASCII Rendering Tool**.

### Really, why?

When I point out that phart is not a Perl or a PHP webapp, it may appear that I am
_throwing shade_ at the existing solutions, but it is meant in a good-hearted way.
Wrapping the OG perl Graph::Easy is a straightforward way to go about it, and a web interface to the same is a project I might create have created as well, but it is no
longer a certainty that a system you are working on will have Perl installed these days,
and spinning up a Docker container in order to add ascii line art graph visualizations to
a python tool seemed a bit excessive, _even for me._

Also, I'm not sure how I didn't find _pydot2ascii_ - which is native python - when I first
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

For your convenience, any 'extra' requirements can be installed bundled by category.
For instance, if you require DOT file support to have phart use one of the dot files
from the `examples/` directory, all requirements, including pydot, to use the examples
can be installed with `piip install -e .'[examples]'`.

To install all `extra` requirements (e.g., `fonttools` for svg rendering support, `scipy` for Kamada-Kawai layout support), you can install them all with `pip instaall -e .'[extra]'`. Additionally, there are `[developer]` and `[test]` module requirements that can be installed, or to get _everything-everywhere-all-at-once_, you can `pip install -e .'[all]'`. (Note: If installing from PyPi, you would use `pip install 'phart[all]'` rather than the `-e .` syntax for installing from source.)

## The CLI

````bash
usage: phart [-h] [--output OUTPUT] [--style {minimal,square,round,diamond,custom,bbox}]
             [--node-spacing NODE_SPACING] [--layer-spacing LAYER_SPACING]
             [--charset {ascii,ansi,unicode}] [--ascii] [--function FUNCTION] [--binary-tree]
             [--layout {arf,auto,bfs,bipartite,btree,circular,hierarchical,kamada-kawai,layered,multipartite,planar,random,shell,spiral,spring,vertical}]
             [--flow-direction {down,up,left,right}] [--bboxes] [--hpad HPAD] [--vpad VPAD]
             [--uniform] [--edge-anchors {auto,center,ports}] [--labels]
             [--colors {attr,none,path,source,target}] [--edge-color-rule RULE]
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
  --charset {ascii,ansi,unicode}
                        Character set to use for rendering (default: unicode)
  --ascii               Force ASCII output (deprecated, use --charset ascii instead)
  --function, -f FUNCTION
                        Function to call in Python file (default: main)
  --binary-tree         Shortcut to enable binary tree layout (respects edge 'side' attributes for left/right)
  --layout, --layout-strategy {auto,arf,bfs,bipartite,btree,circular,hierarchical,kamada-kawai,layered,multipartite,planar,random,shell,spiral,spring,vertical}
                        Node positioning strategy (default: auto - legacy hierarchical, vertical for triads)
  --flow-direction, --flow {down,up,left,right}
                        Layout flow direction: down (default, root at top), up (root at
                        bottom), left (root at right), right (root at left)
  --bboxes              Draw line-art boxes around nodes
  --hpad HPAD           Horizontal padding inside node boxes (default: 1)
  --vpad VPAD           Vertical padding inside node boxes (default: 0)
  --uniform, --size-to-widest
                        Use widest node text as the width baseline for all node boxes
  --edge-anchors {auto,center,ports}
                        Edge anchor strategy: auto (default), center, or ports (distributed
                        on box edges)
  --labels              Use node labels (if present) for displayed node text
  --colors {attr,none,path,source,target}
                        ANSI edge coloring mode: none (default), source, target, path, or attr
  --edge-color-rule RULE
                        Attribute-driven edge color rule for --colors attr. Format:
                        <attribute>:<value>=<color>[,<value>=<color>...] (repeatable)```
````

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
- `--charset ansi`: Uses ASCII glyphs while allowing ANSI color escapes (good for
  older terminals that support ANSI colors but not Unicode line-art)

## File Format Support

## SVG Renderer Modes

PHART now supports two SVG text rendering modes:

- `--svg-text-mode text` (default): emits `<text>` nodes using the configured font family.
- `--svg-text-mode path`: emits each visible character as a glyph outline `<path>` for deterministic vector output.

Path mode requirements:

- install optional dependencies: `pip install phart[svg]`
- provide either:
  - `--svg-font-path /path/to/font.ttf` (recommended), or
  - `--svg-font-family "Family Name"` with matplotlib-based font lookup available

Example:

```bash
phart --output-format svg \
  --svg-text-mode path \
  --svg-font-path /System/Library/Fonts/SFNSMono.ttf \
  graph.dot > graph.svg
```

See [svg-renderer.md](svg-renderer.md) for details and troubleshooting.

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

#### I hope you enjoy it, and include many surprising plain-text diagrams in your next paper/book/website/video. Let me know if you

do something cool with it, or if it breaks on your graph.

## License

MIT License
