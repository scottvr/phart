# PHART Examples

This directory contains example scripts demonstrating PHART's capabilities.

## Chess Masters Example

`chess_masters.py` shows how PHART can visualize complex real-world networks. It creates
an ASCII visualization of World Chess Championship games from 1886-1985.

To run the example:

1. Download WCC.pgn.bz2 from https://chessproblem.my-free-games.com/chess/games/Download-PGN.php
2. Place it in this directory
3. Run `python chess_masters.py`

The script will create both a text file output and display the graph in the terminal.

Sample output:

```
                               ---------------------------------[Botvinnik, Mikhail M]---------------------------------
                               |               |                           |                 |                        |
            v                  |               |                    v      |                 |                        |                     v
  [Bronstein, David I]----[Euwe, Max]----[Keres, Paul]----[Petrosian, Tigran V]----[Reshevsky, Samuel H]----[Smyslov, Vassily V]----[Tal, Mikhail N]
                               ^                               |    |
                                                               |    |                   v
                                                    [Alekhine, Alexander A]----[Spassky, Boris V]
                                                               |           |            |
                                                  v            |           |            |           v
                                        [Bogoljubow, Efim D]----[Capablanca, Jose Raul] ---[Fischer, Robert J]
                                                                          |^
                                                                          |
                                                                  [Lasker, Emanuel]--------------
                                                                          |                     |
                            v                      v                      v                     |                       v
                   [Janowski, Dawid M]----[Marshall, Frank J]----[Schlechter, Carl]----[Steinitz, Wilhelm]----[Tarrasch, Siegbert]
                                                                                                |  |
                                                 v                        v                     |  |
                                       [Chigorin, Mikhail I]----[Gunsberg, Isidor A]----[Zukertort, Johannes H]


                                            [Karpov, Anatoly]----[Kasparov, Gary]----[Korchnoi, Viktor L]
```

This visualization clearly shows:

- The main connected component of historical World Champions
- The separate Karpov-Kasparov-Korchnoi group
- The natural chronological flow (generally older players higher up)
