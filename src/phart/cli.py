"""Command line interface for PHART."""

import sys
import argparse
from pathlib import Path
from typing import Optional

from phart import __version__ as version
from phart.renderer import ASCIIRenderer
from .charset import CharSet
from .core.contracts import OutputRenderConfig, RendererOutputConfig
from .io.input import load_renderer_from_file, run_python_source
from .io.output import render_captured_text, render_renderer_output
from .styles import LayoutOptions, NodeStyle

COLOR_MODES = {"none", "source", "target", "path", "attr"}
OUTPUT_FORMATS = {"text", "ditaa", "ditaa-puml", "svg", "html", "latex-markdown", "mmd"}
LAYOUT_STRATEGIES = {
    "auto",
    "bfs",
    "bipartite",
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
    "--charset": {"use_ascii", "allow_ansi_in_ascii"},
    "--ascii": {"use_ascii", "allow_ansi_in_ascii"},
    "--binary-tree": {"binary_tree_layout"},
    "--layout": {"layout_strategy"},
    "--layout-strategy": {"layout_strategy"},
    "--node-order": {"node_order_mode"},
    "--node-order-attr": {"node_order_attr"},
    "--node-order-reverse": {"node_order_reverse"},
    "--flow-direction": {"flow_direction"},
    "--flow": {"flow_direction"},
    "--bboxes": {"bboxes"},
    "--bbox": {"bboxes"},
    "--hpad": {"hpad"},
    "--vpad": {"vpad"},
    "--uniform": {"uniform"},
    "--size-to-widest": {"uniform"},
    "--edge-anchors": {"edge_anchor_mode"},
    "--shared-ports": {"shared_ports_mode"},
    "--bidirectional-mode": {"bidirectional_mode"},
    "--labels": {"use_labels"},
    "--colors": {"ansi_colors", "edge_color_mode"},
    "--no-color-nodes": {"color_nodes"},
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
        "--version",
        "-v",
        action="version",
        version=version,
    )
    parser.add_argument(
        "--output-format",
        choices=sorted(OUTPUT_FORMATS),
        default="text",
        help=(
            "Output format: text (default), ditaa, ditaa-puml, "
            "svg, html, mmmd, or latex-markdown"
        ),
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
        "--node-order",
        choices=[
            "layout-default",
            "preserve",
            "alpha",
            "natural",
            "numeric",
        ],
        default="layout-default",
        help=(
            "Node ordering policy: layout-default (default), preserve, alpha, "
            "natural, or numeric"
        ),
    )
    parser.add_argument(
        "--node-order-attr",
        type=str,
        default=None,
        help="Optional node attribute name to use as the ordering key",
    )
    parser.add_argument(
        "--node-order-reverse",
        action="store_true",
        help="The result of the sorting method used by the layout strategy will be reversed",
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
        "--shared-ports",
        choices=["any", "minimize", "none"],
        default="any",
        help=(
            "Terminal port sharing policy: any (default), minimize "
            "(prefer unused points on the same face), or none "
            "(avoid sharing until the node has no free terminal slots)"
        ),
    )
    parser.add_argument(
        "--bidirectional-mode",
        choices=["coalesce", "separate"],
        default="coalesce",
        help=(
            "How to render reciprocal directed edges: coalesce (default) draws "
            "one shared route with arrows at both ends; separate draws each "
            "direction independently"
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
        "--no-color-nodes", action="store_true", help="Color edges only, not nodes"
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
    parser.add_argument(
        "--svg-cell-size",
        type=int,
        default=12,
        help="Cell size in pixels for SVG output (default: 12)",
    )
    parser.add_argument(
        "--svg-font-family",
        type=str,
        default="monospace",
        help="Font family for SVG/HTML output (default: monospace)",
    )
    parser.add_argument(
        "--svg-text-mode",
        choices=["text", "path"],
        default="text",
        help="Render SVG characters as <text> (default) or glyph paths",
    )
    parser.add_argument(
        "--svg-font-path",
        type=str,
        default=None,
        help="Font file path required when --svg-text-mode path is used",
    )
    parser.add_argument(
        "--svg-fg",
        type=str,
        default="#111111",
        help="Foreground color for SVG/HTML/LaTeX output",
    )
    parser.add_argument(
        "--svg-bg",
        type=str,
        default="#ffffff",
        help="Background color for SVG/HTML output",
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


def create_layout_options(
    args: argparse.Namespace, explicit_layout_fields: Optional[set[str]] = None
) -> LayoutOptions:
    """Create LayoutOptions from CLI arguments."""
    node_style = NodeStyle[args.style.upper()] if args.style is not None else None
    color_mode = args.colors
    layout_strategy = args.layout_strategy.replace("-", "_")
    binary_tree_layout = args.binary_tree
    edge_color_rules = _parse_edge_color_rules(args.edge_color_rule)
    color_nodes = not args.no_color_nodes
    if color_mode == "attr" and not edge_color_rules:
        raise ValueError("--colors attr requires --edge-color-rule")
    use_ascii = args.charset in {CharSet.ASCII, CharSet.ANSI} or args.use_legacy_ascii
    allow_ansi_in_ascii = args.charset == CharSet.ANSI and not args.use_legacy_ascii
    options = LayoutOptions(
        node_style=node_style,
        node_spacing=args.node_spacing,
        layer_spacing=args.layer_spacing,
        use_ascii=use_ascii,
        binary_tree_layout=binary_tree_layout,
        layout_strategy=layout_strategy,
        node_order_mode=args.node_order,
        node_order_attr=args.node_order_attr,
        node_order_reverse=args.node_order_reverse,
        flow_direction=args.flow_direction,
        bboxes=args.bboxes,
        hpad=args.hpad,
        vpad=args.vpad,
        uniform=args.uniform,
        edge_anchor_mode=args.edge_anchors,
        shared_ports_mode=args.shared_ports,
        bidirectional_mode=args.bidirectional_mode,
        use_labels=args.labels,
        ansi_colors=(color_mode != "none"),
        allow_ansi_in_ascii=allow_ansi_in_ascii,
        edge_color_mode="source" if color_mode == "none" else color_mode,
        edge_color_rules=edge_color_rules,
        color_nodes=color_nodes,
    )
    setattr(options, "_explicit_cli_fields", set(explicit_layout_fields or set()))
    return options


def main() -> Optional[int]:
    """CLI entry point for PHART."""
    args, unknown, explicit_layout_fields, module_argv = parse_args()

    try:
        output_render_config = OutputRenderConfig(
            output_format=args.output_format,
            svg_cell_size=args.svg_cell_size,
            svg_font_family=args.svg_font_family,
            svg_text_mode=args.svg_text_mode,
            svg_font_path=args.svg_font_path,
            svg_fg=args.svg_fg,
            svg_bg=args.svg_bg,
        )
        renderer_output_config = RendererOutputConfig(
            output_format=args.output_format,
            svg_cell_size=args.svg_cell_size,
            svg_font_family=args.svg_font_family,
            svg_text_mode=args.svg_text_mode,
            svg_font_path=args.svg_font_path,
            svg_fg=args.svg_fg,
            svg_bg=args.svg_bg,
        )

        if args.input.suffix == ".py":
            if unknown:
                print(
                    "It looks like you passed arguments intended for the script.\n"
                    "Use '--' to separate phart options from script options.\n\n"
                    f"Example:\n  phart {args.input} -- {' '.join(unknown)}",
                    file=sys.stderr,
                )
                return 2

            cli_options = create_layout_options(args, explicit_layout_fields)
            raw_output = run_python_source(
                args.input,
                function_name=args.function,
                module_argv=module_argv,
                options=cli_options,
            )
            rendered_output = render_captured_text(
                raw_output, config=output_render_config
            )
            if args.output:
                args.output.write_text(rendered_output, encoding="utf-8")
            else:
                sys.stdout.write(rendered_output)
            return 0

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

            cli_options = create_layout_options(args, explicit_layout_fields)
            renderer = load_renderer_from_file(args.input, options=cli_options)
            rendered_output = render_renderer_output(
                renderer, config=renderer_output_config
            )
            if args.output:
                args.output.write_text(rendered_output, encoding="utf-8")
            else:
                sys.stdout.write(rendered_output)
            return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
