import math

from codeask.chunker import Chunk
from codeask.embeddings import DIM, embed_chunks, embed_query


def _cos(a, b):
    return sum(x * y for x, y in zip(a, b)) / (math.hypot(*a) * math.hypot(*b))


def test_vectors_have_expected_shape_and_rank_relevant_chunk_first():
    chunks = [
        Chunk("db.py", 1, 3, "def connect():\n    return sqlite3.connect(DB_PATH)"),
        Chunk("auth.py", 1, 4, "def login(user, password):\n    check_password_hash(user.hash, password)"),
    ]
    vecs = embed_chunks(chunks)
    assert len(vecs) == 2 and all(len(v) == DIM for v in vecs)
    q = embed_query("how are passwords checked when a user logs in?")
    assert _cos(q, vecs[1]) > _cos(q, vecs[0])
