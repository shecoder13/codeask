import hashlib

import pytest

pytest.importorskip("sqlite_vec")

from codeask.embeddings import DIM  # noqa: E402
from codeask.indexer import sync  # noqa: E402
from codeask.store import connect, search  # noqa: E402


def fake_embed(chunks):
    out = []
    for c in chunks:
        v = [0.0] * DIM
        v[int(hashlib.md5(c.text.encode()).hexdigest(), 16) % DIM] = 1.0
        out.append(v)
    return out


def test_sync_is_incremental(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "a.py").write_text("def alpha(): pass\n")
    (repo / "b.py").write_text("def beta(): pass\n")
    db = connect(tmp_path / "i.db")

    assert sync(repo, db, embed=fake_embed) == (2, 0)
    assert sync(repo, db, embed=fake_embed) == (0, 0)          # nothing changed
    (repo / "a.py").write_text("def alpha_two(): pass\n")
    assert sync(repo, db, embed=fake_embed) == (1, 0)          # only a.py redone
    (repo / "b.py").unlink()
    assert sync(repo, db, embed=fake_embed) == (0, 1)          # b.py dropped
    assert [c.path for c in search(db, fake_embed([])[:0] or [0.0] * DIM, "alpha_two")] == ["a.py"]
