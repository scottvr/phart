# src path: src\phart\styles.py
from dataclasses import dataclass, field, fields
from enum import Enum
import unicodedata
from typing import Any, Dict, List, Optional, Tuple, Union

from .style_rules import CompiledStyleRule, compile_style_rules


class NodeStyle(Enum):
    """Node representation styles for ASCII rendering.

    Attributes
    ----------
    MINIMAL : str
        No decorators, just the node label
    SQUARE : str
        Node label in square brackets [node]
    ROUND : str
        Node label in parentheses (node)
    DIAMOND : str
        Node label in angle brackets <node>
    """

    MINIMAL = "minimal"
    SQUARE = "square"
    ROUND = "round"
    DIAMOND = "diamond"
    CUSTOM = "custom"
    BBOX = "bboxes"


class EdgeChar:
    """
    Descriptor for ASCII/Unicode character pairs.

    Provides automatic fallback to ASCII characters when needed.
    """

    def __init__(self, ascii_char: str, unicode_char: str) -> None:
        self.ascii_char = ascii_char
        self.unicode_char = unicode_char

    def __get__(self, obj: Optional[Any], objtype: Optional[type] = None) -> str:
        """Get the appropriate character.

        Returns str when accessed on instance, EdgeChar when accessed on class.
        """
        if obj is None:
            return self  # type: ignore[return-value]
        return self.ascii_char if obj.use_ascii else self.unicode_char

    def __set__(self, obj: Any, value: str) -> None:
        self.unicode_char = value


class FlowDirection(Enum):
    """Layout flow direction for graph rendering.

    Attributes
    ----------
    DOWN : str
        Root at top, children below
    UP : str
        Root at bottom, children above
    RIGHT : str
        Root at left, children to right
    LEFT : str
        Root at right, children to left
    """

    DOWN = "down"
    UP = "up"
    RIGHT = "right"
    LEFT = "left"


@dataclass
class LayoutOptions:
    """Configuration options for graph layout and appearance.

    Core Spacing Parameters:
        node_spacing: Horizontal space between nodes (minimum 1)
        layer_spacing: Vertical space between layers (minimum 0)
        margin: General margin around the entire diagram

    Layout Control:
        node_style: Style for node representation (square, round, etc.)
        show_arrows: Whether to show direction arrows on edges
        use_ascii: Force ASCII output instead of Unicode

    Advanced Layout Control:
        left_padding: Extra space on left side of diagram (default 4)
        right_padding: Extra space on right side of diagram (default 4)
        min_edge_space: Minimum space needed between nodes for edge drawing (default 2)
        preserve_triangle_shape: Keep triangular layouts proportional (default True)
        triangle_height_ratio: Height to width ratio for triangles (default 0.866)
    """

    _instance_counter: int = 0  # Class variable for counting instances

    # Core parameters (existing)
    node_spacing: int = field(default=4)
    margin: int = field(default=1)
    layer_spacing: int = field(default=2)
    node_style: Union[NodeStyle, str, None] = None
    show_arrows: bool = True
    use_ascii: Optional[bool] = None
    custom_decorators: Optional[Dict[str, Tuple[str, str]]] = field(
        default_factory=dict
    )

    # New layout control parameters
    left_padding: int = field(default=4)
    right_padding: int = field(default=4)
    min_edge_space: int = field(default=2)
    preserve_triangle_shape: bool = field(default=True)
    triangle_height_ratio: float = field(default=0.866)  # sqrt(3)/2 for equilateral
    binary_tree_layout: bool = field(default=False)  # Use binary tree positioning
    layout_strategy: str = field(
        default="auto"
    )  # auto, bfs, bipartite, circular, hierarchical, planar, layered, kamada_kawai, spring, arf, spiral, shell, random, multipartite, vertical
    constrained: bool = field(default=False)
    target_canvas_width: Optional[int] = field(default=None)
    target_canvas_height: Optional[int] = field(default=None)
    partition_overlap: int = field(default=0)
    partition_affinity_strength: int = field(default=1)
    cross_partition_edge_style: str = field(default="stub")  # stub or none
    connector_compaction: str = field(default="none")  # none or partition
    partition_order: str = field(default="natural")  # natural or size
    panel_header_mode: str = field(default="basic")  # none, basic, or lineage
    connector_ref_mode: str = field(default="auto")  # auto, id, label, both
    node_order_mode: str = field(
        default="layout_default"
    )  # layout_default, preserve, alpha, natural, numeric
    node_order_attr: Optional[str] = field(default=None)
    node_order_reverse: bool = field(default=False)
    flow_direction: FlowDirection = field(default=FlowDirection.DOWN)
    bboxes: bool = field(default=False)  # Draw line-art boxes around nodes
    hpad: int = field(default=1)  # Horizontal inner padding for boxed nodes
    vpad: int = field(default=0)  # Vertical inner padding for boxed nodes
    uniform: bool = field(default=False)  # Use widest node text width for all boxes
    edge_anchor_mode: str = field(default="auto")  # auto, center, or ports
    shared_ports_mode: str = field(default="any")  # any, minimize, or none
    bidirectional_mode: str = field(default="coalesce")  # coalesce or separate
    use_labels: bool = field(default=False)  # Legacy alias: enable node+edge labels
    node_label_attr: Optional[str] = field(
        default=None
    )  # Node attribute name for display labels; None disables node labels
    edge_label_attr: Optional[str] = field(
        default=None
    )  # Edge attribute name for display labels; None disables edge labels
    node_label_lines: tuple[str, ...] = field(
        default_factory=tuple
    )  # Ordered attribute-path specs for synthesized labels
    node_label_sep: str = field(
        default=" "
    )  # Separator used when composing multi-value label line parts
    node_label_max_lines: Optional[int] = field(
        default=None
    )  # Optional cap for synthesized label lines
    bbox_multiline_labels: bool = field(
        default=False
    )  # Expand bbox height and paint multiline labels when enabled
    ansi_colors: bool = field(default=False)  # ANSI colorized render output
    allow_ansi_in_ascii: bool = field(
        default=False
    )  # Allow ANSI color escapes even when glyphs are ASCII
    # TODO:
    # We should probably introduce the concept of node_color_mode.
    # We already allow for coloring only of edges by  passing --no-color-nodes,
    # So we should probably full embrace the distinction and allow for separate
    # coloring rules for nodes and edges in "colors attr" mode.
    # and on that node, maybe --colors attr is an awkward implementation;
    # that is, maybe --colors should accept "", "none", "path", "node", "edge"
    # as the options and allow for --color-rules --edge-color-rules and --node-color-rules
    # to each accept a rule as currently implemented,  or "none" to allow for the default
    # --colors path|source|target to work, but for edges or nodes to be individually
    # affected by rules or "none"
    edge_color_mode: str = field(default="source")  # target, source, path, or attr
    edge_color_rules: Dict[str, Dict[str, str]] = field(
        default_factory=dict
    )  # attr mode rules: {"attr_name": {"attr_value": "color_spec"}}
    style_rules: List[Dict[str, Any]] = field(default_factory=list)
    edge_glyph_preset: str = field(default="default")  # default, thick, or double
    edge_arrow_style: str = field(default="ascii")  # ascii or unicode
    color_nodes: bool = field(default=True)
    whitespace_mode: str = field(
        default="auto"
    )  # auto, ascii_space, or nbsp for text output spacing

    # Instance-specific ID (unchanged)
    instance_id: int = field(init=False)

    # Edge characters with ASCII fallbacks
    edge_cross = EdgeChar("+", "┼")
    edge_vertical = EdgeChar("|", "│")
    edge_horizontal = EdgeChar("-", "─")
    # TODO:
    # Need to finish the custom edge_arrows, and custom edge-decoraators in general
    # rather than this that I have done. Mayhaps *somebody* likes the unicode arrows.
    #    edge_arrow_r = EdgeChar(">", "→")
    #    edge_arrow_l = EdgeChar("<", "←")
    edge_arrow_r = EdgeChar(">", ">")
    edge_arrow_l = EdgeChar("<", "<")
    #    edge_arrow_up = EdgeChar("^", "↑")
    #    edge_arrow_down = EdgeChar("v", "↓")
    edge_arrow_up = EdgeChar("^", "^")
    edge_arrow_down = EdgeChar("v", "v")
    edge_corner_ul = EdgeChar("+", "┌")
    edge_corner_ur = EdgeChar("+", "┐")
    edge_corner_ll = EdgeChar("+", "└")
    edge_corner_lr = EdgeChar("+", "┘")
    edge_tee_up = EdgeChar("+", "┴")
    edge_tee_down = EdgeChar("+", "┬")
    edge_tee_left = EdgeChar("+", "┤")
    edge_tee_right = EdgeChar("+", "├")
    box_top_left = EdgeChar("+", "┌")
    box_top_right = EdgeChar("+", "┐")
    box_bottom_left = EdgeChar("+", "└")
    box_bottom_right = EdgeChar("+", "┘")

    def __post_init__(self) -> None:
        """Validate and normalize configuration values."""
        self.instance_id = LayoutOptions._instance_counter
        LayoutOptions._instance_counter += 1
        # Track whether caller explicitly requested a non-default node style.
        self._node_style_explicit = self.node_style is not None

        if self.node_style is None:
            # Keep boxed mode compact by default unless style is explicitly requested.
            self.node_style = NodeStyle.MINIMAL if self.bboxes else NodeStyle.SQUARE
        elif isinstance(self.node_style, str):
            try:
                self.node_style = NodeStyle[self.node_style.upper()]
            except KeyError:
                valid_styles = ", ".join([style.name.lower() for style in NodeStyle])
                raise ValueError(
                    f"Invalid node style '{self.node_style}'. Valid options are: {valid_styles}"
                )

        val = self.flow_direction

        if isinstance(val, str):
            val = FlowDirection(val.strip().lower())

        if not isinstance(val, FlowDirection):
            try:
                val = FlowDirection(val)
            except ValueError as e:
                valid = ", ".join(d.value for d in FlowDirection)
                raise ValueError(
                    f"Invalid flow_direction: {self.flow_direction}. Valid: {valid}"
                ) from e

        self.flow_direction = val

        if self.node_style == NodeStyle.CUSTOM and not self.custom_decorators:
            raise ValueError(
                "Custom decorators must be provided when using NodeStyle.CUSTOM"
            )
        if self.node_style == NodeStyle.BBOX:
            self.bboxes = True
            # "bbox" style alias means boxed nodes with minimal inner decorators.
            self.node_style = NodeStyle.MINIMAL

        # Validate core spacing parameters
        if self.node_spacing < 1:
            raise ValueError("node_spacing must be at least 1")
        if self.layer_spacing < 0:
            raise ValueError("layer_spacing must be non-negative")
        if self.layer_spacing <= 1:
            self.layer_spacing = 1
        if self.margin < 1:
            raise ValueError("margin must be >= 1")

        # Validate new parameters
        if self.left_padding < 0:
            raise ValueError("left_padding must be non-negative")
        if self.right_padding < 0:
            raise ValueError("right_padding must be non-negative")
        if self.min_edge_space < 1:
            raise ValueError("min_edge_space must be at least 1")
        if self.triangle_height_ratio <= 0:
            raise ValueError("triangle_height_ratio must be positive")
        if self.hpad < 0:
            raise ValueError("hpad must be non-negative")
        if self.vpad < 0:
            raise ValueError("vpad must be non-negative")

        if isinstance(self.edge_anchor_mode, str):
            self.edge_anchor_mode = self.edge_anchor_mode.strip().lower()
        if self.edge_anchor_mode not in {"auto", "center", "ports"}:
            raise ValueError("edge_anchor_mode must be one of: auto, center, ports")

        if isinstance(self.shared_ports_mode, str):
            self.shared_ports_mode = self.shared_ports_mode.strip().lower()
        if self.shared_ports_mode not in {"any", "minimize", "none"}:
            raise ValueError("shared_ports_mode must be one of: any, minimize, none")

        if isinstance(self.bidirectional_mode, str):
            self.bidirectional_mode = self.bidirectional_mode.strip().lower()
        if self.bidirectional_mode not in {"coalesce", "separate"}:
            raise ValueError("bidirectional_mode must be one of: coalesce, separate")

        if isinstance(self.layout_strategy, str):
            self.layout_strategy = (
                self.layout_strategy.strip().lower().replace("-", "_")
            )
        if self.layout_strategy not in {
            "auto",
            "bfs",
            "bipartite",
            "circular",
            "planar",
            "kamada_kawai",
            "spring",
            "arf",
            "spiral",
            "shell",
            "random",
            "multipartite",
            "hierarchical",
            "vertical",
            "layered",
        }:
            raise ValueError(
                "layout_strategy must be one of: legacy, bfs, bipartite, circular, hierarchical, layered, "
                "planar, kamada_kawai, spring, arf, spiral, shell, random, multipartite, vertical"
            )
        if self.target_canvas_width is not None:
            if self.target_canvas_width <= 0:
                raise ValueError("target_canvas_width must be greater than zero")
        if self.target_canvas_height is not None:
            if self.target_canvas_height <= 0:
                raise ValueError("target_canvas_height must be greater than zero")
        if self.partition_overlap < 0:
            raise ValueError("partition_overlap must be non-negative")
        if self.partition_affinity_strength < 0:
            raise ValueError("partition_affinity_strength must be non-negative")
        if isinstance(self.cross_partition_edge_style, str):
            self.cross_partition_edge_style = (
                self.cross_partition_edge_style.strip().lower()
            )
        if self.cross_partition_edge_style not in {"stub", "none"}:
            raise ValueError("cross_partition_edge_style must be one of: stub, none")
        if isinstance(self.connector_compaction, str):
            self.connector_compaction = self.connector_compaction.strip().lower()
        if self.connector_compaction not in {"none", "partition"}:
            raise ValueError("connector_compaction must be one of: none, partition")
        if isinstance(self.partition_order, str):
            self.partition_order = self.partition_order.strip().lower()
        if self.partition_order not in {"natural", "size"}:
            raise ValueError("partition_order must be one of: natural, size")
        if isinstance(self.panel_header_mode, str):
            self.panel_header_mode = self.panel_header_mode.strip().lower()
        if self.panel_header_mode not in {"none", "basic", "lineage"}:
            raise ValueError("panel_header_mode must be one of: none, basic, lineage")
        if isinstance(self.connector_ref_mode, str):
            self.connector_ref_mode = self.connector_ref_mode.strip().lower()
        if self.connector_ref_mode not in {"auto", "id", "label", "both"}:
            raise ValueError("connector_ref_mode must be one of: auto, id, label, both")
        if self.constrained and self.target_canvas_width is None:
            raise ValueError("constrained layout requires target_canvas_width")

        if isinstance(self.node_order_mode, str):
            self.node_order_mode = (
                self.node_order_mode.strip().lower().replace("-", "_")
            )
        if self.node_order_mode not in {
            "layout_default",
            "preserve",
            "alpha",
            "natural",
            "numeric",
        }:
            raise ValueError(
                "node_order_mode must be one of: layout_default, preserve, alpha, natural, numeric"
            )

        if self.node_order_attr is not None:
            self.node_order_attr = str(self.node_order_attr).strip()
            if not self.node_order_attr:
                self.node_order_attr = None

        if isinstance(self.edge_color_mode, str):
            self.edge_color_mode = self.edge_color_mode.strip().lower()
        if self.edge_color_mode not in {"target", "source", "path", "attr"}:
            raise ValueError(
                "edge_color_mode must be one of: target, source, path, attr"
            )
        if isinstance(self.edge_glyph_preset, str):
            self.edge_glyph_preset = self.edge_glyph_preset.strip().lower()
        if self.edge_glyph_preset not in {"default", "thick", "double"}:
            raise ValueError("edge_glyph_preset must be one of: default, thick, double")
        if isinstance(self.edge_arrow_style, str):
            self.edge_arrow_style = self.edge_arrow_style.strip().lower()
        if self.edge_arrow_style not in {"ascii", "unicode"}:
            raise ValueError("edge_arrow_style must be one of: ascii, unicode")
        if self.use_ascii and self.edge_arrow_style == "unicode":
            # Unicode arrows are not guaranteed visible in ASCII mode.
            self.edge_arrow_style = "ascii"

        if isinstance(self.whitespace_mode, str):
            self.whitespace_mode = (
                self.whitespace_mode.strip().lower().replace("-", "_")
            )
        if self.whitespace_mode not in {"auto", "ascii_space", "nbsp"}:
            raise ValueError("whitespace_mode must be one of: auto, ascii_space, nbsp")

        self.node_label_attr = self._normalize_label_attr_name(self.node_label_attr)
        self.edge_label_attr = self._normalize_label_attr_name(self.edge_label_attr)
        if self.use_labels:
            if self.node_label_attr is None:
                self.node_label_attr = "label"
            if self.edge_label_attr is None:
                self.edge_label_attr = "label"
        self.use_labels = bool(self.node_label_attr or self.edge_label_attr)

        if self.node_label_max_lines is not None and self.node_label_max_lines < 1:
            raise ValueError("node_label_max_lines must be >= 1 when provided")

        if not isinstance(self.node_label_sep, str):
            self.node_label_sep = str(self.node_label_sep)

        normalized_label_lines: list[str] = []
        for raw in self.node_label_lines:
            spec = str(raw).strip()
            if spec:
                normalized_label_lines.append(spec)
        self.node_label_lines = tuple(normalized_label_lines)

        if not isinstance(self.edge_color_rules, dict):
            raise ValueError("edge_color_rules must be a dict of dicts")

        normalized_rules: Dict[str, Dict[str, str]] = {}
        for attr_name, value_map in self.edge_color_rules.items():
            attr_key = str(attr_name).strip().lower()
            if not attr_key:
                raise ValueError("edge_color_rules attribute names cannot be empty")
            if not isinstance(value_map, dict):
                raise ValueError("edge_color_rules values must be dicts")

            normalized_value_map: Dict[str, str] = {}
            for attr_value, color_spec in value_map.items():
                value_key = self._normalize_edge_color_rule_value(attr_value)
                color_text = str(color_spec).strip()
                if not value_key:
                    raise ValueError(
                        "edge_color_rules attribute values cannot be empty"
                    )
                if not color_text:
                    raise ValueError("edge_color_rules color values cannot be empty")
                normalized_value_map.setdefault(value_key, color_text)

            if normalized_value_map:
                normalized_rules[attr_key] = normalized_value_map
        self.edge_color_rules = normalized_rules
        if not isinstance(self.style_rules, list):
            raise ValueError("style_rules must be a list of dicts")
        self._compiled_style_rules: List[CompiledStyleRule] = compile_style_rules(
            self.style_rules
        )

    @staticmethod
    def _normalize_edge_color_rule_value(value: Any) -> str:
        """Normalize edge attribute values for rule matching."""
        text = str(value).strip()
        if len(text) >= 2 and text[0] == text[-1] and text[0] in {"'", '"'}:
            text = text[1:-1]
        return text.strip().lower()

    @staticmethod
    def _normalize_label_attr_name(value: Optional[Any]) -> Optional[str]:
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None
        if text.lower() == "none":
            return None
        return text

    def get_effective_node_spacing(self, has_edges: bool = True) -> int:
        """Calculate effective node spacing considering edge requirements.

        Args:
            has_edges: Whether the nodes being spaced have edges between them

        Returns:
            Effective spacing to use between nodes
        """
        if not has_edges:
            return self.node_spacing
        return max(self.node_spacing, self.min_edge_space)

    def get_paddings(self) -> Tuple[int, int]:
        """Get left and right padding values.

        Returns:
            Tuple of (left_padding, right_padding)
        """
        return self.left_padding, self.right_padding

    def get_arrow_for_direction(self, base_direction: str) -> str:
        """Get the arrow glyph for a geometric direction.

        Direction glyphs are selected from the rendered edge geometry only.
        Layout flow has already been applied to node positions, so applying
        another flow-based rotation here would incorrectly double-transform
        arrow orientation.
        """
        arrow_map = {
            "up": self.get_edge_glyph("arrow_up", self.edge_arrow_up),
            "down": self.get_edge_glyph("arrow_down", self.edge_arrow_down),
            "left": self.get_edge_glyph("arrow_left", self.edge_arrow_l),
            "right": self.get_edge_glyph("arrow_right", self.edge_arrow_r),
        }
        try:
            return arrow_map[base_direction]
        except KeyError as e:
            valid = ", ".join(sorted(arrow_map))
            raise ValueError(
                f"Invalid arrow direction '{base_direction}'. Valid: {valid}"
            ) from e

    def get_edge_glyph_defaults(self) -> Dict[str, str]:
        """Return global edge glyph defaults after preset + arrow style."""
        defaults: Dict[str, str] = {}
        if not self.use_ascii:
            if self.edge_glyph_preset == "thick":
                defaults.update(
                    {
                        "line_horizontal": "━",
                        "line_vertical": "┃",
                        "corner_ul": "┏",
                        "corner_ur": "┓",
                        "corner_ll": "┗",
                        "corner_lr": "┛",
                        "tee_up": "┻",
                        "tee_down": "┳",
                        "tee_left": "┫",
                        "tee_right": "┣",
                        "cross": "╋",
                    }
                )
            elif self.edge_glyph_preset == "double":
                defaults.update(
                    {
                        "line_horizontal": "═",
                        "line_vertical": "║",
                        "corner_ul": "╔",
                        "corner_ur": "╗",
                        "corner_ll": "╚",
                        "corner_lr": "╝",
                        "tee_up": "╩",
                        "tee_down": "╦",
                        "tee_left": "╣",
                        "tee_right": "╠",
                        "cross": "╬",
                    }
                )
        if self.edge_arrow_style == "unicode" and not self.use_ascii:
            defaults.update(
                {
                    "arrow_up": "↑",
                    "arrow_down": "↓",
                    "arrow_left": "←",
                    "arrow_right": "→",
                }
            )
        return defaults

    def get_edge_glyph(self, key: str, fallback: Optional[str] = None) -> str:
        """Resolve a global edge glyph by key with optional fallback."""
        defaults = self.get_edge_glyph_defaults()
        if key in defaults:
            return defaults[key]
        if fallback is not None:
            return fallback
        raise ValueError(f"Unknown edge glyph key '{key}'")

    def __str__(self) -> str:
        # Get all dataclass fields and their current values from this instance
        return f"""LayoutOptions: {
            ", ".join(
                f"{field.name}={getattr(self, field.name)}" for field in fields(self)
            )
        }"""

    def get_node_decorators(self, node_str: str) -> Tuple[str, str]:
        """
        Retrieve decorators for a specific node.

        Parameters
        ----------
        node_str : str
            The string representation of the node.

        Returns
        -------
        Tuple[str, str]
            A tuple containing the prefix and suffix for the node.
        """
        # print(f"DBG TRACE: Entering get_node_decorators for node '{node_str}'")

        # print(f"DBG TRACE: Type self = {type(self)}")

        current_style = (
            self.node_style.node_style
            if isinstance(self.node_style, LayoutOptions)
            else self.node_style
        )

        # print(f"DBG TRACE: After extraction, current_style = {current_style}")
        # print(f"DBG TRACE: Type of current_style = {type(current_style)}")

        # Now check if we're in custom mode
        if current_style == NodeStyle.CUSTOM:
            if not self.custom_decorators:
                raise ValueError(
                    "Custom decorators must be provided when using NodeStyle.CUSTOM"
                )
            return self.custom_decorators.get(node_str, ("*", "*"))

        # For standard styles, use pattern matching
        match current_style:
            case NodeStyle.MINIMAL:
                return "", ""
            case NodeStyle.SQUARE:
                return "[", "]"
            case NodeStyle.ROUND:
                return "(", ")"
            case NodeStyle.DIAMOND:
                return "<", ">"
            case _:
                return "[", "]"  # Default to square brackets

    def get_node_text(self, node_str: str) -> str:
        """Get the full rendered node text including decorators."""
        prefix, suffix = self.get_node_decorators(node_str)
        return f"{prefix}{node_str}{suffix}"

    def get_node_height(self, *, content_lines: int = 1) -> int:
        """Get rendered node height in rows."""
        if not self.bboxes:
            return 1
        # top border + bottom border + content rows + optional vertical padding rows
        return (2 * self.vpad) + 2 + max(1, content_lines)

    def get_node_dimensions(
        self, node_str: str, widest_text_width: Optional[int] = None
    ) -> Tuple[int, int]:
        """Get rendered node width/height for a given node text."""
        multiline = self.bboxes and self.bbox_multiline_labels
        raw_lines = node_str.split("\n") if multiline else [node_str]
        rendered_lines = [self.get_node_text(line) for line in raw_lines]
        text_width = max(
            (self.get_text_display_width(line) for line in rendered_lines),
            default=0,
        )
        if self.bboxes and self.uniform and widest_text_width is not None:
            text_width = max(text_width, widest_text_width)

        if not self.bboxes:
            return text_width, 1

        width = text_width + (2 * self.hpad) + 2  # left/right border columns
        content_lines = len(rendered_lines) if multiline else 1
        return width, self.get_node_height(content_lines=content_lines)

    @staticmethod
    def get_char_display_width(char: str) -> int:
        """Return terminal display width for a single Unicode codepoint."""
        if not char:
            return 0

        if unicodedata.combining(char):
            return 0

        if unicodedata.east_asian_width(char) in {"F", "W"}:
            return 2

        category = unicodedata.category(char)
        if category in {"Cc", "Cf"}:
            return 0

        return 1

    @classmethod
    def get_text_display_width(cls, text: str) -> int:
        """Return terminal display width for text in monospace columns."""
        return sum(cls.get_char_display_width(ch) for ch in text)

    def resolve_padding_char(self, *, markdown_safe: bool = False) -> str:
        """Resolve output padding character for text rendering."""
        if self.whitespace_mode == "ascii_space":
            return " "
        if self.whitespace_mode == "nbsp":
            return "\u00a0"
        return "\u00a0" if markdown_safe else " "
