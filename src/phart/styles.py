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


@dataclass
class LayoutOptions:
    """Configuration options for graph layout and appearance."""

    _instance_counter = 0  # Class variable for counting instances

    node_spacing: int = field(default=4)
    margin: int = field(default=1)
    layer_spacing: int = field(default=2)
    node_style: Union[NodeStyle, str] = NodeStyle.SQUARE
    show_arrows: bool = True
    use_ascii: Optional[bool] = None
    custom_decorators: Optional[Dict[str, Tuple[str, str]]] = field(
        default_factory=dict
    )
    instance_id: int = field(init=False)  # Instance-specific ID

    # Edge characters with ASCII fallbacks
    edge_vertical = EdgeChar("|", "│")
    edge_horizontal = EdgeChar("-", "─")
    edge_cross = EdgeChar("+", "┼")
    edge_arrow_r = EdgeChar(">", "→")
    edge_arrow_l = EdgeChar("<", "←")
    edge_arrow_up = EdgeChar("^", "↑")
    edge_arrow_down = EdgeChar("v", "↓")

    def __str__(self) -> str:
        # Get all dataclass fields and their current values from this instance
        return f"""LayoutOptions: {', '.join(
            f"{field.name}={getattr(self, field.name)}"
            for field in fields(self)
        )}"""

    def __post_init__(self) -> None:
        """Validate and normalize configuration values."""
        self.instance_id = LayoutOptions._instance_counter
        LayoutOptions._instance_counter += 1

        # print(f"DBG TRACE: LayoutOptions instance {self.instance_id} created with:")
        # print(f"DBG TRACE: - node_style: {self.node_style}")
        # print(f"DBG TRACE: - custom_decorators: {self.custom_decorators}")

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
            # for node, (prefix, suffix) in self.custom_decorators.items():
            #    print(
            #        f"Node '{node}' will be decorated with prefix '{prefix}' and suffix '{suffix}'."
            #    )

        if self.node_spacing <= 0:
            raise ValueError("node_spacing must be positive")
        if self.layer_spacing < 0:
            raise ValueError("layer_spacing must be positive")
        if self.margin <= 0:
            raise ValueError("margin must be > = 1")

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
