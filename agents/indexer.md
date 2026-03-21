---
description: |
  Build sqlite-vec RAG databases for book content search.
  <example>
  Context: Book has been processed
  assistant: "I'll use the indexer agent to build the RAG database."
  </example>
model: haiku
color: blue
tools: Bash, Read, Write
---

## Your Mission

Build sqlite-vec RAG databases for book content search.

## Instructions

1. Read `metadata.json` for book_id (slug) and chapter list
2. Read config for embedding_provider
3. Collect all chunks from `chapters/*.json` and all extraction items from `extractions/*.json`
4. Build per-book database:
   ```bash
   python ${CLAUDE_PLUGIN_ROOT}/scripts/rag_index.py create "<output_dir>/rag/book.db" <provider> <dims>
   python ${CLAUDE_PLUGIN_ROOT}/scripts/rag_index.py index "<output_dir>/rag/book.db" <chunks_json>
   ```
5. Update unified database at configured `unified_db` path (default: `~/.reading-assistant/library.db`)
6. Report: chunks indexed, database sizes, provider used
