#!/usr/bin/env python3
"""Provider abstraction for text generation and embeddings across Claude/Ollama/OpenAI."""

import json
import os
import sys

import httpx

CLAUDE_MODELS = {"haiku", "sonnet", "opus"}
CLAUDE_SENTINEL = "__CLAUDE_NATIVE__"


def parse_model_spec(spec: str) -> tuple[str, str]:
    """Parse model spec into (provider, model_name).

    Examples:
        "sonnet" → ("claude", "sonnet")
        "ollama:mistral" → ("ollama", "mistral")
        "openai:gpt-4o" → ("openai", "gpt-4o")
    """
    if spec in CLAUDE_MODELS:
        return "claude", spec
    if ":" in spec:
        provider, model = spec.split(":", 1)
        return provider, model
    return "claude", spec


def generate(prompt: str, model_spec: str, system: str = "",
             temperature: float = 0.3, max_tokens: int = 4096,
             json_mode: bool = False) -> str:
    """Generate text using the specified model.

    For Claude models, returns CLAUDE_SENTINEL — the agent handles generation natively.
    For external models, makes HTTP calls and returns the generated text.
    """
    provider, model = parse_model_spec(model_spec)

    if provider == "claude":
        return CLAUDE_SENTINEL

    if provider == "ollama":
        resp = httpx.post("http://localhost:11434/api/generate",
                          json={"model": model, "prompt": prompt, "system": system,
                                "stream": False,
                                "options": {"temperature": temperature, "num_predict": max_tokens}},
                          timeout=120)
        resp.raise_for_status()
        return resp.json()["response"]

    if provider == "openai":
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable required for OpenAI models")
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        body = {"model": model, "messages": messages,
                "temperature": temperature, "max_tokens": max_tokens}
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        resp = httpx.post("https://api.openai.com/v1/chat/completions",
                          json=body,
                          headers={"Authorization": f"Bearer {api_key}"},
                          timeout=120)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    raise ValueError(f"Unknown generation provider: {provider}")


def embed(texts: list[str], provider: str) -> list[list[float]]:
    """Generate embeddings for a batch of texts.

    Args:
        texts: list of strings to embed
        provider: "openai" or "ollama"

    Returns:
        list of embedding vectors (list of floats)
    """
    if provider == "ollama":
        resp = httpx.post("http://localhost:11434/api/embed",
                          json={"model": "nomic-embed-text", "input": texts},
                          timeout=120)
        resp.raise_for_status()
        return resp.json()["embeddings"]

    if provider == "openai":
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable required for OpenAI embeddings")
        resp = httpx.post("https://api.openai.com/v1/embeddings",
                          json={"model": "text-embedding-3-small", "input": texts},
                          headers={"Authorization": f"Bearer {api_key}"},
                          timeout=120)
        resp.raise_for_status()
        return [item["embedding"] for item in resp.json()["data"]]

    raise ValueError(f"Unknown embedding provider: {provider}")


if __name__ == "__main__":
    action = sys.argv[1]  # "generate" or "embed"
    if action == "generate":
        model_spec = sys.argv[2]
        prompt = sys.stdin.read()
        result = generate(prompt, model_spec)
        print(result)
    elif action == "embed":
        provider = sys.argv[2]
        texts = json.loads(sys.stdin.read())
        embeddings = embed(texts, provider)
        print(json.dumps(embeddings))
