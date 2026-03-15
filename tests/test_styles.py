"""Tests for LayoutOptions validation and normalization."""

import unittest

from phart.styles import LayoutOptions


class TestLayoutOptions(unittest.TestCase):
    def test_node_order_mode_normalizes_hyphenated_values(self):
        options = LayoutOptions(node_order_mode="layout-default")

        self.assertEqual(options.node_order_mode, "layout_default")

    def test_invalid_attr_node_order_mode_is_rejected(self):
        with self.assertRaises(ValueError):
            LayoutOptions(node_order_mode="attr")

    def test_blank_node_order_attr_normalizes_to_none(self):
        options = LayoutOptions(node_order_attr="   ")

        self.assertIsNone(options.node_order_attr)

    def test_node_order_attr_is_allowed_without_special_mode(self):
        options = LayoutOptions(node_order_mode="natural", node_order_attr="rank")

        self.assertEqual(options.node_order_mode, "natural")
        self.assertEqual(options.node_order_attr, "rank")

    def test_bidirectional_mode_validates_and_normalizes(self):
        options = LayoutOptions(bidirectional_mode="SEPARATE")

        self.assertEqual(options.bidirectional_mode, "separate")

    def test_invalid_bidirectional_mode_is_rejected(self):
        with self.assertRaises(ValueError):
            LayoutOptions(bidirectional_mode="split")

    def test_text_display_width_counts_cjk_as_double_width(self):
        options = LayoutOptions()
        self.assertEqual(options.get_text_display_width("ASCII"), 5)
        self.assertEqual(options.get_text_display_width("中文"), 4)

    def test_node_dimensions_use_display_width(self):
        options = LayoutOptions(node_style="minimal", bboxes=True, use_ascii=True)
        width, _height = options.get_node_dimensions("中文")
        # 4 columns for text + 2 inner hpad + 2 borders
        self.assertEqual(width, 8)

    def test_whitespace_mode_normalizes_hyphenated_values(self):
        options = LayoutOptions(whitespace_mode="ascii-space")
        self.assertEqual(options.whitespace_mode, "ascii_space")

    def test_invalid_whitespace_mode_is_rejected(self):
        with self.assertRaises(ValueError):
            LayoutOptions(whitespace_mode="tabs")


if __name__ == "__main__":
    unittest.main()
