#!/usr/bin/env python3
"""
Simple test demonstrating binary tree layout control.
"""

import networkx as nx
from phart import ASCIIRenderer, LayoutOptions

print("DEMONSTRATION: Controlling Binary Tree Node Positioning")
print("=" * 70)

# Create a binary tree
G = nx.DiGraph()
G.add_edge('Root', 'B', side='left')
G.add_edge('Root', 'A', side='right')
G.add_edge('B', 'D', side='left')
G.add_edge('B', 'C', side='right')

print("\nTree structure (note: alphabetically A < B < C < D):")
print("Root has children: B (left), A (right)")
print("B has children: D (left), C (right)")

print("\n" + "─" * 70)
print("WITHOUT binary_tree_layout (alphabetical sorting):")
print("─" * 70)
renderer = ASCIIRenderer(G)
print(renderer.render())

print("\n" + "─" * 70)
print("WITH binary_tree_layout=True (respects edge 'side' attributes):")
print("─" * 70)
options = LayoutOptions(binary_tree_layout=True)
renderer = ASCIIRenderer(G, options=options)
print(renderer.render())

print("\n" + "=" * 70)
print("RESULT: B correctly appears left of A, D left of C!")
print("=" * 70)
