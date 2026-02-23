#!/usr/bin/env python3
"""
Simple Flow Direction Test

Shows flow direction with a simple 3-node graph.
"""

import networkx as nx
from phart import ASCIIRenderer, LayoutOptions


def main():
    print("=" * 70)
    print("Simple Flow Direction Test (3-node graph)")
    print("=" * 70)

    # Simple graph: A -> B, A -> C
    G = nx.DiGraph()
    G.add_edge("A", "B")
    G.add_edge("A", "C")

    print("\nGraph: A -> B, A -> C\n")

    # DOWN
    print("-" * 70)
    print("DOWN: Traditional top-down")
    print("-" * 70)
    options = LayoutOptions(flow_direction="down")
    renderer = ASCIIRenderer(G, options=options)
    print(renderer.render())

    # UP
    print("\n" + "-" * 70)
    print("UP: Dependencies flow upward")
    print("-" * 70)
    options = LayoutOptions(flow_direction="up")
    renderer = ASCIIRenderer(G, options=options)
    print(renderer.render())

    # RIGHT
    print("\n" + "-" * 70)
    print("RIGHT: Left-to-right flow")
    print("-" * 70)
    options = LayoutOptions(flow_direction="right")
    renderer = ASCIIRenderer(G, options=options)
    print(renderer.render())

    # LEFT
    print("\n" + "-" * 70)
    print("LEFT: Right-to-left flow")
    print("-" * 70)
    options = LayoutOptions(flow_direction="left")
    renderer = ASCIIRenderer(G, options=options)
    print(renderer.render())

    print("\n" + "=" * 70)
    print("Notice how arrows always point toward the parent (A)")
    print("=" * 70)


if __name__ == "__main__":
    main()
