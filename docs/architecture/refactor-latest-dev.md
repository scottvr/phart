# Refactor Plan for `latest-dev`

## Why now

Recent feature work added meaningful capability (PlantUML input, multiple output formats, SVG modes, richer color handling), but core modules now mix responsibilities:

- `src/phart/renderer.py` contains rendering engine logic plus output-format-specific serialization details.
- `src/phart/cli.py` contains argument parsing, input-format detection, Python script execution, and output rendering conversion.
- several concerns (input loading, format conversion, ANSI color translation) are coupled through module internals.

This plan introduces stable seams first, then moves code behind those seams while preserving behavior.

## Target architecture

### `core`

Owns domain contracts and neutral data structures.

- `core/contracts.py`
  - loader/output/runner protocols
  - output render configuration dataclass

### `io/input`

Owns source loading/parsing concerns.

- DOT/GraphML/PlantUML auto-detection and parsing
- Python file execution and captured renderer output

### `io/output`

Owns serialization/format conversion concerns.

- text
- ditaa / ditaa-puml
- svg
- html

### `rendering`

Owns canvas composition and graph drawing internals.

- ASCII/Unicode canvas production
- edge routing, node drawing, port selection
- color painting and conflict handling

`ASCIIRenderer` remains a stable façade during the migration.

## Principles

- keep CLI flags and behavior stable during refactor
- keep public imports stable (`phart.ASCIIRenderer`, existing module paths)
- make changes in small, reviewable, behavior-preserving slices
- add compatibility shims before moving public-facing APIs

## Execution stages

1. Stage 1: Architecture doc + interface contracts

- Add `docs/architecture/refactor-latest-dev.md`
- Add protocol/dataclass contracts in `core/contracts.py`

2. Stage 2: Extract captured output conversion

- Move `.py` captured text conversion from CLI to `io/output`
- Keep logic behavior-identical

3. Stage 3: Extract input loaders from CLI

- Move DOT/GraphML/PlantUML parsing and `.py` runner plumbing into `io/input`
- Keep CLI as orchestration only

4. Stage 4: Extract output formatters from renderer

- Move ditaa/svg/html formatters to `io/output`
- Keep `ASCIIRenderer.render()` as canonical canvas/text producer

5. Stage 5: Split rendering internals

- carve `renderer.py` into rendering-focused modules (`canvas`, `edges`, `nodes`, `ansi`)
- keep façade class and backward-compatible imports

6. Stage 6: Hardening

- golden tests across representative graphs and all output formats
- compatibility tests for legacy imports

## Success criteria

- no CLI behavior regressions
- no public import breakage
- reduced complexity in `cli.py` and `renderer.py`
- adding new input/output formats no longer requires touching central orchestrator code
