# Evidence

## 1. PR5: affinity tuning + connector compaction + metadata export finalization. implement affinity penalty heuristics, boundary scoring, connector compaction, partition metadata extraction, cli wiring, and tests of same (new)

**Commits:** [f80f737](https://github.com/scottvr/phart/commit/f80f737), [bb16f7b](https://github.com/scottvr/phart/commit/bb16f7b), [c7681e3](https://github.com/scottvr/phart/commit/c7681e3), [3f6a106](https://github.com/scottvr/phart/commit/3f6a106)
**Files:** [docs/architecture/layout-partitioning-spec.md](https://github.com/scottvr/phart/blob/f80f73758f934d4d142bd6961ffe6f4a336b1aae/docs/architecture/layout-partitioning-spec.md), [examples/gedcom.py](https://github.com/scottvr/phart/blob/f80f73758f934d4d142bd6961ffe6f4a336b1aae/examples/gedcom.py), [src/phart/**init**.py](https://github.com/scottvr/phart/blob/f80f73758f934d4d142bd6961ffe6f4a336b1aae/src/phart/__init__.py), [src/phart/cli.py](https://github.com/scottvr/phart/blob/f80f73758f934d4d142bd6961ffe6f4a336b1aae/src/phart/cli.py), [src/phart/layout.py](https://github.com/scottvr/phart/blob/f80f73758f934d4d142bd6961ffe6f4a336b1aae/src/phart/layout.py), [src/phart/renderer.py](https://github.com/scottvr/phart/blob/f80f73758f934d4d142bd6961ffe6f4a336b1aae/src/phart/renderer.py), [src/phart/styles.py](https://github.com/scottvr/phart/blob/f80f73758f934d4d142bd6961ffe6f4a336b1aae/src/phart/styles.py), [src/phart/rendering/output.py](https://github.com/scottvr/phart/blob/f80f73758f934d4d142bd6961ffe6f4a336b1aae/src/phart/rendering/output.py)

## 2. implement phase 3b from archicture/style-rules-spec.md (new)

**Commits:** [981b4c3](https://github.com/scottvr/phart/commit/981b4c3)
**Files:** [docs/architecture/style-rules-spec.md](https://github.com/scottvr/phart/blob/981b4c33283481a7d05bf956a48822b28e22ffff/docs/architecture/style-rules-spec.md), [src/phart/renderer.py](https://github.com/scottvr/phart/blob/981b4c33283481a7d05bf956a48822b28e22ffff/src/phart/renderer.py), [src/phart/rendering/canvas.py](https://github.com/scottvr/phart/blob/981b4c33283481a7d05bf956a48822b28e22ffff/src/phart/rendering/canvas.py), [src/phart/rendering/routing.py](https://github.com/scottvr/phart/blob/981b4c33283481a7d05bf956a48822b28e22ffff/src/phart/rendering/routing.py), [src/phart/style_rules.py](https://github.com/scottvr/phart/blob/981b4c33283481a7d05bf956a48822b28e22ffff/src/phart/style_rules.py)

## 3. Phase 3 cand d completed; true up docs, ensure examples, brakage callouts. (new)

**Commits:** [623880e](https://github.com/scottvr/phart/commit/623880e)
**Files:** [README.md](https://github.com/scottvr/phart/blob/623880e3306153a5c7b21211d9f0244122761ba2/README.md), [docs/architecture/style-rules-spec.md](https://github.com/scottvr/phart/blob/623880e3306153a5c7b21211d9f0244122761ba2/docs/architecture/style-rules-spec.md), [docs/index.md](https://github.com/scottvr/phart/blob/623880e3306153a5c7b21211d9f0244122761ba2/docs/index.md), [src/phart/cli.py](https://github.com/scottvr/phart/blob/623880e3306153a5c7b21211d9f0244122761ba2/src/phart/cli.py), [src/phart/renderer.py](https://github.com/scottvr/phart/blob/623880e3306153a5c7b21211d9f0244122761ba2/src/phart/renderer.py), [src/phart/styles.py](https://github.com/scottvr/phart/blob/623880e3306153a5c7b21211d9f0244122761ba2/src/phart/styles.py)

## 4. multiline node-labeling (new)

**Commits:** [61e3188](https://github.com/scottvr/phart/commit/61e3188), [9f10bac](https://github.com/scottvr/phart/commit/9f10bac), [2685f16](https://github.com/scottvr/phart/commit/2685f16), [705801b](https://github.com/scottvr/phart/commit/705801b)
**Files:** [README.md](https://github.com/scottvr/phart/blob/61e31883cdad05b1bab3c242e87667efff1fee7c/README.md), [src/phart/cli.py](https://github.com/scottvr/phart/blob/61e31883cdad05b1bab3c242e87667efff1fee7c/src/phart/cli.py), [src/phart/renderer.py](https://github.com/scottvr/phart/blob/61e31883cdad05b1bab3c242e87667efff1fee7c/src/phart/renderer.py), [src/phart/rendering/nodes.py](https://github.com/scottvr/phart/blob/61e31883cdad05b1bab3c242e87667efff1fee7c/src/phart/rendering/nodes.py), [src/phart/styles.py](https://github.com/scottvr/phart/blob/61e31883cdad05b1bab3c242e87667efff1fee7c/src/phart/styles.py), [src/phart/rendering/routing.py](https://github.com/scottvr/phart/blob/61e31883cdad05b1bab3c242e87667efff1fee7c/src/phart/rendering/routing.py)

## 5. early and often, cuz this could get in the weeds... (new)

**Commits:** [7738360](https://github.com/scottvr/phart/commit/7738360)
**Files:** [src/phart/cli.py](https://github.com/scottvr/phart/blob/7738360c504aa334f7b5806e7ca810ff10cf3328/src/phart/cli.py), [src/phart/layout.py](https://github.com/scottvr/phart/blob/7738360c504aa334f7b5806e7ca810ff10cf3328/src/phart/layout.py), [src/phart/styles.py](https://github.com/scottvr/phart/blob/7738360c504aa334f7b5806e7ca810ff10cf3328/src/phart/styles.py)

## 6. vertical pagination (new)

**Commits:** [294eab9](https://github.com/scottvr/phart/commit/294eab9), [095309f](https://github.com/scottvr/phart/commit/095309f)
**Files:** [src/phart/cli.py](https://github.com/scottvr/phart/blob/294eab9e92088b61f19c7db97a1dbf42e5d4383b/src/phart/cli.py), [src/phart/io/output/pagination.py](https://github.com/scottvr/phart/blob/294eab9e92088b61f19c7db97a1dbf42e5d4383b/src/phart/io/output/pagination.py)

## 7. PR3: add style-rule targets connector and panel_header; extend predicate root resolution to connector and panel_header contexts; CLI: edge|node|connector|panel_header targets for mew sty;e rules; tests for parse/compile/runtime behavior (new)

**Commits:** [cadb59d](https://github.com/scottvr/phart/commit/cadb59d)
**Files:** [docs/architecture/layout-partitioning-spec.md](https://github.com/scottvr/phart/blob/cadb59d58e5195490a27a18435815aa33f4c54a6/docs/architecture/layout-partitioning-spec.md), [docs/architecture/style-rules-spec.md](https://github.com/scottvr/phart/blob/cadb59d58e5195490a27a18435815aa33f4c54a6/docs/architecture/style-rules-spec.md), [src/phart/cli.py](https://github.com/scottvr/phart/blob/cadb59d58e5195490a27a18435815aa33f4c54a6/src/phart/cli.py), [src/phart/renderer.py](https://github.com/scottvr/phart/blob/cadb59d58e5195490a27a18435815aa33f4c54a6/src/phart/renderer.py), [src/phart/style_rules.py](https://github.com/scottvr/phart/blob/cadb59d58e5195490a27a18435815aa33f4c54a6/src/phart/style_rules.py)

## 8. Implement Phase 3a for style-rule + node-style, and added a tracked execution board in the architecture doc (new)

**Commits:** [a5c6fb6](https://github.com/scottvr/phart/commit/a5c6fb6)
**Files:** [docs/architecture/style-rules-spec.md](https://github.com/scottvr/phart/blob/a5c6fb639d486d2598143e58e913ea0c25257b28/docs/architecture/style-rules-spec.md), [src/phart/layout.py](https://github.com/scottvr/phart/blob/a5c6fb639d486d2598143e58e913ea0c25257b28/src/phart/layout.py), [src/phart/rendering/colors.py](https://github.com/scottvr/phart/blob/a5c6fb639d486d2598143e58e913ea0c25257b28/src/phart/rendering/colors.py), [src/phart/rendering/nodes.py](https://github.com/scottvr/phart/blob/a5c6fb639d486d2598143e58e913ea0c25257b28/src/phart/rendering/nodes.py), [src/phart/style_rules.py](https://github.com/scottvr/phart/blob/a5c6fb639d486d2598143e58e913ea0c25257b28/src/phart/style_rules.py)

## 9. make node-spacing awaare of new multiline label changes (new)

**Commits:** [b70ed8a](https://github.com/scottvr/phart/commit/b70ed8a)
**Files:** [examples/gedcom.py](https://github.com/scottvr/phart/blob/b70ed8a0bab4f0c3612866dfd3f6c07b07e56cd1/examples/gedcom.py), [src/phart/layout.py](https://github.com/scottvr/phart/blob/b70ed8a0bab4f0c3612866dfd3f6c07b07e56cd1/src/phart/layout.py), [src/phart/rendering/nodes.py](https://github.com/scottvr/phart/blob/b70ed8a0bab4f0c3612866dfd3f6c07b07e56cd1/src/phart/rendering/nodes.py)

## 10. Added functionality in docs. (new)

**Commits:** [a0d5dab](https://github.com/scottvr/phart/commit/a0d5dab), [1e83cd8](https://github.com/scottvr/phart/commit/1e83cd8), [39970bf](https://github.com/scottvr/phart/commit/39970bf), [10db54c](https://github.com/scottvr/phart/commit/10db54c), [a41ba41](https://github.com/scottvr/phart/commit/a41ba41), [7c9e9bd](https://github.com/scottvr/phart/commit/7c9e9bd), [d26a835](https://github.com/scottvr/phart/commit/d26a835), [c952534](https://github.com/scottvr/phart/commit/c952534)
**Files:** [docs/architecture/mermaid-flowchart-syntax.md](https://github.com/scottvr/phart/blob/a0d5dab66763550a892f5aa93f837972361e6f35/docs/architecture/mermaid-flowchart-syntax.md), [docs/architecture/style-rules-spec.md](https://github.com/scottvr/phart/blob/a0d5dab66763550a892f5aa93f837972361e6f35/docs/architecture/style-rules-spec.md), [docs/index.md](https://github.com/scottvr/phart/blob/a0d5dab66763550a892f5aa93f837972361e6f35/docs/index.md), [docs/architecture/layout-partitioning-spec.md](https://github.com/scottvr/phart/blob/a0d5dab66763550a892f5aa93f837972361e6f35/docs/architecture/layout-partitioning-spec.md), [README.md](https://github.com/scottvr/phart/blob/a0d5dab66763550a892f5aa93f837972361e6f35/README.md), [src/phart/**init**.py](https://github.com/scottvr/phart/blob/a0d5dab66763550a892f5aa93f837972361e6f35/src/phart/__init__.py)

## 11. Refactored internal code in examples. (new)

**Commits:** [69d545b](https://github.com/scottvr/phart/commit/69d545b)
**Files:** [examples/gedcom.py](https://github.com/scottvr/phart/blob/69d545b59cf7ccd8898bd5193b6573ef782d3d14/examples/gedcom.py)

## 12. Updated code in docs. (changed)

**Commits:** [cb8644d](https://github.com/scottvr/phart/commit/cb8644d)
**Files:** [docs/architecture/style-rules-spec.md](https://github.com/scottvr/phart/blob/cb8644dc55f192a82a772eb45634ed1ac9f1ba95/docs/architecture/style-rules-spec.md), [examples/multiline-note.ged](https://github.com/scottvr/phart/blob/cb8644dc55f192a82a772eb45634ed1ac9f1ba95/examples/multiline-note.ged)

## 13. Updated documentation in README.md. (changed)

**Commits:** [1a00194](https://github.com/scottvr/phart/commit/1a00194)
**Files:** [README.md](https://github.com/scottvr/phart/blob/1a001949e165c7c56dadbcc45108f4b287cbfcf8/README.md)

## 14. fix mypy types-yaml (fixed)

**Commits:** [a7dc4a0](https://github.com/scottvr/phart/commit/a7dc4a0)
**Files:** [.pre-commit-config.yaml](https://github.com/scottvr/phart/blob/a7dc4a0213611023df7d23196adcb5f938498340/.pre-commit-config.yaml), [README.md](https://github.com/scottvr/phart/blob/a7dc4a0213611023df7d23196adcb5f938498340/README.md), [docs/index.md](https://github.com/scottvr/phart/blob/a7dc4a0213611023df7d23196adcb5f938498340/docs/index.md), [requirements/developer.txt](https://github.com/scottvr/phart/blob/a7dc4a0213611023df7d23196adcb5f938498340/requirements/developer.txt), [requirements/test.txt](https://github.com/scottvr/phart/blob/a7dc4a0213611023df7d23196adcb5f938498340/requirements/test.txt), [src/phart/cli.py](https://github.com/scottvr/phart/blob/a7dc4a0213611023df7d23196adcb5f938498340/src/phart/cli.py), [src/phart/renderer.py](https://github.com/scottvr/phart/blob/a7dc4a0213611023df7d23196adcb5f938498340/src/phart/renderer.py), [src/phart/rendering/colors.py](https://github.com/scottvr/phart/blob/a7dc4a0213611023df7d23196adcb5f938498340/src/phart/rendering/colors.py), [src/phart/style_rules.py](https://github.com/scottvr/phart/blob/a7dc4a0213611023df7d23196adcb5f938498340/src/phart/style_rules.py), [src/phart/styles.py](https://github.com/scottvr/phart/blob/a7dc4a0213611023df7d23196adcb5f938498340/src/phart/styles.py)

## 15. Updated CLI behavior in examples. (fixed)

**Commits:** [20977a7](https://github.com/scottvr/phart/commit/20977a7)
**Files:** [README.md](https://github.com/scottvr/phart/blob/20977a7027f511b2a0dd0d631d831b807dd6cc67/README.md), [docs/index.md](https://github.com/scottvr/phart/blob/20977a7027f511b2a0dd0d631d831b807dd6cc67/docs/index.md), [examples/bom.ged](https://github.com/scottvr/phart/blob/20977a7027f511b2a0dd0d631d831b807dd6cc67/examples/bom.ged), [examples/cli_demo-collatz.sh](https://github.com/scottvr/phart/blob/20977a7027f511b2a0dd0d631d831b807dd6cc67/examples/cli_demo-collatz.sh), [examples/cli_demo-triads.sh](https://github.com/scottvr/phart/blob/20977a7027f511b2a0dd0d631d831b807dd6cc67/examples/cli_demo-triads.sh), [examples/fam_marr.ged](https://github.com/scottvr/phart/blob/20977a7027f511b2a0dd0d631d831b807dd6cc67/examples/fam_marr.ged), [examples/gedcom.py](https://github.com/scottvr/phart/blob/20977a7027f511b2a0dd0d631d831b807dd6cc67/examples/gedcom.py), [examples/issue_7-flow-left-demo.sh](https://github.com/scottvr/phart/blob/20977a7027f511b2a0dd0d631d831b807dd6cc67/examples/issue_7-flow-left-demo.sh), [examples/level3.ged](https://github.com/scottvr/phart/blob/20977a7027f511b2a0dd0d631d831b807dd6cc67/examples/level3.ged), [examples/multiline-note.ged](https://github.com/scottvr/phart/blob/20977a7027f511b2a0dd0d631d831b807dd6cc67/examples/multiline-note.ged), [src/phart/cli.py](https://github.com/scottvr/phart/blob/20977a7027f511b2a0dd0d631d831b807dd6cc67/src/phart/cli.py), [src/phart/rendering/nodes.py](https://github.com/scottvr/phart/blob/20977a7027f511b2a0dd0d631d831b807dd6cc67/src/phart/rendering/nodes.py)

## 16. Fixed behavior in .pre-commit-config.yaml. (fixed)

**Commits:** [819c2ca](https://github.com/scottvr/phart/commit/819c2ca)
**Files:** [.pre-commit-config.yaml](https://github.com/scottvr/phart/blob/819c2ca47ea47405a814ff15e28c9892c201c3e6/.pre-commit-config.yaml)
