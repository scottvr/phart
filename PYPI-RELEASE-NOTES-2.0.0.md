# PHART 2.0.0 (Draft) - PyPI Release Notes

This release is a major jump from the current PyPI package (`1.1.4`) and includes substantial feature growth, CLI expansion, rendering improvements, and stricter runtime expectations.

## Why `2.0.0`

- The package on PyPI is far behind current `main`.
- User-visible behavior and CLI capabilities have expanded significantly.
- Python runtime requirement is now newer (`>=3.14`).

## Highlights

- New constrained-layout paneling workflow for large graphs:
  - target canvas width/height
  - partition overlap and affinity controls
  - connector compaction and panel header modes
  - partition metadata export APIs
- Stronger labeling pipeline:
  - node and edge label controls
  - synthesized multiline labels from attribute paths
  - bbox multiline/singleline rendering controls
- Richer edge rendering controls:
  - shared-port policies
  - bidirectional coalesce/separate modes
  - edge glyph presets and arrow styles
- Improved color and styling controls:
  - style rules
  - per-surface color overrides (node/label/subgraph/collision)
- Expanded Mermaid output support:
  - flow direction support
  - nested subgraph output
  - safer escaping and better label emission
- Continued SVG/HTML and documentation improvements.

## CLI and DX Improvements

- Large expansion of CLI options for layout, labels, colors, and pagination.
- Better newline handling for CLI output (friendlier piping and shell tooling).
- Broader test coverage for new renderer/layout/CLI behavior.

## Compatibility / Breaking Notes

- Python requirement is now `>=3.14`.
- Some validation paths are stricter (invalid style-rule/glyph combinations fail fast).
- If you are upgrading from `1.1.4`, review CLI usage and defaults before rolling into production scripts.

## Upgrade Guidance

- Start by running your existing commands with `phart --help` open and compare flags.
- If you parse output downstream, validate with your real graphs first.
- Consider pinning to `2.0.0` initially before adopting newer releases.
