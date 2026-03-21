import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from write_obsidian import generate_obsidian_notes


def test_generates_moc(tmp_path):
    _setup_outputs(tmp_path)
    generate_obsidian_notes(str(tmp_path), str(tmp_path / "obsidian"))
    moc = tmp_path / "obsidian" / "MOC-test-book.md"
    assert moc.exists()
    content = moc.read_text()
    assert "type: moc" in content
    assert "[[test-book-ch01" in content


def test_generates_chapter_notes(tmp_path):
    _setup_outputs(tmp_path)
    generate_obsidian_notes(str(tmp_path), str(tmp_path / "obsidian"))
    chapters = list((tmp_path / "obsidian" / "chapters").glob("*.md"))
    assert len(chapters) > 0
    content = chapters[0].read_text()
    assert "type: chapter" in content


def test_generates_quote_notes(tmp_path):
    _setup_outputs(tmp_path)
    generate_obsidian_notes(str(tmp_path), str(tmp_path / "obsidian"))
    quotes = list((tmp_path / "obsidian" / "quotes").glob("*.md"))
    assert len(quotes) > 0
    content = quotes[0].read_text()
    assert "type: quote" in content
    assert "verified:" in content


def test_generates_concept_notes(tmp_path):
    _setup_outputs(tmp_path)
    generate_obsidian_notes(str(tmp_path), str(tmp_path / "obsidian"))
    assert (tmp_path / "obsidian" / "concepts").exists()


def test_vault_copy(tmp_path):
    _setup_outputs(tmp_path)
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "test-book").mkdir()
    (vault / "test-book" / "my-notes.md").write_text("user notes")
    generate_obsidian_notes(str(tmp_path), str(tmp_path / "obsidian"), vault_path=str(vault))
    assert (vault / "test-book" / "MOC-test-book.md").exists()
    assert (vault / "test-book" / "my-notes.md").read_text() == "user notes"


def _setup_outputs(tmp_path):
    """Create minimal output structure for obsidian generation."""
    meta = {
        "title": "Test Book", "author": "Author", "slug": "test-book",
        "isbn": None, "language": "en", "genre": "non-fiction",
        "chapters": [{"index": 0, "title": "Intro", "slug": "01-intro", "word_count": 500, "empty": False}],
        "chapter_count": 1, "total_word_count": 500,
    }
    (tmp_path / "metadata.json").write_text(json.dumps(meta))

    summaries = tmp_path / "summaries" / "en"
    summaries.mkdir(parents=True)
    (summaries / "01-intro.md").write_text("# Intro\nSummary of intro chapter.")
    (summaries / "book-summary.md").write_text("# Book Summary\nOverall summary.")

    extractions = tmp_path / "extractions"
    extractions.mkdir()
    (extractions / "quotes.json").write_text(json.dumps([
        {"category": "quote", "text": "Testing is key.", "chapter": 0,
         "page_estimate": 1, "speaker": "Author", "context": "...", "verified": True}
    ]))
    (extractions / "facts.json").write_text(json.dumps([
        {"category": "fact", "text": "70% of bugs are at boundaries.", "chapter": 0,
         "page_estimate": 2, "context": "...", "confidence": "high"}
    ]))
    (extractions / "examples.json").write_text(json.dumps([]))
    (extractions / "metaphors.json").write_text(json.dumps([]))
    (extractions / "glossary.json").write_text(json.dumps([
        {"category": "glossary", "term": "Unit Test", "definition": "A test of an individual component",
         "chapter_first_seen": 0, "related_terms": ["integration test"]}
    ]))
