import networkx as nx
from pathlib import Path


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _append_or_set(container, key, value):
    existing = container.get(key)
    if existing is None:
        container[key] = value
        return
    if isinstance(existing, list):
        existing.append(value)
        return
    container[key] = [existing, value]


def _ensure_path_dict(container, path):
    current = container
    for key in path:
        existing = current.get(key)
        if isinstance(existing, dict):
            current = existing
            continue
        if existing is None:
            current[key] = {}
        else:
            current[key] = {"value": existing}
        current = current[key]
    return current


def _add_relationship_edge(graph, start, end, *, role):
    if not graph.has_edge(start, end):
        graph.add_edge(start, end, role=role)


def gedcom_to_digraph(ged_text):
    G = nx.DiGraph()
    lines = ged_text.strip().split("\n")

    current_id = None
    current_type = None  # 'INDI' or 'FAM'
    key_stack = {}

    for line in lines:
        # GEDCOM format: Level Tag Payload
        parts = line.strip().split(" ", 2)
        if len(parts) < 2:
            continue

        try:
            level = int(parts[0])
        except ValueError:
            continue

        tag = parts[1]
        payload = parts[2] if len(parts) > 2 else ""
        payload = payload.strip()

        for existing_level in list(key_stack.keys()):
            if existing_level >= level:
                del key_stack[existing_level]

        # Level 0: Start of a new record (Individual or Family)
        if level == 0:
            key_stack.clear()
            if tag.startswith("@"):
                current_id = tag
                current_type = payload.strip().upper()
                G.add_node(current_id, type=current_type)
            else:
                current_id = None
                current_type = None

            continue

        if current_id is None:
            continue

        # Level 1: Attributes and relationships
        if level == 1:
            key = tag.lower()
            key_stack[level] = key

            if current_type == "INDI":
                # Basic Individual attributes
                if tag == "NAME":
                    _append_or_set(
                        G.nodes[current_id], "name", payload.replace("/", "").strip()
                    )
                elif tag == "FAMS" and payload.startswith("@"):
                    _append_or_set(G.nodes[current_id], "fams", payload)
                    _add_relationship_edge(G, current_id, payload, role="spouse")
                elif tag == "FAMC" and payload.startswith("@"):
                    _append_or_set(G.nodes[current_id], "famc", payload)
                    _add_relationship_edge(G, payload, current_id, role="child")
                else:
                    # Generic catch-all for any other data (SEX, BIRT, etc.)
                    _append_or_set(G.nodes[current_id], key, payload if payload else {})

            elif current_type == "FAM":
                # Relationship edges
                if tag in ["HUSB", "WIFE", "CHIL"] and payload.startswith("@"):
                    # Parent-to-Family or Family-to-Child flow
                    if tag == "CHIL":
                        _append_or_set(G.nodes[current_id], "chil", payload)
                        _add_relationship_edge(G, current_id, payload, role="child")
                    else:
                        _append_or_set(G.nodes[current_id], key, payload)
                        _add_relationship_edge(G, payload, current_id, role=key)
                else:
                    _append_or_set(G.nodes[current_id], key, payload if payload else {})
            else:
                _append_or_set(G.nodes[current_id], key, payload if payload else {})

            continue

        # Level 2+: Sub-attributes (DATE, CONT, NOTE, etc.) stored under nested dicts.
        ancestry_path = [key_stack[i] for i in range(1, level) if i in key_stack]
        if not ancestry_path:
            continue

        parent = _ensure_path_dict(G.nodes[current_id], ancestry_path)
        key = tag.lower()
        key_stack[level] = key
        _append_or_set(parent, key, payload if payload else {})

    return G


def _extract_lifespan(attrs):
    birt = attrs.get("birt")
    deat = attrs.get("deat")
    birth = birt.get("date") if isinstance(birt, dict) else None
    death = deat.get("date") if isinstance(deat, dict) else None
    if not birth and not death:
        return None
    return f"{birth or '-'}-{death or '-'}"


def _extract_name(attrs, fallback):
    raw = attrs.get("name", fallback)
    if isinstance(raw, dict):
        value = raw.get("value")
        if value:
            return str(value)
        return str(fallback)
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, str) and item.strip():
                return item
            if isinstance(item, dict) and item.get("value"):
                return str(item["value"])
        return str(fallback)
    return str(raw)


def build_person_graph(
    graph: nx.DiGraph,
    *,
    root_family: str = "@F1@",
    family_depth: int = 4,
) -> nx.DiGraph:
    """Build a person-only subgraph rooted at a family ID."""
    families_to_visit = [(root_family, 0)]
    visited_families = set()
    included_people = set()

    while families_to_visit:
        family_id, depth = families_to_visit.pop(0)
        if family_id in visited_families:
            continue
        visited_families.add(family_id)
        if family_id not in graph.nodes:
            continue

        family = graph.nodes[family_id]
        family_members = []
        for tag in ("husb", "wife", "chil"):
            family_members.extend(_as_list(family.get(tag)))

        for person_id in family_members:
            if person_id not in graph.nodes:
                continue
            included_people.add(person_id)
            if depth >= family_depth:
                continue

            person = graph.nodes[person_id]
            for next_family in _as_list(person.get("fams")) + _as_list(
                person.get("famc")
            ):
                if isinstance(next_family, str) and next_family.startswith("@F"):
                    families_to_visit.append((next_family, depth + 1))

    person_graph = nx.DiGraph()
    for person_id in sorted(included_people):
        attrs = dict(graph.nodes[person_id])
        name = _extract_name(attrs, person_id)
        lifespan = _extract_lifespan(attrs)
        attrs["label"] = f"{name} {lifespan}".strip() if lifespan else str(name)
        person_graph.add_node(person_id, **attrs)

    for family_id in visited_families:
        if family_id not in graph.nodes:
            continue
        family = graph.nodes[family_id]
        husbands = [p for p in _as_list(family.get("husb")) if p in included_people]
        wives = [p for p in _as_list(family.get("wife")) if p in included_people]
        children = [p for p in _as_list(family.get("chil")) if p in included_people]

        for husband in husbands:
            for wife in wives:
                person_graph.add_edge(husband, wife, role="spouse")
        for husband in husbands:
            for child in children:
                person_graph.add_edge(husband, child, role="parent")
        for wife in wives:
            for child in children:
                person_graph.add_edge(wife, child, role="parent")

    return person_graph


def main():
    file_path = Path(__file__).with_name("happy.ged")
    ged_contents = file_path.read_text(encoding="utf-8")
    full_graph = gedcom_to_digraph(ged_contents)
    family_graph = build_person_graph(full_graph, root_family="@F1@", family_depth=4)

    from phart import ASCIIRenderer

    renderer = ASCIIRenderer(family_graph)
    print(renderer.render())


if __name__ == "__main__":
    main()
