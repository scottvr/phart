# From Unconnected Nodes to Fully-connected Graph

There is a script in the `examples/` directory to display every possible connectivity combination for a three-node graph.

It's called `triadic_census.py` and it does this:

```python
def generate_triads() -> Dict:
    """Generate all 16 possible directed triads with their standard naming."""
    triads = {
        "003": [],  # Empty triad
        "012": [(1, 2)],  # Single edge
        "102": [(1, 2), (2, 1)],  # Mutual edge
        "021D": [(3, 1), (3, 2)],  # Two edges down
        "021U": [(1, 3), (2, 3)],  # Two edges up
        "021C": [(1, 3), (3, 2)],  # Two edges chain
        "111D": [(1, 2), (2, 1), (3, 1)],  # Mutual + single down
        "111U": [(1, 2), (2, 1), (1, 3)],  # Mutual + single up
        "030T": [(1, 2), (3, 2), (1, 3)],  # Three edges triangle
        "030C": [(1, 3), (3, 2), (2, 1)],  # Three edges cyclic
        "201": [(1, 2), (2, 1), (3, 1), (1, 3)],  # Four edges
        "120D": [(1, 2), (2, 1), (3, 1), (3, 2)],  # Four edges down
        "120U": [(1, 2), (2, 1), (1, 3), (2, 3)],  # Four edges up
        "120C": [(1, 2), (2, 1), (1, 3), (3, 2)],  # Four edges cycle
        "120C": [(1, 2), (2, 1), (1, 3), (3, 2)],  # Four edges cycle
        "210": [(1, 2), (2, 1), (1, 3), (3, 2), (2, 3)],  # Five edges
        "300": [(1, 2), (2, 1), (2, 3), (3, 2), (1, 3), (3, 1)],  # Complete
    }

    graphs = {}
    for name, edge_list in triads.items():
        G = nx.DiGraph()
        G.add_nodes_from([1, 2, 3])  # Always add all three nodes
        G.add_edges_from(edge_list)
        graphs[name] = G
```

The script also contains two lines of code to call phart's render() function, and then some standard fare
text-formatting (left-justification, columnar alignment, newlines and print()) boilerplate for columnar alignment
and subtitling each graph. I will spare you the boilerplate here, but the full script is in the repo.

Being able to manipulate phart's output the same way you would any other 2D string object
in memory and on the terminal is one of the reasons phart came into existence. Anyway, it is a good demonstration of
the ease of use, and power and versatility of such a lightweight approach to visualizing NetworkX graph objects.

## The Triadic Census

First, we're shown this table as a guide to the named graphlets:
```
--------------------------------------------------------------------------------------------
003    |  []           
012    |  [(1, 2)]     
102    |  [(1, 2), (2, 1)]
021D   |  [(3, 1), (3, 2)]
021U   |  [(1, 3), (2, 3)]
021C   |  [(1, 3), (3, 2)]
111D   |  [(1, 2), (2, 1), (3, 1)]
111U   |  [(1, 2), (2, 1), (1, 3)]
030T   |  [(1, 2), (3, 2), (1, 3)]
030C   |  [(1, 3), (3, 2), (2, 1)]
201    |  [(1, 2), (2, 1), (3, 1), (1, 3)]
120D   |  [(1, 2), (2, 1), (3, 1), (3, 2)]
120U   |  [(1, 2), (2, 1), (1, 3), (2, 3)]
120C   |  [(1, 2), (2, 1), (1, 3), (3, 2)]
210    |  [(1, 2), (2, 1), (1, 3), (3, 2), (2, 3)]
300    |  [(1, 2), (2, 1), (2, 3), (3, 2), (1, 3), (3, 1)]
--------------------------------------------------------------------------------------------
```


## The ASCII Diagrams
And now, what you've been waiting for, the diagrams that PHART outputs with the options you can see in the script itself:

```
          003                    012                    102                   021D          
      ┌─────┐                ┌─────┐                ┌─────┐                ┌─────┐          
      │     │                │     │                │     │                │     │          
      │  1  │                │  1  │                │  1  │                │  1  │          
      │     │                │     │                │     │                │     │          
      └─────┘                └─────┘                └─────┘                └─────┘          
                           ┌───┘                  ┌──^                   ┌───^              
                           v                      v                      │                  
┌─────┐     ┌─────┐    ┌─────┐     ┌─────┐    ┌─────┐     ┌─────┐    ┌─────┐     ┌─────┐    
│     │     │     │    │     │     │     │    │     │     │     │    │     │     │     │    
│  2  │     │  3  │    │  2  │     │  3  │    │  2  │     │  3  │    │  3  │────>│  2  │    
│     │     │     │    │     │     │     │    │     │     │     │    │     │     │     │    
└─────┘     └─────┘    └─────┘     └─────┘    └─────┘     └─────┘    └─────┘     └─────┘    
                                                                                            
                                                                                            

         021U                   021C                   111D                   111U          
      ┌─────┐                ┌─────┐                ┌─────┐                ┌─────┐          
      │     │                │     │                │     │                │     │          
      │  1  │                │  3  │                │  1  │                │  1  │          
      │     │                │     │                │     │                │     │          
      └─────┘                └─────┘                └─────┘                └─────┘          
    ┌───┘                  ┌──┘   ^──┐            ┌──^   ^──┐            ┌──^   └──┐        
    v                      v         │            v         │            v         v        
┌─────┐     ┌─────┐    ┌─────┐     ┌─────┐    ┌─────┐     ┌─────┐    ┌─────┐     ┌─────┐    
│     │     │     │    │     │     │     │    │     │     │     │    │     │     │     │    
│  3  │<────│  2  │    │  2  │     │  1  │    │  2  │     │  3  │    │  2  │     │  3  │    
│     │     │     │    │     │     │     │    │     │     │     │    │     │     │     │    
└─────┘     └─────┘    └─────┘     └─────┘    └─────┘     └─────┘    └─────┘     └─────┘    
                                                                                            
                                                                                            

         030T                   030C                    201                   120D          
      ┌─────┐                ┌─────┐                ┌─────┐                ┌─────┐          
      │     │                │     │                │     │                │     │          
      │  3  │                │  1  │                │  1  │                │  1  │          
      │     │                │     │                │     │                │     │          
      └─────┘                └─────┘                └─────┘                └─────┘          
    ┌──┘   ^──┐            ┌──┘   ^──┐            ┌──^  ^──┐             ┌──^   ^──┐        
    v         │            v         │            v        v             v         │        
┌─────┐     ┌─────┐    ┌─────┐     ┌─────┐    ┌─────┐     ┌─────┐    ┌─────┐     ┌─────┐    
│     │     │     │    │     │     │     │    │     │     │     │    │     │     │     │    
│  2  │<────│  1  │    │  3  │────>│  2  │    │  2  │     │  3  │    │  2  │<────│  3  │    
│     │     │     │    │     │     │     │    │     │     │     │    │     │     │     │    
└─────┘     └─────┘    └─────┘     └─────┘    └─────┘     └─────┘    └─────┘     └─────┘    
                                                                                            
                                                                                            

         120U                   120C                    210                    300          
      ┌─────┐                ┌─────┐                ┌─────┐                ┌─────┐          
      │     │                │     │                │     │                │     │          
      │  1  │                │  1  │                │  2  │                │  1  │          
      │     │                │     │                │     │                │     │          
      └─────┘                └─────┘                └─────┘                └─────┘          
    ┌──^   └──┐            ┌──^   └──┐            ┌──^  ^──┐             ┌──^  ^──┐         
    v         v            v         v            v        v             v        v         
┌─────┐     ┌─────┐    ┌─────┐     ┌─────┐    ┌─────┐     ┌─────┐    ┌─────┐     ┌─────┐    
│     │     │     │    │     │     │     │    │     │     │     │    │     │<───>│     │    
│  2  │────>│  3  │    │  2  │<────│  3  │    │  1  │────>│  3  │    │  2  │     │  3  │    
│     │     │     │    │     │     │     │    │     │     │     │    │     │     │     │    
└─────┘     └─────┘    └─────┘     └─────┘    └─────┘     └─────┘    └─────┘     └─────┘
```
