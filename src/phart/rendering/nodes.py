"""Nodes helpesr for renderer"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple

if TYPE_CHECKING:
    from phart.renderer import ASCIIRenderer


def normalize_label_value(label: Any, *, keep_newlines: bool = False) -> str:
    """Normalize node labels for display."""
    text = str(label).strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {"'", '"'}:
        text = text[1:-1]
    text = text.replace("\r\n", "\n")
    if keep_newlines:
        text = "\n".join(part.strip() for part in text.split("\n"))
    else:
        text = text.replace("\n", " ")
    return text.strip()


def get_display_node_text(renderer: ASCIIRenderer, node: Any) -> str:
    """Resolve display text for a node key."""
    multiline = _allow_multiline_labels(renderer)
    if renderer.options.use_labels:
        attrs = renderer.graph.nodes[node] if node in renderer.graph else {}
        label = attrs.get("label")
        if label is not None:
            normalized = normalize_label_value(label, keep_newlines=multiline)
            if normalized:
                return normalized
        if renderer.options.node_label_lines:
            synthesized = _synthesize_label_from_line_specs(renderer, attrs)
            if synthesized:
                return synthesized
        synthesized = _synthesize_label_from_node_attrs(attrs)
        if synthesized:
            normalized = normalize_label_value(synthesized, keep_newlines=multiline)
            if normalized:
                return normalized
    return str(node)


def _synthesize_label_from_node_attrs(attrs: Dict[Any, Any]) -> str:
    """Build a concise display label from node attributes."""
    if not attrs:
        return ""

    name = _extract_scalar_text(attrs.get("name"))
    birth = _extract_gedcom_event_date(attrs.get("birt"))
    death = _extract_gedcom_event_date(attrs.get("deat"))
    if name:
        lifespan = f"{birth or '-'}-{death or '-'}" if (birth or death) else None
        return f"{name} {lifespan}".strip() if lifespan else name

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
    return bool(renderer.options.bboxes and renderer.options.bbox_multiline_labels)


def _synthesize_label_from_line_specs(renderer: ASCIIRenderer, attrs: Dict[Any, Any]) -> str:
    lines: list[str] = []
    for spec in renderer.options.node_label_lines:
        text = _resolve_label_line_spec(attrs, spec)
        if text is None:
            text = ""
        lines.append(text)
        if (
            renderer.options.node_label_max_lines is not None
            and len(lines) >= renderer.options.node_label_max_lines
        ):
            break

    if not any(line.strip() for line in lines):
        return ""

    if _allow_multiline_labels(renderer):
        return "\n".join(lines)
    return renderer.options.node_label_sep.join(line for line in lines if line.strip())


def _resolve_label_line_spec(attrs: Dict[Any, Any], spec: str) -> Optional[str]:
    token = str(spec).strip()
    if not token:
        return None
    if token.lower() == "lifespan":
        birth = _extract_gedcom_event_date(attrs.get("birt"))
        death = _extract_gedcom_event_date(attrs.get("deat"))
        if not birth and not death:
            return None
        return f"{birth or '-'}-{death or '-'}"

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


def _extract_gedcom_event_date(value: Any) -> Optional[str]:
    if isinstance(value, dict):
        return _extract_scalar_text(value.get("date"))
    return None


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
    lines = _resolved_node_label_lines(renderer, node)
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
    label_lines = _resolved_node_label_lines(renderer, node)
    node_width, node_height = renderer._get_node_dimensions(node)
    node_color = renderer._node_color_map.get(node)

    # if  renderer._use_ansi_colors and not renderer.options.bboxes:
    if not renderer.options.bboxes:
        _paint_label(renderer, label_lines[0] if label_lines else "", x, y, node_color)
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
            max(0, (inner_width - renderer.options.get_text_display_width(line_text)) // 2)
            if renderer.options.uniform
            else 0
        )
        inner_start_x = x + 1 + renderer.options.hpad + label_offset
        _paint_label(renderer, line_text, inner_start_x, content_top + line_index, node_color)


def _resolved_node_label_lines(renderer: ASCIIRenderer, node: Any) -> list[str]:
    display_text = renderer._get_display_node_text(node)
    if _allow_multiline_labels(renderer):
        raw_lines = [segment for segment in display_text.split("\n")]
    else:
        raw_lines = [display_text]

    decorated = [renderer.options.get_node_text(line) for line in raw_lines]
    return decorated if decorated else [renderer.options.get_node_text("")]


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
