"""GraphML loading helpers."""

from __future__ import annotations

import networkx as nx  # type: ignore


def parse_graphml_to_digraph(graphml_file: str) -> nx.DiGraph:
    """Load a GraphML file and return a directed graph.

    Raises:
        ValueError: if the file cannot be parsed as GraphML.
    """
    try:
        graph = nx.read_graphml(graphml_file)
    except Exception as exc:
        raise ValueError(f"Failed to read GraphML file: {exc}") from exc

    if not isinstance(graph, nx.DiGraph):
        graph = nx.DiGraph(graph)
    return graph
