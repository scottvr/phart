"""Test suite for PHART ASCII graph renderer."""

import unittest

import networkx as nx  # type: ignore

from phart import ASCIIRenderer, LayoutOptions, NodeStyle

from pathlib import Path


class TestASCIIRenderer(unittest.TestCase):
    """Test cases for basic rendering functionality and encoding."""

    def setUp(self):
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
        renderer = ASCIIRenderer(self.disconnected)
        result = renderer.render()
        lines = result.split("\n")

        # Find lines containing nodes
        a_line = next(i for i, line in enumerate(lines) if "A" in line)
        c_line = next(i for i, line in enumerate(lines) if "C" in line)

        # Components should be separated
        self.assertNotEqual(a_line, c_line)

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
        self.assertEqual(result.strip(), "A")

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
        import tempfile

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


class TestLayoutOptions(unittest.TestCase):
    """Test cases for layout configuration."""

    def test_invalid_spacing(self):
        """Test validation of spacing parameters."""
        with self.assertRaises(ValueError):
            LayoutOptions(node_spacing=0)
        with self.assertRaises(ValueError):
            LayoutOptions(layer_spacing=-1)

    def test_invalid_edge_chars(self):
        """Test validation of edge characters."""
        with self.assertRaises(ValueError):
            LayoutOptions(edge_vertical="||")
        with self.assertRaises(TypeError):
            LayoutOptions(edge_horizontal=1)

    def test_custom_characters(self):
        """Test custom edge character configuration."""
        options = LayoutOptions(
            self.edge_vertical("|"),
            self.edge_horizontal("-"),
            self.edge_cross("+"),
            self.edge_arrow(">"),
        )
        renderer = ASCIIRenderer(
            nx.DiGraph([("A", "B")]),
            options=options,
            node_style=NodeStyle.MINIMAL,
        )
        result = renderer.render()

        self.assertIn("|", result)
        self.assertNotIn("│", result)


if __name__ == "__main__":
    unittest.main()
