"""ANSI constants and conversion helpers for rendering paths."""

from __future__ import annotations

import re
from typing import Optional

ANSI_RESET = "\x1b[0m"
ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*m")
ANSI_SUBWAY_PALETTE = (
    "\x1b[38;5;45m",  # cyan
    "\x1b[38;5;214m",  # orange
    "\x1b[38;5;118m",  # green
    "\x1b[38;5;199m",  # magenta
    "\x1b[38;5;39m",  # blue
    "\x1b[38;5;226m",  # yellow
    "\x1b[38;5;160m",  # red
    "\x1b[38;5;81m",  # aqua
)
ANSI_NAMED_COLORS = {
    "black": "\x1b[30m",
    "red": "\x1b[31m",
    "green": "\x1b[32m",
    "yellow": "\x1b[33m",
    "blue": "\x1b[34m",
    "magenta": "\x1b[35m",
    "cyan": "\x1b[36m",
    "white": "\x1b[37m",
    "bright_black": "\x1b[90m",
    "bright_red": "\x1b[91m",
    "bright_green": "\x1b[92m",
    "bright_yellow": "\x1b[93m",
    "bright_blue": "\x1b[94m",
    "bright_magenta": "\x1b[95m",
    "bright_cyan": "\x1b[96m",
    "bright_white": "\x1b[97m",
    # Palette aliases used by existing subway colors.
    "orange": "\x1b[38;5;214m",
    "aqua": "\x1b[38;5;81m",
}
UNICODE_DITAA_MAP = {
    "─": "-",
    "│": "|",
    "┌": "+",
    "┐": "+",
    "└": "+",
    "┘": "+",
    "┬": "+",
    "┴": "+",
    "├": "+",
    "┤": "+",
    "┼": "+",
    "═": "=",
    "║": "|",
    "╔": "+",
    "╗": "+",
    "╚": "+",
    "╝": "+",
    "╠": "+",
    "╣": "+",
    "╦": "+",
    "╩": "+",
    "╬": "+",
    "→": ">",
    "←": "<",
    "↑": "^",
    "↓": "v",
}


def normalize_edge_attr_value(value: object) -> str:
    text = str(value).strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {"'", '"'}:
        text = text[1:-1]
    return text.strip().lower()


def resolve_color_spec(spec: object) -> Optional[str]:
    """Resolve a color spec into an ANSI escape sequence."""
    token = str(spec).strip()
    if not token:
        return None

    lowered = token.lower()
    if lowered in ANSI_NAMED_COLORS:
        return ANSI_NAMED_COLORS[lowered]

    if token.startswith("\x1b[") and token.endswith("m"):
        return token

    if lowered.startswith("color") and lowered[5:].isdigit():
        lowered = lowered[5:]

    if lowered.isdigit():
        color_index = int(lowered)
        if 0 <= color_index <= 255:
            return f"\x1b[38;5;{color_index}m"

    if lowered.startswith("#") and len(lowered) == 7:
        try:
            r = int(lowered[1:3], 16)
            g = int(lowered[3:5], 16)
            b = int(lowered[5:7], 16)
            return f"\x1b[38;2;{r};{g};{b}m"
        except ValueError:
            return None

    return None


def xterm_index_to_hex(idx: int) -> str:
    idx = max(0, min(255, idx))
    base16 = [
        (0, 0, 0),
        (128, 0, 0),
        (0, 128, 0),
        (128, 128, 0),
        (0, 0, 128),
        (128, 0, 128),
        (0, 128, 128),
        (192, 192, 192),
        (128, 128, 128),
        (255, 0, 0),
        (0, 255, 0),
        (255, 255, 0),
        (0, 0, 255),
        (255, 0, 255),
        (0, 255, 255),
        (255, 255, 255),
    ]
    if idx < 16:
        r, g, b = base16[idx]
        return f"#{r:02x}{g:02x}{b:02x}"
    if idx < 232:
        idx -= 16
        r = idx // 36
        g = (idx % 36) // 6
        b = idx % 6
        conv = [0, 95, 135, 175, 215, 255]
        rr, gg, bb = conv[r], conv[g], conv[b]
        return f"#{rr:02x}{gg:02x}{bb:02x}"
    gray = 8 + (idx - 232) * 10
    return f"#{gray:02x}{gray:02x}{gray:02x}"


def ansi_to_hex(ansi: str) -> Optional[str]:
    match = re.search(r"\x1b\[([0-9;]+)m", ansi)
    if not match:
        return None
    try:
        codes = [int(p) for p in match.group(1).split(";") if p]
    except ValueError:
        return None

    fg_color: Optional[str] = None
    i = 0
    while i < len(codes):
        code = codes[i]

        if code in {0, 39}:
            fg_color = None
        elif 30 <= code <= 37:
            fg_color = xterm_index_to_hex(code - 30)
        elif 90 <= code <= 97:
            fg_color = xterm_index_to_hex(8 + (code - 90))
        elif code == 38 and i + 1 < len(codes):
            mode = codes[i + 1]
            if mode == 5 and i + 2 < len(codes):
                fg_color = xterm_index_to_hex(codes[i + 2])
                i += 2
            elif mode == 2 and i + 4 < len(codes):
                r = max(0, min(255, codes[i + 2]))
                g = max(0, min(255, codes[i + 3]))
                b = max(0, min(255, codes[i + 4]))
                fg_color = f"#{r:02x}{g:02x}{b:02x}"
                i += 4
        i += 1

    return fg_color
