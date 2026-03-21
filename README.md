# reading-assistant

Transform EPUB books into structured knowledge: summaries, extractions, Obsidian notes, and a searchable RAG database.

## What it does

- **Chapter summaries** — multilingual, one per chapter plus a full-book synthesis
- **Knowledge extractions** — facts, examples, metaphors, quotes, and a glossary
- **Book reviews** — fetched from Hardcover and Open Library, synthesized into a meta-review
- **Quality control** — parallel QC agents verify quotes, coverage, categorization, and review fidelity
- **Obsidian Zettelkasten notes** — MOC, chapter notes, concept notes, and quote notes with wikilinks
- **RAG database** — sqlite-vec full-text + vector search over all chunks

## Part of the xiaolai marketplace

Install and manage this plugin through the [xiaolai Claude plugin marketplace](https://github.com/xiaolai/claude-plugin-marketplace).

## Installation

```bash
claude plugin install reading-assistant@xiaolai --scope project
```

Then initialize the environment in your project:

```
/read:init
```

## Commands

| Command | Description |
|---------|-------------|
| `/read:init` | Set up reading-assistant: create venv, install dependencies, validate environment |
| `/read:process` | Full pipeline: parse, summarize, extract, review, QC, Obsidian notes, RAG database |
| `/read:summarize` | Generate chapter summaries in source + target language |
| `/read:extract` | Extract facts, examples, metaphors, quotes, and glossary |
| `/read:reviews` | Fetch and synthesize book reviews |
| `/read:cards` | Generate Obsidian Zettelkasten notes from existing outputs |
| `/read:index` | Build or rebuild sqlite-vec RAG database |
| `/read:query` | Search the RAG database |
| `/read:status` | Show pipeline processing status for a book |

## How it works

The pipeline runs in four phases:

1. **Phase 1 — Parse & chunk** (`parser`, `chunker`): EPUB is parsed into structured chapter JSON with metadata. Chapters are split into overlapping token-bounded chunks. Book reviews are fetched in parallel.
2. **Phase 2 — AI processing** (`summarizer`, `extractor`, `reviewer`): Each chunk is processed for summaries and knowledge extraction. Reviews are synthesized into a meta-review. A cost estimate is presented before this phase begins.
3. **Phase 3 — Quality control** (`qc-coordinator` + 4 sub-agents): Four parallel QC agents verify quote accuracy, summary coverage, category correctness, and review fidelity. Failed checks trigger automatic retry up to a configurable threshold.
4. **Phase 4 — Outputs** (`cardmaker`, `indexer`): Obsidian Zettelkasten notes are generated with wikilinks. A sqlite-vec database is built for full-text and vector search.

## Agents

| Agent | Model | Description |
|-------|-------|-------------|
| `parser` | haiku | Parse EPUB files into structured chapter data, metadata, and detect language |
| `chunker` | haiku | Split chapter text into overlapping chunks for AI processing |
| `summarizer` | sonnet | Generate multilingual chapter and book summaries |
| `extractor` | sonnet | Extract structured knowledge: facts, examples, metaphors, quotes, glossary |
| `reviewer` | sonnet | Synthesize book reviews from multiple sources into a meta-review |
| `qc-coordinator` | opus | Orchestrate quality control with parallel sub-agents, auto-retry, and threshold gating |
| `qc-quote-verifier` | haiku | Mechanically verify extracted quotes against source text using fuzzy matching |
| `qc-category-auditor` | sonnet | Spot-check extracted items for correct categorization |
| `qc-coverage-checker` | sonnet | Verify that chapter summaries cover major topics from source text |
| `qc-review-fidelity` | sonnet | Verify review synthesis accuracy against raw source reviews |
| `cardmaker` | sonnet | Generate atomic Obsidian Zettelkasten notes from processed book data |
| `indexer` | haiku | Build sqlite-vec RAG databases for book content search |

## Prerequisites

- **Python 3.10+** — required by all scripts
- **`/read:init`** — must be run once per project before any other command; creates a virtualenv and installs all Python dependencies
- **`OPENAI_API_KEY`** (optional) — enables OpenAI embeddings and models as an alternative to Claude
- **`HARDCOVER_API_KEY`** (optional) — enables review fetching from Hardcover
- **Ollama** (optional) — enables local model inference; run `ollama serve` before processing

## Configuration

Create `.claude/reading-assistant.local.md` in your project to override defaults. The file uses YAML frontmatter:

```yaml
---
default_language: en
target_languages: [zh, ja]
chunk_size: 2000
overlap: 0.15
summarizer_model: sonnet
extractor_model: sonnet
qc_model: opus
obsidian_vault: /path/to/your/vault
---
```

All fields are optional. Unset fields fall back to built-in defaults.

## License

MIT
