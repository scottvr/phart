from phart import ASCIIRenderer, NodeStyle, LayoutOptions
import networkx as nx


def example_binary_tree():
    """Example of rendering a binary tree"""
    print("\nBinary Tree Example:")
    # Create a binary tree (r=2) of height 3
    G = nx.balanced_tree(r=2, h=3, create_using=nx.DiGraph)
    # Relabel nodes to be more readable
    mapping = {i: f"N{i}" for i in G.nodes()}
    G = nx.relabel_nodes(G, mapping)

    # Try different node styles
    for style in NodeStyle:
        print(f"\nUsing {style.name} style:")
        options = LayoutOptions(node_style=style)
        renderer = ASCIIRenderer(G, options)
        print(renderer.render())
        print("\n" + "=" * 50)  # Add separator between styles


def example_dependency_graph():
    """Example of rendering a software dependency graph"""
    print("\nDependency Graph Example:")
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

    # Use minimal style for better readability with long names
    options = LayoutOptions(
        node_style=NodeStyle.MINIMAL, node_spacing=6, layer_spacing=2
    )
    renderer = ASCIIRenderer(G, options)
    print(renderer.render())


def example_workflow():
    """Example of rendering a workflow/process diagram"""
    print("\nWorkflow Example:")
    G = nx.DiGraph(
        [
            ("Start", "Input Data"),
            ("Input Data", "Validate"),
            ("Validate", "Process"),
            ("Process", "Error Check"),
            ("Error Check", "Process"),  # Feedback loop
            ("Error Check", "Output"),
            ("Output", "End"),
        ]
    )

    # Use round style for workflow nodes
    options = LayoutOptions(node_style=NodeStyle.ROUND, node_spacing=4, layer_spacing=2)
    renderer = ASCIIRenderer(G, options)
    print(renderer.render())


if __name__ == "__main__":
    example_binary_tree()
    example_dependency_graph()
    example_workflow()
