#!/usr/bin/env python3
"""
CLI-Unaware Script - No get_options() helper!

This script has ZERO knowledge that it might be run via CLI.
It just creates graphs normally with LayoutOptions.
The CLI should transparently merge its options.
"""

import networkx as nx
from phart import ASCIIRenderer, LayoutOptions


def main():
    """Main function to avoid double execution."""
    print("=" * 70)
    print("CLI-Unaware Script Test")
    print("=" * 70)
    print("\nThis script knows nothing about CLI - just uses LayoutOptions directly.")
    print("When run via CLI with --ascii flag, ASCII should be used everywhere!")

    # Create a binary tree
    G = nx.DiGraph()
    G.add_edge('A', 'B', side='right')
    G.add_edge('A', 'C', side='left')
    G.add_edge('B', 'D', side='left')
    G.add_edge('B', 'E', side='right')

    print("\n" + "-" * 70)
    print("Test 1: No options at all")
    print("-" * 70)
    r1 = ASCIIRenderer(G)
    print(r1.render())

    print("\n" + "-" * 70)
    print("Test 2: Explicit options with binary_tree_layout=True")
    print("-" * 70)
    print("(Script has NO knowledge of CLI or get_options())")
    options = LayoutOptions(binary_tree_layout=True)
    r2 = ASCIIRenderer(G, options=options)
    print(r2.render())

    print("\n" + "-" * 70)
    print("Test 3: Explicit options with custom layer_spacing")
    print("-" * 70)
    options = LayoutOptions(binary_tree_layout=True, layer_spacing=4)
    r3 = ASCIIRenderer(G, options=options)
    print(r3.render())

    print("\n" + "=" * 70)
    print("Expected Results:")
    print("=" * 70)
    print("Standalone: All use Unicode arrows (↑ →)")
    print("Via CLI with --ascii: All use ASCII chars (^ > | -)")
    print("Via CLI with --binary-tree: CLI flag would apply to all")
    print("BUT user's binary_tree_layout=True in Tests 2 & 3 is preserved!")
    print("So Tests 2 & 3 show C left of B (binary tree layout)")


if __name__ == '__main__':
    main()
