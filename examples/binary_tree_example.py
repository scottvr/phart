#!/usr/bin/env python3

import networkx as nx
from phart import ASCIIRenderer, LayoutOptions

def main():
    print("=" * 70)
    print("Binary Tree Layout: Non-Alphabetical Example")
    print("=" * 70)
    print("\nThis example uses node names that would sort differently")
    print("alphabetically vs. when respecting 'side' attributes:")
    print("  Alphabetically: A < B < C < D < E < F < G")
    print("  By position: C left of B, G left of F, etc.")
    
    G = nx.DiGraph()
    
    # Root with children in non-alphabetical order
    G.add_edge('A', 'B', side='right')   # B goes RIGHT (but B < C alphabetically)
    G.add_edge('A', 'C', side='left')    # C goes LEFT
    
    # B's children
    G.add_edge('B', 'D', side='left')
    G.add_edge('B', 'E', side='right')
    
    # C's children  
    G.add_edge('C', 'F', side='right')   # F goes RIGHT (but F < G alphabetically)
    G.add_edge('C', 'G', side='left')    # G goes LEFT
    
    print("\n" + "-" * 70)
    print("Graph edges with 'side' attributes:")
    print("-" * 70)
    for u, v, data in G.edges(data=True):
        print(f"  {u} -> {v} [side={data.get('side', 'none')}]")
    
    print("\n" + "=" * 70)
    print("WITHOUT binary_tree_layout (alphabetical sorting):")
    print("=" * 70)
    print("Notice: B is left of C (alphabetical), F is left of G")
    options = LayoutOptions(binary_tree_layout=False, layer_spacing=3, use_ascii=True)
    renderer = ASCIIRenderer(G, options=options)
    print(renderer.render())
    
    print("\n" + "=" * 70)
    print("WITH binary_tree_layout=True:")
    print("=" * 70)
    print("Notice: C is left of B (respects 'side'), G is left of F")
    options = LayoutOptions(binary_tree_layout=True, layer_spacing=3, use_ascii=True)
    renderer = ASCIIRenderer(G, options=options)
    print(renderer.render())
    