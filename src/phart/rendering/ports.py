"""Port assignment and anchor selection helpers for ASCIIRenderer."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from phart.renderer import ASCIIRenderer


def get_edge_sides(
    renderer: ASCIIRenderer, start_bounds: Dict[str, int], end_bounds: Dict[str, int]
) -> Tuple[str, str]:
    """Choose source/target box sides for an edge based on relative geometry."""
    vertical_overlap = max(start_bounds["top"], end_bounds["top"]) <= min(
        start_bounds["bottom"], end_bounds["bottom"]
    )
    if (vertical_overlap and start_bounds["center_x"] != end_bounds["center_x"]) or (
        start_bounds["center_y"] == end_bounds["center_y"]
    ):
        if start_bounds["center_x"] <= end_bounds["center_x"]:
            return "right", "left"
        return "left", "right"
    if start_bounds["center_y"] < end_bounds["center_y"]:
        return "bottom", "top"
    return "top", "bottom"


def get_center_anchor_for_side(
    renderer: ASCIIRenderer, bounds: Dict[str, int], side: str
) -> Tuple[int, int]:
    if side == "top":
        return bounds["center_x"], bounds["top"]
    if side == "bottom":
        return bounds["center_x"], bounds["bottom"]
    if side == "left":
        return bounds["left"], bounds["center_y"]
    return bounds["right"], bounds["center_y"]


def get_side_port_values(
    renderer: ASCIIRenderer, bounds: Dict[str, int], side: str
) -> List[int]:
    """Get candidate port coordinates along a side (axis-only values)."""
    if side in ("top", "bottom"):
        if bounds["right"] - bounds["left"] > 1:
            return list(range(bounds["left"] + 1, bounds["right"]))
        return [bounds["center_x"]]
    if bounds["bottom"] - bounds["top"] > 1:
        return list(range(bounds["top"] + 1, bounds["bottom"]))
    return [bounds["center_y"]]


def counter_for_side(
    bounds: Dict[str, int], peer_bounds: Dict[str, int], side: str
) -> int:
    """Project the peer center onto the routing axis for the given side."""
    if side in ("top", "bottom"):
        return peer_bounds["center_x"]
    return peer_bounds["center_y"]


def side_change_penalty(default_side: str, candidate_side: str) -> int:
    """Prefer keeping the default face, then adjacent faces, then the opposite face."""
    if default_side == candidate_side:
        return 0

    opposite_sides = {
        ("top", "bottom"),
        ("bottom", "top"),
        ("left", "right"),
        ("right", "left"),
    }
    if (default_side, candidate_side) in opposite_sides:
        return 6
    return 3


def port_value_to_xy(
    renderer: ASCIIRenderer, bounds: Dict[str, int], side: str, value: int
) -> Tuple[int, int]:
    if side == "top":
        return value, bounds["top"]
    if side == "bottom":
        return value, bounds["bottom"]
    if side == "left":
        return bounds["left"], value
    return bounds["right"], value


def crowding_cost(value: int, used_values: List[int]) -> float:
    """Soft penalty for placing a port too close to existing ports."""
    if not used_values:
        return 0.0
    return sum(1.0 / (abs(value - used) + 1.0) for used in used_values)


def values_with_min_separation(
    candidates: List[int], used_values: List[int], min_sep: int
) -> List[int]:
    """Filter candidate values by minimum separation from existing values."""
    if not used_values:
        return list(candidates)

    filtered = [
        candidate
        for candidate in candidates
        if all(abs(candidate - used) >= min_sep for used in used_values)
    ]
    return filtered if filtered else list(candidates)


def port_pair_jog_cost(start_value: int, end_value: int) -> int:
    """Orthogonal jog distance in the routing axis for a port pair."""
    return abs(start_value - end_value)


def side_center_value(bounds: Dict[str, int], side: str) -> int:
    """Get the center axis coordinate for a given node side."""
    if side in ("top", "bottom"):
        return bounds["center_x"]
    return bounds["center_y"]


def nearest_candidate_to_center(candidates: List[int], center_value: int) -> int:
    """Pick candidate nearest to local side center (deterministic ties)."""
    return min(candidates, key=lambda value: (abs(value - center_value), value))


def choose_port_pair(
    renderer: ASCIIRenderer,
    *,
    start_candidates: List[int],
    end_candidates: List[int],
    start_counter: int,
    end_counter: int,
    used_start_values: List[int],
    used_end_values: List[int],
) -> Tuple[int, int]:
    """Choose best (start,end) port pair using spacing + route-awareness."""
    best_pair: Optional[Tuple[int, int]] = None
    best_key: Optional[Tuple[float, int, int, int, int]] = None

    for start_value in start_candidates:
        for end_value in end_candidates:
            start_cost = abs(start_value - start_counter)
            end_cost = abs(end_value - end_counter)
            jog_cost = renderer._port_pair_jog_cost(start_value, end_value)

            crowding = renderer._crowding_cost(
                start_value, used_start_values
            ) + renderer._crowding_cost(end_value, used_end_values)

            straight_bonus = 3.0 if jog_cost == 0 else 0.0
            score = (
                float(start_cost)
                + float(end_cost)
                + (0.75 * float(jog_cost))
                + (2.0 * crowding)
                - straight_bonus
            )
            pair_key = (
                score,
                start_cost + end_cost,
                jog_cost,
                start_value,
                end_value,
            )
            if best_key is None or pair_key < best_key:
                best_key = pair_key
                best_pair = (start_value, end_value)

    if best_pair is None:
        return start_counter, end_counter
    return best_pair


def assign_monotone_port_values(
    renderer: ASCIIRenderer, counters: List[int], candidates: List[int]
) -> List[int]:
    """Assign candidate ports monotonically to ordered counters."""
    if not counters:
        return []
    if not candidates:
        return list(counters)

    ordered_candidates = sorted(set(candidates))
    ordered_counters = list(counters)
    n = len(ordered_counters)
    m = len(ordered_candidates)

    if n == 1:
        center = ordered_counters[0]
        return [renderer._nearest_candidate_to_center(ordered_candidates, center)]

    if m < n:
        max_index = m - 1
        return [
            ordered_candidates[round((i * max_index) / max(n - 1, 1))] for i in range(n)
        ]

    inf = float("inf")
    dp: List[List[float]] = [[inf for _ in range(m)] for _ in range(n)]
    prev: List[List[int]] = [[-1 for _ in range(m)] for _ in range(n)]

    for j in range(m):
        dp[0][j] = abs(ordered_counters[0] - ordered_candidates[j])

    for i in range(1, n):
        for j in range(i, m):
            local_cost = abs(ordered_counters[i] - ordered_candidates[j])
            best_prev_idx = -1
            best_prev_cost = inf
            for k in range(i - 1, j):
                cand_cost = dp[i - 1][k]
                if cand_cost < best_prev_cost:
                    best_prev_cost = cand_cost
                    best_prev_idx = k
            dp[i][j] = best_prev_cost + local_cost
            prev[i][j] = best_prev_idx

    best_last_idx = min(
        range(n - 1, m),
        key=lambda j: (dp[n - 1][j], j),
    )

    chosen_indices = [0 for _ in range(n)]
    chosen_indices[n - 1] = best_last_idx
    for i in range(n - 1, 0, -1):
        chosen_indices[i - 1] = prev[i][chosen_indices[i]]

    return [ordered_candidates[idx] for idx in chosen_indices]


def assign_monotone_port_indices(
    renderer: ASCIIRenderer, counters: List[int], candidates: List[int]
) -> List[int]:
    """Assign monotonically ordered candidate indices to ordered counters."""
    if not counters:
        return []
    ordered_candidates = sorted(set(candidates))
    if not ordered_candidates:
        return [0 for _ in counters]

    n = len(counters)
    m = len(ordered_candidates)
    if n == 1:
        target = counters[0]
        best_idx = min(
            range(m), key=lambda idx: (abs(ordered_candidates[idx] - target), idx)
        )
        return [best_idx]

    if m < n:
        max_index = m - 1
        return [round((i * max_index) / max(n - 1, 1)) for i in range(n)]

    inf = float("inf")
    dp: List[List[float]] = [[inf for _ in range(m)] for _ in range(n)]
    prev: List[List[int]] = [[-1 for _ in range(m)] for _ in range(n)]

    for j in range(m):
        dp[0][j] = abs(counters[0] - ordered_candidates[j])

    for i in range(1, n):
        for j in range(i, m):
            local_cost = abs(counters[i] - ordered_candidates[j])
            best_prev_idx = -1
            best_prev_cost = inf
            for k in range(i - 1, j):
                cand_cost = dp[i - 1][k]
                if cand_cost < best_prev_cost:
                    best_prev_cost = cand_cost
                    best_prev_idx = k
            dp[i][j] = best_prev_cost + local_cost
            prev[i][j] = best_prev_idx

    best_last_idx = min(
        range(n - 1, m),
        key=lambda j: (dp[n - 1][j], j),
    )
    chosen = [0 for _ in range(n)]
    chosen[n - 1] = best_last_idx
    for i in range(n - 1, 0, -1):
        chosen[i - 1] = prev[i][chosen[i]]
    return chosen


def rebalance_edge_face_role(
    renderer: ASCIIRenderer,
    edge_specs: List[Dict[str, Any]],
    positions: Dict[Any, Tuple[int, int]],
    role: str,
) -> None:
    """Move oversubscribed edge endpoints for one role to alternate faces."""
    node_key = f"{role}_node"
    side_key = f"{role}_side"
    default_side_key = f"default_{role}_side"
    counter_key = f"{role}_counter"
    candidates_key = f"{role}_candidates"
    peer_role = "end" if role == "start" else "start"
    peer_node_key = f"{peer_role}_node"
    face_capacity: Dict[Tuple[Any, str], int] = {}
    face_counts: Dict[Tuple[Any, str], int] = {}
    node_bounds_cache: Dict[Any, Dict[str, int]] = {}
    face_order = ("top", "right", "bottom", "left")

    def _get_bounds(node: Any) -> Dict[str, int]:
        if node not in node_bounds_cache:
            node_bounds_cache[node] = renderer._get_node_bounds(node, positions)
        return node_bounds_cache[node]

    def _get_capacity(node: Any, side: str) -> int:
        key = (node, side)
        if key not in face_capacity:
            bounds = _get_bounds(node)
            candidates = sorted(set(renderer._get_side_port_values(bounds, side)))
            face_capacity[key] = len(candidates) if candidates else 1
        return face_capacity[key]

    for spec in edge_specs:
        face = (spec[node_key], spec[side_key])
        face_counts[face] = face_counts.get(face, 0) + 1

    while True:
        oversubscribed_faces = sorted(
            (
                face
                for face, count in face_counts.items()
                if count > _get_capacity(face[0], face[1])
            ),
            key=lambda face: (str(face[0]), face[1]),
        )
        if not oversubscribed_faces:
            return

        best_move: Optional[
            Tuple[Tuple[int, int, int, str, str], Dict[str, Any], str, int, List[int]]
        ] = None

        for face in oversubscribed_faces:
            node, current_side = face
            node_bounds = _get_bounds(node)
            for spec in edge_specs:
                if spec[node_key] != node or spec[side_key] != current_side:
                    continue

                peer_bounds = _get_bounds(spec[peer_node_key])
                peer_center = (peer_bounds["center_x"], peer_bounds["center_y"])

                for alt_side in face_order:
                    if alt_side == current_side:
                        continue

                    alt_face = (node, alt_side)
                    if face_counts.get(alt_face, 0) >= _get_capacity(node, alt_side):
                        continue

                    alt_candidates = sorted(
                        set(renderer._get_side_port_values(node_bounds, alt_side))
                    )
                    if not alt_candidates:
                        alt_candidates = [renderer._side_center_value(node_bounds, alt_side)]

                    alt_counter = counter_for_side(node_bounds, peer_bounds, alt_side)
                    alt_value = renderer._nearest_candidate_to_center(
                        alt_candidates, alt_counter
                    )
                    alt_anchor = renderer._port_value_to_xy(
                        node_bounds, alt_side, alt_value
                    )
                    score = (
                        abs(alt_anchor[0] - peer_center[0])
                        + abs(alt_anchor[1] - peer_center[1])
                        + side_change_penalty(spec[default_side_key], alt_side)
                        + (2 * face_counts.get(alt_face, 0))
                    )
                    move_key = (
                        score,
                        face_counts.get(alt_face, 0),
                        face_order.index(alt_side),
                        str(spec["edge_key"][0]),
                        str(spec["edge_key"][1]),
                    )

                    if best_move is None or move_key < best_move[0]:
                        best_move = (
                            move_key,
                            spec,
                            alt_side,
                            alt_counter,
                            alt_candidates,
                        )

        if best_move is None:
            return

        _move_key, spec, alt_side, alt_counter, alt_candidates = best_move
        old_face = (spec[node_key], spec[side_key])
        new_face = (spec[node_key], alt_side)
        face_counts[old_face] -= 1
        face_counts[new_face] = face_counts.get(new_face, 0) + 1
        spec[side_key] = alt_side
        spec[counter_key] = alt_counter
        spec[candidates_key] = alt_candidates
        spec["axis_delta"] = abs(spec["start_counter"] - spec["end_counter"])


def compute_edge_anchor_map(
    renderer: ASCIIRenderer, positions: Dict[Any, Tuple[int, int]]
) -> Dict[Tuple[Any, Any], Dict[str, Any]]:
    """Precompute deterministic per-edge anchors for edges that use ports."""
    if not renderer.options.bboxes:
        return {}

    edge_specs: List[Dict[str, Any]] = []

    for start, end in sorted(
        renderer.graph.edges(), key=lambda edge: (str(edge[0]), str(edge[1]))
    ):
        if start not in positions or end not in positions:
            continue
        if not renderer._should_use_ports_for_edge(start, end):
            continue

        start_bounds = renderer._get_node_bounds(start, positions)
        end_bounds = renderer._get_node_bounds(end, positions)
        start_side, end_side = renderer._get_edge_sides(start_bounds, end_bounds)

        start_counter = counter_for_side(start_bounds, end_bounds, start_side)
        end_counter = counter_for_side(end_bounds, start_bounds, end_side)
        start_candidates = renderer._get_side_port_values(start_bounds, start_side)
        end_candidates = renderer._get_side_port_values(end_bounds, end_side)
        if not start_candidates:
            start_candidates = [start_counter]
        if not end_candidates:
            end_candidates = [end_counter]

        edge_specs.append(
            {
                "edge_key": (start, end),
                "start_node": start,
                "start_side": start_side,
                "default_start_side": start_side,
                "start_counter": start_counter,
                "start_candidates": start_candidates,
                "end_node": end,
                "end_side": end_side,
                "default_end_side": end_side,
                "end_counter": end_counter,
                "end_candidates": end_candidates,
                "axis_delta": abs(start_counter - end_counter),
            }
        )

    if renderer.options.minimize_shared_ports:
        rebalance_edge_face_role(renderer, edge_specs, positions, "start")
        rebalance_edge_face_role(renderer, edge_specs, positions, "end")

    edge_anchor_map: Dict[Tuple[Any, Any], Dict[str, Any]] = {}
    used_by_side: Dict[Tuple[Any, str], List[int]] = {}
    min_port_separation = 1
    wiggle_radius = 1
    face_candidate_pools: Dict[Tuple[Tuple[Any, Any], str], List[int]] = {}
    face_requirements: Dict[
        Tuple[Any, str], List[Tuple[Tuple[Any, Any], str, int, str]]
    ] = {}
    for spec in edge_specs:
        edge_key = spec["edge_key"]
        start_node = spec["start_node"]
        start_side = spec["start_side"]
        start_counter = spec["start_counter"]
        end_node = spec["end_node"]
        end_side = spec["end_side"]
        end_counter = spec["end_counter"]
        face_requirements.setdefault((start_node, start_side), []).append(
            (edge_key, "start", start_counter, str(end_node))
        )
        face_requirements.setdefault((end_node, end_side), []).append(
            (edge_key, "end", end_counter, str(start_node))
        )

    for (node, side), items in face_requirements.items():
        node_bounds = renderer._get_node_bounds(node, positions)
        candidates = sorted(set(renderer._get_side_port_values(node_bounds, side)))
        if not candidates:
            candidates = [renderer._side_center_value(node_bounds, side)]
        max_idx = len(candidates) - 1

        sorted_items = sorted(items, key=lambda item: (item[2], item[3]))
        if len(sorted_items) == 1:
            center = renderer._side_center_value(node_bounds, side)
            center_idx = min(
                range(len(candidates)),
                key=lambda idx: (abs(candidates[idx] - center), idx),
            )
            low_idx = max(0, center_idx - wiggle_radius)
            high_idx = min(max_idx, center_idx + wiggle_radius)
            edge_key, role, _counter, _peer = sorted_items[0]
            face_candidate_pools[(edge_key, role)] = candidates[low_idx : high_idx + 1]
        else:
            counters = [item[2] for item in sorted_items]
            base_indices = renderer._assign_monotone_port_indices(counters, candidates)
            n = len(base_indices)
            for idx, (edge_key, role, _counter, _peer) in enumerate(sorted_items):
                base_idx = base_indices[idx]
                left_limit = (
                    (base_indices[idx - 1] + base_idx + 1) // 2 if idx > 0 else 0
                )
                right_limit = (
                    (base_idx + base_indices[idx + 1] - 1) // 2
                    if idx < n - 1
                    else max_idx
                )
                if left_limit > right_limit:
                    left_limit = right_limit = min(max(base_idx, 0), max_idx)
                low_idx = max(left_limit, base_idx - wiggle_radius)
                high_idx = min(right_limit, base_idx + wiggle_radius)
                if low_idx > high_idx:
                    low_idx = high_idx = min(max(base_idx, left_limit), right_limit)
                face_candidate_pools[(edge_key, role)] = candidates[
                    low_idx : high_idx + 1
                ]

    edge_specs_sorted = sorted(
        edge_specs,
        key=lambda spec: (
            spec["axis_delta"],
            str(spec["start_node"]),
            spec["start_side"],
            str(spec["end_node"]),
            spec["end_side"],
            str(spec["edge_key"][0]),
            str(spec["edge_key"][1]),
        ),
    )

    for spec in edge_specs_sorted:
        edge_key = spec["edge_key"]
        start_node = spec["start_node"]
        start_side = spec["start_side"]
        start_counter = spec["start_counter"]
        start_candidates = spec["start_candidates"]
        end_node = spec["end_node"]
        end_side = spec["end_side"]
        end_counter = spec["end_counter"]
        end_candidates = spec["end_candidates"]
        start_key = (start_node, start_side)
        end_key = (end_node, end_side)
        used_start_values = used_by_side.get(start_key, [])
        used_end_values = used_by_side.get(end_key, [])

        start_bounds = renderer._get_node_bounds(start_node, positions)
        end_bounds = renderer._get_node_bounds(end_node, positions)
        start_pool = face_candidate_pools.get((edge_key, "start"), start_candidates)
        end_pool = face_candidate_pools.get((edge_key, "end"), end_candidates)

        start_pool = renderer._values_with_min_separation(
            start_pool, used_start_values, min_port_separation
        )
        end_pool = renderer._values_with_min_separation(
            end_pool, used_end_values, min_port_separation
        )

        start_value, end_value = renderer._choose_port_pair(
            start_candidates=start_pool,
            end_candidates=end_pool,
            start_counter=start_counter,
            end_counter=end_counter,
            used_start_values=used_start_values,
            used_end_values=used_end_values,
        )

        used_by_side.setdefault(start_key, []).append(start_value)
        used_by_side.setdefault(end_key, []).append(end_value)

        edge_anchor_map.setdefault(edge_key, {})["start_side"] = start_side
        edge_anchor_map.setdefault(edge_key, {})["end_side"] = end_side
        edge_anchor_map.setdefault(edge_key, {})["start"] = renderer._port_value_to_xy(
            start_bounds, start_side, start_value
        )
        edge_anchor_map.setdefault(edge_key, {})["end"] = renderer._port_value_to_xy(
            end_bounds, end_side, end_value
        )

    return edge_anchor_map


def get_edge_anchor_points(
    renderer: ASCIIRenderer,
    start: Any,
    end: Any,
    positions: Dict[Any, Tuple[int, int]],
) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    start_bounds = renderer._get_node_bounds(start, positions)
    end_bounds = renderer._get_node_bounds(end, positions)
    start_side, end_side = renderer._get_edge_sides(start_bounds, end_bounds)
    overlap_top = max(start_bounds["top"], end_bounds["top"])
    overlap_bottom = min(start_bounds["bottom"], end_bounds["bottom"])
    has_vertical_overlap = overlap_top <= overlap_bottom

    def _clamp_to_overlap(y_val: int) -> int:
        return min(max(y_val, overlap_top), overlap_bottom)

    if renderer._should_use_ports_for_edge(start, end):
        cached = renderer._edge_anchor_map.get((start, end), {})
        start_anchor = cached.get("start")
        end_anchor = cached.get("end")
        if start_anchor is not None and end_anchor is not None:
            cached_start_side = str(cached.get("start_side", start_side))
            cached_end_side = str(cached.get("end_side", end_side))
            horizontal_sides = (cached_start_side, cached_end_side) in {
                ("left", "right"),
                ("right", "left"),
            }
            if (
                horizontal_sides
                and has_vertical_overlap
                and start_anchor[1] != end_anchor[1]
            ):
                target_y = _clamp_to_overlap(start_anchor[1])
                start_anchor = (start_anchor[0], target_y)
                end_anchor = (end_anchor[0], target_y)
            return start_anchor, end_anchor

    start_anchor = renderer._get_center_anchor_for_side(start_bounds, start_side)
    end_anchor = renderer._get_center_anchor_for_side(end_bounds, end_side)
    horizontal_sides = (start_side, end_side) in {
        ("left", "right"),
        ("right", "left"),
    }
    if horizontal_sides and has_vertical_overlap:
        target_y = (overlap_top + overlap_bottom) // 2
        start_anchor = (start_anchor[0], target_y)
        end_anchor = (end_anchor[0], target_y)
    return (start_anchor, end_anchor)
