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

# Under Development

So I actually didn't mean to ship all of the new file parsers and writers while they're still experimental, but they're stable so when
I unintentionally merged them into main, I just went with it and started writing documentation. 

One interesting thing that I didn't actually anticipate until after I started playing with the SVG modes, fixing bugs, and testing limits,
is that aside from being vectors and zoomable beyond what a character display or even a modern emulated terminal with great resolution, a screenshot,
etc, is that since the SVG is not generated directly from the Graph data, but rather from the output of the ASCIIRenderer, while the paths are still limited to 90 degree angles, the geography of the graph diagram can span much larger, so with appropriate use of layer spacing, node spacing, and the H and V padding,  you can render really compact and densely populated graphs, with paths intricate that remain visibly distinct. 

[Here's another take on "Rainbow Coloring" that takes adantage of these benefits bestowed by virtue of SVG,](https://raw.githubusercontent.com/scottvr/phart/2a156248eb906b7f30e3a3f73ff56664625788db/examples/nx-rainbox-coloring.svg)

Another cool thing about this is since it is essentially using a virtual x/y grid as if it were a console display, you can have the SVG use a font that is not monospaced, but it will be arranged monospace regardless of kerning or glyph positioning hints given by the font itself; PHART decides it's all on a grid. :-) Some really nice looking diagrams can result, despite the primitive orthogonal constrains PHART works in by design.

[And here is a very clean, monospaced look from the AquaKana font!](https://raw.githubusercontent.com/scottvr/phart/2a156248eb906b7f30e3a3f73ff56664625788db/examples/unix.gv.svg)

I'm quite pleased with the results. Let me know if you do anything cool with SVG in PHART.
