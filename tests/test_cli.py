"""Tests for PHART CLI functionality."""

from __future__ import annotations

import unittest
import tempfile
import shutil
import re
from pathlib import Path
import sys
from io import StringIO
from unittest.mock import patch


from phart.cli import create_layout_options, main, parse_args


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
        self.plantuml_file = Path(self.temp_dir) / "simple.puml"
        plantuml_content = """
@startuml
participant "Alice User" as Alice
participant Bob
Alice -> Bob : hello
@enduml
"""
        self.plantuml_file.write_text(plantuml_content, encoding="utf-8")
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

        # Create Python file with script-level binary tree options
        self.py_script_options_file = Path(self.temp_dir) / "test_script_options.py"
        script_options_content = """
import networkx as nx
from phart import ASCIIRenderer, LayoutOptions, NodeStyle

def main():
    G = nx.DiGraph()
    G.add_edge("ROOT", "Z", side="left")
    G.add_edge("ROOT", "A", side="right")
    options = LayoutOptions(
        binary_tree_layout=True,
        node_style=NodeStyle.MINIMAL,
        use_ascii=True,
    )
    renderer = ASCIIRenderer(G, options=options)
    print(renderer.render())
"""
        self.py_script_options_file.write_text(script_options_content, encoding="utf-8")

        # Create Python file to verify script argv forwarding
        self.py_argv_file = Path(self.temp_dir) / "test_argv.py"
        argv_content = """
import sys

def main():
    depth = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    print(f"DEPTH:{depth}")
"""
        self.py_argv_file.write_text(argv_content, encoding="utf-8")
        self.py_wide_output_file = Path(self.temp_dir) / "test_wide_output.py"
        wide_output_content = """
def main():
    print("ABCDEFGHIJKLMNO")
"""
        self.py_wide_output_file.write_text(wide_output_content, encoding="utf-8")
        self.py_multirow_output_file = Path(self.temp_dir) / "test_multirow_output.py"
        multirow_output_content = """
def main():
    print("ROW0")
    print("ROW1")
    print("ROW2")
    print("ROW3")
"""
        self.py_multirow_output_file.write_text(
            multirow_output_content, encoding="utf-8"
        )
        self.py_ansi_output_file = Path(self.temp_dir) / "test_ansi_output.py"
        ansi_output_content = """
def main():
    print("\\x1b[31mABCDEFGHIJ\\x1b[0m")
"""
        self.py_ansi_output_file.write_text(ansi_output_content, encoding="utf-8")

        # Create Python file with script-level bbox disabled, for CLI override tests
        self.py_bbox_override_file = Path(self.temp_dir) / "test_bbox_override.py"
        bbox_override_content = """
import networkx as nx
from phart import ASCIIRenderer, LayoutOptions

def main():
    G = nx.DiGraph()
    G.add_edge("A", "B")
    options = LayoutOptions(
        bboxes=False,
        use_ascii=True,
    )
    renderer = ASCIIRenderer(G, options=options)
    print(renderer.render())
"""
        self.py_bbox_override_file.write_text(bbox_override_content, encoding="utf-8")

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

    def test_plantuml_rendering(self):
        """Test basic PlantUML file rendering."""
        sys.argv = ["phart", str(self.plantuml_file)]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        output = self.stdout.getvalue()
        self.assertIn("Alice", output)
        self.assertIn("Bob", output)
        self.assertNotIn("Error", self.stderr.getvalue())

    def test_output_format_ditaa_puml(self):
        sys.argv = [
            "phart",
            "--output-format",
            "ditaa-puml",
            str(self.test_text_file),
        ]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        output = self.stdout.getvalue()
        self.assertIn("@startditaa", output)
        self.assertIn("@endditaa", output)

    def test_output_format_svg(self):
        sys.argv = [
            "phart",
            "--output-format",
            "svg",
            str(self.test_text_file),
        ]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        output = self.stdout.getvalue()
        self.assertIn("<svg", output)
        self.assertIn("<text", output)

    @patch("phart.cli.load_renderer_from_file")
    def test_output_format_svg_path_mode(self, mock_load_renderer):
        mock_renderer = mock_load_renderer.return_value
        mock_renderer.render_svg.return_value = "<svg><path/></svg>\n"
        sys.argv = [
            "phart",
            "--output-format",
            "svg",
            "--svg-text-mode",
            "path",
            "--svg-font-path",
            "/tmp/test-font.ttf",
            str(self.test_text_file),
        ]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        output = self.stdout.getvalue()
        self.assertIn("<svg", output)
        self.assertIn("<path", output)
        self.assertTrue(mock_renderer.render_svg.called)
        call_kwargs = mock_renderer.render_svg.call_args.kwargs
        self.assertEqual(call_kwargs.get("text_mode"), "path")
        self.assertEqual(call_kwargs.get("font_path"), "/tmp/test-font.ttf")

    def test_output_format_html(self):
        sys.argv = [
            "phart",
            "--output-format",
            "html",
            str(self.test_text_file),
        ]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        output = self.stdout.getvalue()
        self.assertIn("<!DOCTYPE html>", output)
        self.assertIn("<pre", output)

    def test_output_format_latex_markdown(self):
        sys.argv = [
            "phart",
            "--output-format",
            "latex-markdown",
            str(self.test_text_file),
        ]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        output = self.stdout.getvalue()
        self.assertIn(r"\textcolor", output)
        self.assertIn("$", output)

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

    def test_python_script_options_preserve_charset_ansi_color_support(self):
        sys.argv = [
            "phart",
            "--charset",
            "ansi",
            "--colors",
            str(self.py_script_options_file),
        ]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        output = self.stdout.getvalue()
        self.assertIn("\x1b[", output)
        stripped = re.sub(r"\x1b\[[0-9;]*m", "", output)
        self.assertTrue(all(ord(c) < 128 for c in stripped))
        self.assertNotIn("Error", self.stderr.getvalue())

    def test_output_format_svg_for_py_input(self):
        sys.argv = [
            "phart",
            "--output-format",
            "svg",
            str(self.py_main_file),
        ]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        output = self.stdout.getvalue()
        self.assertIn("<svg", output)
        self.assertIn("<text", output)
        self.assertNotIn("Error", self.stderr.getvalue())

    def test_output_format_latex_markdown_for_py_input(self):
        sys.argv = [
            "phart",
            "--output-format",
            "latex-markdown",
            str(self.py_main_file),
        ]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        output = self.stdout.getvalue()
        self.assertIn(r"\textcolor", output)
        self.assertIn("$", output)
        self.assertNotIn("Error", self.stderr.getvalue())

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
        self.assertIn(
            "Could not parse file as PlantUML, GraphML, or DOT format", error_msg
        )

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
        self.assertNotIn(
            "Could not parse file as PlantUML, GraphML, or DOT format", error_msg
        )

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

    def test_python_with_output_file_writes_render_to_file(self):
        output_file = Path(self.temp_dir) / "python_output.txt"
        sys.argv = ["phart", str(self.py_main_file), "--output", str(output_file)]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        self.assertEqual(self.stdout.getvalue(), "")
        self.assertTrue(output_file.exists())
        content = output_file.read_text(encoding="utf-8")
        self.assertIn("A", content)
        self.assertIn("B", content)
        self.assertIn("C", content)
        self.assertNotIn("Error", self.stderr.getvalue())

    def test_markdown_output_auto_uses_nbsp_padding(self):
        output_file = Path(self.temp_dir) / "diagram.md"
        sys.argv = ["phart", str(self.py_main_file), "--output", str(output_file)]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        content = output_file.read_text(encoding="utf-8")
        self.assertIn("\u00a0", content)

    def test_markdown_output_whitespace_override_ascii_space(self):
        output_file = Path(self.temp_dir) / "diagram.md"
        sys.argv = [
            "phart",
            "--whitespace",
            "ascii-space",
            str(self.py_main_file),
            "--output",
            str(output_file),
        ]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        content = output_file.read_text(encoding="utf-8")
        self.assertNotIn("\u00a0", content)

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

    def test_python_respects_script_binary_tree_options_when_cli_omits_them(self):
        sys.argv = ["phart", str(self.py_script_options_file)]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        implicit_output = self.stdout.getvalue()
        self.assertNotIn("Error", self.stderr.getvalue())

        self.stdout.truncate(0)
        self.stdout.seek(0)
        self.stderr.truncate(0)
        self.stderr.seek(0)

        sys.argv = ["phart", "--binary-tree", str(self.py_script_options_file)]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        explicit_output = self.stdout.getvalue()
        self.assertNotIn("Error", self.stderr.getvalue())

        self.assertEqual(implicit_output, explicit_output)

    def test_python_script_args_are_forwarded_after_separator(self):
        sys.argv = ["phart", str(self.py_argv_file), "--", "7"]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        output = self.stdout.getvalue()
        self.assertIn("DEPTH:7", output)
        self.assertNotIn("Error", self.stderr.getvalue())

    def test_gedcom_example_handles_level2_family_subattrs_without_dict_key_errors(
        self,
    ):
        gedcom_example = Path(__file__).resolve().parents[1] / "examples" / "gedcom.py"
        sys.argv = [
            "phart",
            "--labels",
            "--bboxes",
            "--bbox-multiline-labels",
            "--node-label-lines",
            "name,*",
            str(gedcom_example),
            "--",
            "fam_marr.ged",
        ]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        self.assertNotIn("Error", self.stderr.getvalue())

    def test_paginate_output_width_selects_page_x(self):
        sys.argv = [
            "phart",
            "--paginate-output-width",
            "10",
            str(self.py_wide_output_file),
        ]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        self.assertEqual(self.stdout.getvalue(), "ABCDEFGHIJ")

    def test_paginate_output_width_supports_overlap_and_page_x(self):
        sys.argv = [
            "phart",
            "--paginate-output-width",
            "10",
            "--paginate-overlap",
            "2",
            "--page-x",
            "1",
            str(self.py_wide_output_file),
        ]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        self.assertEqual(self.stdout.getvalue(), "FGHIJKLMNO")

    def test_paginate_output_width_list_pages_writes_index_to_stderr(self):
        sys.argv = [
            "phart",
            "--paginate-output-width",
            "10",
            "--list-pages",
            str(self.py_wide_output_file),
        ]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        self.assertIn("Pagination:", self.stderr.getvalue())
        self.assertIn("page[x=0,y=0]", self.stderr.getvalue())

    def test_paginate_output_width_write_pages_emits_files(self):
        page_dir = Path(self.temp_dir) / "pages"
        sys.argv = [
            "phart",
            "--paginate-output-width",
            "10",
            "--write-pages",
            str(page_dir),
            str(self.py_wide_output_file),
        ]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        self.assertTrue((page_dir / "page_x00_y00.txt").exists())
        self.assertTrue((page_dir / "page_x01_y00.txt").exists())

    def test_paginate_output_width_auto_requires_tty_stdout(self):
        sys.argv = [
            "phart",
            "--paginate-output-width",
            "auto",
            str(self.py_wide_output_file),
        ]
        exit_code = main()
        self.assertEqual(exit_code, 1)
        self.assertIn("requires terminal stdout", self.stderr.getvalue())

    def test_paginate_output_height_selects_page_y(self):
        sys.argv = [
            "phart",
            "--paginate-output-height",
            "2",
            "--page-y",
            "1",
            str(self.py_multirow_output_file),
        ]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        self.assertEqual(self.stdout.getvalue(), "ROW2\nROW3")

    def test_paginate_output_height_auto_requires_tty_stdout(self):
        sys.argv = [
            "phart",
            "--paginate-output-height",
            "auto",
            str(self.py_multirow_output_file),
        ]
        exit_code = main()
        self.assertEqual(exit_code, 1)
        self.assertIn(
            "paginate-output-height auto requires terminal stdout",
            self.stderr.getvalue(),
        )

    def test_paginate_output_width_rejects_non_text_format(self):
        sys.argv = [
            "phart",
            "--output-format",
            "svg",
            "--paginate-output-width",
            "10",
            str(self.py_wide_output_file),
        ]
        exit_code = main()
        self.assertEqual(exit_code, 1)
        self.assertIn(
            "only supported with --output-format text", self.stderr.getvalue()
        )

    def test_paginate_width_ignores_ansi_escape_length(self):
        sys.argv = [
            "phart",
            "--paginate-output-width",
            "5",
            "--paginate-overlap",
            "0",
            str(self.py_ansi_output_file),
        ]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        output = self.stdout.getvalue()
        stripped = re.sub(r"\x1b\[[0-9;]*m", "", output)
        self.assertEqual(stripped, "ABCDE")

    def test_paginate_width_preserves_ansi_sequence_integrity(self):
        sys.argv = [
            "phart",
            "--paginate-output-width",
            "5",
            "--paginate-overlap",
            "0",
            "--page-x",
            "1",
            str(self.py_ansi_output_file),
        ]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        output = self.stdout.getvalue()
        stripped = re.sub(r"\x1b\[[0-9;]*m", "", output)
        self.assertEqual(stripped, "FGHIJ")
        self.assertIn("\x1b[31m", output)
        self.assertIn("\x1b[0m", output)

    def test_python_bbox_alias_overrides_script_bbox_option(self):
        sys.argv = ["phart", "--bbox", str(self.py_bbox_override_file)]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        output = self.stdout.getvalue()
        self.assertIn("+", output)
        self.assertNotIn("[A]", output)
        self.assertNotIn("[B]", output)
        self.assertNotIn("Error", self.stderr.getvalue())

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

    def test_shared_ports_mode_flag(self):
        sys.argv = [
            "phart",
            "--bboxes",
            "--edge-anchors",
            "ports",
            "--shared-ports",
            "none",
            str(self.test_text_file),
        ]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        self.assertNotIn("Error", self.stderr.getvalue())

    def test_bidirectional_mode_flag(self):
        sys.argv = [
            "phart",
            "--bidirectional-mode",
            "separate",
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

    def test_colors_flag_emits_ansi_with_ansi_charset(self):
        sys.argv = ["phart", "--colors", "--charset", "ansi", str(self.test_text_file)]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        output = self.stdout.getvalue()
        self.assertIn("\x1b[", output)
        stripped = re.sub(r"\x1b\[[0-9;]*m", "", output)
        self.assertTrue(all(ord(c) < 128 for c in stripped))

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

    def test_edge_color_rule_is_ignored_outside_attr_mode(self):
        sys.argv = [
            "phart",
            "--colors",
            "source",
            "--edge-color-rule",
            "relationship:friend=green",
            str(self.test_text_file),
        ]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        self.assertNotIn("Error", self.stderr.getvalue())

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

    def test_node_order_flags_populate_layout_options(self):
        sys.argv = [
            "phart",
            "--node-order",
            "numeric",
            "--node-order-attr",
            "rank",
            str(self.test_text_file),
        ]
        args, _unknown, explicit_layout_fields, _module_argv = parse_args()
        options = create_layout_options(args, explicit_layout_fields)

        self.assertEqual(options.node_order_mode, "numeric")
        self.assertEqual(options.node_order_attr, "rank")

    def test_whitespace_flag_populates_layout_options(self):
        sys.argv = [
            "phart",
            "--whitespace",
            "ascii-space",
            str(self.test_text_file),
        ]
        args, _unknown, explicit_layout_fields, _module_argv = parse_args()
        options = create_layout_options(args, explicit_layout_fields)
        self.assertEqual(options.whitespace_mode, "ascii_space")

    def test_node_label_line_flags_populate_layout_options(self):
        sys.argv = [
            "phart",
            "--labels",
            "--node-label-lines",
            "name,lifespan,birt.date",
            "--node-label-sep",
            " | ",
            "--node-label-max-lines",
            "2",
            "--bbox-multiline-labels",
            str(self.test_text_file),
        ]
        args, _unknown, explicit_layout_fields, _module_argv = parse_args()
        options = create_layout_options(args, explicit_layout_fields)

        self.assertTrue(options.use_labels)
        self.assertEqual(options.node_label_lines, ("name", "lifespan", "birt.date"))
        self.assertEqual(options.node_label_sep, " | ")
        self.assertEqual(options.node_label_max_lines, 2)
        self.assertTrue(options.bbox_multiline_labels)
