#!/usr/bin/env python3
"""SQLite RAG indexer with optional sqlite-vec vector search.

Creates and queries a SQLite database with:
  - _meta: embedding provider pinning
  - chunks: text + metadata
  - chunks_fts: FTS5 full-text search index
  - chunks_vec: sqlite-vec vector table (optional, skipped if extension unavailable)

Usage:
  python rag_index.py create <db_path> <provider> <dims>
  python rag_index.py index <db_path> <chunks_json_path>
  python rag_index.py query <db_path> <query_text>
"""

import json
import logging
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Database creation
# ---------------------------------------------------------------------------

def create_db(db_path: str, provider: str, dims: int) -> None:
    """Create a new RAG database with required tables.

    Sets up:
      - WAL journal mode for concurrent access
      - _meta table for provider pinning
      - chunks table for text + metadata storage
      - chunks_fts FTS5 virtual table for full-text search
      - chunks_vec vec0 virtual table for vector search (if sqlite-vec available)

    Args:
        db_path: Path to SQLite database file
        provider: Embedding provider name (e.g. "openai", "ollama")
        dims: Embedding vector dimensions
    """
    conn = sqlite3.connect(db_path)
    try:
        # WAL mode for better concurrent performance
        conn.execute("PRAGMA journal_mode=WAL")

        # Metadata table: provider pinning
        conn.execute("""
            CREATE TABLE IF NOT EXISTS _meta (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        # Store provider info
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT OR REPLACE INTO _meta (key, value) VALUES ('embedding_provider', ?)",
            (provider,),
        )
        conn.execute(
            "INSERT OR REPLACE INTO _meta (key, value) VALUES ('embedding_dims', ?)",
            (str(dims),),
        )
        conn.execute(
            "INSERT OR REPLACE INTO _meta (key, value) VALUES ('created_at', ?)",
            (now,),
        )

        # Chunks table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id       TEXT NOT NULL,
                chapter       INTEGER,
                chunk_index   INTEGER,
                text          TEXT NOT NULL,
                category      TEXT,
                metadata_json TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_book_id ON chunks (book_id)")

        # FTS5 table for full-text search
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts
            USING fts5(text, book_id UNINDEXED, chapter UNINDEXED, chunk_index UNINDEXED, content='chunks', content_rowid='id')
        """)

        # Try to create sqlite-vec vector table (optional)
        _try_create_vec_table(conn, dims)

        conn.commit()
    finally:
        conn.close()


def _try_create_vec_table(conn: sqlite3.Connection, dims: int) -> bool:
    """Try to load sqlite-vec and create the chunks_vec table.

    Returns True if successful, False if sqlite-vec is not available.
    """
    try:
        conn.enable_load_extension(True)
        conn.load_extension("vec0")
        conn.execute(f"""
            CREATE VIRTUAL TABLE IF NOT EXISTS chunks_vec
            USING vec0(
                chunk_id INTEGER PRIMARY KEY,
                embedding float[{dims}]
            )
        """)
        conn.execute("INSERT OR REPLACE INTO _meta (key, value) VALUES ('vec_available', 'true')")
        logger.info("sqlite-vec loaded successfully, vector search enabled")
        return True
    except Exception as e:
        logger.warning(f"sqlite-vec not available, vector search disabled: {e}")
        conn.execute("INSERT OR REPLACE INTO _meta (key, value) VALUES ('vec_available', 'false')")
        return False


# ---------------------------------------------------------------------------
# Metadata access
# ---------------------------------------------------------------------------

def get_db_meta(db_path: str) -> dict:
    """Read _meta table as a dictionary.

    Args:
        db_path: Path to SQLite database file

    Returns:
        dict of all key/value pairs in _meta table
    """
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute("SELECT key, value FROM _meta").fetchall()
        return {row[0]: row[1] for row in rows}
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Indexing
# ---------------------------------------------------------------------------

def index_chunks(
    db_path: str,
    chunks: list[dict],
    provider: str,
    dims: int,
    embed_fn: Callable[[list[str]], list[list[float]]],
) -> int:
    """Index chunks into the database.

    Validates that the provider matches the database's pinned provider.
    Deletes existing rows for any book_id found in the new chunks (upsert by book).
    Inserts new chunks and their embeddings.

    Args:
        db_path: Path to SQLite database file
        chunks: List of dicts with keys: book_id, chapter, chunk_index, text, category
        provider: Embedding provider name (must match database's pinned provider)
        dims: Embedding vector dimensions
        embed_fn: Callable that takes list of texts and returns list of embeddings

    Returns:
        Number of chunks indexed

    Raises:
        ValueError: If provider does not match the database's pinned provider
    """
    # Validate provider
    meta = get_db_meta(db_path)
    db_provider = meta.get("embedding_provider", "")
    if db_provider != provider:
        raise ValueError(
            f"provider mismatch: database uses '{db_provider}', got '{provider}'"
        )

    if not chunks:
        return 0

    conn = sqlite3.connect(db_path)
    try:
        # Find all book_ids in new chunks
        book_ids = list({c["book_id"] for c in chunks})

        # Delete existing data for these books (upsert by book)
        for book_id in book_ids:
            # Get row ids to delete from FTS
            rows = conn.execute(
                "SELECT id FROM chunks WHERE book_id = ?", (book_id,)
            ).fetchall()
            row_ids = [r[0] for r in rows]

            # Delete from FTS first (content table sync)
            for row_id in row_ids:
                conn.execute(
                    "INSERT INTO chunks_fts(chunks_fts, rowid, text) VALUES('delete', ?, ?)",
                    (row_id, conn.execute("SELECT text FROM chunks WHERE id=?", (row_id,)).fetchone()[0]),
                )

            # Delete from vec table if available
            if meta.get("vec_available") == "true" and row_ids:
                placeholders = ",".join("?" * len(row_ids))
                conn.execute(
                    f"DELETE FROM chunks_vec WHERE chunk_id IN ({placeholders})",
                    row_ids,
                )

            # Delete from chunks table
            conn.execute("DELETE FROM chunks WHERE book_id = ?", (book_id,))

        # Insert new chunks
        texts = [c["text"] for c in chunks]
        embeddings = embed_fn(texts)

        new_ids = []
        for chunk, embedding in zip(chunks, embeddings):
            cur = conn.execute(
                """
                INSERT INTO chunks (book_id, chapter, chunk_index, text, category, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    chunk["book_id"],
                    chunk.get("chapter"),
                    chunk.get("chunk_index"),
                    chunk["text"],
                    chunk.get("category"),
                    json.dumps(chunk.get("metadata", {})),
                ),
            )
            new_id = cur.lastrowid
            new_ids.append((new_id, chunk, embedding))

        # Insert into FTS
        for new_id, chunk, _ in new_ids:
            conn.execute(
                "INSERT INTO chunks_fts(rowid, text) VALUES(?, ?)",
                (new_id, chunk["text"]),
            )

        # Insert into vec table if available
        if meta.get("vec_available") == "true":
            try:
                for new_id, _, embedding in new_ids:
                    import struct
                    vec_bytes = struct.pack(f"{len(embedding)}f", *embedding)
                    conn.execute(
                        "INSERT INTO chunks_vec(chunk_id, embedding) VALUES(?, ?)",
                        (new_id, vec_bytes),
                    )
            except Exception as e:
                logger.warning(f"Failed to insert into vec table: {e}")

        conn.commit()
        return len(chunks)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Querying
# ---------------------------------------------------------------------------

def query_db(
    db_path: str,
    query_text: str,
    embed_fn: Callable[[list[str]], list[list[float]]],
    top_k: int = 5,
) -> list[dict]:
    """Query the database using FTS5 (and optionally vector search).

    Performs FTS5 full-text search. If sqlite-vec is available, also performs
    vector search and merges results (vector results ranked first).

    Args:
        db_path: Path to SQLite database file
        query_text: Text to search for
        embed_fn: Callable for generating query embedding (used if vec available)
        top_k: Maximum number of results to return

    Returns:
        List of dicts with keys: text, book_id, chapter, score
    """
    meta = get_db_meta(db_path)
    conn = sqlite3.connect(db_path)
    try:
        results = []

        # FTS5 search
        fts_rows = conn.execute(
            """
            SELECT c.id, c.text, c.book_id, c.chapter,
                   bm25(chunks_fts) as score
            FROM chunks_fts
            JOIN chunks c ON chunks_fts.rowid = c.id
            WHERE chunks_fts MATCH ?
            ORDER BY score
            LIMIT ?
            """,
            (query_text, top_k),
        ).fetchall()

        seen_ids = set()
        for row in fts_rows:
            row_id, text, book_id, chapter, score = row
            seen_ids.add(row_id)
            results.append({
                "text": text,
                "book_id": book_id,
                "chapter": chapter,
                "score": float(score) if score is not None else 0.0,
                "source": "fts",
            })

        # Vector search if available
        if meta.get("vec_available") == "true":
            try:
                import struct
                query_embedding = embed_fn([query_text])[0]
                vec_bytes = struct.pack(f"{len(query_embedding)}f", *query_embedding)

                vec_rows = conn.execute(
                    """
                    SELECT cv.chunk_id, c.text, c.book_id, c.chapter,
                           cv.distance as score
                    FROM chunks_vec cv
                    JOIN chunks c ON cv.chunk_id = c.id
                    WHERE embedding MATCH ?
                      AND k = ?
                    ORDER BY score
                    """,
                    (vec_bytes, top_k),
                ).fetchall()

                for row in vec_rows:
                    row_id, text, book_id, chapter, score = row
                    if row_id not in seen_ids:
                        seen_ids.add(row_id)
                        results.append({
                            "text": text,
                            "book_id": book_id,
                            "chapter": chapter,
                            "score": float(score) if score is not None else 0.0,
                            "source": "vec",
                        })
            except Exception as e:
                logger.warning(f"Vector search failed: {e}")

        return results[:top_k]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="SQLite RAG indexer")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # create subcommand
    create_parser = subparsers.add_parser("create", help="Create a new database")
    create_parser.add_argument("db_path", help="Path to database file")
    create_parser.add_argument("provider", help="Embedding provider (e.g. openai, ollama)")
    create_parser.add_argument("dims", type=int, help="Embedding dimensions")

    # index subcommand
    index_parser = subparsers.add_parser("index", help="Index chunks from JSON file")
    index_parser.add_argument("db_path", help="Path to database file")
    index_parser.add_argument("chunks_json", help="Path to JSON file with chunks array")

    # query subcommand
    query_parser = subparsers.add_parser("query", help="Query the database")
    query_parser.add_argument("db_path", help="Path to database file")
    query_parser.add_argument("query_text", help="Text to search for")
    query_parser.add_argument("--top-k", type=int, default=5, help="Number of results")

    args = parser.parse_args()

    if args.command == "create":
        create_db(args.db_path, args.provider, args.dims)
        print(f"Created database at {args.db_path}")

    elif args.command == "index":
        chunks = json.loads(Path(args.chunks_json).read_text())
        meta = get_db_meta(args.db_path)
        provider = meta.get("embedding_provider", "unknown")
        dims = int(meta.get("embedding_dims", 0))

        # For CLI, use a no-op embed function (embeddings must be provided externally)
        def noop_embed(texts):
            return [[0.0] * dims for _ in texts]

        count = index_chunks(args.db_path, chunks, provider=provider, dims=dims, embed_fn=noop_embed)
        print(f"Indexed {count} chunks")

    elif args.command == "query":
        meta = get_db_meta(args.db_path)
        dims = int(meta.get("embedding_dims", 768))

        def noop_embed(texts):
            return [[0.0] * dims for _ in texts]

        results = query_db(args.db_path, args.query_text, embed_fn=noop_embed, top_k=args.top_k)
        for i, r in enumerate(results, 1):
            print(f"{i}. [{r['book_id']} ch{r['chapter']}] {r['text'][:100]}...")
