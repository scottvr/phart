"""Targeted tests for layout-specific branches."""

import unittest

import networkx as nx  # type: ignore

from phart.layout import LayoutManager
from phart.styles import LayoutOptions, NodeStyle


class TestLayoutManager(unittest.TestCase):
    def test_binary_tree_sorter_is_used_with_side_attributes(self):
        """When binary_tree_layout is enabled, side attributes beat alpha order."""
        graph = nx.DiGraph()
        # Alphabetically A < Z, but side attributes should place Z on the left.
        graph.add_edge("ROOT", "Z", side="left")
        graph.add_edge("ROOT", "A", side="right")

        options = LayoutOptions(
            binary_tree_layout=True,
            node_style=NodeStyle.MINIMAL,
            use_ascii=True,
        )
        manager = LayoutManager(graph, options)
        positions, _, _ = manager.calculate_layout()

        self.assertLess(positions["Z"][0], positions["A"][0])

    def test_dense_triad_uses_vertical_layout_path(self):
        """Dense 3-node digraphs should trigger vertical layout scoring path."""
        graph = nx.DiGraph(
            [
                ("A", "B"),
                ("B", "A"),
                ("A", "C"),
                ("C", "A"),
            ]
        )
        options = LayoutOptions(
            node_style=NodeStyle.MINIMAL,
            layer_spacing=4,
            use_ascii=True,
        )
        manager = LayoutManager(graph, options)
        positions, _, _ = manager.calculate_layout()

        # A is highest-importance and should be on top.
        self.assertEqual(positions["A"][1], 0)
        layer_step = max(1, options.layer_spacing) + options.get_node_height() - 1
        self.assertEqual(positions["B"][1], layer_step)
        self.assertEqual(positions["C"][1], layer_step)

    def test_calculate_canvas_dimensions_is_still_functional(self):
        """calculate_canvas_dimensions is currently unused by renderer, but valid."""
        graph = nx.DiGraph([("A", "B")])
        options = LayoutOptions(
            node_style=NodeStyle.MINIMAL,
            right_padding=2,
            use_ascii=True,
        )
        manager = LayoutManager(graph, options)
        positions, _, _ = manager.calculate_layout()

        width, height = manager.calculate_canvas_dimensions(positions)
        expected_width = (
            max(
                x + manager._get_node_width(str(node))  # noqa: SLF001
                for node, (x, _) in positions.items()
            )
            + options.right_padding
            + 6
        )
        expected_height = (
            max(y + options.get_node_height() for _, y in positions.values()) + 1
        )

        self.assertEqual(width, max(1, expected_width))
        self.assertEqual(height, max(1, expected_height))
        self.assertEqual(manager.calculate_canvas_dimensions({}), (0, 0))

    def test_layout_width_uses_labels_when_enabled(self):
        graph = nx.DiGraph()
        graph.add_node("n1", label="A much longer label")
        graph.add_node("n2")
        graph.add_edge("n1", "n2")

        without_labels = LayoutManager(
            graph,
            LayoutOptions(
                node_style=NodeStyle.MINIMAL, use_labels=False, use_ascii=True
            ),
        )
        with_labels = LayoutManager(
            graph,
            LayoutOptions(
                node_style=NodeStyle.MINIMAL, use_labels=True, use_ascii=True
            ),
        )

        self.assertGreater(
            with_labels._get_node_width("n1"),  # noqa: SLF001
            without_labels._get_node_width("n1"),  # noqa: SLF001
        )

    def test_bfs_layout_strategy_layers_by_distance(self):
        graph = nx.DiGraph([("A", "B"), ("A", "C"), ("B", "D"), ("C", "E"), ("E", "F")])
        manager = LayoutManager(
            graph,
            LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                layout_strategy="bfs",
                layer_spacing=4,
                use_ascii=True,
            ),
        )
        positions, _, _ = manager.calculate_layout()

        self.assertEqual(positions["B"][1], positions["C"][1])
        self.assertGreater(positions["D"][1], positions["B"][1])
        self.assertEqual(positions["D"][1], positions["E"][1])
        self.assertGreater(positions["F"][1], positions["E"][1])

    def test_bipartite_layout_strategy_respects_side_hints(self):
        graph = nx.DiGraph()
        graph.add_edge("ROOT", "LEFT_CHILD", side="left")
        graph.add_edge("ROOT", "RIGHT_CHILD", side="right")

        manager = LayoutManager(
            graph,
            LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                layout_strategy="bipartite",
                layer_spacing=4,
                use_ascii=True,
            ),
        )
        positions, _, _ = manager.calculate_layout()

        self.assertLess(positions["LEFT_CHILD"][0], positions["RIGHT_CHILD"][0])

    def test_circular_layout_strategy_spreads_nodes_without_overlap(self):
        graph = nx.DiGraph(
            [
                ("A", "B"),
                ("B", "C"),
                ("C", "D"),
                ("D", "E"),
                ("E", "F"),
                ("F", "A"),
            ]
        )
        manager = LayoutManager(
            graph,
            LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                layout_strategy="circular",
                layer_spacing=4,
                use_ascii=True,
            ),
        )
        positions, _, _ = manager.calculate_layout()

        self.assertGreaterEqual(len({x for x, _ in positions.values()}), 3)
        self.assertGreaterEqual(len({y for _, y in positions.values()}), 3)

        nodes = list(graph.nodes())
        for idx, node_a in enumerate(nodes):
            rect_a = manager._node_rect(node_a, *positions[node_a])  # noqa: SLF001
            for node_b in nodes[idx + 1 :]:
                rect_b = manager._node_rect(node_b, *positions[node_b])  # noqa: SLF001
                self.assertFalse(
                    manager._rectangles_overlap(rect_a, rect_b)  # noqa: SLF001
                )

    def test_planar_layout_strategy_positions_nodes(self):
        graph = nx.DiGraph(
            [
                ("A", "B"),
                ("B", "C"),
                ("C", "D"),
                ("D", "A"),
                ("A", "C"),
            ]
        )
        manager = LayoutManager(
            graph,
            LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                layout_strategy="planar",
                layer_spacing=4,
                use_ascii=True,
            ),
        )
        positions, _, _ = manager.calculate_layout()

        self.assertEqual(set(positions.keys()), set(graph.nodes()))
        self.assertGreaterEqual(len({x for x, _ in positions.values()}), 2)
        self.assertGreaterEqual(len({y for _, y in positions.values()}), 2)

    def test_planar_layout_strategy_falls_back_for_non_planar_graph(self):
        graph = nx.DiGraph(nx.complete_bipartite_graph(3, 3))
        manager = LayoutManager(
            graph,
            LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                layout_strategy="planar",
                layer_spacing=4,
                use_ascii=True,
            ),
        )
        positions, _, _ = manager.calculate_layout()

        self.assertEqual(set(positions.keys()), set(graph.nodes()))
        self.assertGreaterEqual(len({y for _, y in positions.values()}), 2)

    def test_kamada_kawai_layout_strategy_positions_nodes(self):
        graph = nx.DiGraph([("A", "B"), ("A", "C"), ("B", "D"), ("C", "E"), ("D", "E")])
        manager = LayoutManager(
            graph,
            LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                layout_strategy="kamada_kawai",
                layer_spacing=4,
                use_ascii=True,
            ),
        )
        positions, _, _ = manager.calculate_layout()

        self.assertEqual(set(positions.keys()), set(graph.nodes()))
        self.assertGreaterEqual(len({x for x, _ in positions.values()}), 3)
        self.assertGreaterEqual(len({y for _, y in positions.values()}), 2)

    def test_random_layout_strategy_positions_nodes(self):
        graph = nx.DiGraph([(f"N{i}", f"N{i + 1}") for i in range(6)])
        manager = LayoutManager(
            graph,
            LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                layout_strategy="random",
                layer_spacing=4,
                use_ascii=True,
            ),
        )
        positions, _, _ = manager.calculate_layout()

        self.assertEqual(set(positions.keys()), set(graph.nodes()))
        self.assertGreaterEqual(len({x for x, _ in positions.values()}), 3)

    def test_spring_layout_strategy_positions_nodes(self):
        graph = nx.DiGraph([(f"S{i}", f"S{i + 1}") for i in range(6)])
        manager = LayoutManager(
            graph,
            LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                layout_strategy="spring",
                layer_spacing=4,
                use_ascii=True,
            ),
        )
        positions, _, _ = manager.calculate_layout()

        self.assertEqual(set(positions.keys()), set(graph.nodes()))
        self.assertGreaterEqual(len({x for x, _ in positions.values()}), 3)

    def test_arf_layout_strategy_positions_nodes(self):
        graph = nx.DiGraph([(f"A{i}", f"A{i + 1}") for i in range(6)])
        manager = LayoutManager(
            graph,
            LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                layout_strategy="arf",
                layer_spacing=4,
                use_ascii=True,
            ),
        )
        positions, _, _ = manager.calculate_layout()

        self.assertEqual(set(positions.keys()), set(graph.nodes()))
        self.assertGreaterEqual(len({x for x, _ in positions.values()}), 3)

    def test_spiral_layout_strategy_positions_nodes(self):
        graph = nx.DiGraph([(f"P{i}", f"P{i + 1}") for i in range(8)])
        manager = LayoutManager(
            graph,
            LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                layout_strategy="spiral",
                layer_spacing=4,
                use_ascii=True,
            ),
        )
        positions, _, _ = manager.calculate_layout()

        self.assertEqual(set(positions.keys()), set(graph.nodes()))
        self.assertGreaterEqual(len({x for x, _ in positions.values()}), 3)
        self.assertGreaterEqual(len({y for _, y in positions.values()}), 3)

    def test_shell_layout_strategy_positions_nodes(self):
        graph = nx.DiGraph(
            [("Root", "B"), ("Root", "C"), ("B", "D"), ("C", "E"), ("E", "F")]
        )
        manager = LayoutManager(
            graph,
            LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                layout_strategy="shell",
                layer_spacing=4,
                use_ascii=True,
            ),
        )
        positions, _, _ = manager.calculate_layout()

        self.assertEqual(set(positions.keys()), set(graph.nodes()))
        self.assertGreaterEqual(len({x for x, _ in positions.values()}), 2)
        self.assertGreaterEqual(len({y for _, y in positions.values()}), 2)

    def test_multipartite_layout_strategy_uses_subset_attributes(self):
        graph = nx.DiGraph()
        graph.add_node("A", subset=0)
        graph.add_node("B", subset=0)
        graph.add_node("C", subset=1)
        graph.add_node("D", subset=1)
        graph.add_node("E", subset=2)
        graph.add_edges_from([("A", "C"), ("B", "D"), ("C", "E"), ("D", "E")])

        manager = LayoutManager(
            graph,
            LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                layout_strategy="multipartite",
                layer_spacing=4,
                use_ascii=True,
            ),
        )
        positions, _, _ = manager.calculate_layout()

        self.assertEqual(positions["A"][1], positions["B"][1])
        self.assertEqual(positions["C"][1], positions["D"][1])
        self.assertNotEqual(positions["A"][1], positions["C"][1])
        self.assertNotEqual(positions["C"][1], positions["E"][1])


if __name__ == "__main__":
    unittest.main()
