"""Command line interface for PHART."""

import sys
import argparse
import json
import re
import shutil
from pathlib import Path
from typing import Optional, Any

from phart import __version__ as version
from phart.renderer import ASCIIRenderer
from .charset import CharSet
from .core.contracts import OutputRenderConfig, RendererOutputConfig
from .io.input import load_renderer_from_file, run_python_source
from .io.output import render_captured_text, render_renderer_output
from .io.output.pagination import describe_pages, paginate_text
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
    "--constrained": {"constrained"},
    "--node-order": {"node_order_mode"},
    "--node-order-attr": {"node_order_attr"},
    "--node-order-reverse": {"node_order_reverse"},
    "--flow-direction": {"flow_direction"},
    "--flow": {"flow_direction"},
    "--target-canvas-width": {"target_canvas_width"},
    "--target-canvas-height": {"target_canvas_height"},
    "--partition-overlap": {"partition_overlap"},
    "--partition-affinity-strength": {"partition_affinity_strength"},
    "--cross-partition-edge-style": {"cross_partition_edge_style"},
    "--connector-compaction": {"connector_compaction"},
    "--partition-order": {"partition_order"},
    "--panel-headers": {"panel_header_mode"},
    "--connector-ref": {"connector_ref_mode"},
    "--bboxes": {"bboxes"},
    "--bbox": {"bboxes"},
    "--hpad": {"hpad"},
    "--vpad": {"vpad"},
    "--uniform": {"uniform"},
    "--size-to-widest": {"uniform"},
    "--edge-anchors": {"edge_anchor_mode"},
    "--shared-ports": {"shared_ports_mode"},
    "--bidirectional-mode": {"bidirectional_mode"},
    "--labels": {"use_labels", "node_label_attr", "edge_label_attr"},
    "--node-labels": {"node_label_attr"},
    "--edge-labels": {"edge_label_attr"},
    "--node-label-lines": {"node_label_lines"},
    "--node-label-sep": {"node_label_sep"},
    "--node-label-max-lines": {"node_label_max_lines"},
    "--bbox-multiline-labels": {"bbox_multiline_labels"},
    "--colors": {"ansi_colors", "edge_color_mode"},
    "--no-color-nodes": {"color_nodes"},
    "--edge-glyph-preset": {"edge_glyph_preset"},
    "--edge-arrow-style": {"edge_arrow_style"},
    "--edge-color-rule": {"edge_color_rules"},
    "--style-rule": {"style_rules"},
    "--style-rules-file": {"style_rules"},
    "--whitespace": {"whitespace_mode"},
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


def _normalize_label_args(argv: list[str]) -> list[str]:
    """Normalize bare --node-labels/--edge-labels usage.

    Converts:
      --node-labels                 -> --node-labels label
      --node-labels <input>         -> --node-labels label <input>
      --edge-labels                 -> --edge-labels label
      --edge-labels <input>         -> --edge-labels label <input>

    Ambiguous non-option tokens are treated as the positional input when there is no
    other positional token later in argv.
    """
    normalized: list[str] = []
    i = 0
    label_flags = {"--node-labels", "--edge-labels"}
    while i < len(argv):
        token = argv[i]

        if token == "--":
            normalized.extend(argv[i:])
            break

        if token in label_flags:
            next_token = argv[i + 1] if i + 1 < len(argv) else None
            if next_token is None or next_token.startswith("-"):
                normalized.extend([token, "label"])
                i += 1
                continue

            remaining_cli_tokens: list[str] = []
            for value in argv[i + 2 :]:
                if value == "--":
                    break
                remaining_cli_tokens.append(value)
            has_later_positional = any(
                not value.startswith("-") for value in remaining_cli_tokens
            )
            if not has_later_positional:
                normalized.extend([token, "label"])
                i += 1
                continue

        normalized.append(token)
        i += 1

    return normalized


def _normalize_label_attr(value: Optional[Any]) -> Optional[str]:
    """Normalize label attribute text; 'none' disables labels."""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.lower() == "none":
        return None
    return text


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


def _resolve_markdown_safe_text(*, output_format: str, whitespace_mode: str) -> bool:
    """Resolve whether text rendering should replace ASCII spaces with NBSP."""
    normalized_mode = str(whitespace_mode).strip().lower().replace("-", "_")
    if output_format != "text":
        return False
    if normalized_mode == "nbsp":
        return True
    if normalized_mode in {"auto", "ascii_space"}:
        return False
    raise ValueError("whitespace mode must be one of: auto, ascii-space, or nbsp")


def _resolve_target_canvas_dimension(
    spec: Optional[Any],
    *,
    flag_name: str,
    output_to_terminal: bool,
    auto_value: int,
) -> Optional[int]:
    if spec is None:
        return None

    text = str(spec).strip().lower()
    if text == "auto":
        if not output_to_terminal:
            raise ValueError(
                f"{flag_name} auto requires terminal stdout; "
                "use an explicit numeric value when redirecting or writing files"
            )
        return auto_value

    try:
        value = int(text)
    except ValueError as exc:
        raise ValueError(f"{flag_name} must be an integer or 'auto'") from exc
    if value <= 0:
        raise ValueError(f"{flag_name} must be greater than zero")
    return value


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

    argv = _normalize_label_args(_normalize_color_args(cli_raw_argv))

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
        "--constrained",
        action="store_true",
        help="Enable constrained partitioning mode for compatible layout strategies",
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
        "--target-canvas-width",
        nargs="?",
        const="auto",
        default=None,
        metavar="WIDTH|auto",
        help=(
            "Target width for constrained mode. Accepts WIDTH columns or "
            "'auto' (terminal width on terminal stdout)."
        ),
    )
    parser.add_argument(
        "--target-canvas-height",
        nargs="?",
        const="auto",
        default=None,
        metavar="HEIGHT|auto",
        help=(
            "Optional target height for constrained partitioning. Accepts HEIGHT rows "
            "or 'auto' (terminal height on terminal stdout)."
        ),
    )
    parser.add_argument(
        "--partition-overlap",
        type=int,
        default=0,
        help="Context overlap between neighboring constrained partitions (default: 0)",
    )
    parser.add_argument(
        "--partition-affinity-strength",
        type=int,
        default=1,
        help=(
            "Affinity weight used to keep closely related nodes together while "
            "splitting constrained partitions (0 disables)"
        ),
    )
    parser.add_argument(
        "--cross-partition-edge-style",
        choices=["stub", "none"],
        default="stub",
        help="Cross-partition edge rendering style for constrained layout (default: stub)",
    )
    parser.add_argument(
        "--connector-compaction",
        choices=["none", "partition"],
        default="none",
        help=(
            "Connector listing compaction mode for constrained panels: none "
            "(default) or partition"
        ),
    )
    parser.add_argument(
        "--partition-order",
        choices=["natural", "size"],
        default="natural",
        help="Constrained partition ordering: natural rank order or size (default: natural)",
    )
    parser.add_argument(
        "--panel-headers",
        choices=["none", "basic", "lineage"],
        default="basic",
        help="Constrained panel header mode: none, basic (default), or lineage",
    )
    parser.add_argument(
        "--connector-ref",
        choices=["auto", "id", "label", "both"],
        default="auto",
        help="Connector endpoint reference mode: auto (default), id, label, or both",
    )
    parser.add_argument(
        "--bboxes",
        "--bbox",
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
        help=(
            "Enable both node and edge labels using each element's 'label' attribute. "
            "Equivalent to --node-labels --edge-labels."
        ),
    )
    parser.add_argument(
        "--node-labels",
        nargs="?",
        const="label",
        default=None,
        metavar="ATTR",
        help=(
            "Enable node labels. Optionally provide the node attribute name to display "
            "(default: label). Use 'none' to disable node labels explicitly."
        ),
    )
    parser.add_argument(
        "--edge-labels",
        nargs="?",
        const="label",
        default=None,
        metavar="ATTR",
        help=(
            "Enable edge labels. Optionally provide the edge attribute name to display "
            "(default: label). Use 'none' to disable edge labels explicitly."
        ),
    )
    parser.add_argument(
        "--node-label-lines",
        type=str,
        default=None,
        metavar="SPEC",
        help=(
            "Comma-separated ordered label line specs used when --labels is enabled "
            "and node 'label' is absent. Supports dotted paths "
            "(e.g. name,birt.date,deat.date)."
        ),
    )
    parser.add_argument(
        "--node-label-sep",
        type=str,
        default=" ",
        help="Separator for joining multi-value parts within one synthesized label line",
    )
    parser.add_argument(
        "--node-label-max-lines",
        type=int,
        default=None,
        help="Optional maximum number of synthesized label lines",
    )
    parser.add_argument(
        "--bbox-multiline-labels",
        action="store_true",
        help="Enable multiline node labels and bbox height expansion when labels contain line breaks",
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
        "--edge-glyph-preset",
        choices=["default", "thick", "double"],
        default="default",
        help=(
            "Global edge line-art preset: default (thin), thick, or double "
            "(Unicode mode only for thick/double; ASCII falls back to standard glyphs)"
        ),
    )
    parser.add_argument(
        "--edge-arrow-style",
        choices=["ascii", "unicode"],
        default="ascii",
        help=(
            "Global arrowhead style for edges: ascii (default) or unicode. "
            "Unicode arrows are disabled automatically in ASCII charset mode."
        ),
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
        "--style-rule",
        action="append",
        default=[],
        metavar="RULE",
        help=(
            "Advanced style rule expression. Format: "
            "'<target>: <predicate> -> color=<color>' where target is "
            "edge|node|connector|panel_header. "
            "Repeat to add multiple rules."
        ),
    )
    parser.add_argument(
        "--style-rules-file",
        type=Path,
        default=None,
        metavar="FILE",
        help=(
            "JSON or YAML file containing {'rules': [...]} canonical style rules. "
            "YAML requires PyYAML."
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
    parser.add_argument(
        "--whitespace",
        choices=["auto", "ascii-space", "nbsp"],
        default="auto",
        help=(
            "Text output whitespace mode: auto (default), ascii-space, or nbsp. "
            "In auto mode, output-format defaults are used."
        ),
    )
    parser.add_argument(
        "--paginate-output-width",
        nargs="?",
        const="auto",
        default=None,
        metavar="WIDTH|auto",
        help=(
            "Paginate text output horizontally by terminal width (auto) or WIDTH columns. "
            "With no value, defaults to auto."
        ),
    )
    parser.add_argument(
        "--paginate-output-height",
        nargs="?",
        const="auto",
        default=None,
        metavar="HEIGHT|auto",
        help=(
            "Paginate text output vertically by terminal height (auto) or HEIGHT rows. "
            "If omitted, row pagination is disabled and all rows remain in one page."
        ),
    )
    parser.add_argument(
        "--paginate-overlap",
        type=int,
        default=8,
        metavar="COLUMNS",
        help="Overlap columns between neighboring output pages (default: 8)",
    )
    parser.add_argument(
        "--select-output-page-x",
        "--page-x",
        "-x",
        type=int,
        default=0,
        dest="page_x",
        help="Select horizontal page index (default: 0)",
    )
    parser.add_argument(
        "--select-output-page-y",
        "--page-y",
        "-y",
        type=int,
        default=0,
        dest="page_y",
        help="Select vertical page index (currently must be 0)",
    )
    parser.add_argument(
        "--list-pages",
        action="store_true",
        help="Print page index metadata when pagination is enabled",
    )
    parser.add_argument(
        "--write-pages",
        type=Path,
        default=None,
        metavar="DIR",
        help="Write all paginated pages to DIR as page_xNN_yNN.txt files",
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


def _parse_style_rule_string(rule: str) -> dict[str, object]:
    text = str(rule).strip()
    if not text:
        raise ValueError("Invalid --style-rule: rule cannot be empty")
    if ":" not in text or "->" not in text:
        raise ValueError(
            f"Invalid --style-rule '{rule}'. Expected "
            "<target>: <predicate> -> color=<color>[,<key>=<value>...]"
        )
    head, set_text = text.split("->", 1)
    target_text, when_text = head.split(":", 1)
    target = target_text.strip().lower()
    if target not in {"edge", "node", "connector", "panel_header"}:
        raise ValueError(
            f"Invalid --style-rule '{rule}': target must be one of edge, node, connector, panel_header"
        )
    when = when_text.strip()
    set_values: dict[str, str] = {}
    for pair in str(set_text).split(","):
        token = pair.strip()
        if not token:
            continue
        if "=" not in token:
            raise ValueError(
                f"Invalid --style-rule '{rule}': expected <key>=<value> assignments"
            )
        key, value = token.split("=", 1)
        key_text = key.strip().lower()
        value_text = value.strip()
        if not key_text or not value_text:
            raise ValueError(
                f"Invalid --style-rule '{rule}': assignment key/value cannot be empty"
            )
        set_values[key_text] = value_text
    if not set_values:
        raise ValueError(
            f"Invalid --style-rule '{rule}': no assignments found after '->'"
        )
    return {
        "target": target,
        "when": when,
        "set": set_values,
    }


def _load_style_rules_file(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        raise ValueError(f"--style-rules-file not found: {path}")
    raw_text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    loaded: object
    if suffix == ".json":
        loaded = json.loads(raw_text)
    else:
        try:
            import yaml
        except Exception as exc:
            raise ValueError(
                "--style-rules-file YAML parsing requires PyYAML; "
                "use JSON or install PyYAML"
            ) from exc
        loaded = yaml.safe_load(raw_text)

    if not isinstance(loaded, dict):
        raise ValueError("--style-rules-file must contain an object with key 'rules'")
    rules = loaded.get("rules")
    if not isinstance(rules, list):
        raise ValueError("--style-rules-file must define 'rules' as a list")
    parsed: list[dict[str, object]] = []
    for idx, item in enumerate(rules):
        if not isinstance(item, dict):
            raise ValueError(f"--style-rules-file rules[{idx}] must be an object")
        parsed.append(dict(item))
    return parsed


def _legacy_edge_rules_to_style_rules(
    edge_color_rules: dict[str, dict[str, str]],
) -> list[dict[str, object]]:
    normalized: list[dict[str, object]] = []
    for attr_name, mapping in edge_color_rules.items():
        for attr_value, color in mapping.items():
            normalized.append(
                {
                    "target": "edge",
                    "when": f'edge.{attr_name} == "{attr_value}"',
                    "set": {"color": color},
                }
            )
    return normalized


def create_layout_options(
    args: argparse.Namespace, explicit_layout_fields: Optional[set[str]] = None
) -> LayoutOptions:
    """Create LayoutOptions from CLI arguments."""
    node_style = NodeStyle[args.style.upper()] if args.style is not None else None
    color_mode = args.colors
    layout_strategy = args.layout_strategy.replace("-", "_")
    binary_tree_layout = args.binary_tree
    edge_color_rules = _parse_edge_color_rules(args.edge_color_rule)
    style_rules: list[dict[str, object]] = []
    for rule in args.style_rule:
        style_rules.append(_parse_style_rule_string(rule))
    if args.style_rules_file is not None:
        style_rules.extend(_load_style_rules_file(args.style_rules_file))
    style_rules.extend(_legacy_edge_rules_to_style_rules(edge_color_rules))
    node_label_lines: tuple[str, ...] = tuple()
    if args.node_label_lines:
        node_label_lines = tuple(
            token.strip()
            for token in str(args.node_label_lines).split(",")
            if token.strip()
        )
    color_nodes = not args.no_color_nodes
    if color_mode == "attr" and not style_rules:
        raise ValueError(
            "--colors attr requires --edge-color-rule or --style-rule/--style-rules-file"
        )
    use_ascii = args.charset in {CharSet.ASCII, CharSet.ANSI} or args.use_legacy_ascii
    allow_ansi_in_ascii = args.charset == CharSet.ANSI and not args.use_legacy_ascii
    node_label_attr = _normalize_label_attr(args.node_labels)
    edge_label_attr = _normalize_label_attr(args.edge_labels)
    output_to_terminal = args.output is None and sys.stdout.isatty()
    term_size = shutil.get_terminal_size((80, 24))
    target_canvas_width = _resolve_target_canvas_dimension(
        args.target_canvas_width,
        flag_name="--target-canvas-width",
        output_to_terminal=output_to_terminal,
        auto_value=term_size.columns,
    )
    target_canvas_height = _resolve_target_canvas_dimension(
        args.target_canvas_height,
        flag_name="--target-canvas-height",
        output_to_terminal=output_to_terminal,
        auto_value=term_size.lines,
    )
    if args.partition_overlap < 0:
        raise ValueError("--partition-overlap must be non-negative")
    if args.partition_affinity_strength < 0:
        raise ValueError("--partition-affinity-strength must be non-negative")
    if args.constrained and target_canvas_width is None:
        raise ValueError("--constrained requires --target-canvas-width")
    if args.labels:
        if node_label_attr is None:
            node_label_attr = "label"
        if edge_label_attr is None:
            edge_label_attr = "label"

    options = LayoutOptions(
        node_style=node_style,
        node_spacing=args.node_spacing,
        layer_spacing=args.layer_spacing,
        use_ascii=use_ascii,
        binary_tree_layout=binary_tree_layout,
        layout_strategy=layout_strategy,
        constrained=args.constrained,
        node_order_mode=args.node_order,
        node_order_attr=args.node_order_attr,
        node_order_reverse=args.node_order_reverse,
        flow_direction=args.flow_direction,
        target_canvas_width=target_canvas_width,
        target_canvas_height=target_canvas_height,
        partition_overlap=args.partition_overlap,
        partition_affinity_strength=args.partition_affinity_strength,
        cross_partition_edge_style=args.cross_partition_edge_style,
        connector_compaction=args.connector_compaction,
        partition_order=args.partition_order,
        panel_header_mode=args.panel_headers,
        connector_ref_mode=args.connector_ref,
        bboxes=args.bboxes,
        hpad=args.hpad,
        vpad=args.vpad,
        uniform=args.uniform,
        edge_anchor_mode=args.edge_anchors,
        shared_ports_mode=args.shared_ports,
        bidirectional_mode=args.bidirectional_mode,
        use_labels=args.labels,
        node_label_attr=node_label_attr,
        edge_label_attr=edge_label_attr,
        node_label_lines=node_label_lines,
        node_label_sep=args.node_label_sep,
        node_label_max_lines=args.node_label_max_lines,
        bbox_multiline_labels=args.bbox_multiline_labels,
        ansi_colors=(color_mode != "none"),
        allow_ansi_in_ascii=allow_ansi_in_ascii,
        edge_color_mode="source" if color_mode == "none" else color_mode,
        edge_color_rules=edge_color_rules,
        style_rules=style_rules,
        edge_glyph_preset=args.edge_glyph_preset,
        edge_arrow_style=args.edge_arrow_style,
        color_nodes=color_nodes,
        whitespace_mode=args.whitespace,
    )
    setattr(options, "_explicit_cli_fields", set(explicit_layout_fields or set()))
    return options


def main() -> Optional[int]:
    """CLI entry point for PHART."""
    args, unknown, explicit_layout_fields, module_argv = parse_args()
    markdown_safe_text = _resolve_markdown_safe_text(
        output_format=args.output_format,
        whitespace_mode=args.whitespace,
    )

    try:
        output_render_config = OutputRenderConfig(
            output_format=args.output_format,
            svg_cell_size=args.svg_cell_size,
            svg_font_family=args.svg_font_family,
            svg_text_mode=args.svg_text_mode,
            svg_font_path=args.svg_font_path,
            svg_fg=args.svg_fg,
            svg_bg=args.svg_bg,
            markdown_safe_text=markdown_safe_text,
        )
        renderer_output_config = RendererOutputConfig(
            output_format=args.output_format,
            svg_cell_size=args.svg_cell_size,
            svg_font_family=args.svg_font_family,
            svg_text_mode=args.svg_text_mode,
            svg_font_path=args.svg_font_path,
            svg_fg=args.svg_fg,
            svg_bg=args.svg_bg,
            markdown_safe_text=markdown_safe_text,
        )
        paginate_width: Optional[int] = None
        paginate_height: Optional[int] = None
        paginate_enabled = (
            args.paginate_output_width is not None
            or args.paginate_output_height is not None
        )
        if paginate_enabled:
            if args.output_format != "text":
                raise ValueError(
                    "Pagination is only supported with --output-format text"
                )
            term_size = shutil.get_terminal_size((80, 24))
            output_to_terminal = args.output is None and sys.stdout.isatty()

            if args.paginate_output_width is not None:
                width_spec = str(args.paginate_output_width).strip().lower()
                if width_spec == "auto":
                    if not output_to_terminal:
                        raise ValueError(
                            "--paginate-output-width auto requires terminal stdout; "
                            "use an explicit numeric width when redirecting or writing files"
                        )
                    paginate_width = term_size.columns
                else:
                    try:
                        paginate_width = int(width_spec)
                    except ValueError as exc:
                        raise ValueError(
                            "--paginate-output-width must be an integer or 'auto'"
                        ) from exc
                if paginate_width <= 0:
                    raise ValueError(
                        "--paginate-output-width must be greater than zero"
                    )

            if args.paginate_output_height is not None:
                height_spec = str(args.paginate_output_height).strip().lower()
                if height_spec == "auto":
                    if not output_to_terminal:
                        raise ValueError(
                            "--paginate-output-height auto requires terminal stdout; "
                            "use an explicit numeric height when redirecting or writing files"
                        )
                    paginate_height = term_size.lines
                else:
                    try:
                        paginate_height = int(height_spec)
                    except ValueError as exc:
                        raise ValueError(
                            "--paginate-output-height must be an integer or 'auto'"
                        ) from exc
                if paginate_height <= 0:
                    raise ValueError(
                        "--paginate-output-height must be greater than zero"
                    )

            if args.paginate_overlap < 0:
                raise ValueError("--paginate-overlap must be non-negative")
            if paginate_width is not None and args.paginate_overlap >= paginate_width:
                raise ValueError(
                    "--paginate-overlap must be smaller than --paginate-output-width"
                )
            if args.page_x < 0 or args.page_y < 0:
                raise ValueError("--page-x and --page-y must be non-negative")

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
            if paginate_enabled:
                rendered_output = _apply_text_pagination(
                    args, rendered_output, paginate_width, paginate_height
                )
            rendered_output = _ensure_trailing_newline(rendered_output)
            if args.output:
                args.output.write_text(rendered_output, encoding="utf-8")
            else:
                _write_stdout_output(rendered_output)
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
            panel_blocks: Optional[list[str]] = None
            if paginate_enabled and renderer_output_config.output_format == "text":
                if cli_options.constrained:
                    panel_blocks = renderer.render_panel_blocks(
                        markdown_safe=renderer_output_config.markdown_safe_text
                    )
                    rendered_output = "\n\n".join(panel_blocks)
                else:
                    rendered_output = render_renderer_output(
                        renderer, config=renderer_output_config
                    )
            else:
                rendered_output = render_renderer_output(
                    renderer, config=renderer_output_config
                )
            if paginate_enabled:
                rendered_output = _apply_text_pagination(
                    args,
                    rendered_output,
                    paginate_width,
                    paginate_height,
                    panel_blocks=panel_blocks,
                )
            rendered_output = _ensure_trailing_newline(rendered_output)
            if args.output:
                args.output.write_text(rendered_output, encoding="utf-8")
            else:
                _write_stdout_output(rendered_output)
            return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def _write_stdout_output(text: str) -> None:
    """Write CLI output to stdout.

    Ensure newline-terminated textual output for shell/tool compatibility.
    """
    sys.stdout.write(_ensure_trailing_newline(text))


def _ensure_trailing_newline(text: str) -> str:
    if not text or text.endswith("\n"):
        return text
    return text + "\n"


def _apply_text_pagination(
    args: argparse.Namespace,
    rendered_output: str,
    paginate_width: Optional[int],
    paginate_height: Optional[int],
    *,
    panel_blocks: Optional[list[str]] = None,
) -> str:
    overlap_x = args.paginate_overlap if paginate_width is not None else 0

    if panel_blocks is None and args.constrained:
        panel_blocks = _split_constrained_panel_blocks(rendered_output)

    if panel_blocks and len(panel_blocks) > 1:
        selected_blocks: list[str] = []
        panel_descriptions: list[str] = []

        if args.write_pages is not None:
            args.write_pages.mkdir(parents=True, exist_ok=True)

        for panel_idx, panel_text in enumerate(panel_blocks):
            panel_rows = panel_text.splitlines()
            panel_canvas_width = max((len(row) for row in panel_rows), default=1)
            panel_page_width = (
                paginate_width
                if paginate_width is not None
                else max(1, panel_canvas_width)
            )

            pages, canvas_width, canvas_height = paginate_text(
                panel_text,
                page_width=panel_page_width,
                overlap=overlap_x,
                page_height=paginate_height,
                overlap_y=0,
            )
            if args.list_pages:
                description = describe_pages(
                    pages,
                    canvas_width=canvas_width,
                    canvas_height=canvas_height,
                    page_width=panel_page_width,
                    overlap=overlap_x,
                )
                panel_descriptions.append(
                    f"Panel P{panel_idx + 1}/{len(panel_blocks)}\n{description}"
                )

            if args.write_pages is not None:
                for page in pages:
                    page_file = args.write_pages / (
                        f"panel_p{panel_idx + 1:02d}_x{page.x_index:02d}_y{page.y_index:02d}.txt"
                    )
                    page_file.write_text(page.text, encoding="utf-8")

            max_x = max((page.x_index for page in pages), default=0)
            max_y = max((page.y_index for page in pages), default=0)
            selected_x = min(args.page_x, max_x)
            selected_y = min(args.page_y, max_y)
            selected_page = next(
                (
                    page
                    for page in pages
                    if page.x_index == selected_x and page.y_index == selected_y
                ),
                None,
            )
            if selected_page is None:
                raise ValueError(
                    f"Unable to select paginated view for panel P{panel_idx + 1}"
                )
            selected_blocks.append(selected_page.text)

        if args.list_pages and panel_descriptions:
            print("\n\n".join(panel_descriptions), file=sys.stderr)
        return "\n\n".join(selected_blocks)

    rows = rendered_output.splitlines()
    canvas_width = max((len(row) for row in rows), default=1)
    page_width = paginate_width if paginate_width is not None else max(1, canvas_width)

    pages, canvas_width, canvas_height = paginate_text(
        rendered_output,
        page_width=page_width,
        overlap=overlap_x,
        page_height=paginate_height,
        overlap_y=0,
    )

    if args.list_pages:
        print(
            describe_pages(
                pages,
                canvas_width=canvas_width,
                canvas_height=canvas_height,
                page_width=page_width,
                overlap=overlap_x,
            ),
            file=sys.stderr,
        )

    if args.write_pages is not None:
        args.write_pages.mkdir(parents=True, exist_ok=True)
        for page in pages:
            page_file = args.write_pages / (
                f"page_x{page.x_index:02d}_y{page.y_index:02d}.txt"
            )
            page_file.write_text(page.text, encoding="utf-8")

    selected_page = next(
        (
            page
            for page in pages
            if page.x_index == args.page_x and page.y_index == args.page_y
        ),
        None,
    )
    if selected_page is None:
        max_x = max((page.x_index for page in pages), default=0)
        max_y = max((page.y_index for page in pages), default=0)
        raise ValueError(
            f"Requested page x={args.page_x}, y={args.page_y} is out of range "
            f"(max x={max_x}, y={max_y})"
        )
    return selected_page.text


def _split_constrained_panel_blocks(rendered_output: str) -> Optional[list[str]]:
    lines = rendered_output.splitlines()
    if not lines:
        return None

    ansi_re = re.compile(r"\x1b\[[0-9;]*m")
    starts: list[int] = []
    for idx, line in enumerate(lines):
        plain = ansi_re.sub("", line)
        if re.search(r"\bPanel\s+P\d+/\d+\b", plain):
            starts.append(idx)

    if len(starts) < 2:
        return None

    blocks: list[str] = []
    for pos, start in enumerate(starts):
        end = starts[pos + 1] if pos + 1 < len(starts) else len(lines)
        block = "\n".join(lines[start:end]).rstrip()
        if block:
            blocks.append(block)
    return blocks if blocks else None


if __name__ == "__main__":
    sys.exit(main())
