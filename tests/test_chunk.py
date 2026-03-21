import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from chunk import chunk_chapters

FIXTURES = Path(__file__).parent / "fixtures"


def test_chunk_adds_chunks_array(tmp_path):
    """After chunking, each chapter JSON should have a 'chunks' array."""
    from parse_epub import parse_epub
    parse_epub(str(FIXTURES / "sample.epub"), str(tmp_path))
    chunk_chapters(str(tmp_path), chunk_size=500, overlap=0.15)

    chapters_dir = tmp_path / "chapters"
    for ch_file in sorted(chapters_dir.glob("*.json")):
        data = json.loads(ch_file.read_text())
        assert "chunks" in data
        assert len(data["chunks"]) > 0


def test_chunk_respects_size_limit(tmp_path):
    from parse_epub import parse_epub
    parse_epub(str(FIXTURES / "sample.epub"), str(tmp_path))
    chunk_chapters(str(tmp_path), chunk_size=200, overlap=0.1)

    chapters_dir = tmp_path / "chapters"
    for ch_file in sorted(chapters_dir.glob("*.json")):
        data = json.loads(ch_file.read_text())
        for chunk in data["chunks"]:
            # Allow 20% overflow for boundary splits
            assert chunk["token_count"] <= 200 * 1.2


def test_chunk_has_required_fields(tmp_path):
    from parse_epub import parse_epub
    parse_epub(str(FIXTURES / "sample.epub"), str(tmp_path))
    chunk_chapters(str(tmp_path), chunk_size=500, overlap=0.15)

    ch_file = sorted((tmp_path / "chapters").glob("*.json"))[0]
    data = json.loads(ch_file.read_text())
    chunk = data["chunks"][0]
    assert "index" in chunk
    assert "text" in chunk
    assert "token_count" in chunk
    assert "start_char" in chunk
    assert "end_char" in chunk
    assert chunk["index"] == 0
    assert chunk["start_char"] == 0


def test_chunk_skips_empty_chapters(tmp_path):
    """Empty chapters should get an empty chunks array."""
    from parse_epub import parse_epub
    parse_epub(str(FIXTURES / "sample.epub"), str(tmp_path))

    # Manually make a chapter empty
    ch_dir = tmp_path / "chapters"
    ch_files = sorted(ch_dir.glob("*.json"))
    ch_data = json.loads(ch_files[0].read_text())
    ch_data["empty"] = True
    ch_data["text"] = ""
    ch_files[0].write_text(json.dumps(ch_data))

    chunk_chapters(str(tmp_path), chunk_size=500, overlap=0.15)

    result = json.loads(ch_files[0].read_text())
    assert result["chunks"] == []
