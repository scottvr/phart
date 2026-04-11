"""DOT parsing helpers."""

from __future__ import annotations

import re
import warnings
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

import networkx as nx  # type: ignore

_RESERVED_PSEUDO_NODES = {"graph", "node", "edge"}
_SUBGRAPH_METADATA_KEY = "_phart_subgraphs"


def _normalize_dot_id(value: Any) -> str:
    text = str(value).strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {"'", '"'}:
        text = text[1:-1]
    return text.strip()


def _natural_key(value: Any) -> Tuple[Tuple[Any, ...], ...]:
    text = str(value)
    chunks = re.findall(r"\d+|\D+", text.casefold())
    tokens: List[Tuple[Any, ...]] = []
    for chunk in chunks:
        if chunk.isdigit():
            tokens.append((0, int(chunk), chunk))
        else:
            tokens.append((1, chunk))
    return tuple(tokens)


@dataclass
class _RawEdge:
    source: str
    target: str
    attrs: Dict[str, Any]
    context_path: Tuple[str, ...]


@dataclass
class _SubgraphInfo:
    id: str
    name: str
    label: Optional[str]
    parent: Optional[str]
    depth: int
    order: int
    children: List[str] = field(default_factory=list)
    direct_nodes: Set[str] = field(default_factory=set)
    all_nodes: Set[str] = field(default_factory=set)


def _iter_pairings(
    sources: List[str],
    targets: List[str],
) -> List[Tuple[str, str]]:
    if not sources or not targets:
        return []
    count = max(len(sources), len(targets))
    pairs: List[Tuple[str, str]] = []
    for idx in range(count):
        pairs.append((sources[idx % len(sources)], targets[idx % len(targets)]))
    return pairs


def _add_graph_edge(
    graph: nx.DiGraph,
    source: str,
    target: str,
    attrs: Dict[str, Any],
    *,
    directed: bool,
) -> None:
    if graph.has_edge(source, target):
        graph[source][target].update(attrs)
    else:
        graph.add_edge(source, target, **attrs)

    if directed or source == target:
        return

    if graph.has_edge(target, source):
        graph[target][source].update(attrs)
    else:
        graph.add_edge(target, source, **attrs)


def _extract_subgraph_data(root_graph: Any) -> Dict[str, Any]:
    subgraphs: Dict[str, _SubgraphInfo] = {}
    subgraph_name_to_ids: Dict[str, List[str]] = {}
    explicit_nodes: Set[str] = set()
    node_attrs: Dict[str, Dict[str, Any]] = {}
    raw_edges: List[_RawEdge] = []
    node_path_candidates: Dict[str, List[Tuple[str, ...]]] = {}
    order_counter = 0
    id_counter = 0

    def register_node(
        node_name: str,
        attrs: Optional[Dict[str, Any]],
        *,
        context_path: Tuple[str, ...],
        explicit: bool,
    ) -> None:
        if not node_name or node_name.lower() in _RESERVED_PSEUDO_NODES:
            return

        if explicit:
            explicit_nodes.add(node_name)
        node_attrs.setdefault(node_name, {})
        if attrs:
            node_attrs[node_name].update(dict(attrs))
        if context_path:
            node_path_candidates.setdefault(node_name, []).append(context_path)
            for subgraph_id in context_path:
                if subgraph_id in subgraphs:
                    subgraphs[subgraph_id].direct_nodes.add(node_name)

    def register_edge(
        source: str,
        target: str,
        attrs: Optional[Dict[str, Any]],
        *,
        context_path: Tuple[str, ...],
    ) -> None:
        if not source or not target:
            return
        raw_edges.append(
            _RawEdge(
                source=source,
                target=target,
                attrs=dict(attrs or {}),
                context_path=context_path,
            )
        )
        if context_path:
            source_name = source.strip()
            target_name = target.strip()
            if source_name and source_name.lower() not in _RESERVED_PSEUDO_NODES:
                node_path_candidates.setdefault(source_name, []).append(context_path)
            if target_name and target_name.lower() not in _RESERVED_PSEUDO_NODES:
                node_path_candidates.setdefault(target_name, []).append(context_path)

    def walk_graph(
        graph_obj: Any,
        *,
        parent_id: Optional[str],
        context_path: Tuple[str, ...],
    ) -> None:
        nonlocal order_counter, id_counter

        for node_obj in graph_obj.get_nodes():
            node_name = _normalize_dot_id(node_obj.get_name())
            node_obj_attrs = dict(node_obj.get_attributes() or {})
            register_node(
                node_name,
                node_obj_attrs,
                context_path=context_path,
                explicit=True,
            )

        for edge_obj in graph_obj.get_edges():
            source = _normalize_dot_id(edge_obj.get_source())
            target = _normalize_dot_id(edge_obj.get_destination())
            edge_attrs = dict(edge_obj.get_attributes() or {})
            register_edge(
                source,
                target,
                edge_attrs,
                context_path=context_path,
            )

        for subgraph_obj in graph_obj.get_subgraphs():
            subgraph_name = _normalize_dot_id(subgraph_obj.get_name())
            subgraph_attrs = dict(subgraph_obj.get_attributes() or {})
            subgraph_label_raw = subgraph_attrs.get("label")
            subgraph_label = (
                _normalize_dot_id(subgraph_label_raw)
                if subgraph_label_raw is not None
                else None
            )

            subgraph_id = f"sg_{id_counter}_{subgraph_name or 'subgraph'}"
            id_counter += 1
            subgraphs[subgraph_id] = _SubgraphInfo(
                id=subgraph_id,
                name=subgraph_name,
                label=subgraph_label,
                parent=parent_id,
                depth=len(context_path),
                order=order_counter,
            )
            order_counter += 1

            if parent_id is not None and parent_id in subgraphs:
                subgraphs[parent_id].children.append(subgraph_id)
            subgraph_name_to_ids.setdefault(subgraph_name, []).append(subgraph_id)

            next_path = context_path + (subgraph_id,)
            walk_graph(
                subgraph_obj,
                parent_id=subgraph_id,
                context_path=next_path,
            )

    walk_graph(root_graph, parent_id=None, context_path=tuple())

    def resolve_subgraph_id(token: str) -> Optional[str]:
        if token in explicit_nodes:
            return None
        ids = subgraph_name_to_ids.get(token)
        if not ids:
            return None
        return ids[0]

    all_nodes: Set[str] = set(explicit_nodes)
    for edge in raw_edges:
        src_subgraph = resolve_subgraph_id(edge.source)
        dst_subgraph = resolve_subgraph_id(edge.target)
        if src_subgraph is None and edge.source.lower() not in _RESERVED_PSEUDO_NODES:
            all_nodes.add(edge.source)
        if dst_subgraph is None and edge.target.lower() not in _RESERVED_PSEUDO_NODES:
            all_nodes.add(edge.target)

    for node in all_nodes:
        node_attrs.setdefault(node, {})

    node_to_path: Dict[str, Tuple[str, ...]] = {}
    for node in all_nodes:
        candidates = node_path_candidates.get(node, [])
        if not candidates:
            node_to_path[node] = tuple()
            continue
        primary = max(
            candidates,
            key=lambda path: (
                len(path),
                tuple(_natural_key(part) for part in path),
            ),
        )
        node_to_path[node] = primary

    for info in subgraphs.values():
        info.all_nodes.clear()
    for node, path in node_to_path.items():
        for subgraph_id in path:
            if subgraph_id in subgraphs:
                subgraphs[subgraph_id].all_nodes.add(node)

    def subgraph_boundary_nodes(subgraph_id: str, *, direction: str) -> List[str]:
        info = subgraphs.get(subgraph_id)
        if info is None:
            return []
        members = info.all_nodes
        if not members:
            return []
        boundary: Set[str] = set()
        for edge in raw_edges:
            source_subgraph = resolve_subgraph_id(edge.source)
            target_subgraph = resolve_subgraph_id(edge.target)
            if source_subgraph is not None or target_subgraph is not None:
                continue
            source = edge.source
            target = edge.target
            if direction == "out":
                if source in members and target not in members:
                    boundary.add(source)
            else:
                if target in members and source not in members:
                    boundary.add(target)
        if not boundary:
            boundary = set(members)
        return sorted(boundary, key=_natural_key)

    name_to_primary_id = {
        name: ids[0] for name, ids in subgraph_name_to_ids.items() if ids
    }

    return {
        "subgraphs": subgraphs,
        "name_to_primary_id": name_to_primary_id,
        "all_nodes": all_nodes,
        "node_attrs": node_attrs,
        "raw_edges": raw_edges,
        "node_to_path": node_to_path,
        "resolve_subgraph_id": resolve_subgraph_id,
        "subgraph_boundary_nodes": subgraph_boundary_nodes,
    }


def _build_graph_from_dot(root_graph: Any) -> nx.DiGraph:
    extracted = _extract_subgraph_data(root_graph)
    subgraphs: Dict[str, _SubgraphInfo] = extracted["subgraphs"]
    all_nodes: Set[str] = extracted["all_nodes"]
    node_attrs: Dict[str, Dict[str, Any]] = extracted["node_attrs"]
    raw_edges: List[_RawEdge] = extracted["raw_edges"]
    node_to_path: Dict[str, Tuple[str, ...]] = extracted["node_to_path"]
    resolve_subgraph_id = extracted["resolve_subgraph_id"]
    subgraph_boundary_nodes = extracted["subgraph_boundary_nodes"]

    is_directed = str(root_graph.get_type()).strip().lower() == "digraph"

    graph: nx.DiGraph = nx.DiGraph()
    for node in sorted(all_nodes, key=_natural_key):
        graph.add_node(node, **dict(node_attrs.get(node, {})))

    for edge in raw_edges:
        source_subgraph = resolve_subgraph_id(edge.source)
        target_subgraph = resolve_subgraph_id(edge.target)

        source_candidates = (
            subgraph_boundary_nodes(source_subgraph, direction="out")
            if source_subgraph is not None
            else [edge.source]
        )
        target_candidates = (
            subgraph_boundary_nodes(target_subgraph, direction="in")
            if target_subgraph is not None
            else [edge.target]
        )

        for source_node, target_node in _iter_pairings(
            source_candidates, target_candidates
        ):
            if source_node not in graph:
                graph.add_node(source_node, **dict(node_attrs.get(source_node, {})))
            if target_node not in graph:
                graph.add_node(target_node, **dict(node_attrs.get(target_node, {})))
            _add_graph_edge(
                graph,
                source_node,
                target_node,
                dict(edge.attrs),
                directed=is_directed,
            )

    serialized_subgraphs = []
    for info in sorted(subgraphs.values(), key=lambda item: (item.depth, item.order)):
        serialized_subgraphs.append(
            {
                "id": info.id,
                "name": info.name,
                "label": info.label,
                "parent": info.parent,
                "children": list(info.children),
                "direct_nodes": sorted(info.direct_nodes, key=_natural_key),
                "nodes": sorted(info.all_nodes, key=_natural_key),
                "depth": info.depth,
                "order": info.order,
            }
        )

    root_subgraphs = [
        info.id
        for info in sorted(subgraphs.values(), key=lambda item: item.order)
        if info.parent is None
    ]
    graph.graph[_SUBGRAPH_METADATA_KEY] = {
        "schema_version": "1.0",
        "subgraphs": serialized_subgraphs,
        "root_subgraphs": root_subgraphs,
        "node_to_path": {node: list(path) for node, path in node_to_path.items()},
        "name_to_id": dict(extracted["name_to_primary_id"]),
    }
    return graph


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

    return _build_graph_from_dot(graphs[0])
