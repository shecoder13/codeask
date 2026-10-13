import sys
import types

import pytest

from codeask import llm


def test_uses_claude_when_key_is_set(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    monkeypatch.setattr(llm, "_anthropic", lambda s, u, m: "from claude")
    monkeypatch.setattr(llm, "_ollama", lambda s, u, m: "from ollama")
    assert llm.generate("sys", "hi") == "from claude"


def test_falls_back_to_ollama_without_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY")
    monkeypatch.setattr(llm, "_anthropic", lambda s, u, m: "from claude")
    monkeypatch.setattr(llm, "_ollama", lambda s, u, m: "from ollama")
    assert llm.generate("sys", "hi") == "from ollama"


def _fake_httpx(post):
    fake = types.ModuleType("httpx")
    fake.HTTPError = type("HTTPError", (Exception,), {})
    fake.post = post
    return fake


def test_ollama_request_and_response(monkeypatch):
    seen = {}

    class Resp:
        def raise_for_status(self): pass
        def json(self): return {"message": {"content": "answer"}}

    def post(url, json, timeout):
        seen.update(url=url, body=json)
        return Resp()

    monkeypatch.setitem(sys.modules, "httpx", _fake_httpx(post))
    assert llm._ollama("be brief", "question", 50) == "answer"
    assert seen["url"].endswith("/api/chat")
    assert seen["body"]["stream"] is False
    assert [m["role"] for m in seen["body"]["messages"]] == ["system", "user"]


def test_ollama_failure_gives_actionable_error(monkeypatch):
    fake = _fake_httpx(None)

    def post(url, json, timeout):
        raise fake.HTTPError("connection refused")

    fake.post = post
    monkeypatch.setitem(sys.modules, "httpx", fake)
    with pytest.raises(RuntimeError):
        llm._ollama("s", "u", 10)
