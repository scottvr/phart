"""Command line interface for PHART."""

import sys
import ast
import io
import re
import argparse
import importlib.util
from contextlib import redirect_stdout
from html import escape as html_escape
from pathlib import Path
from typing import Optional, Any, ContextManager

from .renderer import ASCIIRenderer, ANSI_ESCAPE_RE, UNICODE_DITAA_MAP
from .styles import NodeStyle, LayoutOptions
from .charset import CharSet
from phart import __version__ as version

COLOR_MODES = {"none", "source", "target", "path", "attr"}
OUTPUT_FORMATS = {"text", "ditaa", "ditaa-puml", "svg", "html"}
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
        "input",
        type=Path,
        help="Input file (.dot, .graphml, .puml/.plantuml/.uml, or .py format)",
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
        help="Output format: text (default), ditaa, ditaa-puml, svg, or html",
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
        help="Cell size in px for SVG output (default: 12)",
    )
    parser.add_argument(
        "--svg-font-family",
        type=str,
        default="monospace",
        help="Font family for SVG/HTML output",
    )
    parser.add_argument(
        "--svg-text-mode",
        choices=["text", "path"],
        default="text",
        help="SVG text rendering mode: text (default) or path (glyph outlines)",
    )
    parser.add_argument(
        "--svg-font-path",
        type=str,
        default=None,
        help="Font file path for --svg-text-mode path (TTF/OTF)",
    )
    parser.add_argument(
        "--svg-fg",
        type=str,
        default="#111111",
        help="Foreground color for SVG/HTML output",
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
    color_nodes = not args.no_color_nodes
    if color_mode == "attr" and not edge_color_rules:
        raise ValueError("--colors attr requires --edge-color-rule")
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
        color_nodes=color_nodes,
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


_ANSI_TOKEN_RE = re.compile(r"\x1b\[[0-9;]*m|.", re.DOTALL)


def _rows_and_colors_from_ansi_text(
    text: str,
) -> tuple[list[str], list[list[Optional[str]]]]:
    rows: list[list[str]] = []
    color_rows: list[list[Optional[str]]] = []
    for line in text.splitlines():
        row_chars: list[str] = []
        row_colors: list[Optional[str]] = []
        active_ansi: Optional[str] = None
        for token in _ANSI_TOKEN_RE.findall(line):
            if token.startswith("\x1b["):
                active_ansi = None if token == "\x1b[0m" else token
                continue
            row_chars.append(token)
            row_colors.append(active_ansi)
        rows.append(row_chars)
        color_rows.append(row_colors)

    width = max((len(r) for r in rows), default=0)
    normalized_rows = ["".join(r).ljust(width) for r in rows]
    normalized_colors: list[list[Optional[str]]] = []
    for color_row in color_rows:
        normalized_colors.append(color_row + [None] * (width - len(color_row)))
    return normalized_rows, normalized_colors


def _render_python_output(args: argparse.Namespace, raw_text: str) -> str:
    if args.output_format == "text":
        return raw_text

    if args.output_format in {"ditaa", "ditaa-puml"}:
        text = ANSI_ESCAPE_RE.sub("", raw_text)
        text = "".join(UNICODE_DITAA_MAP.get(ch, ch) for ch in text)
        lines = [line.rstrip() for line in text.splitlines()]
        while lines and lines[-1] == "":
            lines.pop()
        body = "\n".join(lines)
        if args.output_format == "ditaa-puml":
            return f"@startditaa\n{body}\n@endditaa\n"
        return body + ("\n" if body else "")

    rows, color_canvas = _rows_and_colors_from_ansi_text(raw_text)
    height = len(rows)
    width = max((len(row) for row in rows), default=0)

    if args.output_format == "svg":
        cell_px = args.svg_cell_size
        svg_w = width * cell_px
        svg_h = height * cell_px
        text_x = cell_px / 2
        text_y0 = cell_px * 0.8
        lines = []
        lines.append('<?xml version="1.0" encoding="UTF-8"?>')
        lines.append(
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_w}" height="{svg_h}" '
            f'viewBox="0 0 {svg_w} {svg_h}">'
        )
        lines.append(
            f'  <rect x="0" y="0" width="{svg_w}" height="{svg_h}" fill="{html_escape(args.svg_bg)}" />'
        )
        lines.append(
            "  <g "
            f'font-family="{html_escape(args.svg_font_family)}" '
            f'font-size="{cell_px}" fill="{html_escape(args.svg_fg)}" '
            'text-anchor="middle" xml:space="preserve">'
        )
        for y, row in enumerate(rows):
            for x, ch in enumerate(row):
                if ch == " ":
                    continue
                cx = text_x + x * cell_px
                cy = text_y0 + y * cell_px
                fill = args.svg_fg
                if y < len(color_canvas) and x < len(color_canvas[y]):
                    ansi = color_canvas[y][x]
                    parsed = ASCIIRenderer._ansi_to_hex(ansi) if ansi else None
                    if parsed:
                        fill = parsed
                lines.append(
                    f'    <text x="{cx:.2f}" y="{cy:.2f}" fill="{html_escape(fill)}">{html_escape(ch)}</text>'
                )
        lines.append("  </g>")
        lines.append("</svg>")
        return "\n".join(lines) + "\n"

    if args.output_format == "html":
        html_lines: list[str] = []
        html_lines.append("<!DOCTYPE html>")
        html_lines.append('<html><head><meta charset="utf-8"></head><body>')
        html_lines.append(
            "<pre style="
            f'"background:{html_escape(args.svg_bg)};'
            f"color:{html_escape(args.svg_fg)};"
            f"font-family:{html_escape(args.svg_font_family)};"
            'line-height:1.1;">'
        )
        for y, row in enumerate(rows):
            current_color: Optional[str] = None
            for x, ch in enumerate(row):
                target_color = args.svg_fg
                if y < len(color_canvas) and x < len(color_canvas[y]):
                    ansi = color_canvas[y][x]
                    parsed = ASCIIRenderer._ansi_to_hex(ansi) if ansi else None
                    if parsed:
                        target_color = parsed
                if target_color != current_color:
                    if current_color is not None:
                        html_lines.append("</span>")
                    if target_color != args.svg_fg:
                        html_lines.append(
                            f'<span style="color:{html_escape(target_color)}">'
                        )
                    else:
                        html_lines.append("<span>")
                    current_color = target_color
                html_lines.append(html_escape(ch))
            if current_color is not None:
                html_lines.append("</span>")
            html_lines.append("\n")
        html_lines.append("</pre></body></html>\n")
        return "".join(html_lines)

    raise ValueError(f"Unsupported output format '{args.output_format}'")


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
                capture = io.StringIO()
                output_ctx: ContextManager[Any] = redirect_stdout(capture)

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
                    elif _module_defines_function(args.input, "main"):
                        module = _load_python_module(args.input)
                        module.main()
                    else:
                        _run_python_as_main(args.input)

                rendered = _render_python_output(args, capture.getvalue())
                if args.output:
                    args.output.write_text(rendered, encoding="utf-8")
                else:
                    print(rendered, end="")
                return 0

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
                suffix = args.input.suffix.lower()
                if suffix in {".puml", ".plantuml", ".uml"}:
                    renderer = ASCIIRenderer.from_plantuml(content, options=cli_options)
                elif content.strip().startswith("<?xml") or content.strip().startswith(
                    "<graphml"
                ):
                    renderer = ASCIIRenderer.from_graphml(
                        str(args.input), options=cli_options
                    )
                else:
                    renderer = ASCIIRenderer.from_dot(content, options=cli_options)
            except Exception as parse_error:
                print(
                    "Error: Could not parse file as PlantUML, GraphML, or DOT format: "
                    f"{parse_error}",
                    file=sys.stderr,
                )
                return 1

            if args.output_format == "text":
                rendered = renderer.render()
            elif args.output_format == "ditaa":
                rendered = renderer.render_ditaa(wrap_plantuml=False)
            elif args.output_format == "ditaa-puml":
                rendered = renderer.render_ditaa(wrap_plantuml=True)
            elif args.output_format == "svg":
                rendered = renderer.render_svg(
                    cell_px=args.svg_cell_size,
                    font_family=args.svg_font_family,
                    text_mode=args.svg_text_mode,
                    font_path=args.svg_font_path,
                    fg_color=args.svg_fg,
                    bg_color=args.svg_bg,
                )
            elif args.output_format == "html":
                rendered = renderer.render_html(
                    fg_color=args.svg_fg,
                    bg_color=args.svg_bg,
                    font_family=args.svg_font_family,
                )
            else:
                print(
                    f"Error: Unsupported output format '{args.output_format}'",
                    file=sys.stderr,
                )
                return 2

            if args.output:
                args.output.write_text(rendered, encoding="utf-8")
            else:
                print(rendered, end="")
            return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return None


if __name__ == "__main__":
    sys.exit(main())
