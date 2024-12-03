"""Test suite for PHART ASCII graph renderer."""

import unittest
import sys

import networkx as nx  # type: ignore

from phart import ASCIIRenderer, LayoutOptions, NodeStyle

from pathlib import Path

import tempfile


class TestASCIIRenderer(unittest.TestCase):
    """Test cases for basic rendering functionality and encoding."""

    def setUp(self):
        print(f"\nPython version: {sys.version}")
        print(f"NetworkX version: {nx.__version__}")

        # Try both construction methods to see difference
        try:
            print("\nTrying constructor with edge list:")
            self.chain = nx.DiGraph([("A", "B"), ("B", "C")])
        except Exception as e:
            print(f"Constructor failed: {type(e).__name__}: {e}")

        try:
            print("\nTrying add_edges_from:")
            G = nx.DiGraph()
            G.add_edges_from([("A", "B"), ("B", "C")])
            print("add_edges_from succeeded")
        except Exception as e:
            print(f"add_edges_from failed: {type(e).__name__}: {e}")

        """Set up common test graphs."""
        # Existing test graph setup...
        self.chain = nx.DiGraph([("A", "B"), ("B", "C")])
        self.tree = nx.DiGraph(
            [("A", "B"), ("A", "C"), ("B", "D"), ("B", "E"), ("C", "F")]
        )

        # Diamond pattern (convergent paths)
        self.diamond = nx.DiGraph([("A", "B"), ("A", "C"), ("B", "D"), ("C", "D")])

        # Graph with cycle
        self.cycle = nx.DiGraph([("A", "B"), ("B", "C"), ("C", "A")])

        # Disconnected components
        self.disconnected = nx.DiGraph([("A", "B"), ("C", "D")])

        # Complex graph
        self.complex = nx.DiGraph(
            [
                ("A", "B"),
                ("A", "C"),
                ("B", "D"),
                ("C", "D"),
                ("D", "E"),
                ("B", "C"),
                ("E", "F"),
                ("F", "D"),  # Creates cycle
            ]
        )

    def test_basic_chain(self):
        """Test rendering of a simple chain graph."""
        renderer = ASCIIRenderer(self.chain)
        result = renderer.render()
        lines = result.split("\n")

        # Verify nodes appear in correct order
        self.assertTrue(any("A" in line and "B" not in line for line in lines))
        self.assertTrue(
            any("B" in line and "A" not in line and "C" not in line for line in lines)
        )
        self.assertTrue(any("C" in line and "B" not in line for line in lines))

        # Verify edge characters
        self.assertTrue(any("│" in line or "|" in line for line in lines))

    def test_tree_structure(self):
        """Test rendering of a tree structure."""
        renderer = ASCIIRenderer(self.tree)
        result = renderer.render()
        lines = result.split("\n")

        # Root should be at top
        self.assertTrue(
            any("A" in line and not any(c in line for c in "BCDEF") for line in lines)
        )

        # Verify branching structure
        b_line = next(i for i, line in enumerate(lines) if "B" in line)
        c_line = next(i for i, line in enumerate(lines) if "C" in line)
        self.assertEqual(b_line, c_line)  # B and C should be on same level

        # Verify leaves
        d_line = next(i for i, line in enumerate(lines) if "D" in line)
        e_line = next(i for i, line in enumerate(lines) if "E" in line)
        f_line = next(i for i, line in enumerate(lines) if "F" in line)
        self.assertEqual(d_line, e_line)  # D and E should be on same level
        self.assertEqual(e_line, f_line)  # E and F should be on same level

    def test_node_styles(self):
        """Test different node style options."""
        for style in NodeStyle:
            renderer = ASCIIRenderer(
                self.chain, options=LayoutOptions(node_style=style)
            )
            result = renderer.render()

            if style == NodeStyle.SQUARE:
                self.assertIn("[A]", result)
                self.assertIn("[B]", result)
            elif style == NodeStyle.ROUND:
                self.assertIn("(A)", result)
                self.assertIn("(B)", result)
            elif style == NodeStyle.DIAMOND:
                self.assertIn("<A>", result)
                self.assertIn("<B>", result)
            else:  # MINIMAL
                self.assertIn("A", result)
                self.assertIn("B", result)

    def test_cycle_handling(self):
        """Test proper handling of cycles in graphs."""
        renderer = ASCIIRenderer(self.cycle)
        result = renderer.render()
        lines = result.split("\n")

        # Verify all nodes are present
        for node in "ABC":
            self.assertTrue(any(node in line for line in lines))

        # Nodes shouldn't all be on same line
        nodes_per_line = [sum(1 for n in "ABC" if n in line) for line in lines]
        self.assertTrue(max(nodes_per_line) < 3)

    def test_disconnected_components(self):
        """Test handling of disconnected components."""
        # Create a graph with two clearly disconnected components
        self.disconnected = nx.DiGraph(
            [
                ("A", "B"),  # Component 1
                ("C", "D"),  # Component 2
            ]
        )
        renderer = ASCIIRenderer(self.disconnected)
        result = renderer.render()
        lines = result.split("\n")

        # Find all lines containing each component
        comp1_lines = set(
            i for i, line in enumerate(lines) if any(node in line for node in "AB")
        )
        comp2_lines = set(
            i for i, line in enumerate(lines) if any(node in line for node in "CD")
        )

        # Components should not share any lines
        self.assertTrue(
            not comp1_lines & comp2_lines,
            "Disconnected components should be rendered on different lines",
        )
        # Components should have some vertical separation
        min1, max1 = min(comp1_lines), max(comp1_lines)
        min2, max2 = min(comp2_lines), max(comp2_lines)
        self.assertTrue(
            max1 < min2 or max2 < min1, "Components should be vertically separated"
        )

    def test_empty_graph(self):
        """Test handling of empty graph."""
        empty = nx.DiGraph()
        renderer = ASCIIRenderer(empty)
        result = renderer.render()
        self.assertEqual(result.strip(), "")

    def test_single_node(self):
        """Test rendering of single-node graph."""
        single = nx.DiGraph()
        single.add_node("A")
        renderer = ASCIIRenderer(single)
        result = renderer.render()
        self.assertEqual(result.strip(), "[A]")

    def test_from_dot(self):
        """Test creation from DOT format."""
        dot_string = """
        digraph {
            A -> B;
            B -> C;
        }
        """
        renderer = ASCIIRenderer.from_dot(dot_string)
        result = renderer.render()

        # Verify basic structure
        self.assertIn("A", result)
        self.assertIn("B", result)
        self.assertIn("C", result)

    def test_auto_ascii_detection(self):
        """Test that ASCII mode is auto-detected correctly."""
        renderer = ASCIIRenderer(self.chain)
        self.assertEqual(renderer.options.use_ascii, not renderer._can_use_unicode())

    def test_force_ascii_mode(self):
        """Test forcing ASCII mode."""
        renderer = ASCIIRenderer(self.chain, use_ascii=True)
        result = renderer.render()
        self.assertTrue(all(ord(c) < 128 for c in result))

    def test_unicode_mode(self):
        """Test Unicode mode."""
        renderer = ASCIIRenderer(self.chain, use_ascii=False)
        result = renderer.render()
        self.assertTrue(any(ord(c) > 127 for c in result))

    def test_file_writing(self):
        """Test writing to file with proper encoding."""

        renderer = ASCIIRenderer(self.chain)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as f:
            name = f.name
        try:
            renderer.write_to_file(name)
            with open(name, "r", encoding="utf-8") as f2:
                content = f2.read()
                self.assertEqual(content, renderer.render())
        finally:
            Path(name).unlink()  # Clean up temp file

    def test_graphml_import(self):
        """Test creating renderer from GraphML file."""
        G = nx.DiGraph([("A", "B"), ("B", "C")])
        temp_dir = tempfile.mkdtemp()
        try:
            temp_file = Path(temp_dir) / "test.graphml"
            nx.write_graphml(G, str(temp_file))
            renderer = ASCIIRenderer.from_graphml(str(temp_file))
            result = renderer.render()
            self.assertIn("A", result)
            self.assertIn("B", result)
            self.assertIn("C", result)
        finally:
            if temp_file.exists():
                temp_file.unlink()
            Path(temp_dir).rmdir()

    def test_invalid_graphml(self):
        """Test handling of invalid GraphML file."""
        with tempfile.NamedTemporaryFile(suffix=".graphml") as f:
            f.write(b"not valid graphml")
            f.flush()
            with self.assertRaises(ValueError):
                ASCIIRenderer.from_graphml(f.name)


class TestLayoutOptions(unittest.TestCase):
    def test_edge_chars_ascii_fallback(self):
        """Test that edge characters properly fall back to ASCII when needed."""
        options = LayoutOptions(use_ascii=False)
        self.assertEqual(options.edge_vertical, "│")
        self.assertEqual(options.edge_horizontal, "─")

        options.use_ascii = True
        self.assertEqual(options.edge_vertical, "|")
        self.assertEqual(options.edge_horizontal, "-")

    def test_edge_chars_custom(self):
        """Test that edge characters can be customized."""
        options = LayoutOptions()
        original = options.edge_vertical
        options.edge_vertical = "X"
        self.assertEqual(options.edge_vertical, "X")

        # Reset for other tests
        options.edge_vertical = original

    def test_invalid_spacing(self):
        """Test validation of spacing parameters."""
        with self.assertRaises(ValueError):
            LayoutOptions(node_spacing=0)

        with self.assertRaises(ValueError):
            LayoutOptions(layer_spacing=-1)

        options = LayoutOptions()
        self.assertGreater(options.node_spacing, 0)
        self.assertGreater(options.layer_spacing, 0)


if __name__ == "__main__":
    unittest.main()
