import unittest
import networkx as nx
from phart import ASCIIGraphRenderer, NodeStyle, LayoutOptions

class TestASCIIGraphRenderer(unittest.TestCase):
    def setUp(self):
        """Set up some common test graphs"""
        # Simple chain
        self.chain = nx.DiGraph([("A", "B"), ("B", "C")])

        # Disconnected components
        self.disconnected = nx.DiGraph([("A", "B"), ("C", "D")])

        # Graph with no edges
        self.no_edges = nx.DiGraph()
        self.no_edges.add_nodes_from(["A", "B", "C"])

        # Diamond shape (convergent paths)
        self.diamond = nx.DiGraph([("A", "B"), ("A", "C"), ("B", "D"), ("C", "D")])

        # Cycle
        self.cycle = nx.DiGraph([("A", "B"), ("B", "C"), ("C", "A")])

        # Complex graph with multiple paths
        self.complex = nx.DiGraph([
            ("A", "B"), ("A", "C"), ("B", "D"), ("C", "D"),
            ("D", "E"), ("B", "C"), ("E", "F"), ("F", "D")  # Creates cycle
        ])

    def test_simple_chain(self):
        """Test rendering of a simple chain graph"""
        renderer = ASCIIGraphRenderer(self.chain)
        result = renderer.render()
        self.assertIn("[A]", result)
        self.assertIn("[B]", result)
        self.assertIn("[C]", result)
        # Verify vertical alignment
        lines = result.split('\n')
        self.assertTrue(any('A' in line and 'B' not in line for line in lines))
        self.assertTrue(any('B' in line and 'A' not in line and 'C' not in line for line in lines))
        self.assertTrue(any('C' in line and 'B' not in line for line in lines))

    def test_no_edges(self):
        """Test rendering of a graph with no edges"""
        renderer = ASCIIGraphRenderer(self.no_edges)
        result = renderer.render()
        self.assertIn("[A]", result)
        self.assertIn("[B]", result)
        self.assertIn("[C]", result)
        # All nodes should be on the same line
        self.assertTrue(any('A' in line and 'B' in line and 'C' in line
                          for line in result.split('\n')))

    def test_disconnected_components(self):
        """Test rendering of disconnected components"""
        renderer = ASCIIGraphRenderer(self.disconnected)
        result = renderer.render()
        self.assertIn("[A]", result)
        self.assertIn("[B]", result)
        self.assertIn("[C]", result)
        self.assertIn("[D]", result)
        # Verify components are separated
        a_line = next(i for i, line in enumerate(result.split('\n')) if 'A' in line)
        c_line = next(i for i, line in enumerate(result.split('\n')) if 'C' in line)
        self.assertNotEqual(a_line, c_line)

    def test_cycle_handling(self):
        """Test proper handling of cycles"""
        renderer = ASCIIGraphRenderer(self.cycle)
        result = renderer.render()
        # Verify all nodes are present
        self.assertIn("[A]", result)
        self.assertIn("[B]", result)
        self.assertIn("[C]", result)
        # Verify cycle is rendered (nodes not all on same line)
        lines = result.split('\n')
        nodes_per_line = [sum(node in line for node in 'ABC') for line in lines]
        self.assertTrue(max(nodes_per_line) < 3)

    def test_node_styles(self):
        """Test different node styles"""
        styles = {
            NodeStyle.SQUARE: ("[A]", "[B]"),
            NodeStyle.ROUND: ("(A)", "(B)"),
            NodeStyle.DIAMOND: ("<A>", "<B>"),
            NodeStyle.MINIMAL: ("A", "B")
        }

        for style, (start, end) in styles.items():
            options = LayoutOptions(node_style=style)
            renderer = ASCIIGraphRenderer(self.chain, options)
            result = renderer.render()
            self.assertIn(start, result)
            self.assertIn(end, result)

    def test_complex_graph(self):
        """Test rendering of a complex graph with multiple paths and cycles"""
        renderer = ASCIIGraphRenderer(self.complex)
        result = renderer.render()
        # Verify all nodes are present
        for node in "ABCDEF":
            self.assertIn(f"[{node}]", result)
        # Verify basic layout properties
        lines = result.split('\n')
        # Root should be at top
        self.assertTrue(any('A' in line and not any(n in line for n in "BCDEF")
                          for line in lines))
        # Multiple paths should be rendered
        self.assertTrue(len([line for line in lines if '│' in line]) > 1)

    def test_empty_graph(self):
        """Test handling of empty graph"""
        empty = nx.DiGraph()
        renderer = ASCIIGraphRenderer(empty)
        result = renderer.render()
        self.assertEqual(result.strip(), "")

    def test_single_node(self):
        """Test rendering of single-node graph"""
        single = nx.DiGraph()
        single.add_node("A")
        renderer = ASCIIGraphRenderer(single)
        result = renderer.render()
        self.assertEqual(result.strip(), "[A]")

    def test_custom_layout_options(self):
        """Test custom layout options"""
        options = LayoutOptions(
            node_spacing=6,
            layer_spacing=3,
            edge_vertical='|',
            edge_horizontal='-',
            edge_cross='+',
            node_style=NodeStyle.SQUARE
        )
        renderer = ASCIIGraphRenderer(self.diamond, options)
        result = renderer.render()
        self.assertIn("|", result)  # Custom vertical edge
        self.assertIn("-", result)  # Custom horizontal edge
        self.assertIn("+", result)  # Custom cross character

if __name__ == '__main__':
    unittest.main()
