"""Tests for PHART CLI functionality."""
# src path: tests\test_cli.py

import unittest
import tempfile
from pathlib import Path
import sys
from io import StringIO

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
        self.test_text_file.unlink()
        Path(self.temp_dir).rmdir()

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
        self.assertEqual(self.stderr.getvalue(), "")  # No errors

    def test_style_option(self):
        """Test node style option."""
        sys.argv = ["phart", "--style", "round", str(self.test_text_file)]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        output = self.stdout.getvalue()
        self.assertIn("(A)", output)
        self.assertIn("(B)", output)
        self.assertEqual(self.stderr.getvalue(), "")

    def test_charset_unicode(self):
        """Test explicit unicode charset option."""
        sys.argv = ["phart", "--charset", "unicode", str(self.test_text_file)]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        output = self.stdout.getvalue()
        # Should find at least one unicode character
        self.assertTrue(any(ord(c) > 127 for c in output))
        self.assertEqual(self.stderr.getvalue(), "")

    def test_charset_ascii(self):
        """Test ASCII charset option."""
        sys.argv = ["phart", "--charset", "ascii", str(self.test_text_file)]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        output = self.stdout.getvalue()
        # All characters should be ASCII
        self.assertTrue(all(ord(c) < 128 for c in output))
        self.assertEqual(self.stderr.getvalue(), "")

    def test_legacy_ascii_flag(self):
        """Test that legacy --ascii flag still works."""
        sys.argv = ["phart", "--ascii", str(self.test_text_file)]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        output = self.stdout.getvalue()
        # All characters should be ASCII
        self.assertTrue(all(ord(c) < 128 for c in output))
        self.assertEqual(self.stderr.getvalue(), "")

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
        self.assertEqual(self.stderr.getvalue(), "")

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

    def test_python_with_main(self):
        """Test executing Python file with main() function."""
        sys.argv = ["phart", str(self.py_main_file)]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        output = self.stdout.getvalue()
        self.assertIn("A", output)
        self.assertIn("B", output)
        self.assertIn("C", output)
        self.assertEqual(self.stderr.getvalue(), "")

    def test_python_with_main_block(self):
        """Test executing Python file with __main__ block."""
        sys.argv = ["phart", str(self.py_block_file)]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        output = self.stdout.getvalue()
        self.assertIn("X", output)
        self.assertIn("Y", output)
        self.assertIn("Z", output)
        self.assertEqual(self.stderr.getvalue(), "")

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
        self.assertEqual(self.stderr.getvalue(), "")

    def test_python_missing_function(self):
        """Test error handling for missing function."""
        sys.argv = ["phart", str(self.py_custom_file), "--function", "nonexistent"]
        exit_code = main()
        self.assertEqual(exit_code, 1)
        self.assertIn("Error: Function 'nonexistent' not found", self.stderr.getvalue())
