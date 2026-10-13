import subprocess

from codeask.walker import iter_files


def _make(root):
    (root / "src").mkdir()
    (root / "src" / "app.py").write_text("print('hi')\n")
    (root / "src" / "empty.py").write_text("")
    (root / "logo.png").write_bytes(b"\x89PNG\0\0")
    (root / "big.txt").write_text("x" * 2000)
    (root / "uv.lock").write_text("x")
    (root / "node_modules").mkdir()
    (root / "node_modules" / "dep.js").write_text("1\n")
    (root / "noise.log").write_text("n\n")
    (root / ".gitignore").write_text("*.log\n")


def test_walk_plain_folder(tmp_path):
    _make(tmp_path)
    assert list(iter_files(tmp_path, max_bytes=1000)) == [".gitignore", "noise.log", "src/app.py"]


def test_walk_git_repo_honours_gitignore(tmp_path):
    _make(tmp_path)
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    assert list(iter_files(tmp_path, max_bytes=1000)) == [".gitignore", "src/app.py"]
