# Changeling Forensic Report

Range: `f09049840dd17a5f4f03d594dd0a21fcd31f4be0..f80f73758f934d4d142bd6961ffe6f4a336b1aae`
Commits: 94
Files changed: 380
Insertions: 58462
Deletions: 14614

## Warnings

- [range] Range 'f80f73758f934d4d142bd6961ffe6f4a336b1aae..f09049840dd17a5f4f03d594dd0a21fcd31f4be0' contained no commits; using 'f09049840dd17a5f4f03d594dd0a21fcd31f4be0..f80f73758f934d4d142bd6961ffe6f4a336b1aae' instead.
- [message_scope_mismatch] `ab836fc` Commit message focus does not match dominant file changes.
- [message_scope_mismatch] `a288df6` Commit message focus does not match dominant file changes.
- [mixed_concern] `2a15624` Commit mixes multiple concern types (for example docs/source/tests).
- [mixed_concern] `a7dc4a0` Commit mixes multiple concern types (for example docs/source/tests).
- [message_scope_mismatch] `623880e` Commit message focus does not match dominant file changes.
- [message_scope_mismatch] `d26a835` Commit message focus does not match dominant file changes.
- [message_scope_mismatch] `9f10bac` Commit message focus does not match dominant file changes.

## Candidate Notes

- (fixed) fix svg for both stdout and writing to file, and capturing output of runner for both. begin svg refactor out of renderer [supported]
- (new) add a no-frills mermid flowcchart diagram output [supported]
- (changed) Merge branch 'main' into latest-dev [supported]
- (new) Squashed commit of the following: [supported]
- (new) Merge remote-tracking branch 'origin/refactor/renderer-canvas-colors' into latest-dev [supported]
- (new) Merge branch 'wtf-merge' into refactor/latest-dev [supported]
- (new) add GoT network graphml file into examples [supported]
- (new) some html from tests [supported]
- (fixed) Implemented bidirectional_mode with coalesce as the default and separate as the override. Allows for "show both directions even when reciprocal" mode, which is good for debugging, art, and maybe some real use cases like indicating capacity, distinction/dissimilarity, etc. Mainly it was to make pretty rainbow colorings. :-) [supported]
- (new) Updated CLI behavior in src. [supported]
- (fixed) PR5: affinity tuning + connector compaction + metadata export finalization. implement affinity penalty heuristics, boundary scoring, connector compaction, partition metadata extraction, cli wiring, and tests of same [supported]
- (new) Merge branch 'refactor/architecture-foundation' into refactor/latest-dev [supported]
- (changed) Delete outtest.svg [supported]
- (fixed) fix mypy types-yaml [supported]
- (new) rename test_outputs dir [supported]
- (changed) Merge branch 'old-ordering' into latest-dev [supported]
- (changed) Updated code in htmltest.html. [inferred]
- (new) shared port slot assignment, etc [supported]
- (changed) refactor plantuml code out of renderer and into phart.io. [supported]
- (fixed) Updated CLI behavior in examples. [supported]
- (new) implement phase 3b from archicture/style-rules-spec.md [supported]
- (new) Implement Phase 3a for style-rule + node-style, and added a tracked execution board in the architecture doc [supported]
- (new) make node-spacing awaare of new multiline label changes [supported]
- (new) Extract python input execution into io.input python runner [supported]
- (new) Added functionality in src. [inferred]
- (new) Updated code in src. [inferred]
- (new) Updated code in examples. [inferred]
- (fixed) Fixed behavior in examples. [inferred]
- (new) Added functionality in examples. [inferred]
- (changed) Updated code in unixtest.mmd. [inferred]
- (changed) Updated code in nxatl,py. [inferred]
- (fixed) Fixed behavior in src. [inferred]
- (changed) Updated code in examples. [inferred]
- (new) Refactored internal code in examples. [inferred]
- (changed) Refactored internal code in examples. [inferred]
- (changed) Updated code in src. [inferred]
- (fixed) Fixed behavior in .pre-commit-config.yaml. [inferred]
- (changed) Refactored internal code in tools. [inferred]
