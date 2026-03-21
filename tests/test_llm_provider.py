import sys
from pathlib import Path

import httpx
import pytest
import respx

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from llm_provider import generate, embed, parse_model_spec


def test_parse_model_spec_claude():
    provider, model = parse_model_spec("sonnet")
    assert provider == "claude"
    assert model == "sonnet"


def test_parse_model_spec_claude_variants():
    for name in ["haiku", "opus", "sonnet"]:
        provider, model = parse_model_spec(name)
        assert provider == "claude"
        assert model == name


def test_parse_model_spec_ollama():
    provider, model = parse_model_spec("ollama:mistral")
    assert provider == "ollama"
    assert model == "mistral"


def test_parse_model_spec_openai():
    provider, model = parse_model_spec("openai:gpt-4o")
    assert provider == "openai"
    assert model == "gpt-4o"


@respx.mock
def test_generate_ollama():
    respx.post("http://localhost:11434/api/generate").mock(
        return_value=httpx.Response(200, json={"response": "test output"})
    )
    result = generate("test prompt", "ollama:mistral")
    assert result == "test output"


def test_generate_claude_returns_sentinel():
    """Claude models should return a sentinel indicating 'use agent context'."""
    result = generate("test prompt", "sonnet")
    assert result == "__CLAUDE_NATIVE__"


@respx.mock
def test_generate_openai(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json={
            "choices": [{"message": {"content": "openai output"}}]
        })
    )
    result = generate("test prompt", "openai:gpt-4o")
    assert result == "openai output"


@respx.mock
def test_embed_ollama():
    respx.post("http://localhost:11434/api/embed").mock(
        return_value=httpx.Response(200, json={"embeddings": [[0.1, 0.2, 0.3]]})
    )
    result = embed(["test text"], "ollama")
    assert len(result) == 1
    assert len(result[0]) == 3


@respx.mock
def test_embed_openai(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    respx.post("https://api.openai.com/v1/embeddings").mock(
        return_value=httpx.Response(200, json={
            "data": [{"embedding": [0.1] * 1536}]
        })
    )
    result = embed(["test text"], "openai")
    assert len(result) == 1
    assert len(result[0]) == 1536


def test_embed_unknown_provider():
    with pytest.raises(ValueError, match="Unknown embedding provider"):
        embed(["test"], "unknown_provider")
