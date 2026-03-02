---
date: 2026-03-01
title: PHART: A Look at the New Layout Strategies
---

# Layout Strategy Examples

Supported modes are:
- **auto** (default) - This is the original PHART hierarchical layout method with explicit handling of triads vertically.
- **hierarchical** - This is the legacy hierarchical layout. Falls back to "layered" if cycle detected.
- **vertical** - This is the legacy "vertical" strategy implemented for explicit handling of triangle graphs.
- **layered** - Most strategies have this as a fallback. Nodes are assigned to topological layers (for DAGs) or BFS-like depth layers (for cyclic/non-DAG directed graphs), then centered per layer.
- **bfs** - Breadth-First Search
- **bipartite** - Arrange the node in two straight lines.
- **btree** - Arrange the nodes as a tree, respecting left/right 'side' attributes on edges.
- **circular** - Arrange the nodes in a circular layout.
- **kamada-kawai** - Positions nodes using Kamada-Kawai path-length cost function. (requires scipy)
- **spring** - Position nodes using Fruchterman-Reingold force-directed algorithm. (fallback for kamada-kawai if scipy not available.)
- **arf** - Position nodes using an attractive-repulsive force model.
- **spiral** - Position nodes along a spiral.
- **shell** - Position nodes in concentric shells (rings), using BFS-derived rings by default.
- **multipartite** - Position nodes in layers of straight lines.
- **planar** - Minimize edge (path) intersections.
- **random** - Positions nodes uniformly at random within the unit square.

## Default/Original (Orthogonal/Hierarchical) Layout
Here's an example of a Graph of circular software dependencies:
```python
   dependencies = {
        "package_a": ["package_b", "requests"],
        "package_b": ["package_c"],
        "package_c": ["package_a"],  # Creates cycle
        "requests": ["urllib3", "certifi"],
    }

    for package, deps in dependencies.items():
        for dep in deps:
            G.add_edge(package, dep)
```
If we then render that with the phart defaults, we get:
```
             [package_a]
           ┌──────↑───────┐
           ↓      │       ↓
      [package_b] │  [requests]
    ┌──────┴──────┼───────┴─────┐
    ↓             ↓             ↓
[certifi]    [package_c]    [urllib3]
```

which is a little bit ambiguous. We can try adding bounding boxes, 

setting `layer_spacing=4`, and `colors=source`:

<img width="400" height="400" alt="circular_dep-default-layout" src="https://github.com/user-attachments/assets/46e097c6-9d35-4c50-ae9d-ecb1747dc5f9" />

That is clearer. But maybe this graph is a good case for 
using one of the new layout algorithms. 

Speaking of **new**.. I know I've already embedded these in the README, but here's these two again, just because I find them so nice to look at. And they're screenshots of my plain text terminal from within vscode:

<img width="400" height="400" alt="unix-family-tree" src="https://github.com/user-attachments/assets/1475614f-0f6b-425e-b088-7f121bef27d9" />

and...

<img width="400" height="400" alt="go-package-dependencies" src="https://github.com/user-attachments/assets/932ce0db-cc4e-42ce-b77e-895ecf80fb56" />

OK. **Now back to our circular dependency graph** with a few different new strategies.


Let's see how it looks with the `bipartite` strategy:

### bipartite

<img width="400" height="400" alt="circular_dep-bipartite-dest_color" src="https://github.com/user-attachments/assets/f901011b-4bdf-4c1f-933f-1b12db29adab" />

It is different. It *is* actually clearer as you can 
plainly see the circular inter-dependencies indicated 
by the layout, colors and edge connection indicators.
We could also have instructed phart to draw all of the bounding boxes to be the size of the widest one, 
which would have the effect of making the two columns look more uniform and obviously straight vertical lines.

How about that new **circular** layout, since it's a _circular_ dependency graph:

### circular

<img width="400" height="400" alt="circular_deps-color-shows-ambiguity-with-center-anchors" src="https://github.com/user-attachments/assets/7be6331c-4203-45d1-a9c4-dbe3437b6da9" />

To me that makes it harder to see the cycle. 
But the color algorithm (this time I used "colors=path") 
and the arrowheads do allow you to deduce what's happening, 
even though some paths are atop one another. We can see that 
`urllib` *appears* to go to `certifi` with a single directed 
arrowhead and a solid green path.  However, since `package_b` 
must be going to `package_c` (by the arrowhead and the color, 
and the fact that we know when there are colliding/overlapping
edges/paths, the color becomes gray), which means that `package_c` 
must be going to `package_a`, and well.. 

Deducing connections is not ideally what we want from a visual representation, 
so we can take that as a cue to uses a different layout, or perhaps the colors 
being gray in so many edge paths gives us another idea. Let's set the edge_anchor
strategy to "ports" instead of the default center anchor for edge paths to be drawn.

Heck, we may not even find color useful if we do that:

<img width="400" height="400" alt="circular_dep-circular_layout" src="https://github.com/user-attachments/assets/dbe2525e-08d4-4e0e-b400-f631b2d98b4f" />

Yeah, it is clear what connects to what now. 

Speaking of **circular**... Sometimes  when there are many nodes, setting `colors=target` 
can give quick and useful visual information. 

Here's a different graph in colored circular layout, with the edge paths colored to match their destination edge for easier visual tracing:

<img width="400" height="400" alt="sem-circular-color-target" src="https://github.com/user-attachments/assets/094ebf83-2cdd-4019-a945-b1179deb4ed8" />

### shell

Similar in shape to the circular layout we have **shell**, 
which is a layout made from nodes arranged in concentric circles:

<img width="400" height="400" alt="sem-shell" src="https://github.com/user-attachments/assets/c587433c-8c4b-4c5c-9cd6-7af013f98afb" />

### spiral

Which brings us to another circle-adjacent layout pattern, 
the archimedes spiral:

<img width="400" height="400" alt="sem-spiral" src="https://github.com/user-attachments/assets/fd38aed7-e06d-4738-a480-1791d9307dde" />

It's visually interesting, but it doesn't add much value in helping interpret any relationships; 
it's just cool-looking. Here are a few more where the layout is really just an aestheic or 
page-constrait concern; a matter of preference.


### spring

<img width="400" height="400" alt="sem-spring" src="https://github.com/user-attachments/assets/62c1fd43-fad2-4f42-9d96-48fd2e2fa3f2" />

### Kamada-Kawai

<img width="400" height="400" alt="sem-kamada-kawai" src="https://github.com/user-attachments/assets/62d9afaf-57bb-492c-94be-94090e380978" />

### ARF (attractive-repulsive force)

<img width="400" height="400" alt="sem-arf" src="https://github.com/user-attachments/assets/0311ff86-5804-4811-8ce8-4b02326fc417" />

I feel like there was a reason I did this one in b&w, but I can't recall what I 
wanted to demonstrate by that. *shrug*

### random

<img width="400" height="400" alt="sem-random1" src="https://github.com/user-attachments/assets/cc271919-6f3c-4244-99c3-2202d82eb5cf" />

Really, it is random. Rendered again with the exact same options:

<img width="400" height="400" alt="sem-random2" src="https://github.com/user-attachments/assets/17426958-bae4-44de-8a07-352102ef31a5" />

### planar

<img width="400" height="400" alt="sem-planar" src="https://github.com/user-attachments/assets/dcc02cd5-af9a-429e-8dfd-a6b2f275062b" />

### multipartite

<img width="400" height="400" alt="sem-multipartite-colored-dest" src="https://github.com/user-attachments/assets/1249878e-1f55-4a51-b16f-e8674dd70a9e" />

### bfs

<img width="400" height="80" alt="sem-bfs" src="https://github.com/user-attachments/assets/be0ed61d-a2b4-4715-9cdb-0331f311a6a1" />

So, as the **breadth-first sort** makes clear in that image, 
it is not the best choice to layout this particular graph. 

Speaking of choices. I wanted to demonstrate a little more about 
how other options might be worth tweaking before changing the entire layout strategy. 
(Then again, ease of trying out different options is the reason I put so much time 
into the phart cli. It's fun to experiment.) 

So, take a look at this graph render, using **phart**'s original "legacy" layout engine:

<img width="400" height="160" alt="sempath-1" src="https://github.com/user-attachments/assets/67ad1ea4-5986-4656-8a6d-d36e2ad7cc08" />

It's correct, but it seems intuitively inverted. 
We have a `--flow up` option for cases like that:
<img width="400" height="160" alt="sempath2" src="https://github.com/user-attachments/assets/85e2f87a-b3d1-410b-a5d8-30ab710b7eda" />

That makes more sense to me inverted like that, 
but what a mess at those bottom rows. We can increase `layer_spacing`:

<img width="400" height="80" alt="sempath-4" src="https://github.com/user-attachments/assets/895721ee-2bc9-4ff5-a21a-b3645ac4498a" />


And still confusing. We'll increases the `layer_spacing` further:

<img width="400" height="80" alt="sempath-5" src="https://github.com/user-attachments/assets/9e4d9c89-4d01-4d1c-9a9c-d180c05ff58a" />


OK, so maybe one of the other layouts demonstrates why it is useful to have these additional options available for placing the nodes in a 2D plane for visualization. This one is just too hard to follow in the hierarchical layout with orthogonal edges. 

I hope you enjoyed taking a look at how different layouts effect legibility of the information conveyed by your ascii visualization of a graph using **phart**.

## Other layouts
Let me know if you wan't to discuss implementing another layout strategy
by opening an Issue or starting a Discussion thread. Cheers!
