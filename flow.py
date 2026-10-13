"""Run the pipeline end to end with progress. Usage: uv run python flow.py [max_chunks]"""
import sys
import time

from codeask.chunker import chunk_file
from codeask.embeddings import embed_chunks
from codeask.source import resolve_source
from codeask.walker import iter_files

limit = int(sys.argv[1]) if len(sys.argv) > 1 else None

t = time.time()
folder, commit = resolve_source("https://github.com/pallets/click")
files = list(iter_files(folder))
chunks = [c for f in files for c in chunk_file(folder, f)][:limit]
print(f"{commit[:12]}: {len(files)} files, {len(chunks)} chunks ({time.time() - t:.1f}s)", flush=True)

print("loading model (first run downloads ~130 MB, can take a few minutes)...", flush=True)
t = time.time()
embed_chunks(chunks[:1])
print(f"model ready ({time.time() - t:.0f}s)", flush=True)

t = time.time()
vecs = []
for i in range(0, len(chunks), 100):
    vecs += embed_chunks(chunks[i:i + 100])
    print(f"  embedded {len(vecs)}/{len(chunks)} ({time.time() - t:.0f}s)", flush=True)
print(f"done: {len(vecs)} vectors of {len(vecs[0])} numbers", flush=True)
