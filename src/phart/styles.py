# src path: src\phart\styles.py
from dataclasses import dataclass, field, fields
from typing import Tuple, Any, Optional, Union, Dict
from enum import Enum


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

    _instance_counter = 0  # Class variable for counting instances

    # Core parameters (existing)
    node_spacing: int = field(default=4)
    margin: int = field(default=1)
    layer_spacing: int = field(default=3)
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
    flow_direction: FlowDirection = field(default=FlowDirection.DOWN)
    bboxes: bool = field(default=False)  # Draw line-art boxes around nodes
    hpad: int = field(default=1)  # Horizontal inner padding for boxed nodes
    vpad: int = field(default=0)  # Vertical inner padding for boxed nodes
    uniform: bool = field(default=False)  # Use widest node text width for all boxes
    edge_anchor_mode: str = field(default="center")  # center or ports

    # Instance-specific ID (unchanged)
    instance_id: int = field(init=False)

    # Edge characters with ASCII fallbacks
    edge_cross = EdgeChar("+", "┼")
    edge_vertical = EdgeChar("|", "│")
    edge_horizontal = EdgeChar("-", "─")
    edge_arrow_r = EdgeChar(">", "→")
    edge_arrow_l = EdgeChar("<", "←")
    edge_arrow_up = EdgeChar("^", "↑")
    edge_arrow_down = EdgeChar("v", "↓")
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

        # Validate core spacing parameters
        if self.node_spacing < 1:
            raise ValueError("node_spacing must be at least 1")
        if self.layer_spacing < 0:
            raise ValueError("layer_spacing must be non-negative")
        if self.layer_spacing < 3:
            self.layer_spacing = 4
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
        if self.edge_anchor_mode not in {"center", "ports"}:
            raise ValueError("edge_anchor_mode must be one of: center, ports")

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
            "up": self.edge_arrow_up,
            "down": self.edge_arrow_down,
            "left": self.edge_arrow_l,
            "right": self.edge_arrow_r,
        }
        try:
            return arrow_map[base_direction]
        except KeyError as e:
            valid = ", ".join(sorted(arrow_map))
            raise ValueError(
                f"Invalid arrow direction '{base_direction}'. Valid: {valid}"
            ) from e

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

    def get_node_height(self) -> int:
        """Get rendered node height in rows."""
        if not self.bboxes:
            return 1
        # top border + bottom border + content row + optional vertical padding rows
        return (2 * self.vpad) + 3

    def get_node_dimensions(
        self, node_str: str, widest_text_width: Optional[int] = None
    ) -> Tuple[int, int]:
        """Get rendered node width/height for a given node text."""
        text_width = len(self.get_node_text(node_str))
        if self.bboxes and self.uniform and widest_text_width is not None:
            text_width = max(text_width, widest_text_width)

        if not self.bboxes:
            return text_width, 1

        width = text_width + (2 * self.hpad) + 2  # left/right border columns
        return width, self.get_node_height()
