"""Tests for PHART CLI functionality."""
# src path: tests\test_cli.py

import unittest
import tempfile
import shutil
import re
from pathlib import Path
import sys
from io import StringIO
from unittest.mock import patch

from phart.cli import main


class TestCLI(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_text_file = Path(self.temp_dir) / "test.txt"

        # Create a valid DOT file
        self.dot_content = """
        digraph {
            A -> B;
            B -> C;
        }
        """
        self.test_text_file.write_text(self.dot_content, encoding="utf-8")
        self.labeled_dot_file = Path(self.temp_dir) / "labeled.dot"
        labeled_dot = """
        digraph {
            n1 [label="Alpha Node"];
            n2 [label="Beta Node"];
            n1 -> n2;
        }
        """
        self.labeled_dot_file.write_text(labeled_dot, encoding="utf-8")
        self.edge_attr_dot_file = Path(self.temp_dir) / "edge_attr.dot"
        edge_attr_dot = """
        digraph {
            Alice -> Bob [relationship="friend"];
            Bob -> Charlie [relationship="enemy"];
        }
        """
        self.edge_attr_dot_file.write_text(edge_attr_dot, encoding="utf-8")
        # Create test Python file with main() function
        self.py_main_file = Path(self.temp_dir) / "test_main.py"
        main_content = """
import networkx as nx
from phart import ASCIIRenderer

def main():
    G = nx.DiGraph()
    G.add_edges_from([("A", "B"), ("B", "C")])
    renderer = ASCIIRenderer(G)
    print(renderer.render())
"""
        self.py_main_file.write_text(main_content, encoding="utf-8")

        # Create test Python file with __main__ block
        self.py_block_file = Path(self.temp_dir) / "test_block.py"
        block_content = """
import networkx as nx
from phart import ASCIIRenderer

if __name__ == "__main__":
    G = nx.DiGraph()
    G.add_edges_from([("X", "Y"), ("Y", "Z")])
    renderer = ASCIIRenderer(G)
    print(renderer.render())
"""
        self.py_block_file.write_text(block_content, encoding="utf-8")

        # Create test Python file with custom function
        self.py_custom_file = Path(self.temp_dir) / "test_custom.py"
        custom_content = """
import networkx as nx
from phart import ASCIIRenderer

def demonstrate_graph():
    G = nx.DiGraph()
    G.add_edges_from([("P", "Q"), ("Q", "R")])
    renderer = ASCIIRenderer(G)
    print(renderer.render())
"""
        self.py_custom_file.write_text(custom_content, encoding="utf-8")

        # Save original stdout/stderr
        self.old_stdout = sys.stdout
        self.old_stderr = sys.stderr
        self.stdout = StringIO()
        self.stderr = StringIO()
        sys.stdout = self.stdout
        sys.stderr = self.stderr

        # Save original argv
        self.old_argv = sys.argv

    def tearDown(self):
        """Restore environment."""
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr
        sys.argv = self.old_argv
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_basic_rendering(self):
        """Test basic DOT file rendering."""
        sys.argv = ["phart", str(self.test_text_file)]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        output = self.stdout.getvalue()
        print(output)
        self.assertIn("A", output)
        self.assertIn("B", output)
        self.assertIn("C", output)
        self.assertNotIn("Error", self.stderr.getvalue())

    def test_style_option(self):
        """Test node style option."""
        sys.argv = ["phart", "--style", "round", str(self.test_text_file)]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        output = self.stdout.getvalue()
        self.assertIn("(A)", output)
        self.assertIn("(B)", output)
        self.assertNotIn("Error", self.stderr.getvalue())

    def test_charset_unicode(self):
        """Test explicit unicode charset option."""
        sys.argv = ["phart", "--charset", "unicode", str(self.test_text_file)]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        output = self.stdout.getvalue()
        # Should find at least one unicode character
        self.assertTrue(any(ord(c) > 127 for c in output))
        self.assertNotIn("Error", self.stderr.getvalue())

    def test_charset_ascii(self):
        """Test ASCII charset option."""
        sys.argv = ["phart", "--charset", "ascii", str(self.test_text_file)]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        output = self.stdout.getvalue()
        # All characters should be ASCII
        self.assertTrue(all(ord(c) < 128 for c in output))
        self.assertNotIn("Error", self.stderr.getvalue())

    def test_charset_ansi_with_colors_uses_ascii_glyphs_and_ansi_escapes(self):
        sys.argv = [
            "phart",
            "--charset",
            "ansi",
            "--colors",
            "source",
            str(self.test_text_file),
        ]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        output = self.stdout.getvalue()
        self.assertIn("\x1b[", output)
        stripped = output.replace("\x1b[0m", "")
        stripped = re.sub(r"\x1b\[[0-9;]*m", "", stripped)
        self.assertTrue(all(ord(c) < 128 for c in stripped))
        self.assertNotIn("Error", self.stderr.getvalue())

    def test_legacy_ascii_flag(self):
        """Test that legacy --ascii flag still works."""
        sys.argv = ["phart", "--ascii", str(self.test_text_file)]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        output = self.stdout.getvalue()
        # All characters should be ASCII
        self.assertTrue(all(ord(c) < 128 for c in output))
        self.assertNotIn("Error", self.stderr.getvalue())

    def test_charset_and_legacy_flag(self):
        """Test interaction between --charset and --ascii flags."""
        # When both specified, --ascii should override --charset unicode
        sys.argv = [
            "phart",
            "--charset",
            "unicode",
            "--ascii",
            str(self.test_text_file),
        ]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        output = self.stdout.getvalue()
        # Should still be ASCII-only despite unicode charset
        self.assertTrue(all(ord(c) < 128 for c in output))
        self.assertNotIn("Error", self.stderr.getvalue())

    def test_legacy_ascii_overrides_charset_ansi_color_support(self):
        sys.argv = [
            "phart",
            "--charset",
            "ansi",
            "--ascii",
            "--colors",
            "source",
            str(self.test_text_file),
        ]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        output = self.stdout.getvalue()
        self.assertNotIn("\x1b[", output)

    def test_invalid_file(self):
        """Test handling of invalid file."""
        sys.argv = ["phart", "nonexistent.dot"]
        exit_code = main()
        self.assertEqual(exit_code, 1)
        self.assertIn("Error", self.stderr.getvalue())

    def test_invalid_content(self):
        """Test handling of invalid input content."""
        self.test_text_file.write_text("This is not a valid graph format")
        sys.argv = ["phart", str(self.test_text_file)]
        exit_code = main()
        self.assertEqual(exit_code, 1)
        error_msg = self.stderr.getvalue()
        self.assertIn("Error", error_msg)
        self.assertIn("Could not parse file as GraphML or DOT format", error_msg)

    def test_option_construction_errors_are_not_reported_as_parse_errors(self):
        sys.argv = ["phart", str(self.test_text_file)]
        with patch(
            "phart.cli.create_layout_options",
            side_effect=ValueError("synthetic options error"),
        ):
            exit_code = main()

        self.assertEqual(exit_code, 1)
        error_msg = self.stderr.getvalue()
        self.assertIn("Error: synthetic options error", error_msg)
        self.assertNotIn("Could not parse file as GraphML or DOT format", error_msg)

    def test_python_with_main(self):
        """Test executing Python file with main() function."""
        sys.argv = ["phart", str(self.py_main_file)]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        output = self.stdout.getvalue()
        self.assertIn("A", output)
        self.assertIn("B", output)
        self.assertIn("C", output)
        self.assertNotIn("Error", self.stderr.getvalue())

    def test_python_with_main_block(self):
        """Test executing Python file with __main__ block."""
        sys.argv = ["phart", str(self.py_block_file)]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        output = self.stdout.getvalue()
        self.assertIn("X", output)
        self.assertIn("Y", output)
        self.assertIn("Z", output)
        self.assertNotIn("Error", self.stderr.getvalue())

    def test_python_custom_function(self):
        """Test executing Python file with custom function."""
        sys.argv = [
            "phart",
            str(self.py_custom_file),
            "--function",
            "demonstrate_graph",
        ]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        output = self.stdout.getvalue()
        self.assertIn("P", output)
        self.assertIn("Q", output)
        self.assertIn("R", output)
        self.assertNotIn("Error", self.stderr.getvalue())

    def test_python_missing_function(self):
        """Test error handling for missing function."""
        sys.argv = ["phart", str(self.py_custom_file), "--function", "nonexistent"]
        exit_code = main()
        self.assertEqual(exit_code, 1)
        self.assertIn("Error: Function 'nonexistent' not found", self.stderr.getvalue())

    def test_bbox_flags(self):
        """Test boxed node flags and widest-size alias."""
        sys.argv = [
            "phart",
            "--bboxes",
            "--hpad",
            "2",
            "--vpad",
            "1",
            "--size-to-widest",
            str(self.test_text_file),
        ]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        output = self.stdout.getvalue()
        self.assertTrue("┌" in output or "+" in output)
        self.assertNotIn("Error", self.stderr.getvalue())

    def test_edge_anchor_mode_flag(self):
        """Test edge anchor mode CLI option."""
        sys.argv = [
            "phart",
            "--bboxes",
            "--edge-anchors",
            "ports",
            str(self.test_text_file),
        ]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        self.assertNotIn("Error", self.stderr.getvalue())

    def test_labels_flag_uses_node_labels(self):
        sys.argv = ["phart", "--labels", str(self.labeled_dot_file)]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        output = self.stdout.getvalue()
        self.assertIn("Alpha Node", output)
        self.assertIn("Beta Node", output)
        self.assertNotIn("n1", output)

    def test_colors_flag_emits_ansi_in_unicode_mode(self):
        sys.argv = ["phart", "--colors", str(self.test_text_file)]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        output = self.stdout.getvalue()
        self.assertIn("\x1b[", output)

    def test_colors_flag_is_ignored_in_ascii_mode(self):
        sys.argv = ["phart", "--colors", "--charset", "ascii", str(self.test_text_file)]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        output = self.stdout.getvalue()
        self.assertNotIn("\x1b[", output)

    def test_colors_mode_argument(self):
        sys.argv = [
            "phart",
            "--colors",
            "target",
            str(self.test_text_file),
        ]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        self.assertNotIn("Error", self.stderr.getvalue())

    def test_edge_anchor_mode_auto_flag(self):
        sys.argv = [
            "phart",
            "--bboxes",
            "--edge-anchors",
            "auto",
            str(self.test_text_file),
        ]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        self.assertNotIn("Error", self.stderr.getvalue())

    def test_colors_attr_mode_with_edge_color_rules(self):
        sys.argv = [
            "phart",
            "--colors",
            "attr",
            "--edge-color-rule",
            "relationship:friend=bright_green,enemy=red",
            str(self.edge_attr_dot_file),
        ]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        output = self.stdout.getvalue()
        self.assertIn("\x1b[", output)
        self.assertNotIn("Error", self.stderr.getvalue())

    def test_edge_color_rule_requires_attr_mode(self):
        sys.argv = [
            "phart",
            "--colors",
            "source",
            "--edge-color-rule",
            "relationship:friend=green",
            str(self.test_text_file),
        ]
        exit_code = main()
        self.assertEqual(exit_code, 1)
        self.assertIn(
            "--edge-color-rule requires --colors attr", self.stderr.getvalue()
        )

    def test_invalid_edge_color_rule_format(self):
        sys.argv = [
            "phart",
            "--colors",
            "attr",
            "--edge-color-rule",
            "relationship",
            str(self.test_text_file),
        ]
        exit_code = main()
        self.assertEqual(exit_code, 1)
        self.assertIn("Invalid --edge-color-rule", self.stderr.getvalue())

    def test_colors_none_matches_omitted_colors(self):
        sys.argv = ["phart", str(self.test_text_file)]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        without_colors = self.stdout.getvalue()

        self.stdout.truncate(0)
        self.stdout.seek(0)
        self.stderr.truncate(0)
        self.stderr.seek(0)

        sys.argv = ["phart", "--colors", "none", str(self.test_text_file)]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        with_none = self.stdout.getvalue()

        self.assertEqual(without_colors, with_none)
        self.assertNotIn("\x1b[", with_none)

    def test_layout_strategy_flag(self):
        sys.argv = ["phart", "--layout", "bfs", str(self.test_text_file)]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        self.assertNotIn("Error", self.stderr.getvalue())

    def test_layout_strategy_alias_flag(self):
        sys.argv = [
            "phart",
            "--layout-strategy",
            "circular",
            str(self.test_text_file),
        ]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        self.assertNotIn("Error", self.stderr.getvalue())

    def test_layout_strategy_phase2_values(self):
        for strategy in (
            "planar",
            "kamada-kawai",
            "spring",
            "arf",
            "spiral",
            "shell",
            "random",
            "multipartite",
        ):
            self.stdout.truncate(0)
            self.stdout.seek(0)
            self.stderr.truncate(0)
            self.stderr.seek(0)
            sys.argv = ["phart", "--layout", strategy, str(self.test_text_file)]
            exit_code = main()
            self.assertEqual(exit_code, 0)
            self.assertNotIn("Error", self.stderr.getvalue())
