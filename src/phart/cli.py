"""Command line interface for PHART."""
# src path: src/phart/cli.py

import sys
import ast
import argparse
import importlib.util
from pathlib import Path
from typing import Optional, Any

from .renderer import ASCIIRenderer
from .styles import NodeStyle, LayoutOptions
from .charset import CharSet

def parse_args() -> tuple[argparse.Namespace, list[str]]:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="PHART: Python Hierarchical ASCII Rendering Tool"
    )
    parser.add_argument(
        "input", type=Path, help="Input file (.dot, .graphml, or .py format)"
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
        "--node-spacing",
        type=int,
        default=4,
        help="Horizontal space between nodes (default: 4)",
    )
    parser.add_argument(
        "--layer-spacing",
        type=int,
        default=3,
        help="Vertical space between layers (default: 3)",
    )
    parser.add_argument(
        "--charset",
        type=CharSet,
        choices=list(CharSet),
        default=CharSet.UNICODE,
        help="Character set to use for rendering (default: unicode)",
    )
    # Maintain backwards compatibility
    parser.add_argument(
        "--ascii",
        action="store_true",
        help="Force ASCII output (deprecated, use --charset ascii instead)",
        dest="use_legacy_ascii",
    )
    parser.add_argument(
        "--function",
        "-f",
        type=str,
        help="Function to call in Python file (default: main)",
        default="main",
    )
    parser.add_argument(
        "--binary-tree",
        action="store_true",
        help="Enable binary tree layout (respects edge 'side' attributes)",
    )
    parser.add_argument(
        "--flow-direction",
        "--flow",
        choices=["down", "up", "left", "right"],
        default="down",
        help="Layout flow direction: down (default, root at top), up (root at bottom), "
             "left (root at right), right (root at left)",
    )
    args, unknown = parser.parse_known_args()
    return args, unknown


def _load_python_module(file_path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("dynamic_module", file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load {file_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules["dynamic_module"] = module
    spec.loader.exec_module(module)
    return module


def create_layout_options(args: argparse.Namespace) -> LayoutOptions:
    """Create LayoutOptions from CLI arguments."""
    return LayoutOptions(
        node_style=NodeStyle[args.style.upper()],
        node_spacing=args.node_spacing,
        layer_spacing=args.layer_spacing,
        use_ascii=(args.charset == CharSet.ASCII or args.use_legacy_ascii),
        binary_tree_layout=args.binary_tree,
        flow_direction=args.flow_direction,
    )

def _run_python_as_main(file_path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("__main__", file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load {file_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules["__main__"] = module  # match python's behavior more closely
    spec.loader.exec_module(module)   # executes exactly once
    return module


def _module_defines_function(file_path: Path, function_name: str) -> bool:
    """Return True if file defines a top-level function with the given name."""
    source = file_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(file_path))
    return any(
        isinstance(node, ast.FunctionDef) and node.name == function_name
        for node in tree.body
    )

def main() -> Optional[int]:
    """CLI entry point for PHART."""
    args, unknown = parse_args()
    has_script_separator = "--" in sys.argv[1:]
    module_argv = unknown if has_script_separator else []

    try:
        if args.input.suffix == ".py":
            if unknown and not has_script_separator:
                print(
                    "It looks like you passed arguments intended for the script.\n"
                    "Use '--' to separate phart options from script options.\n\n"
                    f"Example:\n  phart {args.input} -- {' '.join(unknown)}",
                    file=sys.stderr,
                )
                return 2

            old_argv = sys.argv
            sys.argv = [str(args.input)] + module_argv

            try:
                cli_options = create_layout_options(args)
                ASCIIRenderer.default_options = cli_options

                if args.function != "main":
                    module = _load_python_module(args.input)
                    try:
                        func = getattr(module, args.function)
                    except AttributeError:
                        print( f"Error: Function '{args.function}' not found in {args.input}", file=sys.stderr)
                        return 1
                    func()
                    return 0

                if _module_defines_function(args.input, "main"):
                    module = _load_python_module(args.input)
                    module.main()
                else:
                    _run_python_as_main(args.input)
                return 0
       
            finally:
                sys.argv = old_argv

        else:
            if unknown:
                print(
                    f"Error: unrecognized arguments: {' '.join(unknown)}",
                    file=sys.stderr,
                )
                return 2

            with open(args.input, "r", encoding="utf-8") as f:
                content = f.read()

            try:
                if content.strip().startswith("<?xml") or content.strip().startswith(
                    "<graphml"
                ):
                    renderer = ASCIIRenderer.from_graphml(str(args.input))
                else:
                    renderer = ASCIIRenderer.from_dot(content)
            except Exception as format_error:
                print(
                    f"Error: Could not parse file as GraphML or DOT format: {format_error}",
                    file=sys.stderr,
                )
                return 1

            renderer.options.node_style = NodeStyle[args.style.upper()]
            # Prefer explicit charset if specified, fall back to legacy flag if used
            use_ascii = args.charset == CharSet.ASCII or args.use_legacy_ascii
            renderer.options.use_ascii = use_ascii
            renderer.options.node_spacing = args.node_spacing
            renderer.options.layer_spacing = args.layer_spacing

            if args.output:
                renderer.write_to_file(str(args.output))
            else:
                print(renderer.render())
            return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return None

if __name__ == "__main__":
    sys.exit(main())
