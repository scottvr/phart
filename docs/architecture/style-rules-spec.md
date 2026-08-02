# Style Rules Specification 

Status: Implemented in PHART v1.5.x (current branch behavior documented below).

- One rule model for both node and edge styling.
- Support predicates over:
  - element attributes (`self.<attr>`)
  - edge attributes (`edge.<attr>`)
  - source node attributes (`u.<attr>`)
  - destination node attributes (`v.<attr>`)
- Keep current simple workflows working (`--edge-color-rule`).
- Deterministic rule application order and precedence.
- Safe parser/evaluator (no `eval`, no Python code execution).



- Target element: the element currently being styled (`node`, `edge`, `connector`, or `panel_header`).
- Context object:
  - `self`: current target's attributes
  - `edge`: alias of `self` when target is `edge`
  - `node`: alias of `self` when target is `node`
  - `connector`: alias of `self` when target is `connector`
  - `panel_header`: alias of `self` when target is `panel_header`
  - `u`: source-node attributes for an edge
  - `v`: destination-node attributes for an edge
- Rule: a predicate + style assignment for a target type.

## Canonical Rule Model

Rules normalize into an internal structure such as:

```yaml
id: spouse-male
priority: 100 # optional integer; higher runs first
target: edge # edge | node | connector | panel_header
when: role == "spouse" and v.sex == "M"
set:
  color: blue # required field for color behavior
```

Notes:

- `priority` is optional. If omitted, default priority is `0`.
- Ties are resolved by declaration order (stable).
- First matching rule wins for each style field in `set`.

Supported targets:

- `node`
- `edge`
- `connector`
- `panel_header`

Supported `set` keys:

- `node`: `color`, `prefix`, `suffix`, `node_style`
- `edge`: `color` plus edge glyph keys (`arrow_*`, `line_*`, `corner_*`, `tee_*`, `cross`)
- `connector`: `color`, `prefix`, `suffix`
- `panel_header`: `color`, `prefix`, `suffix`

## Expression Language (v1.5)

### Operators

- Comparison: `==`, `!=`
- Membership: `in`, `not in`
- Boolean: `and`, `or`, `not`
- Parentheses: `(`, `)`

### Literals

- Strings: `'text'` or `"text"`
- Numbers: integers/floats
- Booleans: `true`, `false`
- Null: `null`
- Lists: `["A", "B", "C"]`

### Attribute references

- `self.role`, `edge.role`, `node.name`, `u.sex`, `v.sex`
- Unqualified names (for example `role`) are shorthand for `self.role`.

Resolution rules:

- Missing path resolves to `null`.
- Dot-path lookup supports nested dict traversal (`a.b.c`).
- Non-scalar values can only be used with `in`/`not in` in v1.5.

### String comparison semantics

Default string comparisons are case-insensitive in v1.5 for compatibility with existing edge color rule normalization.

## Rule Sources

### CLI (simple)

Keep existing:

```bash
--colors attr --edge-color-rule parenttype:father=bright_blue,mother=bright_magenta
```

This is compiled into equivalent advanced rules at parse time.

### CLI (advanced)

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

### Programmatic

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

## Evaluation Semantics

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

## Backward Compatibility

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

## Error Handling

- Parse errors include rule text and token position.
- Unknown target (`foo`) is rejected.
- Unsupported operator/type combinations are rejected with explicit diagnostics.
- Invalid color values preserve current color validation behavior.

## Security and Safety

- No dynamic code execution.
- Dedicated tokenizer/parser for expression language.
- Explicit recursion and token limits to avoid pathological input.

## Performance Expectations

- Compile all rules once during option normalization.
- Evaluate compiled AST per element.
- Target complexity: O(R _ E) for edges and O(R _ N) for nodes, with small constants.
- Optional future optimization: pre-index rules by referenced attributes.

## Implementation Status (Phased)

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

### Phase 3 Expansion: Legacy Feature Convergence

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


## Examples

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
