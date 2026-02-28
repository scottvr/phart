from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from phart.renderer import ASCIIRenderer


def write_to_file(renderer: ASCIIRenderer, filename: str) -> None:
    """
    Write graph representation to a file.

    Parameters
    ----------
    filename : str
        Path to output file
    """

    with open(filename, "w", encoding="utf-8") as f:
        f.write(renderer.render())
