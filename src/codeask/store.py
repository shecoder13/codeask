"""SQLite index: chunks + vectors (sqlite-vec) + keyword search (FTS5), fused with RRF."""

import hashlib
import os
import re
import sqlite3
from pathlib import Path

import sqlite_vec

from codeask.chunker import Chunk
from codeask.embeddings import DIM


def db_path(folder: Path) -> Path:
    base = Path(os.environ.get("CODEASK_HOME") or Path.home() / ".codeask") / "indexes"
    base.mkdir(parents=True, exist_ok=True)
    return base / f"{folder.name}-{hashlib.sha1(str(folder).encode()).hexdigest()[:10]}.db"


def connect(path) -> sqlite3.Connection:
    db = sqlite3.connect(path)
    db.enable_load_extension(True)
    sqlite_vec.load(db)
    db.enable_load_extension(False)
    db.executescript(f"""
        CREATE TABLE IF NOT EXISTS files(path TEXT PRIMARY KEY, hash TEXT);
        CREATE TABLE IF NOT EXISTS chunks(
            id INTEGER PRIMARY KEY, path TEXT, start_line INT, end_line INT, text TEXT);
        CREATE INDEX IF NOT EXISTS chunks_path ON chunks(path);
        CREATE VIRTUAL TABLE IF NOT EXISTS vec USING vec0(embedding float[{DIM}]);
        CREATE VIRTUAL TABLE IF NOT EXISTS fts USING fts5(path, text);
    """)
    return db


def stored_hashes(db) -> dict[str, str]:
    return dict(db.execute("SELECT path, hash FROM files"))


def remove_file(db, path: str) -> None:
    with db:
        for (i,) in db.execute("SELECT id FROM chunks WHERE path=?", (path,)).fetchall():
            db.execute("DELETE FROM vec WHERE rowid=?", (i,))
            db.execute("DELETE FROM fts WHERE rowid=?", (i,))
        db.execute("DELETE FROM chunks WHERE path=?", (path,))
        db.execute("DELETE FROM files WHERE path=?", (path,))


def add_file(db, path: str, digest: str, chunks: list[Chunk], vectors: list[list[float]]) -> None:
    """Replace everything stored for `path` in one transaction."""
    remove_file(db, path)
    with db:
        for c, v in zip(chunks, vectors, strict=True):
            i = db.execute(
                "INSERT INTO chunks(path, start_line, end_line, text) VALUES (?,?,?,?)",
                (c.path, c.start, c.end, c.text),
            ).lastrowid
            db.execute("INSERT INTO vec(rowid, embedding) VALUES (?,?)", (i, sqlite_vec.serialize_float32(v)))
            db.execute("INSERT INTO fts(rowid, path, text) VALUES (?,?,?)", (i, c.path, c.text))
        db.execute("INSERT INTO files VALUES (?,?)", (path, digest))


def fuse(*rankings: list[int], k: int = 60) -> list[int]:
    """Reciprocal rank fusion: ids ranked high in any list float to the top."""
    score: dict[int, float] = {}
    for ranking in rankings:
        for rank, i in enumerate(ranking):
            score[i] = score.get(i, 0.0) + 1.0 / (k + rank)
    return sorted(score, key=score.__getitem__, reverse=True)


def search(db, qvec: list[float], question: str, k: int = 8, pool: int = 30) -> list[Chunk]:
    by_vector = [r[0] for r in db.execute(
        "SELECT rowid FROM vec WHERE embedding MATCH ? AND k = ? ORDER BY distance",
        (sqlite_vec.serialize_float32(qvec), pool))]
    words = re.findall(r"\w+", question)[:20]
    by_keyword = [r[0] for r in db.execute(
        "SELECT rowid FROM fts WHERE fts MATCH ? ORDER BY rank LIMIT ?",
        (" OR ".join(f'"{w}"' for w in words), pool))] if words else []
    rows = (db.execute("SELECT path, start_line, end_line, text FROM chunks WHERE id=?", (i,)).fetchone()
            for i in fuse(by_vector, by_keyword)[:k])
    return [Chunk(*r) for r in rows if r]
