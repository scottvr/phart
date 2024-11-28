"""Showcase of PHART's graph visualization capabilities."""

import networkx as nx
from phart import ASCIIRenderer, NodeStyle, LayoutOptions


def example_dependency_tree():
    """Example of visualizing a software dependency tree."""
    print("\nSoftware Dependency Example:")
    G = nx.DiGraph(
        [
            ("main.py", "utils.py"),
            ("main.py", "config.py"),
            ("utils.py", "helpers.py"),
            ("utils.py", "constants.py"),
            ("config.py", "constants.py"),
            ("helpers.py", "constants.py"),
        ]
    )

    options = LayoutOptions(
        node_style=NodeStyle.MINIMAL, node_spacing=4, layer_spacing=1
    )
    renderer = ASCIIRenderer(G, options=options)
    print(renderer.render())


def example_hierarchical_org():
    """Example of visualizing an organizational hierarchy."""
    print("\nOrganizational Hierarchy Example:")
    G = nx.DiGraph(
        [
            ("CEO", "CTO"),
            ("CEO", "CFO"),
            ("CEO", "COO"),
            ("CTO", "Dev Lead"),
            ("CTO", "Research Lead"),
            ("CFO", "Controller"),
            ("COO", "Sales Dir"),
            ("COO", "Marketing Dir"),
        ]
    )

    options = LayoutOptions(
        node_style=NodeStyle.SQUARE, node_spacing=6, layer_spacing=2
    )
    renderer = ASCIIRenderer(G, options=options)
    print(renderer.render())


def example_network_topology():
    """Example of visualizing a network topology."""
    print("\nNetwork Topology Example:")
    G = nx.DiGraph(
        [
            ("Router1", "Switch1"),
            ("Router1", "Switch2"),
            ("Switch1", "Server1"),
            ("Switch1", "Server2"),
            ("Switch2", "Server3"),
            ("Switch2", "Server4"),
            ("Server1", "Server2"),  # Cross-connection
            ("Server3", "Server4"),  # Cross-connection
        ]
    )

    options = LayoutOptions(node_style=NodeStyle.ROUND, node_spacing=5, layer_spacing=2)
    renderer = ASCIIRenderer(G, options=options)
    print(renderer.render())


def example_workflow():
    """Example of visualizing a workflow/process diagram."""
    print("\nWorkflow Example:")
    G = nx.DiGraph(
        [
            ("Start", "Input"),
            ("Input", "Validate"),
            ("Validate", "Process"),
            ("Process", "Check"),
            ("Check", "Error"),
            ("Check", "Success"),
            ("Error", "Process"),  # Feedback loop
            ("Success", "Output"),
            ("Output", "End"),
        ]
    )

    options = LayoutOptions(
        node_style=NodeStyle.DIAMOND, node_spacing=4, layer_spacing=1
    )
    renderer = ASCIIRenderer(G, options=options)
    print(renderer.render())


def example_dot_import():
    """Example of importing from DOT format."""
    print("\nDOT Import Example:")
    dot_string = """
    digraph G {
        rankdir=LR;
        A -> B -> C;
        A -> D -> C;
        C -> E;
    }
    """
    renderer = ASCIIRenderer.from_dot(dot_string)
    print(renderer.render())


if __name__ == "__main__":
    print("PHART Graph Visualization Examples")
    print("=================================")

    example_dependency_tree()
    example_hierarchical_org()
    example_network_topology()
    example_workflow()
    example_dot_import()

    print("\nCustom Styling Example:")
    print("Different node styles for the same graph:")
    G = nx.balanced_tree(2, 2, create_using=nx.DiGraph)

    for style in NodeStyle:
        print(f"\nUsing {style.name} style:")
        renderer = ASCIIRenderer(G, node_style=style)
        print(renderer.render())
