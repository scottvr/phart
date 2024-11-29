"""Command line interface for PHART."""

import sys
import argparse
from pathlib import Path
from typing import Optional

from .renderer import ASCIIRenderer
from .styles import NodeStyle


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="PHART: Python Hierarchical ASCII Rendering Tool"
    )
    parser.add_argument("input", type=Path, help="Input file (.dot format)")
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
    return parser.parse_args()


def main() -> Optional[int]:
    """CLI entry point for PHART."""
    args = parse_args()

    try:
        if args.input.suffix.lower() == ".dot":
            with open(args.input, "r", encoding="utf-8") as f:
                dot_content = f.read()
            renderer = ASCIIRenderer.from_dot(
                dot_content,
                node_style=NodeStyle[args.style.upper()],
                use_ascii=args.ascii,
                node_spacing=args.node_spacing,
                layer_spacing=args.layer_spacing,
            )
            print(renderer.render())
            return 0
        else:
            print(
                f"Error: Unsupported file format: {args.input.suffix}",
                file=sys.stderr,
            )
            return 1

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
