# Style Rules Specification (Draft)

Status: Draft (design-only, not fully implemented)
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
- Arbitrary graph traversal in predicates (no multi-hop lookups in v1).
- Automatic GEDCOM semantic inference in PHART core.

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
  color: blue # v1 required for color behavior
```

Notes:

- `priority` is optional. If omitted, default priority is `0`.
- Ties are resolved by declaration order (stable).
- First matching rule wins for each style field in `set`.

## 6. Expression Language (v1)

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
- Non-scalar values can only be used with `in`/`not in` in v1.

### 6.4 String comparison semantics

Default string comparisons are case-insensitive in v1 for compatibility with existing edge color rule normalization.

## 7. Rule Sources

### 7.1 CLI (simple)

Keep existing:

```bash
--colors attr --edge-color-rule parenttype:father=bright_blue,mother=bright_magenta
```

This is compiled into equivalent advanced rules at parse time.

### 7.2 CLI (advanced)

Add repeated option:

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

`LayoutOptions` accepts normalized rules (new field proposed):

```python
style_rules=[
    {
        "target": "edge",
        "when": 'role == "spouse" and v.sex == "M"',
        "set": {"color": "blue"},
    }
]
```

## 8. Evaluation Semantics

1. Build evaluation context for each element.
2. Sort rules by:
   1. `priority` descending
   2. declaration order ascending
3. Evaluate `when` for matching `target`.
4. On match, apply keys in `set` not yet assigned.
5. Continue until all rules checked (or short-circuit if all requested fields set).

v1 color behavior:

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

## 13. Implementation Plan (Phased)

Phase 1:

- Introduce parser + canonical rule model.
- Add `--style-rule` and `--style-rules-file`.
- Compile legacy `--edge-color-rule` to canonical rules.
- Apply canonical rules to edge colors only.

Phase 2:

- Extend canonical rule application to node colors.
- Add explicit conflict tests and precedence coverage.

Phase 3:

- Extend `set` beyond color with explicit support for legacy decoration intent.
- Resolve legacy `NodeStyle.CUSTOM`, per-node decorators, and edge arrow/decorator customization through one unified rule path.

### 13.1 Phase 3 Expansion: Legacy Feature Convergence

#### Background

PHART has two historical styling tracks:

- Global/static style config (`NodeStyle`, box options, arrow glyph fields).
- Incomplete legacy intent for richer per-node/per-edge decorators.

The style-rule system should become the canonical per-element styling mechanism, while preserving backward compatibility for existing global options.

#### Proposed rule-settable fields (v3 target)

Node-target fields:

- `color`
- `prefix`
- `suffix`
- `node_style` (`minimal|square|round|diamond|custom`)
- `hpad`, `vpad` (optional overrides where safe)

Edge-target fields:

- `color`
- `arrow_up`, `arrow_down`, `arrow_left`, `arrow_right`
- `line_horizontal`, `line_vertical`
- `corner_ul`, `corner_ur`, `corner_ll`, `corner_lr`
- `tee_up`, `tee_down`, `tee_left`, `tee_right`

#### Precedence model for legacy + rules

1. Engine defaults
2. `LayoutOptions` explicit global values
3. Legacy compatibility mappings (if any)
4. Style rules (priority + declaration order)

Style rules are last-write authority for the fields they set.

#### Compatibility strategy

- Keep `NodeStyle` and existing decorator fields valid.
- Keep `custom_decorators` valid for programmatic users.
- Add migration path:
  - legacy custom decorators can be normalized into implicit node rules at initialization.
  - no immediate removal/deprecation until rule parity exists and is documented.

#### Constraints

- Multi-character glyphs are out of scope in the first Phase 3 increment; single-cell glyphs only.
- Rule-driven style changes must not violate routing assumptions (cell widths, arrow locking).
- If a rule sets an unsupported field for a target, fail fast with precise diagnostics.

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
