"""
Example of using PHART to visualize package dependencies.
"""

import networkx as nx
from phart import ASCIIRenderer, NodeStyle


def create_sample_dependencies():
    """Create a sample package dependency graph."""
    G = nx.DiGraph()

    # Main package dependencies
    dependencies = {
        "my-app": ["flask", "sqlalchemy", "celery"],
        "flask": ["werkzeug", "jinja2", "click"],
        "sqlalchemy": ["greenlet"],
        "celery": ["click", "redis"],
        "jinja2": ["markupsafe"],
    }

    # Add all edges
    for package, deps in dependencies.items():
        for dep in deps:
            G.add_edge(package, dep)

    return G


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
    print("Package Dependency Examples")
    print("=========================")

    # Simple dependency tree
    print("\nTypical Package Dependencies:")
    G = create_sample_dependencies()
    renderer = ASCIIRenderer(G, node_style=NodeStyle.MINIMAL)
    print(renderer.render())

    # Circular dependencies
    print("\nCircular Dependencies:")
    G = create_circular_deps()
    renderer = ASCIIRenderer(G)
    print(renderer.render())

    # Detect and print cycles
    cycles = list(nx.simple_cycles(G))
    if cycles:
        print("\nDetected dependency cycles:")
        for cycle in cycles:
            print(" -> ".join(cycle + [cycle[0]]))


if __name__ == "__main__":
    main()
