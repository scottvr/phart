#/bin/bash

echo "### Demonstration of layout strategies:"
read -n 1 -s -r -p "Press 'y' to proceed or any other to skip to next step" yn
case "$yn" in
    [Yy])
    echo ""
    echo " ALL layouts using Graph from GitHub Issue #7"
    for charset in ascii ansi unicode;
        do
            echo "## ${charset} demos";
            read -n 1 -s -r -p "Press 'y' to proceed or any other to skip to next step" yn
            case "$yn" in
                [Yy])
                    for x in arf auto bfs bipartite btree circular hierarchical kamada-kawai layered multipartite planar random shell spiral spring vertical ;
                        do
                        echo "# ${x}";
                        phart issue_7.py  --layout ${x} --hpad 1 --vpad 1 --layer-spacing 4 --node-spacing 3 --labels  --colors attr  --edge-anchors ports --edge-color-rule relationship:friend=green,enemy=red --bbox --uniform --charset ${charset} ;
                        done
            ;;
            *) echo;;
            esac
        done
    echo "";
    echo "ALL layouts using the Graph from GitHub Issue #8"
    for charset in ascii ansi unicode;
        do
            echo ""
            echo "## ${charset} demos";
            read -n 1 -s -r -p "Press 'y' to proceed or any other to skip to next step" yn
            case "$yn" in
                [Yy])
                echo ""
            for x in auto circular planar shell spring vertical ;
                do
                    echo "# ${x}";
                    phart issue_8.py  --layout ${x} --hpad 2 --vpad 1 --layer-spacing 4 --node-spacing 3 --labels  --colors attr  --edge-anchors ports --edge-color-rule relationship:friend=green,enemy=red --bbox --uniform --charset ${charset} ;
                done
            ;;
                *);;
            esac
        done
        ;;
    *) echo "";;
esac


echo ""
echo "### Demonstration of various layout options using a Collatz tree."
read -n 1 -s -r -p "Press 'y' to proceed or any other to skip to next step" yn
case "$yn" in
    [Yy])
    echo;

    cmd="phart --ascii --layer-spacing 3 --node-spacing 3 --btree collatz.py -- 3"
    echo "${cmd}"
    read -n 1 -s -r -p "Press 'y' to proceed or any other to skip to next step: " yn
    case "$yn" in
        [Yy])
        echo
        ${cmd}
        ;;
        *)
    esac

    cmd="phart  --layer-spacing 4 --btree --bbox collatz.py -- 5"
    echo
    echo "${cmd}"
    read -n 1 -s -r -p "Press 'y' to proceed or any other to skip to next step: " yn
    case "$yn" in
        [Yy])
        echo
        ${cmd}
        ;;
        *)
    esac

    cmd="phart  --bbox --layer-spacing 4 --btree --edge-anchors ports --uniform collatz.py -- 4"
    echo
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
    echo "# the following command demonstrates how using '--colors source'"
    echo "# can help clear up where an edge path comes from in the event of"
    echo "# a confusing or condensed diagram. It also shows that since our "
    echo "# diagrams are plain text, we can use the 'tail' command to limit"
    echo "# our output to the last n rows (17 in this case) of phart's output."
    echo ""
    cmd="phart --layout bfs --bbox --layer-spacing 4 --btree --edge-anchors center --uniform  --colors source   collatz.py -- 7"
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

    ;;
    *)
;;
esac
