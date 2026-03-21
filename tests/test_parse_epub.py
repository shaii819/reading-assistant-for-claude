import json
import os
from pathlib import Path

import pytest

# Add scripts to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from parse_epub import parse_epub

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_produces_metadata(tmp_path):
    parse_epub(str(FIXTURES / "sample.epub"), str(tmp_path))
    meta_path = tmp_path / "metadata.json"
    assert meta_path.exists()
    meta = json.loads(meta_path.read_text())
    assert meta["title"] == "The Art of Testing"
    assert meta["author"] == "Test Author"
    assert meta["language"] == "en"
    assert meta["genre"] == "non-fiction"
    assert meta["chapter_count"] == 5
    assert len(meta["chapters"]) == 5
    assert meta["slug"] == "the-art-of-testing"
    assert meta["total_word_count"] > 0


def test_parse_produces_chapter_files(tmp_path):
    parse_epub(str(FIXTURES / "sample.epub"), str(tmp_path))
    chapters_dir = tmp_path / "chapters"
    assert chapters_dir.exists()
    files = sorted(chapters_dir.glob("*.json"))
    assert len(files) == 5
    ch1 = json.loads(files[0].read_text())
    assert ch1["index"] == 0
    assert ch1["title"] == "Introduction"
    assert len(ch1["text"]) > 100
    assert ch1["word_count"] > 0
    assert ch1["empty"] is False
    assert "chunks" not in ch1


def test_parse_detects_language(tmp_path):
    parse_epub(str(FIXTURES / "sample.epub"), str(tmp_path))
    meta = json.loads((tmp_path / "metadata.json").read_text())
    assert meta["language"] == "en"


def test_parse_generates_slug(tmp_path):
    parse_epub(str(FIXTURES / "sample.epub"), str(tmp_path))
    meta = json.loads((tmp_path / "metadata.json").read_text())
    assert meta["slug"] == "the-art-of-testing"
    assert meta["chapters"][0]["slug"].startswith("01-")


def test_parse_nonexistent_file(tmp_path):
    with pytest.raises(Exception):
        parse_epub("/nonexistent/book.epub", str(tmp_path))


def test_parse_invalid_file(tmp_path):
    fake = tmp_path / "fake.epub"
    fake.write_text("not an epub")
    with pytest.raises(Exception):
        parse_epub(str(fake), str(tmp_path / "out"))


def test_parse_empty_chapter_marked(tmp_path):
    parse_epub(str(FIXTURES / "sample.epub"), str(tmp_path))
    meta = json.loads((tmp_path / "metadata.json").read_text())
    for ch in meta["chapters"]:
        assert ch["empty"] is False
