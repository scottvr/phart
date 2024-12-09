from dataclasses import dataclass, field
from typing import Tuple, Any, Optional
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


@dataclass
class LayoutOptions:
    """Configuration options for graph layout and appearance."""

    # Core layout options
    node_spacing: int = field(default=4)
    layer_spacing: int = field(default=2)
    node_style: NodeStyle = NodeStyle.SQUARE
    show_arrows: bool = True
    use_ascii: bool = False

    # Edge characters with ASCII fallbacks
    edge_vertical = EdgeChar("|", "│")
    edge_horizontal = EdgeChar("-", "─")
    edge_cross = EdgeChar("+", "┼")
    edge_arrow = EdgeChar(">", "→")
    edge_arrow_up = EdgeChar("^", "↑")
    edge_arrow_down = EdgeChar("v", "↓")

    def __post_init__(self) -> None:
        """Validate configuration values after initialization."""
        if self.node_spacing <= 0:
            raise ValueError("node_spacing must be positive")
        if self.layer_spacing <= 0:
            raise ValueError("layer_spacing must be positive")

    def get_node_decorators(self, node_str: str) -> Tuple[str, str]:
        style_decorators = {
            NodeStyle.SQUARE: ("[", "]"),
            NodeStyle.ROUND: ("(", ")"),
            NodeStyle.DIAMOND: ("<", ">"),
            NodeStyle.MINIMAL: ("", ""),
        }
        return style_decorators.get(self.node_style, style_decorators[NodeStyle.SQUARE])
