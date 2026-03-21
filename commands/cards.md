---
description: "Generate Obsidian Zettelkasten notes from existing outputs"
allowed-tools: Bash, Read, Write, Task
argument-hint: "<output-dir> [--vault <path>]"
---

## Workflow

1. Load config via shared/config-loader.md
2. Verify prerequisites: summaries/ and extractions/ must exist in output-dir
   - If missing → ERROR: "Run /read:summarize and /read:extract first."
3. Determine vault_path: --vault flag > config.obsidian_vault > none
4. Dispatch cardmaker-agent with output-dir and vault_path
5. Update pipeline.json cards phase
