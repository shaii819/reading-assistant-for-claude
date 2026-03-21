import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from estimate_cost import estimate_cost


def test_estimate_returns_required_fields():
    result = estimate_cost(
        chunk_count=100, avg_chunk_tokens=500,
        models={"summarizer": "sonnet", "extractor": "sonnet", "qc": "opus"},
        num_languages=2,
    )
    assert "chunks" in result
    assert "total_input_tokens" in result
    assert "estimated_output_tokens" in result
    assert "total_cost_usd" in result
    assert "by_stage" in result
    assert result["chunks"] == 100


def test_estimate_costs_are_positive():
    result = estimate_cost(100, 500, {"summarizer": "sonnet", "extractor": "sonnet", "qc": "opus"}, 2)
    assert result["total_cost_usd"] > 0
    for stage in result["by_stage"].values():
        assert stage["cost_usd"] >= 0
