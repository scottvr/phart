echo "### Demonstration of ALL layout strategies:"

echo "Using the Graph from GitHub Issue #7
for charset in ascii ansi unicode; do echo "## ${charset}"; for x in arf auto bfs bipartite circular hierarchical kamada-kawai layered multipartite planar random shell spiral spring vertical ; do echo "# ${x}"; phart issue_7.py  --layout ${x} --labels  --colors attr  --edge-anchors ports --edge-color-rule relationship:friend=green,enemy=red --bbox --uniform --charset ${charset} ; done; done

echo "Using the Graph from GitHub Issue #8:"
for charset in ascii ansi unicode; do for x in arf auto bfs bipartite circular hierarchical kamada-kawai layered multipartite planar random shell spiral spring vertical ; do echo "# ${x}"; phart issue_8.py  --layout ${x} --labels  --colors attr  --edge-anchors ports --edge-color-rule relationship:friend=green,enemy=red --bbox --uniform --charset ${charset} ; done; done

echo "### Using the Graph from GitHub Discussion #15:"
for charset in ascii ansi unicode; do for x in arf auto bfs bipartite circular hierarchical kamada-kawai layered multipartite planar random shell spiral spring vertical ; do echo "# ${x}"; phart collatz.py  --layout ${x} --labels  --colors attr  --edge-anchors ports --edge-color-rule relationship:friend=green,enemy=red --bbox --uniform --charset ${charset} ; done; done

echo "########"

echo "### Demonstration of effect of various options:"
