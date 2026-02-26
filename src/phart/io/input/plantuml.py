"""PlantUML loading helpers."""

from __future__ import annotations

import networkx as nx  # type: ignore
import re

from typing import Any, Dict, Optional


def parse_plantuml_to_digraph(plantuml_str: str) -> nx.DiGraph:
    graph: nx.DiGraph[Any] = nx.DiGraph()
    alias_to_id: Dict[str, str] = {}

    declaration_kinds = (
        "abstract class",
        "class",
        "interface",
        "enum",
        "entity",
        "annotation",
        "actor",
        "participant",
        "boundary",
        "control",
        "database",
        "collections",
        "queue",
        "component",
        "node",
        "usecase",
        "object",
        "artifact",
        "cloud",
        "folder",
        "frame",
        "rectangle",
    )
    decl_re = re.compile(
        r"^(?P<kind>"
        + "|".join(re.escape(kind) for kind in declaration_kinds)
        + r")\s+"
        r"(?P<lhs>\"[^\"]+\"|[A-Za-z_][\w.:$-]*)"
        r"(?:\s+as\s+(?P<rhs>\"[^\"]+\"|[A-Za-z_][\w.:$-]*))?"
        r"(?:\s+<<[^>]+>>)?\s*$",
        re.IGNORECASE,
    )
    rel_re = re.compile(
        r"^(?P<src>\"[^\"]+\"|[A-Za-z_][\w.:$-]*)\s*"
        r"(?P<arrow>[A-Za-z0-9_<>*#.\-/\\|]+)\s*"
        r"(?P<dst>\"[^\"]+\"|[A-Za-z_][\w.:$-]*)"
        r"(?:\s*:\s*(?P<label>.+))?\s*$"
    )

    def _unquote(token: str) -> str:
        token = token.strip()
        if len(token) >= 2 and token[0] == token[-1] == '"':
            return token[1:-1]
        return token

    def _ensure_node(node_id: str, label: Optional[str] = None) -> None:
        if node_id not in graph:
            graph.add_node(node_id)
        if label:
            graph.nodes[node_id]["label"] = label

    def _resolve_token(token: str) -> str:
        token = token.strip()
        if len(token) >= 2 and token[0] == token[-1] == '"':
            label = token[1:-1]
            _ensure_node(label, label=label)
            return label
        return alias_to_id.get(token, token)

    for raw_line in plantuml_str.splitlines():
        line = raw_line.strip()
        if "'" in line:
            line = line.split("'", 1)[0].rstrip()
        if not line or line.startswith("//"):
            continue
        lowered = line.lower()
        if lowered in {"@startuml", "@enduml", "{", "}", "end", "end note"}:
            continue
        if lowered.startswith(
            (
                "skinparam ",
                "title ",
                "header ",
                "footer ",
                "legend ",
                "note ",
                "hide ",
                "show ",
                "left to right",
                "top to bottom",
                "scale ",
                "caption ",
                "newpage",
                "page ",
                "!",
            )
        ):
            continue

        decl = decl_re.match(line)
        if decl:
            lhs = decl.group("lhs")
            rhs = decl.group("rhs")
            if rhs:
                lhs_unq = _unquote(lhs)
                rhs_unq = _unquote(rhs)
                if lhs.startswith('"') and rhs.startswith('"'):
                    node_id = lhs_unq
                    _ensure_node(node_id, label=lhs_unq)
                elif lhs.startswith('"'):
                    node_id = rhs_unq
                    alias_to_id[rhs_unq] = node_id
                    _ensure_node(node_id, label=lhs_unq)
                elif rhs.startswith('"'):
                    node_id = lhs_unq
                    alias_to_id[lhs_unq] = node_id
                    _ensure_node(node_id, label=rhs_unq)
                else:
                    node_id = lhs_unq
                    alias_to_id[rhs_unq] = node_id
                    _ensure_node(node_id, label=lhs_unq)
            else:
                node_id = _unquote(lhs)
                _ensure_node(node_id, label=node_id)
                alias_to_id[node_id] = node_id
            continue

        relation = rel_re.match(line)
        if not relation:
            continue

        arrow = relation.group("arrow")
        # Ignore non-link operator tokens.
        if not any(ch in arrow for ch in ("-", ".", "<", ">")):
            continue

        src = _resolve_token(relation.group("src"))
        dst = _resolve_token(relation.group("dst"))
        _ensure_node(src, label=graph.nodes[src].get("label", src))
        _ensure_node(dst, label=graph.nodes[dst].get("label", dst))

        label = relation.group("label")
        edge_attrs: Dict[str, Any] = {}
        if label:
            clean_label = label.strip()
            if clean_label:
                edge_attrs["label"] = clean_label

        has_left = "<" in arrow
        has_right = ">" in arrow
        if has_left and not has_right:
            graph.add_edge(dst, src, **edge_attrs)
        elif has_right and not has_left:
            graph.add_edge(src, dst, **edge_attrs)
        elif has_left and has_right:
            graph.add_edge(src, dst, **edge_attrs)
            graph.add_edge(dst, src, **edge_attrs)
        else:
            # Undirected relation styles are represented as a single directed edge.
            graph.add_edge(src, dst, **edge_attrs)

    if graph.number_of_nodes() == 0:
        raise ValueError("No supported PlantUML nodes or relationships found")
    return graph
