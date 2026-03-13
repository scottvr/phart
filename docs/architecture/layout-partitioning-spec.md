# Constrained Layout Partitioning Spec (Draft)

Status: Draft (architecture/design)
Audience: maintainers and advanced users

## 1. Problem

Output pagination solves viewport slicing after render, but it does not reduce routing complexity or visual density when a layout naturally expands to thousands of columns.

We need an optional layout mode that constrains width (and optionally height) during layout, producing readable partitioned diagrams rather than one giant canvas.

## 2. Goals

- Constrain rendered width at layout time.
- Preserve semantic readability for genealogical/tree-like graphs.
- Keep the current pagination feature intact and independent.
- Work across `flow` directions (`down|up|left|right`).

## 3. Non-Goals

- Exact global optimum partitioning.
- Generic graph decomposition for every topology in v1.
- Replacing existing layout strategies.

## 4. Terminology

- Partition: a bounded sub-layout rendered as one panel/page.
- Panel: output canvas for a partition after routing.
- Cross-partition edge: edge whose endpoints land in different partitions.
- Connector stub: marker indicating continuation to/from another partition.

## 5. User-Facing Surface

New layout modifier:

- `--constrained` (applies partitioning to compatible layout strategies)

New options:

- `--target-canvas-width N|auto` (required when `--constrained` is enabled)
- `--target-canvas-height N|auto` (optional; disabled when omitted)
- `--partition-overlap N` (default `0`; duplicate context columns/rows)
- `--cross-partition-edge-style {stub,none}` (default `stub`)
- `--partition-order {natural,size}` (default `natural`)

Notes:

- `auto` width/height uses terminal dimensions only when writing to terminal.
- Existing `--paginate-output-width/height` remains a post-render viewport feature.

## 6. Conceptual Model

Constrained mode performs:

1. Initial rank assignment from the selected flow direction.
2. Estimate node bbox footprint (including labels, padding, and style).
3. Partition ranked nodes into contiguous rank bands that fit target width.
4. Route each partition independently.
5. Emit connector stubs for cross-partition edges.

This avoids drawing the full ultra-wide graph first and slicing later.

## 7. Partitioning Algorithm (v1)

For `flow=down|up`:

- Partition by contiguous depth/rank ranges.
- Each partition grows rank-by-rank until estimated width would exceed target width.
- Start a new partition at the next rank.

For `flow=left|right`:

- Apply the same logic on transposed axes (breadth/rank in flow axis).

Packing heuristics:

- Keep spouses/parents/children together when possible:
  - Assign affinity penalties for splitting couples and immediate parent-child edges.
  - Allow split only when width constraint would otherwise be violated.

Determinism:

- Given same graph/options, partition assignment must be stable.

## 8. Cross-Partition Edges

When an edge crosses partitions:

- In source panel, draw a short stub + marker like `-> [P3]`.
- In destination panel, draw `from [P1] ->` near the target side.

Connector metadata:

- `source_partition`, `dest_partition`, `edge_id`, `u`, `v`.

`cross-partition-edge-style=none` suppresses markers.

## 9. Data Model Additions

`LayoutOptions` additions (proposed):

- `constrained: bool = False`
- `target_canvas_width: Optional[int] = None`
- `target_canvas_height: Optional[int] = None`
- `partition_overlap: int = 0`
- `cross_partition_edge_style: str = "stub"`
- `partition_order: str = "natural"`

Renderer/runtime additions:

- `PartitionPlan` with:
  - list of partitions
  - node-to-partition mapping
  - cross-partition edge list

## 10. Rendering Semantics

- Each partition gets its own local coordinate system.
- Node ids remain globally unique; labels/attrs unchanged.
- Colors/style rules evaluate against original graph attrs.
- Page index maps to partition index by default.

Interaction with existing output pagination:

- If constrained mode is enabled, output pagination can still apply within each panel.
- Recommended behavior is to disable viewport pagination by default when constrained mode is active, unless explicitly requested.

## 11. Failure Modes and Safeguards

- Node wider than target width:
  - keep node intact and allow controlled overflow for that panel.
- Dense cyclic graph where partitioning explodes connectors:
  - emit warning and suggest fallback to regular layout + output pagination.
- `auto` width/height without terminal stdout:
  - error with explicit guidance to provide numeric dimensions.

## 12. Metrics and Acceptance Criteria

Functional:

- Graphs that previously rendered at >1000 columns can be rendered into bounded panels.
- Partitioning honors flow direction and remains deterministic.
- Cross-partition edges are traceable via connector ids.

Quality:

- No node text truncation introduced by partitioning itself.
- Comparable or better readability than viewport slicing on family-tree graphs.

## 13. Phased Delivery

Phase A:

- Width-only constrained partitioning (`target_canvas_width`).
- Down/up flow support first.
- Stub connectors and panel ordering.

Phase B:

- Height constraint support.
- Left/right flow support parity.
- Overlap context rows/columns.

Phase C:

- Affinity penalty tuning and optional connector compaction.
- Programmatic export of partition metadata.

## 14. Open Questions

- Do we want a dedicated output mode for multi-panel files by default?
- Should connector stubs be style-rule targetable (e.g., `target=connector`)?
- Should panel headers include lineage summary (root ids, rank range)?
