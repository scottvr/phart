# PHART CLI Runtime Architecture (First Pass)

This document is a developer-oriented walkthrough of the current runtime architecture, centered on the CLI entrypoint and the common path:

```bash
phart examples/internet.dot
```

It is intentionally descriptive of the current implementation, not a redesign proposal.

## 1. High-level module map

PHART currently follows a thin-orchestrator + rich-renderer split:

1. `src/phart/cli.py`

- Parses CLI args.
- Normalizes ambiguous options.
- Constructs render configs and `LayoutOptions`.
- Branches between Python-input and graph-file input modes.

2. `src/phart/io/input/*`

- Input adapters:
  - `loader.py`: chooses PlantUML / GraphML / DOT parser path.
  - `python_runner.py`: executes Python source and captures stdout.
  - `dot.py`, `graphml.py`, `plantuml.py`: parse into `networkx.DiGraph`.
  - `__init__.py`: intentionally thin wrapper exports (`_impl`-style indirection) used during the ongoing refactor.

3. `src/phart/renderer.py`

- Core engine and integration point.
- Owns graph, layout manager, canvas, color canvas, rendering flow.
- Delegates domain work to `src/phart/rendering/*` helpers.

4. `src/phart/layout.py`

- Node positioning for all layout strategies.
- Optional constrained partition planning (`PartitionPlan`).

5. `src/phart/io/output/*`

- Output adapters:
  - `dispatcher.py`: render from `ASCIIRenderer` by output format.
  - `captured_text.py`: transform captured text output for Python-input mode.
  - `pagination.py`: ANSI-aware output pagination.

6. `src/phart/styles.py` and `src/phart/style_rules.py`

- `LayoutOptions` is the central runtime configuration object.
- Validation/normalization and style-rule compilation happen in `LayoutOptions.__post_init__`.

## 2. Entry point and control flow

Packaging entrypoint:

- `pyproject.toml` registers `phart = "phart.cli:main"`.

Runtime entrypoint:

- `main()` in `src/phart/cli.py`.

Important `main()` responsibilities:

1. Parse args:

- `parse_args()` handles:
  - pre-normalization for optional-arg ambiguities (`--colors`, `--node-labels`, `--edge-labels`)
  - `--` split for script args
  - unknown-arg capture via `parse_known_args`

2. Build output configs:

- `OutputRenderConfig` (for captured-text mode)
- `RendererOutputConfig` (for direct renderer mode)

3. Validate pagination (text-only, positive sizes, range checks).

4. Branch by input suffix:

- `.py` -> execute source and format captured text.
- non-`.py` -> load renderer from source file and render directly.

5. Emit output:

- stdout or file.
- enforce trailing newline.

Error model from `main()`:

- returns `0` on success.
- returns `2` for CLI misuse cases (unknown args, wrong `--` usage).
- returns `1` for runtime exceptions (wrapped as `Error: ...`).

## 3. Concrete trace: `phart examples/internet.dot`

This is the typical happy path for graph-file input.

1. **CLI parse and normalization**

- `main()` -> `parse_args()`.
- For this command, there are no option flags, so defaults apply.
- `parse_args()` still runs normalization helpers and explicit-field tracking.

2. **Render/output config creation**

- `main()` builds `OutputRenderConfig` and `RendererOutputConfig`.
- `output_format` defaults to `"text"`.
- pagination is disabled unless `--paginate-*` was provided.

3. **Mode selection**

- input suffix is `.dot`, so `main()` takes the non-`.py` branch.

4. **Build runtime layout options**

- `create_layout_options(args, explicit_layout_fields)` creates `LayoutOptions`.
- Normalization/validation occurs in `LayoutOptions.__post_init__`:
  - strategy name normalization
  - charset/ANSI compatibility checks
  - spacing and style validation
  - style-rule compilation to `_compiled_style_rules`

5. **Load renderer from file**

- `load_renderer_from_file(path, options=...)` in `io/input/loader.py`:
  - reads file content
  - chooses parser:
    - PlantUML by extension
    - GraphML by XML signature
    - otherwise DOT
- for `internet.dot`, DOT path is selected.

6. **DOT parse to graph**

- `ASCIIRenderer.from_dot(content, options=...)`
- `parse_dot_to_digraph()` (in `io/input/dot.py`) uses `pydot`, then:
  - extracts nodes/edges/subgraph structure
  - builds `networkx.DiGraph`
  - stores subgraph metadata on `graph.graph["_phart_subgraphs"]`

7. **Renderer construction**

- `ASCIIRenderer.__init__` stores graph/options and creates `LayoutManager`.
- Initializes canvas/color state and edge/color caches.

8. **Output dispatch**

- `render_renderer_output(renderer, config=...)` in `io/output/dispatcher.py`.
- text format -> `renderer.render(markdown_safe=...)`.

9. **Layout pass**

- `ASCIIRenderer.render()` -> `layout_manager.calculate_layout()`.
- strategy default is `"auto"`:
  - currently resolves to hierarchical for most non-trivial graphs.
- if constrained mode were enabled, layout would route through `_layout_constrained`.

10. **Canvas render pass**

- `render()` -> `_render_single_canvas(...)`:
  - prepare layout for subgraph containers
  - initialize canvas dimensions
  - draw subgraph boxes (if metadata present)
  - initialize color maps
  - compute edge anchors/ports
  - route/draw edges
  - draw nodes
  - draw subgraph titles
  - convert canvas rows to final text

11. **Write output**

- back in `main()`:
  - optional pagination (if enabled)
  - newline normalization
  - stdout write (or file write)

## 4. Two runtime pipelines: graph-input vs python-input

PHART has two distinct pipelines that converge at output formatting:

1. Graph-input pipeline (`.dot`, `.graphml`, `.puml`, etc.)

- parse source -> `ASCIIRenderer` -> render via `io/output/dispatcher.py`

2. Python-input pipeline (`.py`)

- execute user module/function under injected `ASCIIRenderer.default_options`
- capture stdout text
- post-format captured text via `io/output/captured_text.py`

This split lets CLI options affect:

- direct graph rendering in graph-input mode
- script-generated rendering in python-input mode (without editing user script code).

## 5. Core data contracts

### `LayoutOptions` (configuration spine)

`LayoutOptions` carries nearly all rendering/layout behavior toggles:

- layout strategy and constrained-partition settings
- node/edge style controls
- labels
- ANSI/color/style rules
- spacing and bbox details

It is the main data contract across:

- CLI option translation
- renderer behavior
- layout manager decisions

### Subgraph metadata (`graph.graph["_phart_subgraphs"]`)

DOT parsing enriches the graph with metadata used later by rendering:

- hierarchical subgraph tree
- node-to-subgraph path
- ordering/depth data

Renderer uses this to draw enclosing subgraph boxes/titles and to preserve structure in Mermaid export.

### Partition metadata (`PartitionPlan`)

When constrained mode is on, `LayoutManager` produces `PartitionPlan`:

- partition membership
- layer ranges
- cross-partition edges

Renderer consumes this plan for panelized output and connector annotations.

## 6. Architectural strengths (current)

1. CLI orchestration is explicit and readable.
2. Input/output adapters are separated from core rendering.
3. `LayoutOptions` provides a unified behavior contract.
4. Rendering internals are being modularized via `rendering/*` helpers.
5. DOT subgraph metadata is preserved and reused downstream.

## 7. Architectural seams to keep in mind

1. `ASCIIRenderer` is still a large integration surface.

- Many responsibilities are delegated, but lifecycle/state orchestration remains centralized.

2. Two output-formatting implementations exist:

- direct renderer output (`rendering/output.py` + dispatcher)
- captured-text output (`io/output/captured_text.py`)
- This is practical, but format behavior must stay aligned across both paths.

3. CLI normalization does non-trivial argument rewriting before parse.

- Helpful for UX, but easy to miss when debugging argument behavior.

4. Merge precedence for `.py` mode is nuanced:

- `ASCIIRenderer.default_options` + `merge_layout_options()` + explicit CLI-field tracking.
- Very useful, but worth re-checking whenever new options are added.

5. Some wrapper layers are transitional refactor scaffolding.

- You will see small pass-through functions and `_impl` naming in adapter modules.
- Treat these as migration seams for separation-of-concerns work, not permanent architecture targets.

## 8. Fast orientation checklist for contributors

If you are adding/changing behavior, this usually helps:

1. New CLI option:

- add arg in `parse_args()`
- map to `LayoutOptions` in `create_layout_options()`
- add to `CLI_LAYOUT_FIELD_MAP` if precedence-sensitive in `.py` mode

2. New input format:

- add parser in `io/input/`
- wire in `io/input/loader.py`
- expose via `ASCIIRenderer.from_*` if applicable

3. New output format:

- add to `OUTPUT_FORMATS`
- update dispatcher and captured-text formatter paths as needed
- verify pagination compatibility expectations

4. New layout strategy:

- add strategy option mapping in CLI
- implement in `LayoutManager.calculate_layout()`
- verify constrained-mode compatibility rules if relevant
