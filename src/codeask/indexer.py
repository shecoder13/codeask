"""Keep the index in step with the files: re-embed only what changed."""

import hashlib
from pathlib import Path

from codeask.chunker import chunk_file
from codeask.embeddings import embed_chunks
from codeask.store import add_file, remove_file, stored_hashes
from codeask.walker import iter_files


def sync(folder: Path, db, embed=embed_chunks, log=lambda s: None) -> tuple[int, int]:
    """Returns (files re-indexed, files removed)."""
    old, seen, changed = stored_hashes(db), set(), 0
    for rel in iter_files(folder):
        seen.add(rel)
        digest = hashlib.sha1((folder / rel).read_bytes()).hexdigest()
        if old.get(rel) == digest:
            continue
        log(f"indexing {rel}")
        chunks = chunk_file(folder, rel)
        add_file(db, rel, digest, chunks, embed(chunks) if chunks else [])
        changed += 1
    gone = set(old) - seen
    for rel in gone:
        remove_file(db, rel)
    return changed, len(gone)
