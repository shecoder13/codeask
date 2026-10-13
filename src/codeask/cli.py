"""codeask index <repo>   |   codeask ask <repo> "question"   (repo = GitHub URL or local folder)"""

import typer

from codeask.answer import answer
from codeask.indexer import sync
from codeask.source import resolve_source
from codeask.store import connect, db_path

app = typer.Typer(no_args_is_help=True, add_completion=False)


def _synced(repo: str):
    folder, _ = resolve_source(repo)
    db = connect(db_path(folder))
    changed, removed = sync(folder, db, log=lambda s: typer.echo(s, err=True))
    return db, changed, removed


@app.command("index")
def index_cmd(repo: str):
    """Build or refresh the index (only changed files are re-embedded)."""
    _, changed, removed = _synced(repo)
    typer.echo(f"done: {changed} files indexed, {removed} removed")


@app.command("ask")
def ask_cmd(repo: str, question: str):
    """Answer a question about the repo, with file and line citations."""
    db, _, _ = _synced(repo)
    text, chunks = answer(db, question)
    typer.echo(text)
    typer.echo("\nSources:")
    for c in chunks:
        typer.echo(f"  {c.path}:{c.start}-{c.end}")


if __name__ == "__main__":
    app()
