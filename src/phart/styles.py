from dataclasses import dataclass, field
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


@dataclass
class LayoutOptions:
    """Configuration options for graph layout and appearance."""

    node_spacing: int = field(default=4)
    layer_spacing: int = field(default=2)
    node_style: Union[NodeStyle, str] = NodeStyle.SQUARE
    show_arrows: bool = True
    use_ascii: Optional[bool] = None
    custom_decorators: Optional[Dict[str, Tuple[str, str]]] = field(
        default_factory=dict
    )

    # Edge characters with ASCII fallbacks
    edge_vertical = EdgeChar("|", "│")
    edge_horizontal = EdgeChar("-", "─")
    edge_cross = EdgeChar("+", "┼")
    edge_arrow = EdgeChar(">", "→")
    edge_arrow_up = EdgeChar("^", "↑")
    edge_arrow_down = EdgeChar("v", "↓")

    def __post_init__(self) -> None:
        """Validate and normalize configuration values."""
        if isinstance(self.node_style, str):
            try:
                # Convert string to NodeStyle enum
                self.node_style = NodeStyle[self.node_style.upper()]
            except KeyError:
                valid_styles = ", ".join([style.name.lower() for style in NodeStyle])
                raise ValueError(
                    f"Invalid node style '{self.node_style}'. Valid options are: {valid_styles}"
                )

        if self.node_style == NodeStyle.CUSTOM:
            # Ensure custom decorators are handled correctly
            if not self.custom_decorators:
                raise ValueError(
                    "Custom decorators must be provided when using NodeStyle.CUSTOM"
                )

            # Ensure decorators are applied as needed (e.g., handle defaults if any node doesn't have a decorator)
            # maybe set up default values for missing nodes or some such..
            for node, (prefix, suffix) in self.custom_decorators.items():
                print(
                    f"Node '{node}' will be decorated with prefix '{prefix}' and suffix '{suffix}'."
                )

        if self.node_spacing <= 0:
            raise ValueError("node_spacing must be positive")
        if self.layer_spacing <= 0:
            raise ValueError("layer_spacing must be positive")

    def get_node_decorators(self, node_str: str) -> Tuple[str, str]:
        """Retrieve decorators for a specific node.

        Parameters
        ----------
        node_str : str
            The string representation of the node.

        Returns
        -------
        Tuple[str, str]
            A tuple containing the prefix and suffix for the node.
        """
        if self.node_style == NodeStyle.CUSTOM:
            # Ensure custom decorators are handled correctly
            if not self.custom_decorators:
                raise ValueError(
                    "Custom decorators must be provided when using NodeStyle.CUSTOM"
                )
                # return '', ''
            else:
                return (
                    self.custom_decorators[node_str]
                    if self.custom_decorators[node_str]
                    else ("", "")
                )

        # Fallback to default styles if not CUSTOM
        match self.node_style:
            case NodeStyle.SQUARE:
                return "[", "]"
            case NodeStyle.ROUND:
                return "(", ")"
            case NodeStyle.DIAMOND:
                return "<", ">"
            case NodeStyle.MINIMAL:
                return "", ""
            case _:
                return "[", "]"  # Default to square brackets
