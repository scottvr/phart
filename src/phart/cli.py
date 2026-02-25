"""Command line interface for PHART."""

import sys
import ast
import argparse
import importlib.util
from contextlib import nullcontext, redirect_stdout
from pathlib import Path
from typing import Optional, Any, ContextManager

from .renderer import ASCIIRenderer
from .styles import NodeStyle, LayoutOptions
from .charset import CharSet


COLOR_MODES = {"none", "source", "target", "path", "attr"}
LAYOUT_STRATEGIES = {
    "auto",
    "bfs",
    "bipartite",
    "btree",
    "circular",
    "planar",
    "kamada-kawai",
    "spring",
    "arf",
    "spiral",
    "shell",
    "random",
    "multipartite",
    "hierarchical",
    "vertical",
    "layered",
}

CLI_LAYOUT_FIELD_MAP = {
    "--style": {"node_style"},
    "--node-spacing": {"node_spacing"},
    "--layer-spacing": {"layer_spacing"},
    "--charset": {"use_ascii"},
    "--ascii": {"use_ascii"},
    "--binary-tree": {"binary_tree_layout"},
    "--btree": {"binary_tree_layout"},
    "--layout": {"layout_strategy"},
    "--layout-strategy": {"layout_strategy"},
    "--flow-direction": {"flow_direction"},
    "--flow": {"flow_direction"},
    "--bboxes": {"bboxes"},
    "--bbox": {"bboxes"},
    "--hpad": {"hpad"},
    "--vpad": {"vpad"},
    "--uniform": {"uniform"},
    "--size-to-widest": {"uniform"},
    "--edge-anchors": {"edge_anchor_mode"},
    "--labels": {"use_labels"},
    "--colors": {"ansi_colors", "edge_color_mode"},
    "--edge-color-rule": {"edge_color_rules"},
}


def _normalize_color_args(argv: list[str]) -> list[str]:
    """Normalize bare --colors usage to avoid optional-value positional ambiguity.

    Converts:
      --colors            -> --colors source
      --colors <input>    -> --colors source <input>  (when <input> is not a mode)
    Leaves explicit forms unchanged:
      --colors source
      --colors=target
    """
    normalized: list[str] = []
    i = 0
    while i < len(argv):
        token = argv[i]

        if token == "--":
            normalized.extend(argv[i:])
            break

        if token == "--colors":
            next_token = argv[i + 1] if i + 1 < len(argv) else None
            if (
                next_token is None
                or next_token.startswith("-")
                or next_token not in COLOR_MODES
            ):
                normalized.extend(["--colors", "source"])
                i += 1
                continue

        normalized.append(token)
        i += 1

    return normalized


def _fields_for_option_token(opt_name: str) -> set[str]:
    """Map an option token to layout fields, including long-option abbreviations."""
    if opt_name in CLI_LAYOUT_FIELD_MAP:
        return set(CLI_LAYOUT_FIELD_MAP[opt_name])

    if not opt_name.startswith("--"):
        return set()

    matches = [
        fields
        for key, fields in CLI_LAYOUT_FIELD_MAP.items()
        if key.startswith(opt_name)
    ]
    if not matches:
        return set()
    if len(matches) == 1:
        return set(matches[0])

    # If ambiguous but all matches map to the same fields, keep them.
    first = matches[0]
    if all(match == first for match in matches):
        return set(first)
    return set()


def _collect_explicit_layout_fields(
    argv: list[str], args: argparse.Namespace
) -> set[str]:
    explicit_fields: set[str] = set()
    for token in argv:
        if token == "--":
            break
        if not token.startswith("-"):
            continue
        opt_name = token.split("=", 1)[0]
        explicit_fields.update(_fields_for_option_token(opt_name))

    # layout=btree implies binary-tree semantics, even without explicit --binary-tree.
    if "layout_strategy" in explicit_fields and args.layout_strategy == "btree":
        explicit_fields.add("binary_tree_layout")

    return explicit_fields


def parse_args() -> tuple[argparse.Namespace, list[str], set[str], list[str]]:
    """Parse command line arguments."""
    raw_argv = sys.argv[1:]
    if "--" in raw_argv:
        sep_index = raw_argv.index("--")
        cli_raw_argv = raw_argv[:sep_index]
        module_argv = raw_argv[sep_index + 1 :]
    else:
        cli_raw_argv = raw_argv
        module_argv = []

    argv = _normalize_color_args(cli_raw_argv)

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
        default=None,
        help="Node style (default: square, or minimal when --bboxes is enabled)",
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
        "--btree",
        action="store_true",
        help="Enable binary tree layout (respects edge 'side' attributes)",
    )
    parser.add_argument(
        "--layout",
        "--layout-strategy",
        choices=sorted(LAYOUT_STRATEGIES),
        dest="layout_strategy",
        default="auto",
        help="Node positioning strategy (default: auto)",
    )
    parser.add_argument(
        "--flow-direction",
        "--flow",
        choices=["down", "up", "left", "right"],
        default="down",
        help="Layout flow direction: down (default, root at top), up (root at bottom), "
        "left (root at right), right (root at left)",
    )
    parser.add_argument(
        "--bboxes",
        action="store_true",
        help="Draw line-art boxes around nodes",
    )
    parser.add_argument(
        "--hpad",
        type=int,
        default=1,
        help="Horizontal padding inside node boxes (default: 1)",
    )
    parser.add_argument(
        "--vpad",
        type=int,
        default=0,
        help="Vertical padding inside node boxes (default: 0)",
    )
    parser.add_argument(
        "--uniform",
        "--size-to-widest",
        action="store_true",
        dest="uniform",
        help="Use widest node text as the width baseline for all node boxes",
    )
    parser.add_argument(
        "--edge-anchors",
        choices=["auto", "center", "ports"],
        default="auto",
        help=(
            "Edge anchor strategy: auto (default), center, or ports "
            "(distributed on box edges)"
        ),
    )
    parser.add_argument(
        "--labels",
        action="store_true",
        help="Use node labels (if present) for displayed node text",
    )
    parser.add_argument(
        "--colors",
        choices=sorted(COLOR_MODES),
        default="none",
        help="ANSI edge coloring mode: none (default), source, target, path, or attr",
    )
    parser.add_argument(
        "--edge-color-rule",
        action="append",
        default=[],
        metavar="RULE",
        help=(
            "Attribute-driven edge color rule for --colors attr. "
            "Format: <attribute>:<value>=<color>[,<value>=<color>...] "
            "(repeatable)"
        ),
    )
    args, unknown = parser.parse_known_args(argv)
    explicit_layout_fields = _collect_explicit_layout_fields(argv, args)
    return args, unknown, explicit_layout_fields, module_argv


def _normalize_attr_match_value(value: str) -> str:
    text = value.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {"'", '"'}:
        text = text[1:-1]
    return text.strip().lower()


def _parse_edge_color_rules(rule_specs: list[str]) -> dict[str, dict[str, str]]:
    parsed: dict[str, dict[str, str]] = {}
    for rule in rule_specs:
        text = str(rule).strip()
        if not text:
            continue

        if ":" not in text:
            raise ValueError(
                f"Invalid --edge-color-rule '{rule}'. Expected "
                "<attribute>:<value>=<color>[,<value>=<color>...]"
            )
        attr_name, mapping_text = text.split(":", 1)
        attr_key = attr_name.strip().lower()
        if not attr_key:
            raise ValueError(
                f"Invalid --edge-color-rule '{rule}': attribute name cannot be empty"
            )

        value_map = parsed.setdefault(attr_key, {})
        mapping_tokens = [token.strip() for token in mapping_text.split(",")]
        added = False
        for token in mapping_tokens:
            if not token:
                continue
            if "=" not in token:
                raise ValueError(
                    f"Invalid --edge-color-rule '{rule}'. Expected "
                    "<value>=<color> pairs after ':'."
                )

            raw_value, raw_color = token.split("=", 1)
            value_key = _normalize_attr_match_value(raw_value)
            color_text = raw_color.strip()
            if not value_key:
                raise ValueError(
                    f"Invalid --edge-color-rule '{rule}': value cannot be empty"
                )
            if not color_text:
                raise ValueError(
                    f"Invalid --edge-color-rule '{rule}': color cannot be empty"
                )
            value_map.setdefault(value_key, color_text)
            added = True

        if not added:
            raise ValueError(
                f"Invalid --edge-color-rule '{rule}': no <value>=<color> pairs found"
            )

    return parsed


def _load_python_module(file_path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("dynamic_module", file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load {file_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules["dynamic_module"] = module
    spec.loader.exec_module(module)
    return module


def create_layout_options(
    args: argparse.Namespace, explicit_layout_fields: Optional[set[str]] = None
) -> LayoutOptions:
    """Create LayoutOptions from CLI arguments."""
    node_style = NodeStyle[args.style.upper()] if args.style is not None else None
    color_mode = args.colors
    layout_strategy = args.layout_strategy.replace("-", "_")
    binary_tree_layout = args.binary_tree
    edge_color_rules = _parse_edge_color_rules(args.edge_color_rule)
    if edge_color_rules and color_mode != "attr":
        raise ValueError("--edge-color-rule requires --colors attr")
    use_ascii = args.charset in {CharSet.ASCII, CharSet.ANSI} or args.use_legacy_ascii
    if args.layout_strategy == "btree":
        binary_tree_layout = True
        layout_strategy = "auto"
    allow_ansi_in_ascii = args.charset == CharSet.ANSI and not args.use_legacy_ascii
    options = LayoutOptions(
        node_style=node_style,
        node_spacing=args.node_spacing,
        layer_spacing=args.layer_spacing,
        use_ascii=use_ascii,
        binary_tree_layout=binary_tree_layout,
        layout_strategy=layout_strategy,
        flow_direction=args.flow_direction,
        bboxes=args.bboxes,
        hpad=args.hpad,
        vpad=args.vpad,
        uniform=args.uniform,
        edge_anchor_mode=args.edge_anchors,
        use_labels=args.labels,
        ansi_colors=(color_mode != "none"),
        allow_ansi_in_ascii=allow_ansi_in_ascii,
        edge_color_mode="source" if color_mode == "none" else color_mode,
        edge_color_rules=edge_color_rules,
    )
    setattr(options, "_explicit_cli_fields", set(explicit_layout_fields or set()))
    return options


def _run_python_as_main(file_path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("__main__", file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load {file_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules["__main__"] = module  # match python's behavior more closely
    spec.loader.exec_module(module)  # executes exactly once
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
    args, unknown, explicit_layout_fields, module_argv = parse_args()

    try:
        if args.input.suffix == ".py":
            if unknown:
                print(
                    "It looks like you passed arguments intended for the script.\n"
                    "Use '--' to separate phart options from script options.\n\n"
                    f"Example:\n  phart {args.input} -- {' '.join(unknown)}",
                    file=sys.stderr,
                )
                return 2

            old_argv = sys.argv
            old_default_options = ASCIIRenderer.default_options
            sys.argv = [str(args.input)] + module_argv

            try:
                cli_options = create_layout_options(args, explicit_layout_fields)
                ASCIIRenderer.default_options = cli_options
                output_ctx: ContextManager[Any] = nullcontext()
                out_file = None
                if args.output:
                    out_file = args.output.open("w", encoding="utf-8")
                    output_ctx = redirect_stdout(out_file)

                try:
                    with output_ctx:
                        if args.function != "main":
                            module = _load_python_module(args.input)
                            try:
                                func = getattr(module, args.function)
                            except AttributeError:
                                print(
                                    f"Error: Function '{args.function}' not found in {args.input}",
                                    file=sys.stderr,
                                )
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
                    if out_file is not None:
                        out_file.close()

            finally:
                sys.argv = old_argv
                ASCIIRenderer.default_options = old_default_options

        else:
            if module_argv:
                print(
                    "Error: script arguments after '--' are only supported for .py input files",
                    file=sys.stderr,
                )
                return 2
            if unknown:
                print(
                    f"Error: unrecognized arguments: {' '.join(unknown)} (incorrect arg to option {''.join(sys.argv[:2][1:])} maybe?)",
                    file=sys.stderr,
                )
                return 2

            with open(args.input, "r", encoding="utf-8") as f:
                content = f.read()

            cli_options = create_layout_options(args, explicit_layout_fields)

            try:
                if content.strip().startswith("<?xml") or content.strip().startswith(
                    "<graphml"
                ):
                    renderer = ASCIIRenderer.from_graphml(
                        str(args.input), options=cli_options
                    )
                else:
                    renderer = ASCIIRenderer.from_dot(content, options=cli_options)
            except Exception as parse_error:
                print(
                    f"Error: Could not parse file as GraphML or DOT format: {parse_error}",
                    file=sys.stderr,
                )
                return 1

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
