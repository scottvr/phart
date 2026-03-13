"""Targeted tests for layout-specific branches."""

import math
import unittest

import networkx as nx  # type: ignore

from phart.layout import LayoutManager
from phart.styles import LayoutOptions, NodeStyle


class TestLayoutManager(unittest.TestCase):
    @staticmethod
    def _clockwise_order_from_top(
        positions: dict[object, tuple[int, int]],
    ) -> list[object]:
        center_x = sum(x for x, _ in positions.values()) / max(len(positions), 1)
        center_y = sum(y for _, y in positions.values()) / max(len(positions), 1)

        return sorted(
            positions,
            key=lambda node: (
                math.atan2(
                    positions[node][0] - center_x,
                    center_y - positions[node][1],
                )
                % (2 * math.pi)
            ),
        )

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

    def test_asymmetric_tree_top_layer_is_compact(self):
        """Top siblings should not be pushed wider than required by overlap."""
        graph = nx.DiGraph()
        graph.add_edge("1", "2", side="left")
        graph.add_edge("1", "Z1", side="right")
        graph.add_edge("2", "4", side="left")
        graph.add_edge("2", "F1", side="right")
        graph.add_edge("4", "8", side="left")
        graph.add_edge("4", "E1", side="right")
        graph.add_edge("8", "L1", side="left")
        graph.add_edge("8", "L2", side="right")

        options = LayoutOptions(
            binary_tree_layout=True,
            layout_strategy="hierarchical",
            node_style=NodeStyle.MINIMAL,
            node_spacing=5,
            use_ascii=True,
        )
        manager = LayoutManager(graph, options)
        positions, _, _ = manager.calculate_layout()

        top_gap = (
            positions["Z1"][0]
            - (positions["2"][0] + manager._get_node_width("2") - 1)  # noqa: SLF001
            - 1
        )
        lower_gap = (
            positions["L2"][0]
            - (positions["L1"][0] + manager._get_node_width("L1") - 1)  # noqa: SLF001
            - 1
        )

        self.assertEqual(top_gap, options.node_spacing)
        self.assertEqual(lower_gap, options.node_spacing)

    def test_subtree_compaction_expands_only_when_descendant_overlap_requires_it(self):
        """Sibling gap can widen only when deeper descendant rows would collide."""
        graph = nx.DiGraph()
        graph.add_edge("ROOT", "LEFTLONG", side="left")
        graph.add_edge("ROOT", "R", side="right")
        graph.add_edge("LEFTLONG", "F1", side="right")
        graph.add_edge("R", "ZLEFTLONG", side="left")

        options = LayoutOptions(
            binary_tree_layout=True,
            layout_strategy="hierarchical",
            node_style=NodeStyle.MINIMAL,
            node_spacing=4,
            use_ascii=True,
        )
        manager = LayoutManager(graph, options)
        positions, _, _ = manager.calculate_layout()

        depth_one_gap = (
            positions["R"][0]
            - (
                positions["LEFTLONG"][0]
                + manager._get_node_width("LEFTLONG")  # noqa: SLF001
                - 1
            )
            - 1
        )
        depth_two_gap = (
            positions["ZLEFTLONG"][0]
            - (positions["F1"][0] + manager._get_node_width("F1") - 1)  # noqa: SLF001
            - 1
        )

        self.assertGreater(depth_one_gap, options.node_spacing)
        self.assertEqual(depth_two_gap, options.node_spacing)

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

    def test_circular_layout_uses_natural_order_by_default(self):
        graph = nx.DiGraph()
        graph.add_nodes_from([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

        manager = LayoutManager(
            graph,
            LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                layout_strategy="circular",
                use_ascii=True,
            ),
        )
        positions, _, _ = manager.calculate_layout()

        self.assertEqual(
            self._clockwise_order_from_top(positions),
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        )

    def test_circular_layout_can_preserve_graph_insertion_order(self):
        graph = nx.DiGraph()
        insertion_order = [0, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
        graph.add_nodes_from(insertion_order)

        manager = LayoutManager(
            graph,
            LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                layout_strategy="circular",
                node_order_mode="preserve",
                use_ascii=True,
            ),
        )
        positions, _, _ = manager.calculate_layout()

        self.assertEqual(self._clockwise_order_from_top(positions), insertion_order)

    def test_node_order_attr_sorts_nodes_by_attribute_value(self):
        graph = nx.DiGraph()
        graph.add_node("third", rank=3)
        graph.add_node("first", rank=1)
        graph.add_node("second", rank=2)

        manager = LayoutManager(
            graph,
            LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                node_order_attr="rank",
                node_order_mode="numeric",
                use_ascii=True,
            ),
        )

        self.assertEqual(
            manager._ordered_nodes(graph.nodes(), default_mode="alpha"),  # noqa: SLF001
            ["first", "second", "third"],
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

    def test_coordinate_layout_strategies_compact_three_node_graph(self):
        graph = nx.DiGraph([("A", "B"), ("B", "C"), ("C", "A")])
        strategies = (
            "random",
            "spring",
            "kamada_kawai",
            "planar",
            "arf",
            "spiral",
            "shell",
        )

        for strategy in strategies:
            with self.subTest(strategy=strategy):
                manager = LayoutManager(
                    graph,
                    LayoutOptions(
                        node_style=NodeStyle.MINIMAL,
                        layout_strategy=strategy,
                        node_spacing=4,
                        layer_spacing=4,
                        use_ascii=True,
                    ),
                )
                positions, _, _ = manager.calculate_layout()
                xs = [x for x, _ in positions.values()]
                ys = [y for _, y in positions.values()]
                self.assertLessEqual(max(xs) - min(xs), 15)
                self.assertLessEqual(max(ys) - min(ys), 15)

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

    def test_constrained_layered_populates_partition_plan(self):
        graph = nx.DiGraph()
        graph.add_edge("R", "A1")
        graph.add_edge("R", "A2")
        graph.add_edge("R", "A3")
        graph.add_edge("R", "A4")
        graph.add_edge("A1", "B1")
        graph.add_edge("A2", "B2")

        manager = LayoutManager(
            graph,
            LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                layout_strategy="constrained_layered",
                target_canvas_width=12,
                node_spacing=4,
                use_ascii=True,
            ),
        )
        positions, _, _ = manager.calculate_layout()

        self.assertEqual(set(positions.keys()), set(graph.nodes()))
        self.assertIsNotNone(manager.partition_plan)
        assert manager.partition_plan is not None
        self.assertEqual(len(manager.partition_plan.partitions), 3)
        self.assertEqual(manager.partition_plan.node_to_partition["R"], 0)
        self.assertEqual(manager.partition_plan.node_to_partition["A1"], 1)
        self.assertEqual(manager.partition_plan.node_to_partition["B1"], 2)
        self.assertTrue(
            any(
                edge.u == "R" and edge.v == "A1"
                for edge in manager.partition_plan.cross_partition_edges
            )
        )

    def test_constrained_layered_partition_order_size_reorders_panels(self):
        graph = nx.DiGraph()
        graph.add_edge("R", "A1")
        graph.add_edge("R", "A2")
        graph.add_edge("R", "A3")
        graph.add_edge("R", "A4")
        graph.add_edge("A1", "B1")
        graph.add_edge("A2", "B2")

        manager = LayoutManager(
            graph,
            LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                layout_strategy="constrained_layered",
                target_canvas_width=12,
                partition_order="size",
                node_spacing=4,
                use_ascii=True,
            ),
        )
        positions, _, _ = manager.calculate_layout()

        self.assertEqual(positions["A1"][1], 0)
        self.assertEqual(positions["A2"][1], 0)
        self.assertEqual(positions["A3"][1], 0)
        self.assertEqual(positions["A4"][1], 0)
        self.assertGreater(positions["R"][1], positions["A1"][1])
        self.assertIsNotNone(manager.partition_plan)
        assert manager.partition_plan is not None
        self.assertEqual(manager.partition_plan.node_to_partition["A1"], 0)
        self.assertEqual(manager.partition_plan.node_to_partition["B1"], 1)
        self.assertEqual(manager.partition_plan.node_to_partition["R"], 2)

    def test_constrained_layered_rejects_left_right_flow(self):
        graph = nx.DiGraph([("A", "B")])
        manager = LayoutManager(
            graph,
            LayoutOptions(
                node_style=NodeStyle.MINIMAL,
                layout_strategy="constrained_layered",
                target_canvas_width=10,
                flow_direction="left",
                use_ascii=True,
            ),
        )

        with self.assertRaises(ValueError):
            manager.calculate_layout()


if __name__ == "__main__":
    unittest.main()
