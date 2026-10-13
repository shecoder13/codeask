"""Local embeddings with fastembed (ONNX, no PyTorch, no API key)."""

from collections.abc import Iterable
from functools import lru_cache

from codeask.chunker import Chunk

MODEL = "BAAI/bge-small-en-v1.5"
DIM = 384


@lru_cache(maxsize=1)
def _model():
    from fastembed import TextEmbedding  # imported lazily: first call downloads the model (~130 MB)

    return TextEmbedding(MODEL)


def embed_chunks(chunks: Iterable[Chunk]) -> list[list[float]]:
    """One vector per chunk. The file path is included so path words ("auth", "config") are searchable."""
    return [v.tolist() for v in _model().embed(f"{c.path}\n{c.text}" for c in chunks)]


def embed_query(question: str) -> list[float]:
    """bge models need a special query prefix; fastembed's query_embed adds it."""
    return next(iter(_model().query_embed(question))).tolist()
