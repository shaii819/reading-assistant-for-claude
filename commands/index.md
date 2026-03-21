---
description: "Build or rebuild sqlite-vec RAG database"
allowed-tools: Bash, Read, Write, Task
argument-hint: "<output-dir> [--rebuild] [--provider openai|ollama]"
---

## Workflow

1. Load config via shared/config-loader.md
2. Verify prerequisites: chapters/ with chunks must exist
3. Determine provider: --provider flag > config.embedding_provider
4. If existing DB has different provider and no --rebuild → ERROR: "DB uses {provider}. Use --rebuild to switch."
5. Dispatch indexer-agent with output-dir, provider, and rebuild flag
6. Update unified DB at config.unified_db
7. Update pipeline.json index phase
