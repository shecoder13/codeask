import pytest

pytest.importorskip("sqlite_vec")

from codeask.chunker import Chunk  # noqa: E402
from codeask.embeddings import DIM  # noqa: E402
from codeask.store import add_file, connect, fuse, remove_file, search, stored_hashes  # noqa: E402


def vec(i):  # a one-hot vector: "direction i"
    v = [0.0] * DIM
    v[i] = 1.0
    return v


def test_fuse_rewards_agreement():
    assert fuse([1, 2, 3], [3, 4])[0] == 3
    assert fuse([], []) == []


def test_search_finds_by_vector_and_by_keyword(tmp_path):
    db = connect(tmp_path / "i.db")
    a, b = Chunk("auth.py", 1, 3, "def login(user): pass"), Chunk("db.py", 1, 3, "def connect(): pass")
    add_file(db, "auth.py", "h1", [a], [vec(0)])
    add_file(db, "db.py", "h2", [b], [vec(1)])
    assert search(db, vec(1), "zzz")[0] == b          # vector match only
    assert search(db, vec(5), "login")[0] == a        # keyword match only
    assert stored_hashes(db) == {"auth.py": "h1", "db.py": "h2"}


def test_replace_and_remove(tmp_path):
    db = connect(tmp_path / "i.db")
    add_file(db, "a.py", "h1", [Chunk("a.py", 1, 1, "old text")], [vec(0)])
    add_file(db, "a.py", "h2", [Chunk("a.py", 1, 1, "new text")], [vec(0)])
    assert [c.text for c in search(db, vec(0), "text")] == ["new text"]
    remove_file(db, "a.py")
    assert search(db, vec(0), "text") == [] and stored_hashes(db) == {}
