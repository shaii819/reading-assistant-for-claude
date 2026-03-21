---
description: "Extract facts, examples, metaphors, quotes, and glossary"
allowed-tools: Bash, Read, Write, Task, AskUserQuestion
argument-hint: "<epub-path> [--category facts|examples|metaphors|quotes|glossary] [--output <dir>]"
---

## Workflow

1. Load config via shared/config-loader.md
2. Resolve paths (same as summarize)
3. Prerequisites: if book_dir/chapters/ missing → run parser + chunker first
4. If --category: extract only that category
5. Dispatch extractor-agent with book_dir, config, and category filter
6. QC: dispatch qc-quote-verifier (if quotes) + qc-category-auditor
7. Update pipeline.json extract phase
