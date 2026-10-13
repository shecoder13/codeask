from codeask.chunker import chunk_file, chunk_text


def test_small_file_is_one_chunk():
    assert chunk_text("a\nb\nc\n") == [(1, 3, "a\nb\nc")]


def test_empty_and_blank():
    assert chunk_text("") == []
    assert chunk_text("\n\n  \n") == []


def test_chunks_are_bounded_numbered_and_cover_every_line():
    lines = [f"line {n} " + "x" * 30 for n in range(1, 301)]
    chunks = chunk_text("\n".join(lines), max_chars=500, overlap=3)
    assert len(chunks) > 1
    covered = set()
    for start, end, body in chunks:
        assert len(body) <= 500
        assert body == "\n".join(lines[start - 1:end])
        covered.update(range(start, end + 1))
    assert covered == set(range(1, 301))


def test_prefers_blank_line_boundary():
    block = ["def f():"] + ["    x = 1"] * 20 + [""]
    chunks = chunk_text("\n".join(block * 3), max_chars=450, overlap=0)
    assert chunks[0][1] == 44  # two whole blocks, not cut mid-function at line 47


def test_overlong_line_is_truncated_not_looped():
    chunks = chunk_text("y" * 10_000, max_chars=100)
    assert len(chunks) == 1 and len(chunks[0][2]) == 100


def test_chunk_file(tmp_path):
    (tmp_path / "a.py").write_text("print(1)\nprint(2)\n")
    (c,) = chunk_file(tmp_path, "a.py")
    assert (c.path, c.start, c.end) == ("a.py", 1, 2)
