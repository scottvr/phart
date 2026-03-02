# phart does mermaid. mermaid pharts. news at 11.

By request, `--output` has another viable target in its `--output-format` directory, with the addition of `mmd`, which is a mermaid TD flowchart.

It's not configurable in any way, but if you have a large graph, it can save you a ton of time since mmd is another plain text format, so you can search and replace to change the number of dashes in an edge (layout hint), or change it to a thick line (`-` to `==`), etc with a quick searach-and-replace op in your favorite 
editor.  

Also, just like with screen renders, if you pass `--label` to the cli, or `use_labels=True` in your LayoutOptions programmatically, then whatever is in 
the label attribute for any  given node will be displayed as appropriate. If there is no label, the string representation of whatever type of object it is is used 
(id, name, etc), though for mermaid, if there was a long and difficult identifier and no alternative label, the id may look a little wonky (e.g., if it had spaces
or quotes in it, they were normalized away.) Without enabling labels, the node name/id is displayed, as with any other rendered output format.

----

Below you see the ["Go Package Dependency" DAG DOT](https://raw.githubusercontent.com/scottvr/phart/refs/heads/main/examples/go-package.dot) that I've used for other tests in other documentation you will find here. Ive embedded the generated mmd inline in the markdown.


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

I don't want to be defensive, but I didn't set out to build a mermaid diagram source generator, so here are a few plain-text diagrams from phart of the same input data. 

Here is the plain text with `--bboxes` and default (legacy/auto) layout strategy:

```
                                 ┌────────┐
                                 │ regexp │
                                 └────────┘
                           ┌──────────┼─────┐
                           v          ├┐    v
                       ┌───────┐────┌───────────────┐
                       │ bytes │    │─regexp/syntax │
                       └───────┘    └───────────────┘
                       ├───┼────────┼─┼┼────┼──────┐
                       v   │        v ││    │      v
          ┌────────┌──────┐┤   ┌─────────┐  ├─┌─────────┐
          │   ┌────│─sort─│┤   │ strconv │  │ │ strings │
          │   │    └──────┘│   └─────────┘  │ └─────────┘
          ├───┼───┬────┴───┴┬───────┼─┼┼────┴──────┼─────────────────┐
          v   │   │         v┌──────┤ │v           v                 v
┌──────────────────┐    ┌──────┐    ┌────┐────┌─────────┐────┌──────────────┐
│ internal/bytealg││    │ math │    │ io │    │ unicode─│────│─unicode/utf8 │
└──────────────────┘    └──────┘    └────┘    └─────────┘    └──────────────┘
          ├───┼───┼─────────┼┼──────┴──┴────────┬──┼────────────┤
          │   v   │         │v ┌────────────────v──┘            v
         ┌────────┐    ┌───────────┐    ┌──────────────┐    ┌──────┐
         ││errors │    │ math/bits │    │ internal/cpu │    │ sync │
         └────────┘    └───────────┘    └──────────────┘    └──────┘
          │   └───┤          └─┤          ┌───────────────────┬─┤
          │       v            │          v  ┌────────────────v─┤
      ┌──────────────────────┐─┤  ┌───────────────┐    ┌─────────────┐
      │ internal/reflectlite │ │  │ internal/race │    │ sync/atomic │
      └──────────────────────┘ │  └───────────────┘    └─────────────┘
                  └────────────┼──────────┴──┼────────────────┴─┘
                               v             v
                          ┌────────┐    ┌─────────┐
                          │ unsafe │    │ runtime │
                          └────────┘    └─────────┘
```

Changing a few options to make some things less ambiguous (also, using color would eliminate the ambiguities and allow the layout to remain compact. Also also, in context, where you know this is a directed graph, it really isn't any more ambiguous than the mermaid SVG above, since if there is no arrowhead at aan intersection, then the path does not terminate there - it is either originating there or "just passing through", but sometimes due to the low grid reolution and forgetting that context, we might look for other layout options). In fact, having said thaat I realize that the context makes the bottom layer unclear - how many edges terminate at unsafe vs how many at runtime? 

----

We can clarify that with `--edge-anchors ports`:

```
 $ phart --bboxes --layer-spacing 4 --vpad 0 --hpad 2    --node-spacing 4  --labels --edge-anchors ports go-package.dot
                                     ┌──────────┐
                                     │  regexp  │
                                     └──────────┘
                                ┌─────┼┘ ││└┼┼┼┼─┐
                                │     │  ││ ││││ │
                                v     │  ││ ││││ v
                          ┌─────────┐─┘  ┌─────────────────┐
                          │ │bytes  │    ││ regexp/syntax  │
                          └─────────┘    └─────────────────┘
                  ┌────────┘│    └┼┼─────┤││ │││     │ ├─┘└──────────────┐
                  │         │┌────┼┼─────┼┼┼─┼┤│     │ │                 │
                  │         vv    ││     ││v │v│     v v                 │
                  │  ┌────────┐   │┌───────────┐────┌───────────┐───┐    │
                  │  │  sort│ │   ││  strconv└─│────│─┐strings  │   │    │
                  │  └────────┘   │└───────────┘    └───────────┘   │    │
                  │       │ │     ││││││ ││   ││     ││││ │   ││    │    │
                  │┌┬─────┼─┼───┬─┴┴┴┼┴┼─┼┼───┼┴─────┼┼┼┴─┼───┼┴────┼─┬┬┬┼┐
                  vvv     │ │   v    │ │ vv   v      vvv  v   │     │ vvvvv
┌────────────────────┐────┌────────┐ │ │┌──────┐    ┌───────────┐   │┌────────────────┐
│  internal/bytealg  │    │  math  │ │ ││  io  │    │ │unicode│ │   ││  unicode/utf8  │
└────────────────────┘    └────────┘ │ │└──────┘    └───────────┘   │└────────────────┘
                 │ ├┼─────┼────┼─┼┼──┼─┼─┘    │       ││      │     │
                 │┌┼┼─────┼────┼─┼┴──┴─┼──────┼┬──────┴┼──────┴─────┼┬┐
                 vvvv     │    v┌┘     v      vv       │            vvv
          ┌──────────┐    ┌─────────────┐────┌────────────────┐    ┌────────┐
          │  errors│ │    │  math/bits  │    │  internal/cpu  │    │  sync  │
          └──────────┘    └─────────────┘    └────────────────┘    └────────┘
                │  │      │     ││   │          ┌───────────────────┼┘├┘
                │  │      │     ││   │          │       ┌───────────┼─┤
                v  │      v     ││   │          v       │           │ v
        ┌────────────────────────┐   │┌─────────────────┐    ┌───────────────┐
        │  internal/reflectlite ││   ││  internal/race  │    │  sync/atomic  │
        └────────────────────────┘   │└─────────────────┘    └───────────────┘
                              ││││   │        │         │           │
                              ││├┼──┬┼┬┬──────┼─────────┼───────────┘
                              vvvv  vvvv      v         v
                             ┌──────────┐    ┌───────────┐
                             │  unsafe  │    │  runtime  │
                             └──────────┘    └───────────┘
```

----

Alles Klar? Nein?  We can go bigger:

```
$  phart --bboxes --layer-spacing 4 --vpad 1 --hpad 2    --node-spacing 4  --labels --edge-anchors ports --uniform go-package.dot
                                                            ┌────────────────────────┐
                                                            │                        │
                                                            │         regexp         │
                                                            │                        │
                                                            └────────────────────────┘
                                                           ┌─┼┘         ││      └┼┼┼┼──┐
                                                           │ │          ││       ││││  │
                                                           v │          ││       ││││  v
                                             ┌────────────────────────┐ ││ ┌────────────────────────┐
                                             │       │                │ ││ │      │││      │        │
                                             │       │ bytes          │ ││ │     regexp/syntax      │
                                             │       │                │ ││ │      │││      │        │
                                             └────────────────────────┘ ││ └────────────────────────┘
                      ┌───────────────────────┘│     │       ┌─────┘││  ││  ││    │││      │┌────┘│└────────────────────────┐
                      │             ┌──────────┘     │┌──────┼──────┼┼──┼┼──┘└────┼┼┤      ││┌────┘                         │
                      │             │                vv      │      ││  │v        ││v      vv│                              │
                      │       ┌────────────────────────┐    ┌────────────────────────┐────┌────────────────────────┐        │
                      │       │     │                  │    ││      ││  │         └─┼│────│─┐│            │        │        │
                      │       │     │    sort          │    ││      │strconv        ││    │ ││     strings│        │        │
                      │       │     │                  │    ││      ││  │           ││    │ ││            │        │        │
                      │       └────────────────────────┘    └────────────────────────┘    └────────────────────────┘        │
                      │             │      │                 ││││   ││  │           │      ││││        │  │ ┌────┘│         │
                      │┌┬───────────┼──────┼┬────────────────┼┼┴┼───┴┴──┼───────────┼──────┼┼┼┴────────┼──┼─┼─────┴──────┬┬┬┼┐
                      vvv           │      │v                v│ └────┐  v           v      vvv         v  │ │            vvvvv
┌────────────────────────┐    ┌────────────────────────┐    ┌────────────────────────┐    ┌────────────────────────┐    ┌────────────────────────┐
│                        │    │     │      │           │    │ │      │               │    │ ││            │ │      │    │                        │
│    internal/bytealg    │    │     │    math          │    │ │      │  io           │    │ ││     unicode│ │      │    │      unicode/utf8      │
│                        │    │     │      │           │    │ │      │               │    │ ││            │ │      │    │                        │
└────────────────────────┘    └────────────────────────┘    └────────────────────────┘    └────────────────────────┘    └────────────────────────┘
                       ││           │┌─────┼────────┼┼┼──────┘│      │              │       ││            │ │
                       │└───────────┼┼┬┬───┼──┬─────┴┼┴───────┴──────┼──────┬┬──────┴───────┴┼────────────┼┐│
                       │            vvvv   │  v  ┌───┘               v      vv               │            vvv
               ┌────────────────────────┐  │ ┌────────────────────────┐────┌────────────────────────┐    ┌────────────────────────┐
               │       │                │  │ │   │                  │ │    │                        │    │                        │
               │       │ errors         │  │ │   │   math/bits      │ │    │      internal/cpu      │    │          sync          │
               │       │                │  │ │   │                  │ │    │                        │    │                        │
               └────────────────────────┘  │ └────────────────────────┘    └────────────────────────┘    └────────────────────────┘
                       │     └─┐           │     │        │         │     ┌───────────────────────────────┼┘││
                       │       │           │     │        │         │     │                        ┌────┬─┼─┴┘
                       │       v           v     │        │         │     v                        │    v │
                       └──────┌────────────────────────┐  │ ┌────────────────────────┐    ┌────────────────────────┐
                              │               │  │     │  │ │       │                │    │        │      │        │
                              │  internal/reflectlite  │  │ │     internal/race      │    │      sync/atomic       │
                              │               │  │     │  │ │       │                │    │        │      │        │
                              └────────────────────────┘  │ └────────────────────────┘    └────────────────────────┘
                                              │┌─┼───┘│   │         │   │                          │  │   │
                                              ││ │    └───┼───────┬┬┼┬──┴───┬──────────────────────┼──┴───┘
                                              vv v        v       vvvv      v                      v
                                             ┌────────────────────────┐    ┌────────────────────────┐
                                             │                        │    │                        │
                                             │         unsafe         │    │        runtime         │
                                             │                        │    │                        │
                                             └────────────────────────┘    └────────────────────────┘
```


At first glance that one looks great to me, but then when I look longer I think there's some ambiguity, and then when looking longer I realize that 
it is clear and correct, but thaat if I had to look thrice to know that for sure, it is then a little  "ambiguous" by definition, right? So we can 
experiment with other layouts. Using the `circular` layout strategy perhaps makes everything more immediately clear, but it makes things pretty huge. 

----

So, if you're going to have to compromise and use color, you could go instead compromise immediate clarity in plain text output and have that output be  mermaid that your reader can paste into a mermaid viewer, or if you're writing in markdown, you can just embed it as I've done above.  

Here's the plain-text `circular` strategy:

```
$ phart --bboxes --layer-spacing 2 --vpad 0 --hpad 2 --node-spacing 2 --labels --edge-anchors ports --layout circular    go-package.dot

                                                                                                                 ┌──────────┐
                                                                                                                 │  regexp  │
                                                                                                                 └──────────┘
                                                                ┌────────────────┌────────────────┐───────────────┼┼┼┼┼┘│                      ┌─────────┐
                                                                │                │  unicode/utf8  │<──────────────┼┼┼┼┼─┼──────────────────────│  bytes  │
                                                                │                └────────────────┘               │││││ │                      └─────────┘
                                                                │                 ^^^                             │││││ │                       ││     └┼────────────────────┐
                                                                │                 │││                             │││││ │                       ││      │                    │
                                                                │                 │││                             │││││ │                       ││      │                    │
                                                                │                 │││                             │││││ │                       ││      │                    │
                                                                │   ┌┬────────────┼┼┼─────────────────────────────┼┼┼┼┼─┴───────────────────────┼┘      │                    │
                                                                │   vv            │││                             │││││                         │       │                    v
                                                          ┌───────────┐           │││                             │││││                         │       └──────────┌────────────────────┐────────┐
                                                          │  unicode  │           │││                             │││││                         │                  │  internal/bytealg  │        │
                                                          └───────────┘           │││                             │││││                         │                  └────────────────────┘        │
                                                  ┌────────^^   │                 │││                             │││││                         │                   ^^│                └───────┐ │
                                                  │        │    │                 │││                             │││││                         │                   │││                        │ │
                                                  │        │    │                 │││                             │││││                         │                   │││                        │ │
                                                  │        │    │                 │││                             │││││                         │                   │││                        │ │
                                                  │        │    │                 │││                             │││││                         │                   │││                        │ │
                                                  │        │    │                 │││                             │││││                         │                   │││                        │ │
                                                  │        │    │                 │││                             │││││                         │                   │││                        │ │
                                                  │        │    │                 │││                             │││││                         │                   │││                        │ │
                                                  │        │    │                 │││                             │││││                         │                   │││                        │ │
                                                  │        │    │                 │││                             │││││                         │                   │││                        │ │
                                             ┌────┼────────┼────┼─────────────────┼┼┼─────────────────────────────┼┼┼┼┘                         │                   │││                        │ │
                                             v    │        │    │                 │││                             ││││                          │                   │││                        │ v
                                       ┌────────┐ │        │    │                 │││                             ││││                          │                   │││                     ┌──────────┐
                                       │  sync  │ │        │    │                 │││                             ││││                          │                   │││                     │  errors  │
                                       └────────┘ │        │    │                 │││                             ││││                          │                   │││                     └──────────┘
                               ┌────────^  ^┼┼┼┼──┼────────┼──┐ │                 │││                             ││││                          │                   │││                      ^^^      └───────┐
                               │            ││││  │        │  │ │                 │││                             ││││                          │                   │││                      │││              │
                               │            ││││  │        │  │ │                 │││                             ││││                          │                   │││                      │││              │
                               │            ││││  │        │  │ │                 │││                             ││││                          │                   │││                      │││              │
                               │            ││││  │        │  │ │                 │││                             ││││                          │                   │││                      │││              │
                               │            ││││  │        │  │ │                 │││                             ││││                          │                   │││                      │││              │
                               │            ││││  │        │  │ │                 │││                             ││││                          │                   │││                      │││              │
                               │            ││││  │        │  │ │                 │││                             ││││                          │                   │││                      │││              │
                               │            ││││  │        │  │ │                 │││                             ││││                          │                   │││                      │││              │
                               │            ││││  │        │  │ │                 │││                             ││││                          │                   │││                      │││              │
                               │            ││││  │        │  │ │                 │││                             ││││                          │                   │││                      │││              │
                               │            ││││  │        │  │ │                 │││                             ││││                          │                   │││                      │││              │
                               │            ││││  │        │  │ │                 │││                             ││││                          │                   │││                      │││              │
                               │┌┬┬┬┬───────┼┼┼┼──┼────────┴──┼─┼─────────────────┼┴┼─────────────────────────────┼┼┴┼──────────────────────────┼───────────────────┼┴┼──────────────────────┼┘│              │
                               │││v││       ││││  │           │ │                 │ │                             ││ │                          │                   │ │                      │ │              v
                         ┌───────────┐      ││││  │           │ │                 │ │                             ││ │                          │                   │ │                      │ │  ┌────────────────────────┐
                         │  strings  │      ││││  │           │ │                 │ │                             ││ │                          │                   │ │                      │ │  │  internal/reflectlite  │
                         └───────────┘      ││││  │           │ │                 │ │                             ││ │                          │                   │ │                      │ │  └────────────────────────┘
                                  ^┼┼─┐     ││││  │           │ │                 │ │                             ││ │                          │                   │ │                      │ │   ^├┘
                                   ││ │     ││││  │           │ │                 │ │                             ││ │                          │                   │ │                      │ │   ││
                                   ││ │     ││││  │           │ │                 │ │                             ││ │                          │                   │ │                      │ │   ││
                                   ││ │     ││││  │           │ │                 │ │                             ││ │                          │                   │ │                      │ │   ││
                                   ││ │     ││││  │           │ │                 │ │                             ││ │                          │                   │ │                      │ │   ││
                                   ││ │     ││││  │           │ │                 │ │                             ││ │                          │                   │ │                      │ │   ││
                                   ││ │     ││││  │           │ │                 │ │                             ││ │                          │                   │ │                      │ │   ││
                                   ││ │     ││││  │           │ │                 │ │                             ││ │                          │                   │ │                      │ │   ││
                                   ││ │     ││││  │           │ │                 │ │                             ││ │                          │                   │ │                      │ │   ││
                                   ││ │     ││││  │           │ │                 │ │                             ││ │                          │                   │ │                      │ │   ││
                                   ││ │     ││││  │           │ │                 │ │                             ││ │                          │                   │ │                      │ │   ││
                                   ││ │     ││││  │           │ │                 │ │                             ││ │                          │                   │ │                      │ │   ││
                                   ││ │     ││││  │           │ │                 │ │                             ││ │                          │                   │ │                      │ │   ││
                                   ││ │     ││││  │           │ │                 │ │                             ││ │                          │                   │ │                      │ │   ││
                                   ││ │     ││││  │           │ │                 │ │                             ││ │                          │                   │ │                      │ │   ││
                            ┌┬┬┬───┼┼─┼─────┼┼┼┼──┼───────────┼─┼─────────────────┴─┼─────────────────────────────┴┼─┼──────────────────────────┼───────────────────┴─┼──────────────────────┘ │   ││
                            │v││   ││ │     ││││  │           │ │                   │                              │ │                          │                     │                        │   ││
                    ┌───────────┐  ││ │     ││││  │           │ │                   │                              │ │                          │                     │                        │   ││          ┌────────┐
                    │  strconv  │──┼┼─┼─────┼┼┼┼──┼───────────┼─┼───────────────────┼──────────────────────────────┼─┼──────────────────────────┼─────────────────────┼────────────────────────┼───┼┼─────────>│  math  │
                    └───────────┘  ││ │     ││││  │           │ │                   │                              │ │                          │                     │                        │   ││          └────────┘
                              ^┼───┼┤ │     ││││  │           │ │                   │                              │ │                          │                     │                        │   ││ ┌─────────┼┘ │
                               │   ││ │     ││││  │           │ │                   │                              │ │                          │                     │                        │   ││ │         │  │
                               │   ││ │     ││││  │           │ │                   │                              │ │                          │                     │                        │   ││ │         │  │
                               │   ││ │     ││││  │           │ │                   │                              │ │                          │                     │                        │   ││ │         │  │
                               │   ││ │     ││││  │           │ │                   │                              │ │                          │                     │                        │   ││ │         │  │
                               │   ││ │     ││││  │           │ │                   │                              │ │                          │                     │                        │   ││ │         │  │
                               │   ││ │     ││││  │           │ │                   │                              │ │                          │                     │                        │   ││ │         │  │
                               │   ││ │     ││││  │           │ │                   │                              │ │                          │                     │                        │   ││ │         │  │
                               │   ││ │     ││││  │           │ │                   │                              │ │                          │                     │                        │   ││ │         │  │
                               │   ││ │     ││││  │           │ │                   │                              │ │                          │                     │                        │   ││ │         │  │
                               │   ││ │     ││││  │           │ │                   │                              │ │                          │                     │                        │   ││ │         │  │
                               │   ││ │     ││││  │           │ │                   │                              │ │                          │                     │                        │   ││ │         │  │
                               │   ││ │     ││││  │           │ │                   │                              │ │                          │                     │                        │   ││ │         │  │
                               │   ││ │     ││││  │           │ │                   │                              │ │                          │                     │                        │   ││ │         │  │
                               │   ││ │     ││││  │           │ │                   │                              │ │                          │                     │                        │   ││ │         │  │
                               └─┬┬┼┼─┼─────┼┼┼┼──┼───────────┼─┼───────────────────┼──────────────────────────────┴─┼──────────────────────────┼─────────────────────┼────────────────────────┼───┴┼─┼──┐      │  │
                                 v│││ │     ││││  │           │ │                   │                                │                          │                     │                        │    │ │  v      │  v
                          ┌────────┐│ │     ││││  │           │ │                   │                                │                          │                     │                        │    │ │ ┌─────────────┐
                          │  sort  ││ │     ││││  │           │ │                   │                                │                          │                     │                        │    │ │ │  math/bits  │
                          └────────┘│ │     ││││  │           │ │                   │                                │                          │                     │                        │    │ │ └─────────────┘
                                ^──┼┼┐│     ││││  │           │ │                   │                                │                          │                     │                        │    │ │       │ │
                                   ││││     ││││  │           │ │                   │                                │                          │                     │                        │    │ │       │ │
                                   ││││     ││││  │           │ │                   │                                │                          │                     │                        │    │ │       │ │
                                   ││││     ││││  │           │ │                   │                                │                          │                     │                        │    │ │       │ │
                                   ││││     ││││  │           │ │                   │                                │                          │                     │                        │    │ │       │ │
                                   ││││     ││││  │           │ │                   │                                │                          │                     │                        │    │ │       │ │
                                   ││││     ││││  │           │ │                   │                                │                          │                     │                        │    │ │       │ │
                                   ││││     ││││  │           │ │                   │                                │                          │                     │                        │    │ │       │ │
                                   ││││     ││││  │           │ │                   │                                │                          │                     │                        │    │ │       │ │
                                   ││││     ││││  │           │ │                   │                                │                          │                     │                        │    │ │       │ │
                                   ││││     ││││  │           │ │                   │                                │                          │                     │                        │    │ │       │ │
                                   ││││     ││││  │           │ │                   │                                │                          │                     │                        │    │ │       │ │
                                   ││││     ││││  │           │ │                   │                                │                          │                     │                        │    │ │       │ │
                                   │├┼┼─────┼┼┼┴──┼┬┬─────────┼─┼───────────────────┴────────────────────────────────┴──────────────────────────┼─────────────────────┼──────────────────────┬┐│    │┌┼───────┘ │
                                   ││││     │││   ││v         │ │┌──────────────────────────────────────────────────────────────────────────────┘                     │                      vvv    vvv         │
                                   ┌─────────────────┐───────┐│ ││┌───────────────────────────────────────────────────────────────────────────────────────────────────┼─────────────────────┌──────────┐        │
                                   │  regexp/syntax  │       ││ │││                             ┌─────────────────────────────────────────────────────────────────────┘                     │  unsafe  │        │
                                   └─────────────────┘       ││ │││                             │                                                        ┌──────────────────────────────────└──────────┘        │
                                            │││              ││ │││                             │                                                        │                            ┌──────^^                 │
                                            │││              ││ │││                             │                                                        │                            │      │                  │
                                            │││              ││ │││                             │                                                        │                            │      │                  │
                                            │││              ││ │││                             │                                                        │                            │      │                  │
                                            │││              ││ │││                             │                                                        │                            │      │                  │
                                            │││              ││ │││                             │                                                        │                            │      │                  │
                                            │││              ││ │││                             │                                                        │                            │      │                  │
                                            │││              ││ │││                             │                                                        │                            │      │                  │
                                            │││              ││ │││                             │                                                        │                            │      │                  │
                                            │││              ││ │││                             │                                                        │                            │      │                  │
                                            ││└──────────────┼┼─┼┼┼─────────────────────────────┼────────────────────────────────────────────────────────┼────────────┐               │      │                  │
                                            ││               v│ vv│                             │                                                        │            v               │      │                  │
                                            │└──────────────┌──────┐────────────────────────────┼──────────────────────────────────────────────┐         │           ┌─────────────────┐     │                  │
                                            └───────────────│──io──│────────────────────────────┼───────────────┐                              │         │           │  internal/race  │     │                  │
                                                            └──────┘                            │               │                              │         │           └─────────────────┘     │                  │
                                                                                                │               │                              │         │                                   │                  │
                                                                                                │               │                              │         │                                   │                  │
                                                                                                │               │                              │         │                                   │                  │
                                                                                                │               │                              │         │                                   │                  │
                                                                                                │┌──────────────┼──────────────────────────────┼─────────┼───────────────────────────────────┼──────────────────┘
                                                                                                vv              │                              v         v                                   │
                                                                                 ┌────────────────┐             │             ┌───────────────┌───────────┐──────────────────────────────────┘
                                                                                 │  internal/cpu  │             │             │               │  runtime  │
                                                                                 └────────────────┘             v             │               └───────────┘
                                                                                                               ┌───────────────┐
                                                                                                               │  sync/atomic  │
                                                                                                               └───────────────┘
```
----

And lastly, here's the raw `mmd` output, without letting markdown render it for us:

```
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

Cheers!
