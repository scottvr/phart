"""Text output pagination helpers."""

from __future__ import annotations

from dataclasses import dataclass

from phart.rendering.ansi import ANSI_TOKEN_RE


@dataclass(frozen=True)
class TextPage:
    x_index: int
    y_index: int
    col_start: int
    col_end: int
    row_start: int
    row_end: int
    text: str


def _page_starts(total: int, page_size: int, overlap: int) -> list[int]:
    if total <= 0:
        return [0]
    if page_size <= 0:
        raise ValueError("page_size must be greater than zero")
    if overlap < 0:
        raise ValueError("overlap must be non-negative")
    if overlap >= page_size:
        raise ValueError("overlap must be smaller than page_size")

    if total <= page_size:
        return [0]

    step = page_size - overlap
    starts = list(range(0, total, step))
    last_start = max(0, total - page_size)
    if starts[-1] > last_start:
        starts[-1] = last_start
    elif starts[-1] != last_start:
        starts.append(last_start)
    ordered_unique: list[int] = []
    seen: set[int] = set()
    for start in starts:
        if start in seen:
            continue
        ordered_unique.append(start)
        seen.add(start)
    return ordered_unique


def paginate_text(
    text: str,
    *,
    page_width: int,
    overlap: int = 8,
    page_height: int | None = None,
    overlap_y: int = 0,
) -> tuple[list[TextPage], int, int]:
    """Paginate plain text into overlapping page slices.

    Returns pages and source canvas width/height.
    """
    rows = text.splitlines()
    canvas_height = len(rows)
    canvas_width = max((_visible_len(row) for row in rows), default=0)
    if page_height is None:
        page_height = canvas_height if canvas_height > 0 else 1

    x_starts = _page_starts(canvas_width, page_width, overlap)
    y_starts = _page_starts(canvas_height, page_height, overlap=overlap_y)

    pages: list[TextPage] = []
    for y_idx, y_start in enumerate(y_starts):
        y_end = min(canvas_height, y_start + page_height)
        row_slice = rows[y_start:y_end]
        for x_idx, x_start in enumerate(x_starts):
            x_end = min(canvas_width, x_start + page_width)
            page_rows = [_slice_ansi_line(row, x_start, x_end).rstrip() for row in row_slice]
            page_text = "\n".join(page_rows)
            pages.append(
                TextPage(
                    x_index=x_idx,
                    y_index=y_idx,
                    col_start=x_start,
                    col_end=max(x_start, x_end - 1),
                    row_start=y_start,
                    row_end=max(y_start, y_end - 1),
                    text=page_text,
                )
            )
    return pages, canvas_width, canvas_height


def _visible_len(line: str) -> int:
    visible = 0
    for token in ANSI_TOKEN_RE.findall(line):
        if token.startswith("\x1b["):
            continue
        visible += 1
    return visible


def _slice_ansi_line(line: str, start: int, end: int) -> str:
    if start >= end:
        return ""

    visible_idx = 0
    active_ansi: str | None = None
    started = False
    output: list[str] = []

    for token in ANSI_TOKEN_RE.findall(line):
        if token.startswith("\x1b["):
            if token == "\x1b[0m":
                active_ansi = None
            else:
                active_ansi = token
            if started:
                output.append(token)
            continue

        in_slice = start <= visible_idx < end
        if in_slice and not started:
            started = True
            if active_ansi is not None:
                output.append(active_ansi)
        if in_slice:
            output.append(token)

        visible_idx += 1
        if visible_idx >= end and started:
            break

    if started and active_ansi is not None:
        output.append("\x1b[0m")

    return "".join(output)


def describe_pages(
    pages: list[TextPage],
    *,
    canvas_width: int,
    canvas_height: int,
    page_width: int,
    overlap: int,
) -> str:
    """Render a concise page index for CLI diagnostics."""
    if not pages:
        return (
            f"Pagination: 0 pages, canvas={canvas_width}x{canvas_height}, "
            f"page_width={page_width}, overlap={overlap}"
        )
    lines = [
        (
            f"Pagination: {len(pages)} page(s), canvas={canvas_width}x{canvas_height}, "
            f"page_width={page_width}, overlap={overlap}"
        )
    ]
    for page in pages:
        lines.append(
            f"  page[x={page.x_index},y={page.y_index}] "
            f"cols={page.col_start + 1}-{page.col_end + 1} "
            f"rows={page.row_start + 1}-{page.row_end + 1}"
        )
    return "\n".join(lines)
