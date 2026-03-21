#!/usr/bin/env python3
"""Estimate token usage and cost for the AI pipeline phases."""

import json
import sys

PRICING = {
    "haiku":  {"input": 0.25, "output": 1.25},
    "sonnet": {"input": 3.00, "output": 15.00},
    "opus":   {"input": 15.00, "output": 75.00},
    "ollama": {"input": 0.00, "output": 0.00},
    "openai:gpt-4o": {"input": 2.50, "output": 10.00},
}


def _get_pricing(model: str) -> dict:
    if model in PRICING:
        return PRICING[model]
    if model.startswith("ollama:"):
        return PRICING["ollama"]
    if model.startswith("openai:"):
        return PRICING.get(model, PRICING["openai:gpt-4o"])
    return PRICING.get("sonnet")


def estimate_cost(chunk_count: int, avg_chunk_tokens: int,
                  models: dict, num_languages: int = 1) -> dict:
    total_input = chunk_count * avg_chunk_tokens
    sum_out = int(total_input * 0.5 * num_languages)
    ext_out = int(total_input * 0.5)
    rev_in, rev_out = 5000, 3000
    qc_in = total_input + sum_out + ext_out
    qc_out = int(qc_in * 0.25)

    stages = {
        "summarize": {"input": total_input, "output": sum_out, "model": models.get("summarizer", "sonnet")},
        "extract": {"input": total_input, "output": ext_out, "model": models.get("extractor", "sonnet")},
        "synthesize_reviews": {"input": rev_in, "output": rev_out, "model": models.get("reviewer", "sonnet")},
        "qc": {"input": qc_in, "output": qc_out, "model": models.get("qc", "opus")},
    }

    total_cost = 0.0
    for stage in stages.values():
        p = _get_pricing(stage["model"])
        cost = (stage["input"] * p["input"] + stage["output"] * p["output"]) / 1_000_000
        stage["cost_usd"] = round(cost, 2)
        total_cost += cost

    total_output = sum(s["output"] for s in stages.values())
    return {
        "chunks": chunk_count,
        "total_input_tokens": total_input,
        "estimated_output_tokens": total_output,
        "by_stage": stages,
        "total_cost_usd": round(total_cost, 2),
    }

if __name__ == "__main__":
    result = estimate_cost(int(sys.argv[1]), int(sys.argv[2]),
                           json.loads(sys.argv[3]), int(sys.argv[4]) if len(sys.argv) > 4 else 1)
    print(json.dumps(result, indent=2))
