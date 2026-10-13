import pytest

from codeask.source import resolve_source


def test_local_folder(tmp_path):
    folder, commit = resolve_source(str(tmp_path))
    assert folder == tmp_path.resolve()
    assert commit is None


@pytest.mark.parametrize("text", ["", "flask", "http://github.com/a/b", "https://gitlab.com/a/b",
                                  "https://github.com/a", "https://github.com/../b",
                                  "https://github.com/a/b/tree/main"])
def test_rejects_bad_input(text):
    with pytest.raises(ValueError):
        resolve_source(text)
