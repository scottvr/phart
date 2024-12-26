"""SVG support for PHART (Python Hierarchical ASCII Rendering Tool)."""

import xml.etree.ElementTree as ET
from typing import Dict, Tuple, Optional, List
import networkx as nx

from .renderer import ASCIIRenderer
from .styles import NodeStyle, LayoutOptions


class SVGParser:
    """Parser for converting SVG computational graphs to NetworkX format."""

    def __init__(self):
        self.namespaces = {
            "svg": "http://www.w3.org/2000/svg",
            "xlink": "http://www.w3.org/1999/xlink",
        }

        self.style_mapping = {
            "circle": NodeStyle.ROUND,
            "rect": NodeStyle.SQUARE,
            "polygon": NodeStyle.DIAMOND,
            "default": NodeStyle.MINIMAL,
        }

    def _extract_node_info(self, element: ET.Element) -> Dict:
        """Extract node information from SVG element."""
        tag = element.tag.split("}")[-1]  # Remove namespace

        info = {
            "id": self._extract_node_id(element),
            "style": self.style_mapping.get(tag, self.style_mapping["default"]),
        }

        if tag == "circle":
            info.update(
                {
                    "x": float(element.get("cx", 0)),
                    "y": float(element.get("cy", 0)),
                    "size": float(element.get("r", 1)),
                }
            )
        elif tag == "rect":
            info.update(
                {
                    "x": float(element.get("x", 0)),
                    "y": float(element.get("y", 0)),
                    "width": float(element.get("width", 1)),
                    "height": float(element.get("height", 1)),
                }
            )

        return info

    def _find_closest_node(
        self, point: Tuple[float, float], nodes: Dict
    ) -> Optional[str]:
        """Find the node closest to the given point."""
        min_distance = float("inf")
        closest_node = None

        for node_id, info in nodes.items():
            if "x" in info:
                node_x, node_y = info["x"], info["y"]
                distance = ((point[0] - node_x) ** 2 + (point[1] - node_y) ** 2) ** 0.5
                if distance < min_distance:
                    min_distance = distance
                    closest_node = node_id

        return closest_node

    def _extract_node_id(self, element: ET.Element) -> str:
        """Extract node identifier from SVG element."""
        return element.get("id") or f"node_{hash(element)}"

    def _parse_path_data(self, d: str) -> List[Tuple[str, List[float]]]:
        """Parse SVG path data into command sequences."""
        import re

        commands = []
        current_cmd = None
        numbers = []

        for token in re.findall(
            r"[A-Za-z]|[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?", d
        ):
            if token.isalpha():
                if current_cmd:
                    commands.append((current_cmd, numbers))
                    numbers = []
                current_cmd = token
            else:
                numbers.append(float(token))

        if current_cmd and numbers:
            commands.append((current_cmd, numbers))

        return commands

    def _extract_edges(
        self, path_element: ET.Element, nodes: Dict
    ) -> List[Tuple[str, str]]:
        """Extract edge information from SVG path element."""
        edges = []
        d = path_element.get("d", "")
        if not d:
            return edges

        commands = self._parse_path_data(d)
        current_point = None

        for cmd, params in commands:
            if cmd == "M":
                current_point = (params[0], params[1])
            elif cmd in ("L", "l"):
                start_point = current_point
                # Convert relative coordinates if needed
                if cmd == "l":
                    end_point = (
                        current_point[0] + params[0],
                        current_point[1] + params[1],
                    )
                else:
                    end_point = (params[0], params[1])

                # Find actual node IDs based on coordinates
                start_node = self._find_closest_node(start_point, nodes)
                end_node = self._find_closest_node(end_point, nodes)

                if start_node and end_node:
                    edges.append((start_node, end_node))

                current_point = end_point

        return edges

    def parse_svg(self, svg_content: str) -> Tuple[nx.DiGraph, LayoutOptions]:
        """Parse SVG content into a NetworkX graph with layout options."""
        root = ET.fromstring(svg_content)
        graph = nx.DiGraph()

        # Parse viewBox for scaling information
        # viewbox = self._parse_viewbox(root)

        # Extract nodes first
        nodes = {}
        for element in root.findall(".//*"):
            tag = element.tag.split("}")[-1]
            if tag in ("circle", "rect", "polygon"):
                node_info = self._extract_node_info(element)
                nodes[node_info["id"]] = node_info
                graph.add_node(node_info["id"], **node_info)

        # Extract edges from paths using node information
        for path in root.findall(".//svg:path", self.namespaces):
            edges = self._extract_edges(path, nodes)  # Pass nodes dictionary here
            graph.add_edges_from(edges)

        # Create layout options based on SVG properties
        options = LayoutOptions(
            node_spacing=4,
            layer_spacing=2,
            node_style=NodeStyle.CUSTOM,
            custom_decorators={
                node_id: self._get_decorators(info["style"])
                for node_id, info in nodes.items()
            },
        )

        return graph, options

    def _parse_viewbox(self, root: ET.Element) -> Tuple[float, float, float, float]:
        """Parse SVG viewBox attribute."""
        viewbox = root.get("viewBox")
        if viewbox:
            return tuple(map(float, viewbox.split()))
        return (
            0.0,
            0.0,
            float(root.get("width", "100")),
            float(root.get("height", "100")),
        )

    def _get_decorators(self, style: NodeStyle) -> Tuple[str, str]:
        """Get appropriate decorators for node style."""
        match style:
            case NodeStyle.ROUND:
                return ("(", ")")
            case NodeStyle.SQUARE:
                return ("[", "]")
            case NodeStyle.DIAMOND:
                return ("<", ">")
            case _:
                return ("", "")


class SVGRenderer(ASCIIRenderer):
    """Extended ASCII renderer with SVG support."""

    @classmethod
    def from_svg(cls, svg_content: str, **kwargs) -> "SVGRenderer":
        """
        Create renderer from SVG content.

        Parameters
        ----------
        svg_content : str
            SVG content as string
        **kwargs
            Additional arguments passed to renderer

        Returns
        -------
        SVGRenderer
            New renderer instance
        """
        parser = SVGParser()
        graph, options = parser.parse_svg(svg_content)

        # Override options with any provided kwargs
        if kwargs:
            for key, value in kwargs.items():
                setattr(options, key, value)

        return cls(graph, options=options)

    @classmethod
    def from_svg_file(cls, file_path: str, **kwargs) -> "SVGRenderer":
        """Create renderer from SVG file."""
        with open(file_path, "r") as f:
            return cls.from_svg(f.read(), **kwargs)


if __name__ == "__main__":
    # Example usage
    sample_svg = """
    <svg viewBox="0 0 100 100">
        <circle cx="20" cy="20" r="5" id="input"/>
        <rect x="70" y="70" width="10" height="10" id="output"/>
        <path d="M25,20 L65,70"/>
    </svg>
    """

    renderer = SVGRenderer.from_svg(sample_svg)
    print(renderer.render())
