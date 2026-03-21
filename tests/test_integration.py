"""End-to-end integration test using the sample EPUB fixture.

Tests the script layer only (not agent orchestration).
Verifies: parse → chunk → outputs exist and match schemas.
"""
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from parse_epub import parse_epub
from chunk import chunk_chapters

FIXTURES = Path(__file__).parent / "fixtures"


def test_full_script_pipeline(tmp_path):
    """Parse → chunk produces valid intermediate artifacts."""
    # Phase 1a: parse
    meta = parse_epub(str(FIXTURES / "sample.epub"), str(tmp_path))
    assert meta["title"] == "The Art of Testing"
    assert meta["chapter_count"] == 5
    assert meta["language"] == "en"
    assert meta["slug"] == "the-art-of-testing"
    assert meta["genre"] == "non-fiction"

    # Phase 1b: chunk
    chunk_chapters(str(tmp_path), chunk_size=500, overlap=0.15)

    # Verify all chapters have chunks
    for ch in meta["chapters"]:
        ch_path = tmp_path / "chapters" / f"{ch['slug']}.json"
        assert ch_path.exists(), f"Missing chapter file: {ch['slug']}.json"
        ch_data = json.loads(ch_path.read_text())
        assert "chunks" in ch_data
        if not ch_data["empty"]:
            assert len(ch_data["chunks"]) > 0
            for chunk in ch_data["chunks"]:
                assert chunk["token_count"] > 0
                assert chunk["start_char"] >= 0
                assert chunk["end_char"] > chunk["start_char"]
                assert len(chunk["text"]) > 0

    # Verify metadata schema
    meta_data = json.loads((tmp_path / "metadata.json").read_text())
    required_fields = ["title", "author", "language", "genre", "total_word_count",
                       "chapter_count", "chapters", "slug"]
    for field in required_fields:
        assert field in meta_data, f"Missing metadata field: {field}"

    # Verify chapter count matches
    chapter_files = list((tmp_path / "chapters").glob("*.json"))
    assert len(chapter_files) == meta_data["chapter_count"]

    # Verify pipeline-ready state
    assert (tmp_path / "metadata.json").exists()
    assert (tmp_path / "chapters").is_dir()


def test_obsidian_generation_from_parsed_data(tmp_path):
    """Parse → chunk → mock summaries/extractions → generate obsidian notes."""
    from write_obsidian import generate_obsidian_notes

    # Parse and chunk
    meta = parse_epub(str(FIXTURES / "sample.epub"), str(tmp_path))
    chunk_chapters(str(tmp_path), chunk_size=500, overlap=0.15)

    # Create mock summaries
    for lang in ["en"]:
        sum_dir = tmp_path / "summaries" / lang
        sum_dir.mkdir(parents=True)
        for ch in meta["chapters"]:
            (sum_dir / f"{ch['slug']}.md").write_text(f"# {ch['title']}\nSummary of {ch['title']}.")
        (sum_dir / "book-summary.md").write_text("# Book Summary\nOverall summary of the book.")

    # Create mock extractions
    ext_dir = tmp_path / "extractions"
    ext_dir.mkdir()
    (ext_dir / "facts.json").write_text(json.dumps([
        {"category": "fact", "text": "70% of bugs are at boundaries", "chapter": 0,
         "page_estimate": 1, "context": "...", "confidence": "high"}
    ]))
    (ext_dir / "quotes.json").write_text(json.dumps([
        {"category": "quote", "text": "Testing shows the presence, not the absence, of bugs.",
         "chapter": 0, "page_estimate": 1, "speaker": "Dijkstra", "context": "...", "verified": True}
    ]))
    (ext_dir / "examples.json").write_text("[]")
    (ext_dir / "metaphors.json").write_text("[]")
    (ext_dir / "glossary.json").write_text(json.dumps([
        {"category": "glossary", "term": "Unit Test", "definition": "Test of individual component",
         "chapter_first_seen": 0, "related_terms": []}
    ]))

    # Generate obsidian notes
    obsidian_dir = str(tmp_path / "obsidian")
    generate_obsidian_notes(str(tmp_path), obsidian_dir)

    # Verify structure
    obs_path = Path(obsidian_dir)
    assert (obs_path / f"MOC-{meta['slug']}.md").exists()
    assert (obs_path / "chapters").is_dir()
    assert (obs_path / "quotes").is_dir()
    assert (obs_path / "concepts").is_dir()

    # Verify MOC has wikilinks
    moc_content = (obs_path / f"MOC-{meta['slug']}.md").read_text()
    assert "[[" in moc_content
    assert "type: moc" in moc_content


def test_cost_estimation_from_chunks(tmp_path):
    """Parse → chunk → estimate cost."""
    from estimate_cost import estimate_cost

    meta = parse_epub(str(FIXTURES / "sample.epub"), str(tmp_path))
    chunk_chapters(str(tmp_path), chunk_size=500, overlap=0.15)

    # Count total chunks and average token size
    total_chunks = 0
    total_tokens = 0
    for ch in meta["chapters"]:
        ch_path = tmp_path / "chapters" / f"{ch['slug']}.json"
        ch_data = json.loads(ch_path.read_text())
        for chunk in ch_data.get("chunks", []):
            total_chunks += 1
            total_tokens += chunk["token_count"]

    avg_tokens = total_tokens // total_chunks if total_chunks > 0 else 0

    result = estimate_cost(total_chunks, avg_tokens,
                          {"summarizer": "sonnet", "extractor": "sonnet", "qc": "opus"}, 2)
    assert result["chunks"] == total_chunks
    assert result["total_cost_usd"] > 0
    assert "summarize" in result["by_stage"]
