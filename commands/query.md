---
description: "Search the RAG database"
allowed-tools: Bash, Read, Write
argument-hint: "<question> [--book <slug>] [--top N]"
---

## Workflow

1. Load config via shared/config-loader.md
2. Determine database:
   - If --book given → look for config.default_output_dir/{slug}/rag/book.db
   - Without --book → use config.unified_db (~/.reading-assistant/library.db)
   - If DB not found → ERROR: "No RAG database found. Run /read:index first."
3. Run query:
   ```bash
   python ${CLAUDE_PLUGIN_ROOT}/scripts/rag_index.py query "<db_path>" "<question>" <top_k>
   ```
4. Display results formatted as:
   - Book title, chapter, text snippet (150 chars), relevance score
