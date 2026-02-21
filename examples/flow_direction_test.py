#!/usr/bin/env python3
"""
Flow Direction Feature Test

Demonstrates all four flow directions: down, up, left, right
"""

import networkx as nx
from phart import ASCIIRenderer, LayoutOptions


def create_test_graph():
    """Create a simple binary tree for testing."""
    G = nx.DiGraph()
    G.add_edge('Root', 'Left', side='left')
    G.add_edge('Root', 'Right', side='right')
    G.add_edge('Left', 'LL', side='left')
    G.add_edge('Left', 'LR', side='right')
    G.add_edge('Right', 'RL', side='left')
    G.add_edge('Right', 'RR', side='right')
    return G


def main():
    print("=" * 70)
    print("Flow Direction Feature Demonstration")
    print("=" * 70)
    print("\nThis shows the same binary tree in all four flow directions.")
    print("Notice how the arrows adapt to show parent-child relationships.\n")

    G = create_test_graph()

    # DOWN (default) - Root at top
    print("=" * 70)
    print("FLOW: DOWN (default) - Root at top, children below")
    print("=" * 70)
    print("Arrows point UP toward parents")
    options = LayoutOptions(
        binary_tree_layout=True,
        flow_direction='down',
        layer_spacing=2
    )
    renderer = ASCIIRenderer(G, options=options)
    print(renderer.render())

    # UP - Root at bottom
    print("\n" + "=" * 70)
    print("FLOW: UP - Root at bottom, children above")
    print("=" * 70)
    print("Arrows point DOWN toward parents")
    options = LayoutOptions(
        binary_tree_layout=True,
        flow_direction='up',
        layer_spacing=2
    )
    renderer = ASCIIRenderer(G, options=options)
    print(renderer.render())

    # RIGHT - Root at left
    print("\n" + "=" * 70)
    print("FLOW: RIGHT - Root at left, children to the right")
    print("=" * 70)
    print("Arrows point LEFT toward parents")
    options = LayoutOptions(
        binary_tree_layout=True,
        flow_direction='right',
        layer_spacing=2
    )
    renderer = ASCIIRenderer(G, options=options)
    print(renderer.render())

    # LEFT - Root at right
    print("\n" + "=" * 70)
    print("FLOW: LEFT - Root at right, children to the left")
    print("=" * 70)
    print("Arrows point RIGHT toward parents")
    options = LayoutOptions(
        binary_tree_layout=True,
        flow_direction='left',
        layer_spacing=2
    )
    renderer = ASCIIRenderer(G, options=options)
    print(renderer.render())

    print("\n" + "=" * 70)
    print("Usage Examples")
    print("=" * 70)
    print("""
In Python code:
    options = LayoutOptions(flow_direction='up')
    renderer = ASCIIRenderer(G, options=options)

Via CLI:
    phart mygraph.dot --flow-direction up
    phart script.py --flow up --ascii

Use cases:
    - DOWN: Org charts, family trees (traditional top-down)
    - UP: Dependency graphs, build systems (dependencies flow up)
    - RIGHT: Timelines, process flows (left-to-right reading)
    - LEFT: Right-to-left language layouts, some phylogenetic trees
""")


if __name__ == '__main__':
    main()
