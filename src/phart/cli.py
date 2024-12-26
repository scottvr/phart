"""Command line interface for PHART."""

import sys
import argparse
from pathlib import Path
from typing import Optional

from .renderer import ASCIIRenderer
from .svg import SVGRenderer
from .styles import NodeStyle


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="PHART: Python Hierarchical ASCII Rendering Tool"
    )
    parser.add_argument(
        "input", type=Path, help="Input file (.dot, .graphml, or .svg format)"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Output file (if not specified, prints to stdout)",
    )
    parser.add_argument(
        "--style",
        choices=[s.name.lower() for s in NodeStyle],
        default="square",
        help="Node style (default: square)",
    )
    parser.add_argument(
        "--ascii",
        action="store_true",
        help="Force ASCII output (no Unicode box characters)",
    )
    parser.add_argument(
        "--node-spacing",
        type=int,
        default=4,
        help="Horizontal space between nodes (default: 4)",
    )
    parser.add_argument(
        "--layer-spacing",
        type=int,
        default=2,
        help="Vertical space between layers (default: 2)",
    )
    parser.add_argument(
        "--preserve-svg-style",
        action="store_true",
        help="Preserve original SVG node styles when converting from SVG",
    )
    return parser.parse_args()


def main() -> Optional[int]:
    """CLI entry point for PHART."""
    args = parse_args()

    try:
        # Read input file content
        with open(args.input, "r", encoding="utf-8") as f:
            content = f.read()

        # Determine file type and create appropriate renderer
        file_suffix = args.input.suffix.lower()
        if file_suffix == ".svg":
            renderer = SVGRenderer.from_svg(
                content,
                node_spacing=args.node_spacing,
                layer_spacing=args.layer_spacing,
                use_ascii=args.ascii,
                # Only override SVG styles if not preserving
                node_style=None
                if args.preserve_svg_style
                else NodeStyle[args.style.upper()],
            )
        else:
            # Try to determine format from content for non-SVG files
            try:
                if content.strip().startswith("<?xml") or content.strip().startswith(
                    "<graphml"
                ):
                    renderer = ASCIIRenderer.from_graphml(str(args.input))
                else:
                    # Assume DOT format if not GraphML
                    renderer = ASCIIRenderer.from_dot(content)
            except Exception as format_error:
                print(
                    f"Error: Could not parse file as GraphML or DOT format: {format_error}",
                    file=sys.stderr,
                )
                return 1

            # Apply style options for non-SVG files
            renderer.options.node_style = NodeStyle[args.style.upper()]
            renderer.options.use_ascii = args.ascii
            renderer.options.node_spacing = args.node_spacing
            renderer.options.layer_spacing = args.layer_spacing

        # Handle output
        if args.output:
            renderer.write_to_file(str(args.output))
        else:
            print(renderer.render())
        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
