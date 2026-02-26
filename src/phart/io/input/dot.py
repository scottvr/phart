"""DOT parsing helpers."""

from __future__ import annotations

import warnings

import networkx as nx  # type: ignore


def parse_dot_to_digraph(dot_string: str) -> nx.DiGraph:
    """Parse a DOT string and return a directed graph.

    Raises:
        ImportError: if `pydot` is unavailable.
        ValueError: if the DOT string does not contain a valid graph.
    """
    try:
        import pydot  # type: ignore
    except ImportError as exc:
        raise ImportError("pydot is required for DOT format support") from exc

    with warnings.catch_warnings():
        # pyparsing emits deprecation warnings via pydot on newer versions.
        # Tests enforce warnings as errors, so suppress this third-party
        # warning only for the parse call.
        warnings.filterwarnings(
            "ignore",
            category=DeprecationWarning,
            module=r"pydot\.dot_parser",
        )
        try:
            from pyparsing import PyparsingDeprecationWarning  # type: ignore

            warnings.filterwarnings("ignore", category=PyparsingDeprecationWarning)
        except Exception:
            pass
        graphs = pydot.graph_from_dot_data(dot_string)

    if not graphs:
        raise ValueError("No valid graphs found in DOT string")

    graph = nx.nx_pydot.from_pydot(graphs[0])
    if not isinstance(graph, nx.DiGraph):
        graph = nx.DiGraph(graph)
    return graph
