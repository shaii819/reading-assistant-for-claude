import json
import sqlite3
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from rag_index import create_db, index_chunks, query_db, get_db_meta


def test_create_db_has_required_tables(tmp_path):
    db_path = str(tmp_path / "test.db")
    create_db(db_path, provider="ollama", dims=768)
    conn = sqlite3.connect(db_path)
    tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()]
    assert "_meta" in tables
    assert "chunks" in tables
    conn.close()


def test_db_meta_records_provider(tmp_path):
    db_path = str(tmp_path / "test.db")
    create_db(db_path, provider="openai", dims=1536)
    meta = get_db_meta(db_path)
    assert meta["embedding_provider"] == "openai"
    assert meta["embedding_dims"] == "1536"


def test_provider_mismatch_errors(tmp_path):
    db_path = str(tmp_path / "test.db")
    create_db(db_path, provider="openai", dims=1536)
    with pytest.raises(ValueError, match="provider"):
        index_chunks(db_path, [], provider="ollama", dims=768, embed_fn=lambda x: [[0.1]*768])


def test_upsert_replaces_book(tmp_path):
    db_path = str(tmp_path / "test.db")
    dims = 3
    create_db(db_path, provider="test", dims=dims)
    chunks1 = [{"book_id": "book1", "chapter": 0, "chunk_index": 0, "text": "hello", "category": None}]
    chunks2 = [{"book_id": "book1", "chapter": 0, "chunk_index": 0, "text": "world", "category": None}]
    fake_embed = lambda texts: [[0.1] * dims for _ in texts]

    index_chunks(db_path, chunks1, provider="test", dims=dims, embed_fn=fake_embed)
    index_chunks(db_path, chunks2, provider="test", dims=dims, embed_fn=fake_embed)

    conn = sqlite3.connect(db_path)
    count = conn.execute("SELECT COUNT(*) FROM chunks WHERE book_id='book1'").fetchone()[0]
    assert count == 1
    text = conn.execute("SELECT text FROM chunks WHERE book_id='book1'").fetchone()[0]
    assert text == "world"
    conn.close()


def test_fts_query(tmp_path):
    db_path = str(tmp_path / "test.db")
    dims = 3
    create_db(db_path, provider="test", dims=dims)
    chunks = [
        {"book_id": "book1", "chapter": 0, "chunk_index": 0, "text": "machine learning is transformative", "category": None},
        {"book_id": "book1", "chapter": 1, "chunk_index": 0, "text": "cooking recipes for beginners", "category": None},
    ]
    fake_embed = lambda texts: [[0.1] * dims for _ in texts]
    index_chunks(db_path, chunks, provider="test", dims=dims, embed_fn=fake_embed)

    results = query_db(db_path, "machine learning", embed_fn=fake_embed, top_k=5)
    assert len(results) > 0
    assert "machine learning" in results[0]["text"].lower()


def test_wal_mode(tmp_path):
    db_path = str(tmp_path / "test.db")
    create_db(db_path, provider="test", dims=3)
    conn = sqlite3.connect(db_path)
    mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
    assert mode == "wal"
    conn.close()
