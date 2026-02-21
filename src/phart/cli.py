"""Command line interface for PHART."""
# src path: src/phart/cli.py

import sys
import argparse
import importlib.util
from pathlib import Path
from typing import Optional, Any

from .renderer import ASCIIRenderer
from .styles import NodeStyle, LayoutOptions
from .charset import CharSet


def parse_args() -> argparse.Namespace:
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

    return parser.parse_args()


def load_python_module(file_path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("dynamic_module", file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load {file_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules["dynamic_module"] = module
    spec.loader.exec_module(module)
    return module


def merge_layout_options(
    base: LayoutOptions, overrides: LayoutOptions
) -> LayoutOptions:
    from dataclasses import asdict, fields
    
    base_dict = asdict(base)
    override_dict = asdict(overrides)
    merged_dict = {}
    
    # Define which fields are "rendering" vs "semantic"
    rendering_fields = {'use_ascii', 'node_style', 'node_spacing', 'layer_spacing', 
                       'left_padding', 'right_padding', 'margin'}
    
    for field in fields(LayoutOptions):
        field_name = field.name
        if field_name == 'instance_id':
            continue
        
        override_val = override_dict.get(field_name)
        base_val = base_dict.get(field_name)
        
        # For rendering fields: CLI (override) takes precedence if not None
        if field_name in rendering_fields:
            merged_dict[field_name] = override_val if override_val is not None else base_val
        # For semantic fields: User (base) takes precedence if not None
        else:
            merged_dict[field_name] = base_val if base_val is not None else override_val
    
    # Special handling for custom_decorators - merge dicts
    if base.custom_decorators and overrides.custom_decorators:
        merged_dict['custom_decorators'] = {**base.custom_decorators, **overrides.custom_decorators}
    elif base.custom_decorators:
        merged_dict['custom_decorators'] = base.custom_decorators.copy()
    elif overrides.custom_decorators:
        merged_dict['custom_decorators'] = overrides.custom_decorators.copy()
    
    return LayoutOptions(**merged_dict)


def create_layout_options(args: argparse.Namespace) -> LayoutOptions:
    """Create LayoutOptions from CLI arguments."""
    return LayoutOptions(
        node_style=NodeStyle[args.style.upper()],
        node_spacing=args.node_spacing,
        layer_spacing=args.layer_spacing,
        use_ascii=(args.charset == CharSet.ASCII or args.use_legacy_ascii),
        binary_tree_layout=args.binary_tree,
    )


def main() -> Optional[int]:
    args = parse_args()

    try:
        if args.input.suffix == ".py":
            module = load_python_module(args.input)

            cli_options = create_layout_options(args)

            # Monkey-patch ASCIIRenderer.__init__ to automatically merge CLI options
            original_init = ASCIIRenderer.__init__
            
            def merged_init(self, graph, **kwargs):
                """Wrapper that automatically merges explicit options with CLI options."""
                if 'options' in kwargs and kwargs['options'] is not None:
                    user_options = kwargs['options']
                    kwargs['options'] = merge_layout_options(user_options, cli_options)
                else:
                    # No explicit options - set default_options so it gets used
                    if not hasattr(ASCIIRenderer, 'default_options') or ASCIIRenderer.default_options is None:
                        ASCIIRenderer.default_options = cli_options
                
                # Call original __init__ with potentially merged options
                original_init(self, graph, **kwargs)
            
            # Replace __init__ method for the duration of script execution
            ASCIIRenderer.__init__ = merged_init
            ASCIIRenderer.default_options = cli_options

            try:
                if args.function != "main":
                    func = getattr(module, args.function)
                    func()
                else:
                    if hasattr(module, "main"):
                        module.main()
                    else:
                        original_name = module.__name__
                        module.__name__ = "__main__"

                        spec = importlib.util.spec_from_file_location(
                            "__main__", args.input
                        )
                        if spec is None or spec.loader is None:
                            raise ImportError(f"Could not load {args.input}")

                        spec.loader.exec_module(module)
                        module.__name__ = original_name

            except AttributeError:
                if args.function != "main":
                    print(
                        f"Error: Function '{args.function}' not found in {args.input}",
                        file=sys.stderr,
                    )
                print(
                    f"Error: No main() function or __main__ block found in {args.input}",
                    file=sys.stderr,
                )
                return 1

        else:
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
            renderer.options.use_ascii = args.ascii
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


if __name__ == "__main__":
    sys.exit(main())
