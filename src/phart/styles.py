from enum import Enum
from dataclasses import dataclass

class NodeStyle(Enum):
    """Different styles for node representation"""
    SQUARE = 1      # [Node]
    ROUND = 2       # (Node)
    DIAMOND = 3     # <Node>
    MINIMAL = 4     # Node

@dataclass
class LayoutOptions:
    """Configuration for graph layout and appearance"""
    # Node layout options
    node_spacing: int = 4      # Minimum horizontal space between nodes
    layer_spacing: int = 2     # Number of rows between layers

    # Edge drawing characters
    edge_vertical: str = '│'   # Character for vertical edges
    edge_horizontal: str = '─'  # Character for horizontal edges
    edge_cross: str = '┼'      # Character where edges cross
    edge_arrow: str = '>'      # Character for arrow heads
    edge_arrow_up: str = '^'   # Character for upward arrows
    edge_arrow_down: str = 'v'  # Character for downward arrows

    # Node appearance
    node_style: NodeStyle = NodeStyle.SQUARE

    def get_node_decorators(self, node_str: str) -> tuple[str, str]:
        """Get the prefix and suffix decorators for a node based on style"""
        match self.node_style:
            case NodeStyle.SQUARE:
                return '[', ']'
            case NodeStyle.ROUND:
                return '(', ')'
            case NodeStyle.DIAMOND:
                return '<', '>'
            case NodeStyle.MINIMAL:
                return '', ''
            case _:
                return '[', ']'  # Default to square brackets
