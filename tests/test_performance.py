import unittest
import time
import networkx as nx
import random
from memory_profiler import profile
from phart import ASCIIGraphRenderer

def create_binary_tree(depth: int) -> nx.DiGraph:
    """Create a binary tree of specified depth"""
    G = nx.DiGraph()
    def add_nodes(parent: int, d: int):
        if d >= depth: return
        left, right = 2*parent + 1, 2*parent + 2
        G.add_edges_from([(f"N{parent}", f"N{left}"), (f"N{parent}", f"N{right}")])
        add_nodes(left, d+1)
        add_nodes(right, d+1)
    add_nodes(0, 0)
    return G

def create_random_dag(n: int, p: float) -> nx.DiGraph:
    """Create random DAG with n nodes and edge probability p"""
    return nx.gnp_random_graph(n, p, directed=True, acyclic=True)

def create_dependency_graph(n_layers: int, width: int) -> nx.DiGraph:
    """Create layered dependency graph"""
    G = nx.DiGraph()
    prev_layer = [f"L0_{i}" for i in range(width)]
    G.add_nodes_from(prev_layer)
    
    for layer in range(1, n_layers):
        curr_layer = [f"L{layer}_{i}" for i in range(width)]
        G.add_nodes_from(curr_layer)
        # Add random dependencies to previous layer
        for node in curr_layer:
            deps = random.sample(prev_layer, random.randint(1, min(3, len(prev_layer))))
            G.add_edges_from((dep, node) for dep in deps)
        prev_layer = curr_layer
    return G

class TestPerformance(unittest.TestCase):
    @profile
    def test_binary_tree_scaling(self):
        """Test performance scaling with binary tree depth"""
        depths = [3, 5, 7, 9]  # 2^depth - 1 nodes
        times = []
        
        for depth in depths:
            G = create_binary_tree(depth)
            renderer = ASCIIGraphRenderer(G)
            
            start_time = time.perf_counter()
            result = renderer.render()
            end_time = time.perf_counter()
            
            elapsed = end_time - start_time
            times.append(elapsed)
            
            print(f"\nBinary Tree Depth {depth}:")
            print(f"Nodes: {G.number_of_nodes()}")
            print(f"Time: {elapsed:.4f} seconds")
            print(f"Output size: {len(result.splitlines())}x{max(len(line) for line in result.splitlines())}")

    @profile
    def test_random_dag_scaling(self):
        """Test performance with random DAGs of increasing size"""
        sizes = [10, 50, 100, 200]
        edge_probability = 0.1
        times = []
        
        for n in sizes:
            G = create_random_dag(n, edge_probability)
            renderer = ASCIIGraphRenderer(G)
            
            start_time = time.perf_counter()
            result = renderer.render()
            end_time = time.perf_counter()
            
            elapsed = end_time - start_time
            times.append(elapsed)
            
            print(f"\nRandom DAG Size {n}:")
            print(f"Edges: {G.number_of_edges()}")
            print(f"Time: {elapsed:.4f} seconds")
            print(f"Output size: {len(result.splitlines())}x{max(len(line) for line in result.splitlines())}")

    @profile
    def test_dependency_graph_scaling(self):
        """Test performance with layered dependency graphs"""
        configs = [
            (3, 5),   # 3 layers, 5 nodes per layer
            (5, 7),   # 5 layers, 7 nodes per layer
            (7, 10),  # 7 layers, 10 nodes per layer
            (10, 15)  # 10 layers, 15 nodes per layer
        ]
        times = []
        
        for n_layers, width in configs:
            G = create_dependency_graph(n_layers, width)
            renderer = ASCIIGraphRenderer(G)
            
            start_time = time.perf_counter()
            result = renderer.render()
            end_time = time.perf_counter()
            
            elapsed = end_time - start_time
            times.append(elapsed)
            
            print(f"\nDependency Graph {n_layers}x{width}:")
            print(f"Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")
            print(f"Time: {elapsed:.4f} seconds")
            print(f"Output size: {len(result.splitlines())}x{max(len(line) for line in result.splitlines())}")

if __name__ == '__main__':
    unittest.main(verbosity=2)
