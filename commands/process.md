---
description: "Full pipeline: parse, summarize, extract, review, QC, Obsidian notes, RAG database"
allowed-tools: Bash, Read, Write, Task, AskUserQuestion, Glob, Grep
argument-hint: "<epub-path> [--output <dir>] [--lang <target>] [--skip <stages>] [--force]"
---

## Full Pipeline Orchestration

### Step 1: Setup

1. Load config via shared/config-loader.md → get config + fingerprint
2. Parse arguments:
   - `epub_path` (required): path to .epub file
   - `--output`: output directory (default: config.default_output_dir)
   - `--lang`: target language (default: config.target_language)
   - `--skip`: comma-separated stage names to skip
   - `--force`: delete existing output and start fresh
3. Validate epub_path exists and is readable
4. Determine output directory and book slug

### Step 2: Resume Logic

Check for existing `pipeline.json` at `{output_dir}/{slug}/pipeline.json`:

**If NOT found:** Create fresh pipeline.json with all phases "pending".

**If found AND --force:** Delete the book output directory, create fresh pipeline.json.

**If found AND no --force:**
1. **Concurrency check:** If any phase has status "running" → ERROR: "Pipeline already running for this book. Wait or use --force."
2. **Config check:** Compare stored config_fingerprint with current. If different → ask user:
   "Config has changed since last run. [1] Continue with original config [2] Start fresh [3] Cancel"
3. **Resume:** Skip phases with status "completed" or "skipped". Start from first "pending" or "failed" phase.

### Step 3: Skip Validation

Valid stages: `parse`, `fetch_reviews`, `chunk`, `summarize`, `extract`, `synthesize_reviews`, `qc`, `cards`, `index`

Dependency check:
- parse → chunk, summarize, extract, cards, index
- chunk → summarize, extract, index
- summarize → cards
- extract → cards
- fetch_reviews → synthesize_reviews

ERROR if a non-skipped stage depends on a skipped stage.

### Step 4: Phase Execution

**Phase execution pattern** (for each phase):
1. Set phase status to "running" + started_at → write pipeline.json
2. Dispatch agent or run script
3. On success: set "completed" + completed_at → write pipeline.json
4. On failure: set "failed" + error → write pipeline.json → STOP

**Phase 1a** (parallel): Dispatch parser-agent + run fetch_reviews.py
**Phase 1b** (after parser): Dispatch chunker-agent
**Cost Gate**: Run estimate_cost.py → show estimate → ask user confirmation
**Phase 2** (parallel): Dispatch summarizer + extractor + reviewer agents
**Phase 3**: Dispatch qc-coordinator → check verdict. If FAIL → stop.
**Phase 4** (parallel): Dispatch cardmaker + indexer agents

### Step 5: Report

Display final status from pipeline.json: all phases, timings, QC verdict, total cost.
