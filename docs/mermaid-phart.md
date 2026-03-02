# phart does mermaid. mermaid pharts. news at 11.

By request, `--output` has another viable target in its `--output-format` directory, with the addition of `mmd`, which is a mermaid TD flowchart.

It's not configurable in any way, but if you have a large graph, it can save you a ton of time since mmd is another plain text format, so you can search and replace to change the number of dashes in an edge (layout hint), or change it to a thick line (`-` to `==`), etc with a quick searach-and-replace op in your favorite 
editor.  

Also, just like with screen renders, if you pass `--label` to the cli, or `use_labels=True` in your LayoutOptions programmatically, then whatever is in 
the label attribute for any  given node will be displayed as appropriate. If there is no label, the string representation of whatever type of object it is is used 
(id, name, etc), though for mermaid, if there was a long and difficult identifier and no alternative label, the id may look a little wonky (e.g., if it had spaces
or quotes in it, they were normalized away.) Without enabling labels, the node name/id is displayed, as with any other rendered output format.

That is all for today. Carry on.  Oh... Below you see the "Go Package Dependency" DAG that I've used for other tests in other documentation you will find here. Ive embedded the generated mmd inline in the markdown.

----

``` mermaid
flowchart TD
    regexp["regexp"] ---> bytes["bytes"]
    regexp["regexp"] ---> io["io"]
    regexp["regexp"] ---> regexp/syntax["regexp/syntax"]
    regexp["regexp"] ---> sort["sort"]
    regexp["regexp"] ---> strconv["strconv"]
    regexp["regexp"] ---> strings["strings"]
    regexp["regexp"] ---> sync["sync"]
    regexp["regexp"] ---> unicode["unicode"]
    regexp["regexp"] ---> unicode/utf8["unicode/utf8"]
    bytes["bytes"] ---> internal/bytealg["internal/bytealg"]
    bytes["bytes"] ---> io["io"]
    bytes["bytes"] ---> unicode["unicode"]
    bytes["bytes"] ---> unicode/utf8["unicode/utf8"]
    bytes["bytes"] ---> errors["errors"]
    io["io"] ---> errors["errors"]
    io["io"] ---> sync["sync"]
    regexp/syntax["regexp/syntax"] ---> sort["sort"]
    regexp/syntax["regexp/syntax"] ---> strconv["strconv"]
    regexp/syntax["regexp/syntax"] ---> strings["strings"]
    regexp/syntax["regexp/syntax"] ---> unicode["unicode"]
    regexp/syntax["regexp/syntax"] ---> unicode/utf8["unicode/utf8"]
    sort["sort"] ---> internal/reflectlite["internal/reflectlite"]
    strconv["strconv"] ---> internal/bytealg["internal/bytealg"]
    strconv["strconv"] ---> math["math"]
    strconv["strconv"] ---> unicode/utf8["unicode/utf8"]
    strconv["strconv"] ---> errors["errors"]
    strconv["strconv"] ---> math/bits["math/bits"]
    strings["strings"] ---> io["io"]
    strings["strings"] ---> sync["sync"]
    strings["strings"] ---> unsafe["unsafe"]
    strings["strings"] ---> errors["errors"]
    strings["strings"] ---> internal/bytealg["internal/bytealg"]
    strings["strings"] ---> unicode["unicode"]
    strings["strings"] ---> unicode/utf8["unicode/utf8"]
    sync["sync"] ---> internal/race["internal/race"]
    sync["sync"] ---> runtime["runtime"]
    sync["sync"] ---> sync/atomic["sync/atomic"]
    sync["sync"] ---> unsafe["unsafe"]
    internal/bytealg["internal/bytealg"] ---> internal/cpu["internal/cpu"]
    internal/bytealg["internal/bytealg"] ---> unsafe["unsafe"]
    errors["errors"] ---> internal/reflectlite["internal/reflectlite"]
    internal/reflectlite["internal/reflectlite"] ---> runtime["runtime"]
    internal/reflectlite["internal/reflectlite"] ---> unsafe["unsafe"]
    math["math"] ---> unsafe["unsafe"]
    math["math"] ---> internal/cpu["internal/cpu"]
    math["math"] ---> math/bits["math/bits"]
    math/bits["math/bits"] ---> unsafe["unsafe"]
    internal/race["internal/race"] ---> unsafe["unsafe"]
    sync/atomic["sync/atomic"] ---> unsafe["unsafe"]
```
----

Here is the plain text `--bboxes` version with `--node-spaces 3` and `--layer-spaces 3` and PHART's default (legacy/auto) layout strategy:

```

                               ┌────────┐
                               │ regexp │
                               └────────┘
                          ┌─────────┤
                          │         ├┬────┐
                          v       ┌─┤│    v
                      ┌───────┐───┌───────────────┐
                      │ bytes │   │ regexp/syntax │
                      └───────┘   └───────────────┘
                      │   │       │ ││    ├─────┐
                      ├───┼───────┼─┼┼────┼─────┤
                      v   │       v ││    │     v
          ┌───────┌──────┐┤  ┌─────────┐  ├┌─────────┐
          │  ┌────│─sort─│┤  │ strconv │  ││ strings │
          │  │    └──────┘│  └─────────┘  │└─────────┘
          │  │   ┌────┘   │┌──────┤ ││    │     ├───────────┐
          ├──┼───┼────────┴┼──────┼─┼┼────┴─────┼───────────┼────┐
          v  │   │         v      │ │v          v           │    v
┌──────────────────┐   ┌──────┐───┌────┐───┌─────────┐───┌──────────────┐
│ internal/bytealg │   │ math │   │ io │   │ unicode │   │ unicode/utf8 │
└──────────────────┘   └──────┘   └────┘   └─────────┘   └──────────────┘
          │  ├───┼─────────┼──────┼──┤          │           │
          ├──┼───┼─────────┼──────┴──┴───────┬──┼───────────┤
          │  v   │         v ┌───────────────v──┘           v
        ┌────────┐   ┌───────────┐   ┌──────────────┐   ┌──────┐
        │ errors │   │ math/bits │   │ internal/cpu │   │ sync │
        └────────┘   └───────────┘   └──────────────┘   └──────┘
          │  └───┤         └─┤          ┌───────────────────┤
          │      │           │          │ ┌────────────────┬┤
          │      v           │          v │                v│
     ┌──────────────────────┐┤  ┌───────────────┐   ┌─────────────┐
     │ internal/reflectlite ││  │ internal/race │   │ sync/atomic │
     └──────────────────────┘│  └───────────────┘   └─────────────┘
                 ├───────────┤          │ │                ││
                 └───────────┼──────────┴─┼────────────────┴┘
                             v            v
                        ┌────────┐   ┌─────────┐
                        │ unsafe │   │ runtime │
                        └────────┘   └─────────┘
```
