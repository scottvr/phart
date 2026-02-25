#/bin/bash

echo "### Demonstration of layout strategies using triads:"
echo ""
echo "# A few good candidate layouts using a Graph from GitHub"
echo "#  Issue #7 (bidirectional but assymetric attributes demo)"
echo ""
for charset in unicode;
    do
        echo "# Run Issue #7a demos using ${charset}?";
        echo ""
        read -n 1 -s -r -p "Press 'y' to proceed or any other to skip to next step" yn
        case "$yn" in
            [Yy])
                for x in arf auto bfs bipartite btree circular hierarchical kamada-kawai layered multipartite planar random shell spiral spring vertical ;
                    do
                    echo "**${x}** layout strategy";
                    echo ""
                    phart issue_7.py  --layout ${x} --hpad 1 --vpad 1 --layer-spacing 4 --node-spacing 3 --labels  --colors attr  --edge-anchors ports --edge-color-rule relationship:friend=green,enemy=red --bbox --uniform --charset ${charset} ;
                    done
        ;;
        *) echo;;
        esac
    done

echo "";
echo "### Demonstration of ALL layouts using the Graph from GitHub Issue #8 (cyclical)"
echo ""
echo "# A few good candidate layouts using a Graph from GitHub"
echo "#  Issue #8 (cyclical triad)"
echo ""
for charset in ascii ansi unicode;
    do
        echo ""
        echo "# Run Issue #8 demos in ${charset}?";
        echo ""
        read -n 1 -s -r -p "Press 'y' to proceed or any other to skip to next step" yn
        case "$yn" in
            [Yy])
            echo ""
        for x in auto circular planar shell spring vertical ;
            do
                echo "**${x}** layout strategy";
                phart issue_8.py  --layout ${x} --hpad 2 --vpad 1 --layer-spacing 4 --node-spacing 3 --labels  --colors attr  --edge-anchors ports --edge-color-rule relationship:friend=green,enemy=red --bbox --uniform --charset ${charset} ;
            done
        ;;
            *);;
        esac
    done

    echo "# Done."
