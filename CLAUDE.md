# reading-assistant

EPUB → structured knowledge pipeline for Claude Code.

## Architecture

Commands orchestrate agents. Agents do the thinking. Scripts handle I/O and external providers.

Pipeline: parse → chunk → [summarize + extract + review] → QC → [cards + index]

- Phase 1 (batch): parser (+ language detection), chunker, review-fetcher
- Cost gate: estimate tokens, confirm with user
- Phase 2 (AI): summarizer, extractor, reviewer — configurable models via provider abstraction
- Phase 3 (QC): 4 parallel sub-agents, auto-retry, threshold gating
- Phase 4 (output): cardmaker (Obsidian), indexer (sqlite-vec RAG)

## Provider Abstraction

`scripts/llm_provider.py` handles Claude/Ollama/OpenAI routing.
Claude models → agent handles natively. External models → agent calls script via Bash.
Never put AI logic in scripts — scripts only handle HTTP transport.

## Data Contracts

All intermediate artifacts have formal JSON schemas in the design spec.
Key files: metadata.json, chapters/*.json, reviews/raw/*.json, pipeline.json.

## Embedding Provider Pinning

Each RAG database is pinned to one embedding provider (stored in _meta table).
Switching providers requires --rebuild.

## Config

User config: `.claude/reading-assistant.local.md` (YAML frontmatter)

## Prerequisites

- Python 3.10+
- Run `/read:init` before first use
- Optional: OPENAI_API_KEY, HARDCOVER_API_KEY, Ollama
