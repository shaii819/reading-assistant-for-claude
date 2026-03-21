#!/usr/bin/env python3
"""Chunk parsed EPUB chapters into overlapping token-bounded segments.

Usage:
    chunk.py <output_dir> [chunk_size] [overlap]

Reads chapters/*.json produced by parse_epub.py, adds a 'chunks' array to
each file, and writes the result back in-place.

Each chunk dict:
    index       — zero-based position within this chapter
    text        — the chunk text
    token_count — number of tokens (cl100k_base)
    start_char  — character offset into chapter text where chunk begins
    end_char    — character offset where chunk ends (exclusive)
"""

import json
import os
import sys
from pathlib import Path

import tiktoken

_ENC = tiktoken.get_encoding("cl100k_base")


# ---------------------------------------------------------------------------
# Token helpers
# ---------------------------------------------------------------------------

def count_tokens(text: str) -> int:
    """Count tokens in *text* using cl100k_base."""
    return len(_ENC.encode(text))


# ---------------------------------------------------------------------------
# Recursive splitter
# ---------------------------------------------------------------------------

def split_text(text: str, max_tokens: int, overlap_frac: float) -> list[dict]:
    """Split *text* into overlapping chunks bounded by *max_tokens*.

    Strategy
    --------
    1. Split on paragraph boundaries (``\\n\\n``).
    2. Accumulate paragraphs until the next would exceed max_tokens.
    3. Flush the current chunk; keep an overlap tail (by token budget) from
       the flushed chunk to seed the next one.
    4. If a single paragraph itself exceeds max_tokens, fall back to
       sentence-level splitting on ``'. '``.

    Returns
    -------
    List of dicts with keys: index, text, token_count, start_char, end_char.
    """
    if not text or not text.strip():
        return []

    overlap_tokens = max(1, int(max_tokens * overlap_frac))

    # Split into paragraphs, keeping track of their char positions.
    paragraphs: list[tuple[str, int]] = []  # (paragraph_text, start_char)
    pos = 0
    for para in text.split("\n\n"):
        paragraphs.append((para, pos))
        pos += len(para) + 2  # +2 for the "\n\n" separator

    # ---------------------------------------------------------------------------
    # Helper: sentence-split a single oversized paragraph
    # ---------------------------------------------------------------------------
    def split_oversized(para: str, para_start: int) -> list[tuple[str, int]]:
        """Break an oversized paragraph into sentence-level pieces."""
        pieces: list[tuple[str, int]] = []
        offset = 0
        for sentence in para.split(". "):
            pieces.append((sentence, para_start + offset))
            offset += len(sentence) + 2  # +2 for '. '
        return pieces

    # Expand any oversized paragraph into sentences before main loop.
    expanded: list[tuple[str, int]] = []
    for para, start in paragraphs:
        if count_tokens(para) > max_tokens:
            expanded.extend(split_oversized(para, start))
        else:
            expanded.append((para, start))

    # ---------------------------------------------------------------------------
    # Main accumulation loop
    # ---------------------------------------------------------------------------
    chunks: list[dict] = []
    current_parts: list[tuple[str, int]] = []  # (text, char_offset_in_chapter)
    current_tokens = 0

    def flush(parts: list[tuple[str, int]]) -> dict:
        """Build a chunk dict from the accumulated parts."""
        chunk_text = "\n\n".join(p[0] for p in parts)
        start_char = parts[0][1]
        end_char = parts[-1][1] + len(parts[-1][0])
        return {
            "index": len(chunks),
            "text": chunk_text,
            "token_count": count_tokens(chunk_text),
            "start_char": start_char,
            "end_char": end_char,
        }

    def build_overlap_tail(parts: list[tuple[str, int]]) -> tuple[list[tuple[str, int]], int]:
        """Return the trailing parts that fit within overlap_tokens budget."""
        tail: list[tuple[str, int]] = []
        tail_tokens = 0
        for p in reversed(parts):
            t = count_tokens(p[0])
            if tail_tokens + t > overlap_tokens:
                break
            tail.insert(0, p)
            tail_tokens += t
        return tail, tail_tokens

    for para, start in expanded:
        para_tokens = count_tokens(para)

        # If adding this paragraph would overflow, flush first.
        if current_parts and (current_tokens + para_tokens > max_tokens):
            chunk = flush(current_parts)
            chunks.append(chunk)

            # Seed next chunk with overlap tail from flushed chunk.
            overlap_parts, overlap_tok = build_overlap_tail(current_parts)
            current_parts = overlap_parts
            current_tokens = overlap_tok

        current_parts.append((para, start))
        current_tokens += para_tokens

    # Flush any remaining content.
    if current_parts:
        chunk = flush(current_parts)
        chunks.append(chunk)

    # Fix up start_char for the very first chunk to be 0 if it starts the text.
    if chunks and chunks[0]["start_char"] == paragraphs[0][1]:
        chunks[0]["start_char"] = 0

    return chunks


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def chunk_chapters(output_dir: str, chunk_size: int = 2000, overlap: float = 0.15) -> None:
    """Add a 'chunks' array to every chapter JSON in *output_dir*/chapters/.

    Parameters
    ----------
    output_dir:  directory produced by parse_epub (contains chapters/)
    chunk_size:  target maximum tokens per chunk
    overlap:     fraction of chunk_size to repeat at the start of each new chunk
    """
    chapters_dir = Path(output_dir) / "chapters"
    if not chapters_dir.exists():
        raise FileNotFoundError(f"chapters/ directory not found in {output_dir}")

    for ch_file in sorted(chapters_dir.glob("*.json")):
        data = json.loads(ch_file.read_text(encoding="utf-8"))

        # Skip empty chapters.
        if data.get("empty") or not data.get("text", "").strip():
            data["chunks"] = []
        else:
            data["chunks"] = split_text(data["text"], chunk_size, overlap)

        ch_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <output_dir> [chunk_size] [overlap]", file=sys.stderr)
        sys.exit(1)

    output_dir = sys.argv[1]
    chunk_size = int(sys.argv[2]) if len(sys.argv) > 2 else 2000
    overlap = float(sys.argv[3]) if len(sys.argv) > 3 else 0.15

    chunk_chapters(output_dir, chunk_size=chunk_size, overlap=overlap)
    print(f"Chunked chapters in {output_dir}/chapters/")
