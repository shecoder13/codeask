# codeask

Ask questions about any codebase and get answers with **file and line citations**.

Point it at a GitHub URL or a local folder. It indexes the code locally, finds the most relevant pieces, and has an LLM answer using only those pieces, citing each claim as `path:start-end`. If the code doesn't contain the answer, it says `Not found in this repo.`

```
$ uv run python -m codeask.cli ask https://github.com/owner/repo "Where is authentication handled?"

Auth is handled in the login middleware [src/auth/middleware.py:12-48] ...

Sources:
  src/auth/middleware.py:12-48
  src/auth/tokens.py:1-60
```

## How it works

```
repo (URL or folder)
  → source   shallow-clones GitHub URLs to ~/.codeask/repos/owner/repo
  → walker   lists text files via `git ls-files`, skipping lockfiles, binaries, vendored dirs, files > 500 KB
  → chunker  ~1500-character line windows with 5-line overlap, so every chunk has exact line numbers
  → embed    BAAI/bge-small-en-v1.5 (384 dims) running locally via fastembed, no API needed
  → store    one SQLite file: sqlite-vec for vectors + FTS5 for keywords
  → search   vector and keyword results merged with reciprocal rank fusion (top 8 chunks)
  → answer   LLM answers from those chunks only, with citations
```

Indexing is incremental: each file is hashed, and only new or changed files are re-embedded. Deleted files are removed from the index. `ask` refreshes the index first, so answers reflect the current code.

## Install

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/). Git must be on your PATH.

```
uv sync
```

The first run downloads the embedding model (about 130 MB) once.

Windows + OneDrive: keep the project outside OneDrive (e.g. `C:\dev\codeask`). If uv fails with a hardlink error, run `$env:UV_LINK_MODE="copy"` first.

## Usage

```
uv run python -m codeask.cli index <repo>
uv run python -m codeask.cli ask <repo> "your question"
```

`<repo>` is a GitHub URL (`https://github.com/owner/repo`) or a local folder path. `ask` indexes automatically if needed, so `index` is only for warming the cache.

Indexes live at `~/.codeask/indexes/<folder>-<hash>.db`. Delete a file to rebuild that repo from scratch. Set `CODEASK_HOME` to move everything (clones and indexes) elsewhere.

## Choosing the LLM

| Setup | How |
|---|---|
| **Claude** (recommended) | Set `ANTHROPIC_API_KEY`. Default model `claude-sonnet-5-5`; override with `CODEASK_MODEL`. |
| **Ollama** (local, free) | Used when no API key is set. Run `ollama serve` and `ollama pull qwen2.5-coder:7b`. Override with `CODEASK_OLLAMA_MODEL` and `OLLAMA_URL`. A 7B model on CPU can take minutes per answer. |

On PowerShell, environment variables last only for that window: `$env:ANTHROPIC_API_KEY="sk-ant-..."`.

Only the retrieved excerpts (and your question) are sent to the LLM. Indexing and search stay on your machine.

## Safety design

- The model is told to use only the excerpts and to answer exactly `Not found in this repo.` otherwise.
- Repository text is treated as untrusted data; the prompt instructs the model to ignore any instructions found inside code or comments.
- Cloning runs git with hooks disabled.

## Tests

```
uv run python -m pytest -q
```

Tests use fake embeddings and a fake LLM, so they need no network or API key.

## Limitations

- Retrieval returns 8 chunks, so broad questions ("explain the whole architecture") get partial answers. Ask about specific behaviour.
- Chunks are line windows, not syntax-aware, so a function can be split across chunks.
- Text-only: binaries, images and files over 500 KB are skipped.
- Private GitHub repos work only if your local git is already authenticated.
- English-tuned embedding model; code in other languages is handled less well.
- Answer quality depends on the LLM; the small local model is noticeably weaker than Claude.

## Project layout

```
src/codeask/
  source.py      GitHub URL or folder → local path
  walker.py      which files to read
  chunker.py     files → cited chunks
  embeddings.py  local embeddings
  store.py       SQLite index and hybrid search
  indexer.py     incremental sync
  llm.py         Claude or Ollama
  answer.py      prompt and citation handling
  cli.py         index / ask commands
tests/
```
