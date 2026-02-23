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
            LayoutOptions(node_style=NodeStyle.MINIMAL, use_labels=False, use_ascii=True),
        )
        with_labels = LayoutManager(
            graph,
            LayoutOptions(node_style=NodeStyle.MINIMAL, use_labels=True, use_ascii=True),
        )

        self.assertGreater(
            with_labels._get_node_width("n1"),  # noqa: SLF001
            without_labels._get_node_width("n1"),  # noqa: SLF001
        )


if __name__ == "__main__":
    unittest.main()
