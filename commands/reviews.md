---
description: "Fetch and synthesize book reviews"
allowed-tools: Bash, Read, Write, Task
argument-hint: "<epub-path-or-title> [--output <dir>]"
---

## Workflow

1. Load config via shared/config-loader.md
2. Determine title and ISBN:
   - If epub path given → parse metadata for title + ISBN
   - If bare title string → use as-is, ISBN = null
3. Resolve output path
4. Dispatch reviewer-agent in standalone mode (fetches + synthesizes)
5. QC: dispatch qc-review-fidelity
6. Update pipeline.json fetch_reviews + synthesize_reviews phases
