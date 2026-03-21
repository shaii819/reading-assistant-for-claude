#!/usr/bin/env python3
"""Mechanically verify extracted quotes against source text using fuzzy matching."""

import json
import sys
from difflib import SequenceMatcher


def _best_match_ratio(quote: str, source: str) -> tuple[float, str]:
    if not quote or not source:
        return 0.0, ""
    quote_len = len(quote)
    best_ratio = 0.0
    best_text = ""
    window = int(quote_len * 1.5)
    step = max(1, quote_len // 4)
    for start in range(0, max(1, len(source) - quote_len // 2), step):
        end = min(len(source), start + window)
        candidate = source[start:end]
        ratio = SequenceMatcher(None, quote, candidate).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_text = candidate
            if ratio >= 0.99:
                break
    return best_ratio, best_text


def verify_quotes(quotes: list[dict], chapter_texts: dict[int, str],
                  threshold: float = 0.95) -> list[dict]:
    results = []
    for i, quote in enumerate(quotes):
        source = chapter_texts.get(quote["chapter"], "")
        ratio, best_text = _best_match_ratio(quote["text"], source)
        results.append({
            "quote_index": i,
            "match_ratio": round(ratio, 4),
            "status": "pass" if ratio >= threshold else "fail",
            "best_match_text": best_text[:200],
        })
    return results

if __name__ == "__main__":
    quotes = json.loads(sys.stdin.read())
    chapter_texts = json.loads(open(sys.argv[1]).read()) if len(sys.argv) > 1 else {}
    threshold = float(sys.argv[2]) if len(sys.argv) > 2 else 0.95
    results = verify_quotes(quotes, chapter_texts, threshold)
    print(json.dumps(results, indent=2))
