"""Tests for PHART CLI functionality."""

import unittest
from pathlib import Path
import tempfile
from phart.cli import main
import sys
from io import StringIO


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

    def test_ascii_option(self):
        """Test ASCII-only output."""
        sys.argv = ["phart", "--ascii", str(self.test_text_file)]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        output = self.stdout.getvalue()
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
