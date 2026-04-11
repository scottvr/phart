"""Test suite for PHART ASCII graph renderer."""

import unittest
import sys
import re
from collections import Counter
from typing import Any, Dict, List

import networkx as nx  # type: ignore

from phart import ASCIIRenderer
from phart.layout import LayoutOptions
from phart.rendering import nodes as nodes_mod
from phart.rendering import ports as ports_mod
from phart.styles import FlowDirection, NodeStyle
from phart.renderer import merge_layout_options
from phart.io.output.files import write_to_file
from pathlib import Path

import tempfile
from unittest.mock import patch


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
        renderer = ASCIIRenderer(
            self.chain,
            options=LayoutOptions(
                bboxes=True,
                use_ascii=False,
                layer_spacing=4,
            ),
        )
        result = renderer.render(print_config=True)
        lines = result.split("\n")

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

    def test_port_pool_expands_to_unused_face_slots_before_reusing_terminal(self):
        pool = ports_mod.expand_face_pool_before_reuse(
            [4, 5],
            [1, 2, 3, 4, 5],
            [4, 5],
            1,
        )
        self.assertEqual(pool, [1, 2, 3])

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

    def test_use_labels_synthesizes_node_text_from_attributes(self):
        graph = nx.DiGraph()
        graph.add_node("n1", name="Alpha", birt={"date": "Y"}, deat={"date": "Y"})

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
        self.assertNotIn("Y-Y", result)
        self.assertNotIn("n1", result)

    def test_node_label_lines_synthesizes_multiline_in_bboxes(self):
        graph = nx.DiGraph()
        graph.add_node("n1", name="Alpha", birt={"date": "Y"}, deat={"date": "Y"})

        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                bboxes=True,
                use_labels=True,
                bbox_multiline_labels=True,
                node_label_lines=("name", "birt.date"),
                use_ascii=True,
            ),
        )
        result = renderer.render()
        self.assertIn("Alpha", result)
        self.assertIn("Y", result)
        self.assertIn("+-------+", result)

    def test_node_label_lines_name_only_is_distinct_from_name_and_birth_date(self):
        graph = nx.DiGraph()
        graph.add_node("n1", name="Alpha", birt={"date": "Y"}, deat={"date": "Y"})

        name_only = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                bboxes=True,
                use_labels=True,
                bbox_multiline_labels=True,
                node_label_lines=("name",),
                use_ascii=True,
            ),
        ).render()
        name_birth_date = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                bboxes=True,
                use_labels=True,
                bbox_multiline_labels=True,
                node_label_lines=("name", "birt.date"),
                use_ascii=True,
            ),
        ).render()

        self.assertIn("Alpha", name_only)
        self.assertNotIn("Y", name_only)
        self.assertIn("Y", name_birth_date)

    def test_node_label_lines_wildcard_includes_remaining_attributes(self):
        graph = nx.DiGraph()
        graph.add_node(
            "n1",
            name="Alpha",
            birt={"date": "Y"},
            deat={"date": "Y"},
            sex="F",
            note="N",
        )

        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                bboxes=True,
                use_labels=True,
                bbox_multiline_labels=True,
                node_label_lines=("name", "*"),
                use_ascii=True,
            ),
        )
        result = renderer.render()
        self.assertIn("Alpha", result)
        self.assertIn("sex=F", result)
        self.assertIn("birt.date=Y", result)

    def test_multiline_bbox_layout_respects_node_spacing_without_overlap(self):
        graph = nx.DiGraph()
        graph.add_node("root", name="Root")
        graph.add_node("left", name="L", note="x")
        graph.add_node("right", name="Right Node", note="very long line")
        graph.add_edge("root", "left")
        graph.add_edge("root", "right")

        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                bboxes=True,
                use_labels=True,
                bbox_multiline_labels=True,
                node_label_lines=("name", "*"),
                node_spacing=1,
                layer_spacing=3,
                use_ascii=True,
            ),
        )
        positions, _width, _height = renderer.layout_manager.calculate_layout()
        left_bounds = renderer._get_node_bounds("left", positions)
        right_bounds = renderer._get_node_bounds("right", positions)
        if left_bounds["top"] == right_bounds["top"]:
            self.assertLess(left_bounds["right"], right_bounds["left"])

    def test_multiline_label_uses_single_line_when_bbox_multiline_disabled(self):
        graph = nx.DiGraph()
        graph.add_node("n1", label="Alpha\nBeta")

        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                bboxes=True,
                use_labels=True,
                bbox_multiline_labels=False,
                use_ascii=True,
            ),
        )
        result = renderer.render()
        self.assertIn("Alpha Beta", result)
        self.assertNotIn("Alpha\nBeta", result)

    def test_edge_label_renders_on_horizontal_edges(self):
        graph = nx.DiGraph()
        graph.add_edge("A", "B", label="E_H")

        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                use_ascii=True,
                flow_direction=FlowDirection.RIGHT,
                edge_label_attr="label",
            ),
        )
        result = renderer.render()
        self.assertIn("E_H", result)

    def test_edge_label_renders_on_vertical_edges(self):
        graph = nx.DiGraph()
        graph.add_edge("A", "B", label="E_V")

        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                use_ascii=True,
                flow_direction=FlowDirection.DOWN,
                edge_label_attr="label",
            ),
        )
        result = renderer.render()
        self.assertIn("E_V", result)

    def test_edge_labels_are_disabled_by_default(self):
        graph = nx.DiGraph()
        graph.add_edge("A", "B", label="E_H")

        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                use_ascii=True,
                flow_direction=FlowDirection.RIGHT,
            ),
        )
        result = renderer.render()
        self.assertNotIn("E_H", result)

    def test_cjk_label_box_width_respects_display_columns(self):
        graph = nx.DiGraph()
        graph.add_node("n1", label="中文")
        graph.add_node("n2", label="A")
        graph.add_edge("n1", "n2")

        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                bboxes=True,
                use_labels=True,
                use_ascii=True,
            ),
        )
        result = renderer.render()

        # "中文" is 4 display columns; with default hpad/borders this yields a 6-dash top.
        self.assertIn("+------+", result)

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

    def test_render_markdown_safe_uses_nbsp_in_auto_mode(self):
        graph = nx.DiGraph()
        graph.add_node("A B")
        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(node_style=NodeStyle.MINIMAL, use_ascii=True),
        )
        result = renderer.render(markdown_safe=True)
        self.assertIn("\u00a0", result)
        self.assertNotIn("A B", result)

    def test_render_markdown_safe_respects_explicit_whitespace_mode(self):
        graph = nx.DiGraph()
        graph.add_node("A B")
        ascii_renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                use_ascii=True,
                whitespace_mode="ascii_space",
            ),
        )
        nbsp_renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                use_ascii=True,
                whitespace_mode="nbsp",
            ),
        )

        ascii_result = ascii_renderer.render(markdown_safe=True)
        nbsp_result = nbsp_renderer.render(markdown_safe=False)

        self.assertIn("A B", ascii_result)
        self.assertNotIn("\u00a0", ascii_result)
        self.assertIn("\u00a0", nbsp_result)

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

    def test_from_dot_preserves_nested_subgraph_nodes_and_edges(self):
        dot_string = """
        digraph {
            subgraph cluster_home {
                label = "User Home/Office";
                Client;
                Router;
                Client -> Router;
            }
            subgraph cluster_internet {
                label = "The Internet Backbone";
                Backbone;
                DNS;
                Backbone -> DNS;
            }
            Router -> Backbone;
        }
        """
        renderer = ASCIIRenderer.from_dot(dot_string)
        self.assertIn("DNS", renderer.graph.nodes())
        self.assertIn(("Backbone", "DNS"), renderer.graph.edges())
        metadata = renderer.graph.graph.get("_phart_subgraphs")
        self.assertIsInstance(metadata, dict)
        assert isinstance(metadata, dict)
        self.assertTrue(metadata.get("subgraphs"))

    def test_from_dot_expands_subgraph_endpoint_edges_without_cluster_nodes(self):
        dot_string = """
        digraph {
            subgraph clusterA { a; b; }
            subgraph clusterB { c; d; }
            clusterA -> clusterB;
        }
        """
        renderer = ASCIIRenderer.from_dot(dot_string)
        nodes = set(renderer.graph.nodes())
        self.assertNotIn("clusterA", nodes)
        self.assertNotIn("clusterB", nodes)
        self.assertIn("a", nodes)
        self.assertIn("d", nodes)
        self.assertEqual(
            sorted(renderer.graph.edges()),
            [("a", "c"), ("b", "d")],
        )

    def test_render_shows_subgraph_titles_without_node_bboxes(self):
        dot_string = Path("examples/internet.dot").read_text(encoding="utf-8")
        renderer = ASCIIRenderer.from_dot(
            dot_string,
            options=LayoutOptions(
                use_ascii=True,
                bboxes=False,
                node_label_attr="label",
                edge_label_attr="label",
            ),
        )
        output = renderer.render()
        self.assertIn("User Home/Office", output)
        self.assertIn("The Internet Backbone", output)
        self.assertIn("DNS", output)

    def test_render_places_subgraph_title_inside_when_border_has_crossing(self):
        dot_string = Path("examples/internet.dot").read_text(encoding="utf-8")
        renderer = ASCIIRenderer.from_dot(
            dot_string,
            options=LayoutOptions(
                use_ascii=True,
                bboxes=True,
                node_spacing=5,
                layer_spacing=5,
                edge_anchor_mode="ports",
                shared_ports_mode="none",
                node_order_mode="preserve",
                bidirectional_mode="separate",
                node_label_attr="label",
                edge_label_attr="label",
            ),
        )
        output = renderer.render()
        self.assertRegex(output, r"\|.*User Home/Office.*\|")
        self.assertRegex(output, r"\|\s+\+[-]+\+\s+\|")

    def test_subgraph_preparation_preserves_layer_alignment_and_clearance(self):
        dot_string = Path("examples/internet.dot").read_text(encoding="utf-8")
        renderer = ASCIIRenderer.from_dot(
            dot_string,
            options=LayoutOptions(
                use_ascii=True,
                bboxes=False,
            ),
        )
        positions, width, height = renderer.layout_manager.calculate_layout()
        prepared_positions, _w2, _h2, _boxes = renderer._prepare_layout_for_subgraphs(
            dict(positions),
            width,
            height,
        )
        original_layers: Dict[int, List[Any]] = {}
        for node, (_x, y) in positions.items():
            original_layers.setdefault(y, []).append(node)

        for layer_nodes in original_layers.values():
            prepared_y_values = {prepared_positions[node][1] for node in layer_nodes}
            self.assertEqual(
                len(prepared_y_values),
                1,
                msg=f"layer nodes must remain aligned: {layer_nodes}",
            )

        boxes = renderer._build_subgraph_boxes(prepared_positions)

        def separated_with_gap(
            a_left: int,
            a_right: int,
            a_top: int,
            a_bottom: int,
            b_left: int,
            b_right: int,
            b_top: int,
            b_bottom: int,
            gap: int = 1,
        ) -> bool:
            return (
                a_right + gap < b_left
                or b_right + gap < a_left
                or a_bottom + gap < b_top
                or b_bottom + gap < a_top
            )

        for idx, upper in enumerate(boxes):
            for lower in boxes[idx + 1 :]:
                self.assertTrue(
                    separated_with_gap(
                        upper.left,
                        upper.right,
                        upper.top,
                        upper.bottom,
                        lower.left,
                        lower.right,
                        lower.top,
                        lower.bottom,
                    ),
                    msg=f"subgraph boxes overlap/touch: {upper.subgraph_id}, {lower.subgraph_id}",
                )

    def test_mermaid_output_emits_nested_subgraphs_when_metadata_present(self):
        dot_string = Path("examples/internet.dot").read_text(encoding="utf-8")
        renderer = ASCIIRenderer.from_dot(
            dot_string,
            options=LayoutOptions(
                use_ascii=True,
                node_label_attr="label",
                edge_label_attr="label",
            ),
        )
        mmd = renderer.mermaid_out()
        self.assertIn("flowchart TD", mmd)
        self.assertIn("subgraph", mmd)
        self.assertIn('["User Home/Office"]', mmd)
        self.assertIn('["The Internet Backbone"]', mmd)
        self.assertIn("DNS", mmd)

    def test_from_plantuml(self):
        """Test creation from PlantUML subset."""
        plantuml = """
        @startuml
        participant "Alice User" as Alice
        participant Bob
        Alice -> Bob : hello
        Bob --> Alice : world
        @enduml
        """
        renderer = ASCIIRenderer.from_plantuml(
            plantuml,
            options=LayoutOptions(use_ascii=True, use_labels=True),
        )
        result = renderer.render()

        self.assertIn("Alice User", result)
        self.assertIn("Bob", result)
        self.assertEqual(renderer.graph.number_of_nodes(), 2)
        self.assertGreaterEqual(renderer.graph.number_of_edges(), 2)

    def test_render_ditaa_wrap(self):
        graph = nx.DiGraph([("A", "B")])
        renderer = ASCIIRenderer(
            graph, options=LayoutOptions(use_ascii=False, bboxes=True)
        )
        ditaa = renderer.render_ditaa(wrap_plantuml=True)
        print(f"DEBUGDITAA:{ditaa}")
        self.assertIn("@startditaa", ditaa)
        self.assertIn("@endditaa", ditaa)
        self.assertNotIn("┌", ditaa)
        self.assertIn("+", ditaa)

    def test_render_svg_and_html(self):
        graph = nx.DiGraph([("A", "B")])
        renderer = ASCIIRenderer(
            graph, options=LayoutOptions(use_ascii=True, ansi_colors=False)
        )
        svg = renderer.render_svg()
        html = renderer.render_html()
        latex_md = renderer.render_latex_markdown()
        self.assertIn("<svg", svg)
        self.assertIn("<text", svg)
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("<pre", html)
        self.assertIn(r"\textcolor", latex_md)
        self.assertIn("$", latex_md)

    def test_ansi_to_hex_supports_named_and_bright_ansi_codes(self):
        self.assertEqual(ASCIIRenderer._ansi_to_hex("\x1b[31m"), "#800000")
        self.assertEqual(ASCIIRenderer._ansi_to_hex("\x1b[32m"), "#008000")
        self.assertEqual(ASCIIRenderer._ansi_to_hex("\x1b[91m"), "#ff0000")
        self.assertEqual(ASCIIRenderer._ansi_to_hex("\x1b[1;32m"), "#008000")
        self.assertEqual(ASCIIRenderer._ansi_to_hex("\x1b[38;5;214m"), "#ffaf00")

    def test_render_svg_path_mode_dispatches_to_glyph_renderer(self):
        graph = nx.DiGraph([("A", "B")])
        renderer = ASCIIRenderer(
            graph, options=LayoutOptions(use_ascii=True, ansi_colors=False)
        )
        with patch.object(ASCIIRenderer, "_append_svg_glyph_paths") as mock_paths:
            mock_paths.side_effect = lambda **kwargs: kwargs["lines"].append(
                '  <path d="M0 0L1 1" />'
            )
            svg = renderer.render_svg(text_mode="path")
        self.assertIn("<svg", svg)
        self.assertIn("<path", svg)
        mock_paths.assert_called_once()

    def test_render_svg_invalid_text_mode_raises(self):
        graph = nx.DiGraph([("A", "B")])
        renderer = ASCIIRenderer(
            graph, options=LayoutOptions(use_ascii=True, ansi_colors=False)
        )
        with self.assertRaises(ValueError):
            renderer.render_svg(text_mode="invalid-mode")

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
        result = ASCIIRenderer(
            self.chain,
            options=LayoutOptions(
                bboxes=True,
                use_ascii=False,
            ),
        ).render()
        print(f"RESULT: {result}")
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

    def test_upward_arrow_is_placed_at_destination_terminal(self):
        edge = nx.DiGraph([("A", "B")])
        result = ASCIIRenderer(
            edge,
            options=LayoutOptions(
                use_ascii=True,
                node_style=NodeStyle.MINIMAL,
                flow_direction=FlowDirection.UP,
                layer_spacing=4,
            ),
        ).render()
        lines = result.splitlines()
        top_idx = next(i for i, line in enumerate(lines) if "B" in line)
        self.assertIn("^", lines[top_idx + 1])

    def test_bidirectional_vertical_arrows_are_at_both_terminals(self):
        edge = nx.DiGraph([("A", "B"), ("B", "A")])
        result = ASCIIRenderer(
            edge,
            options=LayoutOptions(
                use_ascii=True,
                node_style=NodeStyle.MINIMAL,
                flow_direction=FlowDirection.UP,
                layer_spacing=4,
            ),
        ).render()
        lines = result.splitlines()
        top_idx = next(i for i, line in enumerate(lines) if "B" in line)
        bottom_idx = next(i for i, line in enumerate(lines) if "A" in line)
        self.assertIn("^", lines[top_idx + 1])
        self.assertIn("v", lines[bottom_idx - 1])

    def test_bidirectional_horizontal_arrows_point_toward_terminals(self):
        graph = nx.DiGraph([("A", "B"), ("B", "A")])
        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                bboxes=True,
                hpad=1,
                vpad=1,
                use_ascii=True,
            ),
        )

        positions = {"A": (0, 0), "B": (18, 0)}
        width = 32
        height = 8
        renderer._init_canvas(width, height, positions)  # noqa: SLF001
        renderer._edge_color_map = {}  # noqa: SLF001
        renderer._draw_edge("A", "B", positions)  # noqa: SLF001

        start_anchor, end_anchor = renderer._get_edge_anchor_points("A", "B", positions)  # noqa: SLF001
        y = start_anchor[1]
        min_x = min(start_anchor[0], end_anchor[0]) + 1
        max_x = max(start_anchor[0], end_anchor[0]) - 1

        self.assertEqual(
            renderer.canvas[y][min_x],  # noqa: SLF001
            renderer.options.get_arrow_for_direction("left"),
        )
        self.assertEqual(
            renderer.canvas[y][max_x],  # noqa: SLF001
            renderer.options.get_arrow_for_direction("right"),
        )

    def test_overlapping_paths_do_not_erase_terminal_arrow(self):
        graph = nx.DiGraph()
        graph.add_edge("package_a", "package_b")
        graph.add_edge("package_a", "requests")
        graph.add_edge("package_b", "package_c")
        graph.add_edge("package_c", "package_a")
        graph.add_edge("requests", "urllib3")
        graph.add_edge("requests", "certifi")

        result = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                use_ascii=True,
                node_style=NodeStyle.MINIMAL,
                layout_strategy="circular",
                edge_anchor_mode="center",
                layer_spacing=4,
            ),
        ).render()

        lines = result.splitlines()
        urllib3_idx = next(i for i, line in enumerate(lines) if "urllib3" in line)
        self.assertIn("^", lines[urllib3_idx + 1])

    def test_overlapping_colored_paths_preserve_terminal_arrow_cell(self):
        graph = nx.DiGraph()
        graph.add_edge("package_a", "package_b")
        graph.add_edge("package_a", "requests")
        graph.add_edge("package_b", "package_c")
        graph.add_edge("package_c", "package_a")
        graph.add_edge("requests", "urllib3")
        graph.add_edge("requests", "certifi")

        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                use_ascii=False,
                node_style=NodeStyle.MINIMAL,
                bboxes=True,
                hpad=1,
                vpad=0,
                layout_strategy="circular",
                edge_anchor_mode="center",
                ansi_colors=True,
                edge_color_mode="target",
                layer_spacing=4,
                node_spacing=6,
            ),
        )
        renderer.render()

        positions, _, _ = renderer.layout_manager.calculate_layout()
        start_anchor, end_anchor = renderer._get_edge_anchor_points(
            "requests", "urllib3", positions
        )
        start_x, start_y = start_anchor
        end_x, end_y = end_anchor

        if start_y == end_y:
            min_x = min(start_x, end_x) + 1
            max_x = max(start_x, end_x) - 1
            if start_x < end_x:
                expected_x = max_x
                expected_arrow = renderer.options.get_arrow_for_direction("right")
            else:
                expected_x = min_x
                expected_arrow = renderer.options.get_arrow_for_direction("left")
            expected_y = start_y
        else:
            top_anchor = start_anchor if start_y < end_y else end_anchor
            bottom_anchor = end_anchor if start_y < end_y else start_anchor
            if start_y < end_y:
                expected_x = bottom_anchor[0]
                expected_y = bottom_anchor[1] - 1
                expected_arrow = renderer.options.get_arrow_for_direction("down")
            else:
                expected_x = top_anchor[0]
                expected_y = top_anchor[1] + 1
                expected_arrow = renderer.options.get_arrow_for_direction("up")

        self.assertEqual(renderer.canvas[expected_y][expected_x], expected_arrow)  # noqa: SLF001
        self.assertIn((expected_x, expected_y), renderer._locked_arrow_cells)  # noqa: SLF001

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

    def test_uniform_box_labels_are_centered(self):
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

        a_line = next(line for line in lines if "A" in line and "WIDE_NODE" not in line)
        left_pipe = a_line.index("|")
        right_pipe = a_line.rindex("|")
        left_spaces = a_line[left_pipe + 1 : a_line.index("A")]
        right_spaces = a_line[a_line.index("A") + 1 : right_pipe]
        self.assertLessEqual(abs(len(left_spaces) - len(right_spaces)), 1)

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

    def test_edge_anchor_ports_separates_reciprocal_horizontal_edges(self):
        graph = nx.DiGraph([("A", "B"), ("B", "A")])
        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                bboxes=True,
                hpad=1,
                vpad=1,
                edge_anchor_mode="ports",
                use_ascii=True,
                layer_spacing=4,
            ),
        )
        positions = {"A": (0, 0), "B": (16, 0)}
        renderer._edge_anchor_map = renderer._compute_edge_anchor_map(positions)  # noqa: SLF001

        a_to_b_start, a_to_b_end = renderer._get_edge_anchor_points("A", "B", positions)  # noqa: SLF001
        b_to_a_start, b_to_a_end = renderer._get_edge_anchor_points("B", "A", positions)  # noqa: SLF001

        self.assertNotEqual(a_to_b_start[1], b_to_a_end[1])
        self.assertNotEqual(a_to_b_end[1], b_to_a_start[1])

    def test_shared_ports_none_reassigns_oversubscribed_target_face(self):
        graph = nx.DiGraph([("A", "T"), ("B", "T"), ("C", "T")])
        positions = {"A": (0, 0), "B": (0, 2), "C": (0, 4), "T": (16, 2)}

        baseline = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                bboxes=True,
                hpad=1,
                vpad=0,
                edge_anchor_mode="ports",
                use_ascii=True,
                layer_spacing=4,
            ),
        )
        baseline._edge_anchor_map = baseline._compute_edge_anchor_map(positions)  # noqa: SLF001
        baseline_ends = {
            baseline._edge_anchor_map[(source, "T")]["end"]  # noqa: SLF001
            for source in ("A", "B", "C")
        }
        self.assertEqual(len(baseline_ends), 1)

        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                bboxes=True,
                hpad=1,
                vpad=0,
                edge_anchor_mode="ports",
                shared_ports_mode="none",
                use_ascii=True,
                layer_spacing=4,
            ),
        )
        renderer._edge_anchor_map = renderer._compute_edge_anchor_map(positions)  # noqa: SLF001

        end_anchors = {
            renderer._edge_anchor_map[(source, "T")]["end"]  # noqa: SLF001
            for source in ("A", "B", "C")
        }
        self.assertGreater(len(end_anchors), 1)

        rerouted_sources = [
            source
            for source in ("A", "B", "C")
            if renderer._edge_anchor_map[(source, "T")]["end_side"] != "left"  # noqa: SLF001
        ]
        self.assertTrue(rerouted_sources)

        rerouted = rerouted_sources[0]
        _start_anchor, end_anchor = renderer._get_edge_anchor_points(
            rerouted, "T", positions
        )  # noqa: SLF001
        self.assertEqual(
            end_anchor,
            renderer._edge_anchor_map[(rerouted, "T")]["end"],  # noqa: SLF001
        )

    def test_shared_ports_none_reassigns_oversubscribed_source_face(self):
        graph = nx.Graph([("S", "A"), ("S", "B"), ("S", "C")])
        positions = {"S": (8, 0), "A": (0, 8), "B": (8, 8), "C": (16, 8)}

        baseline = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                bboxes=True,
                hpad=0,
                vpad=0,
                edge_anchor_mode="ports",
                use_ascii=True,
                layer_spacing=4,
            ),
        )
        baseline._edge_anchor_map = baseline._compute_edge_anchor_map(positions)  # noqa: SLF001
        baseline_starts = {
            baseline._edge_anchor_map[("S", target)]["start"]  # noqa: SLF001
            for target in ("A", "B", "C")
        }
        self.assertEqual(len(baseline_starts), 1)

        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                bboxes=True,
                hpad=0,
                vpad=0,
                edge_anchor_mode="ports",
                shared_ports_mode="none",
                use_ascii=True,
                layer_spacing=4,
            ),
        )
        renderer._edge_anchor_map = renderer._compute_edge_anchor_map(positions)  # noqa: SLF001

        start_anchors = {
            renderer._edge_anchor_map[("S", target)]["start"]  # noqa: SLF001
            for target in ("A", "B", "C")
        }
        self.assertGreater(len(start_anchors), 1)
        self.assertTrue(
            any(
                renderer._edge_anchor_map[("S", target)]["start_side"] != "bottom"  # noqa: SLF001
                for target in ("A", "B", "C")
            )
        )

    def test_shared_ports_none_counts_start_and_end_together_per_face(self):
        graph = nx.DiGraph(
            [
                ("A", "M"),
                ("B", "M"),
                ("C", "M"),
                ("M", "N"),
                ("M", "O"),
                ("M", "P"),
            ]
        )
        positions = {
            "A": (8, 0),
            "B": (13, 0),
            "C": (18, 0),
            "N": (23, 0),
            "O": (28, 0),
            "P": (33, 0),
            "M": (18, 8),
        }

        baseline = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                bboxes=True,
                hpad=2,
                vpad=0,
                edge_anchor_mode="ports",
                use_ascii=True,
            ),
        )
        baseline._edge_anchor_map = baseline._compute_edge_anchor_map(positions)  # noqa: SLF001
        baseline_top_terminals = 0
        for edge, data in baseline._edge_anchor_map.items():  # noqa: SLF001
            if edge[0] == "M" and data["start_side"] == "top":
                baseline_top_terminals += 1
            if edge[1] == "M" and data["end_side"] == "top":
                baseline_top_terminals += 1
        self.assertEqual(baseline_top_terminals, 6)

        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                bboxes=True,
                hpad=2,
                vpad=0,
                edge_anchor_mode="ports",
                shared_ports_mode="none",
                use_ascii=True,
            ),
        )
        renderer._edge_anchor_map = renderer._compute_edge_anchor_map(positions)  # noqa: SLF001
        top_terminals = 0
        non_top_terminals = 0
        for edge, data in renderer._edge_anchor_map.items():  # noqa: SLF001
            if edge[0] == "M":
                top_terminals += int(data["start_side"] == "top")
                non_top_terminals += int(data["start_side"] != "top")
            if edge[1] == "M":
                top_terminals += int(data["end_side"] == "top")
                non_top_terminals += int(data["end_side"] != "top")

        self.assertEqual(top_terminals, 5)
        self.assertGreater(non_top_terminals, 0)

    def test_shared_ports_minimize_avoids_reuse_on_same_face_without_rebalancing(self):
        graph = nx.DiGraph(
            [
                ("A", "M"),
                ("B", "M"),
                ("C", "M"),
                ("M", "N"),
                ("M", "O"),
                ("M", "P"),
            ]
        )
        positions = {
            "A": (8, 0),
            "B": (13, 0),
            "C": (18, 0),
            "N": (23, 0),
            "O": (28, 0),
            "P": (33, 0),
            "M": (18, 8),
        }

        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                bboxes=True,
                hpad=2,
                vpad=0,
                edge_anchor_mode="ports",
                shared_ports_mode="minimize",
                use_ascii=True,
            ),
        )
        renderer._edge_anchor_map = renderer._compute_edge_anchor_map(positions)  # noqa: SLF001

        top_terminals = 0
        side_terminals = 0
        terminal_points = set()
        for edge, data in renderer._edge_anchor_map.items():  # noqa: SLF001
            if edge[0] == "M":
                terminal_points.add(data["start"])
                top_terminals += int(data["start_side"] == "top")
                side_terminals += int(data["start_side"] != "top")
            if edge[1] == "M":
                terminal_points.add(data["end"])
                top_terminals += int(data["end_side"] == "top")
                side_terminals += int(data["end_side"] != "top")

        self.assertEqual(top_terminals, 6)
        self.assertEqual(side_terminals, 0)
        self.assertEqual(len(terminal_points), 5)

    def test_edge_anchor_center_prefers_horizontal_sides_for_near_aligned_boxes(self):
        graph = nx.DiGraph([("A", "B")])
        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                bboxes=True,
                hpad=1,
                vpad=1,
                edge_anchor_mode="center",
                use_ascii=True,
                layer_spacing=4,
            ),
        )
        positions = {"A": (0, 0), "B": (18, 1)}
        start_anchor, end_anchor = renderer._get_edge_anchor_points("A", "B", positions)  # noqa: SLF001
        a_bounds = renderer._get_node_bounds("A", positions)  # noqa: SLF001
        b_bounds = renderer._get_node_bounds("B", positions)  # noqa: SLF001

        self.assertEqual(start_anchor[0], a_bounds["right"])
        self.assertEqual(end_anchor[0], b_bounds["left"])
        self.assertEqual(start_anchor[1], end_anchor[1])
        self.assertGreater(start_anchor[1], a_bounds["top"])
        self.assertLess(start_anchor[1], a_bounds["bottom"])

    def test_edge_anchor_ports_aligns_rows_for_near_aligned_boxes(self):
        graph = nx.DiGraph([("A", "B")])
        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                bboxes=True,
                hpad=1,
                vpad=1,
                edge_anchor_mode="ports",
                use_ascii=True,
                layer_spacing=4,
            ),
        )
        positions = {"A": (0, 0), "B": (18, 1)}
        renderer._edge_anchor_map = renderer._compute_edge_anchor_map(positions)  # noqa: SLF001
        start_anchor, end_anchor = renderer._get_edge_anchor_points("A", "B", positions)  # noqa: SLF001

        self.assertEqual(start_anchor[1], end_anchor[1])

    def test_get_edge_route_length_returns_horizontal_distance(self):
        graph = nx.DiGraph([("A", "B")])
        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                bboxes=True,
                hpad=1,
                vpad=1,
                edge_anchor_mode="ports",
                use_ascii=True,
                layer_spacing=4,
            ),
        )
        positions = {"A": (0, 0), "B": (18, 1)}

        renderer.layout_manager.calculate_layout = lambda: (positions, 32, 8)

        start_anchor, end_anchor = renderer._get_edge_anchor_points("A", "B", positions)  # noqa: SLF001
        expected = abs(start_anchor[0] - end_anchor[0]) + abs(
            start_anchor[1] - end_anchor[1]
        )

        self.assertEqual(renderer.get_edge_route_length("A", "B"), expected)

    def test_get_edge_route_length_returns_vertical_jogged_distance(self):
        graph = nx.DiGraph([("A", "B")])
        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                bboxes=True,
                hpad=1,
                vpad=1,
                edge_anchor_mode="ports",
                use_ascii=True,
                layer_spacing=4,
            ),
        )
        positions = {"A": (0, 0), "B": (8, 10)}

        renderer.layout_manager.calculate_layout = lambda: (positions, 32, 18)
        renderer._edge_anchor_map = renderer._compute_edge_anchor_map(positions)  # noqa: SLF001
        start_anchor, end_anchor = renderer._get_edge_anchor_points("A", "B", positions)  # noqa: SLF001
        expected = abs(start_anchor[0] - end_anchor[0]) + abs(
            start_anchor[1] - end_anchor[1]
        )

        self.assertEqual(renderer.get_edge_route_length("A", "B"), expected)

    def test_edge_anchor_ports_prefers_straight_vertical_pair_when_available(self):
        graph = nx.DiGraph([("1", "2"), ("1", "Z1"), ("2", "4"), ("2", "F1")])
        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                bboxes=True,
                hpad=1,
                vpad=1,
                edge_anchor_mode="ports",
                use_ascii=True,
                layer_spacing=4,
            ),
        )
        positions = {
            "1": (8, 0),
            "2": (5, 7),
            "Z1": (17, 7),
            "4": (5, 14),
            "F1": (14, 14),
        }
        renderer._edge_anchor_map = renderer._compute_edge_anchor_map(positions)  # noqa: SLF001

        two_to_four_start, two_to_four_end = renderer._get_edge_anchor_points(
            "2", "4", positions
        )  # noqa: SLF001
        two_to_f1_start, _ = renderer._get_edge_anchor_points("2", "F1", positions)  # noqa: SLF001

        self.assertEqual(two_to_four_start[0], two_to_four_end[0])
        self.assertNotEqual(two_to_four_start, two_to_f1_start)

    def test_edge_anchor_ports_prefers_center_for_single_use_surface(self):
        graph = nx.DiGraph([("1", "2"), ("1", "Z1"), ("2", "4"), ("2", "F1")])
        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                bboxes=True,
                hpad=1,
                vpad=1,
                edge_anchor_mode="ports",
                use_ascii=True,
                layer_spacing=4,
            ),
        )
        positions = {
            "1": (8, 0),
            "2": (5, 7),
            "Z1": (17, 7),
            "4": (5, 14),
            "F1": (14, 14),
        }
        renderer._edge_anchor_map = renderer._compute_edge_anchor_map(positions)  # noqa: SLF001

        two_bounds = renderer._get_node_bounds("2", positions)  # noqa: SLF001
        z1_bounds = renderer._get_node_bounds("Z1", positions)  # noqa: SLF001
        four_bounds = renderer._get_node_bounds("4", positions)  # noqa: SLF001
        f1_bounds = renderer._get_node_bounds("F1", positions)  # noqa: SLF001

        end_1_2 = renderer._edge_anchor_map[("1", "2")]["end"]  # noqa: SLF001
        end_1_z1 = renderer._edge_anchor_map[("1", "Z1")]["end"]  # noqa: SLF001
        end_2_4 = renderer._edge_anchor_map[("2", "4")]["end"]  # noqa: SLF001
        end_2_f1 = renderer._edge_anchor_map[("2", "F1")]["end"]  # noqa: SLF001

        self.assertEqual(end_1_2[1], two_bounds["top"])
        self.assertEqual(end_1_z1[1], z1_bounds["top"])
        self.assertEqual(end_2_4[1], four_bounds["top"])
        self.assertEqual(end_2_f1[1], f1_bounds["top"])

        # Single-use destination faces should stay center-biased, but may shift
        # by one slot to preserve straighter routes when beneficial.
        self.assertLessEqual(abs(end_1_2[0] - two_bounds["center_x"]), 1)
        self.assertLessEqual(abs(end_1_z1[0] - z1_bounds["center_x"]), 1)
        self.assertLessEqual(abs(end_2_4[0] - four_bounds["center_x"]), 1)
        self.assertLessEqual(abs(end_2_f1[0] - f1_bounds["center_x"]), 1)

    def test_edge_anchor_ports_assigns_monotone_face_ports_for_ordered_targets(self):
        graph = nx.DiGraph([("P", "L"), ("P", "R")])
        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                bboxes=True,
                hpad=1,
                vpad=1,
                edge_anchor_mode="ports",
                use_ascii=True,
                layer_spacing=4,
            ),
        )
        # This geometry previously produced inverted source-port ordering.
        positions = {"P": (0, 0), "L": (1, 8), "R": (6, 8)}
        renderer._edge_anchor_map = renderer._compute_edge_anchor_map(positions)  # noqa: SLF001

        start_l = renderer._edge_anchor_map[("P", "L")]["start"][0]  # noqa: SLF001
        start_r = renderer._edge_anchor_map[("P", "R")]["start"][0]  # noqa: SLF001
        self.assertLessEqual(start_l, start_r)

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

    def test_ansi_colors_are_enabled_for_ascii_glyphs_when_allowed(self):
        renderer = ASCIIRenderer(
            self.chain,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                use_ascii=True,
                ansi_colors=True,
                allow_ansi_in_ascii=True,
            ),
        )
        result = renderer.render()
        self.assertIn("\x1b[", result)
        stripped = re.sub(r"\x1b\[[0-9;]*m", "", result)
        self.assertTrue(all(ord(c) < 128 for c in stripped))

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
                edge_color_mode="target",
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
                edge_color_mode="path",
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

    def test_edge_color_mode_source(self):
        graph = nx.DiGraph([("A", "B"), ("C", "D")])
        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                use_ascii=False,
                ansi_colors=True,
                edge_color_mode="source",
                bboxes=True,
                layer_spacing=4,
            ),
        )
        renderer.render()
        self.assertEqual(
            renderer._edge_color_map[("A", "B")],  # noqa: SLF001
            renderer._node_color_map["A"],  # noqa: SLF001
        )
        self.assertEqual(
            renderer._edge_color_map[("C", "D")],  # noqa: SLF001
            renderer._node_color_map["C"],  # noqa: SLF001
        )

    def test_edge_color_mode_source_without_node_coloring(self):
        graph = nx.DiGraph([("A", "B"), ("A", "C"), ("D", "E")])
        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                use_ascii=False,
                ansi_colors=True,
                edge_color_mode="source",
                color_nodes=False,
                bboxes=True,
                layer_spacing=4,
            ),
        )
        renderer.render()
        self.assertEqual(renderer._node_color_map, {})  # noqa: SLF001
        self.assertEqual(
            renderer._edge_color_map[("A", "B")],  # noqa: SLF001
            renderer._edge_color_map[("A", "C")],  # noqa: SLF001
        )
        self.assertNotEqual(
            renderer._edge_color_map[("A", "B")],  # noqa: SLF001
            renderer._edge_color_map[("D", "E")],  # noqa: SLF001
        )

    def test_edge_color_mode_path(self):
        graph = nx.DiGraph([("A", "B"), ("A", "C"), ("B", "D")])
        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                use_ascii=False,
                ansi_colors=True,
                edge_color_mode="path",
                bboxes=True,
                layer_spacing=4,
            ),
        )
        renderer.render()
        colors = set(renderer._edge_color_map.values())  # noqa: SLF001
        self.assertGreaterEqual(len(colors), 2)

    def test_edge_color_mode_attr_uses_edge_attributes(self):
        graph = nx.DiGraph()
        graph.add_edge("Alice", "Bob", relationship="friend")
        graph.add_edge("Bob", "Charlie", relationship="enemy")
        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                use_ascii=False,
                ansi_colors=True,
                edge_color_mode="attr",
                edge_color_rules={
                    "relationship": {"friend": "bright_green", "enemy": "red"}
                },
                bboxes=True,
                layer_spacing=4,
            ),
        )
        renderer.render()
        self.assertEqual(renderer._edge_color_map[("Alice", "Bob")], "\x1b[92m")  # noqa: SLF001
        self.assertEqual(renderer._edge_color_map[("Bob", "Charlie")], "\x1b[31m")  # noqa: SLF001

    def test_edge_color_mode_attr_falls_back_to_source_color(self):
        graph = nx.DiGraph()
        graph.add_edge("Alice", "Bob", relationship="ally")
        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                use_ascii=False,
                ansi_colors=True,
                edge_color_mode="attr",
                edge_color_rules={"relationship": {"enemy": "red"}},
                bboxes=True,
                layer_spacing=4,
            ),
        )
        renderer.render()
        self.assertEqual(
            renderer._edge_color_map[("Alice", "Bob")],  # noqa: SLF001
            renderer._node_color_map["Alice"],  # noqa: SLF001
        )

    def test_edge_color_mode_attr_fallback_works_without_node_coloring(self):
        graph = nx.DiGraph()
        graph.add_edge("Alice", "Bob", relationship="ally")
        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                use_ascii=False,
                ansi_colors=True,
                edge_color_mode="attr",
                edge_color_rules={"relationship": {"enemy": "red"}},
                color_nodes=False,
                bboxes=True,
                layer_spacing=4,
            ),
        )
        renderer.render()
        self.assertEqual(renderer._node_color_map, {})  # noqa: SLF001
        self.assertIn(("Alice", "Bob"), renderer._edge_color_map)  # noqa: SLF001
        self.assertIsNotNone(renderer._edge_color_map[("Alice", "Bob")])  # noqa: SLF001

    def test_edge_color_mode_attr_supports_style_rule_with_endpoint_attrs(self):
        graph = nx.DiGraph()
        graph.add_node("A", sex="M")
        graph.add_node("B", sex="F")
        graph.add_node("C", sex="M")
        graph.add_edge("A", "B", role="spouse")
        graph.add_edge("A", "C", role="spouse")
        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                use_ascii=False,
                ansi_colors=True,
                edge_color_mode="attr",
                style_rules=[
                    {
                        "target": "edge",
                        "when": 'role == "spouse" and v.sex == "F"',
                        "set": {"color": "green"},
                    },
                    {
                        "target": "edge",
                        "when": 'role == "spouse" and v.sex == "M"',
                        "set": {"color": "blue"},
                    },
                ],
                bboxes=True,
                layer_spacing=4,
            ),
        )
        renderer.render()
        self.assertEqual(renderer._edge_color_map[("A", "B")], "\x1b[32m")  # noqa: SLF001
        self.assertEqual(renderer._edge_color_map[("A", "C")], "\x1b[34m")  # noqa: SLF001

    def test_edge_style_rule_priority_orders_matches(self):
        graph = nx.DiGraph()
        graph.add_node("A", sex="M")
        graph.add_node("B", sex="F")
        graph.add_edge("A", "B", role="spouse")
        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                use_ascii=False,
                ansi_colors=True,
                edge_color_mode="attr",
                style_rules=[
                    {
                        "target": "edge",
                        "priority": 1,
                        "when": 'role == "spouse"',
                        "set": {"color": "red"},
                    },
                    {
                        "target": "edge",
                        "priority": 10,
                        "when": 'role == "spouse" and v.sex == "F"',
                        "set": {"color": "green"},
                    },
                ],
                bboxes=True,
                layer_spacing=4,
            ),
        )
        renderer.render()
        self.assertEqual(renderer._edge_color_map[("A", "B")], "\x1b[32m")  # noqa: SLF001

    def test_node_style_rule_prefix_suffix_applies_to_labels(self):
        graph = nx.DiGraph()
        graph.add_node("n1", name="Alice")
        options = LayoutOptions(
            use_labels=True,
            style_rules=[
                {
                    "target": "node",
                    "when": 'name == "Alice"',
                    "set": {"prefix": "{", "suffix": "}"},
                }
            ],
        )
        lines = nodes_mod.resolved_node_label_lines(options, graph.nodes["n1"], "n1")
        self.assertEqual(lines, ["{Alice}"])

    def test_node_style_rule_node_style_overrides_global_style(self):
        graph = nx.DiGraph()
        graph.add_node("n1", name="Alice", sex="F")
        graph.add_node("n2", name="Bob", sex="M")
        options = LayoutOptions(
            use_labels=True,
            node_style=NodeStyle.SQUARE,
            style_rules=[
                {
                    "target": "node",
                    "when": 'sex == "F"',
                    "set": {"node_style": "round"},
                }
            ],
        )
        f_lines = nodes_mod.resolved_node_label_lines(options, graph.nodes["n1"], "n1")
        m_lines = nodes_mod.resolved_node_label_lines(options, graph.nodes["n2"], "n2")
        self.assertEqual(f_lines, ["(Alice)"])
        self.assertEqual(m_lines, ["[Bob]"])

    def test_node_style_rule_can_override_node_color(self):
        graph = nx.DiGraph([("A", "B")])
        graph.nodes["A"]["sex"] = "F"
        graph.nodes["B"]["sex"] = "M"
        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                ansi_colors=True,
                edge_color_mode="source",
                style_rules=[
                    {
                        "target": "node",
                        "when": 'sex == "F"',
                        "set": {"color": "red"},
                    }
                ],
            ),
        )
        renderer.render()
        self.assertEqual(renderer._node_color_map["A"], "\x1b[31m")  # noqa: SLF001

    def test_node_style_rule_color_respects_no_color_nodes(self):
        graph = nx.DiGraph([("A", "B")])
        graph.nodes["A"]["sex"] = "F"
        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                ansi_colors=True,
                edge_color_mode="source",
                color_nodes=False,
                style_rules=[
                    {
                        "target": "node",
                        "when": 'sex == "F"',
                        "set": {"color": "red"},
                    }
                ],
            ),
        )
        renderer.render()
        self.assertEqual(renderer._node_color_map, {})  # noqa: SLF001

    def test_edge_style_rule_can_override_edge_line_and_arrow_glyphs(self):
        graph = nx.DiGraph()
        graph.add_edge("A", "B", role="link")
        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                use_ascii=True,
                bboxes=True,
                hpad=1,
                layer_spacing=5,
                flow_direction=FlowDirection.DOWN,
                style_rules=[
                    {
                        "target": "edge",
                        "when": 'role == "link"',
                        "set": {
                            "line_vertical": "!",
                            "arrow_down": "x",
                        },
                    }
                ],
            ),
        )
        output = renderer.render()
        self.assertIn("!", output)
        self.assertIn("x", output)

    def test_edge_glyph_preset_thick_applies_unicode_line_art(self):
        graph = nx.DiGraph([("A", "B")])
        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                use_ascii=False,
                bboxes=True,
                layer_spacing=5,
                edge_glyph_preset="thick",
            ),
        )
        output = renderer.render()
        self.assertIn("┃", output)

    def test_edge_arrow_style_unicode_applies_unicode_arrowheads(self):
        graph = nx.DiGraph([("A", "B")])
        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                use_ascii=False,
                bboxes=True,
                layer_spacing=5,
                edge_arrow_style="unicode",
            ),
        )
        output = renderer.render()
        self.assertIn("↓", output)

    def test_edge_style_rule_glyph_overrides_global_preset(self):
        graph = nx.DiGraph()
        graph.add_edge("A", "B", role="link")
        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                use_ascii=False,
                bboxes=True,
                layer_spacing=5,
                edge_glyph_preset="thick",
                style_rules=[
                    {
                        "target": "edge",
                        "when": 'role == "link"',
                        "set": {"line_vertical": "!"},
                    }
                ],
            ),
        )
        output = renderer.render()
        self.assertIn("!", output)

    def test_attr_mode_bidirectional_requires_rule_attribute_agreement(self):
        graph = nx.DiGraph()
        graph.add_edge("Alice", "Bob", relationship="friend")
        graph.add_edge("Bob", "Alice", relationship="friend")
        graph.add_edge("Bob", "Charlie", relationship="friend")
        graph.add_edge("Charlie", "Bob", relationship="enemy")

        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                use_ascii=False,
                ansi_colors=True,
                edge_color_mode="attr",
                edge_color_rules={
                    "relationship": {"friend": "bright_green", "enemy": "red"}
                },
                bboxes=True,
                edge_anchor_mode="ports",
                layer_spacing=4,
            ),
        )
        renderer.render()

        self.assertTrue(renderer._is_bidirectional_edge("Alice", "Bob"))  # noqa: SLF001
        self.assertTrue(renderer._is_bidirectional_edge("Bob", "Alice"))  # noqa: SLF001
        self.assertFalse(renderer._is_bidirectional_edge("Bob", "Charlie"))  # noqa: SLF001
        self.assertFalse(renderer._is_bidirectional_edge("Charlie", "Bob"))  # noqa: SLF001

    def test_edge_anchor_auto_switches_to_ports_for_attr_mismatch(self):
        graph = nx.DiGraph()
        graph.add_edge("Alice", "Bob", relationship="friend")
        graph.add_edge("Bob", "Alice", relationship="friend")
        graph.add_edge("Bob", "Charlie", relationship="friend")
        graph.add_edge("Charlie", "Bob", relationship="enemy")

        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                use_ascii=False,
                ansi_colors=True,
                edge_color_mode="attr",
                edge_color_rules={
                    "relationship": {"friend": "bright_green", "enemy": "red"}
                },
                bboxes=True,
                edge_anchor_mode="auto",
                layer_spacing=4,
            ),
        )
        renderer.render()

        self.assertFalse(renderer._should_use_ports_for_edge("Alice", "Bob"))  # noqa: SLF001
        self.assertTrue(renderer._should_use_ports_for_edge("Bob", "Charlie"))  # noqa: SLF001

    def test_bidirectional_mode_separate_disables_bidirectional_rendering(self):
        graph = nx.DiGraph([("A", "B"), ("B", "A")])
        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                use_ascii=True,
                bidirectional_mode="separate",
                bboxes=True,
                edge_anchor_mode="ports",
                layer_spacing=4,
            ),
        )
        renderer.render()

        self.assertFalse(renderer._is_bidirectional_edge("A", "B"))  # noqa: SLF001
        self.assertFalse(renderer._is_bidirectional_edge("B", "A"))  # noqa: SLF001

    def test_edge_anchor_auto_uses_ports_for_bidirectional_separate_mode(self):
        graph = nx.DiGraph([("A", "B"), ("B", "A")])
        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                use_ascii=True,
                bidirectional_mode="separate",
                bboxes=True,
                edge_anchor_mode="auto",
                layer_spacing=4,
            ),
        )
        renderer.render()

        self.assertTrue(renderer._should_use_ports_for_edge("A", "B"))  # noqa: SLF001
        self.assertTrue(renderer._should_use_ports_for_edge("B", "A"))  # noqa: SLF001

    def test_bidirectional_edge_dedupes_when_colors_match(self):
        class CountingRenderer(ASCIIRenderer):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.drawn_edges: list[tuple[str, str]] = []

            def _draw_edge(self, start, end, positions):
                self.drawn_edges.append((str(start), str(end)))
                return super()._draw_edge(start, end, positions)

        graph = nx.DiGraph()
        graph.add_edge("Alice", "Bob", relationship="friend")
        graph.add_edge("Bob", "Alice", relationship="friend")
        graph.add_edge("Bob", "Charlie", relationship="friend")
        graph.add_edge("Charlie", "Bob", relationship="enemy")

        renderer = CountingRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                use_ascii=False,
                ansi_colors=True,
                edge_color_mode="attr",
                edge_color_rules={
                    "relationship": {"friend": "bright_green", "enemy": "red"}
                },
                bboxes=True,
                edge_anchor_mode="auto",
                layer_spacing=4,
            ),
        )
        renderer.render()
        counts = Counter(frozenset(edge) for edge in renderer.drawn_edges)

        # Matching reciprocal attrs should share a single rendered route.
        self.assertEqual(counts[frozenset(("Alice", "Bob"))], 1)
        # Mismatched reciprocal attrs should remain separate draws.
        self.assertEqual(counts[frozenset(("Bob", "Charlie"))], 2)

    def test_bidirectional_edge_separate_mode_does_not_dedupe(self):
        class CountingRenderer(ASCIIRenderer):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.drawn_edges: list[tuple[str, str]] = []

            def _draw_edge(self, start, end, positions):
                self.drawn_edges.append((str(start), str(end)))
                return super()._draw_edge(start, end, positions)

        graph = nx.DiGraph()
        graph.add_edge("Alice", "Bob", relationship="friend")
        graph.add_edge("Bob", "Alice", relationship="friend")

        renderer = CountingRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                use_ascii=False,
                ansi_colors=True,
                edge_color_mode="attr",
                edge_color_rules={"relationship": {"friend": "bright_green"}},
                bidirectional_mode="separate",
                bboxes=True,
                edge_anchor_mode="auto",
                layer_spacing=4,
            ),
        )
        renderer.render()
        counts = Counter(frozenset(edge) for edge in renderer.drawn_edges)

        self.assertEqual(counts[frozenset(("Alice", "Bob"))], 2)

    def test_constrained_render_outputs_multi_panel_text_with_connectors(self):
        graph = nx.DiGraph()
        graph.add_edge("R", "A1")
        graph.add_edge("R", "A2")
        graph.add_edge("R", "A3")
        graph.add_edge("R", "A4")
        graph.add_edge("A1", "B1")
        graph.add_edge("A2", "B2")

        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                layout_strategy="layered",
                constrained=True,
                target_canvas_width=12,
                panel_header_mode="basic",
                use_ascii=True,
            ),
        )
        output = renderer.render()

        self.assertIn("=== Panel P1/2", output)
        self.assertIn("=== Panel P2/2", output)
        self.assertIn("Connectors:", output)
        self.assertIn("-> [P2] R->A3", output)
        self.assertIn("from [P1] -> B1 (A1->B1)", output)
        self.assertIn("Boundary Out:", output)
        self.assertIn("Boundary In:", output)

    def test_constrained_render_respects_connector_style_none(self):
        graph = nx.DiGraph()
        graph.add_edge("R", "A1")
        graph.add_edge("R", "A2")
        graph.add_edge("R", "A3")
        graph.add_edge("R", "A4")
        graph.add_edge("A1", "B1")

        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                layout_strategy="layered",
                constrained=True,
                target_canvas_width=12,
                cross_partition_edge_style="none",
                use_ascii=True,
            ),
        )
        output = renderer.render()

        self.assertNotIn("Connectors:", output)
        self.assertNotIn("-> [P", output)

    def test_constrained_render_lineage_headers_include_roots_and_rank_ranges(self):
        graph = nx.DiGraph()
        graph.add_edge("R", "A1")
        graph.add_edge("R", "A2")
        graph.add_edge("R", "A3")
        graph.add_edge("R", "A4")
        graph.add_edge("A1", "B1")
        graph.add_edge("A2", "B2")

        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                layout_strategy="layered",
                constrained=True,
                target_canvas_width=12,
                panel_header_mode="lineage",
                use_ascii=True,
            ),
        )
        output = renderer.render()

        self.assertIn("ranks=", output)
        self.assertIn("roots=", output)

    def test_constrained_render_supports_connector_and_panel_header_style_rules(self):
        graph = nx.DiGraph()
        graph.add_edge("R", "A1")
        graph.add_edge("R", "A2")
        graph.add_edge("R", "A3")
        graph.add_edge("R", "A4")
        graph.add_edge("A1", "B1")
        graph.add_edge("A2", "B2")

        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                layout_strategy="layered",
                constrained=True,
                target_canvas_width=12,
                panel_header_mode="basic",
                style_rules=[
                    {
                        "target": "panel_header",
                        "when": "partition_number == 1",
                        "set": {"prefix": "[HDR] "},
                    },
                    {
                        "target": "connector",
                        "when": 'kind == "incoming"',
                        "set": {"prefix": "[IN] "},
                    },
                ],
                use_ascii=True,
            ),
        )
        output = renderer.render()

        self.assertIn("[HDR]=== Panel P1/2", output)
        self.assertIn("[IN]  from [P1] -> B1 (A1->B1)", output)

    def test_constrained_render_supports_connector_style_rule_color(self):
        graph = nx.DiGraph()
        graph.add_edge("R", "A1")
        graph.add_edge("R", "A2")
        graph.add_edge("R", "A3")
        graph.add_edge("R", "A4")
        graph.add_edge("A1", "B1")

        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                layout_strategy="layered",
                constrained=True,
                target_canvas_width=12,
                ansi_colors=True,
                use_ascii=False,
                style_rules=[
                    {
                        "target": "connector",
                        "when": 'kind == "outgoing"',
                        "set": {"color": "red"},
                    }
                ],
            ),
        )
        output = renderer.render()

        self.assertIn("\x1b[31m", output)
        self.assertIn("\x1b[0m", output)

    def test_constrained_render_overlap_includes_context_layers(self):
        graph = nx.DiGraph()
        graph.add_edge("R", "A1")
        graph.add_edge("R", "A2")
        graph.add_edge("R", "A3")
        graph.add_edge("R", "A4")
        graph.add_edge("A1", "B1")
        graph.add_edge("A2", "B2")

        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                layout_strategy="layered",
                constrained=True,
                target_canvas_width=12,
                partition_overlap=1,
                use_ascii=True,
            ),
        )
        output = renderer.render()

        self.assertIn("=== Panel P1/2", output)
        self.assertIn("=== Panel P2/2", output)
        self.assertNotIn("Boundary In:", output)
        self.assertNotIn("Boundary Out:", output)
        self.assertIn("B1", output)
        self.assertIn("B2", output)
        self.assertIn("R", output)

    def test_constrained_render_connector_ref_mode_both_uses_labels_and_ids(self):
        graph = nx.DiGraph()
        graph.add_edge("R", "A1")
        graph.add_edge("R", "A2")
        graph.add_edge("R", "A3")
        graph.add_edge("R", "A4")
        graph.add_edge("A1", "B1")
        graph.add_edge("A2", "B2")
        labels = {
            "R": "Root",
            "A1": "Alice",
            "A2": "Aaron",
            "A3": "Asha",
            "A4": "Aria",
            "B1": "Ben",
            "B2": "Bianca",
        }
        for node, label in labels.items():
            graph.nodes[node]["label"] = label

        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                layout_strategy="layered",
                constrained=True,
                target_canvas_width=12,
                connector_ref_mode="both",
                use_ascii=True,
            ),
        )
        output = renderer.render()

        self.assertIn("Alice [A1]->Ben [B1]", output)
        self.assertIn("Root [R]->Asha [A3]", output)

    def test_constrained_render_connector_compaction_groups_by_partition(self):
        graph = nx.DiGraph()
        graph.add_edge("R", "A1")
        graph.add_edge("R", "A2")
        graph.add_edge("R", "A3")
        graph.add_edge("R", "A4")
        graph.add_edge("A1", "B1")
        graph.add_edge("A2", "B2")

        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                layout_strategy="layered",
                constrained=True,
                target_canvas_width=12,
                connector_compaction="partition",
                use_ascii=True,
            ),
        )
        output = renderer.render()

        self.assertIn("Boundary Out:", output)
        self.assertIn("4 edges", output)
        self.assertIn("R->A3", output)
        self.assertIn("R->A4", output)
        self.assertEqual(output.count("-> [P2]"), 2)

    def test_export_partition_metadata_returns_stable_dict(self):
        graph = nx.DiGraph()
        graph.add_edge("R", "A1")
        graph.add_edge("R", "A2")
        graph.add_edge("R", "A3")
        graph.add_edge("R", "A4")
        graph.add_edge("A1", "B1")
        graph.add_edge("A2", "B2")

        renderer = ASCIIRenderer(
            graph,
            options=LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                layout_strategy="layered",
                constrained=True,
                target_canvas_width=12,
                use_ascii=True,
            ),
        )
        metadata = renderer.export_partition_metadata()

        self.assertEqual(metadata["schema_version"], "1.0")
        self.assertTrue(metadata["constrained"])
        self.assertEqual(metadata["partition_count"], 2)
        self.assertEqual(metadata["partitions"][0]["partition_number"], 1)
        self.assertIn("R", metadata["node_to_partition"])
        self.assertTrue(
            any(
                edge["edge_id"] == "R->A3" for edge in metadata["cross_partition_edges"]
            )
        )

    def test_file_writing(self):
        """Test writing to file with proper encoding."""

        renderer = ASCIIRenderer(self.chain)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as f:
            name = f.name
        try:
            write_to_file(renderer, filename=name)
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
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
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

    def test_style_bbox_alias_enables_boxes_with_minimal_inner_style(self):
        options = LayoutOptions(node_style="bbox", use_ascii=True)
        self.assertTrue(options.bboxes)
        self.assertEqual(options.node_style, NodeStyle.MINIMAL)

    def test_invalid_box_padding(self):
        with self.assertRaises(ValueError):
            LayoutOptions(hpad=-1)
        with self.assertRaises(ValueError):
            LayoutOptions(vpad=-1)

    def test_invalid_edge_anchor_mode(self):
        with self.assertRaises(ValueError):
            LayoutOptions(edge_anchor_mode="invalid")

    def test_edge_anchor_mode_auto_is_valid_and_default(self):
        options = LayoutOptions()
        self.assertEqual(options.edge_anchor_mode, "auto")
        explicit = LayoutOptions(edge_anchor_mode="auto")
        self.assertEqual(explicit.edge_anchor_mode, "auto")

    def test_invalid_layout_strategy(self):
        with self.assertRaises(ValueError):
            LayoutOptions(layout_strategy="invalid")

    def test_layout_strategy_normalizes_hyphenated_kamada_kawai(self):
        options = LayoutOptions(layout_strategy="kamada-kawai")
        self.assertEqual(options.layout_strategy, "kamada_kawai")

    def test_layout_strategy_accepts_spring(self):
        options = LayoutOptions(layout_strategy="spring")
        self.assertEqual(options.layout_strategy, "spring")

    def test_constrained_layout_accepts_target_width(self):
        options = LayoutOptions(
            layout_strategy="layered",
            constrained=True,
            target_canvas_width=80,
        )
        self.assertEqual(options.layout_strategy, "layered")
        self.assertTrue(options.constrained)
        self.assertEqual(options.target_canvas_width, 80)

    def test_constrained_layout_requires_target_canvas_width(self):
        with self.assertRaises(ValueError):
            LayoutOptions(layout_strategy="layered", constrained=True)

    def test_layout_strategy_accepts_arf_spiral_shell(self):
        for strategy in ("arf", "spiral", "shell"):
            with self.subTest(strategy=strategy):
                options = LayoutOptions(layout_strategy=strategy)
                self.assertEqual(options.layout_strategy, strategy)

    def test_partition_overlap_must_be_non_negative(self):
        with self.assertRaises(ValueError):
            LayoutOptions(partition_overlap=-1)

    def test_partition_affinity_strength_must_be_non_negative(self):
        with self.assertRaises(ValueError):
            LayoutOptions(partition_affinity_strength=-1)

    def test_connector_compaction_defaults_to_none(self):
        options = LayoutOptions()
        self.assertEqual(options.connector_compaction, "none")

    def test_invalid_connector_compaction_raises(self):
        with self.assertRaises(ValueError):
            LayoutOptions(connector_compaction="invalid")

    def test_panel_header_mode_defaults_to_basic(self):
        options = LayoutOptions()
        self.assertEqual(options.panel_header_mode, "basic")

    def test_invalid_panel_header_mode_raises(self):
        with self.assertRaises(ValueError):
            LayoutOptions(panel_header_mode="invalid")

    def test_connector_ref_mode_defaults_to_auto(self):
        options = LayoutOptions()
        self.assertEqual(options.connector_ref_mode, "auto")

    def test_invalid_connector_ref_mode_raises(self):
        with self.assertRaises(ValueError):
            LayoutOptions(connector_ref_mode="invalid")

    def test_invalid_edge_color_mode(self):
        with self.assertRaises(ValueError):
            LayoutOptions(edge_color_mode="invalid")

    def test_edge_color_mode_attr_is_valid(self):
        options = LayoutOptions(edge_color_mode="attr")
        self.assertEqual(options.edge_color_mode, "attr")

    def test_edge_color_rules_are_normalized(self):
        options = LayoutOptions(
            edge_color_rules={"RELATIONSHIP": {'"Friend"': "bright_green"}}
        )
        self.assertIn("relationship", options.edge_color_rules)
        self.assertEqual(
            options.edge_color_rules["relationship"]["friend"], "bright_green"
        )

    def test_style_rules_are_compiled(self):
        options = LayoutOptions(
            style_rules=[
                {
                    "target": "edge",
                    "when": 'role == "spouse"',
                    "set": {"color": "blue"},
                }
            ]
        )
        self.assertEqual(len(options._compiled_style_rules), 1)  # noqa: SLF001

    def test_style_rules_accept_connector_and_panel_header_targets(self):
        options = LayoutOptions(
            style_rules=[
                {
                    "target": "connector",
                    "when": 'kind == "incoming"',
                    "set": {"prefix": "[IN] ", "suffix": " !"},
                },
                {
                    "target": "panel_header",
                    "when": "partition_number == 1",
                    "set": {"color": "red"},
                },
            ]
        )
        self.assertEqual(len(options._compiled_style_rules), 2)  # noqa: SLF001

    def test_style_rule_invalid_target_raises(self):
        with self.assertRaises(ValueError):
            LayoutOptions(
                style_rules=[
                    {"target": "bogus", "when": "true", "set": {"color": "blue"}}
                ]
            )

    def test_style_rule_invalid_connector_set_key_raises(self):
        with self.assertRaises(ValueError):
            LayoutOptions(
                style_rules=[
                    {
                        "target": "connector",
                        "when": "true",
                        "set": {"line_vertical": "!"},
                    }
                ]
            )

    def test_style_rule_invalid_set_key_raises(self):
        with self.assertRaises(ValueError):
            LayoutOptions(
                style_rules=[
                    {
                        "target": "edge",
                        "when": "true",
                        "set": {"prefix": "<"},
                    }
                ]
            )

    def test_style_rule_invalid_node_style_value_raises(self):
        with self.assertRaises(ValueError):
            LayoutOptions(
                style_rules=[
                    {
                        "target": "node",
                        "when": "true",
                        "set": {"node_style": "hexagon"},
                    }
                ]
            )

    def test_style_rule_invalid_edge_glyph_value_raises(self):
        with self.assertRaises(ValueError):
            LayoutOptions(
                style_rules=[
                    {
                        "target": "edge",
                        "when": "true",
                        "set": {"line_horizontal": "=="},
                    }
                ]
            )

    def test_style_rule_wide_edge_glyph_value_raises(self):
        with self.assertRaises(ValueError):
            LayoutOptions(
                style_rules=[
                    {
                        "target": "edge",
                        "when": "true",
                        "set": {"line_horizontal": "好"},
                    }
                ]
            )

    def test_edge_arrow_style_unicode_coerces_to_ascii_in_ascii_mode(self):
        options = LayoutOptions(use_ascii=True, edge_arrow_style="unicode")
        self.assertEqual(options.edge_arrow_style, "ascii")

    def test_invalid_edge_glyph_preset_raises(self):
        with self.assertRaises(ValueError):
            LayoutOptions(edge_glyph_preset="unknown")

    def test_invalid_edge_arrow_style_raises(self):
        with self.assertRaises(ValueError):
            LayoutOptions(edge_arrow_style="unknown")

    def test_default_edge_color_mode_is_source(self):
        options = LayoutOptions()
        self.assertEqual(options.edge_color_mode, "source")

    def test_merge_layout_options_cli_overrides_binary_tree_layout(self):
        script_options = LayoutOptions(binary_tree_layout=False, use_ascii=True)
        cli_options = LayoutOptions(binary_tree_layout=True, use_ascii=True)
        merged = merge_layout_options(script_options, cli_options)
        self.assertTrue(merged.binary_tree_layout)

    def test_merge_layout_options_respects_explicit_cli_fields(self):
        script_options = LayoutOptions(binary_tree_layout=True, use_ascii=True)
        cli_options = LayoutOptions(binary_tree_layout=False, use_ascii=True)
        setattr(cli_options, "_explicit_cli_fields", {"use_ascii"})  # noqa: B010
        merged = merge_layout_options(script_options, cli_options)
        self.assertTrue(merged.binary_tree_layout)

    def test_merge_layout_options_respects_explicit_color_nodes_field(self):
        script_options = LayoutOptions(color_nodes=True, use_ascii=True)
        cli_options = LayoutOptions(color_nodes=False, use_ascii=True)
        setattr(cli_options, "_explicit_cli_fields", {"color_nodes"})  # noqa: B010
        merged = merge_layout_options(script_options, cli_options)
        self.assertFalse(merged.color_nodes)

    def test_merge_layout_options_bboxes_cli_uses_minimal_when_script_style_implicit(
        self,
    ):
        script_options = LayoutOptions(use_ascii=True)
        cli_options = LayoutOptions(bboxes=True, use_ascii=True)
        setattr(cli_options, "_explicit_cli_fields", {"bboxes"})  # nnoqa: B010
        merged = merge_layout_options(script_options, cli_options)
        self.assertTrue(merged.bboxes)
        self.assertEqual(merged.node_style, NodeStyle.MINIMAL)

    def test_merge_layout_options_bboxes_cli_preserves_explicit_script_style(self):
        script_options = LayoutOptions(node_style=NodeStyle.ROUND, use_ascii=True)
        cli_options = LayoutOptions(bboxes=True, use_ascii=True)
        setattr(cli_options, "_explicit_cli_fields", {"bboxes"})  # nnoqa: B010
        merged = merge_layout_options(script_options, cli_options)
        self.assertTrue(merged.bboxes)
        self.assertEqual(merged.node_style, NodeStyle.ROUND)


if __name__ == "__main__":
    unittest.main()
