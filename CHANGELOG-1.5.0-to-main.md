# Changelog: Changes Since `release-1.5.0` (Target: `2.0.6`)

Comparison range: `origin/release-1.5.0..main`

Generated on: 2026-05-31 (America/Chicago)

## Summary

- Commits: 23
- Files changed (net): 22
- Diffstat (net): 2760 insertions, 331 deletions

## Highlights

### Added

- DOT subgraph metadata extraction and rendering support, including nested subgraph handling.
- Mermaid output improvements:
  - flow direction mapping from layout flow (`TD`, `BT`, `LR`, `RL`)
  - nested subgraph emission from metadata
  - safer node-id generation/escaping
  - edge-label support with Mermaid-safe escaping
- New CLI/layout options:
  - `--subgraph-fit-edge-labels`
  - `--bbox-singleline-labels` (with multiline bbox labels now default-enabled)
  - explicit ANSI color overrides:
    - `--node-color`
    - `--label-color`
    - `--subgraph-color`
    - `--collision-color`

### Changed

- BBox multiline label behavior now defaults to enabled (`bbox_multiline_labels=True`).
- CLI text output now ensures newline-terminated stdout/file output for shell compatibility.

### Fixed

- Follow-up fixes to the initial subgraph implementation.
- Mermaid output robustness fixes.
- CI format/test breakage fix.

### Docs and examples

- Large README refresh and expansion.
- New docs:
  - `docs/architecture/cli-runtime-architecture.md`
  - `RAINBOW_COLORING.md`
- New/updated internet DOT examples:
  - `examples/internet.dot`
  - `examples/internet-digraph.dot`
  - `examples/internet-dotapprox.dot`
  - `examples/internet-pbp.dot`

### Tests

- Expanded CLI and renderer tests covering:
  - subgraph parsing/rendering behavior
  - subgraph bbox sizing and edge-label fit
  - mermaid output behavior and escaping
  - color override flags/options

## Full commit list (oldest first)

- `63a1f9a` (2026-03-15) Merge pull request #22 from scottvr/dev-latest
- `4dc9fb9` (2026-03-15) Update README.md
- `0b06505` (2026-03-15) fix format so CI tests work
- `612bbc2` (2026-03-15) Update README.md
- `adde30d` (2026-03-15) Update README.md
- `8e3c6e6` (2026-03-15) Update README.md
- `7f2c87b` (2026-03-15) Update README.md
- `e40d58f` (2026-03-15) Update README.md
- `cd8da42` (2026-03-15) Create RAINBOW_COLORING.md
- `7079278` (2026-03-15) Update README.md
- `8512664` (2026-03-15) Update phart.release-notes.md
- `926cbb9` (2026-03-15) Update phart.release-notes.md
- `958aa4d` (2026-03-16) Update README.md
- `84a07fa` (2026-03-16) Update README.md
- `b3afa70` (2026-03-16) Update README.md
- `a186f7e` (2026-03-16) Merge branch 'main' into dev-latest
- `376996d` (2026-04-10) inital working pass of subgraph support
- `3d149cd` (2026-04-11) fix bugs from first attempt
- `5ca3522` (2026-04-11) add some specific colorizer options (nodes, text, subgraphs, collisions)
- `994134e` (2026-04-11) work on mmd fixes
- `fdc4e50` (2026-04-11) dot dot test
- `376fc23` (2026-04-11) fin. going to bed. i don't even remember
- `e3b4821` (2026-04-11) subraphs and mmd fixes done
