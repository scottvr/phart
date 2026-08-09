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

    def test_label_text_budget_subtracts_borders_and_hpad(self):
        options = LayoutOptions(bboxes=True, hpad=3, node_label_max_width=24)
        # 24 total - 2 borders - (2 * 3) hpad
        self.assertEqual(options.resolve_label_text_budget(), 16)

    def test_label_text_budget_is_none_without_bboxes(self):
        options = LayoutOptions(node_label_max_width=24)
        self.assertIsNone(options.resolve_label_text_budget())

    def test_label_text_budget_is_none_when_multiline_disabled(self):
        options = LayoutOptions(
            bboxes=True, bbox_multiline_labels=False, node_label_max_width=24
        )
        self.assertIsNone(options.resolve_label_text_budget())

    def test_wrap_text_breaks_on_word_boundaries(self):
        options = LayoutOptions()
        self.assertEqual(
            options.wrap_text_to_display_width("alpha beta gamma", 11),
            ["alpha beta", "gamma"],
        )

    def test_wrap_text_hard_breaks_overlong_word(self):
        options = LayoutOptions()
        self.assertEqual(
            options.wrap_text_to_display_width("abcdefghij", 4),
            ["abcd", "efgh", "ij"],
        )

    def test_wrap_text_counts_cjk_as_double_width(self):
        options = LayoutOptions()
        # Each glyph costs two columns, so only three fit in six columns.
        self.assertEqual(
            options.wrap_text_to_display_width("中文字符", 6),
            ["中文字", "符"],
        )

    def test_wrapped_node_width_stays_within_max_width(self):
        options = LayoutOptions(
            node_style="minimal", bboxes=True, use_ascii=True, node_label_max_width=20
        )
        width, height = options.get_node_dimensions("alpha beta gamma delta")
        self.assertLessEqual(width, 20)
        self.assertGreater(height, 3)  # grew past a single content row

    def test_wrap_label_lines_charges_decorator_overhead(self):
        options = LayoutOptions(
            node_style="round", bboxes=True, node_label_max_width=16
        )
        # 16 total - 2 borders - 2 hpad - 2 for the "()" decorators
        lines = options.wrap_label_lines(["alpha beta gamma"], options.get_node_text)
        for line in lines:
            self.assertLessEqual(
                options.get_text_display_width(options.get_node_text(line)), 12
            )

    def test_whitespace_mode_normalizes_hyphenated_values(self):
        options = LayoutOptions(whitespace_mode="ascii-space")
        self.assertEqual(options.whitespace_mode, "ascii_space")

    def test_invalid_whitespace_mode_is_rejected(self):
        with self.assertRaises(ValueError):
            LayoutOptions(whitespace_mode="tabs")


if __name__ == "__main__":
    unittest.main()
