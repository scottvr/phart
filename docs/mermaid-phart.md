# phart does mermaid. mermaid pharts. news at 11.

By request, `--output` has another viable target in its `--output-format` directory, with the addition of `mmd`, which is a mermaid TD flowchart.

It's not configurable in any way, but if you have a large graph, it can save you a ton of time since mmd is another plain text format, so you can search and replace to change the number of dashes in an edge (layout hint), or change it to a thick line (`-` to `==`), etc with a quick searach-and-replace op in your favorite 
editor.  

Also, just like with screen renders, if you pass `--label` to the cli, or `use_labels=True` in your LayoutOptions programmatically, then whatever is in 
the label attribute for any  given node will be displayed as appropriate. If there is no label, the string representation of whatever type of object it is is used 
(id, name, etc), though for mermaid, if there was a long and difficult identifier and no alternative label, the id may look a little wonky (e.g., if it had spaces
or quotes in it, they were normalized away.) Without enabling labels, the node name/id is displayed, as with any other rendered output format.

That is all for today. Carry on.  Oh... Below you see the "Go Package Dependency" DAG that I've used for other tests in other documentation you will find 
here, with the mermaid live editor on the left anad vscode on the right. The DOT file that contains this 50-node graph is in the `examples/` directory in the repo.

----

<img width="1207" height="600" alt="mermaid-pharts" src="https://github.com/user-attachments/assets/0b4f5e5b-4769-4c55-8419-1c4edbd33d6f" />
