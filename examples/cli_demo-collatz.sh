#!/bin/bash

echo " #### PHART CLI options demo using collatz.py, from GitHub Discussion #16"
echo "Here are a few commands, one at a time, on the same graph with different options;"
echo ""


echo ""
echo "######################"
echo ""
cmd="phart --ascii --layer-spacing 3 --node-spacing 3 --binary-tree collatz.py -- 3"
echo ""
echo "# 7-bit ASCII output, with binary tree sorting using edge attribute 'side'"
echo "######################"
echo ""
echo "${cmd}"
read -n 1 -s -r -p "Press 'y' to proceed or any other to skip to next step: " yn
case "$yn" in
    [Yy])
    echo
    ${cmd}
    ;;
    *)
esac

echo ""
echo "######################"
echo ""
cmd="phart  --layer-spacing 4 --binary-tree --bboxes collatz.py --charset unicode -- 5"
echo "# Same command as before, but we'll add bounding boxes and output unicode if supported by your terminal."
echo "${cmd}"
echo ""
read -n 1 -s -r -p "Press 'y' to proceed or any other to skip to next step: " yn
case "$yn" in
    [Yy])
    echo
    ${cmd}
    ;;
    *)
esac

echo ""
echo "######################"
echo ""
cmd="phart  --bboxes --layer-spacing 4 --binary-tree --edge-anchors ports --uniform --charset unicode collatz.py -- 4"
echo "# Same as last, but we'll increase layer spacing by one and tell phart"
echo "# to create multiple edge start/stop points per box face as needed."
echo ""
echo "${cmd}"
echo ""
echo "######################"
echo ""
read -n 1 -s -r -p "Press 'y' to proceed or any other to skip to next step: " yn
case "$yn" in
    [Yy])
    echo
    ${cmd}
    ;;
    *)
esac

echo ""
echo "######################"
echo ""
echo "# the following command demonstrates how using '--colors source'"
echo "# can help clear up where an edge path comes from in the event of"
echo "# a confusing or condensed diagram. It also shows that since our "
echo "# diagrams are plain text, we can use the 'tail' command to limit"
echo "# our output to the last n rows (17 in this case) of phart's output."
echo ""
cmd="phart --layout bfs --bboxes --layer-spacing 4 --binary-tree --edge-anchors center --uniform  --charset unicode  --colors source   collatz.py -- 7"
echo ""
echo "${cmd} | tail -17"
echo ""
echo "######################"
read -n 1 -s -r -p "Press 'y' to proceed or any other to skip to next step: " yn
case "$yn" in
    [Yy])
    echo
    ${cmd} | tail -17
    ;;
    *)
esac

echo "### Done."
