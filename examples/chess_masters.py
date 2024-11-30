"""
World Chess Championship visualization example.

This example demonstrates PHART's ability to handle complex real-world graphs
by visualizing World Chess Championship games from 1886-1985.

Data source: https://chessproblem.my-free-games.com/chess/games/Download-PGN.php
Original example adapted from NetworkX gallery:
https://networkx.org/documentation/latest/auto_examples/drawing/plot_chess_masters.html
"""

import bz2
from pathlib import Path
import networkx as nx
from phart import ASCIIRenderer, NodeStyle

# Tag names specifying game info to store in edge data
GAME_DETAILS = ["Event", "Date", "Result", "ECO", "Site"]


def load_chess_games(pgn_file="WCC.pgn.bz2") -> nx.MultiDiGraph:
    """
    Read chess games in PGN format.

    Parameters
    ----------
    pgn_file : str
        Path to PGN file (can be bz2 compressed)

    Returns
    -------
    NetworkX MultiDiGraph
        Graph where nodes are players and edges represent games
    """
    G = nx.MultiDiGraph()
    game = {}

    with bz2.BZ2File(pgn_file) as datafile:
        lines = [line.decode().rstrip("\r\n") for line in datafile]

    for line in lines:
        if line.startswith("["):
            tag, value = line[1:-1].split(" ", 1)
            game[str(tag)] = value.strip('"')
        else:
            # Empty line after tag set indicates end of game info
            if game:
                white = game.pop("White")
                black = game.pop("Black")
                G.add_edge(white, black, **game)
                game = {}
    return G


def main():
    # Check if data file exists
    data_file = Path(__file__).parent / "WCC.pgn.bz2"
    if not data_file.exists():
        print(f"Please download WCC.pgn.bz2 to {data_file}")
        print(
            "from: https://chessproblem.my-free-games.com/chess/games/Download-PGN.php"
        )
        return

    # Load and analyze the data
    G = load_chess_games(data_file)
    print(
        f"Loaded {G.number_of_edges()} chess games between {G.number_of_nodes()} players\n"
    )

    # Convert to undirected graph for visualization
    H = nx.Graph(G)

    # Create ASCII visualization
    renderer = ASCIIRenderer(
        H,
        node_style=NodeStyle.SQUARE,  # Square brackets for player names
        node_spacing=4,  # Space between nodes
        layer_spacing=1,  # Compact vertical spacing
    )

    # Save to file and display
    renderer.write_to_file("chess_masters.txt")
    print(renderer.render())

    # Print some interesting statistics
    print("\nMost frequent openings:")
    openings = {}
    for _, _, game_info in G.edges(data=True):
        if "ECO" in game_info:
            eco = game_info["ECO"]
            openings[eco] = openings.get(eco, 0) + 1

    for eco, count in sorted(openings.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"ECO {eco}: {count} games")


if __name__ == "__main__":
    main()
