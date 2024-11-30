# PHART Examples

This directory contains example scripts demonstrating PHART's capabilities.

## Chess Masters Example (`chess_masters.py`)

Demonstrates PHART's ability to handle complex real-world networks by visualizing World Chess Championship games from 1886-1985. This example shows how PHART can elegantly handle large, complex graphs with minimal configuration.

To run this example:

1. Download WCC.pgn.bz2 from https://chessproblem.my-free-games.com/chess/games/Download-PGN.php
2. Place it in this directory
3. Run `python chess_masters.py`

## Simple Graph Examples (`simple_graph.py`)

Basic examples showing PHART's core functionality:

- Simple directed graphs
- Different node styles (square, round, diamond, minimal)
- Cycle handling

Perfect for getting started with PHART.

## Dependency Tree Example (`dependency_tree.py`)

Shows how to use PHART for visualizing package dependencies:

- Typical package dependency trees
- Circular dependency detection
- Different layout approaches for dependency graphs

## NetworkX Integration (`networkx_integration.py`)

Demonstrates PHART's seamless integration with NetworkX's various graph generators and algorithms.

## Graph Examples (`showcase.py`)

A collection of different graph types and visualization scenarios:

- Organizational hierarchies
- Network topologies
- Workflow diagrams
- Process flows

## Example Screenshots

The `WCC-plt-Capture.png` shows the matplotlib visualization of the chess masters graph for comparison with PHART's ASCII output.

## Running the Examples

All examples can be run directly:

```bash
python simple_graph.py
python dependency_tree.py
# etc.
```

No additional dependencies are required beyond PHART's core requirements (NetworkX), except for the chess example which needs the WCC.pgn.bz2 data file.
