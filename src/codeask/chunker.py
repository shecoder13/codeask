"""Split files into line-numbered chunks sized for the embedding model."""

from pathlib import Path
from typing import NamedTuple


class Chunk(NamedTuple):
    path: str
    start: int  # 1-based, inclusive
    end: int
    text: str


def chunk_text(text: str, max_chars: int = 1500, overlap: int = 5) -> list[tuple[int, int, str]]:
    """Greedy line packing up to max_chars, preferring to end at a blank line, with line overlap."""
    lines = [ln[:max_chars] for ln in text.splitlines()]
    out, i = [], 0
    while i < len(lines):
        j, size = i, 0
        while j < len(lines) and (j == i or size + len(lines[j]) + 1 <= max_chars):
            size += len(lines[j]) + 1
            j += 1
        if j < len(lines):  # cut early at a blank line if one exists in the back half
            for k in range(j - 1, i + (j - i) // 2, -1):
                if not lines[k].strip():
                    j = k + 1
                    break
        body = "\n".join(lines[i:j])
        if body.strip():
            out.append((i + 1, j, body))
        if j >= len(lines):
            break
        i = max(j - overlap, i + 1)
    return out


def chunk_file(root: Path, rel: str) -> list[Chunk]:
    text = (root / rel).read_text(encoding="utf-8", errors="replace")
    return [Chunk(rel, s, e, t) for s, e, t in chunk_text(text)]
