"""Nodes helpesr for renderer"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from phart.style_rules import evaluate_style_rule_set

if TYPE_CHECKING:
    from phart.renderer import ASCIIRenderer
    from phart.styles import LayoutOptions


def normalize_label_value(label: Any, *, keep_newlines: bool = False) -> str:
    """Normalize node labels for display."""
    text = str(label).strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {"'", '"'}:
        text = text[1:-1]
    text = _decode_graphviz_linebreak_escapes(text)
    text = text.replace("\r\n", "\n")
    if keep_newlines:
        text = "\n".join(part.strip() for part in text.split("\n"))
    else:
        text = text.replace("\n", " ")
    return text.strip()


def _decode_graphviz_linebreak_escapes(text: str) -> str:
    """Decode Graphviz/DOT line-break escapes in label text.

    Graphviz supports ``\\n``, ``\\l``, and ``\\r`` inside labels as line-break
    controls. We normalize all three to ``\\n`` for PHART's line splitter.
    """
    out: list[str] = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch != "\\" or i + 1 >= len(text):
            out.append(ch)
            i += 1
            continue

        nxt = text[i + 1]
        if nxt in {"n", "l", "r"}:
            out.append("\n")
            i += 2
            continue
        if nxt == "\\":
            out.append("\\")
            i += 2
            continue

        # Preserve unknown escape sequences literally.
        out.append("\\")
        out.append(nxt)
        i += 2
    return "".join(out)


def get_display_node_text(renderer: ASCIIRenderer, node: Any) -> str:
    """Resolve display text for a node key."""
    attrs = renderer.graph.nodes[node] if node in renderer.graph else {}
    return resolve_display_node_text(renderer.options, attrs, node)


def resolve_display_node_text(
    options: LayoutOptions, attrs: Dict[Any, Any], fallback_node: Any
) -> str:
    multiline = _allow_multiline_labels_for_options(options)
    node_label_attr = options.node_label_attr
    if node_label_attr:
        label = attrs.get(node_label_attr)
        if label is not None:
            normalized = normalize_label_value(label, keep_newlines=multiline)
            if normalized:
                return normalized
        if node_label_attr == "label":
            if options.node_label_lines:
                synthesized = _synthesize_label_from_line_specs(options, attrs)
                if synthesized:
                    return synthesized
            synthesized = _synthesize_label_from_node_attrs(attrs)
            if synthesized:
                normalized = normalize_label_value(synthesized, keep_newlines=multiline)
                if normalized:
                    return normalized
    return str(fallback_node)


def _synthesize_label_from_node_attrs(attrs: Dict[Any, Any]) -> str:
    """Build a concise display label from node attributes."""
    if not attrs:
        return ""

    name = _extract_scalar_text(attrs.get("name"))
    if name:
        return name

    title = _extract_scalar_text(attrs.get("title"))
    if title:
        return title

    parts = []
    sorted_items = sorted(attrs.items(), key=lambda item: str(item[0]))[:6]
    for key, value in sorted_items:
        key_text = str(key)
        if key_text == "label":
            continue
        scalar = _extract_scalar_text(value)
        if not scalar:
            continue
        parts.append(f"{key_text}={scalar}")
        if len(parts) >= 3:
            break
    return ", ".join(parts)


def _allow_multiline_labels(renderer: ASCIIRenderer) -> bool:
    return _allow_multiline_labels_for_options(renderer.options)


def _allow_multiline_labels_for_options(options: LayoutOptions) -> bool:
    return bool(options.bboxes and options.bbox_multiline_labels)


def _synthesize_label_from_line_specs(
    options: LayoutOptions, attrs: Dict[Any, Any]
) -> str:
    lines: list[str] = []
    explicit_roots: set[str] = set()
    wildcard_seen = False

    for spec in options.node_label_lines:
        if _is_wildcard_label_spec(spec):
            wildcard_seen = True
            for rest_line in _all_remaining_attr_lines(
                attrs, excluded_roots=explicit_roots
            ):
                if rest_line:
                    lines.append(rest_line)
                    if (
                        options.node_label_max_lines is not None
                        and len(lines) >= options.node_label_max_lines
                    ):
                        break
            if (
                options.node_label_max_lines is not None
                and len(lines) >= options.node_label_max_lines
            ):
                break
            continue

        explicit_root = _explicit_spec_root(spec)
        if explicit_root:
            explicit_roots.add(explicit_root)
        text = _resolve_label_line_spec(attrs, spec)
        if text is None:
            text = ""
        lines.append(text)
        if (
            options.node_label_max_lines is not None
            and len(lines) >= options.node_label_max_lines
        ):
            break

    if wildcard_seen and not any(line.strip() for line in lines):
        fallback = _synthesize_label_from_node_attrs(attrs)
        if fallback:
            lines = [fallback]

    if not any(str(line).strip() for line in lines):
        return ""

    if _allow_multiline_labels_for_options(options):
        return "\n".join(lines)
    return options.node_label_sep.join(line for line in lines if line.strip())


def _is_wildcard_label_spec(spec: str) -> bool:
    token = str(spec).strip().lower()
    return token in {"*", "[all the rest]", "[all_the_rest]", "rest", "all"}


def _explicit_spec_root(spec: str) -> Optional[str]:
    token = str(spec).strip()
    if not token:
        return None
    if _is_wildcard_label_spec(token):
        return None
    return token.split(".", 1)[0].strip().lower() or None


def _resolve_label_line_spec(attrs: Dict[Any, Any], spec: str) -> Optional[str]:
    token = str(spec).strip()
    if not token:
        return None

    value: Any = attrs
    for part in token.split("."):
        part = part.strip()
        if not part:
            return None
        if isinstance(value, dict):
            value = value.get(part)
        else:
            return None
    return _extract_scalar_text(value)


def _all_remaining_attr_lines(
    attrs: Dict[Any, Any], *, excluded_roots: set[str]
) -> List[str]:
    lines: List[str] = []
    for key, value in sorted(attrs.items(), key=lambda item: str(item[0]).lower()):
        key_text = str(key).strip()
        key_lower = key_text.lower()
        if key_lower == "label":
            continue
        if key_lower in excluded_roots:
            continue

        flattened = _flatten_attr_values(key_text, value)
        if flattened:
            lines.extend(flattened)
            continue

        scalar = _extract_scalar_text(value)
        if scalar:
            lines.append(f"{key_text}={scalar}")
    return lines


def _flatten_attr_values(prefix: str, value: Any) -> List[str]:
    lines: List[str] = []
    if isinstance(value, dict):
        for key, nested in sorted(value.items(), key=lambda item: str(item[0]).lower()):
            nested_prefix = f"{prefix}.{key}"
            lines.extend(_flatten_attr_values(nested_prefix, nested))
        return lines
    if isinstance(value, (list, tuple)):
        parts = [_extract_scalar_text(item) for item in value]
        scalar_parts = [part for part in parts if part]
        if scalar_parts:
            return [f"{prefix}={','.join(scalar_parts)}"]
        for idx, item in enumerate(value):
            lines.extend(_flatten_attr_values(f"{prefix}[{idx}]", item))
        return lines

    scalar = _extract_scalar_text(value)
    return [f"{prefix}={scalar}"] if scalar else []


def _extract_scalar_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        for item in value:
            text = _extract_scalar_text(item)
            if text:
                return text
        return None
    if isinstance(value, dict):
        return None

    text = str(value).strip()
    if not text:
        return None
    return text


def get_widest_node_text_width(renderer: ASCIIRenderer) -> Optional[int]:
    if not renderer.options.uniform:
        return None
    return max(
        (
            max(
                (
                    renderer.options.get_text_display_width(line)
                    for line in _resolved_node_label_lines(renderer, node)
                ),
                default=0,
            )
            for node in renderer.graph.nodes()
        ),
        default=0,
    )


def get_node_dimensions(renderer: ASCIIRenderer, node: Any) -> Tuple[int, int]:
    lines = resolved_node_label_lines(
        renderer.options,
        renderer.graph.nodes[node] if node in renderer.graph else {},
        node,
    )
    text_width = max(
        (renderer.options.get_text_display_width(line) for line in lines),
        default=0,
    )
    widest = renderer._get_widest_node_text_width()
    if renderer.options.bboxes and renderer.options.uniform and widest is not None:
        text_width = max(text_width, widest)

    if not renderer.options.bboxes:
        return text_width, 1

    width = text_width + (2 * renderer.options.hpad) + 2
    content_rows = len(lines) if _allow_multiline_labels(renderer) else 1
    height = (2 * renderer.options.vpad) + 2 + max(1, content_rows)
    return width, height


def get_node_bounds(
    renderer: ASCIIRenderer, node: Any, positions: Dict[Any, Tuple[int, int]]
) -> Dict[str, int]:
    x, y = positions[node]
    width, height = renderer._get_node_dimensions(node)
    left = x
    right = x + width - 1
    top = y
    bottom = y + height - 1
    center_x = left + (width // 2)
    center_y = top + (height // 2)
    return {
        "left": left,
        "right": right,
        "top": top,
        "bottom": bottom,
        "center_x": center_x,
        "center_y": center_y,
    }


def draw_node(renderer: ASCIIRenderer, node: Any, x: int, y: int) -> None:
    label_lines = resolved_node_label_lines(
        renderer.options,
        renderer.graph.nodes[node] if node in renderer.graph else {},
        node,
    )
    node_width, node_height = renderer._get_node_dimensions(node)
    node_color = renderer._node_color_map.get(node)
    label_color = renderer._label_color_override or node_color

    # if  renderer._use_ansi_colors and not renderer.options.bboxes:
    if not renderer.options.bboxes:
        _paint_label(renderer, label_lines[0] if label_lines else "", x, y, label_color)
        return

    right_x = x + node_width - 1
    bottom_y = y + node_height - 1
    inner_width = max(0, node_width - 2 - (2 * renderer.options.hpad))

    renderer._paint_cell(x, y, renderer.options.box_top_left, node_color)
    renderer._paint_cell(right_x, y, renderer.options.box_top_right, node_color)
    # TODO(width): Border routing assumes box glyphs are single-cell display width.
    # If box edge/corner glyphs are configured as wide glyphs, draw logic must
    # reserve continuation cells and adjust border stepping.
    for col in range(x + 1, right_x):
        renderer._paint_cell(col, y, renderer.options.edge_horizontal, node_color)

    renderer._paint_cell(x, bottom_y, renderer.options.box_bottom_left, node_color)
    renderer._paint_cell(
        right_x, bottom_y, renderer.options.box_bottom_right, node_color
    )
    for col in range(x + 1, right_x):
        renderer._paint_cell(
            col, bottom_y, renderer.options.edge_horizontal, node_color
        )

    for row in range(y + 1, bottom_y):
        renderer._paint_cell(x, row, renderer.options.edge_vertical, node_color)
        renderer._paint_cell(right_x, row, renderer.options.edge_vertical, node_color)

    content_top = y + 1 + renderer.options.vpad
    lines_to_draw = (
        label_lines if _allow_multiline_labels(renderer) else label_lines[:1]
    )
    for line_index, line_text in enumerate(lines_to_draw):
        label_offset = (
            max(
                0,
                (inner_width - renderer.options.get_text_display_width(line_text)) // 2,
            )
            if renderer.options.uniform
            else 0
        )
        inner_start_x = x + 1 + renderer.options.hpad + label_offset
        _paint_label(
            renderer, line_text, inner_start_x, content_top + line_index, label_color
        )


def _resolved_node_label_lines(renderer: ASCIIRenderer, node: Any) -> list[str]:
    attrs = renderer.graph.nodes[node] if node in renderer.graph else {}
    return resolved_node_label_lines(renderer.options, attrs, node)


def resolved_node_label_lines(
    options: LayoutOptions,
    attrs: Dict[Any, Any],
    fallback_node: Any,
) -> list[str]:
    display_text = resolve_display_node_text(options, attrs, fallback_node)
    if _allow_multiline_labels_for_options(options):
        raw_lines = [segment for segment in display_text.split("\n")]
    else:
        raw_lines = [display_text]
    style_set = resolve_effective_node_style_set(options, attrs)
    decorated = [
        _decorate_node_line(
            options=options,
            line=line,
            fallback_node=fallback_node,
            style_set=style_set,
        )
        for line in raw_lines
    ]
    empty = _decorate_node_line(
        options=options,
        line="",
        fallback_node=fallback_node,
        style_set=style_set,
    )
    return decorated if decorated else [empty]


def resolve_effective_node_style_set(
    options: LayoutOptions, attrs: Dict[Any, Any]
) -> Dict[str, str]:
    context = {
        "self": attrs,
        "node": attrs,
    }
    return evaluate_style_rule_set(
        getattr(options, "_compiled_style_rules", []),
        "node",
        context,
    )


def _node_style_decorators_for(
    options: LayoutOptions,
    node_style_token: str,
    *,
    fallback_node: Any,
) -> Tuple[str, str]:
    token = str(node_style_token).strip().lower()
    if token == "minimal":
        return "", ""
    if token == "square":
        return "[", "]"
    if token == "round":
        return "(", ")"
    if token == "diamond":
        return "<", ">"
    if token == "custom":
        decorators = options.custom_decorators or {}
        return decorators.get(str(fallback_node), ("*", "*"))
    return options.get_node_decorators(str(fallback_node))


def _decorate_node_line(
    *,
    options: LayoutOptions,
    line: str,
    fallback_node: Any,
    style_set: Dict[str, str],
) -> str:
    if not style_set:
        return options.get_node_text(line)

    if "node_style" in style_set:
        prefix, suffix = _node_style_decorators_for(
            options, style_set["node_style"], fallback_node=fallback_node
        )
    else:
        prefix, suffix = options.get_node_decorators(line)

    if "prefix" in style_set:
        prefix = style_set["prefix"]
    if "suffix" in style_set:
        suffix = style_set["suffix"]
    return f"{prefix}{line}{suffix}"


def _paint_label(
    renderer: ASCIIRenderer,
    label: str,
    start_x: int,
    y: int,
    color: Optional[str],
) -> None:
    cursor_x = start_x
    for char in label:
        renderer._paint_cell(cursor_x, y, char, color)
        char_width = renderer.options.get_char_display_width(char)
        if char_width <= 0:
            continue

        # Mark continuation cells so wide glyphs occupy their full terminal width.
        for continuation in range(1, char_width):
            renderer._paint_cell(cursor_x + continuation, y, "", color)
        cursor_x += char_width
