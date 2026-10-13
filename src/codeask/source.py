"""Turn a GitHub URL or local folder into a directory on disk."""

import os
import re
import subprocess
from pathlib import Path

_GITHUB = re.compile(r"https://github\.com/([A-Za-z0-9][\w.-]*)/([A-Za-z0-9][\w.-]*?)(?:\.git)?/?")


def _git(*args: str, cwd: Path | None = None) -> str:
    cmd = ["git", "-c", f"core.hooksPath={os.devnull}", *args]
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=300)
    if p.returncode != 0:
        raise RuntimeError(f"git {args[0]} failed: {p.stderr.strip()}")
    return p.stdout.strip()


def resolve_source(text: str) -> tuple[Path, str | None]:
    """Return (folder, commit). A GitHub URL is shallow-cloned (or refreshed) in ~/.codeask/repos."""
    text = text.strip()
    if not text:
        raise ValueError("empty repo input")
    local = Path(text).expanduser()
    if local.is_dir():
        try:
            return local.resolve(), _git("rev-parse", "HEAD", cwd=local)
        except RuntimeError:
            return local.resolve(), None

    m = _GITHUB.fullmatch(text)
    if not m:
        raise ValueError(f"expected a GitHub URL (https://github.com/owner/repo) or a folder: {text!r}")
    owner, repo = m.groups()
    dest = Path(os.environ.get("CODEASK_HOME") or Path.home() / ".codeask") / "repos" / owner / repo
    if (dest / ".git").is_dir():
        _git("fetch", "--depth", "1", "origin", "HEAD", cwd=dest)
        _git("reset", "--hard", "FETCH_HEAD", cwd=dest)
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        _git("clone", "--depth", "1", "--", f"https://github.com/{owner}/{repo}.git", str(dest))
    return dest, _git("rev-parse", "HEAD", cwd=dest)
