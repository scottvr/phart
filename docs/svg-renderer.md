# SVG Renderer

PHART provides two SVG output modes:

- `text` mode (default): writes cell content as SVG `<text>` elements.
- `path` mode: writes glyph outlines as SVG `<path>` elements.

`path` mode is useful when you need deterministic output across environments (no font substitution drift in SVG viewers).

## Install

```bash
pip install phart[svg]
```

`phart[svg]` includes:

- `fonttools` (glyph outline extraction)
- `matplotlib` (font family name lookup when no explicit font path is passed)

## CLI usage

### Default text mode

```bash
phart --output-format svg graph.dot > graph.svg
```

### Glyph path mode with explicit font path

```bash
phart --output-format svg \
  --svg-text-mode path \
  --svg-font-path /path/to/font.ttf \
  graph.dot > graph.svg
```

### Glyph path mode with font family lookup

```bash
phart --output-format svg \
  --svg-text-mode path \
  --svg-font-family "Menlo" \
  graph.dot > graph.svg
```

## Notes

- `text` mode remains the default for speed and broad compatibility.
- In `path` mode, per-cell ANSI edge colors are preserved in the generated SVG.
- If a glyph is missing in the selected font, that character is skipped.

## Troubleshooting

- `SVG path glyph mode requires fonttools`: install `phart[svg]` or `fonttools`.
- `--svg-font-path not found`: verify the path is correct and readable.
- `Could not resolve font '...':` pass `--svg-font-path` explicitly.
