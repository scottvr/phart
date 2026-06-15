import tomllib
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from .layout import CrossPartitionEdge, PartitionPlan
from .renderer import ASCIIRenderer
from .styles import LayoutOptions, NodeStyle


def _resolve_version() -> str:
    pyproject_path = Path(__file__).resolve().parents[2] / "pyproject.toml"
    if pyproject_path.exists():
        with pyproject_path.open("rb") as pyproject_file:
            pyproject = tomllib.load(pyproject_file)
        return str(pyproject["project"]["version"])
    try:
        return version("phart")
    except PackageNotFoundError:
        return "0+unknown"


__version__ = _resolve_version()
__all__ = [
    "ASCIIRenderer",
    "NodeStyle",
    "LayoutOptions",
    "PartitionPlan",
    "CrossPartitionEdge",
]
