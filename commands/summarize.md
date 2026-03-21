---
description: "Generate chapter summaries in source + target language"
allowed-tools: Bash, Read, Write, Task, AskUserQuestion
argument-hint: "<epub-path> [--chapter N] [--output <dir>] [--lang <target>]"
---

## Workflow

1. Load config via shared/config-loader.md
2. Resolve paths:
   - If --output given → use as book_dir
   - If epub path given → derive slug, use config.default_output_dir/slug
3. Prerequisites: if book_dir/chapters/ missing → run parser + chunker first
4. If --chapter N: summarize only chapter N (skip book-summary)
5. Dispatch summarizer-agent with book_dir and config
6. QC: dispatch qc-coverage-checker on source-language summaries
7. Update pipeline.json summarize phase
