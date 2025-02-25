from phart import ASCIIRenderer, NodeStyle
import networkx as nx


def generate_triads():
    triads = {
        "120C": [(1, 2), (2, 1), (1, 3), (3, 2)],  # Four edges cycle
        "210": [(1, 2), (2, 1), (1, 3), (3, 2), (2, 3)],  # Five edges
        "300": [(1, 2), (2, 1), (2, 3), (3, 2), (1, 3), (3, 1)],  # Complete
    }

    graphs = {}
    for name, edge_list in triads.items():
        G = nx.DiGraph()
        G.add_nodes_from([1, 2, 3])  # Always add all three nodes
        G.add_edges_from(edge_list)
        graphs[name] = G

    return graphs


def render_all_triads():
    """Render all triads using PHART and output in a grid-like format."""
    triads = generate_triads()

    # Calculate the width needed for each diagram to create a grid effect
    sample_render = ASCIIRenderer(
        next(iter(triads.values())), node_style=NodeStyle.SQUARE
    ).render()
    width = max(len(line) for line in sample_render.split("\n")) + 4  # Add padding

    # We'll create 4 rows of 4 diagrams each
    output = []
    current_row = []

    for name, graph in triads.items():
        renderer = ASCIIRenderer(graph, node_style=NodeStyle.SQUARE)
        rendered = renderer.render()

        # Add title above the diagram
        diagram_lines = [f"{name:^{width}}"]
        print(f"{diagram_lines}")
        diagram_lines.extend(line.ljust(width) for line in rendered.split("\n"))

        current_row.append(diagram_lines)

        if len(current_row) == 4:  # Start new row after 4 diagrams
            # Combine diagrams in the row
            for i in range(len(current_row[0])):  # For each line
                output.append("".join(diag[i] for diag in current_row))
            output.append("")  # Add blank line between rows
            current_row = []

    # Handle any remaining diagrams in the last row
    if current_row:
        for i in range(len(current_row[0])):
            output.append("".join(diag[i] for diag in current_row))

    return "\n".join(output)


if __name__ == "__main__":
    print(render_all_triads())
