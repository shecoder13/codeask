"""List the text files worth embedding."""

import os
import subprocess
from collections.abc import Iterator
from pathlib import Path

SKIP_DIRS = {".git", "node_modules", "dist", "build", "vendor", "__pycache__", ".venv", "venv", "target"}
SKIP_NAMES = {"package-lock.json", "pnpm-lock.yaml", "yarn.lock", "go.sum", "poetry.lock", "uv.lock"}
SKIP_SUFFIXES = {".lock", ".map", ".min.js", ".min.css"}
MAX_BYTES = 500_000


def _candidates(root: Path) -> list[str]:
    if (root / ".git").exists():  # respects .gitignore
        p = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                           cwd=root, capture_output=True)
        if p.returncode == 0:
            return [x for x in p.stdout.decode("utf-8", "replace").split("\0") if x]
    return [os.path.relpath(os.path.join(d, f), root).replace(os.sep, "/")
            for d, _, files in os.walk(root) for f in files]


def iter_files(root: Path, max_bytes: int = MAX_BYTES) -> Iterator[str]:
    """Yield repo-relative posix paths of non-empty, non-binary files, sorted."""
    for rel in sorted(set(_candidates(root))):
        parts = rel.split("/")
        name = parts[-1]
        if SKIP_DIRS.intersection(parts[:-1]) or name in SKIP_NAMES or name.endswith(tuple(SKIP_SUFFIXES)):
            continue
        path = root / rel
        if path.is_symlink() or not path.is_file():
            continue
        size = path.stat().st_size
        if not 0 < size <= max_bytes:
            continue
        with open(path, "rb") as f:
            if b"\0" in f.read(8000):
                continue
        yield rel
