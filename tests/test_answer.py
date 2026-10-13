from codeask import answer as ans
from codeask.chunker import Chunk


def test_prompt_contains_headers_text_and_question():
    p = ans.build_prompt("where is login?", [Chunk("auth.py", 10, 20, "def login(): ...")])
    assert "### auth.py:10-20" in p and "def login()" in p and p.endswith("Question: where is login?")


def test_answer_passes_prompt_to_llm_and_returns_sources(monkeypatch):
    chunk = Chunk("a.py", 1, 2, "x = 1")
    monkeypatch.setattr(ans, "search", lambda db, qv, q: [chunk])
    seen = {}

    def gen(system, user):
        seen["system"], seen["user"] = system, user
        return "It is x [a.py:1-2]"

    text, sources = ans.answer(None, "what is x?", embed=lambda q: [0.0], gen=gen)
    assert text.startswith("It is x") and sources == [chunk]
    assert "ONLY the excerpts" in seen["system"] and "a.py:1-2" in seen["user"]


def test_no_chunks_means_not_found_without_calling_llm(monkeypatch):
    monkeypatch.setattr(ans, "search", lambda db, qv, q: [])
    text, sources = ans.answer(None, "q", embed=lambda q: [0.0], gen=lambda s, u: 1 / 0)
    assert text == "Not found in this repo." and sources == []
