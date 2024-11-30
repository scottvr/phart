"""Performance tests for PHART ASCII renderer."""

import random
import time
import unittest

import networkx as nx  # type: ignore

from phart import ASCIIRenderer, NodeStyle


def create_binary_tree(depth: int) -> nx.DiGraph:
    """Create a binary tree of specified depth."""
    G = nx.DiGraph()

    def add_nodes(parent: int, d: int):
        if d >= depth:
            return
        left, right = 2 * parent + 1, 2 * parent + 2
        G.add_edges_from([(f"N{parent}", f"N{left}"), (f"N{parent}", f"N{right}")])
        add_nodes(left, d + 1)
        add_nodes(right, d + 1)

    add_nodes(0, 0)
    return G


def create_random_dag(n: int, p: float) -> nx.DiGraph:
    """Create random DAG with n nodes and edge probability p."""
    # Create base graph
    G = nx.DiGraph()
    nodes = range(n)
    G.add_nodes_from(nodes)

    # Add edges ensuring acyclicity by only connecting to higher-numbered nodes
    for i in nodes:
        for j in range(i + 1, n):
            if random.random() < p:
                G.add_edge(i, j)

    return G


def create_dependency_graph(n_layers: int, width: int) -> nx.DiGraph:
    """Create layered dependency graph."""
    G = nx.DiGraph()
    prev_layer = [f"L0_{i}" for i in range(width)]
    G.add_nodes_from(prev_layer)

    for layer in range(1, n_layers):
        curr_layer = [f"L{layer}_{i}" for i in range(width)]
        G.add_nodes_from(curr_layer)
        for node in curr_layer:
            deps = random.sample(prev_layer, random.randint(1, min(3, len(prev_layer))))
            G.add_edges_from((dep, node) for dep in deps)
        prev_layer = curr_layer
    return G


class TestPerformance(unittest.TestCase):
    """Performance tests for the ASCII renderer."""

    def setUp(self):
        """Set up performance test parameters."""
        self.styles = list(NodeStyle)
        self.results = {}

    def test_binary_tree_scaling(self):
        """Test performance scaling with binary tree depth."""
        depths = [3, 5, 7, 9]  # 2^depth - 1 nodes
        for depth in depths:
            G = create_binary_tree(depth)
            for style in self.styles:
                renderer = ASCIIRenderer(G, node_style=style)

                start_time = time.perf_counter()
                result = renderer.render()
                elapsed = time.perf_counter() - start_time

                key = f"binary_tree_d{depth}_{style.name}"
                self.results[key] = {
                    "time": elapsed,
                    "nodes": G.number_of_nodes(),
                    "edges": G.number_of_edges(),
                    "output_size": len(result),
                }

    def test_random_dag_scaling(self):
        """Test performance with random DAGs of increasing size."""
        sizes = [10, 50, 100, 200]
        edge_probability = 0.1

        for n in sizes:
            G = create_random_dag(n, edge_probability)
            renderer = ASCIIRenderer(G)

            start_time = time.perf_counter()
            result = renderer.render()
            elapsed = time.perf_counter() - start_time

            key = f"random_dag_n{n}"
            self.results[key] = {
                "time": elapsed,
                "nodes": G.number_of_nodes(),
                "edges": G.number_of_edges(),
                "output_size": len(result),
            }

    def test_dependency_graph_scaling(self):
        """Test performance with layered dependency graphs."""
        configs = [
            (3, 5),  # 3 layers, 5 nodes per layer
            (5, 7),  # 5 layers, 7 nodes per layer
            (7, 10),  # 7 layers, 10 nodes per layer
            (10, 15),  # 10 layers, 15 nodes per layer
        ]

        for n_layers, width in configs:
            G = create_dependency_graph(n_layers, width)
            renderer = ASCIIRenderer(G)

            start_time = time.perf_counter()
            result = renderer.render()
            elapsed = time.perf_counter() - start_time

            key = f"dep_graph_l{n_layers}w{width}"
            self.results[key] = {
                "time": elapsed,
                "nodes": G.number_of_nodes(),
                "edges": G.number_of_edges(),
                "output_size": len(result),
            }

    def tearDown(self):
        """Print performance results."""
        print("\nPerformance Results:")
        print("=" * 80)
        for test, data in sorted(self.results.items()):
            print(f"\n{test}:")
            print(f"  Time: {data['time']:.4f} seconds")
            print(f"  Nodes: {data['nodes']}")
            print(f"  Edges: {data['edges']}")
            print(f"  Output Size: {data['output_size']} characters")


if __name__ == "__main__":
    unittest.main(verbosity=2)
