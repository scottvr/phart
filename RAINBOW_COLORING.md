
## "Rainbow Coloring" demo

Anyone interested in representing potentially very dense and complex graphs with an ascii line-drawing generator
such that they find themselves here reading this is probably someone with a fair likelyhood to find this next
trick as amusing as I did.

There is a Gallery of some of the visualization capabilities native(-ish) to NetworkX using matplotlib and GraphViz,
and maybe some other tools. Among the things in that Gallery I found was this demonstration of ["Rainbow Coloring"](https://networkx.org/documentation/stable/auto_examples/drawing/plot_rainbow_coloring.html) that shows this neat image, which I will reproduce by way of a screenshot of their website:

<img width="800" height="800" alt="nx-rainbow-graph-screenshot" src="https://github.com/user-attachments/assets/ce5aea65-c086-48ae-9c4d-b2dc324b1da7" />

Pretty cool, huh? Well, one thing that was an early goal in the development of PHART was to be able to go to websites like the one linked above,and find demos of how these systems visualize various graphs, and then to try to get phart to ingest it and see how it works (or doesn't) to represent complex systems of relationships under the very tight constraints it is working with.. It does a pretty good job most of the time, and gets better as I and others attempt things that it hasn't yet done before.

### not a spirograph, it's not yarn art, not better than that - it's just p-hart

So, of course when I saw the code used to generate the image above using NetworkX and matplotlib, I wanted to see if I could get **phart** to handle it. With the recent addition of ANSI color code escape sequences to its limited palettte with which to express itself, I am quite pleased to show you phart's interpretation of the geometric design made by the colored edge paths between nodes as in the image above. Recalll that while phart does have the capabilities originally planned for it - that of drawing rectangles with 7-bit terminal characters, and it has since acquired the ability to translate a graph into a circular layout within those means - still it is, after all, doing so using only orthogonal paths, 90 degree angles... "**Manhattan routing**", as it is sometimes called.

<img width="700" height="700" alt="rainjbow-coloring-13-nodes-correct-sorting" src="https://github.com/user-attachments/assets/78646dd0-b371-4652-b7db-3a1dce91716b" />

So, with only 90 degree jogs available to connect any node to another, and with this graph being comprised of 13 nodes, each connected to all the other nodes... (This complete connectivity is precisely why the circular layout with distance-based coloring gives the pleasing appearance that it does in the original image. My friends and colleagues working in fields involving computer networking, though, may be slightly triggered by [this concept](https://en.wikipedia.org/wiki/Network_topology#Fully_connected_network), and start thinking of things like [this](https://datatracker.ietf.org/doc/html/rfc7727) or [this](https://datatracker.ietf.org/doc/html/rfc2328). _I realize that STP is an IEEE standard, I found an RFC on the topic to link to because an IETF document will have 7-bit hand-drawn ASCII diagrams in it, which is a topic near and dear to me, as you possibly can tell._)

### You can get there from here, just probably not as a crow flies

If you did the math, you know that there are 78 connections to account for in this graph (or 156, depending on how you count a bidirectional path; we're going to use the same connection to go both ways in our diagram. You will see it is quite crowded already.

Here's the original cool-but-incorrect render I had prominently at the top before I realized that the "rainbow" is not the same pattern due to some nodes being out if order, so the length-based color is askew for several edges. Notice that while it makes an interesting rainbow-ish gradient from left to right, it isn't what was intended and you can see the bottom-most node has two same-length horizontal lines to each side, and they are of different colors despite being the same apparent distance. (now notice the labels on the nodes; that's the problem. 0 should be next to 1 and on side and 11 on the other, by shortest (graph) distance; a "green-length" edge (path) got incorrectly respresented by a short (Cartesian) length line.) Here:

<img width="700" height="700"  src="https://github.com/user-attachments/assets/41a402f1-4443-491e-9033-fa5795b7cf9d" />
