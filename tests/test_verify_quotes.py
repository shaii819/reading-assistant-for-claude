from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from verify_quotes import verify_quotes


def test_exact_match_passes():
    source = "The quick brown fox jumps over the lazy dog."
    quotes = [{"text": "The quick brown fox jumps over the lazy dog.", "chapter": 0}]
    results = verify_quotes(quotes, {0: source}, threshold=0.95)
    assert results[0]["status"] == "pass"
    assert results[0]["match_ratio"] >= 0.95


def test_near_match_passes():
    source = "The quick brown fox jumps over the lazy dog."
    quotes = [{"text": "The quick brown fox jumps over the lazy dogs.", "chapter": 0}]
    results = verify_quotes(quotes, {0: source}, threshold=0.90)
    assert results[0]["status"] == "pass"


def test_no_match_fails():
    source = "Completely different text about something else entirely."
    quotes = [{"text": "The quick brown fox jumps over the lazy dog.", "chapter": 0}]
    results = verify_quotes(quotes, {0: source}, threshold=0.95)
    assert results[0]["status"] == "fail"
    assert results[0]["match_ratio"] < 0.5


def test_threshold_boundary():
    source = "Testing is important for quality."
    quotes = [{"text": "Testing is important for quality!", "chapter": 0}]
    results = verify_quotes(quotes, {0: source}, threshold=0.99)
    assert "status" in results[0]
    assert "match_ratio" in results[0]
