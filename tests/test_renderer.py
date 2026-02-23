"""Test suite for PHART ASCII graph renderer."""
# src path: tests\test_renderer.py

import unittest
import sys
import re

import networkx as nx  # type: ignore

from phart import ASCIIRenderer, LayoutOptions, NodeStyle
from phart.styles import FlowDirection
from phart.renderer import merge_layout_options

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
        renderer = ASCIIRenderer(self.chain, layer_spacing=3)
        result = renderer.render(print_config=True)
        lines = result.split("\n")

        for line in lines:
            print(f"DBG: xxx: line={line}")
        # Verify nodes appear in correct order
        self.assertTrue(any("A" in line and "B" not in line for line in lines))
        self.assertTrue(
            any("B" in line and "A" not in line and "C" not in line for line in lines)
        )
        self.assertTrue(any("C" in line and "B" not in line for line in lines))

        # Verify edge characters
        print("checking for pipes")
        for line in lines:
            print(f"{line}\n")
        self.assertTrue(any("|" in line or "│" in line for line in lines))

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
            if style.name not in "CUSTOM":
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

    def test_use_labels_prefers_node_labels(self):
        graph = nx.DiGraph()
        graph.add_node("n1", label="Alpha")
        graph.add_node("n2")
        graph.add_edge("n1", "n2")

        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                use_labels=True,
                use_ascii=True,
            ),
        )
        result = renderer.render()
        self.assertIn("Alpha", result)
        self.assertIn("n2", result)
        self.assertNotIn("n1", result)

    def test_use_labels_normalizes_quoted_and_multiline_labels(self):
        graph = nx.DiGraph()
        graph.add_node("n1", label='"Alpha\nBeta"')

        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                use_labels=True,
                use_ascii=True,
            ),
        )
        result = renderer.render()
        self.assertIn("Alpha Beta", result)

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

    def test_flow_direction_changes_layout_not_arrow_mapping(self):
        """Arrows should follow rendered geometry, not be rotated a second time by flow."""
        edge = nx.DiGraph([("A", "B")])

        down = ASCIIRenderer(
            edge,
            options=LayoutOptions(
                use_ascii=True,
                flow_direction=FlowDirection.DOWN,
                layer_spacing=3,
            ),
        ).render()
        up = ASCIIRenderer(
            edge,
            options=LayoutOptions(
                use_ascii=True,
                flow_direction=FlowDirection.UP,
                layer_spacing=3,
            ),
        ).render()

        self.assertIn("v", down)
        self.assertIn("^", up)

    def test_boxed_node_rendering_with_padding(self):
        """Box mode should draw a rectangle with configured padding."""
        single = nx.DiGraph()
        single.add_node("A")
        renderer = ASCIIRenderer(
            single,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                bboxes=True,
                hpad=2,
                vpad=1,
                use_ascii=True,
            ),
        )
        result = renderer.render()
        expected = "\n".join(
            [
                "+-----+",
                "|     |",
                "|  A  |",
                "|     |",
                "+-----+",
            ]
        )
        self.assertEqual(result.strip(), expected)

    def test_boxed_default_style_is_minimal(self):
        """When style is unspecified, boxed nodes should not include decorators."""
        single = nx.DiGraph()
        single.add_node("A")
        renderer = ASCIIRenderer(
            single,
            options=LayoutOptions(
                bboxes=True,
                hpad=1,
                vpad=0,
                use_ascii=True,
            ),
        )
        result = renderer.render()
        self.assertIn("| A |", result)
        self.assertNotIn("[A]", result)

    def test_boxed_explicit_style_is_preserved(self):
        """Explicitly requested node styles should still render inside boxes."""
        single = nx.DiGraph()
        single.add_node("A")
        renderer = ASCIIRenderer(
            single,
            options=LayoutOptions(
                node_style=NodeStyle.ROUND,
                bboxes=True,
                hpad=1,
                vpad=0,
                use_ascii=True,
            ),
        )
        result = renderer.render()
        self.assertIn("| (A) |", result)

    def test_uniform_box_widths(self):
        """Uniform box mode should size all boxes to the widest node text."""
        graph = nx.DiGraph([("A", "WIDE_NODE")])
        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                bboxes=True,
                hpad=1,
                vpad=0,
                uniform=True,
                use_ascii=True,
                layer_spacing=4,
            ),
        )
        result = renderer.render()
        lines = result.splitlines()

        a_line = next(line for line in lines if "A" in line)
        wide_line = next(line for line in lines if "WIDE_NODE" in line)
        a_width = a_line.rindex("|") - a_line.index("|") + 1
        wide_width = wide_line.rindex("|") - wide_line.index("|") + 1
        self.assertEqual(a_width, wide_width)

    def test_edge_anchor_ports_distribute_parent_connections(self):
        """Ports mode should spread parent-child edge starts along the box side."""
        graph = nx.DiGraph([("Root", "Left"), ("Root", "Mid"), ("Root", "Right")])
        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                bboxes=True,
                hpad=2,
                vpad=0,
                edge_anchor_mode="ports",
                use_ascii=True,
                layer_spacing=4,
            ),
        )
        positions, _, _ = renderer.layout_manager.calculate_layout()
        anchor_map = renderer._compute_edge_anchor_map(positions)
        starts = [
            anchor_map[("Root", child)]["start"] for child in ("Left", "Mid", "Right")
        ]

        self.assertGreater(len({x for x, _ in starts}), 1)

    def test_edge_anchor_center_uses_single_parent_connection(self):
        """Center mode keeps all parent-child starts on one shared anchor."""
        graph = nx.DiGraph([("Root", "Left"), ("Root", "Mid"), ("Root", "Right")])
        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                bboxes=True,
                hpad=2,
                vpad=0,
                edge_anchor_mode="center",
                use_ascii=True,
                layer_spacing=4,
            ),
        )
        positions, _, _ = renderer.layout_manager.calculate_layout()
        starts = [
            renderer._get_edge_anchor_points("Root", child, positions)[0]
            for child in ("Left", "Mid", "Right")
        ]

        self.assertEqual(len(set(starts)), 1)

    def test_unicode_boxed_edges_use_line_junction_glyphs(self):
        graph = nx.DiGraph([("Root", "Left"), ("Root", "Right")])
        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                bboxes=True,
                hpad=2,
                vpad=0,
                use_ascii=False,
                layer_spacing=4,
            ),
        )
        result = renderer.render()
        self.assertTrue(any(ch in result for ch in "┌┐└┘┬┴├┤┼"))

    def test_ascii_boxed_edges_do_not_emit_unicode_junctions(self):
        graph = nx.DiGraph([("Root", "Left"), ("Root", "Right")])
        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                bboxes=True,
                hpad=2,
                vpad=0,
                use_ascii=True,
                layer_spacing=4,
            ),
        )
        result = renderer.render()
        self.assertTrue(all(ord(c) < 128 for c in result))

    def test_ansi_colors_emit_escape_sequences(self):
        renderer = ASCIIRenderer(
            self.chain,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                use_ascii=False,
                ansi_colors=True,
            ),
        )
        result = renderer.render()
        self.assertIn("\x1b[", result)
        self.assertIn("\x1b[0m", result)

    def test_ansi_colors_are_disabled_in_ascii_mode(self):
        renderer = ASCIIRenderer(
            self.chain,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                use_ascii=True,
                ansi_colors=True,
            ),
        )
        result = renderer.render()
        self.assertNotIn("\x1b[", result)

    def test_stripping_ansi_matches_plain_render_output(self):
        base_options = dict(
            node_style=NodeStyle.MINIMAL,
            use_ascii=False,
            bboxes=True,
            hpad=1,
            vpad=0,
            layer_spacing=4,
        )
        plain = ASCIIRenderer(
            self.tree,
            options=LayoutOptions(**base_options),
        ).render()
        colored = ASCIIRenderer(
            self.tree,
            options=LayoutOptions(ansi_colors=True, **base_options),
        ).render()
        stripped = re.sub(r"\x1b\[[0-9;]*m", "", colored)
        self.assertEqual(stripped, plain)

    def test_edge_colors_follow_target_node_colors(self):
        graph = nx.DiGraph([("A", "B"), ("A", "C")])
        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                use_ascii=False,
                ansi_colors=True,
                bboxes=True,
                layer_spacing=4,
            ),
        )
        renderer.render()
        self.assertEqual(
            renderer._edge_color_map[("A", "B")],  # noqa: SLF001
            renderer._node_color_map["B"],  # noqa: SLF001
        )
        self.assertEqual(
            renderer._edge_color_map[("A", "C")],  # noqa: SLF001
            renderer._node_color_map["C"],  # noqa: SLF001
        )

    def test_shared_edge_segments_become_uncolored_on_conflict(self):
        graph = nx.DiGraph([("A", "B"), ("A", "C"), ("A", "D")])
        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                use_ascii=False,
                ansi_colors=True,
                bboxes=True,
                hpad=1,
                vpad=0,
                layer_spacing=4,
            ),
        )
        renderer.render()
        self.assertGreater(len(renderer._edge_conflict_cells), 0)  # noqa: SLF001
        for x, y in renderer._edge_conflict_cells:  # noqa: SLF001
            self.assertIsNone(renderer._color_canvas[y][x])  # noqa: SLF001

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
        self.assertEqual(options.node_style, NodeStyle.SQUARE)

    def test_default_style_is_minimal_when_boxed(self):
        options = LayoutOptions(bboxes=True)
        self.assertEqual(options.node_style, NodeStyle.MINIMAL)

    def test_invalid_box_padding(self):
        with self.assertRaises(ValueError):
            LayoutOptions(hpad=-1)
        with self.assertRaises(ValueError):
            LayoutOptions(vpad=-1)

    def test_invalid_edge_anchor_mode(self):
        with self.assertRaises(ValueError):
            LayoutOptions(edge_anchor_mode="invalid")

    def test_merge_layout_options_cli_overrides_binary_tree_layout(self):
        script_options = LayoutOptions(binary_tree_layout=False, use_ascii=True)
        cli_options = LayoutOptions(binary_tree_layout=True, use_ascii=True)
        merged = merge_layout_options(script_options, cli_options)
        self.assertTrue(merged.binary_tree_layout)


if __name__ == "__main__":
    unittest.main()
