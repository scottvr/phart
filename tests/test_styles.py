"""Tests for LayoutOptions validation and normalization."""

import unittest

from phart.styles import LayoutOptions


class TestLayoutOptions(unittest.TestCase):
    def test_node_order_mode_normalizes_hyphenated_values(self):
        options = LayoutOptions(node_order_mode="layout-default")

        self.assertEqual(options.node_order_mode, "layout_default")

    def test_attr_node_order_requires_attribute_name(self):
        with self.assertRaises(ValueError):
            LayoutOptions(node_order_mode="attr")

    def test_blank_node_order_attr_normalizes_to_none(self):
        options = LayoutOptions(node_order_attr="   ")

        self.assertIsNone(options.node_order_attr)


if __name__ == "__main__":
    unittest.main()
