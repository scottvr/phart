## DOT Subgraph Support v1 (Internet.dot-Driven, Label-Aware)

### Summary

- Implement **nested DOT subgraph/cluster support** with visible container boxes in text output and nested blocks in Mermaid output.
- Keep behavior safe: auto-enabled for DOT only, no CLI flag changes, no impact on non-subgraph inputs.
- Reuse existing label code paths where possible; subgraph titles are **always shown** when present in DOT.
- Subgraph containers are **independent of node `--bboxes`** and must coexist with your current spacing/bbox tuning workflow.

### Implementation Changes

- DOT ingest:
  - Replace current single-pass conversion with recursive pydot flattening to capture nested subgraphs, member nodes, and internal edges.
  - Preserve node/edge attributes (including labels) and attach subgraph metadata (tree + membership + labels) to graph-level metadata.
  - Remove accidental synthetic `cluster*` nodes unless they are explicitly real graph nodes.
- Edge semantics:
  - For edges targeting subgraph IDs, apply deterministic **boundary-pair expansion** (no all-to-all explosion), with dedupe.
- Layout/render:
  - Add soft subgraph contiguity bias (tie-breaker only) so existing layout behavior remains stable.
  - Compute nested container rectangles from node bounds with fixed compact padding.
  - Draw subgraph borders/titles before edges/nodes; expand canvas calculations to include container extents.
- Label reuse:
  - Use existing label normalization utilities for subgraph title text normalization/quoting behavior consistency.
  - Keep current node/edge label behavior intact (`--labels` continues to govern node/edge labels only).
- Mermaid:
  - Emit nested `subgraph` blocks with preserved membership and expanded edges from the same metadata.

### Test Plan

- `examples/internet.dot` acceptance:
  - Both `cluster_home` and `cluster_internet` render with titles.
  - `DNS` and `Backbone -> DNS` appear (no missing subgraph-internal content).
  - Output remains readable under bbox + spacing settings like your screenshot scenario.
- Parser/layout regressions:
  - Nested clusters, boundary edge expansion determinism, no phantom cluster nodes.
  - Existing non-subgraph DOT/GraphML/PlantUML tests remain unchanged and passing.
- Mermaid regressions:
  - Nested blocks emitted only when subgraph metadata exists; flat output unchanged otherwise.

### Assumptions

- v1 scope is DOT subgraphs only.
- Subgraph labels always render when provided in DOT.
- Subgraph containers render regardless of node `--bboxes`.
- No new CLI options in v1 (compact fixed defaults first).
