# Style Rules Specification (v1.5, Implemented)

Status: Implemented in PHART v1.5.x (current branch behavior documented below).
Audience: CLI users, library users, and maintainers

## 1. Problem Statement

PHART currently supports attribute-driven edge coloring via `--edge-color-rule`, but it is limited to direct edge-attribute equality matches. Users need richer conditions, including rules that combine edge attributes with endpoint node attributes (e.g. spouse edge color based on destination sex), while keeping simple cases ergonomic.

The design goal is a unified rule model that can style both nodes and edges without introducing multiple disconnected rule systems.

## 2. Goals

- One rule model for both node and edge styling.
- Support predicates over:
  - element attributes (`self.<attr>`)
  - edge attributes (`edge.<attr>`)
  - source node attributes (`u.<attr>`)
  - destination node attributes (`v.<attr>`)
- Keep current simple workflows working (`--edge-color-rule`).
- Deterministic rule application order and precedence.
- Safe parser/evaluator (no `eval`, no Python code execution).

## 3. Non-Goals

- General-purpose scripting language.
- Arbitrary graph traversal in predicates (no multi-hop lookups in v1.5).

## 4. Terminology

- Target element: the element currently being styled (`node` or `edge`).
- Context object:
  - `self`: current target's attributes
  - `edge`: alias of `self` when target is `edge`
  - `node`: alias of `self` when target is `node`
  - `u`: source-node attributes for an edge
  - `v`: destination-node attributes for an edge
- Rule: a predicate + style assignment for a target type.

## 5. Canonical Rule Model

Rules normalize into this internal structure:

```yaml
id: spouse-male
priority: 100 # optional integer; higher runs first
target: edge # edge | node
when: role == "spouse" and v.sex == "M"
set:
  color: blue # required field for color behavior
```

Notes:

- `priority` is optional. If omitted, default priority is `0`.
- Ties are resolved by declaration order (stable).
- First matching rule wins for each style field in `set`.

## 6. Expression Language (v1.5)

### 6.1 Operators

- Comparison: `==`, `!=`
- Membership: `in`, `not in`
- Boolean: `and`, `or`, `not`
- Parentheses: `(`, `)`

### 6.2 Literals

- Strings: `'text'` or `"text"`
- Numbers: integers/floats
- Booleans: `true`, `false`
- Null: `null`
- Lists: `["A", "B", "C"]`

### 6.3 Attribute references

- `self.role`, `edge.role`, `node.name`, `u.sex`, `v.sex`
- Unqualified names (for example `role`) are shorthand for `self.role`.

Resolution rules:

- Missing path resolves to `null`.
- Dot-path lookup supports nested dict traversal (`a.b.c`).
- Non-scalar values can only be used with `in`/`not in` in v1.5.

### 6.4 String comparison semantics

Default string comparisons are case-insensitive in v1.5 for compatibility with existing edge color rule normalization.

## 7. Rule Sources

### 7.1 CLI (simple)

Keep existing:

```bash
--colors attr --edge-color-rule parenttype:father=bright_blue,mother=bright_magenta
```

This is compiled into equivalent advanced rules at parse time.

### 7.2 CLI (advanced)

CLI supports repeated option:

```bash
--style-rule 'edge: role=="spouse" and v.sex=="M" -> color=blue'
--style-rule 'edge: role=="spouse" and v.sex=="F" -> color=green'
```

Optional file input for complex sets:

```bash
--style-rules-file rules.yaml
```

File format: YAML or JSON containing a `rules` array using canonical model.

### 7.3 Programmatic

`LayoutOptions` accepts raw canonical rule dicts via `style_rules`:

```python
style_rules=[
    {
        "target": "edge",
        "when": 'role == "spouse" and v.sex == "M"',
        "set": {"color": "blue"},
    }
]
```

Implementation note:

- `style_rules` is the public/raw input field.
- Rules are compiled during `LayoutOptions` initialization into `_compiled_style_rules` for runtime evaluation.
- `_compiled_style_rules` is internal and not part of the public stability contract.

## 8. Evaluation Semantics

1. Build evaluation context for each element.
2. Sort rules by:
   1. `priority` descending
   2. declaration order ascending
3. Evaluate `when` for matching `target`.
4. On match, apply keys in `set` not yet assigned.
5. Continue until all rules checked (or short-circuit if all requested fields set).

v1.5 color behavior:

- For edge rendering, `set.color` affects edge color map.
- For node rendering, `set.color` affects node color map.

Fallbacks:

- If no style rule matches, use existing color mode behavior (`source|target|path` etc.).

## 9. Backward Compatibility

- `--edge-color-rule` remains supported.
- Existing `edge_color_rules` field remains accepted.
- Internally, both legacy and advanced forms normalize to one evaluation path.

Legacy mapping example:

```text
--edge-color-rule role:spouse=blue
```

normalizes to:

```yaml
- target: edge
  when: edge.role == "spouse"
  set: { color: blue }
```

## 10. Error Handling

- Parse errors include rule text and token position.
- Unknown target (`foo`) is rejected.
- Unsupported operator/type combinations are rejected with explicit diagnostics.
- Invalid color values preserve current color validation behavior.

## 11. Security and Safety

- No dynamic code execution.
- Dedicated tokenizer/parser for expression language.
- Explicit recursion and token limits to avoid pathological input.

## 12. Performance Expectations

- Compile all rules once during option normalization.
- Evaluate compiled AST per element.
- Target complexity: O(R _ E) for edges and O(R _ N) for nodes, with small constants.
- Optional future optimization: pre-index rules by referenced attributes.

## 13. Implementation Status (Phased)

Phase 1 completed:

- Parser + canonical rule model implemented.
- `--style-rule` and `--style-rules-file` implemented.
- Legacy `--edge-color-rule` is compiled to canonical edge color rules.
- Canonical rules apply to edge colors.

Phase 2 completed:

- Canonical rules apply to node colors.
- Conflict/precedence behavior covered in tests.

Phase 3 completed for current scope:

- `set` supports node decorators (`prefix`, `suffix`, `node_style`) and edge glyph fields (`arrow_*`, `line_*`, `corner_*`, `tee_*`, `cross`).
- Global edge presets and arrow style options implemented.
- Legacy globals remain operational; style-rules override overlapping keys.

### 13.1 Phase 3 Expansion: Legacy Feature Convergence

#### Background

PHART has two historical styling tracks:

- Global/static style config (`NodeStyle`, box options, arrow glyph fields).
- Incomplete legacy intent for richer per-node/per-edge decorators.

The style-rule system should become the canonical per-element styling mechanism, while preserving backward compatibility for existing global options.

#### Implemented rule-settable fields (v1.5)

Node-target fields:

- `color`
- `prefix`
- `suffix`
- `node_style` (`minimal|square|round|diamond|custom`)

Edge-target fields:

- `color`
- `arrow_up`, `arrow_down`, `arrow_left`, `arrow_right`
- `line_horizontal`, `line_vertical`
- `corner_ul`, `corner_ur`, `corner_ll`, `corner_lr`
- `tee_up`, `tee_down`, `tee_left`, `tee_right`
- `cross`

#### Precedence model (implemented)

1. Engine defaults
2. `LayoutOptions` explicit global values
3. Style rules (priority + declaration order)

Style rules are last-write authority for the fields they set.

#### Compatibility strategy (implemented)

- Keep `NodeStyle` and existing decorator fields valid.
- Keep `custom_decorators` valid for programmatic users.
- Do not auto-map legacy globals into implicit style rules in v1.5.

#### Constraints

- Multi-character glyphs are not supported in v1.5; single-cell glyphs only.
- Rule-driven style changes must not violate routing assumptions (cell widths, arrow locking).
- If a rule sets an unsupported field for a target, fail fast with precise diagnostics.

### 13.2 Phase 3 Implementation Checklist

Execution board (feature branch: `feature/style-rule-node-style`):

| ID  | Workstream                 | Status               | Notes                                                                                              |
| --- | -------------------------- | -------------------- | -------------------------------------------------------------------------------------------------- |
| A   | Contracts and option model | Completed (Phase 3a) | Key/target validation active for `node:{color,prefix,suffix,node_style}` and `edge:{color,glyphs}` |
| B   | Node rendering integration | Completed (Phase 3a) | Rule-driven `prefix`/`suffix`/`node_style` wired in shared node line resolution (layout + draw)    |
| C   | Edge rendering integration | Completed (Phase 3b) | Rule-driven `arrow_*`, `line_*`, `corner_*`, `tee_*`, and `cross` integrated into routing/merge    |
| D   | Legacy convergence path    | Completed (Decision) | No implicit legacy-to-rule mapper in Phase 3; legacy globals remain, style-rules are authoritative |
| E   | CLI / UX surface           | Completed            | CLI/docs cover style-rules plus global edge presets/arrow modes                                    |
| F   | Test plan                  | In Progress          | Node-style + edge-glyph rule and validation tests added; parity tests pending                      |
| G   | Rollout sequencing         | Completed (Phase 3)  | Steps 1-5 complete for style-rule/node-style/edge-glyph scope                                      |

#### A. Contracts and option model

- [x] Extend canonical style-rule schema docs with allowed `set` keys per `target`.
- [x] Add `StyleSetKey` validation in rule compilation (reject unknown keys early).
- [x] Add target/key compatibility checks (for example, disallow `arrow_up` on `node`).
- [x] Keep `LayoutOptions` legacy fields unchanged for compatibility (`node_style`, `custom_decorators`, arrow glyph fields).
- [x] Decision: no explicit compatibility mapper in Phase 3.

Acceptance criteria:

- Invalid key/target combinations fail at startup with precise error messages.
- Existing code paths without style rules behave exactly as before.

#### B. Node rendering integration

- [x] Introduce node style-rule evaluator (`target=node`) that can resolve:
  - `color`
  - `prefix`
  - `suffix`
  - `node_style`
  - optional safe padding overrides (`hpad`, `vpad`) only when `bboxes` is true.
- [x] Apply resolved node style fields in one place before node glyph composition.
- [x] Ensure bbox sizing uses post-rule effective text/decorators.
- [x] Ensure multiline label flow remains correct with rule-modified node text wrappers.

Acceptance criteria:

- Per-node rule-driven decorators render deterministically.
- No regressions in existing bbox/multiline tests.

#### C. Edge rendering integration

- [x] Extend edge style-rule evaluator (`target=edge`) beyond `color` to support glyph keys:
  - arrows: `arrow_up/down/left/right`
  - segments: `line_horizontal/line_vertical`
  - junctions: `corner_*`, `tee_*`
- [x] Apply resolved glyphs through routing/canvas paint path without bypassing conflict logic.
- [x] Preserve arrow lock semantics for overlapping edges.
- [x] Keep single-cell glyph invariant enforced at validation time.

Acceptance criteria:

- Rule-selected edge glyphs appear consistently on all routed segments.
- Overlap and bidirectional behavior remain stable.

#### D. Legacy convergence path

- [x] Decision: no implicit legacy-to-rule mapper in Phase 3.
- [x] Keep legacy global options operational (`NodeStyle`, `custom_decorators`, edge glyph fields).
- [x] Define precedence for implemented scope:
  1. defaults
  2. explicit `LayoutOptions` globals
  3. style rules
- [ ] Add debug/trace hook (optional) to inspect effective style source for a node/edge.

Acceptance criteria:

- Legacy scripts continue to render with existing globals.
- Style-rules remain the authoritative per-element override for keys they set.

#### E. CLI / UX surface

- [x] Keep `--style-rule` and `--style-rules-file` unchanged.
- [x] Document new allowed `set` keys and target restrictions in `README.md` and `docs/index.md`.
- [x] Add end-to-end CLI examples for:
  - node decorators via rules
  - edge arrow/glyph override via rules
- [x] Improve CLI error text for unsupported fields and multi-character glyph attempts.

Acceptance criteria:

- Users can discover field support from `--help` and docs without reading code.

#### F. Test plan (required before merge)

- [x] Parser/validator tests:
  - unknown keys
  - wrong target/key combinations
  - multi-char glyph rejection
- [x] Renderer tests:
  - per-node decorator/prefix/suffix application
  - per-edge glyph key application
  - arrow lock/overlap correctness under rule changes
- [ ] Compatibility tests:
  - `NodeStyle` + `custom_decorators` parity vs pre-Phase-3 output
  - legacy edge glyph options parity
- [x] CLI tests:
  - valid/invalid `--style-rule` with new keys
  - style-rules-file examples for node + edge keys

Acceptance criteria:

- New coverage includes behavior assertions and key validation coverage.
- No regressions in existing edge routing and bbox suites.

#### G. Rollout sequencing

1. Validation + schema enforcement (implemented).
2. Node rule fields (`prefix/suffix/node_style`) integration (implemented).
3. Edge glyph fields integration (implemented).
4. Legacy convergence decision + precedence finalization (implemented).
5. Docs/examples finalization (implemented).

## 14. Test Matrix (Minimum)

- Parser:
  - valid/invalid operators, parentheses, quoting, list literals.
- Context access:
  - edge/self/u/v path lookups and missing keys.
- Compatibility:
  - `--edge-color-rule` output equals canonical rule output.
- Precedence:
  - priority and declaration-order tie breaks.
- CLI quoting:
  - examples with shell-safe quoting for `and`/`or` expressions.

## 15. Examples

Simple edge attr:

```yaml
rules:
  - target: edge
    when: role == "parent" and parenttype == "mother"
    set: { color: bright_magenta }
```

Edge + endpoint attr:

```yaml
rules:
  - target: edge
    when: role == "spouse" and v.sex == "M"
    set: { color: blue }
  - target: edge
    when: role == "spouse" and v.sex == "F"
    set: { color: green }
```

Node rule:

```yaml
rules:
  - target: node
    when: sex == "F"
    set: { color: bright_magenta }
```
