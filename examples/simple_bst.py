#!/usr/bin/env python3
"""
Simple test demonstrating binary tree layout control.
"""

import networkx as nx
from phart import ASCIIRenderer, LayoutOptions


def get_options(**kwargs):
    """Get options, merging with CLI defaults if present."""
    user_options = LayoutOptions(**kwargs)
    
    if hasattr(ASCIIRenderer, 'default_options') and ASCIIRenderer.default_options is not None:
        from dataclasses import asdict, fields
        
        cli_dict = asdict(ASCIIRenderer.default_options)
        user_dict = asdict(user_options)
        merged_dict = {}
        
        for field in fields(LayoutOptions):
            field_name = field.name
            if field_name == 'instance_id':
                continue
            
            # CLI takes precedence for rendering options
            if field_name in ['use_ascii', 'node_style', 'node_spacing', 'layer_spacing']:
                cli_val = cli_dict.get(field_name)
                user_val = user_dict.get(field_name)
                merged_dict[field_name] = cli_val if cli_val is not None else user_val
            else:
                # User code controls semantic options
                user_val = user_dict.get(field_name)
                cli_val = cli_dict.get(field_name)
                merged_dict[field_name] = user_val if user_val is not None else cli_val
        
        return LayoutOptions(**merged_dict)
    else:
        return user_options


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
options = get_options(binary_tree_layout=True)
renderer = ASCIIRenderer(G, options=options)
print(renderer.render())

print("\n" + "=" * 70)
print("RESULT: B correctly appears left of A, D left of C!")
print("=" * 70)
