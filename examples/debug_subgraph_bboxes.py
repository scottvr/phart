from pathlib import Path
from phart.renderer import ASCIIRenderer
from phart.styles import LayoutOptions

# debug subgraph bboxes

dot = Path("examples/internet.dot").read_text()
opts = LayoutOptions(
    use_ascii=False,
    bboxes=True,
    node_spacing=5,
    layer_spacing=5,
    edge_anchor_mode="ports",
    shared_ports_mode="none",
    node_order_mode="preserve",
    bidirectional_mode="separate",
    node_label_attr="label",
    edge_label_attr="label",
)
r = ASCIIRenderer.from_dot(dot, options=opts)
pos, w, h = r.layout_manager.calculate_layout()
boxes = r._build_subgraph_boxes(pos)
print("positions", pos)
for n in pos:
    print(n, r._get_node_bounds(n, pos))
for b in boxes:
    print("box", b.subgraph_id, b.left, b.top, b.right, b.bottom, b.title)
