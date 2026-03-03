#!/bin/bash

for x in *.py *.dot *.graphml;  
	do

	phart --bboxes --layer-spacing 3   --vpad 2  --hpad 2    --node-spacing 8  --labels --edge-anchors ports  --layout circular --shared-ports none  --colors attr --edge-color-rule color:red=red,green=green,blue=blue,magenta=magenta,blue=blue --uniform --charset unicode  ${x} ;
	done

