#!/usr/bin/env python3
"""
Binary Tree Layout Example for PHART

This demonstrates how to use the binary_tree_layout feature with edge attributes
to control left/right positioning of nodes in a tree structure.
"""

import networkx as nx
from phart import ASCIIRenderer, LayoutOptions

def example_1_basic_binary_tree():
    """Basic binary tree with left/right edge attributes."""
    print("=" * 60)
    print("Example 1: Basic Binary Tree with Edge Attributes")
    print("=" * 60)
    
    G = nx.DiGraph()
    
    # Root with two children
    G.add_edge('A', 'B', side='right')
    G.add_edge('A', 'C', side='left')
    
    # B's children
    G.add_edge('B', 'D', side='left')
    G.add_edge('B', 'E', side='right')
    
    # C's children
    G.add_edge('C', 'F', side='right')
    G.add_edge('C', 'G', side='left')
    
    print("\nGraph edges with 'side' attributes:")
    for u, v, data in G.edges(data=True):
        print(f"  {u} -> {v} [side={data.get('side', 'none')}]")
    
    print("\nWithout binary_tree_layout (alphabetical):")
    renderer = ASCIIRenderer(G)
    print(renderer.render())
    
    print("\nWith binary_tree_layout=True:")
    options = LayoutOptions(binary_tree_layout=True)
    renderer = ASCIIRenderer(G, options=options)
    print(renderer.render())


def example_2_numeric_attributes():
    """Binary tree using numeric 0/1 for left/right."""
    print("\n" + "=" * 60)
    print("Example 2: Using Numeric 0/1 for Left/Right")
    print("=" * 60)
    
    G = nx.DiGraph()
    
    # Using 0 for left, 1 for right
    G.add_edge('Root', 'Left', position='0')
    G.add_edge('Root', 'Right', position='1')
    G.add_edge('Left', 'LL', position='0')
    G.add_edge('Left', 'LR', position='1')
    G.add_edge('Right', 'RL', position='0')
    G.add_edge('Right', 'RR', position='1')
    
    print("\nGraph edges with 'position' attributes (0=left, 1=right):")
    for u, v, data in G.edges(data=True):
        print(f"  {u} -> {v} [position={data.get('position', 'none')}]")
    
    print("\nWith binary_tree_layout=True:")
    options = LayoutOptions(binary_tree_layout=True)
    renderer = ASCIIRenderer(G, options=options)
    print(renderer.render())


def example_3_mixed_tree():
    """Tree with some nodes having attributes, others not."""
    print("\n" + "=" * 60)
    print("Example 3: Mixed Tree (some attributes specified, some not)")
    print("=" * 60)
    
    G = nx.DiGraph()
    
    # Some edges with attributes
    G.add_edge('A', 'B', side='left')
    G.add_edge('A', 'C', side='right')
    
    # Some without (will be sorted alphabetically in middle)
    G.add_edge('B', 'D')  # No side specified
    G.add_edge('B', 'E')  # No side specified
    G.add_edge('B', 'F')  # No side specified
    
    print("\nGraph edges:")
    for u, v, data in G.edges(data=True):
        side = data.get('side', 'unspecified')
        print(f"  {u} -> {v} [side={side}]")
    
    print("\nWith binary_tree_layout=True:")
    print("(Nodes without 'side' attribute are sorted alphabetically)")
    options = LayoutOptions(binary_tree_layout=True)
    renderer = ASCIIRenderer(G, options=options)
    print(renderer.render())


def example_4_attribute_names():
    """Demonstrating different attribute names that work."""
    print("\n" + "=" * 60)
    print("Example 4: Different Attribute Names")
    print("=" * 60)
    
    print("\nSupported attribute names: 'side', 'position', 'dir', 'child'")
    print("Supported values: 'left', 'right', 'l', 'r', '0', '1'")
    
    G = nx.DiGraph()
    
    # Different attribute names, all work
    G.add_edge('Root', 'A', side='left')
    G.add_edge('Root', 'B', position='right')
    G.add_edge('A', 'C', dir='l')
    G.add_edge('A', 'D', child='r')
    
    print("\nGraph edges with various attribute names:")
    for u, v, data in G.edges(data=True):
        attrs = ', '.join(f"{k}={v}" for k, v in data.items())
        print(f"  {u} -> {v} [{attrs}]")
    
    print("\nWith binary_tree_layout=True:")
    options = LayoutOptions(binary_tree_layout=True)
    renderer = ASCIIRenderer(G, options=options)
    print(renderer.render())


def example_5_user_request():
    """Example addressing the user's original question."""
    print("\n" + "=" * 60)
    print("Example 5: User's Binary Tree Structure Request")
    print("=" * 60)
    
    G = nx.DiGraph()
    
    # Create a binary tree where we explicitly control left/right
    G.add_edge('1', '2', side='left')
    G.add_edge('1', '3', side='right')
    G.add_edge('2', '4', side='left')
    G.add_edge('2', '5', side='right')
    G.add_edge('3', '6', side='left')
    G.add_edge('3', '7', side='right')
    
    print("\nSimple binary tree with explicit left/right control:")
    print("Node 2 goes left of node 3, etc.")
    
    print("\nWith binary_tree_layout=True:")
    options = LayoutOptions(
        binary_tree_layout=True,
        layer_spacing=3  # More vertical space for clarity
    )
    renderer = ASCIIRenderer(G, options=options)
    print(renderer.render())


if __name__ == '__main__':
    example_1_basic_binary_tree()
    example_2_numeric_attributes()
    example_3_mixed_tree()
    example_4_attribute_names()
    example_5_user_request()
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print("""
To use binary tree layout:

1. Add edge attributes to specify left/right children:
   G.add_edge('parent', 'left_child', side='left')
   G.add_edge('parent', 'right_child', side='right')

2. Enable binary tree layout:
   options = LayoutOptions(binary_tree_layout=True)
   renderer = ASCIIRenderer(G, options=options)

3. Supported attribute names: 'side', 'position', 'dir', 'child'
   Supported values: 'left', 'right', 'l', 'r', '0', '1'

4. Nodes without attributes will be sorted alphabetically
   between left and right children.
""")
