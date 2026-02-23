import networkx as nx
from phart import ASCIIRenderer


def create_circular_deps():
    """Create a dependency graph with circular references."""
    G = nx.DiGraph()

    # Circular dependency example
    dependencies = {
        "package_a": ["package_b", "requests"],
        "package_b": ["package_c"],
        "package_c": ["package_a"],  # Creates cycle
        "requests": ["urllib3", "certifi"],
    }

    for package, deps in dependencies.items():
        for dep in deps:
            G.add_edge(package, dep)

    return G


def main():
    # Circular dependencies
    print("\nCircular Dependencies:\n")
    G = create_circular_deps()
    renderer = ASCIIRenderer(G)
    print(renderer.render())


if __name__ == "__main__":
    main()
