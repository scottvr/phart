# src path: src/phart/charset.py
# for adding new charsets and new cli charset features

from enum import Enum


class CharSet(Enum):
    """Character set options for rendering."""

    ASCII = "ascii"  # 7-bit ASCII characters only
    UNICODE = "unicode"  # Unicode box drawing & arrows

    def __str__(self) -> str:
        return self.value
