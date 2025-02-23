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


# In styles.py


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
    layer_spacing: int = field(default=2)
    node_style: Union[NodeStyle, str] = NodeStyle.SQUARE
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

    # Instance-specific ID (unchanged)
    instance_id: int = field(init=False)

    # Edge characters with ASCII fallbacks
    edge_cross = EdgeChar(
        "+", "+"
    )  # '┼' seems unnecessarily large, and will be replaced by proper corner chars soon
    edge_vertical = EdgeChar("|", "│")
    edge_horizontal = EdgeChar("-", "─")
    edge_arrow_r = EdgeChar(">", "→")
    edge_arrow_l = EdgeChar("<", "←")
    edge_arrow_up = EdgeChar("^", "↑")
    edge_arrow_down = EdgeChar("v", "↓")

    def __post_init__(self) -> None:
        """Validate and normalize configuration values."""
        self.instance_id = LayoutOptions._instance_counter
        LayoutOptions._instance_counter += 1

        if isinstance(self.node_style, str):
            try:
                self.node_style = NodeStyle[self.node_style.upper()]
            except KeyError:
                valid_styles = ", ".join([style.name.lower() for style in NodeStyle])
                raise ValueError(
                    f"Invalid node style '{self.node_style}'. Valid options are: {valid_styles}"
                )

        if self.node_style == NodeStyle.CUSTOM and not self.custom_decorators:
            raise ValueError(
                "Custom decorators must be provided when using NodeStyle.CUSTOM"
            )

        # Validate core spacing parameters
        if self.node_spacing < 1:
            raise ValueError("node_spacing must be at least 1")
        if self.layer_spacing < 0:
            raise ValueError("layer_spacing must be non-negative")
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

    def __str__(self) -> str:
        # Get all dataclass fields and their current values from this instance
        return f"""LayoutOptions: {', '.join(
            f"{field.name}={getattr(self, field.name)}"
            for field in fields(self)
        )}"""

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
