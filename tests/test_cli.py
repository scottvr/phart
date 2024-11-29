"""Tests for PHART CLI functionality."""

import unittest
from pathlib import Path
import tempfile
from phart.cli import main
import sys
from io import StringIO


class TestCLI(unittest.TestCase):
    def setUp(self):
        # Create a temporary DOT file
        self.dot_content = """
        digraph {
            A -> B;
            B -> C;
        }
        """
        self.temp_dir = tempfile.mkdtemp()
        self.dot_file = Path(self.temp_dir) / "test.dot"
        self.dot_file.write_text(self.dot_content)

        # Save original stdout/stderr
        self.old_stdout = sys.stdout
        self.old_stderr = sys.stderr
        self.stdout = StringIO()
        self.stderr = StringIO()
        sys.stdout = self.stdout
        sys.stderr = self.stderr

    def tearDown(self):
        # Restore stdout/stderr
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr

        # Clean up temp files
        self.dot_file.unlink()
        Path(self.temp_dir).rmdir()

    def test_basic_rendering(self):
        """Test basic DOT file rendering."""
        sys.argv = ["phart", str(self.dot_file)]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        output = self.stdout.getvalue()
        self.assertIn("A", output)
        self.assertIn("B", output)
        self.assertIn("C", output)

    def test_style_option(self):
        """Test node style option."""
        sys.argv = ["phart", "--style", "round", str(self.dot_file)]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        output = self.stdout.getvalue()
        self.assertIn("(A)", output)
        self.assertIn("(B)", output)

    def test_ascii_option(self):
        """Test ASCII-only output."""
        sys.argv = ["phart", "--ascii", str(self.dot_file)]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        output = self.stdout.getvalue()
        # Should only contain ASCII characters
        self.assertTrue(all(ord(c) < 128 for c in output))

    def test_invalid_file(self):
        """Test handling of invalid file."""
        sys.argv = ["phart", "nonexistent.dot"]
        exit_code = main()
        self.assertEqual(exit_code, 1)
        self.assertIn("Error", self.stderr.getvalue())

    def test_invalid_format(self):
        """Test handling of unsupported file format."""
        bad_file = Path(self.temp_dir) / "test.xyz"
        bad_file.touch()
        sys.argv = ["phart", str(bad_file)]
        exit_code = main()
        self.assertEqual(exit_code, 1)
        self.assertIn("Unsupported file format", self.stderr.getvalue())
        bad_file.unlink()
