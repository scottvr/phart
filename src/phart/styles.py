"""Style and configuration options for PHART rendering."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Tuple, Any


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


def make_ascii_property(name: str, ascii_char: str, unicode_char: str) -> property:
    """Create a property that handles ASCII fallback for edge characters."""
    private_name = f"_{name}"

    def getter(self: Any) -> str:
        return ascii_char if self.use_ascii else unicode_char

    def setter(self: Any, value: str) -> None:
        setattr(self, private_name, value)

    return property(getter, setter)


@dataclass
class LayoutOptions:
    """
    Configuration options for graph layout and appearance.

    Parameters
    ----------
    node_spacing : int, optional (default=4)
        Minimum horizontal space between nodes
    layer_spacing : int, optional (default=2)
        Number of rows between layers
    edge_vertical : str, optional (default='│')
        Character used for vertical edges
    edge_horizontal : str, optional (default='─')
        Character used for horizontal edges
    edge_cross : str, optional (default='┼')
        Character used where edges cross
    edge_arrow : str, optional (default='>')
        Character used for horizontal arrow heads
    edge_arrow_up : str, optional (default='^')
        Character used for upward arrow heads
    edge_arrow_down : str, optional (default='v')
        Character used for downward arrow heads
    node_style : NodeStyle, optional (default=NodeStyle.SQUARE)
        Style enum determining node appearance

    Notes
    -----
    All edge characters should be single characters. For best results,
    use Unicode box-drawing characters.

    Examples
    --------
    >>> options = LayoutOptions(
    ...     node_spacing=6,
    ...     edge_vertical='|',
    ...     node_style=NodeStyle.ROUND
    ... )
    """

    node_spacing: int = 4
    layer_spacing: int = 2
    node_style: NodeStyle = NodeStyle.SQUARE
    show_arrows: bool = True
    use_ascii: bool = False  # If True, use ASCII-only characters

    _edge_vertical: str = field(default="|", init=False)
    _edge_horizontal: str = field(default="─", init=False)
    _edge_cross: str = field(default="┼", init=False)
    _edge_arrow: str = field(default=">", init=False)
    _edge_arrow_up: str = field(default="^", init=False)
    _edge_arrow_down: str = field(default="v", init=False)

    # Generate properties
    edge_vertical = make_ascii_property("edge_vertical", "|", "│")
    edge_horizontal = make_ascii_property("edge_horizontal", "-", "─")
    edge_cross = make_ascii_property("edge_cross", "+", "┼")
    edge_arrow = make_ascii_property("edge_arrow", ">", "→")
    edge_arrow_up = make_ascii_property("edge_arrow_up", "^", "↑")
    edge_arrow_down = make_ascii_property("edge_arrow_down", "v", "↓")

    def __post_init__(self) -> None:
        """Validate configuration values after initialization."""
        if self.node_spacing <= 0:
            raise ValueError("node_spacing must be positive")
        if self.layer_spacing <= 0:
            raise ValueError("layer_spacing must be positive")
        if not isinstance(self.node_style, NodeStyle):
            raise TypeError("node_style must be a NodeStyle enum value")

    def get_node_decorators(self, node_str: str) -> Tuple[str, str]:
        """
        Get the prefix and suffix decorators for a node based on style.

        Parameters
        ----------
        node_str : str
            Node identifier to be decorated

        Returns
        -------
        tuple
            (prefix, suffix) pair of strings
        """

        style_decorators = {
            NodeStyle.SQUARE: ("[", "]"),
            NodeStyle.ROUND: ("(", ")"),
            NodeStyle.DIAMOND: ("<", ">"),
            NodeStyle.MINIMAL: ("", ""),
        }
        return style_decorators.get(
            self.node_style, ("[", "]")
        )  # Default to square brackets
